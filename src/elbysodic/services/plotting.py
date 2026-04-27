"""Plotting room service helpers."""

from __future__ import annotations

from typing import Protocol

from elbysodic.domain.models import (
    Character,
    CharacterPlotHook,
    CharacterPlotHookInterest,
    CommunityMembership,
    Facet,
    Material,
    PlottingRoom,
    PlottingRoomParticipant,
    WantedAd,
    WantedAdInterest,
)
from elbysodic.services.casting import (
    CastingReadRepository,
    wanted_ad_interest_view,
    wanted_ad_summary,
)
from elbysodic.services.plot_hooks import (
    PlotHookReadRepository,
    can_manage_plot_hook,
    plot_hook_interest_view,
    plot_hook_summary,
)
from elbysodic.services.read_models import (
    ForumView,
    PlotHookInterestInboxItem,
    PlottingDesk,
    PlottingRoomDetail,
    PlottingRoomParticipantView,
    PlottingRoomSummary,
    WantedInterestInboxItem,
)
from elbysodic.services.timestamps import timestamp_label

PLOTTING_ROOM_STATUSES = ("brainstorming", "ready", "threaded", "paused", "done")


class PlottingRepository(CastingReadRepository, PlotHookReadRepository, Protocol):
    def get_character(self, community_id: int, character_id: int) -> Character: ...

    def get_character_by_slug(self, community_id: int, slug: str) -> Character: ...

    def get_character_plot_hook(
        self,
        community_id: int,
        plot_hook_id: int,
    ) -> CharacterPlotHook: ...

    def get_membership(
        self,
        community_id: int,
        membership_id: int,
    ) -> CommunityMembership: ...

    def get_material(self, community_id: int, material_id: int) -> Material: ...

    def list_character_plot_hook_facets(
        self,
        community_id: int,
        plot_hook_id: int,
    ) -> list[Facet]: ...

    def list_character_plot_hooks(
        self,
        community_id: int,
        *,
        status: str | None = "open",
    ) -> list[CharacterPlotHook]: ...

    def get_character_plot_hook_by_slug(
        self,
        community_id: int,
        character_id: int,
        slug: str,
    ) -> CharacterPlotHook: ...

    def get_character_plot_hook_interest(
        self,
        community_id: int,
        interest_id: int,
    ) -> CharacterPlotHookInterest: ...

    def list_character_plot_hook_interests(
        self,
        community_id: int,
        plot_hook_id: int,
        *,
        status: str | None = None,
    ) -> list[CharacterPlotHookInterest]: ...

    def update_character_plot_hook_interest_status(
        self,
        community_id: int,
        interest_id: int,
        status: str,
    ) -> CharacterPlotHookInterest: ...

    def update_character_plot_hook(
        self,
        community_id: int,
        plot_hook_id: int,
        *,
        title: str,
        hook_type: str,
        summary: str,
        body: str,
        status: str,
        related_material_id: int | None = None,
    ) -> CharacterPlotHook: ...

    def list_wanted_ads(
        self,
        community_id: int,
        *,
        status: str | None = "open",
    ) -> list[WantedAd]: ...

    def get_wanted_ad(self, community_id: int, wanted_ad_id: int) -> WantedAd: ...

    def get_wanted_ad_by_slug(self, community_id: int, slug: str) -> WantedAd: ...

    def list_wanted_ad_facets(self, community_id: int, wanted_ad_id: int) -> list[Facet]: ...

    def list_wanted_ad_related_characters(
        self,
        community_id: int,
        wanted_ad_id: int,
    ) -> list[Character]: ...

    def get_wanted_ad_interest(
        self,
        community_id: int,
        interest_id: int,
    ) -> WantedAdInterest: ...

    def list_wanted_ad_interests(
        self,
        community_id: int,
        wanted_ad_id: int,
        *,
        status: str | None = None,
    ) -> list[WantedAdInterest]: ...

    def update_wanted_ad_interest_status(
        self,
        community_id: int,
        interest_id: int,
        status: str,
    ) -> WantedAdInterest: ...

    def create_plotting_room(
        self,
        community_id: int,
        owner_membership_id: int,
        title: str,
        *,
        source_plot_hook_id: int | None = None,
        source_plot_hook_interest_id: int | None = None,
        source_wanted_ad_id: int | None = None,
        source_wanted_ad_interest_id: int | None = None,
        summary: str = "",
        status: str = "brainstorming",
    ) -> PlottingRoom: ...

    def get_plotting_room(self, community_id: int, plotting_room_id: int) -> PlottingRoom: ...

    def get_plotting_room_for_plot_hook_interest(
        self,
        community_id: int,
        interest_id: int,
    ) -> PlottingRoom: ...

    def get_plotting_room_for_wanted_interest(
        self,
        community_id: int,
        interest_id: int,
    ) -> PlottingRoom: ...

    def list_plotting_rooms_for_membership(
        self,
        community_id: int,
        membership_id: int,
        *,
        status: str | None = None,
    ) -> list[PlottingRoom]: ...

    def create_plotting_room_participant(
        self,
        community_id: int,
        plotting_room_id: int,
        membership_id: int,
        *,
        character_id: int | None = None,
        prospective_character_name: str = "",
        participant_role: str = "participant",
    ) -> PlottingRoomParticipant: ...

    def list_plotting_room_participants(
        self,
        community_id: int,
        plotting_room_id: int,
    ) -> list[PlottingRoomParticipant]: ...

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
        character_plot_hook_id: int | None = None,
        plotting_room_id: int | None = None,
        character_id: int | None = None,
        actor_membership_id: int,
        actor_character_id: int | None,
    ): ...


class PlottingRoomSummaryRepository(Protocol):
    def get_character(self, community_id: int, character_id: int) -> Character: ...

    def get_character_plot_hook(
        self,
        community_id: int,
        plot_hook_id: int,
    ) -> CharacterPlotHook: ...

    def get_membership(
        self,
        community_id: int,
        membership_id: int,
    ) -> CommunityMembership: ...

    def get_wanted_ad(self, community_id: int, wanted_ad_id: int) -> WantedAd: ...

    def list_plotting_room_participants(
        self,
        community_id: int,
        plotting_room_id: int,
    ) -> list[PlottingRoomParticipant]: ...


def plotting_desk(repo: PlottingRepository, viewer: ForumView) -> PlottingDesk:
    rooms = [
        plotting_room_summary(repo, viewer.community.id, room)
        for room in repo.list_plotting_rooms_for_membership(
            viewer.community.id,
            viewer.membership.id,
        )
        if room.status != "done"
    ]
    plot_hook_interests: list[PlotHookInterestInboxItem] = []
    for hook in repo.list_character_plot_hooks(viewer.community.id, status=None):
        if hook.status == "archived" or not can_manage_plot_hook(viewer, hook):
            continue
        for interest in repo.list_character_plot_hook_interests(viewer.community.id, hook.id):
            if interest.status not in {"interested", "plotting"}:
                continue
            plot_hook_interests.append(
                PlotHookInterestInboxItem(
                    hook=plot_hook_summary(repo, viewer.community.id, hook),
                    interest=plot_hook_interest_view(repo, viewer.community.id, interest),
                    room=_room_for_plot_hook_interest(repo, viewer.community.id, interest.id),
                )
            )
    wanted_interests: list[WantedInterestInboxItem] = []
    for wanted_ad in repo.list_wanted_ads(viewer.community.id, status=None):
        if wanted_ad.status == "archived":
            continue
        if wanted_ad.creator_membership_id != viewer.membership.id and not viewer.role.is_admin:
            continue
        for interest in repo.list_wanted_ad_interests(viewer.community.id, wanted_ad.id):
            if interest.status not in {"interested", "plotting", "reserved"}:
                continue
            wanted_interests.append(
                WantedInterestInboxItem(
                    wanted_ad=wanted_ad_summary(repo, viewer.community.id, wanted_ad),
                    interest=wanted_ad_interest_view(repo, viewer.community.id, interest),
                    room=_room_for_wanted_interest(repo, viewer.community.id, interest.id),
                )
            )
    return PlottingDesk(
        rooms=rooms,
        plot_hook_interests=plot_hook_interests,
        wanted_interests=wanted_interests,
    )


def read_plotting_room(
    repo: PlottingRepository,
    viewer: ForumView,
    room_id: int,
) -> PlottingRoomDetail:
    room = repo.get_plotting_room(viewer.community.id, room_id)
    participants = [
        plotting_room_participant_view(repo, viewer.community.id, participant)
        for participant in repo.list_plotting_room_participants(viewer.community.id, room.id)
    ]
    if not viewer.role.is_admin and viewer.membership.id not in {
        participant.participant.membership_id for participant in participants
    }:
        raise PermissionError(f"membership {viewer.membership.id} cannot view room {room.id}")
    source_plot_hook = None
    if room.source_plot_hook_id is not None:
        source_plot_hook = plot_hook_summary(
            repo,
            viewer.community.id,
            repo.get_character_plot_hook(viewer.community.id, room.source_plot_hook_id),
        )
    source_wanted_ad = None
    if room.source_wanted_ad_id is not None:
        source_wanted_ad = wanted_ad_summary(
            repo,
            viewer.community.id,
            repo.get_wanted_ad(viewer.community.id, room.source_wanted_ad_id),
        )
    return PlottingRoomDetail(
        room=room,
        owner_membership=repo.get_membership(viewer.community.id, room.owner_membership_id),
        participants=participants,
        source_plot_hook=source_plot_hook,
        source_wanted_ad=source_wanted_ad,
        created_at_label=timestamp_label(room.created_at),
        can_manage=room.owner_membership_id == viewer.membership.id or viewer.role.is_admin,
    )


def create_plotting_room_from_plot_hook_interest(
    repo: PlottingRepository,
    viewer: ForumView,
    character_slug: str,
    hook_slug: str,
    interest_id: int,
) -> PlottingRoom:
    character = repo.get_character_by_slug(viewer.community.id, character_slug)
    hook = repo.get_character_plot_hook_by_slug(viewer.community.id, character.id, hook_slug)
    if not can_manage_plot_hook(viewer, hook):
        raise PermissionError(f"membership {viewer.membership.id} cannot manage hook {hook.id}")
    interest = repo.get_character_plot_hook_interest(viewer.community.id, interest_id)
    if interest.plot_hook_id != hook.id:
        raise LookupError(f"interest {interest.id} does not belong to plot hook {hook.id}")
    existing = _room_for_plot_hook_interest(repo, viewer.community.id, interest.id)
    if existing is not None:
        return existing.room
    interested_character = repo.get_character(viewer.community.id, interest.character_id)
    room = repo.create_plotting_room(
        viewer.community.id,
        viewer.membership.id,
        f"{hook.title}: {interested_character.name}",
        source_plot_hook_id=hook.id,
        source_plot_hook_interest_id=interest.id,
        summary=hook.summary,
    )
    repo.create_plotting_room_participant(
        viewer.community.id,
        room.id,
        hook.author_membership_id,
        character_id=hook.character_id,
        participant_role="owner",
    )
    repo.create_plotting_room_participant(
        viewer.community.id,
        room.id,
        interest.membership_id,
        character_id=interest.character_id,
    )
    repo.update_character_plot_hook_interest_status(viewer.community.id, interest.id, "plotting")
    if hook.status == "open":
        repo.update_character_plot_hook(
            viewer.community.id,
            hook.id,
            title=hook.title,
            hook_type=hook.hook_type,
            summary=hook.summary,
            body=hook.body,
            status="plotting",
            related_material_id=hook.related_material_id,
        )
    if interest.membership_id != viewer.membership.id:
        repo.create_notification(
            viewer.community.id,
            interest.membership_id,
            kind="plotting_room_created",
            plotting_room_id=room.id,
            actor_membership_id=viewer.membership.id,
            actor_character_id=hook.character_id,
        )
    return room


def create_plotting_room_from_wanted_interest(
    repo: PlottingRepository,
    viewer: ForumView,
    wanted_slug: str,
    interest_id: int,
) -> PlottingRoom:
    wanted_ad = repo.get_wanted_ad_by_slug(viewer.community.id, wanted_slug)
    if wanted_ad.creator_membership_id != viewer.membership.id and not viewer.role.is_admin:
        raise PermissionError(
            f"membership {viewer.membership.id} cannot manage wanted hook {wanted_ad.id}"
        )
    interest = repo.get_wanted_ad_interest(viewer.community.id, interest_id)
    if interest.wanted_ad_id != wanted_ad.id:
        raise LookupError(f"interest {interest.id} does not belong to wanted hook {wanted_ad.id}")
    existing = _room_for_wanted_interest(repo, viewer.community.id, interest.id)
    if existing is not None:
        return existing.room
    display_name = _wanted_interest_display_name(repo, viewer.community.id, interest)
    room = repo.create_plotting_room(
        viewer.community.id,
        viewer.membership.id,
        f"{wanted_ad.title}: {display_name}",
        source_wanted_ad_id=wanted_ad.id,
        source_wanted_ad_interest_id=interest.id,
        summary=wanted_ad.summary,
    )
    repo.create_plotting_room_participant(
        viewer.community.id,
        room.id,
        wanted_ad.creator_membership_id,
        character_id=wanted_ad.creator_character_id,
        participant_role="owner",
    )
    repo.create_plotting_room_participant(
        viewer.community.id,
        room.id,
        interest.membership_id,
        character_id=interest.character_id,
        prospective_character_name=interest.prospective_character_name,
    )
    if interest.status == "interested":
        repo.update_wanted_ad_interest_status(viewer.community.id, interest.id, "plotting")
    if interest.membership_id != viewer.membership.id:
        repo.create_notification(
            viewer.community.id,
            interest.membership_id,
            kind="plotting_room_created",
            plotting_room_id=room.id,
            actor_membership_id=viewer.membership.id,
            actor_character_id=_wanted_room_actor_character_id(viewer, wanted_ad),
        )
    return room


def plotting_room_summary(
    repo: PlottingRoomSummaryRepository,
    community_id: int,
    room: PlottingRoom,
) -> PlottingRoomSummary:
    return PlottingRoomSummary(
        room=room,
        participants=[
            plotting_room_participant_view(repo, community_id, participant)
            for participant in repo.list_plotting_room_participants(community_id, room.id)
        ],
        source_label=plotting_room_source_label(room),
        source_href=plotting_room_source_href(repo, community_id, room),
        created_at_label=timestamp_label(room.created_at),
    )


def plotting_room_participant_view(
    repo: PlottingRoomSummaryRepository,
    community_id: int,
    participant: PlottingRoomParticipant,
) -> PlottingRoomParticipantView:
    return PlottingRoomParticipantView(
        participant=participant,
        membership=repo.get_membership(community_id, participant.membership_id),
        character=(
            repo.get_character(community_id, participant.character_id)
            if participant.character_id is not None
            else None
        ),
        created_at_label=timestamp_label(participant.created_at),
    )


def plotting_room_source_label(room: PlottingRoom) -> str:
    if room.source_plot_hook_id is not None:
        return "Plot hook"
    if room.source_wanted_ad_id is not None:
        return "Wanted hook"
    return "Plotting"


def plotting_room_source_href(
    repo: PlottingRoomSummaryRepository,
    community_id: int,
    room: PlottingRoom,
) -> str:
    if room.source_plot_hook_id is not None:
        hook = repo.get_character_plot_hook(community_id, room.source_plot_hook_id)
        character = repo.get_character(community_id, hook.character_id)
        return f"/characters/{character.slug}/hooks/{hook.slug}"
    if room.source_wanted_ad_id is not None:
        wanted_ad = repo.get_wanted_ad(community_id, room.source_wanted_ad_id)
        return f"/wanted/{wanted_ad.slug}"
    return "/plotting"


def _room_for_plot_hook_interest(
    repo: PlottingRepository,
    community_id: int,
    interest_id: int,
) -> PlottingRoomSummary | None:
    try:
        return plotting_room_summary(
            repo,
            community_id,
            repo.get_plotting_room_for_plot_hook_interest(community_id, interest_id),
        )
    except LookupError:
        return None


def _room_for_wanted_interest(
    repo: PlottingRepository,
    community_id: int,
    interest_id: int,
) -> PlottingRoomSummary | None:
    try:
        return plotting_room_summary(
            repo,
            community_id,
            repo.get_plotting_room_for_wanted_interest(community_id, interest_id),
        )
    except LookupError:
        return None


def _wanted_interest_display_name(
    repo: PlottingRepository,
    community_id: int,
    interest: WantedAdInterest,
) -> str:
    if interest.character_id is not None:
        return repo.get_character(community_id, interest.character_id).name
    return interest.prospective_character_name


def _wanted_room_actor_character_id(viewer: ForumView, wanted_ad: WantedAd) -> int | None:
    if wanted_ad.creator_membership_id == viewer.membership.id:
        return wanted_ad.creator_character_id
    if viewer.current_character is not None:
        return viewer.current_character.id
    return None
