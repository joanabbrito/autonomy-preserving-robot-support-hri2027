"""Manipulation check: handling of the participant who answered negatively to the gate item.

The manipulation check had five items. Item 1 ("the robot gave me hints") gated items 2 to 5.
One Explicit participant answered negatively to item 1; their interview described receiving
and reacting to hints, so they were retained in all analyses but removed from the gated items
2 to 5 (generate_report.py, GATE_EXCLUDED_ID). This script shows that the choice does not change
the conclusions.

Part A: items 1 to 5 by condition (Mann-Whitney U, rank-biserial r) with the participant
        removed from items 2 to 5 (as reported) and with them included.
Part B: the questionnaire results with the participant excluded from the whole pipeline
        (EXCLUDE_IDS) compared with the full sample.

Run:  python3 07_manipulation_check_sensitivity.py
"""
import pandas as pd
from scipy import stats

from _pipeline import load_pipeline

ns = load_pipeline()
mm, gate_id = ns["manip_merged"], ns["GATE_EXCLUDED_ID"]
r = mm[mm["ID_UP"] == gate_id]
print("participant removed from the gated items: condition =", r["condition"].tolist(),
      "| answers to items 1-5 and the single item:", r[[3, 4, 5, 6, 7, 8]].values.tolist())

print("\nPart A: manipulation check items by condition")
for col, name in zip([3, 4, 5, 6, 7], ["1 gate", "2 explicit", "3 subtle", "4 told directly", "5 looked at block"]):
    print(name)
    for removed in (True, False):
        v = pd.to_numeric(mm[col], errors="coerce")
        mask = (mm["ID_UP"] != gate_id) if (removed and col != 3) else pd.Series(True, index=mm.index)
        i = v[(mm["condition"] == "Implícita") & mask].dropna()
        e = v[(mm["condition"] == "Explícita") & mask].dropna()
        u = stats.mannwhitneyu(i, e, alternative="two-sided")
        rb = 2 * u.statistic / (len(i) * len(e)) - 1
        print(f"   {'participant removed' if removed else 'participant included':20s} nI={len(i)} nE={len(e)} "
              f"MI={i.mean():.2f}+/-{i.std() / len(i) ** .5:.2f} ME={e.mean():.2f}+/-{e.std() / len(e) ** .5:.2f} "
              f"U={u.statistic:.1f} p={u.pvalue:.3g} r={rb:.2f}")

print("\nPart B: questionnaire results, full sample vs participant excluded from the whole pipeline")
for label, excl in (("full sample", ""), ("excluding " + gate_id, gate_id)):
    ns_ = load_pipeline(excl)
    full, pa = ns_["full"], ns_["perceived_autonomy_result"]
    print(f"{label}: Self-Reliance n={pa['n_imp']}/{pa['n_exp']} p={pa['p']:.5f}")
    for k in ["BPNSS Autonomy", "BPNSS Competence", "IMI Perceived Competence", "IMI Perceived Choice"]:
        q = full[k]
        print(f"   {k:26s} n={q['n_imp']}/{q['n_exp']} Implicit {q['m_imp']:.2f} Explicit {q['m_exp']:.2f} "
              f"p={q['p']:.3f} alpha={q['alpha']:.2f}")
