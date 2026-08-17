"""Page actions for /notifications — Chirp 0.10 ``_actions.py`` (#303).

Follows the recipe in ``pages/characters/_actions.py``. Mutations dispatch
on the hidden ``_action`` form field. ``page.py`` ``post()`` is only the
no-``_action`` fallback.
"""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.pages.actions import action
from chirp.templating.returns import FormAction

from elbysodic.services import AppServices


def _parse_notification_id(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise HTTPError(status=400, detail="notification_id must be an integer") from exc


@action("mark_all_read")
async def mark_all_read(services: AppServices) -> FormAction:
    services.mark_all_notifications_read()
    return FormAction("/notifications", status=302)


@action("open")
async def open_notification(
    services: AppServices,
    notification_id: str = "",
) -> FormAction:
    try:
        href = services.open_notification(_parse_notification_id(notification_id))
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    return FormAction(href, status=302)
