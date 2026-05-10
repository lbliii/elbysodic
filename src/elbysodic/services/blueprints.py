"""Service boundary for director-authored Program Blueprint previews."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import replace
from typing import Literal, Protocol

from elbysodic.blueprints import (
    BlueprintDiffRow,
    ProgramBlueprint,
    ProgramBlueprintPreview,
    preview_program_blueprint_yaml,
)
from elbysodic.domain import Board, Character, Community, CommunityTheme, Material, Role, WantedAd
from elbysodic.services import policies
from elbysodic.services.read_models import ForumView


class BlueprintPlanRepository(Protocol):
    def get_community_by_slug(self, slug: str) -> Community: ...

    def get_role_by_slug(self, community_id: int, slug: str) -> Role: ...

    def get_character_by_slug(self, community_id: int, slug: str) -> Character: ...

    def get_board_by_slug(self, community_id: int, slug: str) -> Board: ...

    def get_material_by_slug(self, community_id: int, slug: str) -> Material: ...

    def get_wanted_ad_by_slug(self, community_id: int, slug: str) -> WantedAd: ...

    def get_theme_by_slug(self, community_id: int, slug: str) -> CommunityTheme: ...


def preview_program_blueprint(
    repo: BlueprintPlanRepository,
    viewer: ForumView,
    source: str,
) -> ProgramBlueprintPreview:
    if not policies.can_manage_world(viewer.membership, viewer.role):
        raise PermissionError(
            f"membership {viewer.membership.id} cannot preview program blueprints"
        )
    preview = preview_program_blueprint_yaml(source)
    if not preview.is_valid or preview.blueprint is None:
        return preview
    diff_rows = plan_program_blueprint_hydration(repo, preview.blueprint)
    return replace(
        preview,
        diff_rows=diff_rows,
        preview_fingerprint=_preview_fingerprint(source, diff_rows),
    )


def plan_program_blueprint_hydration(
    repo: BlueprintPlanRepository,
    blueprint: ProgramBlueprint,
) -> tuple[BlueprintDiffRow, ...]:
    rows: list[BlueprintDiffRow] = []
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


def _preview_fingerprint(source: str, rows: tuple[BlueprintDiffRow, ...]) -> str:
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
    return digest.hexdigest()[:16]
