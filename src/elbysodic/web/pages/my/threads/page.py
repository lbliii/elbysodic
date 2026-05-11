"""Writer obligation dashboard."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services import AppServices


def get(request: Request, services: AppServices) -> Page:
    viewer = services.viewer()
    selected_character_slug = _selected_character_slug(request, viewer)
    return Page.mounted(
        "my/threads/page.html",
        current_path=request.url,
        viewer=viewer,
        dashboard=services.my_threads(character_slug=selected_character_slug),
        character_lens_is_explicit=request.query.get("character") is not None,
    )


def _selected_character_slug(request: Request, viewer: object) -> str | None:
    raw_value = request.query.get("character")
    if raw_value is None:
        current_character = getattr(viewer, "current_character", None)
        slug = getattr(current_character, "slug", "")
        return str(slug) if slug else None
    value = str(raw_value or "").strip().lower()
    if value in {"", "all", "none"}:
        return None
    return value or None
