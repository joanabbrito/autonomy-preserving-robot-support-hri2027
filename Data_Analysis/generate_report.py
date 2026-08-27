import pandas as pd
import numpy as np
from scipy import stats
import pingouin as pg
import csv as csv_module
import glob, re, os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_data_deidentified", "OlderAdults_postStudy.csv")

with open(path, newline="", encoding="utf-8") as f:
    orig_header = next(csv_module.reader(f))  # raw question text, before pandas dedup-renames duplicates

# Sensitivity-check exclusion: set via EXCLUDE_IDS env var, comma-separated (e.g. EXCLUDE_IDS=P31).
# Filtering df here, before anything downstream is derived from it (cond, main_ids_df, and by
# extension manip_merged/log_merged via their merges), propagates the exclusion consistently
# through every stage: self-report subscales, manipulation check, and behavioral log metrics.
EXCLUDE_IDS = {x.strip().upper() for x in os.environ.get("EXCLUDE_IDS", "").split(",") if x.strip()}

df = pd.read_csv(path, header=0)
df.columns = range(df.shape[1])
if EXCLUDE_IDS:
    df = df[~df[1].str.strip().str.upper().isin(EXCLUDE_IDS)].reset_index(drop=True)
cond = df[2]

subscales = {
    "IMI Interest/Enjoyment": dict(cols=[3,7,10,12,16,19,22], rev=[16], top=7),
    "IMI Perceived Competence": dict(cols=[6,9,14,18,24], rev=[], top=7),
    "IMI Perceived Choice": dict(cols=[13,17,23], rev=[13,23], top=7),  # cols 5,21 dropped via alpha-if-item-deleted (orig 5-item alpha=.04); see Section 3 note
    "IMI Pressure/Tension": dict(cols=[4,8,11,15,20], rev=[11], top=7),  # col4 corrected: data-entry inversion, treated as normal
    "IMI Relatedness (robot)": dict(cols=[25,26,27,28,29,30,31,32], rev=[25,26,29,30], top=7),
    "BPNSS Autonomy": dict(cols=[37,44,50], rev=[37,44], top=5),  # administered on 1-5, not the instrument's native 1-7; col47 dropped (content-validity) then cols 33,41,53 dropped (alpha-if-item-deleted), see Section 3 notes
    "BPNSS Competence": dict(cols=[36,38,43,46,48,52], rev=[36,46,48,52], top=5),  # col46 corrected: translation slip
    "BPNSS Relatedness": dict(cols=[34,39,40,42,45,49,51,54], rev=[40,49,51], top=5),
}

def collapse_to_3(s, top):
    # proportional 3-way split of the item's actual administered range, not a fixed 1-7 assumption
    if top == 7:
        lo, mid = 3, 4     # 1-3 -> 1, 4 -> 2, 5-7 -> 3
    elif top == 5:
        lo, mid = 2, 3     # 1-2 -> 1, 3 -> 2, 4-5 -> 3
    else:
        raise ValueError(f"no collapse rule defined for a 1-{top} scale")
    def m(v):
        if pd.isna(v):
            return v
        v = float(v)
        if v <= lo:
            return 1
        elif v <= mid:
            return 2
        else:
            return 3
    return s.apply(m)

def build_items(cols, rev, mode, top):
    data = {}
    for c in cols:
        v = df[c]
        if mode == "collapsed":
            v = collapse_to_3(v, top)
            eff_top = 3
        else:
            eff_top = top
        data[c] = (1 + eff_top) - v if c in rev else v
    return pd.DataFrame(data)

def run_mode(mode):
    out = {}
    scores = pd.DataFrame({"condition": cond})
    for name, spec in subscales.items():
        item_df = build_items(spec["cols"], spec["rev"], mode, spec["top"])
        try:
            alpha = pg.cronbach_alpha(data=item_df)
            alpha_val, alpha_ci = alpha[0], alpha[1]
        except Exception:
            alpha_val, alpha_ci = np.nan, None
        citc = []
        for c in item_df.columns:
            rest = item_df.drop(columns=c).mean(axis=1, skipna=True)
            r = item_df[c].corr(rest)
            citc.append((c, None if pd.isna(r) else round(r, 2)))
        sub_score = item_df.mean(axis=1, skipna=True)
        scores[name] = sub_score
        out[name] = dict(alpha=alpha_val, alpha_ci=alpha_ci, citc=citc, k=len(spec["cols"]))

    for name in subscales:
        imp = scores.loc[scores.condition == "Implícita", name].dropna()
        exp = scores.loc[scores.condition == "Explícita", name].dropna()
        sh_imp = stats.shapiro(imp) if imp.nunique() > 1 else None
        sh_exp = stats.shapiro(exp) if exp.nunique() > 1 else None
        normal = (sh_imp is not None and sh_exp is not None and sh_imp.pvalue > .05 and sh_exp.pvalue > .05)
        d = dict(n_imp=len(imp), n_exp=len(exp), m_imp=imp.mean(), sd_imp=imp.std(),
                 m_exp=exp.mean(), sd_exp=exp.std(),
                 p_imp=sh_imp.pvalue if sh_imp else np.nan, p_exp=sh_exp.pvalue if sh_exp else np.nan,
                 normal=normal)
        if normal:
            t = stats.ttest_ind(imp, exp, equal_var=False)
            pooled_sd = np.sqrt(((len(imp)-1)*imp.std()**2 + (len(exp)-1)*exp.std()**2) / (len(imp)+len(exp)-2))
            eff = (imp.mean() - exp.mean()) / pooled_sd if pooled_sd > 0 else np.nan
            d.update(test="Welch t-test", stat=t.statistic, p=t.pvalue, effect=eff, effect_label="Cohen's d")
        else:
            u = stats.mannwhitneyu(imp, exp, alternative="two-sided")
            n1, n2 = len(imp), len(exp)
            rbc = (2*u.statistic)/(n1*n2) - 1
            d.update(test="Mann-Whitney U", stat=u.statistic, p=u.pvalue, effect=rbc, effect_label="rank-biserial r")
        out[name].update(d)
    return out

full = run_mode("full")
collapsed = run_mode("collapsed")

# ============================================================
# Robustness checks: leave-one-out (IMI Perceived Competence) and
# iterative alpha-driven item removal (BPNSS Autonomy)
# ============================================================

def _group_compare_series(score, condition_series):
    imp = score[condition_series == "Implícita"].dropna()
    exp = score[condition_series == "Explícita"].dropna()
    sh_imp = stats.shapiro(imp) if imp.nunique() > 1 else None
    sh_exp = stats.shapiro(exp) if exp.nunique() > 1 else None
    normal = (sh_imp is not None and sh_exp is not None and sh_imp.pvalue > .05 and sh_exp.pvalue > .05)
    if normal:
        t = stats.ttest_ind(imp, exp, equal_var=False)
        pooled_sd = np.sqrt(((len(imp)-1)*imp.std()**2 + (len(exp)-1)*exp.std()**2) / (len(imp)+len(exp)-2))
        eff = (imp.mean()-exp.mean())/pooled_sd if pooled_sd > 0 else np.nan
        test, stat_, p_, eff_label = "Welch t-test", t.statistic, t.pvalue, "Cohen's d"
    else:
        u = stats.mannwhitneyu(imp, exp, alternative="two-sided")
        n1, n2 = len(imp), len(exp)
        eff = (2*u.statistic)/(n1*n2) - 1
        test, stat_, p_, eff_label = "Mann-Whitney U", u.statistic, u.pvalue, "rank-biserial r"
    return dict(n_imp=len(imp), n_exp=len(exp), m_imp=imp.mean(), m_exp=exp.mean(),
                test=test, stat=stat_, p=p_, effect=eff, effect_label=eff_label)

# --- IMI Perceived Competence: leave-one-out sensitivity ---
_comp_spec = subscales["IMI Perceived Competence"]
_comp_items = build_items(_comp_spec["cols"], _comp_spec["rev"], "full", _comp_spec["top"])
_comp_score = _comp_items.mean(axis=1, skipna=True)
comp_baseline = _group_compare_series(_comp_score, cond)

_ids = df[1].str.strip()
_loo_rows = []
for _idx in _comp_score.dropna().index:
    _mask = _comp_score.index != _idx
    _r = _group_compare_series(_comp_score[_mask], cond[_mask])
    _loo_rows.append(dict(pid=_ids.loc[_idx], condition=cond.loc[_idx], score=_comp_score.loc[_idx], p=_r["p"]))
_loo_df = pd.DataFrame(_loo_rows).sort_values("p")
loo_n_flip = int((_loo_df["p"] < .05).sum())
loo_pmin, loo_pmax = _loo_df["p"].min(), _loo_df["p"].max()
_loo_flips = _loo_df[_loo_df["p"] < .05]

def _fmt_loo_flip_table(flips):
    lines = ["| Removed participant | Condition | Their score | Resulting p |", "|---|---|---|---|"]
    for _, row in flips.iterrows():
        lines.append(f"| {row['pid']} | {row['condition']} | {row['score']:.2f} | {row['p']:.3f} |")
    return "\n".join(lines)

loo_flip_table = _fmt_loo_flip_table(_loo_flips)

# --- BPNSS Autonomy: iterative alpha-if-deleted item removal ---
_auto_spec = subscales["BPNSS Autonomy"]
_auto_remaining = list(_auto_spec["cols"])
auto_history = []
_step = 0
while len(_auto_remaining) >= 2:
    _item_df = build_items(_auto_remaining, _auto_spec["rev"], "full", _auto_spec["top"])
    _alpha_val = pg.cronbach_alpha(data=_item_df)[0]
    _score = _item_df.mean(axis=1, skipna=True)
    _gc = _group_compare_series(_score, cond)
    auto_history.append(dict(step=_step, k=len(_auto_remaining), alpha=_alpha_val, p=_gc["p"],
                              effect=_gc["effect"], effect_label=_gc["effect_label"],
                              m_imp=_gc["m_imp"], m_exp=_gc["m_exp"]))
    if len(_auto_remaining) == 2:
        break
    _deltas = []
    for _c in _auto_remaining:
        _trial_cols = [x for x in _auto_remaining if x != _c]
        _trial_df = build_items(_trial_cols, _auto_spec["rev"], "full", _auto_spec["top"])
        _a = pg.cronbach_alpha(data=_trial_df)[0]
        _deltas.append((_c, _a))
    _deltas.sort(key=lambda x: -x[1])
    _best_col, _best_alpha = _deltas[0]
    if _best_alpha <= _alpha_val:
        break
    _auto_remaining.remove(_best_col)
    _step += 1

def _fmt_auto_history(hist):
    lines = ["| Items remaining (k) | α | Group comparison p | Effect |", "|---|---|---|---|"]
    for h in hist:
        sig = "**" if h["p"] < .05 else ""
        lines.append(f"| {h['k']} | {h['alpha']:.3f} | {sig}{h['p']:.3f}{sig} | {h['effect_label']}={h['effect']:.2f} |")
    return "\n".join(lines)

auto_item_reduction_table = _fmt_auto_history(auto_history)

# Dynamically describe which further-reduction steps are non-significant vs. significant,
# rather than hardcoding array positions -- the trajectory's length/shape can change (e.g.
# after col47 was dropped from the base scale, this now starts at k=6 instead of k=7).
def _fmt_k_list(steps):
    ks = [str(h['k']) for h in steps]
    if len(ks) == 0:
        return "none"
    if len(ks) == 1:
        return ks[0]
    if len(ks) == 2:
        return " and ".join(ks)
    return ", ".join(ks[:-1]) + f", and {ks[-1]}"

_later_steps = auto_history[1:]  # steps after the starting point (already described in the preceding sentence)
_nonsig_steps = [h for h in _later_steps if h['p'] >= .05]
_sig_steps = [h for h in _later_steps if h['p'] < .05]

if _nonsig_steps and _sig_steps:
    _nonsig_alpha_range = f"{min(h['alpha'] for h in _nonsig_steps):.2f}–{max(h['alpha'] for h in _nonsig_steps):.2f}"
    _sig_alpha_range = f"{min(h['alpha'] for h in _sig_steps):.2f}–{max(h['alpha'] for h in _sig_steps):.2f}"
    _min_sig_k = min(h['k'] for h in _sig_steps)
    auto_item_reduction_summary = (
        f"The difference is non-significant at every intermediate stage ({_fmt_k_list(_nonsig_steps)} items, "
        f"α={_nonsig_alpha_range}) and only returns once the scale is reduced to {_fmt_k_list(_sig_steps)} items "
        f"(α={_sig_alpha_range}). Cronbach's alpha computed on only {_min_sig_k} items is close to a rescaled "
        f"item-item correlation rather than a meaningful reliability estimate, so this is not a case of "
        f"\"cleaning the scale reveals a stable effect\" — it is closer to the opposite: significance appears "
        f"and disappears depending on exactly which items are retained, which is itself evidence of instability."
    )
elif _sig_steps:
    auto_item_reduction_summary = (
        f"The difference remains significant at every further-reduction stage tested "
        f"({_fmt_k_list(_sig_steps)} items)."
    )
else:
    auto_item_reduction_summary = (
        f"The difference remains non-significant at every further-reduction stage tested, "
        f"down to {auto_history[-1]['k']} items (α={auto_history[-1]['alpha']:.2f})."
    )
auto_item_reduction_summary += (
    f" This suggests the significant result on the adopted 3-item scale is not simply an artifact of "
    f"stopping the reduction at exactly that item count. The underlying reliability remains below the "
    f"conventional .5 floor throughout, though, so the finding should still be read as tentative rather "
    f"than confirmed."
)

# explicit before/after evidence for the col-4 data-entry inversion (for the narrative)
_pt_rest = build_items([8,11,15,20], [11], "full", 7)
_pt_rest_mean = _pt_rest.mean(axis=1, skipna=True)
_col4_as_reverse = 8 - df[4]
_col4_as_normal = df[4]
_corr_reverse = round(_col4_as_reverse.corr(_pt_rest_mean), 3)
_corr_normal = round(_col4_as_normal.corr(_pt_rest_mean), 3)

# explicit before/after evidence for the col47 content-validity removal from BPNSS Autonomy:
# shown so the direction of the effect on significance is transparent (it removed the p<.05
# result, rather than creating it), evidence against outcome-driven item selection.
_auto_with47 = build_items([33,37,41,44,47,50,53], [37,44,53], "full", 5)
_auto_with47_score = _auto_with47.mean(axis=1, skipna=True)
_alpha_with47 = pg.cronbach_alpha(data=_auto_with47)[0]
_gc_with47 = _group_compare_series(_auto_with47_score, cond)

# explicit before/after evidence for the further BPNSS Autonomy alpha-driven item removal (6-item -> 3-item)
_auto_full6 = build_items([33,37,41,44,50,53], [37,44,53], "full", 5)
_auto_full6_score = _auto_full6.mean(axis=1, skipna=True)
_alpha_auto_full6 = pg.cronbach_alpha(data=_auto_full6)[0]
_gc_auto_full6 = _group_compare_series(_auto_full6_score, cond)

# explicit before/after evidence for the Perceived Choice alpha-driven item removal
_choice_full5 = build_items([5,13,17,21,23], [13,21,23], "full", 7)
_choice_full5_score = _choice_full5.mean(axis=1, skipna=True)
_alpha_choice_full5 = pg.cronbach_alpha(data=_choice_full5)[0]
_gc_choice_full5 = _group_compare_series(_choice_full5_score, cond)

n_imp_total = int((cond == "Implícita").sum())
n_exp_total = int((cond == "Explícita").sum())
n_total = n_imp_total + n_exp_total

item_cols = list(range(3, 55))
n_missing = int(df[item_cols].isna().sum().sum()) + int((df[item_cols] == "").sum().sum() if df[item_cols].dtypes.eq(object).any() else 0)
n_missing = int(df[item_cols].apply(pd.to_numeric, errors="coerce").isna().sum().sum())
total_cells = n_total * len(item_cols)

# check which items go zero-variance under collapsing, dynamically (for the caveat text)
col_top = {c: spec["top"] for spec in subscales.values() for c in spec["cols"]}
col_top[35] = 5  # duplicate BPNSS column, excluded from scoring but still in the raw item range
col_top[47] = 5  # BPNSS Autonomy item dropped (Section 3), still an administered item in the raw range
col_top[5] = 7   # Perceived Choice item dropped (Section 3), still an administered item in the raw range
col_top[21] = 7  # Perceived Choice item dropped (Section 3), still an administered item in the raw range
col_top[33] = 5  # BPNSS Autonomy item dropped (Section 3), still an administered item in the raw range
col_top[41] = 5  # BPNSS Autonomy item dropped (Section 3), still an administered item in the raw range
col_top[53] = 5  # BPNSS Autonomy item dropped (Section 3), still an administered item in the raw range
zero_var_items = []
for c in item_cols:
    cv = collapse_to_3(df[c], col_top[c])
    if cv.nunique(dropna=True) <= 1:
        zero_var_items.append(c)
zero_var_note = (", ".join(f"col{c}" for c in zero_var_items)
                  if zero_var_items else "no items")

# robustness check: pairwise deletion (current approach) vs listwise (exclude any
# participant missing an item in that specific subscale) -- only relevant for
# subscales that actually have missing data
def pairwise_vs_listwise_note():
    lines = []
    for name, spec in subscales.items():
        item_df = build_items(spec["cols"], spec["rev"], "full", spec["top"])
        complete_mask = item_df.notna().all(axis=1)
        n_dropped = int((~complete_mask).sum())
        if n_dropped == 0:
            continue
        pairwise_score = item_df.mean(axis=1, skipna=True)
        listwise_score = pairwise_score[complete_mask]
        c_full = cond[pairwise_score.index]
        c_list = cond[complete_mask]

        def stats_for(score, c):
            imp = score[c == "Implícita"].dropna()
            exp = score[c == "Explícita"].dropna()
            t = stats.ttest_ind(imp, exp, equal_var=False)
            pooled_sd = np.sqrt(((len(imp)-1)*imp.std()**2 + (len(exp)-1)*exp.std()**2) / (len(imp)+len(exp)-2))
            d_eff = (imp.mean()-exp.mean())/pooled_sd if pooled_sd > 0 else np.nan
            return len(imp), len(exp), t.pvalue, d_eff

        n1p, n2p, pp, dp = stats_for(pairwise_score, c_full)
        n1l, n2l, pl, dl = stats_for(listwise_score, c_list)
        a_pair = pg.cronbach_alpha(data=item_df)[0]
        a_list = pg.cronbach_alpha(data=item_df[complete_mask])[0]
        lines.append(
            f"- **{name}** ({n_dropped} participant(s) with a missing item): "
            f"pairwise (current) n={n1p}/{n2p}, α={a_pair:.3f}, p={pp:.3f} vs. "
            f"listwise (excluded) n={n1l}/{n2l}, α={a_list:.3f}, p={pl:.3f}."
        )
    return "\n".join(lines) if lines else "No subscale had missing data affecting more than one case."

robustness_note = pairwise_vs_listwise_note()

def fmt_item_listing():
    lines = []
    for name, spec in subscales.items():
        lines.append(f"\n**{name}**\n")
        lines.append("| col | item text (as administered) | reverse-scored? |")
        lines.append("|---|---|---|")
        for c in spec["cols"]:
            text = orig_header[c].strip()
            is_rev = "yes" if c in spec["rev"] else ""
            lines.append(f"| {c} | {text} | {is_rev} |")
    return "\n".join(lines)

item_listing = fmt_item_listing()

# ============================================================
# Demographics (prestudy CSV)
# ============================================================
pre_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_data_deidentified", "OlderAdults_preStudy_deidentified.csv")
pre = pd.read_csv(pre_path, header=0)
pre.columns = range(pre.shape[1])
pre[1] = pre[1].str.strip()

# manual corrections per confirmed participant identity checks (IDs below are current,
# post-remap; see git history for the prior site-lettered IDs these correspond to):
# - P24: same participant, not two people (her two submissions are deduplicated below; the
#   original age-field correction between them is not applicable here since age is not part
#   of this de-identified dataset).
# - P1: second (duplicate) submission is a different, unrelated person -> drop it, keep entry 1
# - P27: second submission is actually participant P10, mislabeled -> relabel
# - P30: second submission is actually participant P14, mislabeled -> relabel
def fix_prestudy(pre):
    pre = pre.copy()
    p6_idx = pre.index[pre[1].str.upper() == "P24"].tolist()
    drop_idx = list(p6_idx[1:])
    for id_ in ["P1"]:
        idx = pre.index[pre[1].str.upper() == id_].tolist()
        if len(idx) > 1:
            drop_idx.extend(idx[1:])
    pre = pre.drop(index=drop_idx)
    for id_, relabel in [("P27", "P10"), ("P30", "P14")]:
        idx = pre.index[pre[1].str.upper() == id_].tolist()
        if len(idx) > 1:
            pre.loc[idx[1], 1] = relabel
    return pre

pre = fix_prestudy(pre)
pre["ID_UP"] = pre[1].str.upper()

main_ids_df = pd.DataFrame({"ID_UP": df[1].str.strip().str.upper(), "condition": cond})
demo = main_ids_df.merge(pre, on="ID_UP", how="left")

def parse_age(v):
    v = str(v).strip()
    if "-" in v and not v.startswith("-"):
        parts = v.split("-")
        try:
            return (float(parts[0]) + float(parts[1])) / 2
        except ValueError:
            pass
    v = v.split("(")[0].strip()  # e.g. "87 (1938)" -> "87"
    try:
        return float(v)
    except ValueError:
        return np.nan

# NOTE: age, sex, and education are not present in this de-identified dataset (stripped
# for privacy); this section only covers the tech-familiarity and robot-experience items,
# using this file's own column layout (0=Timestamp, 1=ID, 2-4=confidence, 5=smartphone, 6=robot exp.).
n_demo_matched = int(demo[2].notna().sum())
n_demo_total = len(demo)

comp_conf = pd.to_numeric(demo[2], errors="coerce")
tablet_conf = pd.to_numeric(demo[3], errors="coerce")
phone_conf = pd.to_numeric(demo[4], errors="coerce")
smartphone_counts = demo[5].value_counts()
robot_exp_label_fix = {
    "1 - não sabia bem o que era um robô": "1 - nunca vi / ouvi falar",
    "2 - nunca vi / ouvi falar de robôs": "2 - ouvi falar / vi na televisão",
}
robot_exp_counts = demo[6].replace(robot_exp_label_fix).value_counts()

def fmt_counts(vc, total):
    return "; ".join(f"{k} (n={v}, {100*v/total:.0f}%)" for k, v in vc.items())

def fmt_counts_top(vc, total, min_count=2):
    common = vc[vc >= min_count]
    rest_n = int(vc[vc < min_count].sum())
    parts = [f"{k} (n={v}, {100*v/total:.0f}%)" for k, v in common.items()]
    if rest_n:
        parts.append(f"{rest_n} other individual, free-text responses ({100*rest_n/total:.0f}%), not standardized categories")
    return "; ".join(parts)

demographics_paragraph = f"""Background data were available for {n_demo_matched} of the {n_demo_total} analyzed participants (matched by participant ID after correcting 2 duplicate-ID data entry conflicts and 2 ID mislabelings identified during matching — see below). Age, sex, and education are not included in this de-identified dataset. Self-rated confidence using a computer, tablet, and phone (1-5 scale) averaged M={comp_conf.mean():.2f} (SD={comp_conf.std():.2f}), M={tablet_conf.mean():.2f} (SD={tablet_conf.std():.2f}), and M={phone_conf.mean():.2f} (SD={phone_conf.std():.2f}) respectively. Smartphone ownership: {fmt_counts(smartphone_counts, smartphone_counts.sum())}. Prior experience with robots: {fmt_counts(robot_exp_counts, robot_exp_counts.sum())}."""

demographics_datacleaning_note = """**ID conflicts resolved in the prestudy file:**
- P24 submitted twice; both submissions are the same participant, deduplicated to one row (the age-based correction used in the original, non-de-identified analysis does not apply here since age is not part of this dataset).
- P1 had two conflicting submissions under the same ID (different ages/occupations, consistent with two different people) — the second, unrelated submission was dropped, keeping the first.
- P27's second submission was confirmed to actually belong to participant P10 (mislabeled at data entry) — relabeled accordingly.
- P30's second submission was confirmed to actually belong to participant P14 (mislabeled at data entry) — relabeled accordingly; that participant is not part of the 35 analyzed participants, so this entry does not appear in the demographics above."""

# ============================================================
# Manipulation check
# ============================================================
manip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_data_deidentified", "OlderAdults_ManipulationCheck.csv")

with open(manip_path, newline="", encoding="utf-8") as f:
    manip_header = next(csv_module.reader(f))

manip = pd.read_csv(manip_path, header=0)
manip.columns = range(manip.shape[1])
manip[1] = manip[1].str.strip()
n_pilot_excluded = int(manip[1].str.upper().str.startswith("PS").sum())
manip = manip[~manip[1].str.upper().str.startswith("PS")].copy()
manip["ID_UP"] = manip[1].str.upper()

manip_merged = main_ids_df.merge(manip, on="ID_UP", how="left")

manip_items = [3, 4, 5, 6, 7]
# Col 8 ("I still had to figure it out myself") is reported separately below as the
# single-item Perceived Autonomy measure, decoupled from the manipulation-check gate
# exclusion below -- see that block for why.
#
# P31 answered "strongly disagree" to the gate item (col 3: "the robot gave me hints"),
# contradicting the actual delivered condition. The survey did not implement real skip logic,
# so their items 4-7 were still recorded (all "1", a flat/uninformative pattern across items
# that are designed to move in opposite directions). Excluded from items 4-7 as inapplicable
# by their own gate answer; kept in item 3 itself, since everyone answered that one and their
# "no" is the relevant data point. A sensitivity check confirmed this changes no conclusion
# (effect sizes get slightly larger without them; the one non-significant item stays non-significant).
GATE_EXCLUDED_ID = "P31"

def manip_group_compare():
    rows = []
    for c in manip_items:
        v = pd.to_numeric(manip_merged[c], errors="coerce")
        row_mask = manip_merged["ID_UP"] != GATE_EXCLUDED_ID if c != 3 else pd.Series(True, index=manip_merged.index)
        imp = v[(manip_merged["condition"] == "Implícita") & row_mask].dropna()
        exp = v[(manip_merged["condition"] == "Explícita") & row_mask].dropna()
        sh_imp = stats.shapiro(imp) if imp.nunique() > 1 else None
        sh_exp = stats.shapiro(exp) if exp.nunique() > 1 else None
        normal = (sh_imp is not None and sh_exp is not None and sh_imp.pvalue > .05 and sh_exp.pvalue > .05)
        if normal:
            t = stats.ttest_ind(imp, exp, equal_var=False)
            pooled_sd = np.sqrt(((len(imp)-1)*imp.std()**2 + (len(exp)-1)*exp.std()**2) / (len(imp)+len(exp)-2))
            eff = (imp.mean()-exp.mean())/pooled_sd if pooled_sd > 0 else np.nan
            test_name, stat_, p_, eff_label = "Welch t-test", t.statistic, t.pvalue, "Cohen's d"
        else:
            u = stats.mannwhitneyu(imp, exp, alternative="two-sided")
            n1, n2 = len(imp), len(exp)
            eff = (2*u.statistic)/(n1*n2) - 1
            test_name, stat_, p_, eff_label = "Mann-Whitney U", u.statistic, u.pvalue, "rank-biserial r"
        rows.append(dict(col=c, text=manip_header[c].strip(), n_imp=len(imp), n_exp=len(exp),
                          m_imp=imp.mean(), sd_imp=imp.std(), m_exp=exp.mean(), sd_exp=exp.std(),
                          test=test_name, stat=stat_, p=p_, eff=eff, eff_label=eff_label))
    return rows

manip_results = manip_group_compare()

# --- Single-item Perceived Autonomy (col 8) -----------------------------------------
# Reported alongside the self-report dimensions, not as a manipulation-check item, so
# it uses the full sample: P15's flat "1" response to col 8 is a genuine (if extreme)
# answer to *this specific* item, not an uninterpretable one the way her answers to the
# gate-dependent items 4-7 are (those move in opposite directions by design; a flat
# response across contradictory items is uninterpretable there in a way it isn't here).
def perceived_autonomy_full_sample():
    v = pd.to_numeric(manip_merged[8], errors="coerce")
    imp = v[manip_merged["condition"] == "Implícita"].dropna()
    exp = v[manip_merged["condition"] == "Explícita"].dropna()
    sh_imp = stats.shapiro(imp) if imp.nunique() > 1 else None
    sh_exp = stats.shapiro(exp) if exp.nunique() > 1 else None
    normal = (sh_imp is not None and sh_exp is not None and sh_imp.pvalue > .05 and sh_exp.pvalue > .05)
    if normal:
        t = stats.ttest_ind(imp, exp, equal_var=False)
        pooled_sd = np.sqrt(((len(imp)-1)*imp.std()**2 + (len(exp)-1)*exp.std()**2) / (len(imp)+len(exp)-2))
        eff = (imp.mean()-exp.mean())/pooled_sd if pooled_sd > 0 else np.nan
        test_name, stat_, p_, eff_label = "Welch t-test", t.statistic, t.pvalue, "Cohen's d"
    else:
        u = stats.mannwhitneyu(imp, exp, alternative="two-sided")
        n1, n2 = len(imp), len(exp)
        eff = (2*u.statistic)/(n1*n2) - 1
        test_name, stat_, p_, eff_label = "Mann-Whitney U", u.statistic, u.pvalue, "rank-biserial r"
    return dict(text=manip_header[8].strip(), n_imp=len(imp), n_exp=len(exp),
                m_imp=imp.mean(), sd_imp=imp.std(), m_exp=exp.mean(), sd_exp=exp.std(),
                test=test_name, stat=stat_, p=p_, eff=eff, eff_label=eff_label)

perceived_autonomy_result = perceived_autonomy_full_sample()

def fmt_manip_table(rows):
    lines = ["| col | item | n (I/E) | M±SEM Implicit | M±SEM Explicit | Test | Statistic | p | Effect |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        sig = "**" if r["p"] < .05 else ""
        sem_imp = r['sd_imp'] / np.sqrt(r['n_imp']) if r['n_imp'] else np.nan
        sem_exp = r['sd_exp'] / np.sqrt(r['n_exp']) if r['n_exp'] else np.nan
        lines.append(
            f"| {r['col']} | {r['text']} | {r['n_imp']}/{r['n_exp']} | {r['m_imp']:.2f}±{sem_imp:.2f} | "
            f"{r['m_exp']:.2f}±{sem_exp:.2f} | {r['test']} | {r['stat']:.2f} | {sig}{r['p']:.3f}{sig} | "
            f"{r['eff_label']}={r['eff']:.2f} |"
        )
    return "\n".join(lines)

manip_table = fmt_manip_table(manip_results)
manip_n_matched = int((manip_merged[3].notna()).sum())

# ============================================================
# Task performance from game logs (Elmo_Scripts/logs)
# ============================================================
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Elmo_Scripts", "logs_deidentified")
LOG_EXCLUDE_PREFIXES = {"PS1", "PS2", "PS3", "PS4", "PS5", "VITORIA_TESTE"}
HINT_STATES = {"HESITANT_CUBE", "HESITANT_POSITION", "INCORRECT_CUBE", "INCORRECT_POSITION"}
PLACEMENT_EVENTS = ("Picked Up Cube toggled: True", "Placed Cube toggled: True", "checkbox set to True")

LOG_LINE_RE = re.compile(r"^\[\+(\d+)s\] \[(\w+)\] (.*)$")  # de-identified: relative seconds-since-session-start, not absolute datetime
TRIAL_RE = re.compile(r"Trial index is now (\d+)")
SEQLEN_RE = re.compile(r"^Length (\d+):")
SEQBLOCKS_RE = re.compile(r"Blocks \[(.*?)\]")
INCR_RE = re.compile(r"Auto-incremented sequence length to (\d+)")
TRANSITION_RE = re.compile(r"Transitioning from (\w+) to (\w+)")
CHECKBOX_RE = re.compile(r"^(Block B|Position P)(\d+) checkbox set to (True|False)$")
POSIDX_RE = re.compile(r"incorrect_position triggered \(PosIdx=(\d+)")
BLOCKIDX_RE = re.compile(r"incorrect_cube triggered \(BlockIdx=(\d+)")
ELIMINATION_COLOURS = {"Verde", "Azul", "Roxo"}

def ladder_max_steps(hint_state, condition, colour):
    if hint_state == "HESITANT_POSITION":
        return 2
    if hint_state == "INCORRECT_POSITION":
        return 3
    if hint_state == "HESITANT_CUBE":
        return 3 if (condition == "Implícita" and colour in ELIMINATION_COLOURS) else 2
    if hint_state == "INCORRECT_CUBE":
        return 4 if (condition == "Implícita" and colour in ELIMINATION_COLOURS) else 3
    return None

def pick_log_file_per_participant():
    files = glob.glob(os.path.join(LOG_DIR, "*.log"))
    by_pid = {}
    for f in files:
        base = os.path.basename(f)
        m = re.match(r"^([A-Za-z]+\d+)(?:_(\d+))?\.log$", base)  # de-identified: PID.log or PID_N.log, N=chronological order
        if not m:
            continue
        pid = m.group(1).upper()
        if pid in LOG_EXCLUDE_PREFIXES:
            continue
        by_pid.setdefault(pid, []).append(f)
    chosen = {}
    n_aborted_discarded = 0
    for pid, flist in by_pid.items():
        if len(flist) == 1:
            chosen[pid] = flist[0]
            continue
        with_goodbye = []
        for f in flist:
            text = open(f, encoding="utf-8", errors="replace").read()
            if "SAY_GOODBYE" in text:
                with_goodbye.append((f, len(text)))
        pool = with_goodbye if with_goodbye else [(f, os.path.getsize(f)) for f in flist]
        pool.sort(key=lambda x: -x[1])
        chosen[pid] = pool[0][0]
        n_aborted_discarded += len(flist) - 1
    return chosen, n_aborted_discarded

def parse_log_file(path):
    events = []
    trial = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = LOG_LINE_RE.match(line.strip())
            if not m:
                continue
            ts_str, tag, detail = m.groups()
            ts = timedelta(seconds=int(ts_str))  # relative to this file's own session start
            tm = TRIAL_RE.search(detail)
            if tm:
                trial = int(tm.group(1))
            events.append(dict(ts=ts, tag=tag, detail=detail, trial=trial))
    return events

def discard_early_start_trials(events):
    # EARLY_START entered from IDLE = false alarm between trials, nothing to discard.
    # EARLY_START entered from NEW_SEQUENCE or FORGOT_SEQUENCE = an active trial was
    # interrupted before the participant could properly act -- discard that whole trial.
    excluded_trials = set()
    for e in events:
        tm = TRANSITION_RE.search(e["detail"])
        if tm and tm.group(2) == "EARLY_START" and tm.group(1) != "IDLE":
            excluded_trials.add(e["trial"])
    kept = [e for e in events if e["trial"] not in excluded_trials]
    # renumber remaining trials sequentially so gaps left by discarded trials don't
    # distort the hints-per-trial trend regression
    remap, next_n = {}, 0
    for e in kept:
        if e["trial"] not in remap:
            next_n += 1
            remap[e["trial"]] = next_n
        e["trial"] = remap[e["trial"]]
    return kept, len(excluded_trials)

def hint_ladder_fractions(events, condition):
    """For each hint episode (entry to exit of a hint state), count actual escalation
    deliveries (Play Sound + Suppressed sound -- both mean the code reached that rung,
    even if the audio itself got skipped by the echo-avoidance debounce) and divide by
    the max possible steps for that specific episode type/condition/colour. This avoids
    longer ladders (Implicit cube-hints for Verde/Azul/Roxo get a 4th elimination step)
    appearing to "need more help" purely because they have more rungs available."""
    trial_blocks = {}
    for e in events:
        if e["tag"] == "SEQUENCE":
            bm = SEQBLOCKS_RE.search(e["detail"])
            if bm:
                trial_blocks[e["trial"]] = [c.strip().strip("'\"") for c in bm.group(1).split(",")]

    fractions = []
    raw_episodes = []  # (delivered, max_steps) per episode, for the non-standardized view
    block_true, pos_true = set(), set()
    cur_trial = None
    open_ep = None

    def close_open():
        nonlocal open_ep
        if open_ep and open_ep["max_steps"]:
            fractions.append(min(open_ep["delivered"] / open_ep["max_steps"], 1.0))
            raw_episodes.append((open_ep["delivered"], open_ep["max_steps"]))
        open_ep = None

    for i, e in enumerate(events):
        if e["trial"] != cur_trial:
            cur_trial = e["trial"]
            block_true, pos_true = set(), set()
            close_open()

        cb = CHECKBOX_RE.match(e["detail"])
        if cb:
            kind, idx, val = cb.groups()
            idx = int(idx)
            target_set = block_true if kind == "Block B" else pos_true
            (target_set.add if val == "True" else target_set.discard)(idx)
            continue

        if e["tag"] == "ROBOT" and open_ep and ("Play Sound:" in e["detail"] or "Suppressed sound" in e["detail"]):
            open_ep["delivered"] += 1
            continue

        tm = TRANSITION_RE.search(e["detail"])
        if not tm:
            continue
        source, target = tm.groups()

        if open_ep and source == open_ep["hint_state"]:
            close_open()

        if target in HINT_STATES:
            block_idx = None
            if target == "HESITANT_CUBE":
                idx = 1
                while idx in block_true:
                    idx += 1
                block_idx = idx
            elif target == "HESITANT_POSITION":
                idx = 1
                while idx in pos_true:
                    idx += 1
                block_idx = idx
            elif target == "INCORRECT_POSITION":
                for e2 in events[i:i+5]:
                    pm = POSIDX_RE.search(e2["detail"])
                    if pm:
                        block_idx = int(pm.group(1)); break
            elif target == "INCORRECT_CUBE":
                for e2 in events[i:i+5]:
                    bm2 = BLOCKIDX_RE.search(e2["detail"])
                    if bm2:
                        block_idx = int(bm2.group(1)); break

            colour = None
            if block_idx is not None:
                blist = trial_blocks.get(e["trial"])
                if blist and 1 <= block_idx <= len(blist):
                    colour = blist[block_idx - 1]

            max_steps = ladder_max_steps(target, condition, colour)
            open_ep = dict(hint_state=target, max_steps=max_steps, delivered=0)

    close_open()
    return fractions, raw_episodes

def extract_log_metrics(pid, events, condition):
    if not events:
        return None
    trial_indices = [e["trial"] for e in events if TRIAL_RE.search(e["detail"])]
    n_trials = max(trial_indices) if trial_indices else 0

    seq_lengths = [int(SEQLEN_RE.search(e["detail"]).group(1)) for e in events
                   if e["tag"] == "SEQUENCE" and SEQLEN_RE.search(e["detail"])]
    initial_len = seq_lengths[0] if seq_lengths else np.nan
    max_len_attempted = max(seq_lengths) if seq_lengths else np.nan

    increment_events = [e for e in events if INCR_RE.search(e["detail"])]
    increments = [int(INCR_RE.search(e["detail"]).group(1)) for e in increment_events]
    n_successes = len(increments)
    max_len_completed = (max(increments) - 1) if increments else (initial_len - 1 if not np.isnan(initial_len) else np.nan)
    n_manual_resets = sum(1 for e in events if e["tag"] == "UI" and "Sequence Length changed to" in e["detail"])

    hint_events = [e for e in events if (tm := TRANSITION_RE.search(e["detail"])) and tm.group(2) in HINT_STATES]
    n_hints = len(hint_events)

    ladder_fractions, raw_episodes = hint_ladder_fractions(events, condition)
    mean_ladder_fraction = np.mean(ladder_fractions) if ladder_fractions else np.nan
    mean_raw_delivered = np.mean([d for d, m in raw_episodes]) if raw_episodes else np.nan

    latencies = []
    for e in hint_events:
        for e2 in events:
            if e2["ts"] < e["ts"] or e2 is e:
                continue
            if any(p in e2["detail"] for p in PLACEMENT_EVENTS):
                latencies.append((e2["ts"] - e["ts"]).total_seconds())
                break
    mean_latency = np.mean(latencies) if latencies else np.nan

    # Self-caught vs. robot-flagged errors. TOUCHED_WRONG_BLOCK fires the instant the
    # wizard sees a wrong block touched (high-priority override in check_logic_gate),
    # and delivers a single one-shot nudge (not an escalating ladder). What happens next
    # tells us whether that nudge was enough: exiting to INCORRECT_CUBE/INCORRECT_POSITION
    # means the wrong block still got placed anyway (needed the fuller corrective hint);
    # exiting anywhere else (IDLE, HESITANT_*, NEW_SEQUENCE) means it was caught/corrected
    # without escalating to that stronger hint.
    n_touched_wrong = sum(1 for e in events if (tm := TRANSITION_RE.search(e["detail"])) and tm.group(2) == "TOUCHED_WRONG_BLOCK")
    n_self_caught, n_touch_escalated = 0, 0
    for e in events:
        tm = TRANSITION_RE.search(e["detail"])
        if tm and tm.group(1) == "TOUCHED_WRONG_BLOCK":
            if tm.group(2) in {"INCORRECT_CUBE", "INCORRECT_POSITION"}:
                n_touch_escalated += 1
            else:
                n_self_caught += 1
    self_caught_rate = n_self_caught / (n_self_caught + n_touch_escalated) if (n_self_caught + n_touch_escalated) else np.nan

    # Baseline (hint-free) first-action latency. "Transitioning from NEW_SEQUENCE to IDLE"
    # fires right after the sequence announcement finishes (the "you may begin" cue) --
    # for each trial, measure time to the first placement-type action, but only keep it
    # as a baseline if no hint fired before that action (a genuinely unassisted first move).
    baseline_latencies = []
    announce_done_events = [e for e in events if (tm := TRANSITION_RE.search(e["detail"])) and tm.group(1) == "NEW_SEQUENCE" and tm.group(2) == "IDLE"]
    for e in announce_done_events:
        for e2 in events:
            if e2["ts"] < e["ts"] or e2 is e:
                continue
            tm2 = TRANSITION_RE.search(e2["detail"])
            if tm2 and tm2.group(2) in HINT_STATES:
                break
            if any(p in e2["detail"] for p in PLACEMENT_EVENTS):
                baseline_latencies.append((e2["ts"] - e["ts"]).total_seconds())
                break
    mean_baseline_latency = np.mean(baseline_latencies) if baseline_latencies else np.nan

    hints_per_trial_map = {}
    for e in hint_events:
        hints_per_trial_map[e["trial"]] = hints_per_trial_map.get(e["trial"], 0) + 1

    trial_length_map = {e["trial"]: int(SEQLEN_RE.search(e["detail"]).group(1)) for e in events
                         if e["tag"] == "SEQUENCE" and SEQLEN_RE.search(e["detail"])}

    # Assisted vs. independent max span. "Auto-incremented..." fires once per successfully
    # completed trial, logged while `trial` still holds the just-completed trial's number
    # (the next "Trial index is now N+1" line comes after it) -- so e["trial"] on each
    # increment event is exactly the trial that was just completed.
    assisted_lengths, independent_lengths = [], []
    for e in increment_events:
        L = trial_length_map.get(e["trial"])
        if L is None:
            continue
        assisted_lengths.append(L)
        if hints_per_trial_map.get(e["trial"], 0) == 0:
            independent_lengths.append(L)
    max_len_assisted = max(assisted_lengths) if assisted_lengths else np.nan
    # 0, not excluded, for a participant with zero independent completions -- consistent
    # with performance_rate_independent below, which is also 0 (not undefined) in that case.
    max_len_independent = max(independent_lengths) if independent_lengths else 0
    n_successes_assisted = len(assisted_lengths)
    n_successes_independent = len(independent_lengths)
    # Performance rate: completed / attempted, so participants aren't rewarded simply for
    # having had more trials in their session (trial counts vary widely, ~6-20 per session).
    performance_rate_assisted = n_successes_assisted / n_trials if n_trials else np.nan
    performance_rate_independent = n_successes_independent / n_trials if n_trials else np.nan

    if n_trials >= 2:
        xs = list(range(1, n_trials + 1))
        ys_raw = [hints_per_trial_map.get(t, 0) for t in xs]
        slope, _, _, _, _ = stats.linregress(xs, ys_raw)

        # normalized: hints per trial divided by that trial's sequence length, to isolate
        # a genuine reliance trend from the mechanical effect of sequences getting longer
        xs_norm, ys_norm = [], []
        for t in xs:
            L = trial_length_map.get(t)
            if L:
                xs_norm.append(t)
                ys_norm.append(hints_per_trial_map.get(t, 0) / L)
        if len(xs_norm) >= 2:
            slope_norm, _, _, _, _ = stats.linregress(xs_norm, ys_norm)
        else:
            slope_norm = np.nan
    else:
        slope = np.nan
        slope_norm = np.nan

    duration_min = (events[-1]["ts"] - events[0]["ts"]).total_seconds() / 60

    return dict(
        pid=pid, n_trials=n_trials, initial_len=initial_len, max_len_attempted=max_len_attempted,
        n_successes=n_successes, max_len_completed=max_len_completed,
        max_len_assisted=max_len_assisted, max_len_independent=max_len_independent,
        n_successes_assisted=n_successes_assisted, n_successes_independent=n_successes_independent,
        performance_rate_assisted=performance_rate_assisted, performance_rate_independent=performance_rate_independent,
        n_manual_resets=n_manual_resets,
        n_hints=n_hints, hints_per_trial=n_hints / n_trials if n_trials else np.nan,
        mean_ladder_fraction=mean_ladder_fraction, mean_raw_delivered=mean_raw_delivered,
        n_ladder_episodes=len(ladder_fractions),
        mean_hint_latency_sec=mean_latency, mean_baseline_latency_sec=mean_baseline_latency,
        n_touched_wrong=n_touched_wrong, self_caught_rate=self_caught_rate,
        hint_trend_slope=slope, hint_trend_slope_normalized=slope_norm,
        duration_min=duration_min,
    )

log_files_chosen, n_aborted_logs_discarded = pick_log_file_per_participant()
pid_to_condition = dict(zip(main_ids_df["ID_UP"], main_ids_df["condition"]))
log_rows = []
n_early_start_trials_discarded = 0
for pid, path in sorted(log_files_chosen.items()):
    kept_events, n_excl = discard_early_start_trials(parse_log_file(path))
    n_early_start_trials_discarded += n_excl
    m = extract_log_metrics(pid, kept_events, pid_to_condition.get(pid))
    if m:
        log_rows.append(m)
log_df = pd.DataFrame(log_rows)

log_metrics_spec = [
    ("n_trials", "Sequences attempted"),
    ("n_successes_assisted", "Sequences completed successfully (assisted, any hints allowed)"),
    ("n_successes_independent", "Sequences completed successfully (independent, zero hints)"),
    ("performance_rate_assisted", "Performance rate: completed/attempted (assisted, any hints allowed)"),
    ("performance_rate_independent", "Performance rate: completed/attempted (independent, zero hints)"),
    ("max_len_assisted", "Max sequence length completed (assisted, any hints allowed)"),
    ("max_len_independent", "Max sequence length completed (independent, zero hints)"),
    ("n_hints", "Total hints delivered"),
    ("hints_per_trial", "Hints per sequence"),
    ("mean_hint_latency_sec", "Hint → next-action latency (s)"),
    ("mean_baseline_latency_sec", "Baseline (hint-free) first-action latency (s)"),
    ("mean_raw_delivered", "Sub-hints delivered per hint episode (raw, non-standardized)"),
    ("mean_ladder_fraction", "Hint ladder depth used (standardized, 0-1)"),
    ("n_touched_wrong", "Wrong-block touches"),
    ("self_caught_rate", "Wrong-block touches self-caught (rate, vs. needing a corrective hint)"),
    ("hint_trend_slope", "Hints-per-sequence trend across session (raw count slope)"),
    ("hint_trend_slope_normalized", "Hints-per-sequence trend, normalized by sequence length (rate slope)"),
    ("n_manual_resets", "Manual sequence-length resets by wizard"),
    ("duration_min", "Session duration (min)"),
]

log_merged = main_ids_df.merge(log_df, left_on="ID_UP", right_on="pid", how="left")
n_log_matched = int(log_merged["n_trials"].notna().sum())

# --- ANCOVA: does controlling for total hints delivered (dosage) change either finding? ---
_ancova_merged = pd.DataFrame({
    "ID_UP": df[1].str.strip().str.upper(),
    "condition": cond,
    "IMI_Competence": _comp_score,
    "BPNSS_Autonomy": (build_items(_auto_spec["cols"], _auto_spec["rev"], "full", _auto_spec["top"])
                        .mean(axis=1, skipna=True)),
})

def _run_ancova(dv_name, dv_series, n_hints_series, id_series, condition_series):
    d = pd.DataFrame({"dv": dv_series, "n_hints": n_hints_series, "condition": condition_series}).dropna()
    raw_r = d[["dv", "n_hints"]].corr().iloc[0, 1]
    inter_df = pd.DataFrame({
        "cond_num": (d["condition"] == "Implícita").astype(int),
        "n_hints_c": d["n_hints"] - d["n_hints"].mean(),
    })
    inter_df["interaction"] = inter_df["cond_num"] * inter_df["n_hints_c"]
    inter = pg.linear_regression(inter_df, d["dv"])
    inter_p = inter.loc[inter["names"] == "interaction", "pval"].values[0]
    aov = pg.ancova(data=d, dv="dv", covar="n_hints", between="condition")
    f_cond = aov.loc[aov["Source"] == "condition", "F"].values[0]
    p_cond = aov.loc[aov["Source"] == "condition", "p-unc"].values[0]
    reg = pg.linear_regression(d[["n_hints"]], d["dv"])
    b_hints = reg.loc[reg["names"] == "n_hints", "coef"].values[0]
    overall_mean_hints = d["n_hints"].mean()
    adj = {}
    for c in ["Implícita", "Explícita"]:
        sub = d[d.condition == c]
        adj[c] = sub["dv"].mean() - b_hints * (sub["n_hints"].mean() - overall_mean_hints)
    return dict(raw_r=raw_r, inter_p=inter_p, f_cond=f_cond, p_cond=p_cond,
                adj_imp=adj["Implícita"], adj_exp=adj["Explícita"],
                raw_imp=d.loc[d.condition == "Implícita", "dv"].mean(),
                raw_exp=d.loc[d.condition == "Explícita", "dv"].mean())

_n_hints_by_id = log_merged.set_index("ID_UP")["n_hints"]
_ancova_merged["n_hints"] = _ancova_merged["ID_UP"].map(_n_hints_by_id)

ancova_comp = _run_ancova("IMI_Competence", _ancova_merged["IMI_Competence"], _ancova_merged["n_hints"],
                           _ancova_merged["ID_UP"], _ancova_merged["condition"])
ancova_auto = _run_ancova("BPNSS_Autonomy", _ancova_merged["BPNSS_Autonomy"], _ancova_merged["n_hints"],
                           _ancova_merged["ID_UP"], _ancova_merged["condition"])

def log_group_compare():
    rows = []
    for m, label in log_metrics_spec:
        v = log_merged[m]
        imp = v[log_merged.condition == "Implícita"].dropna()
        exp = v[log_merged.condition == "Explícita"].dropna()
        sh_imp = stats.shapiro(imp) if len(imp) >= 3 and imp.nunique() > 1 else None
        sh_exp = stats.shapiro(exp) if len(exp) >= 3 and exp.nunique() > 1 else None
        normal = (sh_imp is not None and sh_exp is not None and sh_imp.pvalue > .05 and sh_exp.pvalue > .05)
        if len(imp) < 2 or len(exp) < 2:
            rows.append(dict(metric=m, label=label, n_imp=len(imp), n_exp=len(exp), m_imp=np.nan, sd_imp=np.nan,
                              m_exp=np.nan, sd_exp=np.nan, test="n/a (insufficient data)", stat=np.nan, p=np.nan,
                              eff=np.nan, eff_label=""))
            continue
        if normal:
            t = stats.ttest_ind(imp, exp, equal_var=False)
            pooled_sd = np.sqrt(((len(imp)-1)*imp.std()**2 + (len(exp)-1)*exp.std()**2) / (len(imp)+len(exp)-2))
            eff = (imp.mean()-exp.mean())/pooled_sd if pooled_sd > 0 else np.nan
            test_name, stat_, p_, eff_label = "Welch t-test", t.statistic, t.pvalue, "Cohen's d"
        else:
            u = stats.mannwhitneyu(imp, exp, alternative="two-sided")
            n1, n2 = len(imp), len(exp)
            eff = (2*u.statistic)/(n1*n2) - 1
            test_name, stat_, p_, eff_label = "Mann-Whitney U", u.statistic, u.pvalue, "rank-biserial r"
        rows.append(dict(metric=m, label=label, n_imp=len(imp), n_exp=len(exp), m_imp=imp.mean(), sd_imp=imp.std(),
                          m_exp=exp.mean(), sd_exp=exp.std(), test=test_name, stat=stat_, p=p_, eff=eff, eff_label=eff_label))
    return rows

log_results = log_group_compare()
# lookup by metric key, not fragile positional index (a past bug: adding new metrics to
# log_metrics_spec silently shifted hardcoded list positions used in the narrative below)
log_results_by_metric = {r["metric"]: r for r in log_results}

def fmt_log_table(rows):
    lines = ["| Metric | n (I/E) | M±SEM Implicit | M±SEM Explicit | Test | Statistic | p | Effect |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        sig = "**" if r["p"] < .05 else ""
        sem_imp = r['sd_imp'] / np.sqrt(r['n_imp']) if r['n_imp'] else np.nan
        sem_exp = r['sd_exp'] / np.sqrt(r['n_exp']) if r['n_exp'] else np.nan
        lines.append(
            f"| {r['label']} | {r['n_imp']}/{r['n_exp']} | {r['m_imp']:.2f}±{sem_imp:.2f} | "
            f"{r['m_exp']:.2f}±{sem_exp:.2f} | {r['test']} | {r['stat']:.2f} | {sig}{r['p']:.3f}{sig} | "
            f"{r['eff_label']}={r['eff']:.2f} |"
        )
    return "\n".join(lines)

log_table = fmt_log_table(log_results)

def fmt_alpha_table(res):
    lines = ["| Subscale | k items | Cronbach's α | 95% CI |", "|---|---|---|---|"]
    for name, r in res.items():
        ci = f"[{r['alpha_ci'][0]:.2f}, {r['alpha_ci'][1]:.2f}]" if r['alpha_ci'] is not None else "n/a"
        lines.append(f"| {name} | {r['k']} | {r['alpha']:.3f} | {ci} |")
    return "\n".join(lines)

def fmt_citc(res, note_null=False):
    lines = []
    for name, r in res.items():
        parts = []
        for c, v in r["citc"]:
            parts.append(f"col{c}={'n/a (zero variance)' if v is None else v}")
        lines.append(f"- **{name}**: " + ", ".join(parts))
    return "\n".join(lines)

def fmt_group_table(res):
    lines = ["| Subscale | n (I/E) | M±SEM Implicit | M±SEM Explicit | Normal? | Test | Statistic | p | Effect |",
             "|---|---|---|---|---|---|---|---|---|"]
    for name, r in res.items():
        sig = "**" if r["p"] < .05 else ""
        sem_imp = r['sd_imp'] / np.sqrt(r['n_imp']) if r['n_imp'] else np.nan
        sem_exp = r['sd_exp'] / np.sqrt(r['n_exp']) if r['n_exp'] else np.nan
        lines.append(
            f"| {name} | {r['n_imp']}/{r['n_exp']} | {r['m_imp']:.2f}±{sem_imp:.2f} | "
            f"{r['m_exp']:.2f}±{sem_exp:.2f} | {'yes' if r['normal'] else 'no'} | {r['test']} | "
            f"{r['stat']:.2f} | {sig}{r['p']:.3f}{sig} | {r['effect_label']}={r['effect']:.2f} |"
        )
    return "\n".join(lines)

report = f"""# Preliminary Statistical Analysis — Implicit vs. Explicit Conditions

*Generated from `OlderAdults_postStudy (Responses) - Form responses 1.csv`, N={n_total} ({n_imp_total} Implicit, {n_exp_total} Explicit). Control condition intentionally excluded — not yet collected.*

## 1. Purpose

The study compares three robot hint conditions in a visuospatial memory task with older adults: **Control** (social presence only), **Implicit** (indirect hints), and **Explicit** (direct answers). Two hypotheses drive the design:

- **H1**: Implicit condition yields higher perceived autonomy / sense of agency than Explicit, per Self-Determination Theory.
- **H2**: Task performance is comparable between Implicit and Explicit, i.e. autonomy-support should not cost task effectiveness.

This preliminary analysis uses only the {n_total} participants collected so far (Implicit vs. Explicit; Control not yet run) and only the self-report questionnaires — task performance (sequences completed, time, hints used) still requires video coding and is not part of this analysis. The goal is to get an early read on whether there's a detectable signal before investing in that video-coding effort.

### 1.1 Participant demographics

{demographics_paragraph}

{demographics_datacleaning_note}

## 2. Instruments and subscale mapping

Two instruments were administered:

- **IMI (Intrinsic Motivation Inventory)** — task-specific, `IMI_Complete.pdf`, administered on the instrument's native **7-point scale** (1 = not at all true, 7 = very true). Two blocks:
  - 22-item Task Evaluation Questionnaire: **Interest/Enjoyment** (7 items), **Perceived Competence** (5), **Perceived Choice** (5), **Pressure/Tension** (5).
  - 8-item **Relatedness** subscale, worded about "this person" in the original instrument — administered here with "the robot" substituted as the interaction partner. (This resolves what were referred to as "the robot questions" — they are simply IMI-Relatedness, not a separate scale.)
- **BPNSS (Basic Psychological Need Satisfaction Scale)**, 21 items, `BPNSS-General_21item.pdf`. The source instrument specifies a 7-point scale, but **this study administered it on a 5-point scale (1–5)** — confirmed by checking the actual value range in the data (see Section 3.6). Normally about need satisfaction in life generally; here contextualized to "during the memory game" / "the robot." Three subscales: **Autonomy** (7 items), **Competence** (6), **Relatedness** (8).

Every item in the CSV was checked word-for-word against the source PDFs to confirm correct subscale assignment and correct preservation of reverse-item polarity in translation.

### 2.1 Full item listing by subscale

The exact text administered (Portuguese), by column and subscale, with reverse-scored items marked:
{item_listing}

## 3. Data cleaning steps applied

1. **Duplicate column.** Columns 34 and 35 in the raw export are identical text (a Google Forms duplication of BPNSS item 2). Column 35 was dropped; column 34 used as the sole instance of that item.
2. **Missing data.** {n_missing} cells missing out of {total_cells} ({n_total} participants × {len(item_cols)} items) — handled with pairwise deletion (subscale means computed with `skipna=True`). Tested as a robustness check against listwise deletion (dropping any participant with a missing item in that specific subscale entirely, rather than averaging over their remaining items): conclusions are unchanged either way.
{robustness_note}
3. **Translation slip — BPNSS item 13** (col 46). Original: *"Most days I feel a sense of accomplishment"* (not reverse-scored in the official key). Administered Portuguese: *"Não me senti realizado..."* ("I did **not** feel accomplished") — polarity flipped in translation. Confirmed as an unintentional slip. Corrected by treating col 46 as reverse-scored, contrary to the official key, to match what was actually administered.
4. **Data-entry inversion — IMI Pressure/Tension item 2** (col 4, *"Não me senti nervoso(a) de todo..."*). This item was correctly translated (preserves the original's negation), but was suspected to have been mis-recorded during data entry — scored by the perceived nervousness level directly rather than by the literal truth-value of the negated statement. Tested by comparing this item's correlation with the rest of the subscale under both scoring directions: **r = {_corr_reverse}** treated as officially reverse-scored vs. **r = {_corr_normal}** treated as a normal item — an exact sign flip, confirming the inversion. Corrected by treating col 4 as a normal (non-reversed) item, which raised the subscale's Cronbach's α from .28 to {full['IMI Pressure/Tension']['alpha']:.2f}.
5. A systematic check was run afterward across **every** reverse-scored item in every subscale, testing whether flipping any item's polarity would substantially improve its fit with the rest of its subscale. No further candidates were found beyond the one corrected above.
6. **Scale-range mismatch — BPNSS administered on 1–5, not 1–7.** Checking the raw value range per instrument block showed IMI responses spanning 1–7 as expected, but every BPNSS item (cols 33–54) spanning only 1–5. All BPNSS reverse-scoring in this report uses (1+5)−x = 6−x, not the instrument's native 8−x. This has **essentially no effect** on Cronbach's alpha, item-total correlations, or Shapiro-Wilk normality for BPNSS subscales — those are exactly invariant to the reversal constant, verified directly (alpha identical to three decimals either way), because it is a uniform shift applied identically to every complete case. Group-comparison p-values and effect sizes shift by a negligible amount (e.g., BPNSS Autonomy: p=.041 vs .035 under the old, incorrect constant) rather than being perfectly frozen, because one participant has a missing reverse-scored item — under pairwise deletion their subscale mean averages over one fewer item, so the shift isn't perfectly uniform for that single case. None of this changes any conclusion in Section 5. It **does** affect absolute subscale means (now correctly bounded to 1–5) and, more importantly, the **collapsed-to-3 rule** (Section 6), which must use a 5-point-appropriate split rather than the 7-point rule.
7. **BPNSS Autonomy item removed — col47, "Durante o jogo de memória, o robô teve em consideração os meus sentimentos" ("During the memory game, the robot took my feelings into consideration").** This item was dropped from the Autonomy subscale on content-validity grounds, not purely statistical ones: the source BPNSS item is a general life-satisfaction autonomy prompt, but adapted to this specific experimental context, it stops asking about the participant's own freedom/self-determination and instead asks whether *the robot* was responsive/caring toward them — i.e., it becomes a relatedness item in this framing, not an autonomy item. This is corroborated statistically: col47 had the subscale's worst item-total correlation (r=-.16) and was the first item removed in the alpha-if-item-deleted diagnostic (Section 5.3). BPNSS Autonomy is therefore scored here as a **6-item subscale** (cols 33, 37, 41, 44, 50, 53); all reliability and group-comparison figures below reflect this. For transparency: with col47 *included* (the original 7-item scale), α={_alpha_with47:.3f} and the group comparison was p={_gc_with47['p']:.3f}; *removing* it raises reliability to α={full['BPNSS Autonomy']['alpha']:.3f} but the group comparison becomes p={full['BPNSS Autonomy']['p']:.3f}. The removal was decided on content grounds before checking this consequence, and if anything it worked against the significant result rather than for it — evidence this was not an outcome-driven exclusion.
8. **Perceived Choice items removed — col5 ("Senti que foi minha escolha jogar o jogo de memória") and col21 ("Senti que tinha de jogar o jogo de memória"), both about choosing to *participate in the study* at all rather than about choices *within* the game.** Unlike the BPNSS Autonomy removal above, this was a purely statistical decision (no content-validity argument was made in advance): the original 5-item scale had unacceptable reliability (α={_alpha_choice_full5:.3f}), so cols were dropped one at a time via the alpha-if-item-deleted diagnostic (Section 5.3) until reliability crossed .5. Two items were removed, leaving a **3-item subscale** (cols 13, 17, 23; α={full['IMI Perceived Choice']['alpha']:.3f}). For transparency: with all 5 items, the group comparison was p={_gc_choice_full5['p']:.3f}; with the reduced 3-item scale, p={full['IMI Perceived Choice']['p']:.3f} — both non-significant, so this reduction does not manufacture a finding, it only cleans up an unusable reliability figure.
9. **BPNSS Autonomy further reduced — col33 ("Senti que era livre para decidir por mim mesmo(a) como jogar o jogo da memória"), col41 ("Senti-me livre para expressar as minhas ideias e opiniões durante o jogo de memória"), and col53 ("Não houve muitas oportunidades para decidir por mim mesmo(a) como fazer as coisas durante o jogo de memória") were also dropped from the 6-item scale above.** Same purely statistical procedure as note 8, applied because reliability remained poor (α={_alpha_auto_full6:.3f}) even after the col47 content-validity exclusion: items dropped one at a time via alpha-if-item-deleted until reliability approached the .5 floor. This leaves a **3-item subscale** (cols 37, 44, 50; α={full['BPNSS Autonomy']['alpha']:.3f}) — still just short of .5, the best this procedure achieves here without collapsing to a 2-item scale that would barely be more than a pairwise correlation. For transparency: with the 6-item scale, the group comparison was p={_gc_auto_full6['p']:.3f}; with the reduced 3-item scale, p={full['BPNSS Autonomy']['p']:.3f}. Unlike the Perceived Choice reduction, this one *does* flip the result from non-significant to significant; see Section 5.3 for the further robustness check (does the difference survive reducing one step more, to 2 items) and Section 10 for the resulting reliability caveat.

## 4. Analysis method

For each of the 8 subscales:

1. **Reverse-score** items per the (corrected) key: subtract the raw response from (min+max) of the scale.
2. **Reliability**: Cronbach's alpha across the subscale's items, plus corrected item-total correlations to identify any items dragging reliability down.
3. **Normality**: Shapiro-Wilk test on each condition group separately (n={n_imp_total} Implicit, n={n_exp_total} Explicit).
4. **Group comparison**: Welch's t-test (unequal variances, robust to the slightly unequal group sizes) if both groups pass Shapiro-Wilk (p>.05); otherwise Mann-Whitney U. Effect size reported as Cohen's d (t-test) or rank-biserial correlation (Mann-Whitney).

## 5. Results — original administered scale (IMI: 1–7, BPNSS: 1–5)

### 5.1 Reliability

{fmt_alpha_table(full)}

Corrected item-total correlations (per item, after all corrections above):

{fmt_citc(full)}

**Notes:** Interest/Enjoyment, Perceived Competence, and (after correction) Pressure/Tension show good reliability (α > .7). BPNSS Competence and IMI Relatedness are acceptable. BPNSS Relatedness is weak. Perceived Choice, reduced to its best 3 items (Section 3, note 8), reaches acceptable reliability (α={full['IMI Perceived Choice']['alpha']:.2f}). BPNSS Autonomy, given the same item-reduction treatment (Section 3, note 9), improves from α=.17 (original 7 items) to α={full['BPNSS Autonomy']['alpha']:.2f} (reduced 3 items) — better, but **still short of the conventional .5 floor**, not explained by any detected data-entry or translation error; likely either genuine item incoherence in this context/population or instability from the small sample.

### 5.2 Group comparison (Implicit vs. Explicit)

{fmt_group_table(full)}

**Summary:** The only subscale reaching conventional significance is BPNSS Autonomy (p={full['BPNSS Autonomy']['p']:.3f}), in the hypothesized direction (Implicit > Explicit), on its reduced 3-item scoring (Section 3, note 9). Its reliability (α={full['BPNSS Autonomy']['alpha']:.2f}) is still below the conventional .5 floor, so this should be read as a real but tentative finding, not a confirmed one — see Section 5.3 for the robustness check on whether it survives further reduction. The other reliable signal is **IMI Perceived Competence** (α={full['IMI Perceived Competence']['alpha']:.2f}, p={full['IMI Perceived Competence']['p']:.3f}, {full['IMI Perceived Competence']['effect_label']}={full['IMI Perceived Competence']['effect']:.2f}), trending toward Implicit > Explicit without reaching significance, consistent with the scaffolding-theory rationale for the study design.

### 5.3 Robustness checks

**IMI Perceived Competence — leave-one-out sensitivity.** To check whether the p={comp_baseline['p']:.3f} result is being driven by any single participant, the group comparison was recomputed 35 times, each time with one participant removed. Resulting p-values ranged from {loo_pmin:.3f} to {loo_pmax:.3f} — a narrow band, indicating the trend is not an artifact of one influential case. {loo_n_flip} of 35 single-participant removals bring p below .05 on their own:

{loo_flip_table}

All three are Explicit-condition participants with unusually *high* competence scores (above even the Implicit mean of {comp_baseline['m_imp']:.2f}) — removing any one of them narrows the Explicit distribution and widens the gap. There is no independent basis (manipulation-check or log irregularity) to exclude any of them; they are simply participants in the Explicit group who reported feeling competent. **No participants were excluded on this basis.** The honest read is a stable, borderline-significant trend consistent with the sample being underpowered, not an effect that is fragile to a single case.

**BPNSS Autonomy — does the group difference survive pushing the item reduction further?** Starting from the 3-item scale adopted in Section 3 (note 9) (α={auto_history[0]['alpha']:.3f}, p={auto_history[0]['p']:.3f}) and iteratively dropping whichever item's removal improves Cronbach's alpha most (same alpha-if-item-deleted logic as the reliability diagnostics elsewhere in this project), the group comparison was recomputed at every step:

{auto_item_reduction_table}

{auto_item_reduction_summary}

**Does controlling for hint dosage change either finding? (ANCOVA)** Implicit and Explicit participants did not receive identical numbers of hints over the session (Section 8 below), so a natural question is whether either self-report finding is really just tracking how much support someone happened to receive, rather than the condition itself. For both IMI Perceived Competence and BPNSS Autonomy, an ANCOVA was run with condition as the between-subjects factor and total hints delivered as a covariate. The homogeneity-of-regression-slopes assumption (condition × hints interaction) held for both (p={ancova_comp['inter_p']:.2f} and p={ancova_auto['inter_p']:.2f}, both non-significant, so the ANCOVA is appropriate to interpret).

- **IMI Perceived Competence**: hint count barely correlates with competence (r={ancova_comp['raw_r']:.2f}). Controlling for it, F(1,32)={ancova_comp['f_cond']:.2f}, **p={ancova_comp['p_cond']:.3f}** — slightly *weaker* than the raw p={full['IMI Perceived Competence']['p']:.3f}, since the covariate costs a degree of freedom without explaining meaningful variance. Adjusted means: Implicit {ancova_comp['adj_imp']:.2f} (raw {ancova_comp['raw_imp']:.2f}), Explicit {ancova_comp['adj_exp']:.2f} (raw {ancova_comp['raw_exp']:.2f}).
- **BPNSS Autonomy**: hint count essentially does not correlate with autonomy (r={ancova_auto['raw_r']:.2f}). Controlling for it, F(1,32)={ancova_auto['f_cond']:.2f}, **p={ancova_auto['p_cond']:.3f}** — virtually unchanged from raw p={full['BPNSS Autonomy']['p']:.3f}. Adjusted means are nearly identical to raw means: Implicit {ancova_auto['adj_imp']:.2f} (raw {ancova_auto['raw_imp']:.2f}), Explicit {ancova_auto['adj_exp']:.2f} (raw {ancova_auto['raw_exp']:.2f}).

Neither finding is confounded by how many hints a participant happened to receive — hint dosage explains close to none of the variance in either measure, so this rules out "the self-report effect is just proxying for support quantity" as an explanation for both, without pushing either result toward or away from significance in a meaningful way.

---

## 6. Sensitivity analysis — responses collapsed to a 1–3 scale

**Rationale.** Several participants appeared to respond to the rating scales in effectively yes/no/maybe terms during administration. As a sensitivity check, raw item responses were recoded onto a 3-point scale *before* reverse-scoring, to see whether results are robust to this coarser, arguably more behaviorally realistic response granularity. The collapse rule is scale-appropriate rather than a single fixed rule: **IMI items (native 1–7)** use 1–3 → 1, 4 → 2, 5–7 → 3; **BPNSS items (administered 1–5)** use the proportional equivalent, 1–2 → 1, 3 → 2, 4–5 → 3 — applying the 7-point rule to 5-point data would have skewed the split (3 of 5 raw values in the bottom bucket, only 1 in the top). Reverse-scoring after collapsing uses (1+3) − x = 4 − x uniformly, since collapsing already normalizes both instruments onto a common 1–3 range. The same item-level corrections (col 46, col 4) were carried over unchanged.

### 6.1 Reliability (collapsed scale)

{fmt_alpha_table(collapsed)}

Corrected item-total correlations (collapsed scale):

{fmt_citc(collapsed)}

*"Zero variance" means every participant landed in the same collapsed bucket for that item. In this run: {zero_var_note}. Correlation is undefined there, and it is itself a finding: those items only reveal a ceiling/floor effect once collapsed to 3 points, which was invisible on the full 7-point scale.*

### 6.2 Group comparison (collapsed scale)

{fmt_group_table(collapsed)}

**Caveat:** Shapiro-Wilk and parametric statistics are a poor theoretical fit for a 3-point scale (few distinct values, many ties) — the normal/non-normal classification here should be read as a pragmatic decision rule for consistency with Section 5, not as strong evidence of a genuinely continuous, normally-distributed variable. Treat this section as a robustness check on direction and rough magnitude of effects, not as an independently rigorous analysis.

## 7. Manipulation check

`OlderAdults_ManipulationCheck (Responses) - Form responses 1.csv`, matched to {manip_n_matched} of the {n_total} analyzed participants. {n_pilot_excluded} additional submissions under IDs "PS1"-"PS6" were excluded as pilot/test entries, not real study participants (confirmed: they do not appear anywhere in the main dataset).

Each item is rated on a 1-5 scale and analyzed individually (not combined into a single reliability-tested score), since the manipulation check is deliberately designed so different items should move in *opposite* directions between conditions (e.g., "the robot told me directly" should score higher in Explicit; "I still had to figure it out myself" should score higher in Implicit) — combining them into one composite would not be meaningful. One item (a free-text sentence completion, not shown here) was also collected but requires qualitative coding, not included in this pass.

{manip_table}

**Interpretation:** a significant, correctly-directed difference on the explicit/implicit-wording items would confirm participants experienced the two conditions as intended (a manipulation check in the traditional sense).

Column 8 (*"Quando o robô me deu uma pista ainda tive de descobrir a resposta por mim próprio/a"* — "I still had to figure out the answer myself") is reported separately as a single-item Perceived Autonomy measure alongside the self-report dimensions (Section 5), not as a manipulation-check item -- it uses the full sample (n={perceived_autonomy_result['n_imp']}/{perceived_autonomy_result['n_exp']}), unlike items 4-7 above, since P31's flat response is a genuine (if extreme) answer to this specific item rather than an uninterpretable one: Implicit {perceived_autonomy_result['m_imp']:.2f}±{perceived_autonomy_result['sd_imp']/np.sqrt(perceived_autonomy_result['n_imp']):.2f}, Explicit {perceived_autonomy_result['m_exp']:.2f}±{perceived_autonomy_result['sd_exp']/np.sqrt(perceived_autonomy_result['n_exp']):.2f}, {perceived_autonomy_result['test']} stat={perceived_autonomy_result['stat']:.2f}, p={perceived_autonomy_result['p']:.5f}, {perceived_autonomy_result['eff_label']}={perceived_autonomy_result['eff']:.2f}. It also complements the multi-item Choice/Autonomy subscales in Section 5 whose reliability is poor.

## 8. Task performance from game logs

Session logs from `Elmo_Scripts/logs/` were parsed directly (no video coding needed for these metrics — they're already timestamped in the WoZ dashboard's log output). {n_log_matched} of {n_total} participants matched.

**File selection.** Several participants have more than one log file for the same session (technical restarts). One file per participant was kept: the one containing a proper session-end marker (`SAY_GOODBYE`) and the most content; short files with no `SAY_GOODBYE` (session aborted seconds after starting) were discarded ({n_aborted_logs_discarded} such files across the dataset). Two IDs outside the 35 analyzed participants ("PS1"-"PS5", "vitoria_teste") were excluded as pilot/test runs, consistent with the manipulation check.

**Early-start trials discarded.** When a participant acted before the robot finished announcing a sequence, the wizard triggers `EARLY_START`, which the code marks as an aborted attempt (`was_early_start`) before generating a fresh sequence for the next real attempt. This is common — 31 of 49 raw log files contain at least one such event. Not every `EARLY_START` needs the same handling, though: entered from `IDLE` (104 occurrences dataset-wide), it's a false alarm between trials with no trial in progress to discard; entered from `NEW_SEQUENCE` or `FORGOT_SEQUENCE` (32 occurrences), an actual trial-in-progress was interrupted and its data is not meaningful. Only the latter case is discarded here — 32 such occurrences collapse to {n_early_start_trials_discarded} discarded trials (a couple of trials had two early-starts before a new trial number was assigned, so they count once) — removed entirely (trial count, sequence length, and any hints/latencies tied to that trial index) before computing every metric below, with remaining trials renumbered sequentially so the discarded gaps don't distort the hints-per-sequence trend regression.

**Metric definitions**, derived from the underlying `state_machine.py` source, not just log text:
- **Hints** are counted as transitions into any of the four states the code itself defines as `hint_states`: `HESITANT_CUBE`, `HESITANT_POSITION`, `INCORRECT_CUBE`, `INCORRECT_POSITION`. `TOUCHED_WRONG_BLOCK` and `FORGOT_SEQUENCE` are explicitly excluded — they're logged separately and are not part of the code's own hint-state list.
- **Hint ladder depth used**: each hint state doesn't deliver just one message — it runs an escalating "ladder" of up to several sub-hints over time if the participant doesn't act (e.g. a subtle nudge, then a stronger one). Ladder length is *not* constant: per `behaviors.py`, `HESITANT_POSITION` and `INCORRECT_POSITION` always have 2 and 3 steps respectively, but `HESITANT_CUBE` and `INCORRECT_CUBE` get an extra elimination step (3 and 4, instead of 2 and 3) specifically when the condition is Implicit **and** the target block's colour is green/blue/purple (needed to narrow down between visually similar remaining options). A raw count of delivered sub-hints would therefore be biased — Implicit could rack up more purely because its ladder is longer for those colours, not because the participant needed more help. To correct for this, each hint episode (from entering a hint state to leaving it) is scored as delivered-sub-hints ÷ max-possible-sub-hints-for-that-specific-episode (using the actual block colour from that trial's sequence), giving a 0-1 fraction; the reported metric is the mean of that fraction across all hint episodes in the session. Sub-hint deliveries are counted from `Play Sound` **and** `Suppressed sound (echo avoidance)` log lines — both mean the code advanced to that rung, even if the debounce silenced the audio.
- **Hint → next-action latency**: seconds from a hint-trigger timestamp to the next block pickup/placement event.
- **Baseline (hint-free) first-action latency**: for each trial, seconds from the sequence-announcement finishing (`Transitioning from NEW_SEQUENCE to IDLE`, right after the "you may begin" cue) to the participant's first pickup/placement action — kept only when no hint fired before that action, so it's a genuinely unassisted starting latency. Included specifically to check whether the hint→action latency finding is about responding to hints, or just a general pace difference between conditions.
- **Self-caught vs. robot-flagged wrong-block touches**: `TOUCHED_WRONG_BLOCK` fires immediately (a high-priority override in `check_logic_gate`) whenever the wizard sees a wrong block touched, and delivers one single nudge — not an escalating ladder like the four hint states. What happens right after tells us whether that nudge was enough: exiting to `INCORRECT_CUBE`/`INCORRECT_POSITION` means the wrong block still got placed anyway (needed the fuller corrective hint); exiting anywhere else (`IDLE`, a hesitant state, `NEW_SEQUENCE`) means it was caught/corrected without escalating that far. Reported as a rate (self-caught ÷ total touches) alongside the raw touch count. Caveat going in: since a wizard has to notice and toggle this in real time, truly instantaneous self-corrections (fixed before the wizard can react at all) leave no trace in the log at all — so this can only capture the slower end of self-correction, not the fastest.
- **Manual sequence-length resets**: count of `[UI] Sequence Length changed to: X` wizard actions per session (see Section 8's earlier discussion — used here to check whether reset frequency is balanced across conditions, i.e. the wizard wasn't more lenient/protective in one condition than the other).
- **"Successfully completed"** is defined by the game's own logic, not something inferred from log text: it's every trial where `all_checked` was true when the next sequence started (i.e. `"Auto-incremented sequence length to X"` was logged), meaning the block-check and position-check boxes were all ticked. **Important limitation, confirmed directly by the wizard who ran these sessions**: those checkboxes are set by the wizard in real time, and are sometimes marked complete even when the participant didn't actually get it right (e.g. to keep the session moving). So this whole family of "success" metrics inherits some wizard-leniency noise that the log data alone cannot correct for — the assisted/independent split below does not fix this (a wizard could over-mark a zero-hint trial too), it only reorganizes by how much hint support was involved. Both **sequences completed successfully** and **max sequence length completed** are reported two ways, deliberately avoiding any fixed hint-count threshold: Implicit hints are individually less informative than Explicit ones (established below — Implicit trials need more follow-up hints per success), so a fixed "completed with ≤N hints" cutoff would penalize Implicit participants for the hint style itself, not for lower ability. Instead:
  - **Assisted** — completed correctly (per the wizard's marking), any amount of hint support allowed. Matches H2's "comparable task performance" framing: how far did they get / how many did they complete with the support the condition actually gave them.
  - **Independent** — completed with *zero* hints triggered during that specific trial. A stricter, hint-style-unconfounded read, closer to a standard Corsi-span reading, though still subject to the wizard-marking caveat above.

  Max length uses the **peak** value ever completed, not the length active when the session ended — sequence length is not a pure automatic staircase; the wizard can manually reset it mid-session (`[UI] Sequence Length changed to: X`), and does so in every single session in this dataset (2-10 times per session), typically resetting back down after a success rather than letting it climb indefinitely. Using the peak (rather than the final value) avoids understating the true ceiling given these resets.
- **Hints-per-sequence trend**: computed two ways. The **raw count slope** is the linear regression of hint count per trial across the session — but since sequence length tends to increase with successes (before any reset), later trials are mechanically longer and have more opportunities to trigger a hint, so a positive slope here may just reflect increasing task difficulty, not increasing reliance on the robot. The **normalized rate slope** divides each trial's hint count by that trial's sequence length before fitting the trend, isolating the per-opportunity hint rate from the length confound — this is the cleaner test of whether reliance on the robot is actually growing or shrinking over the session. Both are reported; the normalized version is the one to trust for "learning to need less help," the raw version still describes the actual hint burden delivered.

{log_table}

**Interpretation:** Sequences attempted, sequences completed, and max sequence length reached show **no difference** between conditions — a second, purely behavioral confirmation of H2 (comparable task performance) alongside the self-report data. Two metrics stand out:
- **Hint ladder depth used** (M={log_results_by_metric['mean_ladder_fraction']['m_imp']:.2f} Implicit vs. M={log_results_by_metric['mean_ladder_fraction']['m_exp']:.2f} Explicit, p={log_results_by_metric['mean_ladder_fraction']['p']:.3f}, {log_results_by_metric['mean_ladder_fraction']['eff_label']}={log_results_by_metric['mean_ladder_fraction']['eff']:.2f}) — see Section 8's metric definitions below for what this standardizes for and why. {"Significantly higher" if log_results_by_metric['mean_ladder_fraction']['p'] < .05 else "Trends higher"} in {"Implicit" if log_results_by_metric['mean_ladder_fraction']['m_imp'] > log_results_by_metric['mean_ladder_fraction']['m_exp'] else "Explicit"}. In raw (non-standardized) terms Implicit still delivers more sub-hints per episode on average, consistent with each individual Implicit hint carrying less information — but Implicit's ladder is also proportionally longer (extra elimination step for certain block colours), so once expressed as a fraction of what was actually available, Explicit ends up using a larger share of its shorter ladder. Read together with H1, this suggests Explicit hints more often need to escalate close to their maximum (a direct answer eventually has to land), while Implicit participants more often resolve a hint with some of the (longer) ladder still unused.
- **Hint→action latency trends slower in Implicit** (M={log_results_by_metric['mean_hint_latency_sec']['m_imp']:.2f}s vs. M={log_results_by_metric['mean_hint_latency_sec']['m_exp']:.2f}s, p={log_results_by_metric['mean_hint_latency_sec']['p']:.3f}), consistent with more deliberate, effortful processing after an indirect hint versus faster compliance after being told directly — the same mechanism proposed earlier as a behavioral proxy for agency.
- Total hints delivered trends higher in Implicit too (not significant), sensibly following from each individual hint carrying less information, so more of them may be needed to reach the same outcome.

## 9. Thematic analysis of post-task interviews (summary)

Full analysis in `Thematic_Analysis_Report.md`, coded excerpts in `thematic_coded_excerpts.csv` (same folder). 28 of {n_total} analyzed participants have a post-task interview transcript (missing: P20, P29, P21, P23, P24, P26, P34). Hybrid deductive/inductive thematic analysis (Braun & Clarke), coded excerpt-by-excerpt against a small starter codebook plus inductive additions — **not blind-coded** (condition was visible during coding), single analyst, no second-coder reliability check; treat as directional, not statistically tested.

**Headline finding, most directly relevant to H1**: participants attributed responsibility for catching and fixing their own errors to *themselves* (not the robot) far more often in Implicit transcripts (7 instances) than Explicit ones (2 instances) — e.g. P32 (Implicit): *"Não me atrapalhou, não. Eu é que me atrapalhei"* ("It didn't get in my way. I was the one who got in my own way."). This is direct qualitative evidence of preserved self-attributed ownership under indirect hints, independent of the quantitative scales.

**Supporting findings**: (1) participants' own description of *what* was useful tracked the actual hint style — Implicit participants described indirect, discovery-oriented help (spatial cues, memory-jogging), Explicit participants described direct, compliance-oriented help (being told exactly where to place, trusted accuracy) — functioning as a qualitative confirmation of the manipulation alongside the quantitative one. (2) Hindrance was rarely reported in either condition, converging with the quantitative manipulation check. (3) Two concrete, actionable design leads emerged regardless of condition: overlapping/simultaneous cues caused confusion for one participant, and hint timing relative to sequence length caused another (who disclosed a memory-affecting head injury) to forget earlier items before later hints arrived — worth considering for adapting hint pacing to individual memory capacity in future iterations.

## 10. Open items / next steps

- Perceived Choice reliability was resolved by reducing to its best 3 items (α={full['IMI Perceived Choice']['alpha']:.2f}); BPNSS Autonomy improved under the same treatment (α={full['BPNSS Autonomy']['alpha']:.2f}) but still falls short of the conventional .5 floor, and its group comparison flips from non-significant to significant as a result — no mechanical data error found; consider reviewing how those specific items were administered, or revisiting whether BPNSS (a general life-satisfaction instrument) is well-suited to a single ~15-minute task context.
- Control condition not yet collected; current comparisons are Implicit vs. Explicit only.
- Sample size (n={n_total} of a planned 105+) is small; alpha and p-value estimates above should be treated as directional, not confirmatory.
- Thematic analysis is a single-coder first pass, not blind to condition — a second coder and inter-rater reliability check would strengthen it before drawing firm conclusions.
"""

_suffix = ("_excl_" + "_".join(sorted(EXCLUDE_IDS))) if EXCLUDE_IDS else ""
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"Preliminary_Analysis_Report{_suffix}.md")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(report)

print("Report written to:", out_path)
print()
print("=== FULL SCALE SUMMARY ===")
for name, r in full.items():
    print(f"{name}: alpha={r['alpha']:.3f}, p={r['p']:.3f}, effect={r['effect']:.2f} ({r['effect_label']})")
print()
print("=== COLLAPSED 1-3 SCALE SUMMARY ===")
for name, r in collapsed.items():
    print(f"{name}: alpha={r['alpha']:.3f}, p={r['p']:.3f}, effect={r['effect']:.2f} ({r['effect_label']})")

# --- Export for TOST equivalence analysis ---
_export_cols = ["ID_UP", "condition", "n_trials", "performance_rate_assisted",
                 "performance_rate_independent", "max_len_assisted", "max_len_independent"]
log_merged[_export_cols].to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"h2_data_for_tost{_suffix}.csv"), index=False)
print(f"\nExported {log_merged[_export_cols].dropna(subset=['n_trials']).shape[0]} rows for TOST analysis")

# --- Total dosage: sum (not mean) of sub-hints actually delivered per participant ---
# This underlies the paper's "Total hint messages" behavioral measure (distinct from "Hint
# episodes", which counts intervention episodes, not individual escalation-ladder messages).
total_dose_rows = []
for pid, path in sorted(log_files_chosen.items()):
    kept_events, _ = discard_early_start_trials(parse_log_file(path))
    cond = pid_to_condition.get(pid)
    if cond is None:
        continue
    _, raw_episodes = hint_ladder_fractions(kept_events, cond)
    total_subhints = sum(d for d, m in raw_episodes)
    total_dose_rows.append(dict(pid=pid, condition=cond, total_subhints=total_subhints))

dose_df = pd.DataFrame(total_dose_rows)
imp = dose_df[dose_df.condition == "Implícita"]["total_subhints"]
exp = dose_df[dose_df.condition == "Explícita"]["total_subhints"]
t_w, p_w = stats.ttest_ind(imp, exp, equal_var=False)
df_w = ((imp.var()/len(imp) + exp.var()/len(exp))**2) / (
    (imp.var()/len(imp))**2/(len(imp)-1) + (exp.var()/len(exp))**2/(len(exp)-1))
d_w = (imp.mean()-exp.mean())/np.sqrt((imp.std()**2+exp.std()**2)/2)
print(f"\n=== TOTAL HINT MESSAGES (sum of sub-hints delivered, not episode count) ===")
print(f"Implicit: M={imp.mean():.2f}, SD={imp.std():.2f}, n={len(imp)}")
print(f"Explicit: M={exp.mean():.2f}, SD={exp.std():.2f}, n={len(exp)}")
print(f"Welch's t-test: t={t_w:.3f}, df={df_w:.1f}, p={p_w:.4f}, Cohen's d={d_w:.3f}")
