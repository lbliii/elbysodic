"""Validate Elbysodic theme CSS import and ownership conventions."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
THEME_ENTRYPOINT = REPO_ROOT / "src/elbysodic/web/static/elbysodic-theme.css"
THEME_DIR = REPO_ROOT / "src/elbysodic/web/static/elbysodic-theme"
EMPTY_SELECTOR_FILES = {
    "50-page-compositions.css": "composition review queue",
    "90-legacy.css": "legacy ledger",
}
EXTERNALLY_PROVIDED_PROPERTIES = {
    "--elbysodic-preview-accent",
    "--elbysodic-preview-bg",
    "--elbysodic-preview-border",
    "--elbysodic-preview-muted",
    "--elbysodic-preview-text",
}

_IMPORT_RE = re.compile(r'@import\s+url\("\./elbysodic-theme/([^"]+\.css)"\);')
_SELECTOR_RE = re.compile(r"^(?:[.#]|[a-z][\w-]*(?:[.#:\[]|\s|,|>|\+|~))", re.IGNORECASE)
_CUSTOM_PROPERTY_DEFINITION_RE = re.compile(r"(?<![\w-])(--[A-Za-z0-9_-]+)\s*:")
_CUSTOM_PROPERTY_REFERENCE_RE = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)(\s*,)?")


def imported_theme_files(entrypoint: Path = THEME_ENTRYPOINT) -> list[str]:
    return _IMPORT_RE.findall(entrypoint.read_text(encoding="utf-8"))


def theme_css_files(theme_dir: Path = THEME_DIR) -> list[str]:
    return sorted(path.name for path in theme_dir.glob("*.css"))


def file_selector_lines(path: Path) -> list[int]:
    selector_lines: list[int] = []
    in_comment = False

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("/*"):
            in_comment = "*/" not in stripped
            continue
        if in_comment:
            in_comment = "*/" not in stripped
            continue
        if stripped.startswith(("@", "}", "*")):
            continue
        if "{" in stripped and _SELECTOR_RE.match(stripped):
            selector_lines.append(line_number)

    return selector_lines


def theme_custom_property_errors(
    *,
    entrypoint: Path = THEME_ENTRYPOINT,
    theme_dir: Path = THEME_DIR,
) -> list[str]:
    files = [entrypoint, *sorted(theme_dir.glob("*.css"))]
    definitions: set[str] = set()
    references: list[tuple[Path, int, str, bool]] = []

    for path in files:
        text = path.read_text(encoding="utf-8")
        definitions.update(_CUSTOM_PROPERTY_DEFINITION_RE.findall(text))
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in _CUSTOM_PROPERTY_REFERENCE_RE.finditer(line):
                references.append((path, line_number, match.group(1), bool(match.group(2))))

    allowed = definitions | EXTERNALLY_PROVIDED_PROPERTIES
    return [
        f"{path.relative_to(REPO_ROOT)}:{line_number} references undefined custom property {name}"
        for path, line_number, name, has_fallback in references
        if name not in allowed and not has_fallback
    ]


def validate_theme_css(
    *,
    entrypoint: Path = THEME_ENTRYPOINT,
    theme_dir: Path = THEME_DIR,
) -> list[str]:
    errors: list[str] = []
    imports = imported_theme_files(entrypoint)
    files = theme_css_files(theme_dir)

    duplicate_imports = sorted({name for name in imports if imports.count(name) > 1})
    errors.extend(
        f"{entrypoint.relative_to(REPO_ROOT)} imports {name} more than once"
        for name in duplicate_imports
    )
    errors.extend(
        f"{entrypoint.relative_to(REPO_ROOT)} imports missing theme file {name}"
        for name in imports
        if name not in files
    )
    errors.extend(
        f"{theme_dir.relative_to(REPO_ROOT) / name} is not imported by "
        f"{entrypoint.relative_to(REPO_ROOT)}"
        for name in files
        if name not in imports
    )

    for name, purpose in EMPTY_SELECTOR_FILES.items():
        path = theme_dir / name
        if not path.exists():
            continue
        selector_lines = file_selector_lines(path)
        if selector_lines:
            lines = ", ".join(str(line) for line in selector_lines[:5])
            errors.append(
                f"{path.relative_to(REPO_ROOT)} should remain an empty {purpose}; "
                f"selectors found on line(s) {lines}"
            )

    errors.extend(theme_custom_property_errors(entrypoint=entrypoint, theme_dir=theme_dir))

    return errors


def main() -> int:
    errors = validate_theme_css()
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
