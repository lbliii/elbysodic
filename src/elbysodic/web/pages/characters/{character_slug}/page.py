"""Character profile for the active community roster."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.services.plot_hooks import PLOT_HOOK_TYPES
from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class CharacterProfileForm:
    intent: str
    name: str
    avatar_url: str
    poster_url: str
    poster_alt: str
    tagline: str
    accent_color: str
    summary: str
    plot_hook_title: str = ""
    plot_hook_type: str = ""
    plot_hook_summary: str = ""
    plot_hook_body: str = ""
    plot_hook_facets: str = ""


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
    if intent == "submit_application":
        try:
            character = services.submit_character_application(character_slug)
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        return Redirect(f"/characters/{character.slug}")
    if intent == "create_plot_hook":
        try:
            plot_hook = services.create_plot_hook(
                character_slug,
                title=str(form.get("plot_hook_title") or ""),
                hook_type=str(form.get("plot_hook_type") or "scene"),
                summary=str(form.get("plot_hook_summary") or ""),
                body=str(form.get("plot_hook_body") or ""),
                facet_slugs=_plot_hook_facet_slugs(form),
            )
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        return Redirect(f"/characters/{character_slug}/hooks/{plot_hook.slug}")

    name = str(form.get("name") or "")
    summary = str(form.get("summary") or "")
    avatar_url = str(form.get("avatar_url") or "")
    poster_url = str(form.get("poster_url") or "")
    poster_alt = str(form.get("poster_alt") or "")
    tagline = str(form.get("tagline") or "")
    accent_color = str(form.get("accent_color") or "")
    try:
        character = services.update_character(
            character_slug,
            name=name,
            summary=summary,
            avatar_url=avatar_url,
            poster_url=poster_url,
            poster_alt=poster_alt,
            tagline=tagline,
            accent_color=accent_color,
        )
    except ValueError as exc:
        return _render_profile(
            request,
            character_slug,
            error=str(exc),
            name=name,
            summary=summary,
            avatar_url=avatar_url,
            poster_url=poster_url,
            poster_alt=poster_alt,
            tagline=tagline,
            accent_color=accent_color,
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
    poster_url: str | None = None,
    poster_alt: str | None = None,
    tagline: str | None = None,
    accent_color: str | None = None,
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
        poster_url=profile.character.poster_url or "" if poster_url is None else poster_url,
        poster_alt=profile.character.poster_alt if poster_alt is None else poster_alt,
        tagline=profile.character.tagline if tagline is None else tagline,
        accent_color=profile.character.accent_color if accent_color is None else accent_color,
        plot_hook_types=PLOT_HOOK_TYPES,
    )


def _plot_hook_facet_slugs(form: object) -> list[str]:
    values: list[object]
    get_list = getattr(form, "get_list", None)
    getlist = getattr(form, "getlist", None)
    if callable(get_list):
        values = list(get_list("plot_hook_facets"))
    elif callable(getlist):
        values = list(getlist("plot_hook_facets"))
    else:
        raw = getattr(form, "get", lambda _name: None)("plot_hook_facets")
        values = [] if raw is None else [raw]
    slugs: list[str] = []
    for value in values:
        slug = str(value or "").strip()
        if slug and slug not in slugs:
            slugs.append(slug)
    return slugs
