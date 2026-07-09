"""Finish the passkey sign-in ceremony and establish the app session.

Session establishment goes through ``AppServices.login_with_passkey`` →
``create_passkey_login_session``, the same session/identity path password
login uses, so both entry paths share one cookie posture.
"""

from __future__ import annotations

import binascii
import logging
from dataclasses import replace

from chirp.http.request import Request
from chirp.http.response import JSONResponse
from chirp.security import passkeys as passkey_ceremonies
from chirp.security.passkeys import PasskeyChallengeError, PasskeyVerificationError

from elbysodic.services.access import DEV_IDENTITY_COOKIE, dev_identity_cookie_value
from elbysodic.services.auth import SESSION_COOKIE
from elbysodic.web import passkeys as passkey_rp
from elbysodic.web.security import session_cookie
from elbysodic.web.state import get_services, get_web_security_config

logger = logging.getLogger(__name__)

_GENERIC_FAILURE = "Passkey sign-in failed. Try again or use your password."


async def post(request: Request) -> JSONResponse:
    body = await request.json()
    if not isinstance(body, dict):
        return _rejected("Malformed passkey response.")

    stored = _stored_credential(body.get("id"))
    if stored is None:
        # Unknown credential ids and undecodable ids fail the same way so the
        # endpoint does not confirm which credentials exist.
        return _rejected(_GENERIC_FAILURE)

    services = get_services()
    try:
        verified = passkey_ceremonies.finish_authentication(
            credential=body,
            stored=stored,
            config=passkey_rp.config_for_request(request),
        )
    except PasskeyChallengeError:
        return _rejected("Passkey sign-in expired. Start again.")
    except PasskeyVerificationError:
        return _rejected(_GENERIC_FAILURE)

    if verified.sign_count_regressed:
        # Clone-detection signal: fail closed without touching the stored
        # counter or issuing a session.
        logger.warning(
            "passkey sign count regressed for credential %s; rejecting sign-in",
            stored.id,
        )
        return _rejected(_GENERIC_FAILURE)

    services.repo.update_user_passkey_credential_sign_count(
        stored.credential_id,
        verified.new_sign_count,
    )
    try:
        session, identity = services.login_with_passkey(stored.user_id)
    except PermissionError as exc:
        return _rejected(str(exc))

    security = get_web_security_config()
    # The same SetCookie material password login attaches in login/page.py.
    cookies = [
        session_cookie(
            SESSION_COOKIE,
            session.token,
            max_age=60 * 60 * 24 * 30,
            security=security,
        )
    ]
    if not security.production:
        cookies.append(
            session_cookie(
                DEV_IDENTITY_COOKIE,
                dev_identity_cookie_value(identity),
                max_age=60 * 60 * 24 * 30,
                security=security,
            )
        )
    response = JSONResponse.from_value({"ok": True, "redirect": _safe_next(body.get("next"))})
    return replace(response, cookies=tuple(cookies))


def _stored_credential(raw_credential_id: object):
    if not isinstance(raw_credential_id, str) or not raw_credential_id:
        return None
    from webauthn.helpers import base64url_to_bytes

    try:
        credential_id = base64url_to_bytes(raw_credential_id)
    except ValueError, binascii.Error:
        return None
    try:
        return get_services().repo.get_user_passkey_credential(credential_id)
    except LookupError:
        return None


def _rejected(detail: str) -> JSONResponse:
    return JSONResponse.from_value({"ok": False, "error": detail}, status=422)


def _safe_next(next_url: object) -> str:
    candidate = str(next_url or "")
    if not candidate.startswith("/") or candidate.startswith("//"):
        return "/"
    return candidate
