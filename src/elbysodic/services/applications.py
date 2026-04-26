"""Character application desk and review workflows."""

from __future__ import annotations

from typing import Protocol

from elbysodic.domain.models import Character, CommunityMembership, Material, Notification, Role
from elbysodic.services import policies
from elbysodic.services.casting import CastingReadRepository, character_reserve_view
from elbysodic.services.facets import facet_tags
from elbysodic.services.materials import MaterialSummaryRepository, material_summary
from elbysodic.services.read_models import (
    APPLICATION_STATUS_LABELS,
    APPLICATION_STATUS_VARIANTS,
    ApplicationCharacterView,
    ApplicationsDesk,
    ForumView,
)


class ApplicationRepository(
    CastingReadRepository,
    MaterialSummaryRepository,
    Protocol,
):
    def get_character_by_slug(self, community_id: int, slug: str) -> Character: ...

    def get_role(self, community_id: int, role_id: int) -> Role: ...

    def list_community_characters(self, community_id: int) -> list[Character]: ...

    def list_memberships(self, community_id: int) -> list[CommunityMembership]: ...

    def list_materials(
        self, community_id: int, *, status: str | None = "published"
    ) -> list[Material]: ...

    def update_character_application_status(
        self,
        community_id: int,
        character_id: int,
        application_status: str,
    ) -> Character: ...

    def create_notification(
        self,
        community_id: int,
        membership_id: int,
        *,
        kind: str,
        thread_id: int | None = None,
        post_id: int | None = None,
        wanted_ad_id: int | None = None,
        wanted_ad_interest_id: int | None = None,
        character_id: int | None = None,
        actor_membership_id: int,
        actor_character_id: int,
    ) -> Notification: ...


def applications_desk(repo: ApplicationRepository, viewer: ForumView) -> ApplicationsDesk:
    character_views = [
        application_character_view(repo, viewer, character)
        for character in repo.list_community_characters(viewer.community.id)
    ]
    materials = [
        material_summary(repo, viewer.community.id, material)
        for material in repo.list_materials(viewer.community.id)
        if material.material_type == "application"
    ]
    return ApplicationsDesk(
        my_applications=[
            item for item in character_views if item.character.membership_id == viewer.membership.id
        ],
        review_queue=(
            [item for item in character_views if item.character.application_status == "submitted"]
            if viewer.role.is_admin
            else []
        ),
        accepted_characters=[
            item for item in character_views if item.character.application_status == "accepted"
        ],
        application_materials=materials,
        can_review=viewer.role.is_admin,
    )


def submit_character_application(
    repo: ApplicationRepository,
    viewer: ForumView,
    character_slug: str,
) -> Character:
    character = repo.get_character_by_slug(viewer.community.id, character_slug)
    if not policies.can_post_as(viewer.membership, character):
        raise PermissionError(
            f"membership {viewer.membership.id} cannot submit character {character.id}"
        )
    if character.application_status not in {"draft", "revision_requested"}:
        raise ValueError(
            f"character {character.id} cannot be submitted from {character.application_status}"
        )
    character = repo.update_character_application_status(
        viewer.community.id,
        character.id,
        "submitted",
    )
    notify_application_directors(repo, viewer, character)
    return character


def accept_character_application(
    repo: ApplicationRepository,
    viewer: ForumView,
    character_slug: str,
) -> Character:
    if not viewer.role.is_admin:
        raise PermissionError(f"membership {viewer.membership.id} cannot review applications")
    character = repo.get_character_by_slug(viewer.community.id, character_slug)
    if character.application_status != "submitted":
        raise ValueError(
            f"character {character.id} cannot be accepted from {character.application_status}"
        )
    character = repo.update_character_application_status(
        viewer.community.id,
        character.id,
        "accepted",
    )
    notify_application_owner(repo, viewer, character, "application_accepted")
    return character


def request_character_application_revision(
    repo: ApplicationRepository,
    viewer: ForumView,
    character_slug: str,
) -> Character:
    if not viewer.role.is_admin:
        raise PermissionError(f"membership {viewer.membership.id} cannot review applications")
    character = repo.get_character_by_slug(viewer.community.id, character_slug)
    if character.application_status != "submitted":
        raise ValueError(
            f"character {character.id} cannot be revised from {character.application_status}"
        )
    character = repo.update_character_application_status(
        viewer.community.id,
        character.id,
        "revision_requested",
    )
    notify_application_owner(repo, viewer, character, "application_revision_requested")
    return character


def application_character_view(
    repo: ApplicationRepository,
    viewer: ForumView,
    character: Character,
) -> ApplicationCharacterView:
    return ApplicationCharacterView(
        character=character,
        membership=repo.get_membership(viewer.community.id, character.membership_id),
        facets=facet_tags(
            repo,
            viewer.community.id,
            repo.list_character_facets(viewer.community.id, character.id),
        ),
        reserves=[
            character_reserve_view(repo, viewer.community.id, reserve)
            for reserve in repo.list_character_reserves(viewer.community.id, character.id)
        ],
        status_label=application_status_label(character.application_status),
        status_variant=application_status_variant(character.application_status),
        is_owned_by_viewer=character.membership_id == viewer.membership.id,
    )


def notify_application_directors(
    repo: ApplicationRepository,
    viewer: ForumView,
    character: Character,
) -> None:
    for membership in repo.list_memberships(viewer.community.id):
        role = repo.get_role(viewer.community.id, membership.role_id)
        if not role.is_admin or membership.id == viewer.membership.id:
            continue
        repo.create_notification(
            viewer.community.id,
            membership.id,
            kind="application_submitted",
            character_id=character.id,
            actor_membership_id=viewer.membership.id,
            actor_character_id=character.id,
        )


def notify_application_owner(
    repo: ApplicationRepository,
    viewer: ForumView,
    character: Character,
    kind: str,
) -> None:
    actor_character_id = application_actor_character_id(viewer, character)
    if character.membership_id == viewer.membership.id:
        return
    repo.create_notification(
        viewer.community.id,
        character.membership_id,
        kind=kind,
        character_id=character.id,
        actor_membership_id=viewer.membership.id,
        actor_character_id=actor_character_id,
    )


def application_actor_character_id(viewer: ForumView, target_character: Character) -> int:
    if (
        viewer.current_character is not None
        and viewer.current_character.membership_id == viewer.membership.id
    ):
        return viewer.current_character.id
    if viewer.roster:
        return viewer.roster[0].id
    if target_character.membership_id == viewer.membership.id:
        return target_character.id
    raise ValueError("application actor needs a character")


def application_status_label(status: str) -> str:
    return APPLICATION_STATUS_LABELS.get(status, status.replace("_", " ").title())


def application_status_variant(status: str) -> str:
    return APPLICATION_STATUS_VARIANTS.get(status, "muted")
