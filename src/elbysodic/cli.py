"""Command-line entrypoint for the Elbysodic app."""

from __future__ import annotations

import signal
import sqlite3
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated

from milo import CLI, Context, Description, Option

from elbysodic.services import (
    bootstrap_first_realm,
    create_services,
    default_database_path,
    initialize_database,
)
from elbysodic.web.app import create_app
from elbysodic.web.pounce_railway import apply_railway_pounce_defaults

HUMAN_COMMAND_SURFACES = ("cli", "llms")
COMMAND_NAMES = frozenset({"serve", "init-db", "seed-demo", "bootstrap-first-realm", "dev"})
OPTIONS_WITH_VALUES = frozenset(
    {
        "--db-path",
        "--host",
        "--port",
        "--completions",
        "-o",
        "--output-file",
    }
)
BUILTIN_FLAGS = frozenset(
    {
        "-h",
        "--help",
        "--version",
        "--llms-txt",
        "--mcp",
        "--mcp-install",
        "--mcp-uninstall",
        "--completions",
    }
)
DB_PATH_DESCRIPTION = (
    "SQLite database path. Defaults to ELBYSODIC_DB_PATH, then "
    "RAILWAY_VOLUME_MOUNT_PATH/elbysodic.sqlite3, then var/elbysodic.sqlite3."
)


def main(argv: list[str] | None = None) -> None:
    """Run the single Milo-backed Elbysodic CLI runtime."""

    raw_args = list(sys.argv[1:] if argv is None else argv)
    cli.run(_normalize_argv(raw_args))


def build_cli() -> CLI:
    """Build the complete typed command tree."""

    app_cli = CLI(
        name="elbysodic",
        description="Run and maintain an Elbysodic play-by-post studio.",
        version="0.1.0",
    )

    @app_cli.command(
        "serve",
        description="Run the web server.",
        surfaces=HUMAN_COMMAND_SURFACES,
        annotations={"destructiveHint": False, "idempotentHint": False},
        display_result=False,
    )
    def serve(
        db_path: Annotated[
            str,
            Option(metavar="PATH"),
            Description(DB_PATH_DESCRIPTION),
        ] = "",
        host: Annotated[
            str,
            Option(metavar="HOST"),
            Description("Host interface for the web server."),
        ] = "127.0.0.1",
        port: Annotated[
            int,
            Option(metavar="PORT"),
            Description("Port for the web server."),
        ] = 8000,
        debug: Annotated[
            bool,
            Option(),
            Description("Enable or disable Chirp debug mode."),
        ] = True,
        seed_demo: Annotated[
            bool,
            Option(),
            Description("Seed demo data during app startup."),
        ] = False,
    ) -> None:
        """Run the Elbysodic web application until it receives a stop signal."""

        _run_server(
            debug=debug,
            db_path=_coerce_db_path(db_path),
            seed_demo=seed_demo,
            host=host,
            port=port,
            stop_on_sighup=debug,
        )

    @app_cli.command(
        "init-db",
        description="Create the SQLite schema.",
        surfaces=HUMAN_COMMAND_SURFACES,
        annotations={"destructiveHint": False, "idempotentHint": True},
    )
    def init_db(
        db_path: Annotated[
            str,
            Option(metavar="PATH"),
            Description(DB_PATH_DESCRIPTION),
        ] = "",
        seed: Annotated[
            bool,
            Option(),
            Description("Also seed demo forum data after creating the schema."),
        ] = False,
    ) -> str:
        """Create the database schema and optionally seed local demo data."""

        initialized_path = initialize_database(_coerce_db_path(db_path), seed_demo=seed)
        return f"initialized {initialized_path}"

    @app_cli.command(
        "seed-demo",
        description="Create schema and idempotently seed demo data.",
        surfaces=HUMAN_COMMAND_SURFACES,
        annotations={"destructiveHint": True, "idempotentHint": True},
    )
    def seed_demo(
        db_path: Annotated[
            str,
            Option(metavar="PATH"),
            Description(DB_PATH_DESCRIPTION),
        ] = "",
    ) -> str:
        """Create the schema and idempotently seed the local demo realms."""

        initialized_path = initialize_database(_coerce_db_path(db_path), seed_demo=True)
        return f"seeded {initialized_path}"

    @app_cli.command(
        "bootstrap-first-realm",
        description="Create the first empty configured realm and director account.",
        surfaces=HUMAN_COMMAND_SURFACES,
        annotations={"destructiveHint": True, "idempotentHint": False},
    )
    def bootstrap_realm(
        realm_name: Annotated[
            str,
            Option(metavar="NAME"),
            Description("Name of the first realm."),
        ],
        realm_slug: Annotated[
            str,
            Option(metavar="SLUG"),
            Description("URL slug for the first realm."),
        ],
        director_email: Annotated[
            str,
            Option(metavar="EMAIL"),
            Description("Email address for the first director login account."),
        ],
        director_password: Annotated[
            str,
            Option(metavar="PASSWORD"),
            Description("Initial password for the first director login account."),
        ],
        director_username: Annotated[
            str,
            Option(metavar="USERNAME"),
            Description("Community-local username for the first director membership."),
        ],
        director_name: Annotated[
            str,
            Option(metavar="NAME"),
            Description("Community-local display name for the first director membership."),
        ],
        db_path: Annotated[
            str,
            Option(metavar="PATH"),
            Description(DB_PATH_DESCRIPTION),
        ] = "",
    ) -> str:
        """Create the first realm and its community-local director identity."""

        result = bootstrap_first_realm(
            _coerce_db_path(db_path),
            realm_name=realm_name,
            realm_slug=realm_slug,
            director_email=director_email,
            director_password=director_password,
            director_username=director_username,
            director_display_name=director_name,
        )
        return (
            "created first realm "
            f"{result.community.slug} with director membership {result.membership.username}"
        )

    dev = app_cli.group(
        "dev",
        description="Developer workflows for local Elbysodic work.",
    )

    @dev.command(
        "preview",
        description="Prepare seeded demo data and run the local preview server.",
        surfaces=HUMAN_COMMAND_SURFACES,
        display_result=False,
    )
    def preview(
        ctx: Context,
        db_path: Annotated[
            str,
            Option(metavar="PATH"),
            Description(DB_PATH_DESCRIPTION),
        ] = "",
        host: Annotated[
            str,
            Option(metavar="HOST"),
            Description("Host interface for the local preview server."),
        ] = "127.0.0.1",
        port: Annotated[
            int,
            Option(metavar="PORT"),
            Description("Port for the local preview server."),
        ] = 8001,
        debug: Annotated[
            bool,
            Option(),
            Description("Enable or disable Chirp debug mode."),
        ] = True,
        seed_demo: Annotated[
            bool,
            Option(),
            Description("Seed demo data before starting the preview."),
        ] = True,
    ) -> None:
        """Run a seeded local preview on the standard development port."""

        resolved_db_path = _coerce_db_path(db_path)
        initialized_path = initialize_database(resolved_db_path, seed_demo=seed_demo)
        ctx.log(f"preview database ready {initialized_path}")
        ctx.log(f"serving local preview at http://{host}:{port}/")
        _run_server(
            debug=debug,
            db_path=initialized_path,
            seed_demo=False,
            host=host,
            port=port,
            stop_on_sighup=debug,
        )

    @dev.command(
        "check",
        description="Run the standard local developer verification gate.",
        surfaces=HUMAN_COMMAND_SURFACES,
        display_result=False,
    )
    def check(
        ctx: Context,
        quick: Annotated[
            bool,
            Option(),
            Description("Run the focused CLI tests instead of the full test suite."),
        ] = False,
    ) -> None:
        """Run the standard local verification commands."""

        run_developer_checks(quick=quick, ctx=ctx)

    db = dev.group("db", description="SQLite maintenance helpers for local work.")

    @db.command(
        "checkpoint",
        description="Checkpoint the local SQLite WAL file.",
        surfaces=HUMAN_COMMAND_SURFACES,
    )
    def checkpoint(
        db_path: Annotated[
            str,
            Option(metavar="PATH"),
            Description(DB_PATH_DESCRIPTION),
        ] = "",
    ) -> str:
        """Run a best-effort TRUNCATE checkpoint against a local database."""

        source_path = _coerce_db_path(db_path)
        result = checkpoint_database(source_path)
        return (
            "checkpointed "
            f"{result.path} "
            f"busy={result.busy} log={result.log_frames} checkpointed={result.checkpointed_frames}"
        )

    @db.command(
        "backup",
        description="Create an online SQLite backup of the local database.",
        surfaces=HUMAN_COMMAND_SURFACES,
    )
    def backup(
        db_path: Annotated[
            str,
            Option(metavar="PATH"),
            Description(DB_PATH_DESCRIPTION),
        ] = "",
        output: Annotated[
            str,
            Option(metavar="PATH"),
            Description("Destination path for the integrity-checked backup."),
        ] = "",
        overwrite: Annotated[
            bool,
            Option(),
            Description("Replace an existing backup file."),
        ] = False,
    ) -> str:
        """Copy a local database using SQLite's online backup API."""

        source_path = _coerce_db_path(db_path)
        if output.strip() == "":
            raise ValueError("output is required")
        backup_path = backup_database(source_path, Path(output), overwrite=overwrite)
        return f"backed up {source_path} to {backup_path}"

    return app_cli


def developer_check_commands(*, quick: bool = False) -> list[list[str]]:
    test_command = ["uv", "run", "pytest", "tests/test_cli.py", "-q", "--tb=short"]
    if not quick:
        test_command = ["uv", "run", "pytest", "-q", "--tb=short"]
    return [
        ["uv", "run", "ruff", "check", "."],
        ["uv", "run", "ruff", "format", ".", "--check"],
        test_command,
        ["uv", "run", "ty", "check", "src/elbysodic/", "tests/"],
        ["uv", "run", "milo", "verify", "src/elbysodic/cli.py"],
        [
            "uv",
            "run",
            "python",
            "-c",
            "from elbysodic.web import create_app; "
            "create_app(debug=False, db_path=':memory:').check()",
        ],
    ]


def run_developer_checks(*, quick: bool = False, ctx: Context | None = None) -> None:
    active_context = ctx or Context(color=False)
    for command in developer_check_commands(quick=quick):
        active_context.log(f"$ {' '.join(command)}")
        completed = subprocess.run(  # noqa: S603 - commands are fixed gates.
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if completed.stdout:
            active_context.log(completed.stdout.rstrip())
        if completed.returncode != 0:
            raise SystemExit(completed.returncode)


class CheckpointResult:
    def __init__(self, *, path: Path, busy: int, log_frames: int, checkpointed_frames: int) -> None:
        self.path = path
        self.busy = busy
        self.log_frames = log_frames
        self.checkpointed_frames = checkpointed_frames


def checkpoint_database(path: Path) -> CheckpointResult:
    if str(path) == ":memory:":
        raise ValueError("checkpoint requires a filesystem database path")
    if not path.exists():
        raise FileNotFoundError(path)
    connection = connect_for_maintenance(path)
    try:
        row = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        return CheckpointResult(
            path=path,
            busy=int(row[0]),
            log_frames=int(row[1]),
            checkpointed_frames=int(row[2]),
        )
    finally:
        connection.close()


def backup_database(source_path: Path, backup_path: Path, *, overwrite: bool = False) -> Path:
    if str(source_path) == ":memory:":
        raise ValueError("backup requires a filesystem database path")
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    if backup_path.exists() and not overwrite:
        raise FileExistsError(backup_path)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if backup_path.exists():
        backup_path.unlink()
    source = connect_for_maintenance(source_path)
    destination = sqlite3.connect(backup_path)
    try:
        source.backup(destination)
        integrity = destination.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"backup integrity check failed: {integrity}")
    finally:
        destination.close()
        source.close()
    return backup_path


def connect_for_maintenance(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(path)


def _run_server(
    *,
    debug: bool,
    db_path: Path,
    seed_demo: bool,
    host: str,
    port: int,
    stop_on_sighup: bool,
) -> None:
    services = create_services(db_path, seed_demo=seed_demo)
    app = create_app(debug=debug, services=services)
    if not debug:
        apply_railway_pounce_defaults()
    try:
        with _sighup_as_keyboard_interrupt(enabled=stop_on_sighup):
            app.run(host=host, port=port)
    finally:
        services.close()


@contextmanager
def _sighup_as_keyboard_interrupt(*, enabled: bool) -> Iterator[None]:
    if not enabled or not hasattr(signal, "SIGHUP"):
        yield
        return
    previous_handler = signal.getsignal(signal.SIGHUP)

    def handle_sighup(signum: int, frame: object) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGHUP, handle_sighup)
    try:
        yield
    finally:
        signal.signal(signal.SIGHUP, previous_handler)


def _coerce_db_path(db_path: str | Path | None) -> Path:
    if db_path is None or str(db_path).strip() == "":
        return default_database_path()
    return Path(db_path)


def _normalize_argv(raw_args: list[str]) -> list[str]:
    """Preserve the mature argparse argv while dispatching through Milo."""

    if not raw_args:
        return ["serve"]

    command_index = _command_index(raw_args)
    if command_index is not None:
        if command_index == 0:
            normalized = raw_args
        else:
            command = raw_args[command_index]
            normalized = [command, *raw_args[:command_index], *raw_args[command_index + 1 :]]
        return _normalize_true_default_flags(normalized)

    if any(argument in BUILTIN_FLAGS for argument in raw_args):
        return raw_args
    return _normalize_true_default_flags(["serve", *raw_args])


def _command_index(args: list[str]) -> int | None:
    """Find a command token without mistaking an option value for one."""

    expects_value = False
    for index, argument in enumerate(args):
        if expects_value:
            expects_value = False
            continue
        option, separator, _value = argument.partition("=")
        if option in OPTIONS_WITH_VALUES and not separator:
            expects_value = True
            continue
        if argument in COMMAND_NAMES:
            return index
    return None


def _normalize_true_default_flags(args: list[str]) -> list[str]:
    """Accept argparse's redundant positive forms for default-true flags."""

    if args and args[0] == "serve":
        args = _collapse_boolean_pair(args, positive="--debug", negative="--no-debug")
    if args[:2] == ["dev", "preview"]:
        args = _collapse_boolean_pair(args, positive="--debug", negative="--no-debug")
        args = _collapse_boolean_pair(
            args,
            positive="--seed-demo",
            negative="--no-seed-demo",
        )
    return args


def _collapse_boolean_pair(args: list[str], *, positive: str, negative: str) -> list[str]:
    positions = [
        (index, argument) for index, argument in enumerate(args) if argument in {positive, negative}
    ]
    if not positions:
        return args
    enabled = positions[-1][1] == positive
    collapsed = [argument for argument in args if argument not in {positive, negative}]
    if not enabled:
        collapsed.append(negative)
    return collapsed


cli = build_cli()


if __name__ == "__main__":
    main()
