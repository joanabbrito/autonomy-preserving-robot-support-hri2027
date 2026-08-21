import pandas as pd
import pingouin as pg
import numpy as np
import os

# Sensitivity-check exclusion: set via EXCLUDE_IDS env var, comma-separated (e.g. EXCLUDE_IDS=P15).
# Must match generate_report.py's EXCLUDE_IDS so this reads the matching exported CSV.
_exclude_ids = {x.strip().upper() for x in os.environ.get("EXCLUDE_IDS", "").split(",") if x.strip()}
_suffix = ("_excl_" + "_".join(sorted(_exclude_ids))) if _exclude_ids else ""

df = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"h2_data_for_tost{_suffix}.csv"))
df["condition"] = df["condition"].map({"Implícita": "Implicit", "Explícita": "Explicit"})

metrics = {
    "Trials": "n_trials",
    "Performance (assisted)": "performance_rate_assisted",
    "Performance (independent)": "performance_rate_independent",
    "Max. Length (assisted)": "max_len_assisted",
    "Max. Length (independent)": "max_len_independent",
}

BOUND_D = 0.5  # same convention as the reference paper (Cohen's d = 0.5, medium effect)

print(f"Equivalence bound: Cohen's d = {BOUND_D} (post-hoc, not preregistered)")
print()
print(f"{'Metric':<28}{'n_I':<6}{'n_E':<6}{'Mimp':<10}{'Mexp':<10}{'TOST p':<10}{'Equivalent?':<12}")

for label, col in metrics.items():
    imp = df.loc[df.condition == "Implicit", col].dropna()
    exp = df.loc[df.condition == "Explicit", col].dropna()

    # pooled SD to convert Cohen's d bound into raw units for this metric
    n1, n2 = len(imp), len(exp)
    s1, s2 = imp.std(ddof=1), exp.std(ddof=1)
    pooled_sd = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
    bound_raw = BOUND_D * pooled_sd

    tost = pg.tost(imp, exp, bound=bound_raw, paired=False, correction=False)
    p = tost["pval"].values[0]
    equiv = "YES" if p < 0.05 else "no"
    print(f"{label:<28}{n1:<6}{n2:<6}{imp.mean():<10.3f}{exp.mean():<10.3f}{p:<10.4f}{equiv:<12}")

print()
print("For reference, also standard independent t-test p-values (as currently reported in the paper):")
for label, col in metrics.items():
    imp = df.loc[df.condition == "Implicit", col].dropna()
    exp = df.loc[df.condition == "Explicit", col].dropna()
    tt = pg.ttest(imp, exp, paired=False)
    print(f"  {label}: t-test p = {tt['p-val'].values[0]:.3f}")
