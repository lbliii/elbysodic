"""Validate Elbysodic towncrier fragment formatting."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


def validate_fragment(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8").strip()
    errors: list[str] = []

    if not text:
        errors.append("fragment is empty")
    if text.startswith("-"):
        errors.append("fragment should not start with a dash")
    if "\n\n" in text:
        errors.append("fragment should be one short paragraph")

    return errors


def main(argv: list[str] | None = None) -> int:
    paths = [Path(arg) for arg in (argv if argv is not None else sys.argv[1:])]
    config_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))["tool"]["towncrier"]
    fragment_root = (config_path.parent / config["directory"]).resolve()
    ignored = set(config.get("ignore", []))
    failed = False

    for path in paths:
        if path.resolve().parent == fragment_root and path.name in ignored:
            continue
        for error in validate_fragment(path):
            failed = True
            print(f"{path}: {error}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
