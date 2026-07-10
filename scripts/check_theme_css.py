"""Validate Elbysodic theme CSS import and ownership conventions."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
THEME_ENTRYPOINT = REPO_ROOT / "src/elbysodic/web/static/elbysodic-theme.css"
THEME_DIR = REPO_ROOT / "src/elbysodic/web/static/elbysodic-theme"
PAGES_DIR = REPO_ROOT / "src/elbysodic/web/pages"
EMPTY_SELECTOR_FILES = {
    "90-legacy.css": "legacy ledger",
}
LEGACY_CHIRPUI_UTILITY_CLASSES = frozenset(
    {
        "chirpui-clamp-2",
        "chirpui-clamp-3",
        "chirpui-display",
        "chirpui-display--xl",
        "chirpui-focus-ring",
        "chirpui-font-2xl",
        "chirpui-font-base",
        "chirpui-font-lg",
        "chirpui-font-medium",
        "chirpui-font-mono",
        "chirpui-font-sm",
        "chirpui-font-xl",
        "chirpui-font-xs",
        "chirpui-list-reset",
        "chirpui-mb-md",
        "chirpui-measure-lg",
        "chirpui-measure-md",
        "chirpui-measure-sm",
        "chirpui-min-w-0",
        "chirpui-mt-md",
        "chirpui-mt-sm",
        "chirpui-placeholder-inline",
        "chirpui-prose-lg",
        "chirpui-prose-sm",
        "chirpui-scroll-x",
        "chirpui-text-muted",
        "chirpui-truncate",
        "chirpui-ui-base",
        "chirpui-ui-bold",
        "chirpui-ui-label",
        "chirpui-ui-lg",
        "chirpui-ui-medium",
        "chirpui-ui-meta",
        "chirpui-ui-normal",
        "chirpui-ui-semibold",
        "chirpui-ui-sm",
        "chirpui-ui-title",
        "chirpui-ui-xl",
        "chirpui-ui-xs",
        "chirpui-visually-hidden",
    }
)
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
_CHIRPUI_CLASS_RE = re.compile(r"\bchirpui-[a-z0-9-]+\b")


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
            references.extend(
                (path, line_number, match.group(1), bool(match.group(2)))
                for match in _CUSTOM_PROPERTY_REFERENCE_RE.finditer(line)
            )

    allowed = definitions | EXTERNALLY_PROVIDED_PROPERTIES
    return [
        f"{path.relative_to(REPO_ROOT)}:{line_number} references undefined custom property {name}"
        for path, line_number, name, has_fallback in references
        if name not in allowed and not has_fallback
    ]


def legacy_chirpui_utility_errors(pages_dir: Path = PAGES_DIR) -> list[str]:
    errors: list[str] = []
    for path in sorted(pages_dir.rglob("*.html")):
        try:
            display_path = path.relative_to(REPO_ROOT)
        except ValueError:
            display_path = path
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            legacy_classes = sorted(
                set(_CHIRPUI_CLASS_RE.findall(line)) & LEGACY_CHIRPUI_UTILITY_CLASSES
            )
            errors.extend(
                f"{display_path}:{line_number} uses legacy Chirp-UI utility {name}"
                for name in legacy_classes
            )
    return errors


def validate_theme_css(
    *,
    entrypoint: Path = THEME_ENTRYPOINT,
    theme_dir: Path = THEME_DIR,
    pages_dir: Path = PAGES_DIR,
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
    errors.extend(legacy_chirpui_utility_errors(pages_dir))

    return errors


def main() -> int:
    errors = validate_theme_css()
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
