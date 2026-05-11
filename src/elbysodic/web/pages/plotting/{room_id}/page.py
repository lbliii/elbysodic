"""Plotting room detail page."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Fragment, Page

from elbysodic.web.recovery import recover_missing_route
from elbysodic.web.state import get_services


def get(request: Request, room_id: str) -> Page:
    return _render_room(request, room_id)


async def post(request: Request, room_id: str) -> Fragment | Page | Redirect:
    services = get_services(request)
    parsed_room_id = _parse_room_id(room_id)
    form = await request.form()
    intent = str(form.get("intent") or "")
    if intent == "save_plan":
        try:
            services.update_plotting_room_plan(
                parsed_room_id,
                notes=str(form.get("notes") or ""),
                next_step=str(form.get("next_step") or ""),
                target_board_id=_optional_int(form.get("target_board_id")),
                status=str(form.get("status") or "brainstorming"),
            )
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        return Redirect(f"/plotting/{parsed_room_id}")
    if intent == "start_scene":
        try:
            services.create_thread_from_plotting_room(
                parsed_room_id,
                board_id=_required_int(form.get("board_id"), "board_id is required"),
                character_id=_required_int(form.get("character_id"), "character_id is required"),
                title=str(form.get("title") or ""),
                summary=str(form.get("summary") or ""),
                body=str(form.get("body") or ""),
                location=str(form.get("location") or ""),
                timeline=str(form.get("timeline") or ""),
                posting_mode=str(form.get("posting_mode") or "freeform"),
            )
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        return Redirect(f"/plotting/{parsed_room_id}")
    if intent == "post_message":
        try:
            await services.create_plotting_room_message(
                parsed_room_id,
                str(form.get("body") or ""),
            )
            room = services.read_plotting_room(parsed_room_id)
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        if request.is_htmx:
            return Fragment(
                "plotting/{room_id}/page.html",
                "plotting_room_message_composer",
                room=room,
                viewer=services.viewer(),
            )
        return Redirect(f"/plotting/{parsed_room_id}")
    raise HTTPError(status=400, detail=f"unknown plotting room intent: {intent}")


def _render_room(request: Request, room_id: str) -> Page:
    services = get_services(request)
    try:
        parsed_room_id = _parse_room_id(room_id)
    except HTTPError:
        return recover_missing_route(request, kind="plotting", slug=room_id)
    try:
        room = services.read_plotting_room(parsed_room_id)
    except LookupError:
        return recover_missing_route(request, kind="plotting", slug=room_id)
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    return Page.mounted(
        "plotting/{room_id}/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        room=room,
    )


def _parse_room_id(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise HTTPError(status=404, detail="plotting room not found") from exc


def _optional_int(value: object) -> int | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    return _required_int(raw, "value must be an integer")


def _required_int(value: object, message: str) -> int:
    try:
        return int(str(value or ""))
    except ValueError as exc:
        raise HTTPError(status=400, detail=message) from exc
