import os
import subprocess
import sys
import shlex
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

def test_smoke_backtest_runs_30d_slice():
    """
    Runs a tiny backtest to ensure pipeline is wired.
    Skips if OFFLINE=1 (e.g., CI without data access).
    """
    if os.getenv("OFFLINE") == "1":
        return

    # tests/test_smoke_backtest.py
    cmd = (
        f"{sys.executable} -m src.backtester "
        f"--config {ROOT/'config'/'config.yaml'} "
        f"--ticker AAPL,MSFT,NVDA "
        f"--start-date 2024-12-02 --end-date 2024-12-06 "
        f"--no-interactive"
    )

    proc = subprocess.run(shlex.split(cmd), cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
    assert proc.returncode == 0

