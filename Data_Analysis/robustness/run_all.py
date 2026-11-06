"""Run every robustness script and save the combined output to results_all.txt.

Run:  python3 run_all.py
Scripts are run in numeric order with the same Python interpreter. 02_site_adjusted.py is
skipped automatically when participant_site.csv is not present (see its docstring).
Dependencies: pandas, numpy, scipy, statsmodels, pingouin, openpyxl, matplotlib.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
out = []
for script in sorted(HERE.glob("0[0-9]_*.py")):
    out.append(f"######## {script.name}")
    result = subprocess.run([sys.executable, "-W", "ignore", str(script)], capture_output=True, text=True, cwd=HERE)
    out.append(result.stdout.rstrip())
    if result.returncode != 0:
        out.append(f"[exit code {result.returncode}] {result.stderr.strip().splitlines()[-1] if result.stderr.strip() else ''}")
    out.append("")
(HERE / "results_all.txt").write_text("\n".join(out), encoding="utf-8")
print("wrote", HERE / "results_all.txt")
