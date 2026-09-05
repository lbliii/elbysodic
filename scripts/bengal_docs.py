"""Build the Bengal handbook from Elbysodic's canonical ``docs/`` tree.

Bengal 0.5.1 loads ``build.content_dir`` correctly but its build orchestrator
still discovers ``<site>/content``. This adapter stages the three public
handbook sections under that expected path without duplicating their source of
truth. It can be removed when the pinned Bengal release honors the configured
content directory end to end.
"""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PUBLIC_SECTIONS = ("product", "architecture", "operations")


def _run(*args: str) -> None:
    print(f"+ {shlex.join(args)}", flush=True)
    # Arguments are assembled internally and the executable is resolved from
    # the active environment; no user-provided shell input reaches this call.
    subprocess.run(args, check=True)  # noqa: S603


def _bengal() -> str:
    environment_executable = Path(sys.executable).with_name("bengal")
    executable = (
        str(environment_executable) if environment_executable.is_file() else shutil.which("bengal")
    )
    if executable is None:
        raise SystemExit("Bengal is not installed. Run `uv sync --group docs --frozen` first.")
    return executable


def _stage_site(stage: Path) -> None:
    shutil.copy2(ROOT / "bengal.toml", stage / "bengal.toml")
    content = stage / "content"
    content.mkdir()
    shutil.copy2(DOCS / "index.md", content / "index.md")
    for section in PUBLIC_SECTIONS:
        shutil.copytree(DOCS / section, content / section)


def _complete_generated_contract(output: Path) -> None:
    """Supply artifacts referenced unconditionally by Bengal's 0.5 theme."""
    shutil.copy2(ROOT / "site" / "static" / "rss.xml", output / "rss.xml")
    shutil.copy2(DOCS / "index.md", output / "index.md")


def _publish_local_artifact(output: Path) -> None:
    destination = ROOT / "public"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(output, destination)
    print(f"Handbook artifact: {destination}")


def _build(stage: Path, *, validate: bool) -> None:
    bengal = _bengal()
    source = str(stage)
    config = str(stage / "bengal.toml")
    output = stage / "public"

    if validate:
        _run(bengal, "check", "--source", source, "--style", "ci", "--limit", "0")

    _run(
        bengal,
        "build",
        "--source",
        source,
        "--config",
        config,
        "--strict",
        "--clean-output",
        "--no-incremental",
        "--style",
        "ci",
    )
    _complete_generated_contract(output)

    if validate:
        _run(
            bengal,
            "audit",
            "--source",
            source,
            "--output",
            str(output),
            "--style",
            "ci",
            "--limit",
            "0",
        )

    _publish_local_artifact(output)


def _preview(stage: Path) -> None:
    bengal = _bengal()
    _run(
        bengal,
        "preview",
        "--source",
        str(stage),
        "--config",
        str(stage / "bengal.toml"),
        "--strict",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check", "preview"))
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="elbysodic-bengal-") as temp_dir:
        stage = Path(temp_dir)
        _stage_site(stage)
        if args.command == "preview":
            _preview(stage)
        else:
            _build(stage, validate=args.command == "check")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
