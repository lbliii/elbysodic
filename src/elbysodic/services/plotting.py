"""Plotting room service helpers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from typing import Protocol

from elbysodic.domain.models import (
    Board,
    Character,
    CharacterPlotHook,
    CharacterPlotHookInterest,
    CommunityMembership,
    Facet,
    Material,
    PlottingRoom,
    PlottingRoomMessage,
    PlottingRoomParticipant,
    Role,
    Thread,
    WantedAd,
    WantedAdInterest,
)
from elbysodic.services import policies
from elbysodic.services.casting import (
    CastingReadRepository,
    wanted_ad_interest_view,
    wanted_ad_summary,
    wanted_interest_stage,
)
from elbysodic.services.plot_hooks import (
    PlotHookReadRepository,
    can_manage_plot_hook,
    plot_hook_interest_view,
    plot_hook_summary,
)
from elbysodic.services.posting import PostingRepository
from elbysodic.services.posting import start_thread as _start_thread
from elbysodic.services.read_models import (
    CreatedThread,
    ForumView,
    PlotHookInterestInboxItem,
    PlottingDesk,
    PlottingRoomDetail,
    PlottingRoomMessageBatch,
    PlottingRoomMessageView,
    PlottingRoomParticipantView,
    PlottingRoomSummary,
    WantedInterestInboxItem,
)
from elbysodic.services.timestamps import timestamp_label

PLOTTING_ROOM_STATUSES = ("brainstorming", "ready", "threaded", "paused", "done")
MAX_PLOTTING_ROOM_MESSAGE_BODY = 2000


@dataclass(frozen=True, slots=True)
class PlottingRoomLiveEvent:
    kind: str
    message: PlottingRoomMessageView | None = None


_plotting_room_subscribers: dict[int, set[asyncio.Queue[PlottingRoomLiveEvent]]] = {}


class PlottingRepository(
    CastingReadRepository, PlotHookReadRepository, PostingRepository, Protocol
):
    def get_board(self, community_id: int, board_id: int) -> Board: ...

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

    def get_role(self, community_id: int, role_id: int) -> Role: ...

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

    def list_boards(self, community_id: int) -> list[Board]: ...

    def get_thread(self, community_id: int, thread_id: int) -> Thread: ...

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

    def create_plotting_room_message(
        self,
        community_id: int,
        plotting_room_id: int,
        author_membership_id: int,
        body: str,
        *,
        author_character_id: int | None = None,
    ) -> PlottingRoomMessage: ...

    def get_plotting_room_message(
        self,
        community_id: int,
        message_id: int,
    ) -> PlottingRoomMessage: ...

    def list_plotting_room_messages(
        self,
        community_id: int,
        plotting_room_id: int,
        *,
        after_id: int | None = None,
        limit: int = 100,
    ) -> list[PlottingRoomMessage]: ...

    def update_plotting_room_plan(
        self,
        community_id: int,
        plotting_room_id: int,
        *,
        notes: str,
        next_step: str,
        target_board_id: int | None,
        status: str,
    ) -> PlottingRoom: ...

    def attach_plotting_room_thread(
        self,
        community_id: int,
        plotting_room_id: int,
        thread_id: int,
    ) -> PlottingRoom: ...

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
        if wanted_ad.creator_membership_id != viewer.membership.id and not (
            policies.can_manage_casting(viewer.membership, viewer.role)
        ):
            continue
        for interest in repo.list_wanted_ad_interests(viewer.community.id, wanted_ad.id):
            if interest.status not in {"interested", "plotting", "reserved"}:
                continue
            room = _room_for_wanted_interest(repo, viewer.community.id, interest.id)
            stage_label, stage_variant = wanted_interest_stage(
                interest,
                room.room if room is not None else None,
            )
            wanted_interests.append(
                WantedInterestInboxItem(
                    wanted_ad=wanted_ad_summary(repo, viewer.community.id, wanted_ad),
                    interest=wanted_ad_interest_view(repo, viewer.community.id, interest),
                    room=room,
                    stage_group=_wanted_interest_stage_group(room),
                    stage_label=stage_label,
                    stage_variant=stage_variant,
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
    participant_membership_ids = _participant_membership_ids(participants)
    can_edit_plan = _can_edit_plotting_room_plan(viewer, room, participant_membership_ids)
    can_create_scene = _can_create_scene_from_room(viewer, room)
    if not can_edit_plan:
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
    target_board = (
        repo.get_board(viewer.community.id, room.target_board_id)
        if room.target_board_id is not None
        else None
    )
    target_thread = (
        repo.get_thread(viewer.community.id, room.target_thread_id)
        if room.target_thread_id is not None
        else None
    )
    return PlottingRoomDetail(
        room=room,
        owner_membership=repo.get_membership(viewer.community.id, room.owner_membership_id),
        participants=participants,
        source_plot_hook=source_plot_hook,
        source_wanted_ad=source_wanted_ad,
        target_board=target_board,
        target_thread=target_thread,
        scene_boards=[
            board
            for board in repo.list_boards(viewer.community.id)
            if policies.can_start_thread(viewer.membership, board, viewer.role)
        ],
        scene_character_options=_scene_character_options(viewer, participants),
        messages=plotting_room_message_views(
            repo,
            viewer.community.id,
            repo.list_plotting_room_messages(
                viewer.community.id,
                room.id,
                limit=100,
            ),
        ),
        created_at_label=timestamp_label(room.created_at),
        can_manage=can_create_scene,
        can_edit_plan=can_edit_plan,
        can_create_scene=can_create_scene and room.target_thread_id is None,
    )


def read_plotting_room_messages(
    repo: PlottingRepository,
    viewer: ForumView,
    room_id: int,
    *,
    after_id: int | None,
    limit: int = 100,
) -> PlottingRoomMessageBatch:
    membership = repo.get_membership(viewer.community.id, viewer.membership.id)
    role = repo.get_role(viewer.community.id, membership.role_id)
    if not membership.is_active:
        raise PermissionError(f"membership {membership.id} cannot view room {room_id}")
    current_viewer = replace(viewer, membership=membership, role=role)
    room = repo.get_plotting_room(current_viewer.community.id, room_id)
    participants = repo.list_plotting_room_participants(
        current_viewer.community.id,
        room.id,
    )
    participant_membership_ids = {item.membership_id for item in participants}
    if not _can_edit_plotting_room_plan(
        current_viewer,
        room,
        participant_membership_ids,
    ):
        raise PermissionError(f"membership {membership.id} cannot view room {room.id}")
    messages = repo.list_plotting_room_messages(
        current_viewer.community.id,
        room.id,
        after_id=after_id,
        limit=limit,
    )
    return PlottingRoomMessageBatch(
        messages=plotting_room_message_views(
            repo,
            current_viewer.community.id,
            messages,
        ),
        last_message_id=messages[-1].id if messages else after_id,
    )


def update_plotting_room_plan(
    repo: PlottingRepository,
    viewer: ForumView,
    room_id: int,
    *,
    notes: str,
    next_step: str,
    target_board_id: int | None,
    status: str,
) -> PlottingRoom:
    room = repo.get_plotting_room(viewer.community.id, room_id)
    participants = [
        plotting_room_participant_view(repo, viewer.community.id, participant)
        for participant in repo.list_plotting_room_participants(viewer.community.id, room.id)
    ]
    if not _can_edit_plotting_room_plan(viewer, room, _participant_membership_ids(participants)):
        raise PermissionError(f"membership {viewer.membership.id} cannot edit room {room.id}")
    cleaned_status = clean_plotting_room_status(status)
    if cleaned_status == "threaded" and room.target_thread_id is None:
        raise ValueError("start a scene before marking a room threaded")
    if target_board_id is not None:
        board = repo.get_board(viewer.community.id, target_board_id)
        if not policies.can_start_thread(viewer.membership, board, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot start scenes in board {board.id}"
            )
    return repo.update_plotting_room_plan(
        viewer.community.id,
        room.id,
        notes=notes.strip(),
        next_step=next_step.strip(),
        target_board_id=target_board_id,
        status=cleaned_status,
    )


def create_thread_from_plotting_room(
    repo: PlottingRepository,
    viewer: ForumView,
    room_id: int,
    *,
    board_id: int,
    character_id: int,
    title: str,
    summary: str,
    body: str,
    location: str = "",
    timeline: str = "",
    posting_mode: str = "freeform",
) -> CreatedThread:
    room = repo.get_plotting_room(viewer.community.id, room_id)
    if not _can_create_scene_from_room(viewer, room):
        raise PermissionError(f"membership {viewer.membership.id} cannot create a scene")
    if room.target_thread_id is not None:
        raise ValueError("plotting room already has a scene")
    board = repo.get_board(viewer.community.id, board_id)
    participants = [
        plotting_room_participant_view(repo, viewer.community.id, participant)
        for participant in repo.list_plotting_room_participants(viewer.community.id, room.id)
    ]
    participant_ids = [
        item.participant.character_id
        for item in participants
        if item.participant.character_id is not None
    ]
    with repo.transaction():
        created = _start_thread(
            repo,
            viewer,
            board_slug=board.slug,
            character_id=character_id,
            title=title,
            body=body,
            status="active",
            location=location,
            timeline=timeline,
            summary=summary,
            posting_mode=posting_mode,
            participant_ids=participant_ids,
        )
        repo.attach_plotting_room_thread(viewer.community.id, room.id, created.thread.id)
        _notify_room_threaded(repo, viewer, room, participants, created.thread)
    return created


async def create_plotting_room_message(
    repo: PlottingRepository,
    viewer: ForumView,
    room_id: int,
    body: str,
) -> PlottingRoomMessageView:
    room = repo.get_plotting_room(viewer.community.id, room_id)
    participants = [
        plotting_room_participant_view(repo, viewer.community.id, participant)
        for participant in repo.list_plotting_room_participants(viewer.community.id, room.id)
    ]
    if not _can_edit_plotting_room_plan(viewer, room, _participant_membership_ids(participants)):
        raise PermissionError(f"membership {viewer.membership.id} cannot post in room {room.id}")
    cleaned = body.strip()
    if not cleaned:
        raise ValueError("message body is required")
    if len(cleaned) > MAX_PLOTTING_ROOM_MESSAGE_BODY:
        cleaned = cleaned[:MAX_PLOTTING_ROOM_MESSAGE_BODY]
    message = repo.create_plotting_room_message(
        viewer.community.id,
        room.id,
        viewer.membership.id,
        cleaned,
        author_character_id=(
            viewer.current_character.id if viewer.current_character is not None else None
        ),
    )
    message_view = plotting_room_message_view(repo, viewer.community.id, message)
    await publish_plotting_room_live_event(
        room.id,
        PlottingRoomLiveEvent(kind="message", message=message_view),
    )
    return message_view


def plotting_room_message_view(
    repo: PlottingRepository,
    community_id: int,
    message: PlottingRoomMessage,
) -> PlottingRoomMessageView:
    return PlottingRoomMessageView(
        message=message,
        author_membership=repo.get_membership(community_id, message.author_membership_id),
        author_character=(
            repo.get_character(community_id, message.author_character_id)
            if message.author_character_id is not None
            else None
        ),
        created_at_label=timestamp_label(message.created_at),
    )


def plotting_room_message_views(
    repo: PlottingRepository,
    community_id: int,
    messages: list[PlottingRoomMessage],
) -> list[PlottingRoomMessageView]:
    memberships = repo.list_memberships_by_ids(
        community_id,
        sorted({message.author_membership_id for message in messages}),
    )
    characters = repo.list_characters_by_ids(
        community_id,
        sorted(
            {
                message.author_character_id
                for message in messages
                if message.author_character_id is not None
            }
        ),
    )
    return [
        PlottingRoomMessageView(
            message=message,
            author_membership=memberships[message.author_membership_id],
            author_character=(
                characters[message.author_character_id]
                if message.author_character_id is not None
                else None
            ),
            created_at_label=timestamp_label(message.created_at),
        )
        for message in messages
    ]


async def subscribe_plotting_room_live(room_id: int) -> asyncio.Queue[PlottingRoomLiveEvent]:
    queue: asyncio.Queue[PlottingRoomLiveEvent] = asyncio.Queue()
    _plotting_room_subscribers.setdefault(room_id, set()).add(queue)
    await queue.put(PlottingRoomLiveEvent(kind="ready"))
    return queue


async def unsubscribe_plotting_room_live(
    room_id: int,
    queue: asyncio.Queue[PlottingRoomLiveEvent],
) -> None:
    subscribers = _plotting_room_subscribers.get(room_id)
    if subscribers is None:
        return
    subscribers.discard(queue)
    if not subscribers:
        _plotting_room_subscribers.pop(room_id, None)


async def publish_plotting_room_live_event(
    room_id: int,
    event: PlottingRoomLiveEvent,
) -> None:
    for queue in list(_plotting_room_subscribers.get(room_id, ())):
        await queue.put(event)


def clean_plotting_room_status(status: str) -> str:
    cleaned = status.strip().lower().replace("-", "_")
    if cleaned not in PLOTTING_ROOM_STATUSES:
        return "brainstorming"
    return cleaned


def _participant_membership_ids(participants: list[PlottingRoomParticipantView]) -> set[int]:
    return {participant.participant.membership_id for participant in participants}


def _can_edit_plotting_room_plan(
    viewer: ForumView,
    room: PlottingRoom,
    participant_membership_ids: set[int],
) -> bool:
    return (
        viewer.membership.id == room.owner_membership_id
        or viewer.membership.id in participant_membership_ids
        or policies.can_manage_casting(viewer.membership, viewer.role)
    )


def _can_create_scene_from_room(viewer: ForumView, room: PlottingRoom) -> bool:
    return room.owner_membership_id == viewer.membership.id or policies.can_manage_casting(
        viewer.membership,
        viewer.role,
    )


def _scene_character_options(
    viewer: ForumView,
    participants: list[PlottingRoomParticipantView],
) -> list[Character]:
    participant_character_ids = {
        participant.participant.character_id
        for participant in participants
        if participant.participant.membership_id == viewer.membership.id
        and participant.participant.character_id is not None
    }
    if participant_character_ids:
        return [
            character for character in viewer.roster if character.id in participant_character_ids
        ]
    return viewer.roster


def _notify_room_threaded(
    repo: PlottingRepository,
    viewer: ForumView,
    room: PlottingRoom,
    participants: list[PlottingRoomParticipantView],
    thread: Thread,
) -> None:
    notified_membership_ids: set[int] = set()
    for participant in participants:
        membership_id = participant.participant.membership_id
        if membership_id == viewer.membership.id or membership_id in notified_membership_ids:
            continue
        repo.create_notification(
            viewer.community.id,
            membership_id,
            kind="plotting_room_threaded",
            thread_id=thread.id,
            plotting_room_id=room.id,
            actor_membership_id=viewer.membership.id,
            actor_character_id=thread.author_character_id,
        )
        notified_membership_ids.add(membership_id)


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
    if wanted_ad.creator_membership_id != viewer.membership.id and not (
        policies.can_manage_casting(viewer.membership, viewer.role)
    ):
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


def _wanted_interest_stage_group(room: PlottingRoomSummary | None) -> str:
    if room is None:
        return "raised"
    if room.room.status == "threaded" or room.room.target_thread_id is not None:
        return "threaded"
    if room.room.status == "ready":
        return "ready"
    return "plotting"


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
