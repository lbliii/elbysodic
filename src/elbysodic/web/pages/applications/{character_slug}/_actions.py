"""Page actions for /applications/{character_slug} — Chirp 0.10 ``_actions.py`` (#343).

Follows the recipe in ``pages/wanted/{wanted_slug}/_actions.py`` and
``pages/characters/{character_slug}/hooks/{hook_slug}/_actions.py``. Mutations
dispatch on the hidden ``_action`` form field. ``page.py`` ``post()`` is only
the no-``_action`` fallback.
"""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.pages.actions import action
from chirp.templating.returns import FormAction

from elbysodic.services import AppServices
from elbysodic.services.read_models import ApplicationReviewRoom


def _application_field_values(
    form: object,
    room: ApplicationReviewRoom,
) -> dict[int, str]:
    values: dict[int, str] = {}
    form_get = getattr(form, "get", lambda _name: None)
    if not any(
        form_get(f"application_field_{item.field.field.id}") is not None
        for item in room.intake_fields
    ):
        return values
    for item in room.intake_fields:
        field = item.field.field
        value = str(form_get(f"application_field_{field.id}") or "")
        value = value.strip()
        if field.is_required and not value:
            raise ValueError(f"{field.label} is required")
        values[field.id] = value[:5000]
    return values


@action("save_application")
async def save_application(
    request: Request,
    services: AppServices,
    character_slug: str,
    summary: str = "",
    body: str = "",
) -> FormAction:
    form = await request.form()
    try:
        room = services.read_application_review_room(character_slug)
        services.update_application_draft(
            character_slug,
            summary=summary,
            body=body,
            application_field_values=_application_field_values(form, room),
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction(f"/applications/{character_slug}", status=302)


@action("submit_application")
async def submit_application(
    services: AppServices,
    character_slug: str,
) -> FormAction:
    try:
        services.submit_character_application(character_slug)
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction(f"/applications/{character_slug}", status=302)


@action("save_review")
async def save_review(
    services: AppServices,
    character_slug: str,
    revision_notes: str = "",
    staff_notes: str = "",
    checklist: str = "",
) -> FormAction:
    try:
        services.update_application_review(
            character_slug,
            revision_notes=revision_notes,
            staff_notes=staff_notes,
            checklist=checklist,
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction(f"/applications/{character_slug}", status=302)


@action("accept_application")
async def accept_application(
    services: AppServices,
    character_slug: str,
) -> FormAction:
    try:
        services.accept_character_application(character_slug)
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction(f"/applications/{character_slug}", status=302)


@action("request_revision")
async def request_revision(
    services: AppServices,
    character_slug: str,
    revision_notes: str = "",
) -> FormAction:
    try:
        services.request_character_application_revision(
            character_slug,
            note=revision_notes,
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction(f"/applications/{character_slug}", status=302)
