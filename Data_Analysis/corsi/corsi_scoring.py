"""Corsi block-tapping scoring.

Score = span of the participant's LAST run: the longest sequence reproduced correctly
in that run (0 if none). The first run included extra help and a demonstration of the
task, so the last run is taken as the real attempt.

Input : corsi_trials_deidentified.csv  (participant, run, length, correct; one row per trial)
Output: corsi_scores_deidentified.csv  (participant, n_runs, first_run_span, last_run_span, best_run_span)
Run   : python3 -I corsi_scoring.py   (from this folder)
"""
import pandas as pd

trials = pd.read_csv("corsi_trials_deidentified.csv")


def run_span(g):
    ok = g.loc[g["correct"] == 1, "length"]
    return int(ok.max()) if len(ok) else 0


rows = []
for pid, g in trials.groupby("participant"):
    spans = [run_span(r) for _, r in g.groupby("run")]
    rows.append(dict(participant=pid, n_runs=len(spans), first_run_span=spans[0],
                     last_run_span=spans[-1], best_run_span=max(spans)))
scores = pd.DataFrame(rows)
scores["_n"] = scores["participant"].str[1:].astype(int)
scores = scores.sort_values("_n").drop(columns="_n")
scores.to_csv("corsi_scores_deidentified.csv", index=False)

s = scores["last_run_span"]
print(f"N={len(s)}  M={s.mean():.2f}  SD={s.std():.2f}  zeros={int((s == 0).sum())} ({(s == 0).mean() * 100:.0f}%)")
