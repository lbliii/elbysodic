"""Character profile for the active community roster."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.services.plot_hooks import PLOT_HOOK_TYPES
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
class CharacterProfileForm:
    intent: str
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
    post_profile_variant = str(form.get("post_profile_variant") or "bio")
    post_accent_style = str(form.get("post_accent_style") or "soft")
    post_border_style = str(form.get("post_border_style") or "hairline")
    post_title_style = str(form.get("post_title_style") or "standard")
    post_density = str(form.get("post_density") or "calm")
    post_style_preset = str(form.get("post_style_preset") or "")
    accent_source = str(form.get("accent_source") or "inherit")
    if accent_source != "custom":
        accent_color = ""
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
            post_profile_variant=post_profile_variant,
            post_accent_style=post_accent_style,
            post_border_style=post_border_style,
            post_title_style=post_title_style,
            post_density=post_density,
            post_style_preset=post_style_preset,
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
            post_profile_variant=post_profile_variant,
            post_accent_style=post_accent_style,
            post_border_style=post_border_style,
            post_title_style=post_title_style,
            post_density=post_density,
            post_style_preset=post_style_preset,
            accent_source=accent_source,
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
    post_profile_variant: str | None = None,
    post_accent_style: str | None = None,
    post_border_style: str | None = None,
    post_title_style: str | None = None,
    post_density: str | None = None,
    post_style_preset: str = "",
    accent_source: str | None = None,
) -> Page:
    services = get_services()
    viewer = services.viewer()
    profile = services.read_character(character_slug)
    style_policy = services.post_style_policy()
    resolved_accent_source = (
        "custom"
        if (profile.character.accent_color if accent_source is None else accent_color)
        else "inherit"
    )
    current_name = profile.character.name if name is None else name
    current_summary = profile.character.summary if summary is None else summary
    current_poster_url = profile.character.poster_url or "" if poster_url is None else poster_url
    current_poster_alt = profile.character.poster_alt if poster_alt is None else poster_alt
    current_tagline = profile.character.tagline if tagline is None else tagline
    current_accent_color = profile.character.accent_color if accent_color is None else accent_color
    current_post_profile_variant = (
        profile.character.post_profile_variant
        if post_profile_variant is None
        else post_profile_variant
    )
    current_post_accent_style = (
        profile.character.post_accent_style if post_accent_style is None else post_accent_style
    )
    current_post_border_style = (
        profile.character.post_border_style if post_border_style is None else post_border_style
    )
    current_post_title_style = (
        profile.character.post_title_style if post_title_style is None else post_title_style
    )
    current_post_density = profile.character.post_density if post_density is None else post_density
    preview_accent_color = (
        current_accent_color
        if resolved_accent_source == "custom" and current_accent_color
        else profile.accent_color
    )
    preview_accent_label = (
        "Custom accent"
        if resolved_accent_source == "custom" and current_accent_color
        else profile.accent_source_label
    )
    post_style_preview_config_id = f"character-post-style-preview-config-{profile.character.id}"
    return Page(
        "characters/{character_slug}/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        profile=profile,
        error=error,
        name=current_name,
        summary=current_summary,
        avatar_url=profile.character.avatar_url or "" if avatar_url is None else avatar_url,
        poster_url=current_poster_url,
        poster_alt=current_poster_alt,
        tagline=current_tagline,
        accent_color=current_accent_color,
        post_profile_variant=current_post_profile_variant,
        post_accent_style=current_post_accent_style,
        post_border_style=current_post_border_style,
        post_title_style=current_post_title_style,
        post_density=current_post_density,
        post_style_preset=post_style_preset,
        accent_source=resolved_accent_source,
        post_profile_variant_labels=style_policy.profile_variant_labels(
            profile.character.post_profile_variant,
        ),
        post_accent_style_labels=style_policy.accent_style_labels(
            profile.character.post_accent_style,
        ),
        post_border_style_labels=style_policy.border_style_labels(
            profile.character.post_border_style,
        ),
        post_title_style_labels=style_policy.title_style_labels(
            profile.character.post_title_style,
        ),
        post_density_labels=style_policy.density_labels(profile.character.post_density),
        post_style_presets=POST_STYLE_PRESETS,
        post_style_preview_config_id=post_style_preview_config_id,
        post_style_preview_config={
            "inheritedAccentColor": profile.accent_color,
            "inheritedAccentLabel": profile.accent_source_label,
            "initial": {
                "accentSource": resolved_accent_source,
                "customAccent": current_accent_color or "",
                "name": current_name,
                "postAccentStyle": current_post_accent_style,
                "postBorderStyle": current_post_border_style,
                "postDensity": current_post_density,
                "postProfileVariant": current_post_profile_variant,
                "postTitleStyle": current_post_title_style,
                "posterAlt": current_poster_alt,
                "posterUrl": current_poster_url,
                "stylePreset": post_style_preset,
                "summary": current_summary,
                "tagline": current_tagline,
                "writer": profile.owner_membership.username,
            },
            "presets": POST_STYLE_PRESETS,
        },
        preview_accent_color=preview_accent_color,
        preview_accent_label=preview_accent_label,
        all_post_profile_variant_labels=POST_PROFILE_VARIANT_LABELS,
        all_post_accent_style_labels=POST_ACCENT_STYLE_LABELS,
        all_post_border_style_labels=POST_BORDER_STYLE_LABELS,
        all_post_title_style_labels=POST_TITLE_STYLE_LABELS,
        all_post_density_labels=POST_DENSITY_LABELS,
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
