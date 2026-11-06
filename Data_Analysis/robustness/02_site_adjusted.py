"""Site-adjusted robustness check for the questionnaire results.

Participants were recruited at three sites. This script adds recruitment site (3 levels) as a
covariate and also tests whether site itself is associated with each measure.

Model: outcome ~ condition  versus  outcome ~ condition + C(site), N = 35.
"Site effect F p" is the F-test of the site terms (model with site vs model without).

DATA NOTE: the per-participant site assignment is NOT included in this repository. With a few
participants per site it could, combined with other fields, support re-identification (see the
README). The script therefore expects a file `participant_site.csv` with columns
`new_id` (participant ID, e.g. P12) and `site` (any label), placed next to this script, or a path
given as the first argument. Without it the script stops with a message.

Run:  python3 02_site_adjusted.py [path/to/participant_site.csv]
"""
import sys
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf

from _pipeline import HERE, load_pipeline

site_path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "participant_site.csv"
if not site_path.exists():
    print(f"[02_site_adjusted] skipped: {site_path.name} not found (withheld for privacy, see the docstring).")
    sys.exit(0)

ns = load_pipeline()
mm, lm, am = ns["manip_merged"], ns["log_merged"], ns["_ancova_merged"]
site = pd.read_csv(site_path)[["new_id", "site"]].rename(columns={"new_id": "ID_UP"})

d = am[["ID_UP", "condition", "IMI_Competence", "BPNSS_Autonomy"]].merge(
    mm[["ID_UP", 8]].rename(columns={8: "single_item"}), on="ID_UP")
d = d.merge(lm[["ID_UP", "duration_min"]], on="ID_UP")
d = d.merge(ns["dose_df"][["pid", "total_subhints"]].rename(columns={"pid": "ID_UP"}), on="ID_UP")
d = d.merge(site, on="ID_UP")
d["single_item"] = pd.to_numeric(d["single_item"])
d["imp"] = (d.condition == "Implícita").astype(int)  # 1 = Implicit

print(pd.crosstab(d.site, d.condition))
for dv in ["single_item", "BPNSS_Autonomy", "IMI_Competence", "total_subhints", "duration_min"]:
    m0 = smf.ols(f"{dv} ~ imp", data=d).fit()
    m1 = smf.ols(f"{dv} ~ imp + C(site)", data=d).fit()
    f = m1.compare_f_test(m0)  # (F, p, df_diff)
    print(f"{dv:16s} cond effect raw b={m0.params['imp']:+.2f} p={m0.pvalues['imp']:.3f} | "
          f"site-adjusted b={m1.params['imp']:+.2f} p={m1.pvalues['imp']:.3f} | site effect F p={f[1]:.3f}")
print(d.groupby("site")[["single_item", "BPNSS_Autonomy", "IMI_Competence"]].mean().round(2))
