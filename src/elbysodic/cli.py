"""Command-line entrypoint for the Elbysodic app."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from elbysodic.services import default_database_path, initialize_database
from elbysodic.web.app import create_app


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    command = args.command or "serve"
    if command == "init-db":
        db_path = initialize_database(args.db_path, seed_demo=not args.no_seed)
        sys.stdout.write(f"initialized {db_path}\n")
        return

    if command == "seed-demo":
        db_path = initialize_database(args.db_path, seed_demo=True)
        sys.stdout.write(f"seeded {db_path}\n")
        return

    app = create_app(debug=args.debug, db_path=args.db_path)
    app.run(host=args.host, port=args.port)


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
        "--no-seed",
        action="store_true",
        help="Create the schema without demo forum data.",
    )

    subparsers.add_parser(
        "seed-demo",
        parents=[shared],
        help="Create schema and idempotently seed demo data.",
    )
    serve = subparsers.add_parser("serve", parents=[shared], help="Run the web server.")
    _add_serve_options(serve, include_defaults=False)
    return parser


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
