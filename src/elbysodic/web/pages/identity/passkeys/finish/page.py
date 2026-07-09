"""Finish passkey enrollment and persist the credential for the account."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.http.response import JSONResponse
from chirp.security import passkeys as passkey_ceremonies
from chirp.security.passkeys import PasskeyChallengeError, PasskeyVerificationError

from elbysodic.web import passkeys as passkey_rp
from elbysodic.web.state import get_services

MAX_LABEL_LENGTH = 80


async def post(request: Request) -> JSONResponse:
    services = get_services(request)
    viewer = services.viewer()
    body = await request.json()
    if not isinstance(body, dict):
        return _rejected("Malformed passkey response.")
    label = str(body.pop("label", "") or "").strip()[:MAX_LABEL_LENGTH]

    try:
        registered = passkey_ceremonies.finish_registration(
            credential=body,
            config=passkey_rp.config_for_request(request),
        )
    except PasskeyChallengeError:
        return _rejected("Passkey enrollment expired. Start again.")
    except PasskeyVerificationError:
        return _rejected("Passkey enrollment failed. Try again.")

    try:
        services.repo.create_user_passkey_credential(
            viewer.membership.user_id,
            credential_id=registered.credential_id,
            public_key=registered.public_key,
            sign_count=registered.sign_count,
            transports=registered.transports or (),
            label=label or "Passkey",
        )
    except ValueError:
        return _rejected("That passkey is already registered to an account.")
    return JSONResponse.from_value({"ok": True, "redirect": "/identity"})


def _rejected(detail: str) -> JSONResponse:
    return JSONResponse.from_value({"ok": False, "error": detail}, status=422)
