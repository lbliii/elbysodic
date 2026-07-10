"""Pounce 0.9 Railway bundle defaults for Elbysodic production launch.

Aligns with lbliii/pounce ``examples/deploy/railway`` (#248, #291):
``/readyz`` exposes JSON ``{"status":"draining"}`` during deploy overlap,
``shutdown_timeout`` stays within Railway's ``drainingSeconds`` window, and
``POUNCE_BUILD_ID`` surfaces through ``/_pounce/info`` when introspection is on.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

POUNCE_HEALTH_CHECK_PATH = "/readyz"
POUNCE_SHUTDOWN_TIMEOUT = 10.0
POUNCE_INTROSPECTION_PATH = "/_pounce/info"


def _introspection_enabled() -> bool:
    return os.environ.get("POUNCE_INTROSPECTION", "").lower() in ("1", "true", "yes", "on")


def _railway_server_config_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    patched = dict(kwargs)
    patched["health_check_path"] = POUNCE_HEALTH_CHECK_PATH
    patched["shutdown_timeout"] = POUNCE_SHUTDOWN_TIMEOUT
    if os.environ.get("ELBYSODIC_RAILWAY_PROBE_SMOKE") == "1":
        patched["workers"] = 1
    if _introspection_enabled():
        patched["introspection_enabled"] = True
        patched["introspection_bind"] = "0.0.0.0"  # noqa: S104 -- Railway public bind when introspection is explicitly enabled
        patched["introspection_path"] = POUNCE_INTROSPECTION_PATH
    return patched


def apply_railway_pounce_defaults() -> None:
    """Patch Chirp production launch with the official Railway bundle knobs."""
    import chirp.server.production as chirp_production
    import pounce.config as pounce_config

    if getattr(chirp_production, "_elbysodic_railway_patch", False):
        return

    original_run: Callable[..., None] = chirp_production.run_production_server
    original_config_factory = pounce_config.ServerConfig

    def patched_config_factory(**kwargs: Any) -> Any:
        return original_config_factory(**_railway_server_config_kwargs(kwargs))

    def run_production_server(*args: Any, **kwargs: Any) -> None:
        vars(pounce_config)["ServerConfig"] = patched_config_factory
        try:
            original_run(*args, **kwargs)
        finally:
            vars(pounce_config)["ServerConfig"] = original_config_factory

    vars(chirp_production)["run_production_server"] = run_production_server
    vars(chirp_production)["_elbysodic_railway_patch"] = True
