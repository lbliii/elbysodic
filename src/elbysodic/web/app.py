"""Chirp application factory for Elbysodic."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

from chirp.app import App
from chirp.config import AppConfig
from chirp.ext.chirp_ui import use_chirp_ui
from chirp.middleware.auth_rate_limit import AuthRateLimitConfig, AuthRateLimitMiddleware
from chirp.middleware.csrf import CSRFConfig, CSRFMiddleware
from chirp.middleware.security_headers import SecurityHeadersConfig, SecurityHeadersMiddleware
from chirp.middleware.sessions import SessionConfig, SessionMiddleware
from chirp.middleware.static import StaticFiles

from elbysodic.services import AppServices, create_services
from elbysodic.web.navigation import location_nav_tree_items
from elbysodic.web.security import (
    AutoCSRFFormsMiddleware,
    RequireLoginMiddleware,
    resolve_web_security_config,
)
from elbysodic.web.state import configure_services, dev_tools_enabled
from elbysodic.web.tenant import TenantPrefixMiddleware

PAGES_DIR = Path(__file__).parent / "pages"
STATIC_DIR = Path(__file__).parent / "static"
DEV_TOOLS_ENV = "ELBYSODIC_DEV_TOOLS"


def create_app(
    *,
    debug: bool = True,
    services: AppServices | None = None,
    db_path: str | Path | None = None,
    dev_tools: bool | None = None,
) -> App:
    security = resolve_web_security_config(debug=debug)
    config = AppConfig(
        template_dir=PAGES_DIR,
        debug=debug,
        env=security.env,
        secret_key=security.secret_key,
        allowed_hosts=security.allowed_hosts,
        strict_transport_security=security.strict_transport_security,
    )
    app = App(config=config)
    configured_services = (services or create_services(db_path)).with_request_auth(
        production=security.production
    )

    configure_services(
        configured_services,
        dev_tools_enabled=_resolve_dev_tools(
            debug=debug,
            dev_tools=dev_tools,
            production=security.production,
        ),
        web_security_config=security,
    )
    use_chirp_ui(app)
    app.template_global()(location_nav_tree_items)
    app.template_global()(dev_tools_enabled)
    app.add_middleware(TenantPrefixMiddleware())
    if security.production:
        app.add_middleware(
            AuthRateLimitMiddleware(
                AuthRateLimitConfig(
                    paths=("/login",),
                    requests=10,
                    window_seconds=60,
                    block_seconds=300,
                )
            )
        )
        app.add_middleware(
            SessionMiddleware(
                SessionConfig(
                    secret_key=security.secret_key,
                    secure=security.secure_cookies,
                    httponly=True,
                    samesite="lax",
                )
            )
        )
        app.add_middleware(CSRFMiddleware(CSRFConfig()))
        app.add_middleware(AutoCSRFFormsMiddleware())
        app.add_middleware(
            SecurityHeadersMiddleware(
                SecurityHeadersConfig(
                    strict_transport_security=security.strict_transport_security,
                )
            )
        )
    app.add_middleware(RequireLoginMiddleware(security))
    app.add_middleware(StaticFiles(directory=str(STATIC_DIR), prefix="/elbysodic-static"))
    app.mount_pages(str(PAGES_DIR))
    _copy_page_contracts(app)

    return app


def _resolve_dev_tools(*, debug: bool, dev_tools: bool | None, production: bool) -> bool:
    if production:
        return False
    if dev_tools is not None:
        return dev_tools
    configured = os.environ.get(DEV_TOOLS_ENV)
    if configured is not None:
        return configured.strip().lower() not in {"0", "false", "no", "off"}
    return debug


def _copy_page_contracts(app: App) -> None:
    """Expose filesystem-page handler contracts to Chirp's route wrapper."""

    for route in app._mutable_state.pending_routes:
        source_handler = getattr(route, "page_source_handler", None)
        route_contract = getattr(source_handler, "_chirp_contract", None)
        if route_contract is not None:
            cast(Any, route.handler)._chirp_contract = route_contract
