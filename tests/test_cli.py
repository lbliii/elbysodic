from __future__ import annotations

from pathlib import Path

import pytest

from elbysodic import cli
from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.services import AppServices, initialize_database

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


def test_cli_bootstrap_first_realm_creates_empty_configured_realm(tmp_path, capsys) -> None:
    db_path = tmp_path / "forum.sqlite3"

    cli.main(
        [
            "bootstrap-first-realm",
            "--db-path",
            str(db_path),
            "--realm-name",
            "Starter Realm",
            "--realm-slug",
            "starter-realm",
            "--director-email",
            "director@example.com",
            "--director-password",
            "correct horse battery staple",
            "--director-username",
            "starlane",
            "--director-name",
            "Starter Director",
        ]
    )

    output = capsys.readouterr().out
    assert "created first realm starter-realm with director membership starlane" in output
    connection = connect(db_path)
    try:
        community_count = connection.execute("SELECT COUNT(*) FROM communities").fetchone()[0]
        board_count = connection.execute("SELECT COUNT(*) FROM boards").fetchone()[0]
        material_count = connection.execute("SELECT COUNT(*) FROM materials").fetchone()[0]
        sidebar_count = connection.execute("SELECT COUNT(*) FROM sidebar_sections").fetchone()[0]
        theme_count = connection.execute("SELECT COUNT(*) FROM themes").fetchone()[0]
        role = connection.execute("SELECT community_id, slug, is_admin FROM roles").fetchone()
        membership = connection.execute(
            "SELECT community_id, username, display_name FROM community_memberships"
        ).fetchone()
    finally:
        connection.close()

    assert community_count == 1
    assert board_count == 0
    assert material_count == 0
    assert sidebar_count > 0
    assert theme_count == 1
    assert dict(role) == {"community_id": 1, "slug": "director", "is_admin": 1}
    assert dict(membership) == {
        "community_id": 1,
        "username": "starlane",
        "display_name": "Starter Director",
    }
    with pytest.raises(ValueError, match="empty community table"):
        cli.main(
            [
                "bootstrap-first-realm",
                "--db-path",
                str(db_path),
                "--realm-name",
                "Second Realm",
                "--realm-slug",
                "second-realm",
                "--director-email",
                "second@example.com",
                "--director-password",
                "correct horse battery staple",
                "--director-username",
                "second",
                "--director-name",
                "Second Director",
            ]
        )


def test_first_realm_setup_rolls_back_partial_rows(monkeypatch) -> None:
    connection = connect(":memory:")
    create_schema(connection)
    repo = ForumRepository(connection)
    services = AppServices(repo, None)

    def fail_defaults(_community_id: int) -> None:
        raise RuntimeError("default setup failed")

    monkeypatch.setattr(repo, "ensure_sidebar_section_defaults", fail_defaults)
    initial_phrase = "correct horse battery staple"

    with pytest.raises(RuntimeError, match="default setup failed"):
        services.create_first_realm(
            realm_name="Broken Realm",
            realm_slug="broken-realm",
            director_email="director@example.com",
            director_password=initial_phrase,
            director_username="director",
            director_display_name="Director",
        )

    assert connection.execute("SELECT COUNT(*) FROM communities").fetchone()[0] == 0
    assert connection.execute("SELECT COUNT(*) FROM roles").fetchone()[0] == 0
    assert connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
    assert connection.execute("SELECT COUNT(*) FROM community_memberships").fetchone()[0] == 0
    assert connection.execute("SELECT COUNT(*) FROM sidebar_sections").fetchone()[0] == 0
