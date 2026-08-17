"""Page actions for /wanted/{wanted_slug} — Chirp 0.10 ``_actions.py`` (#314).

Follows the recipe in ``pages/notifications/_actions.py`` and
``pages/claims/_actions.py``. Mutations dispatch on the hidden
``_action`` form field. ``page.py`` ``post()`` is only the no-``_action``
fallback.
"""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.pages.actions import action
from chirp.templating.returns import FormAction

from elbysodic.services import AppServices


def _parse_interest_id(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise HTTPError(status=400, detail="interest_id must be an integer") from exc


@action("express_interest")
async def express_interest(services: AppServices, wanted_slug: str) -> FormAction:
    try:
        services.express_wanted_interest(wanted_slug)
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction(f"/wanted/{wanted_slug}", status=302)


@action("express_prospective_interest")
async def express_prospective_interest(
    services: AppServices,
    wanted_slug: str,
    prospective_character_name: str = "",
    note: str = "",
) -> FormAction:
    try:
        services.express_prospective_wanted_interest(
            wanted_slug,
            prospective_character_name=prospective_character_name,
            note=note,
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction(f"/wanted/{wanted_slug}", status=302)


@action("reserve_interest")
async def reserve_interest(
    services: AppServices,
    wanted_slug: str,
    interest_id: str = "",
) -> FormAction:
    try:
        services.reserve_wanted_interest(wanted_slug, _parse_interest_id(interest_id))
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction(f"/wanted/{wanted_slug}", status=302)


@action("start_plotting_room")
async def start_plotting_room(
    services: AppServices,
    wanted_slug: str,
    interest_id: str = "",
) -> FormAction:
    try:
        room = services.create_plotting_room_from_wanted_interest(
            wanted_slug,
            _parse_interest_id(interest_id),
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction(f"/plotting/{room.id}", status=302)


@action("create_reserve")
async def create_reserve(
    services: AppServices,
    wanted_slug: str,
    interest_id: str = "",
) -> FormAction:
    try:
        services.create_reserve_for_wanted_interest(
            wanted_slug,
            _parse_interest_id(interest_id),
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction(f"/wanted/{wanted_slug}", status=302)


@action("update_lifecycle_status")
async def update_lifecycle_status(
    services: AppServices,
    wanted_slug: str,
    status: str = "",
) -> FormAction:
    try:
        services.update_wanted_ad_lifecycle_status(wanted_slug, status=status)
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction(f"/wanted/{wanted_slug}", status=302)
