"""Passkey relying-party configuration for the Elbysodic web app.

WebAuthn binds every credential to a Relying Party ID (``rp_id``) and an
origin. On Railway (and any HTTPS deploy) pin them explicitly::

    ELBYSODIC_PASSKEY_ORIGIN=https://your-app.up.railway.app
    ELBYSODIC_PASSKEY_RP_ID=your-app.up.railway.app

Without the env override the config derives the origin from the incoming
request, so local ``localhost`` vs ``127.0.0.1`` and dev ports match what the
browser actually uses (the common local WebAuthn footgun).
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

from chirp.http.request import Request
from chirp.security.passkeys import PasskeyConfig

ELBYSODIC_PASSKEY_ORIGIN = "ELBYSODIC_PASSKEY_ORIGIN"
ELBYSODIC_PASSKEY_RP_ID = "ELBYSODIC_PASSKEY_RP_ID"
RP_NAME = "Elbysodic"


def config_for_request(request: Request) -> PasskeyConfig:
    """Return the passkey relying-party config for this request.

    When ``ELBYSODIC_PASSKEY_ORIGIN`` is set, that origin (and the optional
    ``ELBYSODIC_PASSKEY_RP_ID``) wins — for production deploys behind a stable
    public URL. Otherwise derive both from the request.
    """

    env_origin = (os.environ.get(ELBYSODIC_PASSKEY_ORIGIN) or "").strip().rstrip("/")
    if env_origin:
        rp_id = (
            (os.environ.get(ELBYSODIC_PASSKEY_RP_ID) or "").strip()
            or urlparse(env_origin).hostname
            or "localhost"
        )
        return PasskeyConfig(rp_id=rp_id, rp_name=RP_NAME, origin=env_origin)

    origin = _origin_from_request(request)
    hostname = urlparse(origin).hostname or "localhost"
    return PasskeyConfig(rp_id=hostname, rp_name=RP_NAME, origin=origin)


def _origin_from_request(request: Request) -> str:
    """Derive the browser origin from the incoming request."""

    current = request.headers.get("hx-current-url")
    if current:
        parsed = urlparse(str(current))
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"

    railway_domain = (os.environ.get("RAILWAY_PUBLIC_DOMAIN") or "").strip()
    if railway_domain:
        return f"https://{railway_domain}"

    host = str(request.headers.get("host") or "localhost:8000")
    return f"{_request_proto(request)}://{host}"


def _request_proto(request: Request) -> str:
    """Best-effort scheme for origin derivation.

    The scheme only shapes the *expected* origin string the WebAuthn library
    compares against; it is not a trust decision (the assertion signature is).
    Production and staging always terminate TLS, so pin ``https`` there.
    """

    env = (os.environ.get("ELBYSODIC_ENV") or "").strip().lower()
    if env in ("production", "prod", "staging"):
        return "https"
    if os.environ.get("RAILWAY_ENVIRONMENT_ID") or os.environ.get("RAILWAY_PUBLIC_DOMAIN"):
        return "https"
    return "http"
