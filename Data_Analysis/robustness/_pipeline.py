"""Shared helper: load the main analysis pipeline (generate_report.py) without side effects.

generate_report.py recomputes every statistic and, at the very end, writes
Preliminary_Analysis_Report.md and h2_data_for_tost.csv next to itself. The scripts in this
folder only need the intermediate data frames, so this helper runs the pipeline inside a
temporary COPY of the repository layout (Data_Analysis/ and Elmo_Scripts/logs_deidentified/).
No file of this repository is modified.

Data frames exposed by the pipeline (all indexed by participant ID in column "ID_UP"):
    manip_merged     manipulation check responses; column 8 is the Self-Reliance single item
    log_merged       behavioral metrics from the session logs
    _ancova_merged   questionnaire dimension scores (IMI_Competence, BPNSS_Autonomy, ...)
    dose_df          hint dose per participant (total_subhints = "Hints Received")
Condition labels in the data are Portuguese: "Implícita" = Implicit, "Explícita" = Explicit.
"""
import contextlib
import io
import os
import runpy
import shutil
import tempfile
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_ANALYSIS = HERE.parent                      # .../Data_Analysis
REPO = DATA_ANALYSIS.parent                      # repository root
LOGS = REPO / "Elmo_Scripts" / "logs_deidentified"

_cache = {}


def load_pipeline(exclude_ids=""):
    """Run generate_report.py in a temporary copy and return its namespace (a dict).

    exclude_ids: comma-separated participant IDs to leave out of the whole pipeline
                 (the same EXCLUDE_IDS switch generate_report.py supports, e.g. "P31").
    """
    if exclude_ids in _cache:
        return _cache[exclude_ids]
    warnings.filterwarnings("ignore")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        shutil.copytree(DATA_ANALYSIS, tmp / "Data_Analysis",
                        ignore=shutil.ignore_patterns("robustness", "*.pdf"))
        shutil.copytree(LOGS, tmp / "Elmo_Scripts" / "logs_deidentified")
        old_env = os.environ.get("EXCLUDE_IDS")
        os.environ["EXCLUDE_IDS"] = exclude_ids
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                ns = runpy.run_path(str(tmp / "Data_Analysis" / "generate_report.py"),
                                    run_name="robustness_helper")
        finally:
            if old_env is None:
                os.environ.pop("EXCLUDE_IDS", None)
            else:
                os.environ["EXCLUDE_IDS"] = old_env
    _cache[exclude_ids] = ns
    return ns
