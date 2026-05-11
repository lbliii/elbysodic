"""Realm interaction detail and response handling."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request, interaction_slug: str) -> Page:
    return _render_interaction(request, interaction_slug)


async def post(request: Request, interaction_slug: str) -> Page | Redirect:
    form = await request.form()
    selected_option_ids = _selected_option_ids(form)
    try:
        get_services(request).submit_realm_interaction(interaction_slug, selected_option_ids)
    except ValueError as exc:
        return _render_interaction(request, interaction_slug, error=str(exc))
    return Redirect(f"/interactions/{interaction_slug}")


def _render_interaction(
    request: Request,
    interaction_slug: str,
    *,
    error: str | None = None,
) -> Page:
    services = get_services(request)
    return Page.mounted(
        "interactions/{interaction_slug}/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        detail=services.read_realm_interaction(interaction_slug),
        error=error,
    )


def _selected_option_ids(form: object) -> dict[int, int]:
    selected: dict[int, int] = {}
    keys = getattr(form, "keys", list)()
    for key in keys:
        key_text = str(key)
        if not key_text.startswith("question_"):
            continue
        question_id_text = key_text.removeprefix("question_")
        value = getattr(form, "get", lambda _name: "")(key_text)
        try:
            question_id = int(question_id_text)
            option_id = int(str(value))
        except ValueError:
            continue
        selected[question_id] = option_id
    return selected
