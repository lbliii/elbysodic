"""Page actions for /claims — Chirp 0.10 ``_actions.py`` (#309).

Follows the recipe in ``pages/characters/_actions.py`` and
``pages/notifications/_actions.py``. Mutations dispatch on the hidden
``_action`` form field. ``page.py`` ``post()`` is only the no-``_action``
fallback.
"""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.pages.actions import action
from chirp.templating.returns import FormAction, Page

from elbysodic.db.repositories.base import TenantBoundaryError
from elbysodic.services import AppServices
from elbysodic.web.pages.claims.page import render_claims


def _optional_int(value: str) -> int | None:
    return int(value) if value else None


def _required_int(value: str, message: str) -> int:
    if not value:
        raise ValueError(message)
    return int(value)


@action("create_claim")
async def create_claim(
    request: Request,
    services: AppServices,
    claim_type_id: str = "",
    label: str = "",
    status: str = "",
    character_id: str = "",
    notes: str = "",
) -> FormAction | Page:
    try:
        services.create_director_claim(
            _required_int(claim_type_id, "choose a claim type"),
            label=label,
            status=status or "claimed",
            character_id=_optional_int(character_id),
            notes=notes,
        )
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except (LookupError, ValueError, TenantBoundaryError) as exc:
        return render_claims(request, error=str(exc))
    return FormAction("/claims", status=302)


@action("update_claim")
async def update_claim(
    request: Request,
    services: AppServices,
    claim_id: str = "",
    label: str = "",
    status: str = "",
    character_id: str = "",
    notes: str = "",
) -> FormAction | Page:
    try:
        services.update_director_claim(
            _required_int(claim_id, "choose a claim to update"),
            label=label,
            status=status or "claimed",
            character_id=_optional_int(character_id),
            notes=notes,
        )
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except (LookupError, ValueError, TenantBoundaryError) as exc:
        return render_claims(request, error=str(exc))
    return FormAction("/claims", status=302)
