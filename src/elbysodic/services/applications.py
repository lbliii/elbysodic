"""Character application desk and review workflows."""

from __future__ import annotations

from typing import Protocol

from elbysodic.domain.models import (
    Character,
    CharacterApplication,
    CharacterApplicationEvent,
    CommunityMembership,
    Material,
    Notification,
    Role,
)
from elbysodic.services import policies
from elbysodic.services.casting import CastingReadRepository, character_reserve_view
from elbysodic.services.facets import facet_tags
from elbysodic.services.materials import MaterialSummaryRepository, material_summary
from elbysodic.services.read_models import (
    APPLICATION_STATUS_LABELS,
    APPLICATION_STATUS_VARIANTS,
    ApplicationCharacterView,
    ApplicationReviewEventView,
    ApplicationReviewRoom,
    ApplicationsDesk,
    ForumView,
)
from elbysodic.services.timestamps import timestamp_label

MAX_APPLICATION_FIELD_LENGTH = 5000


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

    def ensure_character_application(
        self,
        community_id: int,
        character_id: int,
        *,
        source_wanted_ad_id: int | None = None,
        source_wanted_ad_interest_id: int | None = None,
    ) -> CharacterApplication: ...

    def get_character_application_for_character_or_none(
        self,
        community_id: int,
        character_id: int,
    ) -> CharacterApplication | None: ...

    def update_character_application_draft(
        self,
        community_id: int,
        application_id: int,
        *,
        title: str,
        summary: str,
        body: str,
    ) -> CharacterApplication: ...

    def update_character_application_review(
        self,
        community_id: int,
        application_id: int,
        *,
        revision_notes: str,
        staff_notes: str,
        checklist: str,
    ) -> CharacterApplication: ...

    def transition_character_application_status(
        self,
        community_id: int,
        application_id: int,
        *,
        status: str,
        actor_membership_id: int,
        actor_character_id: int | None,
        note: str = "",
    ) -> CharacterApplication: ...

    def list_character_application_events(
        self,
        community_id: int,
        application_id: int,
    ) -> list[CharacterApplicationEvent]: ...

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
    can_review = policies.can_manage_applications(viewer.membership, viewer.role)
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
            if can_review
            else []
        ),
        accepted_characters=[
            item for item in character_views if item.character.application_status == "accepted"
        ],
        application_materials=materials,
        can_review=can_review,
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
    application = repo.ensure_character_application(viewer.community.id, character.id)
    repo.transition_character_application_status(
        viewer.community.id,
        application.id,
        status="submitted",
        actor_membership_id=viewer.membership.id,
        actor_character_id=character.id,
        note="Submitted for director review.",
    )
    character = repo.get_character(viewer.community.id, character.id)
    notify_application_directors(repo, viewer, character)
    return character


def accept_character_application(
    repo: ApplicationRepository,
    viewer: ForumView,
    character_slug: str,
) -> Character:
    if not policies.can_manage_applications(viewer.membership, viewer.role):
        raise PermissionError(f"membership {viewer.membership.id} cannot review applications")
    character = repo.get_character_by_slug(viewer.community.id, character_slug)
    if character.application_status != "submitted":
        raise ValueError(
            f"character {character.id} cannot be accepted from {character.application_status}"
        )
    application = repo.ensure_character_application(viewer.community.id, character.id)
    repo.transition_character_application_status(
        viewer.community.id,
        application.id,
        status="accepted",
        actor_membership_id=viewer.membership.id,
        actor_character_id=application_actor_character_id(viewer, character),
        note="Accepted for play.",
    )
    character = repo.get_character(viewer.community.id, character.id)
    notify_application_owner(repo, viewer, character, "application_accepted")
    return character


def request_character_application_revision(
    repo: ApplicationRepository,
    viewer: ForumView,
    character_slug: str,
    *,
    note: str = "",
) -> Character:
    if not policies.can_manage_applications(viewer.membership, viewer.role):
        raise PermissionError(f"membership {viewer.membership.id} cannot review applications")
    character = repo.get_character_by_slug(viewer.community.id, character_slug)
    if character.application_status != "submitted":
        raise ValueError(
            f"character {character.id} cannot be revised from {character.application_status}"
        )
    application = repo.ensure_character_application(viewer.community.id, character.id)
    cleaned_note = _clean_application_text(note, field_name="revision note")
    if cleaned_note:
        repo.update_character_application_review(
            viewer.community.id,
            application.id,
            revision_notes=cleaned_note,
            staff_notes=application.staff_notes,
            checklist=application.checklist,
        )
        application = repo.ensure_character_application(viewer.community.id, character.id)
    repo.transition_character_application_status(
        viewer.community.id,
        application.id,
        status="revision_requested",
        actor_membership_id=viewer.membership.id,
        actor_character_id=application_actor_character_id(viewer, character),
        note=cleaned_note or "Requested revisions.",
    )
    character = repo.get_character(viewer.community.id, character.id)
    notify_application_owner(repo, viewer, character, "application_revision_requested")
    return character


def read_application_review_room(
    repo: ApplicationRepository,
    viewer: ForumView,
    character_slug: str,
) -> ApplicationReviewRoom:
    character = repo.get_character_by_slug(viewer.community.id, character_slug)
    can_review = policies.can_manage_applications(viewer.membership, viewer.role)
    can_edit = policies.can_post_as(viewer.membership, character)
    if not can_review and not can_edit:
        raise PermissionError(
            f"membership {viewer.membership.id} cannot view application for character {character.id}"
        )
    application = repo.ensure_character_application(viewer.community.id, character.id)
    character_view = application_character_view(repo, viewer, character)
    return ApplicationReviewRoom(
        application=application,
        character_view=character_view,
        events=[
            application_review_event_view(repo, viewer, event)
            for event in repo.list_character_application_events(viewer.community.id, application.id)
        ],
        can_edit_application=can_edit
        and character.application_status in {"draft", "revision_requested"},
        can_review=can_review,
    )


def update_application_draft(
    repo: ApplicationRepository,
    viewer: ForumView,
    character_slug: str,
    *,
    summary: str,
    body: str,
) -> CharacterApplication:
    character = repo.get_character_by_slug(viewer.community.id, character_slug)
    if not policies.can_post_as(viewer.membership, character):
        raise PermissionError(
            f"membership {viewer.membership.id} cannot edit application for character {character.id}"
        )
    if character.application_status not in {"draft", "revision_requested"}:
        raise ValueError(
            f"character {character.id} cannot edit application from {character.application_status}"
        )
    application = repo.ensure_character_application(viewer.community.id, character.id)
    return repo.update_character_application_draft(
        viewer.community.id,
        application.id,
        title=character.name,
        summary=_clean_application_text(summary, field_name="application summary"),
        body=_clean_application_text(body, field_name="application body"),
    )


def update_application_review(
    repo: ApplicationRepository,
    viewer: ForumView,
    character_slug: str,
    *,
    revision_notes: str,
    staff_notes: str,
    checklist: str,
) -> CharacterApplication:
    if not policies.can_manage_applications(viewer.membership, viewer.role):
        raise PermissionError(f"membership {viewer.membership.id} cannot review applications")
    character = repo.get_character_by_slug(viewer.community.id, character_slug)
    application = repo.ensure_character_application(viewer.community.id, character.id)
    return repo.update_character_application_review(
        viewer.community.id,
        application.id,
        revision_notes=_clean_application_text(revision_notes, field_name="revision notes"),
        staff_notes=_clean_application_text(staff_notes, field_name="staff notes"),
        checklist=_clean_application_text(checklist, field_name="checklist"),
    )


def application_character_view(
    repo: ApplicationRepository,
    viewer: ForumView,
    character: Character,
) -> ApplicationCharacterView:
    return ApplicationCharacterView(
        character=character,
        application=repo.get_character_application_for_character_or_none(
            viewer.community.id,
            character.id,
        ),
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


def application_review_event_view(
    repo: ApplicationRepository,
    viewer: ForumView,
    event: CharacterApplicationEvent,
) -> ApplicationReviewEventView:
    actor_membership = repo.get_membership(viewer.community.id, event.actor_membership_id)
    actor = (
        repo.get_character(viewer.community.id, event.actor_character_id)
        if event.actor_character_id is not None
        else None
    )
    actor_label = actor.name if actor is not None else actor_membership.display_name
    return ApplicationReviewEventView(
        event=event,
        actor_membership=actor_membership,
        actor=actor,
        actor_label=actor_label,
        created_at_label=timestamp_label(event.created_at),
        from_label=application_status_label(event.from_status) if event.from_status else None,
        to_label=application_status_label(event.to_status),
    )


def notify_application_directors(
    repo: ApplicationRepository,
    viewer: ForumView,
    character: Character,
) -> None:
    for membership in repo.list_memberships(viewer.community.id):
        role = repo.get_role(viewer.community.id, membership.role_id)
        if (
            not policies.can_manage_applications(membership, role)
            or membership.id == viewer.membership.id
        ):
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


def _clean_application_text(value: str, *, field_name: str) -> str:
    cleaned = value.strip()
    if len(cleaned) > MAX_APPLICATION_FIELD_LENGTH:
        raise ValueError(f"{field_name} must be {MAX_APPLICATION_FIELD_LENGTH} characters or fewer")
    return cleaned
