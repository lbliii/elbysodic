"""Character plot-hook detail page."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.services.plot_hooks import PLOT_HOOK_STATUSES, PLOT_HOOK_TYPES
from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class PlotHookActionForm:
    intent: str
    interest_id: str = ""
    title: str = ""
    hook_type: str = ""
    status: str = ""
    summary: str = ""
    body: str = ""
    facets: str = ""


def get(request: Request, character_slug: str, hook_slug: str) -> Page:
    return _render_hook(request, character_slug, hook_slug)


@contract(
    form=FormContract(
        PlotHookActionForm,
        "characters/{character_slug}/hooks/{hook_slug}/page.html",
    )
)
async def post(request: Request, character_slug: str, hook_slug: str) -> Page | Redirect:
    services = get_services(request)
    form = await request.form()
    intent = str(form.get("intent") or "")
    if intent == "express_interest":
        try:
            services.express_plot_hook_interest(character_slug, hook_slug)
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        return Redirect(f"/characters/{character_slug}/hooks/{hook_slug}")
    if intent == "start_plotting_room":
        try:
            room = services.create_plotting_room_from_plot_hook_interest(
                character_slug,
                hook_slug,
                _parse_interest_id(form.get("interest_id")),
            )
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        return Redirect(f"/plotting/{room.id}")
    if intent == "save":
        try:
            hook = services.update_plot_hook(
                character_slug,
                hook_slug,
                title=str(form.get("title") or ""),
                hook_type=str(form.get("hook_type") or "scene"),
                summary=str(form.get("summary") or ""),
                body=str(form.get("body") or ""),
                status=str(form.get("status") or "open"),
                facet_slugs=_facet_slugs(form),
            )
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        return Redirect(f"/characters/{character_slug}/hooks/{hook.slug}")
    if intent == "archive":
        try:
            hook = services.update_plot_hook(
                character_slug,
                hook_slug,
                title=str(form.get("title") or ""),
                hook_type=str(form.get("hook_type") or "scene"),
                summary=str(form.get("summary") or ""),
                body=str(form.get("body") or ""),
                status="archived",
                facet_slugs=_facet_slugs(form),
            )
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        return Redirect(f"/characters/{character_slug}/hooks/{hook.slug}")
    raise HTTPError(status=400, detail=f"unknown plot hook intent: {intent}")


def _render_hook(request: Request, character_slug: str, hook_slug: str) -> Page:
    services = get_services(request)
    try:
        hook = services.read_plot_hook(character_slug, hook_slug)
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    return Page.mounted(
        "characters/{character_slug}/hooks/{hook_slug}/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        hook=hook,
        plot_hook_types=PLOT_HOOK_TYPES,
        plot_hook_statuses=PLOT_HOOK_STATUSES,
    )


def _facet_slugs(form: object) -> list[str]:
    values: list[object]
    get_list = getattr(form, "get_list", None)
    getlist = getattr(form, "getlist", None)
    if callable(get_list):
        values = list(get_list("facets"))
    elif callable(getlist):
        values = list(getlist("facets"))
    else:
        raw = getattr(form, "get", lambda _name: None)("facets")
        values = [] if raw is None else [raw]
    slugs: list[str] = []
    for value in values:
        slug = str(value or "").strip()
        if slug and slug not in slugs:
            slugs.append(slug)
    return slugs


def _parse_interest_id(value: object) -> int:
    try:
        return int(str(value or ""))
    except ValueError as exc:
        raise HTTPError(status=400, detail="interest_id must be an integer") from exc
