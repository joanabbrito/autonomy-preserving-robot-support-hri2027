"""Corsi Block Tapping Task: comparison across conditions and relation to the outcomes.

The (computerized) Corsi task was administered in the first session as a coarse proxy of
visuospatial memory capacity. Results are available for 32 of the 35 participants; the data of
three participants were not recorded because of a technical problem.

Score = span of the participant's LAST run (longest sequence reproduced correctly; 0 if none).
The first run included extra help and a demonstration of the task, so the last run is taken as
the real attempt (see corsi/corsi_scoring.py, which produces the scores read here).
For transparency, the best-run rule is also reported.

Analyses (N = 32):
  1. Corsi score by condition (Welch t-test and Mann-Whitney U), last-run and best-run rule.
  2. Spearman correlations of the Corsi score with Self-Reliance, BPNSS Autonomy, IMI Perceived
     Competence, assisted performance rate and assisted max length.
  3. Condition effect on the three questionnaire outcomes with and without the Corsi score as
     a covariate (OLS), on the same 32 participants.
  4. Condition x Corsi interaction (Corsi centered at its mean).
The correlations with all behavioral log metrics are in 05_corsi_game_metric_correlations.py.

Run:  python3 04_corsi_analysis.py
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

from _pipeline import DATA_ANALYSIS, load_pipeline

ns = load_pipeline()
mm, lm, am = ns["manip_merged"], ns["log_merged"], ns["_ancova_merged"]

corsi = pd.read_csv(DATA_ANALYSIS / "corsi" / "corsi_scores_deidentified.csv")
corsi = corsi.rename(columns={"participant": "ID_UP", "last_run_span": "last_correct",
                              "best_run_span": "best_correct"})[["ID_UP", "last_correct", "best_correct"]]

d = am[["ID_UP", "condition", "IMI_Competence", "BPNSS_Autonomy"]].merge(
    mm[["ID_UP", 8]].rename(columns={8: "single_item"}), on="ID_UP").merge(corsi, on="ID_UP", how="left")
d = d.merge(lm[["ID_UP", "performance_rate_assisted", "max_len_assisted"]], on="ID_UP")
d["single_item"] = pd.to_numeric(d["single_item"])
d["imp"] = (d.condition == "Implícita").astype(int)  # 1 = Implicit

x = d.dropna(subset=["last_correct"]).copy()
print("N with Corsi:", len(x), "| missing:", sorted(d.loc[d.last_correct.isna(), "ID_UP"]))
print("Corsi (last run): M=%.2f SD=%.2f, zeros=%d (%.0f%%)" % (
    x.last_correct.mean(), x.last_correct.std(), (x.last_correct == 0).sum(), 100 * (x.last_correct == 0).mean()))

print("\n1. Corsi score by condition")
for label, col in [("last-run rule (used in the paper)", "last_correct"), ("best-run rule", "best_correct")]:
    a = x.loc[x.imp == 1, col]
    b = x.loc[x.imp == 0, col]
    pooled = np.sqrt(((len(a) - 1) * a.var() + (len(b) - 1) * b.var()) / (len(a) + len(b) - 2))
    print(f"{label}: Implicit M={a.mean():.2f} (SD {a.std():.2f}, n={len(a)}, zeros={(a == 0).sum()}) vs "
          f"Explicit M={b.mean():.2f} (SD {b.std():.2f}, n={len(b)}, zeros={(b == 0).sum()}); "
          f"Welch p={stats.ttest_ind(a, b, equal_var=False).pvalue:.3f} d={(a.mean() - b.mean()) / pooled:+.2f}; "
          f"MWU p={stats.mannwhitneyu(a, b).pvalue:.3f}")

print("\n2. Spearman correlations of Corsi (last run) with outcomes, n=%d" % len(x))
for col in ["single_item", "BPNSS_Autonomy", "IMI_Competence", "performance_rate_assisted", "max_len_assisted"]:
    rho, p = stats.spearmanr(x.last_correct, x[col])
    print(f"  {col:26s} rho={rho:+.2f} p={p:.3f}")

print("\n3. Condition effect (Implicit - Explicit) without and with the Corsi score, n=%d" % len(x))
for dv in ["single_item", "BPNSS_Autonomy", "IMI_Competence"]:
    m0 = smf.ols(f"{dv} ~ imp", data=x).fit()
    m1 = smf.ols(f"{dv} ~ imp + last_correct", data=x).fit()
    print(f"  {dv:16s} unadj b={m0.params['imp']:+.2f} p={m0.pvalues['imp']:.3f} | "
          f"+Corsi b={m1.params['imp']:+.2f} p={m1.pvalues['imp']:.3f}")

print("\n4. Condition x Corsi interaction (Corsi centered at its mean %.2f), n=%d" % (x.last_correct.mean(), len(x)))
x["corsi_c"] = x.last_correct - x.last_correct.mean()
for dv in ["single_item", "BPNSS_Autonomy", "IMI_Competence"]:
    m = smf.ols(f"{dv} ~ imp * corsi_c", data=x).fit()
    print(f"  {dv:16s} interaction b={m.params['imp:corsi_c']:+.3f} (SE {m.bse['imp:corsi_c']:.3f}) "
          f"p={m.pvalues['imp:corsi_c']:.3f}")
