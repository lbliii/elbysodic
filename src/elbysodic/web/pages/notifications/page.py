"""Notification inbox for watched threads and mentions."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.forms import FormData
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.web.actions import dispatch_form_action
from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class NotificationActionForm:
    intent: str
    notification_id: str = ""


def get(request: Request) -> Page:
    return _render_notifications(request)


@contract(form=FormContract(NotificationActionForm, "notifications/page.html"))
async def post(request: Request) -> Page | Redirect:
    form = await request.form()
    return await dispatch_form_action(
        request,
        form,
        {
            "mark_all_read": _mark_all_read,
            "open": _open_notification,
        },
        unknown_detail="unknown notification intent",
    )


def _render_notifications(request: Request) -> Page:
    services = get_services(request)
    viewer = services.viewer()
    notification_center = services.notification_center()
    return Page.mounted(
        "notifications/page.html",
        current_path=request.url,
        viewer=viewer,
        inbox=notification_center.inbox,
    )


def _parse_notification_id(value: object) -> int:
    try:
        return int(str(value or ""))
    except ValueError as exc:
        raise HTTPError(status=400, detail="notification_id must be an integer") from exc


def _mark_all_read(request: Request, _form: FormData) -> Redirect:
    get_services(request).mark_all_notifications_read()
    return Redirect("/notifications")


def _open_notification(request: Request, form: FormData) -> Redirect:
    try:
        href = get_services(request).open_notification(
            _parse_notification_id(form.get("notification_id"))
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    return Redirect(href)
