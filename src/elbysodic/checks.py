"""Canonical developer verification shared by the CLI, Make, and Poe."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _client_test_command(repo_root: Path | None = None) -> list[str]:
    root = repo_root or REPO_ROOT
    client_root = root / "tests" / "client"
    paths = sorted(client_root.glob("*.test.cjs"))
    if not paths:
        # The tooling leaf integrates before the composer test leaf.
        paths = [client_root / "composer.test.cjs"]
    return [
        "node",
        "--test",
        *(path.relative_to(root).as_posix() for path in paths),
    ]


def check_commands(
    *, full: bool = False, quick: bool = False, base: str = "origin/main"
) -> list[list[str]]:
    commands = [
        ["uv", "run", "ruff", "check", "."],
        ["uv", "run", "ruff", "format", ".", "--check"],
        ["uv", "run", "ty", "check", "src/elbysodic/", "tests/"],
        [
            "uv",
            "run",
            "python",
            "-c",
            "from elbysodic.web import create_app; "
            "create_app(debug=False, db_path=':memory:').check(warnings_as_errors=True)",
        ],
        ["uv", "run", "python", "scripts/kida_check.py"],
        ["uv", "run", "milo", "verify", "src/elbysodic/cli.py"],
        [
            "uv",
            "run",
            "--group",
            "docs",
            "--frozen",
            "python",
            "scripts/bengal_docs.py",
            "check",
        ],
        [
            "uv",
            "run",
            "chirp",
            "check",
            "elbysodic.web.contract_app:app",
            "--baseline",
            "tests/fixtures/chirp_hypermedia_baseline.json",
        ],
        _client_test_command(),
    ]
    if full:
        tests = ["tests/test_cli.py"] if quick else []
        commands.append(["uv", "run", "pytest", *tests, "-q", "--tb=short"])
        if not quick:
            commands.append(
                ["uv", "run", "chirp", "diff", "elbysodic.web.contract_app:app", "--base", base]
            )
    return commands


def run_commands(commands: list[list[str]], *, log: Callable[[str], None] | None = None) -> None:
    for command in commands:
        message = f"$ {' '.join(command)}"
        if log is None:
            sys.stdout.write(f"{message}\n")
            sys.stdout.flush()
        else:
            log(message)
        try:
            if log is None:
                result = subprocess.run(  # noqa: S603 -- fixed gate commands
                    command,
                    check=False,
                )
            else:
                result = subprocess.run(  # noqa: S603 -- fixed gate commands
                    command,
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
        except FileNotFoundError as exc:
            message = f"Developer check requires {command[0]!r} on PATH."
            if log is None:
                sys.stderr.write(f"{message}\n")
            else:
                log(message)
            raise SystemExit(127) from exc
        if log is not None and result.stdout:
            output = result.stdout
            if isinstance(output, bytes):
                output = output.decode(errors="replace")
            log(output.rstrip())
        if result.returncode:
            raise SystemExit(result.returncode)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true", help="Also run pytest and contract diff.")
    parser.add_argument("--quick", action="store_true", help="Narrow full pytest to CLI tests.")
    parser.add_argument("--base", default="origin/main", help="Contract diff base ref.")
    args = parser.parse_args(argv)
    run_commands(check_commands(full=args.full, quick=args.quick, base=args.base))


if __name__ == "__main__":
    main()
