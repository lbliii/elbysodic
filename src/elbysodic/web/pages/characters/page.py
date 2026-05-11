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
    POST_STYLE_PRESETS,
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
    post_style_preset: str
    accent_source: str
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
    post_style_preset = str(form.get("post_style_preset") or "")
    accent_source = str(form.get("accent_source") or "inherit")
    if accent_source != "custom":
        accent_color = ""
    make_default = str(form.get("make_default") or "") == "on"

    try:
        character = get_services(request).create_character(
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
            post_style_preset=post_style_preset,
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
            post_style_preset=post_style_preset,
            accent_source=accent_source,
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
    post_style_preset: str = "",
    accent_source: str = "inherit",
    make_default: bool = False,
) -> Page:
    services = get_services(request)
    viewer = services.viewer()
    style_policy = services.post_style_policy()
    post_style_preview_config_id = "character-post-style-preview-config"
    return Page.mounted(
        "characters/page.html",
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
        post_style_preset=post_style_preset,
        accent_source=accent_source,
        post_profile_variant_labels=style_policy.profile_variant_labels(),
        post_accent_style_labels=style_policy.accent_style_labels(),
        post_border_style_labels=style_policy.border_style_labels(),
        post_title_style_labels=style_policy.title_style_labels(),
        post_density_labels=style_policy.density_labels(),
        post_style_presets=POST_STYLE_PRESETS,
        post_style_preview_config_id=post_style_preview_config_id,
        post_style_preview_config={
            "inheritedAccentColor": "",
            "inheritedAccentLabel": "Inherit from community direction",
            "initial": {
                "accentSource": accent_source,
                "customAccent": accent_color,
                "name": name or "New face",
                "postAccentStyle": post_accent_style,
                "postBorderStyle": post_border_style,
                "postDensity": post_density,
                "postProfileVariant": post_profile_variant,
                "postTitleStyle": post_title_style,
                "posterAlt": poster_alt,
                "posterUrl": poster_url,
                "stylePreset": post_style_preset,
                "summary": summary,
                "tagline": tagline,
                "writer": viewer.membership.username,
            },
            "presets": POST_STYLE_PRESETS,
        },
        all_post_profile_variant_labels=POST_PROFILE_VARIANT_LABELS,
        all_post_accent_style_labels=POST_ACCENT_STYLE_LABELS,
        all_post_border_style_labels=POST_BORDER_STYLE_LABELS,
        all_post_title_style_labels=POST_TITLE_STYLE_LABELS,
        all_post_density_labels=POST_DENSITY_LABELS,
        make_default=make_default,
    )
