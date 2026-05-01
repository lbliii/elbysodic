"""Director Studio hub."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.domain.boards import BOARD_KIND_LABELS, BOARD_SIDEBAR_SECTION_LABELS
from elbysodic.services.read_models import (
    POST_ACCENT_STYLE_LABELS,
    POST_BORDER_STYLE_LABELS,
    POST_DENSITY_LABELS,
    POST_PROFILE_VARIANT_LABELS,
    POST_TITLE_STYLE_LABELS,
)
from elbysodic.services.themes import (
    DENSITY_LABELS,
    FONT_STACK_LABELS,
    RADIUS_LABELS,
    TEXTURE_LABELS,
    THEME_MODE_FIELDS,
)
from elbysodic.web.state import get_services


def get(request: Request) -> Page:
    return _render_studio(request)


async def post(request: Request) -> Page | Redirect:
    services = get_services(request)
    form = await request.form()
    intent = str(form.get("intent") or "identity_accent")
    redirect_to = "/studio"
    try:
        if intent == "board_taxonomy":
            raw_parent_id = str(form.get("parent_board_id") or "")
            board_id = _required_int(form.get("board_id"), "choose a board to update")
            services.update_board_taxonomy(
                board_id,
                board_kind=str(form.get("board_kind") or ""),
                parent_board_id=int(raw_parent_id) if raw_parent_id else None,
                sidebar_section=str(form.get("sidebar_section") or ""),
            )
            services.update_board_navigation(
                board_id,
                navigation_order=_required_int(
                    form.get("navigation_order"),
                    "choose a navigation order",
                ),
                show_in_navigation=form.get("show_in_navigation") == "on",
                sidebar_section=str(form.get("sidebar_section") or ""),
            )
        elif intent == "board_navigation":
            services.update_board_navigation(
                _required_int(form.get("board_id"), "choose a board to update"),
                navigation_order=_required_int(
                    form.get("navigation_order"),
                    "choose a navigation order",
                ),
                show_in_navigation=form.get("show_in_navigation") == "on",
                sidebar_section=str(form.get("sidebar_section") or ""),
            )
        elif intent == "sidebar_section":
            services.update_sidebar_section_config(
                str(form.get("section_key") or ""),
                label=str(form.get("label") or ""),
                description=str(form.get("description") or ""),
                sort_order=_required_int(
                    form.get("sort_order"),
                    "choose a sidebar section order",
                ),
                show_label=form.get("show_label") == "on",
            )
        elif intent == "post_style_policy":
            services.update_post_style_policy(
                enabled_post_profile_variants=_form_values(
                    form,
                    "enabled_post_profile_variants",
                ),
                enabled_post_accent_styles=_form_values(
                    form,
                    "enabled_post_accent_styles",
                ),
                enabled_post_border_styles=_form_values(
                    form,
                    "enabled_post_border_styles",
                ),
                enabled_post_title_styles=_form_values(
                    form,
                    "enabled_post_title_styles",
                ),
                enabled_post_densities=_form_values(
                    form,
                    "enabled_post_densities",
                ),
            )
        elif intent == "default_theme":
            services.update_default_theme(
                slug=str(form.get("theme_slug") or ""),
                name=str(form.get("theme_name") or ""),
                typography_display=str(form.get("theme_typography_display") or ""),
                typography_body=str(form.get("theme_typography_body") or ""),
                typography_mono=str(form.get("theme_typography_mono") or ""),
                radius=str(form.get("theme_radius") or ""),
                density=str(form.get("theme_density") or ""),
                texture=str(form.get("theme_texture") or ""),
                light=_theme_mode_values(form, "light"),
                dark=_theme_mode_values(form, "dark"),
            )
            redirect_to = "/studio#appearance-theme"
        elif intent == "community_media":
            services.update_community_media(
                community_mark_url=str(form.get("community_mark_url") or ""),
                community_mark_alt=str(form.get("community_mark_alt") or ""),
                world_hero_image_url=str(form.get("world_hero_image_url") or ""),
                world_hero_image_alt=str(form.get("world_hero_image_alt") or ""),
            )
            redirect_to = "/studio#appearance-media"
        elif intent == "material_status":
            services.update_material_production_state(
                str(form.get("material_slug") or ""),
                status=str(form.get("status") or ""),
                is_featured=form.get("is_featured") == "on",
            )
            redirect_to = "/studio#continuity-events"
        else:
            raw_group_id = str(form.get("identity_accent_facet_group_id") or "")
            facet_group_id = int(raw_group_id) if raw_group_id else None
            services.update_identity_accent_group(facet_group_id)
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except (LookupError, ValueError) as exc:
        return _render_studio(request, error=str(exc))
    return Redirect(redirect_to)


def _render_studio(request: Request, *, error: str | None = None) -> Page:
    services = get_services(request)
    studio = services.director_studio()
    return Page(
        "studio/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=services.viewer(),
        studio=studio,
        error=error,
        post_profile_variant_labels=POST_PROFILE_VARIANT_LABELS,
        post_accent_style_labels=POST_ACCENT_STYLE_LABELS,
        post_border_style_labels=POST_BORDER_STYLE_LABELS,
        post_title_style_labels=POST_TITLE_STYLE_LABELS,
        post_density_labels=POST_DENSITY_LABELS,
        board_kind_labels=BOARD_KIND_LABELS,
        sidebar_section_labels=BOARD_SIDEBAR_SECTION_LABELS,
        theme_mode_field_defs=THEME_MODE_FIELDS,
        theme_font_labels=FONT_STACK_LABELS,
        theme_radius_labels=RADIUS_LABELS,
        theme_density_labels=DENSITY_LABELS,
        theme_texture_labels=TEXTURE_LABELS,
    )


def _form_values(form: object, name: str) -> list[str]:
    get_list = getattr(form, "get_list", None)
    getlist = getattr(form, "getlist", None)
    if callable(get_list):
        return [str(value) for value in get_list(name)]
    if callable(getlist):
        return [str(value) for value in getlist(name)]
    raw = getattr(form, "get", lambda _name: None)(name)
    return [] if raw is None else [str(raw)]


def _required_int(raw: object, message: str) -> int:
    value = str(raw or "")
    if not value:
        raise ValueError(message)
    return int(value)


def _theme_mode_values(form: object, mode: str) -> dict[str, str]:
    return {
        key: str(getattr(form, "get", lambda _name: "")(f"theme_{mode}_{key}") or "")
        for key, _label in THEME_MODE_FIELDS
    }
