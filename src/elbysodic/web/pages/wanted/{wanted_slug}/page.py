"""Wanted hook detail page."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.web.recovery import recover_missing_route
from elbysodic.web.state import get_services


def get(request: Request, wanted_slug: str) -> Page:
    return _render_wanted(request, wanted_slug)


async def post(request: Request, wanted_slug: str) -> Page | Redirect:
    services = get_services(request)
    form = await request.form()
    intent = str(form.get("intent") or "")
    if intent == "express_interest":
        try:
            services.express_wanted_interest(wanted_slug)
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        return Redirect(f"/wanted/{wanted_slug}")
    if intent == "express_prospective_interest":
        try:
            services.express_prospective_wanted_interest(
                wanted_slug,
                prospective_character_name=str(form.get("prospective_character_name") or ""),
                note=str(form.get("note") or ""),
            )
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        return Redirect(f"/wanted/{wanted_slug}")
    if intent == "reserve_interest":
        try:
            services.reserve_wanted_interest(
                wanted_slug,
                _parse_interest_id(form.get("interest_id")),
            )
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        return Redirect(f"/wanted/{wanted_slug}")
    if intent == "start_plotting_room":
        try:
            room = services.create_plotting_room_from_wanted_interest(
                wanted_slug,
                _parse_interest_id(form.get("interest_id")),
            )
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        return Redirect(f"/plotting/{room.id}")
    if intent == "create_reserve":
        try:
            services.create_reserve_for_wanted_interest(
                wanted_slug,
                _parse_interest_id(form.get("interest_id")),
            )
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        return Redirect(f"/wanted/{wanted_slug}")
    if intent == "update_lifecycle_status":
        try:
            services.update_wanted_ad_lifecycle_status(
                wanted_slug,
                status=str(form.get("status") or ""),
            )
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        return Redirect(f"/wanted/{wanted_slug}")
    raise HTTPError(status=400, detail=f"unknown wanted intent: {intent}")


def _render_wanted(request: Request, wanted_slug: str) -> Page:
    services = get_services(request)
    try:
        wanted = services.read_wanted_ad(wanted_slug)
    except LookupError:
        return recover_missing_route(request, kind="wanted", slug=wanted_slug)
    return Page(
        "wanted/{wanted_slug}/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=services.viewer(),
        wanted=wanted,
    )


def _parse_interest_id(value: object) -> int:
    try:
        return int(str(value or ""))
    except ValueError as exc:
        raise HTTPError(status=400, detail="interest_id must be an integer") from exc
