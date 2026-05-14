from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/check_theme_css.py"
SPEC = importlib.util.spec_from_file_location("check_theme_css", SCRIPT_PATH)
assert SPEC is not None
check_theme_css = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(check_theme_css)


def test_theme_css_manifest_and_owner_ledgers_are_valid() -> None:
    assert check_theme_css.validate_theme_css() == []
