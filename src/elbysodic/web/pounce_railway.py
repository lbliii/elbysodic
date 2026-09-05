"""Pounce 0.9 Railway bundle defaults for Elbysodic production launch.

Aligns with lbliii/pounce ``examples/deploy/railway`` (#248, #291):
``shutdown_timeout`` stays within Railway's ``drainingSeconds`` window and
``POUNCE_BUILD_ID`` surfaces through ``/_pounce/info`` when introspection is
on. Pounce 0.9.1 process workers do not receive the explicit drain command
(lbliii/pounce#316), so Railway stays on one worker until that upstream
lifecycle contract is released and proven here.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, Protocol, cast

from chirp.app import App

POUNCE_HEALTH_CHECK_PATH = "/readyz"
POUNCE_SHUTDOWN_TIMEOUT = 10.0
POUNCE_INTROSPECTION_PATH = "/_pounce/info"


class _ChirpServerLauncher(Protocol):
    def run(
        self,
        app: App,
        *,
        host: str | None,
        port: int | None,
        lifecycle_collector: Any | None,
    ) -> None: ...


def run_chirp_asgi_adapter(
    chirp_app: App,
    runtime_app: object,
    *,
    host: str | None,
    port: int | None,
    lifecycle_collector: Any | None,
) -> None:
    """Launch a wrapped ASGI app through Chirp's frozen server configuration.

    Chirp 0.10 exposes public ``freeze`` and ASGI call seams, but its public
    ``run`` method always serves the Chirp object itself. The one private
    launcher lookup below is the compatibility bridge that lets Pounce send
    ``pounce.worker.draining`` to Elbysodic's wrapper without duplicating
    Chirp's development and production configuration mapping.
    """

    freeze = getattr(chirp_app, "freeze", None)
    if callable(freeze):
        freeze()
    else:
        # Compatibility for the pre-0.10 shape retained by existing canaries.
        ensure_frozen = getattr(chirp_app, "_ensure_frozen", None)
        if not callable(ensure_frozen):
            raise TypeError("Chirp launch adapter requires a supported freeze seam")
        ensure_frozen()
    launcher = cast(_ChirpServerLauncher | None, getattr(chirp_app, "_server", None))
    if launcher is None or not callable(getattr(launcher, "run", None)):
        raise RuntimeError("Chirp 0.10 server launcher compatibility seam changed")
    launcher.run(
        cast(App, runtime_app),
        host=host,
        port=port,
        lifecycle_collector=lifecycle_collector,
    )


def _introspection_enabled() -> bool:
    return os.environ.get("POUNCE_INTROSPECTION", "").lower() in ("1", "true", "yes", "on")


def _railway_server_config_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    patched = dict(kwargs)
    patched["health_check_path"] = POUNCE_HEALTH_CHECK_PATH
    patched["shutdown_timeout"] = POUNCE_SHUTDOWN_TIMEOUT
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
