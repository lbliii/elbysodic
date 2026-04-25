"""Notification inbox for watched threads and mentions."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request) -> Page:
    return _render_notifications(request)


async def post(request: Request) -> Page | Redirect:
    services = get_services()
    form = await request.form()
    intent = str(form.get("intent") or "")
    if intent == "mark_all_read":
        services.mark_all_notifications_read()
        return Redirect("/notifications")
    if intent == "open":
        try:
            href = services.open_notification(_parse_notification_id(form.get("notification_id")))
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        return Redirect(href)
    raise HTTPError(status=400, detail=f"unknown notification intent: {intent}")


def _render_notifications(request: Request) -> Page:
    services = get_services()
    viewer = services.viewer()
    return Page(
        "notifications/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        inbox=services.notifications(),
    )


def _parse_notification_id(value: object) -> int:
    try:
        return int(str(value or ""))
    except ValueError as exc:
        raise HTTPError(status=400, detail="notification_id must be an integer") from exc
