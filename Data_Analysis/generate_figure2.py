"""Regenerate Figure 2 (self-reported subscale means by condition) for sigconf.tex,
computed directly from the raw survey CSV via generate_report.py's subscale-scoring
logic -- no manually-transcribed numbers.

Single combined figure: seven grouped-bar panels in one row (Single Item, IMI, BPNSS,
Latency, Wrong-block touches, Performance, Max Length), with a dashed divider between
Wrong-block touches and Performance separating H1-testing measures (left) from
H2-testing measures (right), matching Figure 2's caption/Description in sigconf.tex.

pdf.fonttype is set to 42 (TrueType) rather than the matplotlib default of 3 (bitmap),
so the embedded fonts are proper scalable/searchable outlines instead of Type 3.

Respects the same EXCLUDE_IDS env var as generate_report.py / run_tost.py
(e.g. EXCLUDE_IDS=P31), so re-running a sensitivity check regenerates this figure too.
"""

import os
import runpy
import io
import contextlib

import matplotlib
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
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
perceived_autonomy_result = _ns["perceived_autonomy_result"]
log_results_by_metric = _ns["log_results_by_metric"]

# Trimmed per review comment: Interest/Enjoyment and both Relatedness dimensions are
# manipulation-check-only (not H1 tests), and Pressure/Tension is a downstream consequence
# of the manipulation rather than a direct H1 test -- all three were dropped from the
# figure to make room for the single-item measure and the behavioral H1/H2 proxies below.
# They are still reported in prose/Table S1.
IMI_LABELS = {
    "Perceived\nCompetence": "IMI Perceived Competence",
    "Perceived\nChoice": "IMI Perceived Choice",
}
BPNSS_LABELS = {
    "Autonomy": "BPNSS Autonomy",
    "Competence": "BPNSS Competence",
}


def build_panel_data(label_map):
    data = {}
    for display, key in label_map.items():
        r = full[key]
        sem_imp = r["sd_imp"] / np.sqrt(r["n_imp"])
        sem_exp = r["sd_exp"] / np.sqrt(r["n_exp"])
        low_reliability = r["alpha"] < 0.3
        p = r["p"]
        display_label = display + ("$^\\dagger$" if low_reliability else "")
        data[display_label] = (r["m_imp"], sem_imp, r["m_exp"], sem_exp, p)
    return data


imi = build_panel_data(IMI_LABELS)
bpnss = build_panel_data(BPNSS_LABELS)

# Single-item Perceived Autonomy gets its own panel rather than being folded into BPNSS:
# it's not part of the BPNSS instrument (just a direct, high-power complement to the
# poorly-reliable multi-item Autonomy dimension), and sharing BPNSS's axes/title made it
# read as if it were a BPNSS item.
_r = perceived_autonomy_result
single_item = {
    "Perceived\nAutonomy": (
        _r["m_imp"], _r["sd_imp"] / np.sqrt(_r["n_imp"]),
        _r["m_exp"], _r["sd_exp"] / np.sqrt(_r["n_exp"]),
        _r["p"],
    )
}


def behavioral_panel(metric_key, display_label):
    r = log_results_by_metric[metric_key]
    return {
        display_label: (
            r["m_imp"], r["sd_imp"] / np.sqrt(r["n_imp"]),
            r["m_exp"], r["sd_exp"] / np.sqrt(r["n_exp"]),
            r["p"],
        )
    }


# Behavioral H1 proxies (Section 3.6/5.1): Latency and Wrong-block touches.
latency = behavioral_panel("mean_hint_latency_sec", "Latency")
wrong_block = behavioral_panel("n_touched_wrong", "Wrong-block\ntouches")

# H2 outcome metrics (Section 3.6/5.4): Performance a 0-1 rate, Max Length a
# sequence-length count -- two incompatible scales, so two panels. Trials is NOT an H2
# test (it's an exposure check, alongside Hint episodes/Total hints which aren't in this
# figure at all) and was deliberately dropped here, unlike in Table 1 where it's still
# reported.
performance = {}
performance.update(behavioral_panel("performance_rate_assisted", "Assisted\nPerformance"))
performance.update(behavioral_panel("performance_rate_independent", "Independent\nPerformance"))
max_length = {}
max_length.update(behavioral_panel("max_len_assisted", "Assisted\nMax Length"))
max_length.update(behavioral_panel("max_len_independent", "Independent\nMax Length"))

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
        label="Implicit", zorder=3,
    )
    ax.bar(
        x + width / 2, exp_means, width,
        yerr=exp_se, capsize=4,
        facecolor="white", edgecolor="black", linewidth=1.1,
        hatch="..", label="Explicit",
        error_kw=dict(ecolor="black", elinewidth=1.1, capthick=1.1),
        zorder=3,
    )

    for i, k in enumerate(labels):
        p = data[k][4]
        if p is not None:
            top = max(data[k][0] + data[k][1], data[k][2] + data[k][3]) + (ylim[1] - ylim[0]) * 0.06
            ax.plot(
                [i - width / 2, i - width / 2, i + width / 2, i + width / 2],
                [top - (ylim[1] - ylim[0]) * 0.015, top, top, top - (ylim[1] - ylim[0]) * 0.015],
                color="black", linewidth=0.9, zorder=4,
            )
            p_label = "p<.001" if p < .001 else f"p={p:.3f}"
            ax.text(i, top + (ylim[1] - ylim[0]) * 0.01, p_label, ha="center", va="bottom", fontsize=9.5, zorder=4)

    ax.set_xlim(-0.5, n - 0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9.3)
    ax.set_ylim(*ylim)
    ax.set_yticks(yticks)
    if title:
        ax.set_title(title, fontweight="bold", fontsize=12)
    ax.grid(axis="y", color="0.85", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# --- Single combined figure: 7 panels in one row -------------------------------------
fig, axes = plt.subplots(
    1, 7, figsize=(15.5, 3.6),
    gridspec_kw={"width_ratios": [1.0, 1.5, 1.5, 1.05, 1.05, 1.5, 1.5]},
)
ax_single, ax_imi, ax_bpnss, ax_latency, ax_wrong, ax_perf, ax_maxlen = axes

plot_panel(ax_single, single_item, ylim=(1, 5.9), yticks=[1, 2, 3, 4, 5], title="Single Item")
ax_single.set_ylabel("Mean rating")

plot_panel(ax_imi, imi, ylim=(1, 7.3), yticks=[1, 2, 3, 4, 5, 6, 7], title="IMI")
plot_panel(ax_bpnss, bpnss, ylim=(1, 5.9), yticks=[1, 2, 3, 4, 5], title="BPNSS")

plot_panel(ax_latency, latency, ylim=(0, 19), yticks=[0, 5, 10, 15], title=None)
ax_latency.set_ylabel("Seconds")
plot_panel(ax_wrong, wrong_block, ylim=(0, 2.6), yticks=[0, 1, 2], title=None)
ax_wrong.set_ylabel("Count")
plot_panel(ax_perf, performance, ylim=(0, 0.95), yticks=[0, .25, .5, .75], title=None)
ax_perf.set_ylabel("Rate")
plot_panel(ax_maxlen, max_length, ylim=(0, 5.5), yticks=[0, 2, 4], title=None)
ax_maxlen.set_ylabel("Blocks")

plt.tight_layout(rect=(0, 0.1, 1, 0.94))

# "Behavioral" super-title centered above the four rightmost (behavioral) panels,
# positioned post-layout from actual axes positions.
behav_pos = [a.get_position() for a in (ax_latency, ax_wrong, ax_perf, ax_maxlen)]
behav_x = (behav_pos[0].x0 + behav_pos[-1].x1) / 2
behav_y = max(p.y1 for p in behav_pos) + 0.045
fig.text(behav_x, behav_y, "Behavioral", ha="center", va="bottom", fontweight="bold", fontsize=12)

# Divider line between the H1 cluster (..., Wrong-block touches) and H2 cluster
# (Performance, Max Length), computed post-layout from actual axes positions.
h1_pos = [a.get_position() for a in (ax_single, ax_imi, ax_bpnss, ax_latency, ax_wrong)]
h2_pos = [a.get_position() for a in (ax_perf, ax_maxlen)]
# The divider sits halfway between the right edge of the Wrong-block touches panel and the
# left edge of the Performance panel *including its y-axis tick labels and title*, so it does
# not cross them. The label extents are measured from the rendered figure.
fig.canvas.draw()
_renderer = fig.canvas.get_renderer()
_inv = fig.transFigure.inverted()
_wrong_right = max(h1_pos[-1].x1, ax_wrong.get_tightbbox(_renderer).transformed(_inv).x1)
_perf_left = min(h2_pos[0].x0, ax_perf.get_tightbbox(_renderer).transformed(_inv).x0)
divider_x = (_wrong_right + _perf_left) / 2
top_y = max(p.y1 for p in h1_pos + h2_pos) + 0.05
bottom_y = min(p.y0 for p in h1_pos + h2_pos) - 0.03

fig.add_artist(plt.Line2D(
    [divider_x, divider_x], [bottom_y, top_y],
    color="0.6", linewidth=1, linestyle="--", transform=fig.transFigure,
))

handles, labels_ = ax_single.get_legend_handles_labels()
divider_handle = plt.Line2D([0], [0], color="0.6", linewidth=1, linestyle="--")
handles.append(divider_handle)
labels_.append("Divider: H1 metrics (left) vs. H2 metrics (right)")
fig.legend(handles, labels_, loc="lower center", ncol=3, frameon=True, bbox_to_anchor=(0.5, 0.0))

plt.savefig(OUT_PATH, bbox_inches="tight")
print(f"Saved {OUT_PATH}")

for panel_name, panel in [("Single-item", single_item), ("IMI", imi), ("BPNSS", bpnss),
                           ("Latency", latency), ("Wrong-block touches", wrong_block),
                           ("Performance", performance), ("Max Length", max_length)]:
    for label, (m_i, se_i, m_e, se_e, p) in panel.items():
        print(f"{panel_name} {label!r}: Implicit {m_i:.2f}+/-{se_i:.2f}, Explicit {m_e:.2f}+/-{se_e:.2f}, p={p}")
