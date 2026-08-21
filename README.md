# "It Was Me Who Corrected It": Designing and Evaluating Autonomy-Preserving Robotic Support for Older Adults

Code, materials, and analysis scripts accompanying the HRI 2027 submission (paper title above). Shared for transparency and reproducibility during anonymous review.

## Contents

```
Elmo_Scripts/                Robot control system (Wizard-of-Oz FSM, hint behaviors, GUI dashboard)
    logs_deidentified/       Per-session interaction logs, de-identified (see below)
Data_Analysis/
    generate_report.py       Main statistics pipeline (self-report, manipulation check, behavioral)
    generate_figure2.py      Regenerates the self-report subscale figure from the raw pipeline
    run_tost.py              TOST equivalence tests for H2 outcome measures
    thematic_coded_excerpts.csv   Coded interview excerpts underlying the thematic analysis
    Thematic_Analysis_Report.md
    Preliminary_Analysis_Report.md
    h2_data_for_tost.csv     Per-participant behavioral metrics used by run_tost.py
    raw_data_deidentified/   Survey responses (see below)
```

## What's included and what's not

This repository shares the code and data needed to reproduce every statistic reported in the paper, while protecting the privacy of a vulnerable participant population (older adults, several recruited through nursing homes and daycare centers).

**Included:**
- All robot control and Wizard-of-Oz dashboard code.
- All analysis and statistics scripts.
- Session interaction logs, with timestamps and internal file paths removed (only participant ID and event sequence retained).
- Survey response data (post-study questionnaires, manipulation check), and pre-study responses with demographic fields (age, sex, education, prior occupation) removed.
- Coded interview excerpts used in the thematic analysis.

**Not included:**
- Session video/audio recordings.
- Raw interview transcripts (the coded excerpts above are drawn from these).
- Pre-study demographic fields that, combined with small per-site sample sizes, could support re-identification.
- Any file mapping participant IDs to names.

Participant IDs used throughout (e.g. `A3`, `P16`, `M2`) match those used in the paper and supplementary material.

## Reproducing the analysis

`Data_Analysis/generate_report.py` is the main entry point; it reads from `raw_data_deidentified/` and `../Elmo_Scripts/logs_deidentified/` (relative to its own location) and regenerates `Preliminary_Analysis_Report.md`. `run_tost.py` and `generate_figure2.py` build on its output for the equivalence tests and the self-report figure, respectively.
