"""Begin passkey enrollment for the signed-in account."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.http.response import JSONResponse
from chirp.security import passkeys as passkey_ceremonies

from elbysodic.web import passkeys as passkey_rp
from elbysodic.web.state import get_services


async def post(request: Request) -> JSONResponse:
    services = get_services(request)
    viewer = services.viewer()
    user = services.repo.get_user(viewer.membership.user_id)
    existing = [
        credential.credential_id
        for credential in services.repo.list_user_passkey_credentials(user.id)
    ]
    options = passkey_ceremonies.begin_registration(
        user_id=str(user.id).encode(),
        user_name=user.email,
        user_display_name=viewer.membership.display_name or user.email,
        exclude_credentials=existing,
        config=passkey_rp.config_for_request(request),
    )
    return JSONResponse.from_value(options)
