"""Command-line entrypoint for the Elbysodic development app."""

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

    app = create_app(db_path=args.db_path)
    app.run(port=args.port)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="elbysodic")
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "--db-path",
        type=Path,
        default=default_database_path(),
        help="SQLite database path. Defaults to ELBYSODIC_DB_PATH or var/elbysodic.sqlite3.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=default_database_path(),
        help="SQLite database path. Defaults to ELBYSODIC_DB_PATH or var/elbysodic.sqlite3.",
    )
    parser.add_argument("--port", type=int, default=8000, help="Port for the development server.")
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
    serve = subparsers.add_parser("serve", parents=[shared], help="Run the development server.")
    serve.add_argument("--port", type=int, default=8000, help="Port for the development server.")
    return parser
