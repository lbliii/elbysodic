"""Prepare and verify a redacted scrypt-to-argon2 staging login smoke."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from chirp.security import passwords as chirp_passwords

from elbysodic.db.repository import ForumRepository
from elbysodic.db.schema import connect
from elbysodic.services.auth import SEED_LOGIN_PHRASE
from elbysodic.services.forum import default_database_path

STAGING_ENV = "staging"
TARGET_ACCOUNT = "writer@example.com"
DEMO_HASH = "-".join(("dev", "password", "hash"))


def _hash_format(password_hash: str) -> str:
    if password_hash == DEMO_HASH:
        return "demo-seed"
    if password_hash.startswith("pbkdf2_sha256$"):
        return "pbkdf2-sha256"
    if password_hash.startswith("$scrypt$"):
        return "scrypt"
    if password_hash.startswith("$argon2id$"):
        return "argon2id"
    return "unknown"


def _require_staging_demo() -> None:
    environment = (os.environ.get("ELBYSODIC_ENV") or "").strip().lower()
    demo_mode = (os.environ.get("ELBYSODIC_DEMO_MODE") or "").strip().lower()
    if environment != STAGING_ENV or demo_mode not in {"1", "true", "yes", "on"}:
        raise RuntimeError("password rehash smoke requires staging demo mode")


def _repository(database_path: Path) -> tuple[ForumRepository, object]:
    if not database_path.is_file():
        raise RuntimeError("password rehash smoke database does not exist")
    connection = connect(database_path, check_same_thread=False)
    return ForumRepository(connection), connection


def _status(database_path: Path) -> str:
    repo, connection = _repository(database_path)
    try:
        return _hash_format(repo.get_user_by_email(TARGET_ACCOUNT).password_hash)
    finally:
        connection.close()


def _prepare(database_path: Path) -> tuple[str, str]:
    repo, connection = _repository(database_path)
    try:
        user = repo.get_user_by_email(TARGET_ACCOUNT)
        before = _hash_format(user.password_hash)
        if before == "scrypt":
            return before, before
        if before not in {"demo-seed", "argon2id"}:
            raise RuntimeError(f"refusing to replace unexpected fixture format: {before}")
        legacy_hash = chirp_passwords._hash_scrypt(SEED_LOGIN_PHRASE)
        if not repo.update_user_password_hash(
            user.id,
            expected_hash=user.password_hash,
            new_hash=legacy_hash,
        ):
            raise RuntimeError("fixture account changed concurrently; retry from status")
        return before, "scrypt"
    finally:
        connection.close()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "prepare", "verify"))
    parser.add_argument("--db-path", type=Path, default=default_database_path())
    parser.add_argument(
        "--confirm-staging-write",
        action="store_true",
        help="Required for prepare; confirms one seeded staging hash may be replaced.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    _require_staging_demo()
    if args.action == "prepare":
        if not args.confirm_staging_write:
            raise RuntimeError("prepare requires --confirm-staging-write")
        before, after = _prepare(args.db_path)
        print(f"rehash smoke prepared: account=seeded-writer before={before} after={after}")
        return 0

    current = _status(args.db_path)
    if args.action == "verify" and current != "argon2id":
        raise RuntimeError(f"password rehash smoke expected argon2id, found {current}")
    print(f"rehash smoke {args.action}: account=seeded-writer format={current}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
