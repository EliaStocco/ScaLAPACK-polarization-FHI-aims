import json

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def model(x, A, m):
    return A * x**m


# -----------------------------
# Load + reshape data
# -----------------------------
df = pd.read_csv("dataframe.csv")

df = df.pivot(
    index=["basis", "ncores"],
    columns="calculation",
    values="time"
).reset_index()

# Compute target quantity
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


basis_sets = ["light", "intermediate", "tight"]


# -----------------------------
# Fit per basis set
# -----------------------------
for basis in basis_sets:

    sub_df = (
        df[df["basis"] == basis]
        .sort_values("ncores")
    )

    if len(sub_df) < 2:
        print(f"Skipping {basis}: insufficient data")
        continue

    x = sub_df["ncores"].to_numpy()
    y = sub_df["time"].to_numpy()

    # -------------------------
    # log-log fit
    # -------------------------
    logx = np.log10(x)
    logy = np.log10(y)

    (m_log, q), cov = np.polyfit(logx, logy, 1, cov=True)
    dm_log, dq = np.sqrt(np.diag(cov))

    results["log"][basis] = {
        "m": float(m_log),
        "q": float(q),
        "err-m": float(dm_log),
        "err-q": float(dq),
    }

    # -------------------------
    # nonlinear fit y = A x^m
    # -------------------------
    popt, pcov = curve_fit(model, x, y)

    A, m = popt
    dA, dm = np.sqrt(np.diag(pcov))

    results["linear"][basis] = {
        "A": float(A),
        "m": float(m),
        "log10(A)": float(np.log10(A)),
        "err-A": float(dA),
        "err-m": float(dm),
        "err-log10(A)": float(dA / (A * np.log(10))),
    }


# -----------------------------
# Save results
# -----------------------------
with open("fit.json", "w") as f:
    json.dump(results, f, indent=4)