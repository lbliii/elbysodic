"""Chirp application factory for Elbysodic."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from chirp.app import App
from chirp.config import AppConfig
from chirp.ext.chirp_ui import use_chirp_ui
from chirp.middleware.auth_rate_limit import AuthRateLimitConfig, AuthRateLimitMiddleware
from chirp.middleware.security_headers import SecurityHeadersConfig
from chirp.middleware.stack import secure_stack
from chirp.middleware.static import StaticFiles

from elbysodic.services import AppServices, create_services
from elbysodic.web.errors import register_error_handlers
from elbysodic.web.navigation import location_nav_tree_items
from elbysodic.web.routes import (
    active_route_path,
    board_section_for_path,
    primary_nav_items,
    shell_navigation,
    shell_route_state,
)
from elbysodic.web.security import (
    PRODUCTION_CONTENT_SECURITY_POLICY,
    IdentityFailureMiddleware,
    RequireLoginMiddleware,
    resolve_web_security_config,
)
from elbysodic.web.shell import sidebar_is_hidden
from elbysodic.web.state import (
    close_request_services,
    configure_services,
    dev_tools_enabled,
    get_services,
)
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
        htmx=True,
        # The app owns a tenant-aware /health route (Railway healthcheckPath);
        # move Chirp's auto-mounted liveness probe off that path.
        health_path="/livez",
    )
    app = App(config=config)
    register_error_handlers(app, include_internal=not debug)
    owns_services = services is None
    base_services = services or create_services(db_path, seed_demo=seed_demo)
    configured_services = base_services.with_request_auth(production=security.production)
    if owns_services:
        app.on_shutdown(configured_services.close)

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
    app.register_oob_region(
        "sidebar_oob",
        target_id="elbysodic-shell-sidebar-content",
        swap="true",
        wrap=False,
        optional=True,
    )
    app.template_global()(location_nav_tree_items)
    app.template_global()(dev_tools_enabled)
    app.template_global()(sidebar_is_hidden)
    app.template_global()(active_route_path)
    app.template_global()(board_section_for_path)
    app.template_global()(primary_nav_items)
    app.template_global()(shell_navigation)
    app.template_global()(shell_route_state)
    app.template_global()(community_initials)
    # Every environment runs the same middleware chain (dev/prod parity).
    # Explicit priorities pin the resolved order regardless of registration
    # order: lower priority runs outermost.
    app.add_middleware(RequestTimingMiddleware(), priority=-30)
    app.add_middleware(RequestServicesCleanupMiddleware(), priority=-25)
    app.add_middleware(TenantPrefixMiddleware(), priority=-20)
    app.add_middleware(
        AuthRateLimitMiddleware(
            AuthRateLimitConfig(
                paths=("/login",),
                requests=10,
                window_seconds=60,
                block_seconds=300,
                # Keying stays on the fail-closed, trusted-proxy-corrected
                # Request.trusted_client_ip default; a spoofed X-Forwarded-For
                # cannot rotate the limiter bucket. htmx form posts get a
                # friendly self-contained 429 fragment instead of bare text.
                error_template="_components/_rate_limited.html",
                error_block="login_rate_limited",
            )
        ),
        priority=-10,
    )
    # secure_stack wires SessionMiddleware -> CSRFMiddleware ->
    # SecurityHeadersMiddleware in contract-passing order in ALL envs. The
    # session cookie's Secure flag stays at SessionConfig's "auto" default,
    # resolved at freeze from AppConfig.env (True for production/staging,
    # False for local development) — never from debug.
    for middleware in secure_stack(
        config,
        headers=SecurityHeadersConfig(
            content_security_policy=PRODUCTION_CONTENT_SECURITY_POLICY,
            strict_transport_security=security.strict_transport_security,
        ),
    ):
        app.add_middleware(middleware, priority=0)
    app.add_middleware(RequireLoginMiddleware(security), priority=10)
    app.add_middleware(IdentityFailureMiddleware(), priority=20)
    app.add_middleware(
        StaticFiles(directory=str(STATIC_DIR), prefix="/elbysodic-static"), priority=30
    )
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


def community_initials(name: object) -> str:
    words = [word for word in re.split(r"[^A-Za-z0-9]+", str(name)) if word]
    if not words:
        return ""
    return "".join(word[0] for word in words[:3]).upper()


class RequestServicesCleanupMiddleware:
    """Close request-scoped service repositories after each response."""

    async def __call__(self, request: object, call_next: Any) -> object:
        try:
            return await call_next(request)
        finally:
            close_request_services(request)
