from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest
from chirp.app import App
from pounce._health import build_health_response
from pounce._request_pipeline import maybe_build_builtin_response
from pounce.config import ServerConfig

from elbysodic.web.pounce_railway import (
    _railway_server_config_kwargs,
    run_chirp_asgi_adapter,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
RAILWAY_JSON = REPO_ROOT / "railway.json"


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


def test_railway_bundle_uses_single_worker_until_process_drain_is_fixed() -> None:
    config = _railway_server_config_kwargs({"workers": 48})

    assert config["workers"] == 1
    assert config["health_check_path"] == "/readyz"


def test_chirp_launch_adapter_uses_public_freeze_and_serves_wrapper() -> None:
    calls: list[tuple[object, ...]] = []
    runtime_app = object()
    lifecycle_collector = object()

    class Launcher:
        def run(
            self,
            app: object,
            *,
            host: str | None,
            port: int | None,
            lifecycle_collector: Any | None,
        ) -> None:
            calls.append(("run", app, host, port, lifecycle_collector))

    class ChirpCanary:
        _server = Launcher()

        def freeze(self) -> None:
            calls.append(("freeze",))

        def _ensure_frozen(self) -> None:
            raise AssertionError("Chirp 0.10 public freeze must be preferred")

    run_chirp_asgi_adapter(
        cast(App, ChirpCanary()),
        runtime_app,
        host="127.0.0.1",
        port=8080,
        lifecycle_collector=lifecycle_collector,
    )

    assert calls == [
        ("freeze",),
        ("run", runtime_app, "127.0.0.1", 8080, lifecycle_collector),
    ]


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
