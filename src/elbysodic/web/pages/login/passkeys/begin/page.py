"""Begin the passkey sign-in ceremony (usernameless, discoverable credential)."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.http.response import JSONResponse
from chirp.security import passkeys as passkey_ceremonies

from elbysodic.web import passkeys as passkey_rp


async def post(request: Request) -> JSONResponse:
    options = passkey_ceremonies.begin_authentication(
        # Usernameless sign-in: never enumerate stored credential ids to
        # anonymous visitors; discoverable credentials identify themselves.
        allow_credentials=None,
        config=passkey_rp.config_for_request(request),
    )
    return JSONResponse.from_value(options)
