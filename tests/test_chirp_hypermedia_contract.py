"""Regression proof for the committed chirp hypermedia contract baseline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from chirp.app import App

from elbysodic.web.contract_app import app as contract_app

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINE = REPO_ROOT / "tests" / "fixtures" / "chirp_hypermedia_baseline.json"
CHIRP_APP = "elbysodic.web.contract_app:app"


def test_contract_app_exports_chirp_app() -> None:
    assert isinstance(contract_app, App)


def test_committed_hypermedia_baseline_matches_current() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "chirp.cli",
            "check",
            CHIRP_APP,
            "--baseline",
            str(BASELINE),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
