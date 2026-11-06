"""Equivalence tests (TOST) for the measures that test H2, plus the number of trials.

For each metric: Implicit minus Explicit difference with a 90% CI (Welch), Cohen's d with the
pooled SD, the TOST p value for an equivalence bound of d = 0.5 (about half a pooled SD), and
the smallest bound d (searched in steps of 0.01) at which the TOST p value falls below .05.
A non-significant TOST at d = 0.5 means equivalence is NOT shown; the smallest bound tells
which differences the data can exclude.

Input: ../h2_data_for_tost.csv (per-participant behavioral metrics).
Requires: pingouin.

Run:  python3 03_tost_equivalence.py
"""
import numpy as np
import pandas as pd
import pingouin as pg
from scipy import stats

from _pipeline import DATA_ANALYSIS

df = pd.read_csv(DATA_ANALYSIS / "h2_data_for_tost.csv")
df["c"] = df["condition"].map({"Implícita": "I", "Explícita": "E"})
METRICS = {"Assisted performance": "performance_rate_assisted",
           "Independent performance": "performance_rate_independent",
           "Assisted max length": "max_len_assisted",
           "Independent max length": "max_len_independent",
           "Trials": "n_trials"}


def tost_p(a, b, d):
    """TOST p value for the bound d (in pooled-SD units); also returns the pooled SD."""
    sp = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return pg.tost(a, b, bound=d * sp, paired=False, correction=False)["pval"].values[0], sp


print(f"{'metric':26s} {'diff(I-E)':>10s} {'90%CI diff':>20s} {'d':>6s} {'90%CI d':>16s} "
      f"{'TOST p@.5':>9s} {'min bound d (p<.05)':>20s}")
for label, col in METRICS.items():
    a = df.loc[df.c == "I", col].dropna()
    b = df.loc[df.c == "E", col].dropna()
    n1, n2 = len(a), len(b)
    diff = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / n1 + b.var(ddof=1) / n2)
    dfw = (a.var(ddof=1) / n1 + b.var(ddof=1) / n2) ** 2 / (
        (a.var(ddof=1) / n1) ** 2 / (n1 - 1) + (b.var(ddof=1) / n2) ** 2 / (n2 - 1))
    tcrit = stats.t.ppf(.95, dfw)
    lo, hi = diff - tcrit * se, diff + tcrit * se
    p5, sp = tost_p(a, b, 0.5)
    d, lod, hid = diff / sp, lo / sp, hi / sp
    min_bound = None
    for bound in np.arange(0.3, 2.5, 0.01):
        if tost_p(a, b, bound)[0] < .05:
            min_bound = round(bound, 2)
            break
    print(f"{label:26s} {diff:10.3f} [{lo:7.3f},{hi:7.3f}]   {d:6.2f} [{lod:5.2f},{hid:5.2f}]  "
          f"{p5:9.3f}  {min_bound}")
