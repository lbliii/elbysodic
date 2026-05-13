from __future__ import annotations

import asyncio
import os
import signal
import socket
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import IO
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from chirp.testing import TestClient

from elbysodic import cli
from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.services import AppServices, initialize_database
from elbysodic.web import app as web_app

RAILWAY_HOST = ".".join(("0", "0", "0", "0"))
LOCAL_HOST = "127.0.0.1"


class _FakeApp:
    def __init__(self, calls: dict[str, object]) -> None:
        self._calls = calls

    def run(self, *, host: str | None = None, port: int | None = None) -> None:
        self._calls["host"] = host
        self._calls["port"] = port


class _FakeServices:
    def __init__(self, calls: dict[str, object]) -> None:
        self._calls = calls

    def close(self) -> None:
        self._calls["services_closed"] = True


def _unused_port() -> int:
    with socket.socket() as sock:
        sock.bind((LOCAL_HOST, 0))
        return int(sock.getsockname()[1])


def _start_cli_subprocess(args: list[str]) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    return subprocess.Popen(  # noqa: S603 - argv is built by these tests, not user input.
        [sys.executable, "-c", "from elbysodic.cli import main; main()", *args],
        cwd=Path(__file__).parents[1],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _read_process_output(stream: IO[str] | None) -> str:
    return "" if stream is None else stream.read()


def _wait_for_health(port: int, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 20
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = _read_process_output(process.stdout)
            raise AssertionError(f"server exited before health check: {output}")
        try:
            with urlopen(f"http://{LOCAL_HOST}:{port}/health", timeout=0.5) as response:
                if response.status == 200:
                    return
        except (OSError, URLError) as exc:
            last_error = exc
        time.sleep(0.1)
    raise AssertionError(f"server did not become healthy: {last_error}")


def _stop_process_cleanly(process: subprocess.Popen[str], stop_signal: signal.Signals) -> str:
    process.send_signal(stop_signal)
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        output = _read_process_output(process.stdout)
        raise AssertionError(f"server did not exit after {stop_signal.name}: {output}") from None
    output = _read_process_output(process.stdout)
    assert process.returncode == 0, output
    return output


def _assert_port_reusable(port: int) -> None:
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((LOCAL_HOST, port))


def _assert_database_writable(db_path: Path) -> None:
    connection = connect(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.rollback()
    finally:
        connection.close()


def test_cli_can_start_production_server_on_railway_host_and_port(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_create_services(path: Path, *, seed_demo: bool) -> _FakeServices:
        calls["db_path"] = path
        calls["seed_demo"] = seed_demo
        return _FakeServices(calls)

    def fake_create_app(*, debug: bool, services: _FakeServices) -> _FakeApp:
        calls["debug"] = debug
        calls["services"] = services
        return _FakeApp(calls)

    monkeypatch.setattr(cli, "create_services", fake_create_services)
    monkeypatch.setattr(cli, "create_app", fake_create_app)

    cli.main(["--host", RAILWAY_HOST, "--port", "1234", "--no-debug"])

    assert calls["debug"] is False
    assert calls["seed_demo"] is False
    assert calls["host"] == RAILWAY_HOST
    assert calls["port"] == 1234
    assert calls["services_closed"] is True


def test_cli_serve_subcommand_accepts_same_server_options(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_create_services(path: Path, *, seed_demo: bool) -> _FakeServices:
        calls["db_path"] = path
        calls["seed_demo"] = seed_demo
        return _FakeServices(calls)

    def fake_create_app(*, debug: bool, services: _FakeServices) -> _FakeApp:
        calls["debug"] = debug
        calls["services"] = services
        return _FakeApp(calls)

    monkeypatch.setattr(cli, "create_services", fake_create_services)
    monkeypatch.setattr(cli, "create_app", fake_create_app)

    cli.main(["serve", "--host", RAILWAY_HOST, "--port", "5678", "--no-debug"])

    assert calls["debug"] is False
    assert calls["seed_demo"] is False
    assert calls["host"] == RAILWAY_HOST
    assert calls["port"] == 5678


def test_cli_serve_can_explicitly_seed_demo_data(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_create_services(path: Path, *, seed_demo: bool) -> _FakeServices:
        calls["db_path"] = path
        calls["seed_demo"] = seed_demo
        return _FakeServices(calls)

    def fake_create_app(*, debug: bool, services: _FakeServices) -> _FakeApp:
        calls["debug"] = debug
        calls["services"] = services
        return _FakeApp(calls)

    monkeypatch.setattr(cli, "create_services", fake_create_services)
    monkeypatch.setattr(cli, "create_app", fake_create_app)

    cli.main(["serve", "--seed-demo"])

    assert calls["seed_demo"] is True


def test_cli_dev_preview_seeds_demo_and_runs_standard_preview_port(monkeypatch, tmp_path) -> None:
    calls: dict[str, object] = {}
    db_path = tmp_path / "preview.sqlite3"

    def fake_initialize_database(path: Path, *, seed_demo: bool) -> Path:
        calls["initialize_path"] = path
        calls["initialize_seed_demo"] = seed_demo
        return path

    def fake_create_services(path: Path, *, seed_demo: bool) -> _FakeServices:
        calls["db_path"] = path
        calls["create_seed_demo"] = seed_demo
        return _FakeServices(calls)

    def fake_create_app(*, debug: bool, services: _FakeServices) -> _FakeApp:
        calls["debug"] = debug
        calls["services"] = services
        return _FakeApp(calls)

    monkeypatch.setattr(cli, "initialize_database", fake_initialize_database)
    monkeypatch.setattr(cli, "create_services", fake_create_services)
    monkeypatch.setattr(cli, "create_app", fake_create_app)

    cli.main(["dev", "preview", "--db-path", str(db_path)])

    assert calls["initialize_path"] == db_path
    assert calls["initialize_seed_demo"] is True
    assert calls["debug"] is True
    assert calls["db_path"] == db_path
    assert calls["create_seed_demo"] is False
    assert calls["host"] == "127.0.0.1"
    assert calls["port"] == 8001


def test_cli_dev_preview_accepts_server_options(monkeypatch, tmp_path) -> None:
    calls: dict[str, object] = {}
    db_path = tmp_path / "preview.sqlite3"

    def fake_initialize_database(path: Path, *, seed_demo: bool) -> Path:
        calls["initialize_path"] = path
        calls["initialize_seed_demo"] = seed_demo
        return path

    def fake_create_services(path: Path, *, seed_demo: bool) -> _FakeServices:
        calls["db_path"] = path
        calls["create_seed_demo"] = seed_demo
        return _FakeServices(calls)

    def fake_create_app(*, debug: bool, services: _FakeServices) -> _FakeApp:
        calls["debug"] = debug
        calls["services"] = services
        return _FakeApp(calls)

    monkeypatch.setattr(cli, "initialize_database", fake_initialize_database)
    monkeypatch.setattr(cli, "create_services", fake_create_services)
    monkeypatch.setattr(cli, "create_app", fake_create_app)

    cli.main(
        [
            "dev",
            "preview",
            "--db-path",
            str(db_path),
            "--host",
            RAILWAY_HOST,
            "--port",
            "9001",
            "--no-debug",
            "--no-seed-demo",
        ]
    )

    assert calls["initialize_path"] == db_path
    assert calls["initialize_seed_demo"] is False
    assert calls["debug"] is False
    assert calls["db_path"] == db_path
    assert calls["create_seed_demo"] is False
    assert calls["host"] == RAILWAY_HOST
    assert calls["port"] == 9001


def test_cli_closes_services_when_server_run_raises(monkeypatch, tmp_path) -> None:
    calls: dict[str, object] = {}

    class FailingApp(_FakeApp):
        def run(self, *, host: str | None = None, port: int | None = None) -> None:
            super().run(host=host, port=port)
            raise RuntimeError("server failed")

    def fake_create_services(path: Path, *, seed_demo: bool) -> _FakeServices:
        calls["db_path"] = path
        calls["seed_demo"] = seed_demo
        return _FakeServices(calls)

    def fake_create_app(*, debug: bool, services: _FakeServices) -> FailingApp:
        calls["debug"] = debug
        calls["services"] = services
        return FailingApp(calls)

    monkeypatch.setattr(cli, "create_services", fake_create_services)
    monkeypatch.setattr(cli, "create_app", fake_create_app)

    with pytest.raises(RuntimeError, match="server failed"):
        cli.main(["serve", "--db-path", str(tmp_path / "forum.sqlite3")])

    assert calls["services_closed"] is True


def test_dev_cli_exposes_preview_to_milo_discovery() -> None:
    result = cli.build_dev_cli().invoke(["--llms-txt"])

    assert result.exit_code == 0
    assert "preview" in result.output
    assert "local preview" in result.output


def test_app_services_close_releases_filesystem_database(tmp_path) -> None:
    db_path = tmp_path / "forum.sqlite3"
    initialize_database(db_path)
    connection = connect(db_path)
    services = AppServices(ForumRepository(connection), None)

    services.close()
    services.close()

    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        connection.execute("SELECT 1")

    reopened = connect(db_path)
    try:
        reopened.execute("BEGIN IMMEDIATE")
        reopened.rollback()
    finally:
        reopened.close()


def test_create_app_closes_internally_created_services_on_shutdown(monkeypatch) -> None:
    calls: dict[str, object] = {}

    class FakeAppServices(_FakeServices):
        def with_request_auth(self, *, production: bool) -> FakeAppServices:
            calls["production"] = production
            return self

    def fake_create_services(path: Path, *, seed_demo: bool) -> FakeAppServices:
        calls["db_path"] = path
        calls["seed_demo"] = seed_demo
        return FakeAppServices(calls)

    async def run_lifespan() -> None:
        app = web_app.create_app(debug=True, db_path=Path(":memory:"), seed_demo=False)
        async with TestClient(app):
            pass

    monkeypatch.setattr(web_app, "create_services", fake_create_services)

    asyncio.run(run_lifespan())

    assert calls["seed_demo"] is False
    assert calls["services_closed"] is True


@pytest.mark.parametrize("stop_signal", [signal.SIGTERM, signal.SIGINT])
def test_cli_serve_exits_cleanly_on_stop_signal(tmp_path, stop_signal: signal.Signals) -> None:
    port = _unused_port()
    db_path = tmp_path / "serve.sqlite3"
    process = _start_cli_subprocess(
        [
            "serve",
            "--host",
            LOCAL_HOST,
            "--port",
            str(port),
            "--db-path",
            str(db_path),
            "--no-debug",
        ]
    )
    try:
        _wait_for_health(port, process)
        _stop_process_cleanly(process, stop_signal)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)

    _assert_port_reusable(port)
    _assert_database_writable(db_path)


def test_dev_preview_exits_cleanly_on_sigterm(tmp_path) -> None:
    port = _unused_port()
    db_path = tmp_path / "preview.sqlite3"
    process = _start_cli_subprocess(
        [
            "dev",
            "preview",
            "--host",
            LOCAL_HOST,
            "--port",
            str(port),
            "--db-path",
            str(db_path),
        ]
    )
    try:
        _wait_for_health(port, process)
        output = _stop_process_cleanly(process, signal.SIGTERM)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)

    assert "preview database ready" in output
    _assert_port_reusable(port)
    _assert_database_writable(db_path)


@pytest.mark.skipif(not hasattr(signal, "SIGHUP"), reason="SIGHUP is POSIX-only")
def test_dev_preview_debug_exits_cleanly_on_sighup(tmp_path) -> None:
    port = _unused_port()
    db_path = tmp_path / "preview.sqlite3"
    process = _start_cli_subprocess(
        [
            "dev",
            "preview",
            "--host",
            LOCAL_HOST,
            "--port",
            str(port),
            "--db-path",
            str(db_path),
        ]
    )
    try:
        _wait_for_health(port, process)
        _stop_process_cleanly(process, signal.SIGHUP)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)

    _assert_port_reusable(port)
    _assert_database_writable(db_path)


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
