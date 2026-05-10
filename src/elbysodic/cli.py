"""Command-line entrypoint for the Elbysodic app."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.services import default_database_path, initialize_database
from elbysodic.services.bootstrap import bootstrap_admin
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

    if command == "bootstrap-admin":
        db_path = _bootstrap_admin(args)
        sys.stdout.write(f"bootstrapped admin at {db_path}\n")
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
        "bootstrap-admin",
        parents=[shared],
        help="Create or promote the first production admin membership.",
    )
    bootstrap.add_argument("--email", required=True, help="Admin login email.")
    bootstrap.add_argument("--username", required=True, help="Community-local admin username.")
    bootstrap.add_argument("--display-name", required=True, help="Rendered admin display name.")
    bootstrap.add_argument(
        "--community-name",
        help=(
            "Target community name. Required when multiple communities exist; created when missing."
        ),
    )
    bootstrap.add_argument(
        "--reset-password",
        action="store_true",
        help="Reset the password when the user already exists.",
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


def _bootstrap_admin(args: argparse.Namespace) -> Path:
    password = _prompt_password(confirm=True)
    db_path = initialize_database(args.db_path)
    connection = connect(db_path)
    try:
        create_schema(connection)
        result = bootstrap_admin(
            ForumRepository(connection),
            email=args.email,
            password=password,
            username=args.username,
            display_name=args.display_name,
            community_name=args.community_name,
            reset_password=args.reset_password,
        )
    finally:
        connection.close()

    created = []
    if result.created_community:
        created.append("community")
    if result.created_user:
        created.append("user")
    if result.reset_password:
        created.append("password")
    if result.created_membership:
        created.append("membership")
    if result.promoted_membership:
        created.append("membership-role")
    changed = ", ".join(created) if created else "no changes"
    sys.stdout.write(
        "admin "
        f"{result.user.email} -> {result.community.name} "
        f"(@{result.membership.username}, {result.role.name}); {changed}\n"
    )
    return db_path


def _prompt_password(*, confirm: bool) -> str:
    password = getpass.getpass("Password: ")
    if not password:
        raise SystemExit("password is required")
    if confirm:
        repeated = getpass.getpass("Confirm password: ")
        if password != repeated:
            raise SystemExit("passwords do not match")
    return password
