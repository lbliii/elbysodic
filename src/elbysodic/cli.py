"""Command-line entrypoint for the Elbysodic app."""

from __future__ import annotations

import argparse
import signal
import sqlite3
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from milo import CLI

from elbysodic.checks import check_commands, run_commands
from elbysodic.services import (
    bootstrap_first_realm,
    create_services,
    default_database_path,
    initialize_database,
)
from elbysodic.web.app import create_app
from elbysodic.web.pounce_railway import apply_railway_pounce_defaults


def main(argv: list[str] | None = None) -> None:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    if raw_args and raw_args[0] == "dev":
        build_dev_cli().run(raw_args[1:])
        return

    parser = _build_parser()
    args = parser.parse_args(raw_args)

    command = args.command or "serve"
    if command == "init-db":
        db_path = initialize_database(args.db_path, seed_demo=args.seed)
        sys.stdout.write(f"initialized {db_path}\n")
        return

    if command == "seed-demo":
        db_path = initialize_database(args.db_path, seed_demo=True)
        sys.stdout.write(f"seeded {db_path}\n")
        return

    if command == "bootstrap-first-realm":
        result = bootstrap_first_realm(
            args.db_path,
            realm_name=args.realm_name,
            realm_slug=args.realm_slug,
            director_email=args.director_email,
            director_password=args.director_password,
            director_username=args.director_username,
            director_display_name=args.director_name,
        )
        sys.stdout.write(
            "created first realm "
            f"{result.community.slug} with director membership {result.membership.username}\n"
        )
        return

    _run_server(
        debug=args.debug,
        db_path=args.db_path,
        seed_demo=args.seed_demo,
        host=args.host,
        port=args.port,
        stop_on_sighup=args.debug,
    )


def build_dev_cli() -> CLI:
    """Build the Milo-backed developer workflow namespace."""

    dev_cli = CLI(
        name="elbysodic dev",
        description="Developer workflows for local Elbysodic work.",
        version="0.1.0",
    )

    @dev_cli.command(
        "preview",
        description="Prepare seeded demo data and run the local preview server.",
        annotations={"destructiveHint": False, "idempotentHint": True},
        display_result=False,
    )
    def preview(
        db_path: str = "",
        host: str = "127.0.0.1",
        port: int = 8001,
        debug: bool = True,
        seed_demo: bool = True,
    ) -> None:
        """Run a seeded local preview on the standard development port."""

        resolved_db_path = _coerce_db_path(db_path)
        initialized_path = initialize_database(resolved_db_path, seed_demo=seed_demo)
        sys.stdout.write(f"preview database ready {initialized_path}\n")
        sys.stdout.write(f"serving local preview at http://{host}:{port}/\n")
        sys.stdout.flush()
        _run_server(
            debug=debug,
            db_path=initialized_path,
            seed_demo=False,
            host=host,
            port=port,
            stop_on_sighup=debug,
        )

    @dev_cli.command(
        "check",
        description="Run the standard local developer verification gate.",
        annotations={"destructiveHint": False, "idempotentHint": True},
        display_result=False,
    )
    def check(quick: bool = False) -> None:
        """Run the standard local verification commands."""

        run_developer_checks(quick=quick)

    db = dev_cli.group("db", description="SQLite maintenance helpers for local work.")

    @db.command(
        "checkpoint",
        description="Checkpoint the local SQLite WAL file.",
        display_result=False,
    )
    def checkpoint(db_path: str = "") -> None:
        """Run a best-effort TRUNCATE checkpoint against a local database."""

        source_path = _coerce_db_path(db_path)
        result = checkpoint_database(source_path)
        sys.stdout.write(
            "checkpointed "
            f"{result.path} "
            f"busy={result.busy} log={result.log_frames} checkpointed={result.checkpointed_frames}\n"
        )

    @db.command(
        "backup",
        description="Create an online SQLite backup of the local database.",
        display_result=False,
    )
    def backup(db_path: str = "", output: str = "", overwrite: bool = False) -> None:
        """Copy a local database using SQLite's online backup API."""

        source_path = _coerce_db_path(db_path)
        if output.strip() == "":
            raise ValueError("output is required")
        backup_path = backup_database(source_path, Path(output), overwrite=overwrite)
        sys.stdout.write(f"backed up {source_path} to {backup_path}\n")

    return dev_cli


def developer_check_commands(*, quick: bool = False) -> list[list[str]]:
    return check_commands(full=True, quick=quick)


def run_developer_checks(*, quick: bool = False) -> None:
    run_commands(developer_check_commands(quick=quick))


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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="elbysodic")
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "--db-path",
        type=Path,
        default=default_database_path(),
        help=(
            "SQLite database path. Defaults to ELBYSODIC_DB_PATH, then "
            "RAILWAY_VOLUME_MOUNT_PATH/elbysodic.sqlite3, then var/elbysodic.sqlite3."
        ),
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=default_database_path(),
        help=(
            "SQLite database path. Defaults to ELBYSODIC_DB_PATH, then "
            "RAILWAY_VOLUME_MOUNT_PATH/elbysodic.sqlite3, then var/elbysodic.sqlite3."
        ),
    )
    _add_serve_options(parser, include_defaults=True)
    subparsers = parser.add_subparsers(dest="command")

    init_db = subparsers.add_parser(
        "init-db",
        parents=[shared],
        help="Create the SQLite schema.",
    )
    init_db.add_argument(
        "--seed",
        action="store_true",
        help="Also seed demo forum data after creating the schema.",
    )

    subparsers.add_parser(
        "seed-demo",
        parents=[shared],
        help="Create schema and idempotently seed demo data.",
    )
    bootstrap = subparsers.add_parser(
        "bootstrap-first-realm",
        parents=[shared],
        help="Create the first empty configured realm and director account.",
    )
    bootstrap.add_argument("--realm-name", required=True, help="Name of the first realm.")
    bootstrap.add_argument("--realm-slug", required=True, help="URL slug for the first realm.")
    bootstrap.add_argument(
        "--director-email",
        required=True,
        help="Email address for the first director login account.",
    )
    bootstrap.add_argument(
        "--director-password",
        required=True,
        help="Initial password for the first director login account.",
    )
    bootstrap.add_argument(
        "--director-username",
        required=True,
        help="Community-local username for the first director membership.",
    )
    bootstrap.add_argument(
        "--director-name",
        required=True,
        help="Community-local display name for the first director membership.",
    )
    serve = subparsers.add_parser("serve", parents=[shared], help="Run the web server.")
    _add_serve_options(serve, include_defaults=False)
    subparsers.add_parser(
        "dev",
        add_help=False,
        help="Run developer workflows powered by Milo.",
    )
    return parser


def _coerce_db_path(db_path: str | Path | None) -> Path:
    if db_path is None or str(db_path).strip() == "":
        return default_database_path()
    return Path(db_path)


def _add_serve_options(parser: argparse.ArgumentParser, *, include_defaults: bool) -> None:
    default: object = None if include_defaults else argparse.SUPPRESS
    parser.add_argument(
        "--host",
        default="127.0.0.1" if include_defaults else default,
        help="Host interface for the web server.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000 if include_defaults else default,
        help="Port for the web server.",
    )
    parser.add_argument(
        "--debug",
        action=argparse.BooleanOptionalAction,
        default=True if include_defaults else default,
        help="Enable or disable Chirp debug mode.",
    )
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        default=False if include_defaults else default,
        help="Seed demo data during app startup.",
    )
