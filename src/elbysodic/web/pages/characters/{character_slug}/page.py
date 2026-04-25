"""Character profile for the active community roster."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class CharacterProfileForm:
    intent: str
    name: str
    avatar_url: str
    summary: str


def get(request: Request, character_slug: str) -> Page:
    return _render_profile(request, character_slug)


@contract(form=FormContract(CharacterProfileForm, "characters/{character_slug}/page.html"))
async def post(request: Request, character_slug: str) -> Page | Redirect:
    form = await request.form()
    services = get_services()
    intent = str(form.get("intent") or "save")
    if intent == "set_default":
        profile = services.read_character(character_slug)
        try:
            services.set_default_character(profile.character.id)
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        return Redirect(f"/characters/{profile.character.slug}")

    name = str(form.get("name") or "")
    summary = str(form.get("summary") or "")
    avatar_url = str(form.get("avatar_url") or "")
    try:
        character = services.update_character(
            character_slug,
            name=name,
            summary=summary,
            avatar_url=avatar_url,
        )
    except ValueError as exc:
        return _render_profile(
            request,
            character_slug,
            error=str(exc),
            name=name,
            summary=summary,
            avatar_url=avatar_url,
        )
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    return Redirect(f"/characters/{character.slug}")


def _render_profile(
    request: Request,
    character_slug: str,
    *,
    error: str | None = None,
    name: str | None = None,
    summary: str | None = None,
    avatar_url: str | None = None,
) -> Page:
    services = get_services()
    viewer = services.viewer()
    profile = services.read_character(character_slug)
    return Page(
        "characters/{character_slug}/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        profile=profile,
        error=error,
        name=profile.character.name if name is None else name,
        summary=profile.character.summary if summary is None else summary,
        avatar_url=profile.character.avatar_url or "" if avatar_url is None else avatar_url,
    )
