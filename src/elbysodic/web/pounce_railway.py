"""Public Pounce configuration and launch path for Elbysodic production."""

from __future__ import annotations

import os
from typing import Any

from chirp.app import App
from pounce import ASGIApp, LifecycleCollector, ServerConfig
from pounce import run as pounce_run

POUNCE_HEALTH_CHECK_PATH = "/readyz"
POUNCE_SHUTDOWN_TIMEOUT = 10.0
POUNCE_INTROSPECTION_PATH = "/_pounce/info"


def railway_server_config(
    chirp_app: App,
    *,
    host: str | None,
    port: int | None,
) -> ServerConfig:
    """Resolve Chirp's production settings into an explicit Pounce config."""

    app_config = chirp_app.config
    kwargs: dict[str, Any] = {
        "host": app_config.host if host is None else host,
        "port": app_config.port if port is None else port,
        # Pounce 0.9.1 does not deliver its explicit drain command to process
        # workers, so Railway remains single-worker until that contract lands.
        "workers": 1,
        "worker_mode": app_config.worker_mode,
        "shutdown_timeout": POUNCE_SHUTDOWN_TIMEOUT,
        "max_request_size": app_config.max_request_body_size,
        "health_check_path": POUNCE_HEALTH_CHECK_PATH,
        "metrics_enabled": app_config.metrics_enabled,
        "metrics_path": app_config.metrics_path,
        "rate_limit_enabled": app_config.rate_limit_enabled,
        "rate_limit_requests_per_second": app_config.rate_limit_requests_per_second,
        "rate_limit_burst": app_config.rate_limit_burst,
        "rate_limit_max_tracked_ips": app_config.rate_limit_max_tracked_ips,
        "trusted_hosts": frozenset(app_config.trusted_proxies),
        "forwarded_for_trusted_hops": app_config.forwarded_for_trusted_hops,
        "request_queue_enabled": app_config.request_queue_enabled,
        "request_queue_max_depth": app_config.request_queue_max_depth,
        "sentry_dsn": app_config.sentry_dsn,
        "sentry_environment": app_config.sentry_environment,
        "sentry_release": app_config.sentry_release,
        "sentry_traces_sample_rate": app_config.sentry_traces_sample_rate,
        "reload_timeout": app_config.reload_timeout,
        "otel_endpoint": app_config.otel_endpoint,
        "otel_service_name": app_config.otel_service_name,
        "websocket_compression": app_config.websocket_compression,
        "websocket_max_message_size": app_config.websocket_max_message_size,
        "lifecycle_logging": app_config.lifecycle_logging,
        "log_format": app_config.log_format,
        "log_level": app_config.log_level,
        "max_connections": app_config.max_connections,
        "backlog": app_config.backlog,
        "keep_alive_timeout": app_config.keep_alive_timeout,
        "request_timeout": app_config.request_timeout,
        "ssl_certfile": app_config.ssl_certfile,
        "ssl_keyfile": app_config.ssl_keyfile,
    }
    if _introspection_enabled():
        kwargs.update(
            introspection_enabled=True,
            introspection_bind="0.0.0.0",  # noqa: S104 -- explicit Railway introspection is public.
            introspection_path=POUNCE_INTROSPECTION_PATH,
        )
    return ServerConfig(**kwargs)


def run_chirp_asgi_adapter(
    chirp_app: App,
    runtime_app: ASGIApp,
    *,
    host: str | None,
    port: int | None,
    lifecycle_collector: LifecycleCollector | None,
) -> None:
    """Serve the drain-aware ASGI wrapper without reaching into Chirp internals."""

    if chirp_app.config.debug:
        # Keep Chirp's debug server, reload, and contract checks on its public
        # API. Development has no Pounce worker-drain lifecycle to forward.
        chirp_app.run(host=host, port=port, lifecycle_collector=lifecycle_collector)
        return

    chirp_app.freeze()
    config = railway_server_config(chirp_app, host=host, port=port)
    if lifecycle_collector is None:
        pounce_run(runtime_app, config=config)
        return

    # pounce.run intentionally exposes only ServerConfig. Preserve Chirp's
    # optional lifecycle-collector seam through Pounce's public Server API.
    from pounce.server import Server

    Server(config, runtime_app, lifecycle_collector=lifecycle_collector).run()


def _introspection_enabled() -> bool:
    return os.environ.get("POUNCE_INTROSPECTION", "").lower() in ("1", "true", "yes", "on")
