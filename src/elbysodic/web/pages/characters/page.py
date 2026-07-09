"""Character roster for the active community membership.

Mutations live in ``_actions.py`` (Chirp page actions, dispatched on the
hidden ``_action`` form field). ``post()`` below is only the no-``_action``
fallback that keeps the POST method registered on this path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from chirp.contracts import FormContract, contract
from chirp.http.request import Request
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

ROSTER_TEMPLATE = "characters/page.html"


@dataclass(frozen=True, slots=True)
class CharacterCreateForm:
    _action: str
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
    return render_roster(request)


@contract(form=FormContract(CharacterCreateForm, ROSTER_TEMPLATE))
async def post(request: Request) -> Page:
    """Fallback — creation dispatches via ``pages/characters/_actions.py``."""
    return render_roster(request)


def roster_context(
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
) -> dict[str, Any]:
    """Template context shared by the full roster page render and the
    ``character_create_form`` block re-render (the ValidationError path)."""
    services = get_services(request)
    viewer = services.viewer()
    roster_page = services.character_roster_page(
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
    )
    return {
        "current_path": request.url,
        "viewer": viewer,
        "roster_dashboard": roster_page.roster_dashboard,
        "error": error,
        "name": name,
        "summary": summary,
        "avatar_url": avatar_url,
        "poster_url": poster_url,
        "poster_alt": poster_alt,
        "tagline": tagline,
        "accent_color": accent_color,
        "post_profile_variant": post_profile_variant,
        "post_accent_style": post_accent_style,
        "post_border_style": post_border_style,
        "post_title_style": post_title_style,
        "post_density": post_density,
        "post_style_preset": post_style_preset,
        "accent_source": accent_source,
        "post_profile_variant_labels": roster_page.post_style_policy.profile_variant_labels(),
        "post_accent_style_labels": roster_page.post_style_policy.accent_style_labels(),
        "post_border_style_labels": roster_page.post_style_policy.border_style_labels(),
        "post_title_style_labels": roster_page.post_style_policy.title_style_labels(),
        "post_density_labels": roster_page.post_style_policy.density_labels(),
        "post_style_presets": POST_STYLE_PRESETS,
        "post_style_preview_config_id": roster_page.post_style_preview_config_id,
        "post_style_preview_config": roster_page.post_style_preview_config,
        "all_post_profile_variant_labels": POST_PROFILE_VARIANT_LABELS,
        "all_post_accent_style_labels": POST_ACCENT_STYLE_LABELS,
        "all_post_border_style_labels": POST_BORDER_STYLE_LABELS,
        "all_post_title_style_labels": POST_TITLE_STYLE_LABELS,
        "all_post_density_labels": POST_DENSITY_LABELS,
        "make_default": make_default,
    }


def render_roster(request: Request, **form_state: Any) -> Page:
    return Page.mounted(ROSTER_TEMPLATE, **roster_context(request, **form_state))
