"""Fit the HSE06 dipole-only cost to a power law.

Run ``extract.py`` first.  The resulting ``fit.json`` is read by ``plot.py``.
"""

import json

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def model(ncores, prefactor, exponent):
    return prefactor * ncores**exponent


df = pd.read_csv("dataframe.csv")
df = df.pivot(index="ncores", columns="calculation", values="time").reset_index()

missing = {"scf", "dipole"}.difference(df.columns)
if missing:
    raise ValueError(f"Missing calculation data: {', '.join(sorted(missing))}")

df["time"] = df["dipole"] - df["scf"]
if (df["time"] <= 0).any():
    raise ValueError("Dipole-minus-SCF times must be positive for a log-log fit")

df = df.sort_values("ncores")
x = df["ncores"].to_numpy()
y = df["time"].to_numpy()

(exponent_log, intercept_log), covariance_log = np.polyfit(
    np.log10(x), np.log10(y), 1, cov=True
)
error_exponent_log, error_intercept_log = np.sqrt(np.diag(covariance_log))

(prefactor, exponent), covariance = curve_fit(model, x, y)
error_prefactor, error_exponent = np.sqrt(np.diag(covariance))

results = {
    "log": {
        "formula": "log10(y) = m log10(x) + q",
        "m": exponent_log,
        "q": intercept_log,
        "err-m": error_exponent_log,
        "err-q": error_intercept_log,
    },
    "linear": {
        "formula": "y = A x^m",
        "A": prefactor,
        "m": exponent,
        "log10(A)": np.log10(prefactor),
        "err-A": error_prefactor,
        "err-m": error_exponent,
        "err-log10(A)": error_prefactor / (prefactor * np.log(10)),
    },
}

with open("fit.json", "w") as handle:
    json.dump(results, handle, indent=4)
