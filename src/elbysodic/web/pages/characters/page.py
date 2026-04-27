"""Character roster for the active community membership."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.services.read_models import (
    POST_ACCENT_STYLE_LABELS,
    POST_BORDER_STYLE_LABELS,
    POST_DENSITY_LABELS,
    POST_PROFILE_VARIANT_LABELS,
    POST_TITLE_STYLE_LABELS,
)
from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class CharacterCreateForm:
    name: str
    avatar_url: str
    poster_url: str
    poster_alt: str
    tagline: str
    accent_color: str
    post_profile_variant: str
    post_accent_style: str
    post_border_style: str
    post_title_style: str
    post_density: str
    summary: str
    make_default: str


def get(request: Request) -> Page:
    return _render_roster(request)


@contract(form=FormContract(CharacterCreateForm, "characters/page.html"))
async def post(request: Request) -> Page | Redirect:
    form = await request.form()
    name = str(form.get("name") or "")
    summary = str(form.get("summary") or "")
    avatar_url = str(form.get("avatar_url") or "")
    poster_url = str(form.get("poster_url") or "")
    poster_alt = str(form.get("poster_alt") or "")
    tagline = str(form.get("tagline") or "")
    accent_color = str(form.get("accent_color") or "")
    post_profile_variant = str(form.get("post_profile_variant") or "bio")
    post_accent_style = str(form.get("post_accent_style") or "soft")
    post_border_style = str(form.get("post_border_style") or "hairline")
    post_title_style = str(form.get("post_title_style") or "standard")
    post_density = str(form.get("post_density") or "calm")
    make_default = str(form.get("make_default") or "") == "on"

    try:
        character = get_services().create_character(
            name=name,
            summary=summary,
            avatar_url=avatar_url,
            poster_url=poster_url,
            poster_alt=poster_alt,
            tagline=tagline,
            accent_color=accent_color,
            post_profile_variant=post_profile_variant,
            post_accent_style=post_accent_style,
            post_border_style=post_border_style,
            post_title_style=post_title_style,
            post_density=post_density,
            make_default=make_default,
        )
    except ValueError as exc:
        return _render_roster(
            request,
            error=str(exc),
            name=name,
            summary=summary,
            avatar_url=avatar_url,
            poster_url=poster_url,
            poster_alt=poster_alt,
            tagline=tagline,
            accent_color=accent_color,
            post_profile_variant=post_profile_variant,
            post_accent_style=post_accent_style,
            post_border_style=post_border_style,
            post_title_style=post_title_style,
            post_density=post_density,
            make_default=make_default,
        )

    return Redirect(f"/characters/{character.slug}")


def _render_roster(
    request: Request,
    *,
    error: str | None = None,
    name: str = "",
    summary: str = "",
    avatar_url: str = "",
    poster_url: str = "",
    poster_alt: str = "",
    tagline: str = "",
    accent_color: str = "",
    post_profile_variant: str = "bio",
    post_accent_style: str = "soft",
    post_border_style: str = "hairline",
    post_title_style: str = "standard",
    post_density: str = "calm",
    make_default: bool = False,
) -> Page:
    services = get_services()
    viewer = services.viewer()
    return Page(
        "characters/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        roster_dashboard=services.character_roster(),
        error=error,
        name=name,
        summary=summary,
        avatar_url=avatar_url,
        poster_url=poster_url,
        poster_alt=poster_alt,
        tagline=tagline,
        accent_color=accent_color,
        post_profile_variant=post_profile_variant,
        post_accent_style=post_accent_style,
        post_border_style=post_border_style,
        post_title_style=post_title_style,
        post_density=post_density,
        post_profile_variant_labels=POST_PROFILE_VARIANT_LABELS,
        post_accent_style_labels=POST_ACCENT_STYLE_LABELS,
        post_border_style_labels=POST_BORDER_STYLE_LABELS,
        post_title_style_labels=POST_TITLE_STYLE_LABELS,
        post_density_labels=POST_DENSITY_LABELS,
        make_default=make_default,
    )
