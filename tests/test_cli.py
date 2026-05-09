from __future__ import annotations

from pathlib import Path

from elbysodic import cli
from elbysodic.db import connect
from elbysodic.services import initialize_database

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
