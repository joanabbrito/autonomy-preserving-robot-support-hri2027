"""Regenerate Figure 2 (self-reported subscale means by condition) for sigconf.tex,
computed directly from the raw survey CSV via generate_report.py's subscale-scoring
logic -- no manually-transcribed numbers.

Respects the same EXCLUDE_IDS env var as generate_report.py / run_tost.py / final_stats.py
(e.g. EXCLUDE_IDS=P31), so re-running a sensitivity check regenerates this figure too.
"""

import os
import runpy
import io
import contextlib

import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "self_report_subscales.pdf")

# Suppress generate_report.py's own stdout/report-file side effects' noise here;
# it still writes Preliminary_Analysis_Report*.md and h2_data_for_tost*.csv as normal.
_buf = io.StringIO()
with contextlib.redirect_stdout(_buf):
    _ns = runpy.run_path(os.path.join(HERE, "generate_report.py"), run_name="not_main_guard_needed")

full = _ns["full"]

IMI_LABELS = {
    "Interest/\nEnjoyment": "IMI Interest/Enjoyment",
    "Perceived\nCompetence": "IMI Perceived Competence",
    "Perceived\nChoice": "IMI Perceived Choice",
    "Pressure/\nTension": "IMI Pressure/Tension",
    "Relatedness\n(robot)": "IMI Relatedness (robot)",
}
BPNSS_LABELS = {
    "Autonomy": "BPNSS Autonomy",
    "Competence": "BPNSS Competence",
    "Relatedness": "BPNSS Relatedness",
}


# Bracketed with its p-value in the figure specifically because these are the two
# dimensions the Results/Discussion text discusses by name (BPNSS Autonomy p=.061,
# IMI Perceived Competence p=.107) -- not a blanket numeric cutoff, since a fixed
# p<.10 threshold would silently drop Perceived Competence despite it being the
# paper's own headline H1 signal.
HIGHLIGHTED_KEYS = {"BPNSS Autonomy", "IMI Perceived Competence"}


def build_panel_data(label_map):
    data = {}
    for display, key in label_map.items():
        r = full[key]
        sem_imp = r["sd_imp"] / np.sqrt(r["n_imp"])
        sem_exp = r["sd_exp"] / np.sqrt(r["n_exp"])
        low_reliability = r["alpha"] < 0.3
        p = r["p"] if key in HIGHLIGHTED_KEYS else None
        display_label = display + ("$^\\dagger$" if low_reliability else "")
        data[display_label] = (r["m_imp"], sem_imp, r["m_exp"], sem_exp, p, low_reliability)
    return data


imi = build_panel_data(IMI_LABELS)
bpnss = build_panel_data(BPNSS_LABELS)

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.size"] = 11
plt.rcParams["hatch.linewidth"] = 0.6


def plot_panel(ax, data, ylim, yticks, title):
    labels = list(data.keys())
    n = len(labels)
    x = np.arange(n)
    width = 0.32

    imp_means = [data[k][0] for k in labels]
    imp_se = [data[k][1] for k in labels]
    exp_means = [data[k][2] for k in labels]
    exp_se = [data[k][3] for k in labels]

    ax.bar(
        x - width / 2, imp_means, width,
        yerr=imp_se, capsize=4,
        facecolor="white", edgecolor="black", linewidth=1.1,
        error_kw=dict(ecolor="black", elinewidth=1.1, capthick=1.1),
        label="Implicit",
    )
    ax.bar(
        x + width / 2, exp_means, width,
        yerr=exp_se, capsize=4,
        facecolor="white", edgecolor="black", linewidth=1.1,
        hatch="..", label="Explicit",
        error_kw=dict(ecolor="black", elinewidth=1.1, capthick=1.1),
    )

    for i, k in enumerate(labels):
        p = data[k][4]
        if p is not None:
            top = max(data[k][0] + data[k][1], data[k][2] + data[k][3]) + (ylim[1] - ylim[0]) * 0.06
            ax.plot(
                [i - width / 2, i - width / 2, i + width / 2, i + width / 2],
                [top - (ylim[1] - ylim[0]) * 0.015, top, top, top - (ylim[1] - ylim[0]) * 0.015],
                color="black", linewidth=0.9,
            )
            ax.text(i, top + (ylim[1] - ylim[0]) * 0.01, f"p={p:.3f}", ha="center", va="bottom", fontsize=9.5)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9.3)
    ax.set_ylim(*ylim)
    ax.set_yticks(yticks)
    ax.set_title(title, fontweight="bold", fontsize=12)
    ax.grid(axis="y", color="0.85", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


fig, axes = plt.subplots(1, 2, figsize=(11.5, 3.97))

plot_panel(axes[0], imi, ylim=(1, 7.3), yticks=[2, 4, 6], title="IMI")
axes[0].set_ylabel("Mean rating")

plot_panel(axes[1], bpnss, ylim=(1, 5.5), yticks=[1, 2, 3, 4, 5], title="BPNSS")

handles, labels_ = axes[0].get_legend_handles_labels()
fig.legend(handles, labels_, loc="lower center", ncol=2, frameon=True, bbox_to_anchor=(0.5, -0.05))

plt.tight_layout()
plt.savefig(OUT_PATH, bbox_inches="tight")
print(f"Saved {OUT_PATH}")
for panel_name, panel in [("IMI", imi), ("BPNSS", bpnss)]:
    for label, (m_i, se_i, m_e, se_e, p, dagger) in panel.items():
        print(f"{panel_name} {label!r}: Implicit {m_i:.2f}+/-{se_i:.2f}, Explicit {m_e:.2f}+/-{se_e:.2f}, "
              f"p={p}, low_reliability={dagger}")
