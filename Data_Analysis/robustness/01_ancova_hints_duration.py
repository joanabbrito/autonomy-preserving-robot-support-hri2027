"""ANCOVA robustness check for the questionnaire results.

Question: do the condition differences in Self-Reliance, BPNSS Autonomy and IMI Perceived
Competence survive adjustment for hint volume and session duration? Implicit participants
received more hints and tended to have longer sessions, so these are plausible alternative
explanations (hints are a consequence of the condition, so this is a robustness check, not
confounder removal).

Model: ordinary least squares, outcome ~ condition + covariates (N = 35).
    n_hints          = hint episodes, i.e. "Help Needed" (moments in which help was needed)
    total_subhints   = total hints delivered, i.e. "Hints Received"
    duration_min     = session duration in minutes
Reported: Implicit minus Explicit difference b (scale units), its SE, p, and the adjusted
effect size b / residual SD. Self-Reliance is also analysed on ranks.

Run:  python3 01_ancova_hints_duration.py
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from _pipeline import load_pipeline

ns = load_pipeline()
mm, lm, am = ns["manip_merged"], ns["log_merged"], ns["_ancova_merged"]

d = am[["ID_UP", "condition", "IMI_Competence", "BPNSS_Autonomy"]].copy()
d = d.merge(mm[["ID_UP", 8]].rename(columns={8: "single_item"}), on="ID_UP", how="left")  # Self-Reliance
d = d.merge(lm[["ID_UP", "n_hints", "duration_min"]], on="ID_UP", how="left")
dose = ns["dose_df"][["pid", "total_subhints"]].rename(columns={"pid": "ID_UP"})
d = d.merge(dose, on="ID_UP", how="left")
d["single_item"] = pd.to_numeric(d["single_item"], errors="coerce")
d["imp"] = (d["condition"] == "Implícita").astype(int)  # 1 = Implicit, 0 = Explicit

print("N", len(d), " missing:",
      d[["single_item", "IMI_Competence", "BPNSS_Autonomy", "n_hints", "duration_min"]].isna().sum().to_dict())
print("corr totalhints~duration r=%.2f ; totalhints~episodes r=%.2f" % (
    d[["total_subhints", "duration_min"]].corr().iloc[0, 1], d[["total_subhints", "n_hints"]].corr().iloc[0, 1]))
print("total_subhints by cond:", d.groupby("condition")["total_subhints"].agg(["mean", "std"]).round(2).to_dict())
print("hints by cond:", d.groupby("condition")["n_hints"].agg(["mean", "std"]).round(1).to_dict())
print("duration by cond:", d.groupby("condition")["duration_min"].agg(["mean", "std"]).round(2).to_dict())

MODELS = [("raw", "{dv} ~ imp"),
          ("+episodes", "{dv} ~ imp + n_hints"),
          ("+totalhints", "{dv} ~ imp + total_subhints"),
          ("+duration", "{dv} ~ imp + duration_min"),
          ("+totalhints+duration", "{dv} ~ imp + total_subhints + duration_min")]


def run(dv, rank=False):
    x = d[[dv, "imp", "n_hints", "total_subhints", "duration_min"]].dropna().copy()
    if rank:
        x[dv] = x[dv].rank()
    out = []
    for label, formula in MODELS:
        m = smf.ols(formula.format(dv=dv), data=x).fit()
        b, se, p = m.params["imp"], m.bse["imp"], m.pvalues["imp"]
        out.append((label, len(x), b, se, p, b / np.sqrt(m.scale)))
    return out


for dv, rank in [("single_item", False), ("single_item", True), ("BPNSS_Autonomy", False), ("IMI_Competence", False)]:
    print("\n==", dv, "(ranked)" if rank else "")
    for label, n, b, se, p, dd in run(dv, rank):
        print(f"  {label:20s} n={n} Implicit-Explicit b={b:+.3f} (SE {se:.3f})  p={p:.3f}  adj.d={dd:+.2f}")
