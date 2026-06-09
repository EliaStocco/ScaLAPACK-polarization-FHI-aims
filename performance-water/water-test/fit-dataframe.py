import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import json


def model(x, A, m):
    return A * x**m


df = pd.read_csv("dataframe.csv")

results = {
    "log": {
        "formula": "log10(y) = m log10(x) + q"
    },
    "linear": {
        "formula": "y = A x^m"
    }
}

for mol in sorted(df["molecules"].unique()):

    sub_df = df[df["molecules"] == mol].sort_values("ncores")

    x = sub_df["ncores"].to_numpy(dtype=float)
    y = sub_df["time"].to_numpy(dtype=float)

    # log-log fit
    logx = np.log10(x)
    logy = np.log10(y)

    (m_log, q), cov = np.polyfit(logx, logy, 1, cov=True)
    dm_log, dq = np.sqrt(np.diag(cov))

    results["log"][str(mol)] = {
        "m": float(m_log),
        "q": float(q),
        "err-m": float(dm_log),
        "err-q": float(dq),
    }

    # nonlinear fit
    popt, pcov = curve_fit(model, x, y, p0=[y[0], -1])

    A, m = popt
    dA, dm = np.sqrt(np.diag(pcov))

    results["linear"][str(mol)] = {
        "A": float(A),
        "m": float(m),
        "log10(A)": float(np.log10(A)),
        "err-A": float(dA),
        "err-m": float(dm),
        "err-log10(A)": float(dA / (A * np.log(10))),
    }

with open("fit.json", "w") as f:
    json.dump(results, f, indent=4)