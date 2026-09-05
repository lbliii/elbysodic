"""Service boundary for director-authored Program Blueprint previews."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable
from contextlib import AbstractContextManager
from dataclasses import asdict, dataclass, replace
from typing import Literal, Protocol

from elbysodic.blueprints import (
    BlueprintApplyMode,
    BlueprintDiffRow,
    ProgramBlueprint,
    ProgramBlueprintPreview,
    blueprint_theme_tokens,
    preview_program_blueprint_yaml,
)
from elbysodic.domain import (
    Board,
    Character,
    Community,
    CommunityMembership,
    CommunityTheme,
    Material,
    Role,
    WantedAd,
)
from elbysodic.services import policies
from elbysodic.services.read_models import ForumView


class BlueprintPlanRepository(Protocol):
    def transaction(self) -> AbstractContextManager[None]: ...

    def get_community(self, community_id: int) -> Community: ...

    def get_community_by_slug(self, slug: str) -> Community: ...

    def get_membership(self, community_id: int, membership_id: int) -> CommunityMembership: ...

    def get_role(self, community_id: int, role_id: int) -> Role: ...

    def get_role_by_slug(self, community_id: int, slug: str) -> Role: ...

    def get_character_by_slug(self, community_id: int, slug: str) -> Character: ...

    def get_board_by_slug(self, community_id: int, slug: str) -> Board: ...

    def get_material_by_slug(self, community_id: int, slug: str) -> Material: ...

    def get_wanted_ad_by_slug(self, community_id: int, slug: str) -> WantedAd: ...

    def get_theme_by_slug(self, community_id: int, slug: str) -> CommunityTheme: ...

    def update_community_name_and_slug(
        self, community_id: int, *, slug: str, name: str
    ) -> Community: ...

    def create_role(
        self,
        community_id: int,
        slug: str,
        name: str,
        *,
        is_admin: bool = False,
        capabilities: Iterable[str] | None = None,
    ) -> Role: ...

    def update_role(
        self,
        community_id: int,
        role_id: int,
        *,
        name: str,
        is_admin: bool,
        capabilities: Iterable[str],
    ) -> Role: ...

    def create_character(
        self,
        community_id: int,
        membership_id: int,
        slug: str,
        name: str,
        avatar_url: str | None = None,
        poster_url: str | None = None,
        poster_alt: str = "",
        tagline: str = "",
        accent_color: str = "",
        summary: str = "",
        post_profile_variant: str = "bio",
        post_accent_style: str = "soft",
        post_border_style: str = "hairline",
        post_title_style: str = "standard",
        post_density: str = "calm",
        *,
        application_status: str = "accepted",
        make_default: bool = False,
    ) -> Character: ...

    def update_character(
        self,
        community_id: int,
        character_id: int,
        *,
        slug: str,
        name: str,
        avatar_url: str | None,
        poster_url: str | None = None,
        poster_alt: str = "",
        tagline: str = "",
        accent_color: str = "",
        summary: str = "",
        post_profile_variant: str = "bio",
        post_accent_style: str = "soft",
        post_border_style: str = "hairline",
        post_title_style: str = "standard",
        post_density: str = "calm",
    ) -> Character: ...

    def set_default_character(
        self, community_id: int, membership_id: int, character_id: int
    ) -> CommunityMembership: ...

    def create_board(
        self,
        community_id: int,
        slug: str,
        name: str,
        description: str = "",
        *,
        parent_board_id: int | None = None,
        board_kind: str = "location",
        sidebar_section: str | None = None,
        tagline: str = "",
        image_url: str | None = None,
        image_alt: str = "",
        image_treatment: str = "poster",
        image_focal_point: str = "center",
        image_overlay: str = "medium",
        sort_order: int = 0,
        navigation_order: int | None = None,
        show_in_navigation: bool = True,
        is_private: bool = False,
    ) -> Board: ...

    def update_board(
        self,
        community_id: int,
        board_id: int,
        *,
        name: str,
        description: str,
        sort_order: int,
        parent_board_id: int | None = None,
        board_kind: str = "location",
        sidebar_section: str | None = None,
        tagline: str = "",
        image_url: str | None = None,
        image_alt: str = "",
        image_treatment: str | None = None,
        image_focal_point: str | None = None,
        image_overlay: str | None = None,
        is_private: bool = False,
        navigation_order: int | None = None,
        show_in_navigation: bool | None = None,
    ) -> Board: ...

    def create_material(
        self,
        community_id: int,
        slug: str,
        title: str,
        *,
        material_type: str = "guide",
        presentation_variant: str = "chapter",
        summary: str = "",
        body: str = "",
        status: str = "published",
        sort_order: int = 0,
        is_featured: bool = False,
    ) -> Material: ...

    def update_material(
        self,
        community_id: int,
        material_id: int,
        *,
        title: str,
        material_type: str,
        presentation_variant: str | None = None,
        summary: str,
        body: str,
        status: str = "published",
        sort_order: int = 0,
        is_featured: bool = False,
    ) -> Material: ...

    def create_wanted_ad(
        self,
        community_id: int,
        creator_membership_id: int,
        slug: str,
        title: str,
        *,
        creator_character_id: int | None = None,
        related_material_id: int | None = None,
        wanted_type: str = "plot_role",
        summary: str = "",
        body: str = "",
        status: str = "open",
    ) -> WantedAd: ...

    def update_wanted_ad(
        self,
        community_id: int,
        wanted_ad_id: int,
        *,
        title: str,
        wanted_type: str,
        summary: str,
        body: str,
        related_material_id: int | None,
    ) -> WantedAd: ...

    def upsert_default_theme(
        self,
        community_id: int,
        *,
        slug: str,
        name: str,
        tokens_json: str,
    ) -> CommunityTheme: ...

    def reserve_command_submission(
        self,
        community_id: int,
        membership_id: int,
        *,
        command_key: str,
        token: str,
    ) -> bool: ...

    def get_command_submission(
        self,
        community_id: int,
        membership_id: int,
        *,
        command_key: str,
        token: str,
    ) -> object | None: ...

    def complete_command_submission(
        self,
        community_id: int,
        membership_id: int,
        *,
        command_key: str,
        token: str,
        result_path: str,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class BlueprintApplyReadiness:
    can_check_gate: bool
    items: tuple[str, ...]


def preview_program_blueprint(
    repo: BlueprintPlanRepository,
    viewer: ForumView,
    source: str,
) -> ProgramBlueprintPreview:
    viewer = _current_blueprint_viewer(repo, viewer)
    if not policies.can_manage_world(viewer.membership, viewer.role):
        raise PermissionError(
            f"membership {viewer.membership.id} cannot preview program blueprints"
        )
    preview = preview_program_blueprint_yaml(source)
    if not preview.is_valid or preview.blueprint is None:
        return preview
    diff_rows = plan_program_blueprint_hydration(
        repo,
        preview.blueprint,
        target_community=viewer.community,
    )
    return replace(
        preview,
        diff_rows=diff_rows,
        preview_fingerprint=_preview_fingerprint(
            source,
            diff_rows,
            _blueprint_live_records(repo, viewer, preview.blueprint),
        ),
    )


def program_blueprint_apply_readiness(
    preview: ProgramBlueprintPreview | None,
) -> BlueprintApplyReadiness:
    if preview is None:
        return BlueprintApplyReadiness(
            can_check_gate=False,
            items=("Preview a valid Program Blueprint before checking the apply gate.",),
        )
    if not preview.is_valid:
        return BlueprintApplyReadiness(
            can_check_gate=False,
            items=("Resolve validation notes before checking the apply gate.",),
        )
    action_counts = _diff_action_counts(preview.diff_rows)
    items = [
        _diff_action_readiness_summary(action_counts),
        _collision_readiness_summary(preview.diff_rows),
        "Create only rejects live content collisions; skip existing preserves them.",
        "Explicit update replaces only current-realm rows and same-writer faces or wanted hooks.",
        "Starter faces and wanted hooks are owned by the importing director membership.",
        "Apply uses one rollback-tested transaction and a fingerprint-scoped idempotency key.",
    ]
    return BlueprintApplyReadiness(
        can_check_gate=bool(preview.preview_fingerprint)
        and not any(row.action == "blocked" for row in preview.diff_rows),
        items=tuple(items),
    )


def apply_program_blueprint_preview(
    repo: BlueprintPlanRepository,
    viewer: ForumView,
    source: str,
    accepted_fingerprint: str,
    *,
    mode: BlueprintApplyMode = "create_only",
    on_applied: Callable[[], None] | None = None,
) -> ProgramBlueprintPreview:
    preview = preview_program_blueprint(repo, viewer, source)
    if not preview.is_valid:
        raise ValueError("Preview a valid Program Blueprint before applying.")
    if not accepted_fingerprint:
        raise ValueError("Program Blueprint preview changed; preview again before applying.")
    if mode == "dry_run":
        if accepted_fingerprint != preview.preview_fingerprint:
            raise ValueError("Program Blueprint preview changed; preview again before applying.")
        return replace(preview, apply_mode=mode)
    if mode not in {"create_only", "skip_existing", "explicit_update"}:
        raise ValueError("Choose create only, skip existing, explicit update, or dry run.")
    blueprint = preview.blueprint
    if blueprint is None:
        raise ValueError("Preview a valid Program Blueprint before applying.")
    if blueprint.slug != viewer.community.slug:
        raise ValueError("Program Blueprint must target the current realm before apply.")
    _validate_blueprint_apply_target(preview, blueprint, viewer)
    command_token = f"{accepted_fingerprint}:{mode}"
    with repo.transaction():
        current_viewer = _current_blueprint_viewer(repo, viewer)
        if (
            repo.get_command_submission(
                current_viewer.community.id,
                current_viewer.membership.id,
                command_key="program_blueprint_apply",
                token=command_token,
            )
            is not None
        ):
            raise ValueError(f"This Program Blueprint preview was already applied in {mode} mode.")
        current_preview = preview_program_blueprint(repo, current_viewer, source)
        if accepted_fingerprint != current_preview.preview_fingerprint:
            raise ValueError("Program Blueprint preview changed; preview again before applying.")
        current_blueprint = current_preview.blueprint
        if current_blueprint is None:
            raise ValueError("Preview a valid Program Blueprint before applying.")
        _validate_blueprint_apply_target(current_preview, current_blueprint, current_viewer)
        _validate_create_only_collisions(
            repo,
            current_viewer,
            current_blueprint,
            current_preview,
            mode,
        )
        if not repo.reserve_command_submission(
            current_viewer.community.id,
            current_viewer.membership.id,
            command_key="program_blueprint_apply",
            token=command_token,
        ):
            raise ValueError(f"This Program Blueprint preview was already applied in {mode} mode.")
        _hydrate_program_blueprint(repo, current_viewer, current_blueprint, mode)
        if on_applied is not None:
            on_applied()
        repo.complete_command_submission(
            current_viewer.community.id,
            current_viewer.membership.id,
            command_key="program_blueprint_apply",
            token=command_token,
            result_path="/studio/intake?blueprint=applied",
        )
    return replace(current_preview, apply_mode=mode, applied=True)


def _validate_blueprint_apply_target(
    preview: ProgramBlueprintPreview,
    blueprint: ProgramBlueprint,
    viewer: ForumView,
) -> None:
    if blueprint.slug != viewer.community.slug:
        raise ValueError("Program Blueprint must target the current realm before apply.")
    blocked = [row for row in preview.diff_rows if row.action == "blocked"]
    if blocked:
        raise ValueError(blocked[0].detail)


def _validate_create_only_collisions(
    repo: BlueprintPlanRepository,
    viewer: ForumView,
    blueprint: ProgramBlueprint,
    preview: ProgramBlueprintPreview,
    mode: BlueprintApplyMode,
) -> None:
    if mode != "create_only":
        return
    community = repo.get_community(viewer.community.id)
    if community.name != blueprint.name:
        raise ValueError("Create-only mode cannot replace the current realm name.")
    try:
        role = repo.get_role_by_slug(community.id, blueprint.role_slug)
    except LookupError:
        role = None
    if role is not None:
        expected_capabilities = blueprint.role_capabilities
        if role.name != blueprint.role_name or role.capabilities != expected_capabilities:
            raise ValueError("Create-only mode cannot replace the existing Blueprint role.")
    collisions = [
        row
        for row in preview.diff_rows
        if row.section not in {"program", "role", "appearance"} and row.action in {"update", "skip"}
    ]
    if collisions:
        collision = collisions[0]
        raise ValueError(f"Create-only mode found existing {collision.section}: {collision.label}.")


def _hydrate_program_blueprint(
    repo: BlueprintPlanRepository,
    viewer: ForumView,
    blueprint: ProgramBlueprint,
    mode: BlueprintApplyMode,
) -> None:
    community = repo.get_community(viewer.community.id)
    if mode == "explicit_update" and community.name != blueprint.name:
        community = repo.update_community_name_and_slug(
            community.id,
            slug=blueprint.slug,
            name=blueprint.name,
        )
    expected_capabilities = blueprint.role_capabilities
    try:
        role = repo.get_role_by_slug(community.id, blueprint.role_slug)
    except LookupError:
        repo.create_role(
            community.id,
            blueprint.role_slug,
            blueprint.role_name,
            is_admin=bool(expected_capabilities),
            capabilities=expected_capabilities,
        )
    else:
        if mode == "explicit_update":
            if role.id == viewer.role.id and role.capabilities != expected_capabilities:
                raise ValueError(
                    "Blueprint apply cannot change the importing director's own capabilities."
                )
            repo.update_role(
                community.id,
                role.id,
                name=blueprint.role_name,
                is_admin=bool(expected_capabilities),
                capabilities=expected_capabilities,
            )

    style = blueprint.appearance.post_style if blueprint.appearance is not None else None
    first_owned_character_id: int | None = None
    for character_seed in blueprint.characters:
        try:
            character = repo.get_character_by_slug(community.id, character_seed.slug)
        except LookupError:
            character = repo.create_character(
                community.id,
                viewer.membership.id,
                character_seed.slug,
                character_seed.name,
                summary=character_seed.summary,
                tagline=character_seed.tagline,
                post_profile_variant=style.profile_variant if style is not None else "bio",
                post_accent_style=style.accent_style if style is not None else "soft",
                post_border_style=style.border_style if style is not None else "hairline",
                post_title_style=style.title_style if style is not None else "standard",
                post_density=style.density if style is not None else "calm",
            )
        else:
            if mode == "explicit_update":
                if character.membership_id != viewer.membership.id:
                    raise ValueError(
                        f"Existing face is owned by another writer: {character_seed.name}."
                    )
                character = repo.update_character(
                    community.id,
                    character.id,
                    slug=character.slug,
                    name=character_seed.name,
                    avatar_url=character.avatar_url,
                    poster_url=character.poster_url,
                    poster_alt=character.poster_alt,
                    tagline=character_seed.tagline,
                    accent_color=character.accent_color,
                    summary=character_seed.summary,
                    post_profile_variant=(
                        style.profile_variant
                        if style is not None
                        else character.post_profile_variant
                    ),
                    post_accent_style=(
                        style.accent_style if style is not None else character.post_accent_style
                    ),
                    post_border_style=(
                        style.border_style if style is not None else character.post_border_style
                    ),
                    post_title_style=(
                        style.title_style if style is not None else character.post_title_style
                    ),
                    post_density=style.density if style is not None else character.post_density,
                )
        if first_owned_character_id is None and character.membership_id == viewer.membership.id:
            first_owned_character_id = character.id
    current_membership = repo.get_membership(community.id, viewer.membership.id)
    if current_membership.default_character_id is None and first_owned_character_id is not None:
        repo.set_default_character(
            community.id,
            current_membership.id,
            first_owned_character_id,
        )

    for index, board_seed in enumerate(blueprint.boards, start=1):
        try:
            board = repo.get_board_by_slug(community.id, board_seed.slug)
        except LookupError:
            repo.create_board(
                community.id,
                board_seed.slug,
                board_seed.name,
                board_seed.description,
                board_kind=board_seed.board_kind,
                tagline=board_seed.tagline,
                image_url=board_seed.image_url or None,
                image_alt=board_seed.image_alt,
                image_treatment=board_seed.image_treatment,
                image_focal_point=board_seed.image_focal_point,
                image_overlay=board_seed.image_overlay,
                sort_order=index * 10,
            )
        else:
            if mode == "explicit_update":
                repo.update_board(
                    community.id,
                    board.id,
                    name=board_seed.name,
                    description=board_seed.description,
                    sort_order=board.sort_order,
                    parent_board_id=board.parent_board_id,
                    board_kind=board_seed.board_kind,
                    sidebar_section=board.sidebar_section,
                    tagline=board_seed.tagline,
                    image_url=board_seed.image_url or None,
                    image_alt=board_seed.image_alt,
                    image_treatment=board_seed.image_treatment,
                    image_focal_point=board_seed.image_focal_point,
                    image_overlay=board_seed.image_overlay,
                    is_private=board.is_private,
                    navigation_order=board.navigation_order,
                    show_in_navigation=board.show_in_navigation,
                )

    material_variants = {
        item.material_type: item.variant
        for item in (
            blueprint.appearance.material_variants if blueprint.appearance is not None else ()
        )
    }
    materials_by_slug: dict[str, Material] = {}
    for index, material_seed in enumerate(blueprint.materials, start=1):
        variant = material_variants.get(material_seed.material_type, "chapter")
        try:
            material = repo.get_material_by_slug(community.id, material_seed.slug)
        except LookupError:
            material = repo.create_material(
                community.id,
                material_seed.slug,
                material_seed.title,
                material_type=material_seed.material_type,
                presentation_variant=variant,
                summary=material_seed.summary,
                body=material_seed.body,
                sort_order=index * 10,
                is_featured=index == 1,
            )
        else:
            if mode == "explicit_update":
                material = repo.update_material(
                    community.id,
                    material.id,
                    title=material_seed.title,
                    material_type=material_seed.material_type,
                    presentation_variant=variant,
                    summary=material_seed.summary,
                    body=material_seed.body,
                    status=material.status,
                    sort_order=material.sort_order,
                    is_featured=material.is_featured,
                )
        materials_by_slug[material_seed.slug] = material

    for wanted_seed in blueprint.wanted:
        related_material_id = (
            materials_by_slug[wanted_seed.related_material_slug].id
            if wanted_seed.related_material_slug
            else None
        )
        try:
            wanted = repo.get_wanted_ad_by_slug(community.id, wanted_seed.slug)
        except LookupError:
            repo.create_wanted_ad(
                community.id,
                viewer.membership.id,
                wanted_seed.slug,
                wanted_seed.title,
                creator_character_id=first_owned_character_id,
                related_material_id=related_material_id,
                wanted_type=wanted_seed.wanted_type,
                summary=wanted_seed.summary,
                body=wanted_seed.body,
            )
        else:
            if mode == "explicit_update":
                if wanted.creator_membership_id != viewer.membership.id:
                    raise ValueError(
                        f"Existing wanted hook is owned by another writer: {wanted_seed.title}."
                    )
                repo.update_wanted_ad(
                    community.id,
                    wanted.id,
                    title=wanted_seed.title,
                    wanted_type=wanted_seed.wanted_type,
                    summary=wanted_seed.summary,
                    body=wanted_seed.body,
                    related_material_id=related_material_id,
                )

    if blueprint.theme is not None:
        try:
            repo.get_theme_by_slug(community.id, blueprint.theme.slug)
        except LookupError:
            should_apply_theme = True
        else:
            should_apply_theme = mode == "explicit_update"
        if should_apply_theme:
            repo.upsert_default_theme(
                community.id,
                slug=blueprint.theme.slug,
                name=blueprint.theme.name,
                tokens_json=json.dumps(
                    blueprint_theme_tokens(blueprint.theme),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            )


def plan_program_blueprint_hydration(
    repo: BlueprintPlanRepository,
    blueprint: ProgramBlueprint,
    *,
    target_community: Community | None = None,
) -> tuple[BlueprintDiffRow, ...]:
    rows: list[BlueprintDiffRow] = []
    if target_community is not None and blueprint.slug != target_community.slug:
        return (
            BlueprintDiffRow(
                "program",
                blueprint.slug,
                blueprint.name,
                "blocked",
                "Blueprint program slug does not match the current realm.",
            ),
        )
    try:
        community = repo.get_community_by_slug(blueprint.slug)
    except LookupError:
        community = None
    rows.append(
        BlueprintDiffRow(
            "program",
            blueprint.slug,
            blueprint.name,
            "update" if community is not None else "create",
            (
                "Existing realm matched by slug; program identity would be reviewed for update."
                if community is not None
                else "New realm would be created from the blueprint program."
            ),
        )
    )
    if community is None:
        rows.extend(_new_program_rows(blueprint))
        return tuple(rows)
    community_id = community.id
    rows.append(
        _row_for_existing(
            section="role",
            slug=blueprint.role_slug,
            label=blueprint.role_name,
            exists=lambda: repo.get_role_by_slug(community_id, blueprint.role_slug),
            update_detail="Existing director role would be reviewed for update.",
            create_detail="Director role would be created.",
        )
    )
    rows.extend(
        _row_for_existing(
            section="face",
            slug=character.slug,
            label=character.name,
            exists=lambda character=character: repo.get_character_by_slug(
                community_id,
                character.slug,
            ),
            existing_action="skip",
            update_detail="Existing starter face would be skipped until explicit update mode exists.",
            create_detail="Starter face would be created for the importing director.",
        )
        for character in blueprint.characters
    )
    rows.extend(
        _row_for_existing(
            section="scene hub",
            slug=board.slug,
            label=board.name,
            exists=lambda board=board: repo.get_board_by_slug(community_id, board.slug),
            update_detail="Existing scene hub would be reviewed for update.",
            create_detail="Scene hub would be created.",
        )
        for board in blueprint.boards
    )
    rows.extend(
        _row_for_existing(
            section="material",
            slug=material.slug,
            label=material.title,
            exists=lambda material=material: repo.get_material_by_slug(
                community_id,
                material.slug,
            ),
            update_detail="Existing material would be reviewed for update.",
            create_detail="Material would be created.",
        )
        for material in blueprint.materials
    )
    rows.extend(
        _row_for_existing(
            section="wanted hook",
            slug=wanted.slug,
            label=wanted.title,
            exists=lambda wanted=wanted: repo.get_wanted_ad_by_slug(community_id, wanted.slug),
            existing_action="skip",
            update_detail="Existing wanted hook would be skipped until explicit update mode exists.",
            create_detail="Wanted hook would be created for the importing director.",
        )
        for wanted in blueprint.wanted
    )
    theme = blueprint.theme
    if theme is not None:
        rows.append(
            _row_for_existing(
                section="theme",
                slug=theme.slug,
                label=theme.name,
                exists=lambda: repo.get_theme_by_slug(community_id, theme.slug),
                update_detail="Existing theme tokens would be reviewed for update.",
                create_detail="Theme tokens would be created and selected as default.",
            )
        )
    if blueprint.appearance is not None:
        rows.append(
            BlueprintDiffRow(
                "appearance",
                blueprint.slug,
                "Appearance settings",
                "update",
                "Community appearance policy would be reviewed for update.",
            )
        )
    return tuple(rows)


def _new_program_rows(blueprint: ProgramBlueprint) -> tuple[BlueprintDiffRow, ...]:
    rows = [
        BlueprintDiffRow(
            "role",
            blueprint.role_slug,
            blueprint.role_name,
            "create",
            "Director role would be created.",
        ),
        *(
            BlueprintDiffRow(
                "face",
                character.slug,
                character.name,
                "create",
                "Starter face would be created for the importing director.",
            )
            for character in blueprint.characters
        ),
        *(
            BlueprintDiffRow(
                "scene hub", board.slug, board.name, "create", "Scene hub would be created."
            )
            for board in blueprint.boards
        ),
        *(
            BlueprintDiffRow(
                "material", material.slug, material.title, "create", "Material would be created."
            )
            for material in blueprint.materials
        ),
        *(
            BlueprintDiffRow(
                "wanted hook",
                wanted.slug,
                wanted.title,
                "create",
                "Wanted hook would be created for the importing director.",
            )
            for wanted in blueprint.wanted
        ),
    ]
    if blueprint.theme is not None:
        rows.append(
            BlueprintDiffRow(
                "theme",
                blueprint.theme.slug,
                blueprint.theme.name,
                "create",
                "Theme tokens would be created and selected as default.",
            )
        )
    if blueprint.appearance is not None:
        rows.append(
            BlueprintDiffRow(
                "appearance",
                blueprint.slug,
                "Appearance settings",
                "create",
                "Community appearance policy would be created.",
            )
        )
    return tuple(rows)


def _row_for_existing(
    *,
    section: str,
    slug: str,
    label: str,
    exists: Callable[[], object],
    update_detail: str,
    create_detail: str,
    existing_action: Literal["update", "skip"] = "update",
) -> BlueprintDiffRow:
    try:
        exists()
    except LookupError:
        return BlueprintDiffRow(section, slug, label, "create", create_detail)
    return BlueprintDiffRow(section, slug, label, existing_action, update_detail)


type BlueprintLiveRecord = (
    Community
    | CommunityMembership
    | Role
    | Character
    | Board
    | Material
    | WantedAd
    | CommunityTheme
)


def _current_blueprint_viewer(
    repo: BlueprintPlanRepository,
    viewer: ForumView,
) -> ForumView:
    community = repo.get_community(viewer.community.id)
    membership = repo.get_membership(community.id, viewer.membership.id)
    role = repo.get_role(community.id, membership.role_id)
    return replace(viewer, community=community, membership=membership, role=role)


def _blueprint_live_records(
    repo: BlueprintPlanRepository,
    viewer: ForumView,
    blueprint: ProgramBlueprint,
) -> tuple[tuple[str, str, BlueprintLiveRecord], ...]:
    community_id = viewer.community.id
    records: list[tuple[str, str, BlueprintLiveRecord]] = [
        ("program", blueprint.slug, viewer.community),
        ("membership", str(viewer.membership.id), viewer.membership),
        ("viewer role", str(viewer.role.id), viewer.role),
    ]

    def add_existing(
        section: str,
        slug: str,
        load: Callable[[], BlueprintLiveRecord],
    ) -> None:
        try:
            record = load()
        except LookupError:
            return
        records.append((section, slug, record))

    add_existing(
        "role",
        blueprint.role_slug,
        lambda: repo.get_role_by_slug(community_id, blueprint.role_slug),
    )
    for character in blueprint.characters:
        add_existing(
            "face",
            character.slug,
            lambda character=character: repo.get_character_by_slug(
                community_id,
                character.slug,
            ),
        )
    for board in blueprint.boards:
        add_existing(
            "scene hub",
            board.slug,
            lambda board=board: repo.get_board_by_slug(community_id, board.slug),
        )
    for material in blueprint.materials:
        add_existing(
            "material",
            material.slug,
            lambda material=material: repo.get_material_by_slug(
                community_id,
                material.slug,
            ),
        )
    for wanted in blueprint.wanted:
        add_existing(
            "wanted hook",
            wanted.slug,
            lambda wanted=wanted: repo.get_wanted_ad_by_slug(
                community_id,
                wanted.slug,
            ),
        )
    theme = blueprint.theme
    if theme is not None:
        add_existing(
            "theme",
            theme.slug,
            lambda: repo.get_theme_by_slug(community_id, theme.slug),
        )
    return tuple(records)


def _preview_fingerprint(
    source: str,
    rows: tuple[BlueprintDiffRow, ...],
    live_records: tuple[tuple[str, str, BlueprintLiveRecord], ...],
) -> str:
    digest = hashlib.sha256()
    digest.update(source.encode("utf-8"))
    for row in rows:
        digest.update(b"\0")
        digest.update(row.section.encode("utf-8"))
        digest.update(b"\0")
        digest.update(row.slug.encode("utf-8"))
        digest.update(b"\0")
        digest.update(row.action.encode("utf-8"))
        digest.update(b"\0")
        digest.update(row.detail.encode("utf-8"))
    for section, slug, record in live_records:
        values = asdict(record)
        values.pop("created_at", None)
        values.pop("updated_at", None)
        digest.update(b"\0live\0")
        digest.update(section.encode("utf-8"))
        digest.update(b"\0")
        digest.update(slug.encode("utf-8"))
        digest.update(b"\0")
        digest.update(
            json.dumps(
                values,
                sort_keys=True,
                separators=(",", ":"),
                default=_fingerprint_json_default,
            ).encode("utf-8")
        )
    return digest.hexdigest()[:16]


def _fingerprint_json_default(value: object) -> object:
    if isinstance(value, (frozenset, set)):
        return sorted(value)
    raise TypeError(f"Unsupported Blueprint fingerprint value: {type(value).__name__}")


def _diff_action_counts(rows: tuple[BlueprintDiffRow, ...]) -> dict[str, int]:
    return {
        action: sum(1 for row in rows if row.action == action)
        for action in ("create", "update", "skip", "blocked", "warning")
    }


def _diff_action_readiness_summary(action_counts: dict[str, int]) -> str:
    return (
        "Preflight resolved "
        f"{action_counts['create']} create, "
        f"{action_counts['update']} update, "
        f"{action_counts['skip']} skip, "
        f"{action_counts['blocked']} blocked, and "
        f"{action_counts['warning']} warning actions."
    )


def _collision_readiness_summary(rows: tuple[BlueprintDiffRow, ...]) -> str:
    skipped_collisions = [
        row for row in rows if row.action == "skip" and row.section in {"face", "wanted hook"}
    ]
    if not skipped_collisions:
        return "No live face or wanted-hook collisions need explicit update mode."
    labels = ", ".join(f"{row.section}: {row.label}" for row in skipped_collisions[:3])
    overflow = len(skipped_collisions) - 3
    if overflow > 0:
        labels = f"{labels}, and {overflow} more"
    return f"Skipped live collisions need explicit update mode before apply: {labels}."
