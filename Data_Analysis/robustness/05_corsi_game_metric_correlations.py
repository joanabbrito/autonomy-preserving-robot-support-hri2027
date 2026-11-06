"""Correlations between the Corsi score and the game's behavioral (log) metrics.

Question: is the standard Corsi score related to how participants behaved in the game? The game
differs from the standard task (it requires recalling color as well as position and drops the
order requirement), so weak relations are expected.

Every numeric metric of the session-log table (log_merged) with at least 3 distinct values and
at least 20 observations is correlated with the Corsi score (last-run rule, N = 32), with both
Pearson's r and Spearman's rho. No correction for multiple comparisons is applied; the point is
to show that none is significant. The last line reports the largest |coefficient| and the
smallest p value across metrics.

Run:  python3 05_corsi_game_metric_correlations.py
"""
import pandas as pd
from scipy import stats

from _pipeline import DATA_ANALYSIS, load_pipeline

ns = load_pipeline()
lm = ns["log_merged"]
corsi = pd.read_csv(DATA_ANALYSIS / "corsi" / "corsi_scores_deidentified.csv")
corsi = corsi.rename(columns={"participant": "ID_UP", "last_run_span": "last_correct"})[["ID_UP", "last_correct"]]
d = lm.merge(corsi, on="ID_UP", how="inner")
print("n with Corsi and logs:", len(d))

metrics = [k for k in d.columns
           if k != "last_correct" and pd.api.types.is_numeric_dtype(d[k])
           and d[k].nunique() > 2 and d[k].notna().sum() >= 20]
rows = []
print(f"{'metric':40s} n   pearson r  p     spearman rho  p")
for k in metrics:
    x = d[["last_correct", k]].dropna()
    r, p = stats.pearsonr(x.last_correct, x[k])
    rho, ps = stats.spearmanr(x.last_correct, x[k])
    rows.append((k, len(x), r, p, rho, ps))
    print(f"{k:40s} {len(x):2d}  {r:+.2f}  {p:.3f}   {rho:+.2f}  {ps:.3f}")
print("max |pearson r|: %.2f (min p %.3f) | max |spearman rho|: %.2f (min p %.3f)" % (
    max(abs(r[2]) for r in rows), min(r[3] for r in rows),
    max(abs(r[4]) for r in rows), min(r[5] for r in rows)))
