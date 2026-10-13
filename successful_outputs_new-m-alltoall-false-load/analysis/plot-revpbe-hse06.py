#!/usr/bin/env python3
"""Plot revPBE and HSE06 polarization scaling by molecule count."""
from pathlib import Path
import csv, json
import numpy as np
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
with (HERE / "analysis-dataframe.csv").open(newline="") as f:
    rows = list(csv.DictReader(f))
with (HERE / "fit.json").open() as f:
    fits = json.load(f)["fits"]

colors = {"revPBE": "#0173b2", "HSE06": "#d55e00", "revPBE0": "#029e73"}
markers = {"revPBE": "o", "HSE06": "s", "revPBE0": "^"}
fig, axes = plt.subplots(2, 3, figsize=(11, 7), sharex="col", sharey="row")
top_axes = axes[0]
coefficient_axes = axes[1]

for ax, coefficient_axis, molecules in zip(top_axes, coefficient_axes, (128, 196, 256)):
    for functional in ("revPBE", "HSE06", "revPBE0"):
        subset = sorted(
            [
                r for r in rows
                if r["functional"] == functional
                and int(r["molecules"]) == molecules
                and int(r["ncores"]) >= 128
                and not (functional == "HSE06" and molecules == 196 and int(r["ncores"]) == 2048)
            ],
            key=lambda r: int(r["ncores"]),
        )
        if not subset:
            continue
        x = np.array([int(r["ncores"]) for r in subset], dtype=float)
        y = np.array([float(r["polarization_time_s"]) for r in subset])
        label = functional
        ax.plot(x, y, marker=markers[functional], color=colors[functional], linestyle="-", label=label)

        # Running fit: fit every prefix of the available x-values.  A
        # two-point prefix is the smallest subset defining a log-log slope.
        running_x, running_m = [], []
        for end in range(2, len(x) + 1):
            exponent, intercept = np.polyfit(np.log10(x[:end]), np.log10(y[:end]), 1)
            running_x.append(x[end - 1])
            # Define the reported scaling coefficient as positive:
            # time ~ ncores**(-m), so ideal inverse scaling has m=1.
            running_m.append(-exponent)
        coefficient_axis.plot(
            running_x, running_m, marker=markers[functional], color=colors[functional],
            linestyle="-", label=functional,
        )
    ax.set_title(f"{molecules} molecules")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlabel("n. cores")
    ax.set_xticks([128, 256, 512, 1024, 2048])
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax.grid(True, which="both", alpha=0.2)

top_axes[0].set_ylabel("Polarization overhead (s)")
top_axes[0].legend(loc="best", fontsize=8)
for coefficient_axis in coefficient_axes:
    coefficient_axis.axhline(1, color="0.4", linestyle="--", linewidth=0.8)
    coefficient_axis.set_xlabel("largest core count included")
    coefficient_axis.set_ylabel("running positive $m$")
    coefficient_axis.grid(True, alpha=0.2)
coefficient_axes[0].text(
    0.03, 0.03, "$m$: log-log fit from 128 cores\nto the indicated endpoint",
    transform=coefficient_axes[0].transAxes, fontsize=8, va="bottom",
)
fig.suptitle("Polarization scaling: revPBE vs HSE06")
fig.tight_layout()
output = HERE / "scaling-per-box.pdf"
fig.savefig(output, bbox_inches="tight")
print(f"Wrote {output}")


def low_core_subset(functional, molecules):
    """Return all retained points, including the 16-core runs."""
    return sorted(
        [
            r for r in rows
            if r["functional"] == functional
            and int(r["molecules"]) == molecules
            and int(r["ncores"]) >= 16
            and not (functional == "HSE06" and molecules == 196 and int(r["ncores"]) == 2048)
        ],
        key=lambda r: int(r["ncores"]),
    )


def configure_core_axis(ax):
    ax.set_xscale("log", base=2)
    ax.set_xticks([16, 32, 64, 128, 256, 512, 1024, 2048])
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax.grid(True, which="both", alpha=0.2)


# Standalone low-core views complement the 128-core-and-up comparison above.
fig, axes = plt.subplots(1, 3, figsize=(11, 3.5), sharey=True)
for ax, molecules in zip(axes, (128, 196, 256)):
    for functional in ("revPBE", "HSE06", "revPBE0"):
        subset = low_core_subset(functional, molecules)
        if not subset:
            continue
        x = np.array([int(r["ncores"]) for r in subset], dtype=float)
        y = np.array([float(r["polarization_time_s"]) for r in subset])
        exponent, intercept = np.polyfit(np.log10(x), np.log10(y), 1)
        xx = np.logspace(np.log10(x.min()), np.log10(x.max()), 200)
        ax.plot(x, y, marker=markers[functional], color=colors[functional], linestyle="-", label=functional)
        ax.plot(xx, 10 ** intercept * xx ** exponent, color=colors[functional], linestyle="--", alpha=0.8)
    ax.set(title=f"{molecules} molecules", yscale="log", xlabel="n. cores")
    configure_core_axis(ax)
axes[0].set_ylabel("Polarization overhead (s)")
axes[0].legend(loc="best", fontsize=8)
fig.suptitle("Polarization overhead scalability: cores from 16")
fig.tight_layout()
output = HERE / "scalability-overhead-from16.pdf"
fig.savefig(output, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {output}")

fig, axes = plt.subplots(1, 3, figsize=(11, 3.5), sharey=True)
for ax, molecules in zip(axes, (128, 196, 256)):
    for functional in ("revPBE", "HSE06", "revPBE0"):
        subset = low_core_subset(functional, molecules)
        if len(subset) < 2:
            continue
        x = np.array([int(r["ncores"]) for r in subset], dtype=float)
        y = np.array([float(r["polarization_time_s"]) for r in subset])
        running_x, running_m = [], []
        for end in range(2, len(x) + 1):
            exponent, _ = np.polyfit(np.log10(x[:end]), np.log10(y[:end]), 1)
            running_x.append(x[end - 1])
            running_m.append(-exponent)
        ax.plot(running_x, running_m, marker=markers[functional], color=colors[functional], linestyle="-", label=functional)
    ax.axhline(1, color="0.4", linestyle="--", linewidth=0.8)
    ax.set(title=f"{molecules} molecules", xlabel="largest core count included")
    configure_core_axis(ax)
axes[0].set_ylabel("running positive $m$")
axes[0].legend(loc="best", fontsize=8)
fig.suptitle("Running scalability exponent: cores from 16")
fig.tight_layout()
output = HERE / "scalability-exponent-from16.pdf"
fig.savefig(output, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {output}")
