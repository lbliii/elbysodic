"""Director Studio hub."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.domain.boards import BOARD_KIND_LABELS, BOARD_SIDEBAR_SECTION_LABELS
from elbysodic.services.operations import OperationsInspectionConfig
from elbysodic.services.read_models import (
    POST_ACCENT_STYLE_LABELS,
    POST_BORDER_STYLE_LABELS,
    POST_DENSITY_LABELS,
    POST_PROFILE_VARIANT_LABELS,
    POST_TITLE_STYLE_LABELS,
    DirectorStudio,
)
from elbysodic.services.themes import (
    DENSITY_LABELS,
    FONT_STACK_LABELS,
    RADIUS_LABELS,
    TEXTURE_LABELS,
    THEME_MODE_FIELDS,
)
from elbysodic.web.state import get_services, get_web_security_config


@dataclass(frozen=True, slots=True)
class StudioCockpitLane:
    kicker: str
    title: str
    summary: str
    href: str
    cta: str
    count: int
    items: tuple[str, ...] = ()
    variant: str = "attention"


@dataclass(frozen=True, slots=True)
class StudioRoomCard:
    key: str
    kicker: str
    title: str
    summary: str
    href: str
    cta: str
    count: int
    items: tuple[str, ...] = ()
    variant: str = "info"


def get(request: Request) -> Page | Redirect:
    return render_studio_room(request, "overview")


async def post(request: Request) -> Page | Redirect:
    return await handle_studio_post(request, _studio_room_for_path(request.url))


async def handle_studio_post(request: Request, room: str) -> Page | Redirect:
    services = get_services(request)
    form = await request.form()
    intent = str(form.get("intent") or "identity_accent")
    redirect_to = _studio_room_href(room)
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
            redirect_to = "/studio/structure#board-taxonomy"
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
            redirect_to = "/studio/structure#navigation-composer"
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
            redirect_to = "/studio/structure#navigation-composer"
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
            redirect_to = "/studio/appearance#identity-appearance-style"
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
            redirect_to = "/studio/appearance#appearance-theme"
        elif intent == "community_media":
            services.update_community_media(
                community_mark_url=str(form.get("community_mark_url") or ""),
                community_mark_alt=str(form.get("community_mark_alt") or ""),
                world_hero_image_url=str(form.get("world_hero_image_url") or ""),
                world_hero_image_alt=str(form.get("world_hero_image_alt") or ""),
                world_hero_treatment=str(form.get("world_hero_treatment") or ""),
                world_hero_focal_point=str(form.get("world_hero_focal_point") or ""),
                world_hero_overlay=str(form.get("world_hero_overlay") or ""),
                world_hero_height=str(form.get("world_hero_height") or ""),
            )
            redirect_to = "/studio/appearance#appearance-media"
        elif intent == "material_status":
            services.update_material_production_state(
                str(form.get("material_slug") or ""),
                status=str(form.get("status") or ""),
                is_featured=form.get("is_featured") == "on",
            )
            redirect_to = "/studio/content#continuity-events"
        elif intent == "gateway_curation":
            services.update_gateway_curation(
                scene_hub_target_ids=_ordered_targets(
                    form,
                    "scene_hub_target_id",
                    "scene_hub_position_",
                ),
                wanted_hook_target_ids=_ordered_targets(
                    form,
                    "wanted_hook_target_id",
                    "wanted_hook_position_",
                ),
                guidebook_material_target_ids=_ordered_targets(
                    form,
                    "guidebook_material_target_id",
                    "guidebook_material_position_",
                ),
            )
            redirect_to = "/studio/structure#gateway-curation"
        else:
            raw_group_id = str(form.get("identity_accent_facet_group_id") or "")
            facet_group_id = int(raw_group_id) if raw_group_id else None
            services.update_identity_accent_group(facet_group_id)
            redirect_to = "/studio/appearance#identity-appearance"
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except (LookupError, ValueError) as exc:
        return render_studio_room(request, room, error=str(exc))
    return Redirect(redirect_to)


def render_studio_room(
    request: Request,
    room: str,
    *,
    error: str | None = None,
) -> Page | Redirect:
    services = get_services(request)
    studio = services.director_studio()
    if error is None and studio.can_manage and _is_empty_configured_realm(studio):
        return Redirect("/studio/launch")
    cockpit_lanes = _studio_cockpit_lanes(studio)
    studio_rooms = _studio_room_cards(studio, cockpit_lanes)
    shape_hub_rooms = tuple(
        item for item in studio_rooms if item.key in {"intake", "appearance", "content"}
    )
    operations = None
    if room == "overview":
        security = get_web_security_config()
        operations = services.director_operations(
            inspection_config=OperationsInspectionConfig(
                environment=security.env,
                secure_cookies=security.secure_cookies,
            )
        )
    return Page.mounted(
        "studio/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        studio=studio,
        studio_room=room,
        studio_rooms=studio_rooms,
        shape_hub_rooms=shape_hub_rooms,
        operations=operations,
        current_studio_room=next(
            (item for item in studio_rooms if item.key == room),
            None,
        ),
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
        cockpit_lanes=cockpit_lanes,
    )


def _is_empty_configured_realm(studio: DirectorStudio) -> bool:
    return not studio.board_taxonomy and not studio.materials


def _studio_room_for_path(current_path: object) -> str:
    path = str(current_path or "").split("?", 1)[0].split("#", 1)[0].rstrip("/")
    if path.endswith("/studio/appearance"):
        return "appearance"
    if path.endswith("/studio/structure"):
        return "structure"
    if path.endswith("/studio/content"):
        return "content"
    return "overview"


def _studio_room_href(room: str) -> str:
    if room in {"appearance", "structure", "content"}:
        return f"/studio/{room}"
    return "/studio"


def _form_values(form: object, name: str) -> list[str]:
    get_list = getattr(form, "get_list", None)
    getlist = getattr(form, "getlist", None)
    if callable(get_list):
        return [str(value) for value in get_list(name)]
    if callable(getlist):
        return [str(value) for value in getlist(name)]
    raw = getattr(form, "get", lambda _name: None)(name)
    return [] if raw is None else [str(raw)]


def _ordered_targets(form: object, field_name: str, position_prefix: str) -> list[int]:
    selected_ids = {int(value) for value in _form_values(form, field_name) if str(value)}
    get_value = getattr(form, "get", lambda _name: "")

    def position_for(target_id: int) -> tuple[int, int]:
        raw_position = str(get_value(f"{position_prefix}{target_id}") or "")
        try:
            position = int(raw_position)
        except ValueError:
            raise ValueError("spotlight order must be a positive number") from None
        if position < 1:
            raise ValueError("spotlight order must be a positive number")
        return (position, target_id)

    return sorted(selected_ids, key=position_for)


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


def _studio_cockpit_lanes(studio: DirectorStudio) -> list[StudioCockpitLane]:
    lanes: list[StudioCockpitLane] = []
    if studio.review_queue_count:
        lanes.append(
            StudioCockpitLane(
                "Applications",
                "Review queue",
                "Submitted faces waiting for director movement.",
                "/applications",
                "Review applications",
                studio.review_queue_count,
                tuple(item.character.name for item in studio.applications.review_queue[:4]),
            )
        )
    if studio.claims.reserved_count:
        lanes.append(
            StudioCockpitLane(
                "Claims",
                "Reserved claims",
                "Claims and reserves directors may need to honor before accepting new faces.",
                "/claims?status=reserved",
                "Open reserved claims",
                studio.claims.reserved_count,
                tuple(studio.claims.claim_type_names[:4]),
            )
        )
    if studio.draft_materials:
        lanes.append(
            StudioCockpitLane(
                "Materials",
                "Draft materials",
                "Guidebook, event, and canon pages still waiting on director publication.",
                "/studio/content#continuity-events",
                "Review drafts",
                len(studio.draft_materials),
                tuple(item.material.title for item in studio.draft_materials[:4]),
            )
        )
    if studio.navigation_warnings:
        lanes.append(
            StudioCockpitLane(
                "Navigation",
                "Shell health",
                "Sidebar, board map, and route-shape notes that need review.",
                "/studio/structure#navigation",
                "Review navigation",
                len(studio.navigation_warnings),
                tuple(warning.title for warning in studio.navigation_warnings[:4]),
                "warning",
            )
        )
    if studio.theme_warnings:
        lanes.append(
            StudioCockpitLane(
                "Appearance",
                "Theme health",
                "Readability warnings in the realm's light or dark palette.",
                "/studio/appearance#appearance-theme",
                "Review theme",
                len(studio.theme_warnings),
                tuple(warning.title for warning in studio.theme_warnings[:4]),
                "warning",
            )
        )
    missing_launch_items = [
        item for item in studio.launch_readiness.items if item.is_required and not item.is_complete
    ]
    if missing_launch_items:
        lanes.append(
            StudioCockpitLane(
                "Launch",
                "Opening checklist",
                "Required opening lanes still backstage before invite-only opening.",
                "/studio/launch",
                "Open launch room",
                len(missing_launch_items),
                tuple(f"{item.label} - {item.status_label}" for item in missing_launch_items[:4]),
            )
        )
    return lanes


def _studio_room_cards(
    studio: DirectorStudio,
    cockpit_lanes: list[StudioCockpitLane],
) -> tuple[StudioRoomCard, ...]:
    missing_launch_items = [
        item for item in studio.launch_readiness.items if item.is_required and not item.is_complete
    ]
    structure_count = (
        studio.navigation_attention_count
        + studio.navigation_warning_count
        + studio.navigation_note_count
    )
    content_count = len(studio.draft_materials) + len(studio.events)
    return (
        StudioRoomCard(
            "operations",
            "Today",
            "Operations",
            "A daily director desk for reviews, claim conflicts, reserves, hooks, and health signals.",
            "/studio",
            "Open today",
            len(cockpit_lanes),
            tuple(lane.title for lane in cockpit_lanes[:4]) or ("No urgent lanes right now.",),
            "attention" if cockpit_lanes else "success",
        ),
        StudioRoomCard(
            "launch",
            "Opening",
            "Launch",
            "Realm opening checklist, access requests, invitations, and first-writer gates.",
            "/studio/launch",
            "Open launch room",
            len(missing_launch_items),
            tuple(item.label for item in missing_launch_items[:4])
            or ("Opening requirements are currently satisfied.",),
            "warning" if missing_launch_items else "success",
        ),
        StudioRoomCard(
            "discovery",
            "Public presence",
            "Discovery profile",
            "Network listing, premise fit, pace expectations, roster posture, and public realm signals.",
            "/studio/discovery",
            "Edit discovery",
            studio.open_wanted_count,
            tuple(item.wanted_ad.title for item in studio.open_wanted_ads[:4])
            or ("No open wanted hooks are advertising right now.",),
        ),
        StudioRoomCard(
            "structure",
            "Realm shape",
            "Structure",
            "Audit the home spotlight, board map, sidebar language, and navigation health after object-local edits.",
            "/studio/structure",
            "Open audit",
            structure_count,
            tuple(warning.title for warning in studio.navigation_warnings[:4])
            or ("Navigation is coherent right now.",),
            "warning" if structure_count else "success",
        ),
        StudioRoomCard(
            "intake",
            "Applications",
            "Intake",
            "Application fields, claims, reserves, and director-defined face requirements.",
            "/studio/intake",
            "Edit intake",
            len(studio.claims.groups),
            tuple(studio.claims.claim_type_names[:4]) or ("No claim types configured yet.",),
        ),
        StudioRoomCard(
            "appearance",
            "Skinning",
            "Appearance",
            "Theme tokens, realm media, identity accents, and post style vocabulary.",
            "/studio/appearance",
            "Open appearance",
            len(studio.theme_warnings),
            tuple(warning.title for warning in studio.theme_warnings[:4])
            or ("Theme contrast is healthy for checked surfaces.",),
            "warning" if studio.theme_warnings else "success",
        ),
        StudioRoomCard(
            "content",
            "Story materials",
            "Content",
            "Guidebook materials, the current event, wanted hooks, and location coverage.",
            "/studio/content",
            "Open content",
            content_count,
            tuple(item.material.title for item in studio.draft_materials[:4])
            or tuple(studio.event_titles[:4])
            or ("No guidebook drafts are waiting.",),
        ),
    )
