from __future__ import annotations

from pathlib import Path

import pytest

from elbysodic import cli
from elbysodic.db import ForumRepository, connect
from elbysodic.services import initialize_database
from elbysodic.services.auth import verify_password

RAILWAY_HOST = ".".join(("0", "0", "0", "0"))


class _FakeApp:
    def __init__(self, calls: dict[str, object]) -> None:
        self._calls = calls

    def run(self, *, host: str | None = None, port: int | None = None) -> None:
        self._calls["host"] = host
        self._calls["port"] = port


def test_cli_can_start_production_server_on_railway_host_and_port(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_create_app(*, debug: bool, db_path: Path, seed_demo: bool) -> _FakeApp:
        calls["debug"] = debug
        calls["db_path"] = db_path
        calls["seed_demo"] = seed_demo
        return _FakeApp(calls)

    monkeypatch.setattr(cli, "create_app", fake_create_app)

    cli.main(["--host", RAILWAY_HOST, "--port", "1234", "--no-debug"])

    assert calls["debug"] is False
    assert calls["seed_demo"] is False
    assert calls["host"] == RAILWAY_HOST
    assert calls["port"] == 1234


def test_cli_serve_subcommand_accepts_same_server_options(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_create_app(*, debug: bool, db_path: Path, seed_demo: bool) -> _FakeApp:
        calls["debug"] = debug
        calls["db_path"] = db_path
        calls["seed_demo"] = seed_demo
        return _FakeApp(calls)

    monkeypatch.setattr(cli, "create_app", fake_create_app)

    cli.main(["serve", "--host", RAILWAY_HOST, "--port", "5678", "--no-debug"])

    assert calls["debug"] is False
    assert calls["seed_demo"] is False
    assert calls["host"] == RAILWAY_HOST
    assert calls["port"] == 5678


def test_cli_serve_can_explicitly_seed_demo_data(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_create_app(*, debug: bool, db_path: Path, seed_demo: bool) -> _FakeApp:
        calls["debug"] = debug
        calls["db_path"] = db_path
        calls["seed_demo"] = seed_demo
        return _FakeApp(calls)

    monkeypatch.setattr(cli, "create_app", fake_create_app)

    cli.main(["serve", "--seed-demo"])

    assert calls["seed_demo"] is True


def test_cli_init_db_creates_schema_without_demo_seed_by_default(monkeypatch, tmp_path) -> None:
    calls: dict[str, object] = {}
    db_path = tmp_path / "forum.sqlite3"

    def fake_initialize_database(path: Path, *, seed_demo: bool) -> Path:
        calls["path"] = path
        calls["seed_demo"] = seed_demo
        return path

    monkeypatch.setattr(cli, "initialize_database", fake_initialize_database)

    cli.main(["init-db", "--db-path", str(db_path)])

    assert calls == {"path": db_path, "seed_demo": False}


def test_cli_init_db_can_explicitly_seed_demo_data(monkeypatch, tmp_path) -> None:
    calls: dict[str, object] = {}
    db_path = tmp_path / "forum.sqlite3"

    def fake_initialize_database(path: Path, *, seed_demo: bool) -> Path:
        calls["path"] = path
        calls["seed_demo"] = seed_demo
        return path

    monkeypatch.setattr(cli, "initialize_database", fake_initialize_database)

    cli.main(["init-db", "--db-path", str(db_path), "--seed"])

    assert calls == {"path": db_path, "seed_demo": True}


def test_initialize_database_leaves_demo_seed_explicit(tmp_path) -> None:
    db_path = tmp_path / "forum.sqlite3"

    initialize_database(db_path)
    connection = connect(db_path)
    try:
        community_count = connection.execute("SELECT COUNT(*) FROM communities").fetchone()[0]
    finally:
        connection.close()

    assert community_count == 0

    initialize_database(db_path, seed_demo=True)
    connection = connect(db_path)
    try:
        seeded_community_count = connection.execute("SELECT COUNT(*) FROM communities").fetchone()[
            0
        ]
    finally:
        connection.close()

    assert seeded_community_count > 0


def test_cli_bootstrap_admin_creates_first_admin_without_plaintext_output(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    db_path = tmp_path / "forum.sqlite3"
    monkeypatch.setattr(cli, "_prompt_password", lambda *, confirm: "correct horse battery staple")

    cli.main(
        [
            "bootstrap-admin",
            "--db-path",
            str(db_path),
            "--email",
            "Owner@Example.com",
            "--username",
            "llane",
            "--display-name",
            "L Lane",
            "--community-name",
            "Elbysodic",
        ]
    )

    output = capsys.readouterr().out
    assert "correct horse battery staple" not in output
    assert "owner@example.com -> Elbysodic (@llane, Admin)" in output
    connection = connect(db_path)
    try:
        repo = ForumRepository(connection)
        community = repo.get_community_by_name("Elbysodic")
        user = repo.get_user_by_email("owner@example.com")
        membership = repo.get_membership_for_user(community.id, user.id)
        role = repo.get_role(community.id, membership.role_id)
    finally:
        connection.close()

    assert role.is_admin is True
    assert membership.username == "llane"
    assert verify_password("correct horse battery staple", user.password_hash)


def test_cli_bootstrap_admin_is_idempotent_and_does_not_reset_password_by_default(
    monkeypatch,
    tmp_path,
) -> None:
    db_path = tmp_path / "forum.sqlite3"
    passwords = iter(["first password", "second password"])
    monkeypatch.setattr(cli, "_prompt_password", lambda *, confirm: next(passwords))
    base_args = [
        "bootstrap-admin",
        "--db-path",
        str(db_path),
        "--email",
        "owner@example.com",
        "--username",
        "llane",
        "--display-name",
        "L Lane",
        "--community-name",
        "Elbysodic",
    ]

    cli.main(base_args)
    cli.main(base_args)

    connection = connect(db_path)
    try:
        repo = ForumRepository(connection)
        community = repo.get_community_by_name("Elbysodic")
        user = repo.get_user_by_email("owner@example.com")
        memberships = repo.list_memberships(community.id)
        roles = connection.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
    finally:
        connection.close()

    assert len(memberships) == 1
    assert roles == 1
    assert verify_password("first password", user.password_hash)
    assert not verify_password("second password", user.password_hash)


def test_cli_bootstrap_admin_can_reset_existing_password(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "forum.sqlite3"
    passwords = iter(["first password", "second password"])
    monkeypatch.setattr(cli, "_prompt_password", lambda *, confirm: next(passwords))
    base_args = [
        "bootstrap-admin",
        "--db-path",
        str(db_path),
        "--email",
        "owner@example.com",
        "--username",
        "llane",
        "--display-name",
        "L Lane",
        "--community-name",
        "Elbysodic",
    ]

    cli.main(base_args)
    cli.main([*base_args, "--reset-password"])

    connection = connect(db_path)
    try:
        user = ForumRepository(connection).get_user_by_email("owner@example.com")
    finally:
        connection.close()

    assert not verify_password("first password", user.password_hash)
    assert verify_password("second password", user.password_hash)


def test_cli_bootstrap_admin_promotes_existing_membership(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "forum.sqlite3"
    initialize_database(db_path)
    connection = connect(db_path)
    try:
        repo = ForumRepository(connection)
        community = repo.create_community("existing", "Existing")
        member_role = repo.create_role(community.id, "member", "Member")
        existing_hash = "existing-login-hash"
        user = repo.create_user("owner@example.com", existing_hash)
        repo.create_membership(community.id, user.id, member_role.id, "llane", "L Lane")
    finally:
        connection.close()
    monkeypatch.setattr(cli, "_prompt_password", lambda *, confirm: "new password")

    cli.main(
        [
            "bootstrap-admin",
            "--db-path",
            str(db_path),
            "--email",
            "owner@example.com",
            "--username",
            "llane",
            "--display-name",
            "L Lane",
            "--community-name",
            "Existing",
        ]
    )

    connection = connect(db_path)
    try:
        repo = ForumRepository(connection)
        community = repo.get_community_by_name("Existing")
        user = repo.get_user_by_email("owner@example.com")
        membership = repo.get_membership_for_user(community.id, user.id)
        role = repo.get_role(community.id, membership.role_id)
    finally:
        connection.close()

    assert role.slug == "admin"
    assert role.is_admin is True
    assert user.password_hash == existing_hash


def test_cli_bootstrap_admin_requires_community_name_when_ambiguous(
    monkeypatch,
    tmp_path,
) -> None:
    db_path = tmp_path / "forum.sqlite3"
    initialize_database(db_path)
    connection = connect(db_path)
    try:
        repo = ForumRepository(connection)
        repo.create_community("one", "One")
        repo.create_community("two", "Two")
    finally:
        connection.close()
    monkeypatch.setattr(cli, "_prompt_password", lambda *, confirm: "password")

    with pytest.raises(ValueError, match="multiple communities exist"):
        cli.main(
            [
                "bootstrap-admin",
                "--db-path",
                str(db_path),
                "--email",
                "owner@example.com",
                "--username",
                "llane",
                "--display-name",
                "L Lane",
            ]
        )
