"""Director Studio discovery profile editor."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request) -> Page:
    return _render_discovery_editor(request)


async def post(request: Request) -> Page | Redirect:
    services = get_services(request)
    form = await request.form()
    try:
        services.update_discovery_profile(
            premise_archetype=str(form.get("premise_archetype") or ""),
            play_engine=str(form.get("play_engine") or ""),
            lore_aperture=str(form.get("lore_aperture") or ""),
            access_model=str(form.get("access_model") or ""),
            application_model=str(form.get("application_model") or ""),
            age_rating=str(form.get("age_rating") or ""),
            content_rating=str(form.get("content_rating") or ""),
            activity_pace=str(form.get("activity_pace") or ""),
            activity_expectation=str(form.get("activity_expectation") or ""),
            forum_adjunct=str(form.get("forum_adjunct") or ""),
            roster_posture=str(form.get("roster_posture") or ""),
            catalog_pitch=str(form.get("catalog_pitch") or ""),
            onboarding_pitch=str(form.get("onboarding_pitch") or ""),
            staff_pick_label=str(form.get("staff_pick_label") or ""),
            tag_lines=str(form.get("discovery_tags") or ""),
        )
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except (LookupError, ValueError) as exc:
        return _render_discovery_editor(request, error=str(exc))
    return Redirect("/studio/discovery")


def _render_discovery_editor(request: Request, *, error: str | None = None) -> Page:
    services = get_services(request)
    try:
        editor = services.discovery_profile_editor()
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    return Page.mounted(
        "studio/discovery/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        studio=services.director_studio(),
        editor=editor,
        error=error,
    )
