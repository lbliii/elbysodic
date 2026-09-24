from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, cast

import pytest
from chirp.app import App
from chirp.config import AppConfig
from pounce._health import build_health_response
from pounce._request_pipeline import maybe_build_builtin_response
from pounce.config import ServerConfig

from elbysodic.web import pounce_railway
from elbysodic.web.pounce_railway import (
    POUNCE_HEALTH_CHECK_PATH,
    POUNCE_INTROSPECTION_PATH,
    POUNCE_SHUTDOWN_TIMEOUT,
    railway_server_config,
    run_chirp_asgi_adapter,
)
from elbysodic.web.worker_draining import (
    active_plotting_streams,
    emit_worker_draining,
    is_worker_draining,
    reset_worker_draining,
    wrap_worker_draining,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
RAILWAY_JSON = REPO_ROOT / "railway.json"
RAILWAY_HOST = "0.0.0.0"  # noqa: S104 -- bind address for the production config canary.


def test_railway_json_encodes_pounce_bundle_numbers() -> None:
    payload = json.loads(RAILWAY_JSON.read_text())
    deploy = payload["deploy"]

    assert deploy["healthcheckPath"] == "/ready"
    assert deploy["numReplicas"] == 1
    assert deploy["overlapSeconds"] == 5
    assert deploy["drainingSeconds"] == 15
    assert deploy["restartPolicyMaxRetries"] == 3
    assert isinstance(deploy["overlapSeconds"], int)
    assert isinstance(deploy["drainingSeconds"], int)
    assert isinstance(deploy["numReplicas"], int)


def test_readyz_draining_contract_returns_json_503() -> None:
    status, _, body = build_health_response(worker_id=0, active_connections=0, draining=True)
    payload = json.loads(body.decode("utf-8"))
    assert status == 503
    assert payload["status"] == "draining"

    config = ServerConfig(health_check_path="/readyz")
    head = maybe_build_builtin_response(
        config,
        "HEAD",
        "/readyz",
        worker_id=0,
        active_connections=0,
        draining=True,
    )
    assert head is not None
    assert head.status == 503
    assert json.loads(head.body.decode("utf-8"))["status"] == "draining"


def test_railway_config_preserves_chirp_production_settings(monkeypatch) -> None:
    chirp_config = AppConfig(
        host=RAILWAY_HOST,
        port=8123,
        worker_mode="async",
        max_request_body_size=24_000_000,
        log_format="json",
        log_level="warning",
        metrics_enabled=True,
        trusted_proxies=("10.0.0.0/8",),
    )
    monkeypatch.setenv("POUNCE_INTROSPECTION", "true")

    config = railway_server_config(
        cast(App, type("ChirpAppStub", (), {"config": chirp_config})()),
        host=None,
        port=None,
    )

    assert config.host == RAILWAY_HOST
    assert config.port == 8123
    assert config.workers == 1
    assert config.worker_mode == "async"
    assert config.max_request_size == 24_000_000
    assert config.health_check_path == POUNCE_HEALTH_CHECK_PATH
    assert config.shutdown_timeout == POUNCE_SHUTDOWN_TIMEOUT
    assert config.log_format == "json"
    assert config.log_level == "warning"
    assert config.trusted_hosts == frozenset({"10.0.0.0/8"})
    assert config.introspection_enabled is True
    assert config.introspection_bind == RAILWAY_HOST
    assert config.introspection_path == POUNCE_INTROSPECTION_PATH


def test_chirp_launch_adapter_uses_public_freeze_and_pounce_run(monkeypatch) -> None:
    calls: list[tuple[object, ...]] = []
    chirp_config = AppConfig(worker_mode="async", max_request_body_size=20_000_000)
    runtime_app = object()

    class ChirpCanary:
        config = chirp_config

        def freeze(self) -> None:
            calls.append(("freeze",))

    def capture_pounce_run(app: object, *, config: ServerConfig) -> None:
        calls.append(("pounce.run", app, config))

    monkeypatch.setattr(pounce_railway, "pounce_run", capture_pounce_run)

    run_chirp_asgi_adapter(
        cast(App, ChirpCanary()),
        cast(Any, runtime_app),
        host=RAILWAY_HOST,
        port=8080,
        lifecycle_collector=None,
    )

    assert len(calls) == 2
    assert calls[0] == ("freeze",)
    assert calls[1][0:2] == ("pounce.run", runtime_app)
    config = calls[1][2]
    assert isinstance(config, ServerConfig)
    assert config.host == RAILWAY_HOST
    assert config.port == 8080
    assert config.workers == 1
    assert config.worker_mode == "async"
    assert config.max_request_size == 20_000_000


def test_debug_launch_keeps_chirp_public_server_path(monkeypatch) -> None:
    calls: list[tuple[object, ...]] = []

    class ChirpCanary:
        config = AppConfig(debug=True)

        def run(
            self,
            *,
            host: str | None,
            port: int | None,
            lifecycle_collector: Any | None,
        ) -> None:
            calls.append((host, port, lifecycle_collector))

    monkeypatch.setattr(
        pounce_railway,
        "pounce_run",
        lambda *_args, **_kwargs: pytest.fail("debug launch must stay on Chirp"),
    )
    collector = object()
    run_chirp_asgi_adapter(
        cast(App, ChirpCanary()),
        cast(Any, object()),
        host="127.0.0.1",
        port=8080,
        lifecycle_collector=cast(Any, collector),
    )

    assert calls == [("127.0.0.1", 8080, collector)]


def test_worker_drain_signal_is_cleared_for_the_next_generation(caplog) -> None:
    caplog.set_level(logging.INFO, logger="pounce.elbysodic")
    proxy = wrap_worker_draining(App(config=AppConfig(debug=False)))

    async def run() -> None:
        reset_worker_draining()
        await emit_worker_draining(proxy, worker_id=0, generation=7)
        assert is_worker_draining()

        # Chirp runs the worker-startup hook for each Pounce generation. Its
        # reset must not carry an old drain event or stream gauge forward.
        reset_worker_draining()
        assert not is_worker_draining()
        assert active_plotting_streams() == 0

        await emit_worker_draining(proxy, worker_id=0, generation=8)
        assert is_worker_draining()
        reset_worker_draining()

    asyncio.run(run())
    messages = [record.getMessage() for record in caplog.records]
    assert any(
        "event=worker_draining" in message and "generation=7" in message for message in messages
    )
    assert any(
        "event=worker_draining" in message and "generation=8" in message for message in messages
    )


@pytest.mark.process
def test_railway_probe_smoke_local() -> None:
    import importlib.util
    import sys

    module_path = REPO_ROOT / "scripts" / "railway_probe_smoke.py"
    spec = importlib.util.spec_from_file_location("railway_probe_smoke", module_path)
    assert spec is not None
    assert spec.loader is not None
    smoke = importlib.util.module_from_spec(spec)
    sys.modules["railway_probe_smoke"] = smoke
    spec.loader.exec_module(smoke)

    assert smoke.run_local_smoke() == 0
