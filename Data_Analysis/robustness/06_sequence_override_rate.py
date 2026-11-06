"""How often did the researcher hold or reset the sequence length?

The game normally advances the sequence length automatically after a successful trial. The
researcher (Wizard) could hold or reset it when the participant appeared to need substantial
help. For each session log, a trial is an "auto-increment opportunity" if the log shows
"[STATE] Auto-incremented sequence length" during that trial; it is "overridden" if the length
of the next sequence is not higher than the current one.

Reported: number of trials, opportunities and overridden opportunities, the override rate over
opportunities and over all trials, overall and by condition.

Input: ../h2_data_for_tost.csv (condition per participant) and
       ../../Elmo_Scripts/logs_deidentified/<ID>.log (one file per session; if there are several
       files for a participant, the last by name length/alphabet is used).

Run:  python3 06_sequence_override_rate.py
"""
import os
import re

import pandas as pd

from _pipeline import DATA_ANALYSIS, LOGS

cond = pd.read_csv(DATA_ANALYSIS / "h2_data_for_tost.csv").set_index("ID_UP")["condition"].map(
    {"Implícita": "Implicit", "Explícita": "Explicit"})
seq_re = re.compile(r"\[SEQUENCE\] Length (\d+):")
auto_re = re.compile(r"\[STATE\] Auto-incremented sequence length to (\d+)")

rows = []
for pid in cond.index:
    candidates = sorted([f for f in os.listdir(LOGS) if f == f"{pid}.log" or re.fullmatch(rf"{pid}_\d+\.log", f)],
                        key=lambda f: (len(f), f))
    if not candidates:
        print("missing", pid)
        continue
    lines = open(LOGS / candidates[-1], encoding="utf-8", errors="replace").readlines()
    trials = [(i, int(m.group(1))) for i, line in enumerate(lines) if (m := seq_re.search(line))]
    n_auto = n_over = 0
    for t in range(len(trials) - 1):
        start, length = trials[t]
        end, next_length = trials[t + 1]
        if any(auto_re.search(line) for line in lines[start:end]):
            n_auto += 1
            if next_length <= length:
                n_over += 1
    rows.append(dict(pid=pid, cond=cond[pid], n_trials=len(trials), n_auto=n_auto, n_over=n_over))

d = pd.DataFrame(rows)
print("participants", len(d))
tot = d[["n_trials", "n_auto", "n_over"]].sum()
print("trials", tot.n_trials, "| auto-increment opportunities", tot.n_auto, "| overridden", tot.n_over,
      "| rate over opportunities %.1f%%" % (100 * tot.n_over / tot.n_auto),
      "| over all trials %.1f%%" % (100 * tot.n_over / tot.n_trials))
for c, g in d.groupby("cond"):
    s = g[["n_trials", "n_auto", "n_over"]].sum()
    print(c, "n=%d" % len(g), "opps", s.n_auto, "overridden", s.n_over, "rate %.1f%%" % (100 * s.n_over / s.n_auto))
