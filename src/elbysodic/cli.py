"""Command-line entrypoint for the Elbysodic app."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from elbysodic.services import bootstrap_first_realm, default_database_path, initialize_database
from elbysodic.web.app import create_app


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

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

    app = create_app(debug=args.debug, db_path=args.db_path, seed_demo=args.seed_demo)
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
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        default=False if include_defaults else default,
        help="Seed demo data during app startup.",
    )
