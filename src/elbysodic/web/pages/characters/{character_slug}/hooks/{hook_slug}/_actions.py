"""Page actions for /characters/{character_slug}/hooks/{hook_slug} (#327).

Follows the recipe in ``pages/wanted/{wanted_slug}/_actions.py``. Mutations
dispatch on the hidden ``_action`` form field. ``page.py`` ``post()`` is only
the no-``_action`` fallback.
"""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.pages.actions import action
from chirp.templating.returns import FormAction

from elbysodic.services import AppServices


def _parse_interest_id(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise HTTPError(status=400, detail="interest_id must be an integer") from exc


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


@action("express_interest")
async def express_interest(
    services: AppServices,
    character_slug: str,
    hook_slug: str,
) -> FormAction:
    try:
        services.express_plot_hook_interest(character_slug, hook_slug)
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction(f"/characters/{character_slug}/hooks/{hook_slug}", status=302)


@action("start_plotting_room")
async def start_plotting_room(
    services: AppServices,
    character_slug: str,
    hook_slug: str,
    interest_id: str = "",
) -> FormAction:
    try:
        room = services.create_plotting_room_from_plot_hook_interest(
            character_slug,
            hook_slug,
            _parse_interest_id(interest_id),
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction(f"/plotting/{room.id}", status=302)


@action("save")
async def save(
    request: Request,
    services: AppServices,
    character_slug: str,
    hook_slug: str,
    title: str = "",
    hook_type: str = "",
    summary: str = "",
    body: str = "",
    status: str = "",
) -> FormAction:
    form = await request.form()
    try:
        hook = services.update_plot_hook(
            character_slug,
            hook_slug,
            title=title,
            hook_type=hook_type or "scene",
            summary=summary,
            body=body,
            status=status or "open",
            facet_slugs=_facet_slugs(form),
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction(f"/characters/{character_slug}/hooks/{hook.slug}", status=302)


@action("archive")
async def archive(
    request: Request,
    services: AppServices,
    character_slug: str,
    hook_slug: str,
    title: str = "",
    hook_type: str = "",
    summary: str = "",
    body: str = "",
) -> FormAction:
    form = await request.form()
    try:
        hook = services.update_plot_hook(
            character_slug,
            hook_slug,
            title=title,
            hook_type=hook_type or "scene",
            summary=summary,
            body=body,
            status="archived",
            facet_slugs=_facet_slugs(form),
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction(f"/characters/{character_slug}/hooks/{hook.slug}", status=302)
