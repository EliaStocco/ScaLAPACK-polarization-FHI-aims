import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import json


def model(x, A, m):
    return A * x**m


# -----------------------------
# Load + reshape data
# -----------------------------
df = pd.read_csv("dataframe.csv")

df = df.pivot(
    index=["supercell", "ncores"],
    columns="calculation",
    values="time"
).reset_index()

# compute target quantity
df["time"] = df["dipole"] - df["scf"]


# -----------------------------
# Output structure
# -----------------------------
results = {
    "log": {
        "formula": "log10(y) = m log10(x) + q"
    },
    "linear": {
        "formula": "y = A x^m"
    }
}


supercell = [4]


# -----------------------------
# Fit per system size
# -----------------------------
for mol in supercell:

    sub_df = df[df["supercell"] == mol].sort_values("ncores")

    x = sub_df["ncores"].to_numpy()
    y = sub_df["time"].to_numpy()

    # -------------------------
    # log-log fit
    # -------------------------
    logx = np.log10(x)
    logy = np.log10(y)

    (m_log, q), cov = np.polyfit(logx, logy, 1, cov=True)
    dm_log, dq = np.sqrt(np.diag(cov))

    results["log"][str(mol)] = {
        "m": m_log,
        "q": q,
        "err-m": dm_log,
        "err-q": dq
    }

    # -------------------------
    # nonlinear fit y = A x^m
    # -------------------------
    popt, pcov = curve_fit(model, x, y)

    A, m = popt
    dA, dm = np.sqrt(np.diag(pcov))

    results["linear"][str(mol)] = {
        "A": A,
        "m": m,
        "log10(A)": np.log10(A),
        "err-A": dA,
        "err-m": dm,
        "err-log10(A)": dA / (A * np.log(10))
    }


# -----------------------------
# Save results
# -----------------------------
with open("fit.json", "w") as f:
    json.dump(results, f, indent=4)