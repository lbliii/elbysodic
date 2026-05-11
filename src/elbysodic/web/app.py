"""Chirp application factory for Elbysodic."""

from __future__ import annotations

import os
from pathlib import Path

from chirp.app import App
from chirp.config import AppConfig
from chirp.ext.chirp_ui import use_chirp_ui
from chirp.middleware.auth_rate_limit import AuthRateLimitConfig, AuthRateLimitMiddleware
from chirp.middleware.csrf import CSRFConfig, CSRFMiddleware
from chirp.middleware.security_headers import SecurityHeadersConfig, SecurityHeadersMiddleware
from chirp.middleware.sessions import SessionConfig, SessionMiddleware
from chirp.middleware.static import StaticFiles

from elbysodic.services import AppServices, create_services
from elbysodic.web.errors import register_error_handlers
from elbysodic.web.navigation import location_nav_tree_items
from elbysodic.web.routes import active_route_path, board_section_for_path, shell_route_state
from elbysodic.web.security import (
    PRODUCTION_CONTENT_SECURITY_POLICY,
    IdentityFailureMiddleware,
    RequireLoginMiddleware,
    resolve_web_security_config,
)
from elbysodic.web.shell import sidebar_is_hidden
from elbysodic.web.state import configure_services, dev_tools_enabled, get_services
from elbysodic.web.tenant import TenantPrefixMiddleware
from elbysodic.web.timing import RequestTimingMiddleware

PAGES_DIR = Path(__file__).parent / "pages"
STATIC_DIR = Path(__file__).parent / "static"
DEV_TOOLS_ENV = "ELBYSODIC_DEV_TOOLS"


def create_app(
    *,
    debug: bool = True,
    services: AppServices | None = None,
    db_path: str | Path | None = None,
    dev_tools: bool | None = None,
    seed_demo: bool = False,
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
    register_error_handlers(app, include_internal=not debug)
    configured_services = (
        services or create_services(db_path, seed_demo=seed_demo)
    ).with_request_auth(production=security.production)

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
    app.provide(AppServices, get_services)
    app.register_oob_region(
        "program_theme_oob",
        target_id="elbysodic-program-theme",
        swap="innerHTML",
        wrap=True,
        optional=True,
    )
    app.register_oob_region(
        "product_shell_oob",
        target_id="elbysodic-product-shell",
        swap="innerHTML",
        wrap=True,
        optional=True,
    )
    app.template_global()(location_nav_tree_items)
    app.template_global()(dev_tools_enabled)
    app.template_global()(sidebar_is_hidden)
    app.template_global()(active_route_path)
    app.template_global()(board_section_for_path)
    app.template_global()(shell_route_state)
    if not security.production:
        app.template_global("csrf_field")(_empty_csrf_field)
        app.template_global("csrf_token")(_empty_csrf_token)
    app.add_middleware(RequestTimingMiddleware())
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
        app.add_middleware(
            SecurityHeadersMiddleware(
                SecurityHeadersConfig(
                    content_security_policy=PRODUCTION_CONTENT_SECURITY_POLICY,
                    strict_transport_security=security.strict_transport_security,
                )
            )
        )
    app.add_middleware(RequireLoginMiddleware(security))
    app.add_middleware(IdentityFailureMiddleware())
    app.add_middleware(StaticFiles(directory=str(STATIC_DIR), prefix="/elbysodic-static"))
    app.mount_pages(str(PAGES_DIR))

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


def _empty_csrf_field() -> str:
    return ""


def _empty_csrf_token() -> str:
    return ""
