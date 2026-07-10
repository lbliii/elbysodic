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


def test_legacy_chirpui_utility_gate_reports_template_and_line(tmp_path: Path) -> None:
    template = tmp_path / "sample.html"
    template.write_text(
        '<span class="chirpui-visually-hidden">Scene label</span>\n',
        encoding="utf-8",
    )

    errors = check_theme_css.legacy_chirpui_utility_errors(tmp_path)

    assert errors == [f"{template}:1 uses legacy Chirp-UI utility chirpui-visually-hidden"]


def test_app_owned_accessibility_utilities_preserve_behavior() -> None:
    css = (check_theme_css.THEME_DIR / "15-app-utilities.css").read_text(encoding="utf-8")

    assert ".elbysodic-visually-hidden" in css
    for declaration in (
        "clip: rect(0, 0, 0, 0);",
        "height: 1px;",
        "overflow: clip;",
        "position: absolute;",
        "white-space: nowrap;",
        "width: 1px;",
    ):
        assert declaration in css
    assert ".elbysodic-text-muted" in css
    assert "color: var(--chirpui-text-muted);" in css
