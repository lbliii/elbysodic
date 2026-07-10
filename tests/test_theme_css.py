from __future__ import annotations

import importlib.util
import re
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/check_theme_css.py"
SPEC = importlib.util.spec_from_file_location("check_theme_css", SCRIPT_PATH)
assert SPEC is not None
check_theme_css = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(check_theme_css)


def test_theme_css_manifest_and_owner_ledgers_are_valid() -> None:
    assert check_theme_css.validate_theme_css() == []


def test_cluster_alignment_modifiers_have_owned_layout_rules() -> None:
    theme_css = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(check_theme_css.THEME_DIR.glob("*.css"))
    )
    assert re.search(
        r"\.elbysodic-cluster--between\s*\{[^}]*justify-content:\s*space-between",
        theme_css,
        re.DOTALL,
    )
    assert re.search(
        r"\.elbysodic-cluster--end\s*\{[^}]*justify-content:\s*flex-end",
        theme_css,
        re.DOTALL,
    )

    pages_root = Path(__file__).resolve().parents[1] / "src/elbysodic/web/pages"
    modifiers = {
        modifier
        for path in pages_root.rglob("*.html")
        for modifier in re.findall(
            r"elbysodic-cluster--([a-z-]+)",
            path.read_text(encoding="utf-8"),
        )
    }
    assert modifiers <= {"between", "end"}
