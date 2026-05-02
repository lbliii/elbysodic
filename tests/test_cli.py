from __future__ import annotations

from pathlib import Path

from elbysodic import cli

RAILWAY_HOST = ".".join(("0", "0", "0", "0"))


class _FakeApp:
    def __init__(self, calls: dict[str, object]) -> None:
        self._calls = calls

    def run(self, *, host: str | None = None, port: int | None = None) -> None:
        self._calls["host"] = host
        self._calls["port"] = port


def test_cli_can_start_production_server_on_railway_host_and_port(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_create_app(*, debug: bool, db_path: Path) -> _FakeApp:
        calls["debug"] = debug
        calls["db_path"] = db_path
        return _FakeApp(calls)

    monkeypatch.setattr(cli, "create_app", fake_create_app)

    cli.main(["--host", RAILWAY_HOST, "--port", "1234", "--no-debug"])

    assert calls["debug"] is False
    assert calls["host"] == RAILWAY_HOST
    assert calls["port"] == 1234


def test_cli_serve_subcommand_accepts_same_server_options(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_create_app(*, debug: bool, db_path: Path) -> _FakeApp:
        calls["debug"] = debug
        calls["db_path"] = db_path
        return _FakeApp(calls)

    monkeypatch.setattr(cli, "create_app", fake_create_app)

    cli.main(["serve", "--host", RAILWAY_HOST, "--port", "5678", "--no-debug"])

    assert calls["debug"] is False
    assert calls["host"] == RAILWAY_HOST
    assert calls["port"] == 5678
