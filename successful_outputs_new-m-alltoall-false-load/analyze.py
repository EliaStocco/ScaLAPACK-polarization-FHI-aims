#!/usr/bin/env python3
"""Analyze the successful new-m, alltoall=false, load-balanced runs."""
from pathlib import Path
import csv, json, re
import numpy as np
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
OUT = HERE / "analysis"
OUT.mkdir(exist_ok=True)
ROOT = HERE
TIME = re.compile(
    r"\| Total time\s*:\s*([0-9.eE+-]+)\s*s\s+([0-9.eE+-]+)\s*s"
)
PAT = {
 "wannier_time_s": re.compile(r"Total time for Wannier Center Evolution\s*:\s*[\d.eE+-]+\s*s\s+([\d.eE+-]+)\s*s"),
 "fourier_ev_time_s": re.compile(r"Total Time for Fourier interpolated EV solution\s*:\s*([\d.eE+-]+)\s+([\d.eE+-]+)"),
 "dipole_matrix_time_s": re.compile(r"Total Time for dipole matrix\s*:\s*([\d.eE+-]+)\s+([\d.eE+-]+)"),
 "dipole_term_time_s": re.compile(r"Total Time for dipole term\s*:\s*([\d.eE+-]+)\s+([\d.eE+-]+)"),
 "berry_term_time_s": re.compile(r"Total Time for berry term\s*:\s*([\d.eE+-]+)\s+([\d.eE+-]+)"),
}

def total(p):
    vals = [float(x[1]) for x in TIME.findall(p.read_text(errors="replace"))]
    if not vals: raise ValueError(f"no total time: {p}")
    return vals[-1]

def components(p):
    text = p.read_text(errors="replace")
    out = {}
    for name, pat in PAT.items():
        vals = [float(x[-1] if isinstance(x, tuple) else x) for x in pat.findall(text)]
        if not vals: raise ValueError(f"no {name}: {p}")
        out[name] = sum(vals)
    return out

def fit(x, y):
    m, b = np.polyfit(np.log10(x), np.log10(y), 1)
    pred = m*np.log10(x)+b
    ss = float(np.sum((np.log10(y)-pred)**2)); st = float(np.sum((np.log10(y)-np.mean(np.log10(y)))**2))
    return {"A": float(10**b), "m": float(m), "r_squared": 1-ss/st if st else 1.0, "n_points": len(x)}

def main():
    rows=[]
    for d in sorted(ROOT.glob("new-m=*-alltoall-false-load/*-*/results/aims.n=*.out")):
        m = int(d.parts[-4].split("=")[1].split("-")[0]); calc, functional = d.parts[-3].split("-",1); n=int(d.stem.split("=")[1])
        row={"molecules":m,"functional":functional,"calculation":calc,"ncores":n,"time_s":total(d),"file":str(d.relative_to(ROOT))}
        if calc=="dipole": row.update(components(d))
        rows.append(row)
    rows.sort(key=lambda r:(r["functional"],r["molecules"],r["calculation"],r["ncores"]))
    fields=["molecules","functional","calculation","ncores","time_s",*PAT,"file"]
    with (OUT/"dataframe.csv").open("w",newline="") as f: csv.DictWriter(f,fieldnames=fields).writeheader(); csv.DictWriter(f,fieldnames=fields).writerows(rows)
    grouped={}
    for r in rows: grouped.setdefault((r["functional"],r["molecules"],r["ncores"]),{})[r["calculation"]]=r
    paired=[]
    for (fun,m,n), cs in sorted(grouped.items()):
        if "scf" not in cs or "dipole" not in cs: continue
        p=cs["dipole"]; s=cs["scf"]; overhead=p["time_s"]-s["time_s"]
        if overhead<=0: continue
        q={"functional":fun,"molecules":m,"ncores":n,"scf":s["time_s"],"dipole":p["time_s"],"polarization_time_s":overhead}
        q.update({k:p[k] for k in PAT}); q["extra_time_s"]=abs(overhead-p["wannier_time_s"]); paired.append(q)
    af=["functional","molecules","ncores","scf","dipole","polarization_time_s",*PAT,"extra_time_s"]
    with (OUT/"analysis-dataframe.csv").open("w",newline="") as f: w=csv.DictWriter(f,fieldnames=af); w.writeheader(); w.writerows(paired)
    fits={}; comp=[]
    for fun,m in sorted({(r["functional"],r["molecules"]) for r in paired}):
        rs=sorted([r for r in paired if r["functional"]==fun and r["molecules"]==m],key=lambda r:r["ncores"])
        fits.setdefault(fun,{})[str(m)]={}
        for name in ["scf","dipole","polarization_time_s",*PAT,"extra_time_s"]:
            sub=[r for r in rs if float(r[name])>0]; x=np.array([r["ncores"] for r in sub]); y=np.array([float(r[name]) for r in sub]); z=fit(x,y); fits[fun][str(m)][name]=z
            comp.append({"functional":fun,"molecules":m,"component":name,**z,"deviation_from_ideal":abs(z["m"]+1),"doubling_factor":2**z["m"]})
        fig,ax=plt.subplots(figsize=(7,5));
        for name in ["scf","dipole","polarization_time_s",*PAT,"extra_time_s"]:
            sub=[r for r in rs if float(r[name])>0]; x=np.array([r["ncores"] for r in sub]); y=np.array([float(r[name]) for r in sub]); z=fits[fun][str(m)][name]; xx=np.logspace(np.log10(x.min()),np.log10(x.max()),200); ax.plot(x,y,"o",label=name.replace("_time_s", "")); ax.plot(xx,z["A"]*xx**z["m"],"--",alpha=.7)
        ax.set(xscale="log",yscale="log",xlabel="n. cores",ylabel="CPU time (s)",title=f"{fun}, {m} molecules"); ax.grid(True,which="both",alpha=.2); ax.legend(fontsize=7,ncol=2); fig.tight_layout(); fig.savefig(OUT/f"components-{fun}-m{m}.pdf"); plt.close(fig)
    with (OUT/"fit.json").open("w") as f: json.dump({"formula":"time=A*ncores**m","fits":fits},f,indent=2); f.write("\n")
    comp.sort(key=lambda r:r["deviation_from_ideal"],reverse=True)
    with (OUT/"component-scalability.csv").open("w",newline="") as f: w=csv.DictWriter(f,fieldnames=list(comp[0])); w.writeheader(); w.writerows(comp)
    # Overview plot: polarization overhead and running scaling exponent by functional.
    available_funs = {r["functional"] for r in paired}
    preferred_funs = ["revPBE", "HSE06", "revPBE0"]
    funs = [fun for fun in preferred_funs if fun in available_funs]
    funs.extend(sorted(available_funs - set(funs)))
    fig,axes=plt.subplots(2,len(funs),figsize=(4*len(funs),7),sharex="col",sharey="row"); top_axes,coefficient_axes=np.asarray(axes).reshape(2,-1)
    for ax,coefficient_axis,fun in zip(top_axes,coefficient_axes,funs):
        for m in sorted({r["molecules"] for r in paired if r["functional"]==fun}):
            rs=sorted([r for r in paired if r["functional"]==fun and r["molecules"]==m and r["ncores"]>=128 and not (fun=="HSE06" and m==196 and r["ncores"]==2048)],key=lambda r:r["ncores"]); x=np.array([r["ncores"] for r in rs]); y=np.array([r["polarization_time_s"] for r in rs]); ax.plot(x,y,"o-",label=f"{m} molecules")
            running_x=[]; running_m=[]
            for end in range(2,len(x)+1):
                exponent,_=np.polyfit(np.log10(x[:end]),np.log10(y[:end]),1); running_x.append(x[end-1]); running_m.append(-exponent)
            coefficient_axis.plot(running_x,running_m,"o-",label=f"{m} molecules")
        ax.set(xscale="log",yscale="log",title=fun,xlabel="n. cores"); ax.set_xticks([128,256,512,1024,2048]); ax.get_xaxis().set_major_formatter(plt.ScalarFormatter()); ax.grid(True,which="both",alpha=.2)
        coefficient_axis.axhline(1,color="0.4",linestyle="--",linewidth=.8); coefficient_axis.set(xscale="log",xlabel="largest core count included"); coefficient_axis.set_xticks([128,256,512,1024,2048]); coefficient_axis.get_xaxis().set_major_formatter(plt.ScalarFormatter()); coefficient_axis.grid(True,which="both",alpha=.2)
    if len(top_axes) > 1: top_axes[1].annotate("orange curve to be recalculated", xy=(0.5,0.06), xycoords="axes fraction", ha="center", color="#d55e00", fontsize=8)
    top_axes[0].set_ylabel("Polarization overhead (s)"); top_axes[0].legend(); coefficient_axes[0].set_ylabel("running positive $m$"); coefficient_axes[0].text(.03,.03,"$m$: log-log fit from 128 cores\nto the indicated endpoint",transform=coefficient_axes[0].transAxes,fontsize=8,va="bottom"); fig.tight_layout(); fig.savefig(OUT/"scaling-per-xc.pdf"); plt.close(fig)
    print(f"Extracted {len(rows)} records, {len(paired)} paired records; outputs in {OUT}")

if __name__ == "__main__": main()
