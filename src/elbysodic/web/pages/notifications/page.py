"""Notification inbox for watched threads and mentions.

Mutations live in ``_actions.py`` (Chirp page actions, dispatched on the
hidden ``_action`` form field). ``post()`` below is only the no-``_action``
fallback that keeps the POST method registered on this path.
"""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services

NOTIFICATIONS_TEMPLATE = "notifications/page.html"


@dataclass(frozen=True, slots=True)
class NotificationActionForm:
    _action: str
    notification_id: str = ""


def get(request: Request) -> Page:
    return _render_notifications(request)


@contract(form=FormContract(NotificationActionForm, NOTIFICATIONS_TEMPLATE))
async def post(request: Request) -> Page:
    """Fallback — mutations dispatch via ``pages/notifications/_actions.py``."""
    return _render_notifications(request)


def _render_notifications(request: Request) -> Page:
    services = get_services(request)
    viewer = services.viewer()
    notification_center = services.notification_center()
    return Page.mounted(
        NOTIFICATIONS_TEMPLATE,
        current_path=request.url,
        viewer=viewer,
        inbox=notification_center.inbox,
    )
