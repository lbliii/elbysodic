"""Casting, wanted hook, interest, and reserve service helpers."""

from __future__ import annotations

from typing import Protocol

from elbysodic.domain.models import (
    Board,
    Character,
    CharacterReserve,
    CommunityMembership,
    Facet,
    Material,
    PlottingRoom,
    Thread,
    WantedAd,
    WantedAdInterest,
)
from elbysodic.domain.vocabulary import wanted_type_label
from elbysodic.services import policies
from elbysodic.services.facets import FacetReadRepository, facet_tags
from elbysodic.services.markup import render_prose_body
from elbysodic.services.posts import PostViewRepository, post_mention_links
from elbysodic.services.read_models import (
    CastingDesk,
    CastingWantedItem,
    CharacterReserveView,
    ForumView,
    WantedAdDetail,
    WantedAdInterestDetailItem,
    WantedAdInterestView,
    WantedAdSummary,
    WantedBoard,
)
from elbysodic.services.timestamps import timestamp_label

WANTED_STATUSES: tuple[str, ...] = ("open", "reserved", "filled", "archived")


class CastingReadRepository(FacetReadRepository, PostViewRepository, Protocol):
    def get_character(self, community_id: int, character_id: int) -> Character: ...

    def list_characters(self, community_id: int, membership_id: int) -> list[Character]: ...

    def get_membership(
        self,
        community_id: int,
        membership_id: int,
    ) -> CommunityMembership: ...

    def get_material(self, community_id: int, material_id: int) -> Material: ...

    def get_board(self, community_id: int, board_id: int) -> Board: ...

    def list_wanted_ads(
        self,
        community_id: int,
        *,
        status: str | None = "open",
    ) -> list[WantedAd]: ...

    def get_wanted_ad_by_slug(self, community_id: int, slug: str) -> WantedAd: ...

    def list_wanted_ad_facets(self, community_id: int, wanted_ad_id: int) -> list[Facet]: ...

    def list_wanted_ad_related_characters(
        self,
        community_id: int,
        wanted_ad_id: int,
    ) -> list[Character]: ...

    def list_wanted_ad_interests(
        self,
        community_id: int,
        wanted_ad_id: int,
    ) -> list[WantedAdInterest]: ...

    def get_wanted_ad_interest(
        self,
        community_id: int,
        interest_id: int,
    ) -> WantedAdInterest: ...

    def get_plotting_room_for_wanted_interest(
        self,
        community_id: int,
        interest_id: int,
    ) -> PlottingRoom: ...

    def get_thread(self, community_id: int, thread_id: int) -> Thread: ...

    def list_character_reserves_for_community(
        self,
        community_id: int,
    ) -> list[CharacterReserve]: ...

    def list_character_reserves_for_wanted_ad(
        self,
        community_id: int,
        wanted_ad_id: int,
    ) -> list[CharacterReserve]: ...

    def list_character_reserves(
        self,
        community_id: int,
        character_id: int,
    ) -> list[CharacterReserve]: ...

    def create_character_reserve(
        self,
        community_id: int,
        membership_id: int,
        character_id: int,
        title: str,
        *,
        wanted_ad_id: int | None = None,
        wanted_ad_interest_id: int | None = None,
        reserve_type: str = "wanted",
        notes: str = "",
        status: str = "active",
    ) -> CharacterReserve: ...

    def get_wanted_ad(self, community_id: int, wanted_ad_id: int) -> WantedAd: ...


class CastingRepository(CastingReadRepository, Protocol):
    def update_wanted_ad_status(
        self,
        community_id: int,
        wanted_ad_id: int,
        status: str,
    ) -> WantedAd: ...

    def create_wanted_ad_interest(
        self,
        community_id: int,
        wanted_ad_id: int,
        membership_id: int,
        character_id: int | None = None,
        *,
        prospective_character_name: str = "",
        note: str = "",
        status: str = "interested",
    ) -> WantedAdInterest: ...

    def update_wanted_ad_interest_status(
        self,
        community_id: int,
        interest_id: int,
        status: str,
    ) -> WantedAdInterest: ...

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
        character_id: int | None = None,
        actor_membership_id: int,
        actor_character_id: int | None,
    ): ...


def wanted_board(repo: CastingReadRepository, viewer: ForumView) -> WantedBoard:
    return WantedBoard(
        open_ads=[
            wanted_ad_summary(repo, viewer.community.id, wanted_ad)
            for wanted_ad in repo.list_wanted_ads(viewer.community.id)
        ]
    )


def casting_desk(repo: CastingReadRepository, viewer: ForumView) -> CastingDesk:
    active_reserves = [
        character_reserve_view(repo, viewer.community.id, reserve)
        for reserve in repo.list_character_reserves_for_community(viewer.community.id)
    ]
    wanted_with_interest: list[CastingWantedItem] = []
    for wanted_ad in repo.list_wanted_ads(viewer.community.id, status=None):
        if wanted_ad.status == "archived":
            continue
        interests = [
            wanted_ad_interest_view(repo, viewer.community.id, interest)
            for interest in repo.list_wanted_ad_interests(
                viewer.community.id,
                wanted_ad.id,
            )
        ]
        reserves = [
            reserve for reserve in active_reserves if reserve.reserve.wanted_ad_id == wanted_ad.id
        ]
        if not interests and not reserves:
            continue
        wanted_with_interest.append(
            CastingWantedItem(
                wanted_ad=wanted_ad_summary(repo, viewer.community.id, wanted_ad),
                interests=interests,
                reserves=reserves,
                is_created_by_viewer=wanted_ad.creator_membership_id == viewer.membership.id,
            )
        )
    return CastingDesk(
        active_face=viewer.current_character,
        active_face_reserves=[
            reserve
            for reserve in active_reserves
            if viewer.current_character is not None
            and reserve.reserve.character_id == viewer.current_character.id
        ],
        my_reserves=[
            reserve
            for reserve in active_reserves
            if reserve.reserve.membership_id == viewer.membership.id
        ],
        active_reserves=active_reserves,
        wanted_with_interest=wanted_with_interest,
    )


def read_wanted_ad(
    repo: CastingReadRepository,
    viewer: ForumView,
    wanted_slug: str,
) -> WantedAdDetail:
    wanted_ad = repo.get_wanted_ad_by_slug(viewer.community.id, wanted_slug)
    can_manage = can_manage_wanted_ad(viewer, wanted_ad)
    if wanted_ad.status == "archived" and not can_manage:
        raise LookupError(f"wanted ad not found in community {viewer.community.id}: {wanted_slug}")
    facets = facet_tags(
        repo,
        viewer.community.id,
        repo.list_wanted_ad_facets(viewer.community.id, wanted_ad.id),
    )
    facet_ids = {tag.facet.id for tag in facets}
    related = []
    for candidate in repo.list_wanted_ads(viewer.community.id):
        if candidate.id == wanted_ad.id:
            continue
        candidate_facets = facet_tags(
            repo,
            viewer.community.id,
            repo.list_wanted_ad_facets(viewer.community.id, candidate.id),
        )
        if facet_ids and not facet_ids.intersection({tag.facet.id for tag in candidate_facets}):
            continue
        related.append(wanted_ad_summary(repo, viewer.community.id, candidate))
    interests = [
        wanted_ad_interest_detail_item(
            repo,
            viewer,
            interest,
            can_manage=can_manage,
        )
        for interest in repo.list_wanted_ad_interests(viewer.community.id, wanted_ad.id)
    ]
    reserves = [
        character_reserve_view(repo, viewer.community.id, reserve)
        for reserve in repo.list_character_reserves_for_wanted_ad(
            viewer.community.id,
            wanted_ad.id,
        )
    ]
    viewer_interest = None
    if viewer.current_character is not None:
        viewer_interest = next(
            (
                interest
                for interest in interests
                if interest.character is not None
                and interest.interest.character_id == viewer.current_character.id
            ),
            None,
        )
    viewer_prospective_interest = next(
        (
            interest
            for interest in interests
            if interest.character is None
            and interest.interest.membership_id == viewer.membership.id
        ),
        None,
    )
    if viewer_interest is None:
        viewer_interest = viewer_prospective_interest
    is_created_by_viewer = wanted_ad.creator_membership_id == viewer.membership.id
    return WantedAdDetail(
        wanted_ad=wanted_ad,
        creator_membership=repo.get_membership(
            viewer.community.id,
            wanted_ad.creator_membership_id,
        ),
        creator_character=(
            repo.get_character(viewer.community.id, wanted_ad.creator_character_id)
            if wanted_ad.creator_character_id is not None
            else None
        ),
        related_material=(
            repo.get_material(viewer.community.id, wanted_ad.related_material_id)
            if wanted_ad.related_material_id is not None
            else None
        ),
        related_characters=repo.list_wanted_ad_related_characters(
            viewer.community.id,
            wanted_ad.id,
        ),
        facets=facets,
        interests=interests,
        reserves=reserves,
        reserve_interest_ids={
            reserve.reserve.wanted_ad_interest_id
            for reserve in reserves
            if reserve.reserve.wanted_ad_interest_id is not None
        },
        viewer_interest=viewer_interest,
        can_express_interest=(
            wanted_ad.status == "open"
            and viewer.current_character is not None
            and policies.can_story_act_as(viewer.membership, viewer.current_character)
            and viewer_interest is None
            and not is_created_by_viewer
        ),
        can_express_prospective_interest=(
            wanted_ad.status == "open"
            and viewer_prospective_interest is None
            and not is_created_by_viewer
        ),
        is_created_by_viewer=is_created_by_viewer,
        can_manage=can_manage,
        rendered_body=render_prose_body(
            wanted_ad.body,
            mentions=post_mention_links(repo, viewer.community.id),
        ),
        type_label=wanted_type_label(wanted_ad.wanted_type),
        related_ads=related[:4],
    )


def update_wanted_ad_lifecycle_status(
    repo: CastingRepository,
    viewer: ForumView,
    wanted_slug: str,
    *,
    status: str,
) -> WantedAd:
    wanted_ad = repo.get_wanted_ad_by_slug(viewer.community.id, wanted_slug)
    if not can_manage_wanted_ad(viewer, wanted_ad):
        raise PermissionError(
            f"membership {viewer.membership.id} cannot manage wanted hook {wanted_ad.id}"
        )
    normalized_status = status.strip().lower()
    if normalized_status not in WANTED_STATUSES:
        allowed = ", ".join(WANTED_STATUSES)
        raise ValueError(f"wanted hook status must be one of: {allowed}")
    if wanted_ad.status == normalized_status:
        return wanted_ad
    return repo.update_wanted_ad_status(viewer.community.id, wanted_ad.id, normalized_status)


def express_wanted_interest(
    repo: CastingRepository,
    viewer: ForumView,
    wanted_slug: str,
) -> WantedAdInterest:
    if viewer.current_character is None:
        raise ValueError("create a character before expressing interest")
    if not policies.can_story_act_as(viewer.membership, viewer.current_character):
        raise PermissionError(
            f"membership {viewer.membership.id} cannot use character {viewer.current_character.id}"
        )
    wanted_ad = repo.get_wanted_ad_by_slug(viewer.community.id, wanted_slug)
    if wanted_ad.status != "open":
        raise ValueError(f"wanted hook {wanted_ad.id} is not open")
    if wanted_ad.creator_membership_id == viewer.membership.id:
        raise ValueError("you cannot express interest in your own wanted hook")
    interest = repo.create_wanted_ad_interest(
        viewer.community.id,
        wanted_ad.id,
        viewer.membership.id,
        viewer.current_character.id,
    )
    if wanted_ad.creator_membership_id != viewer.membership.id:
        repo.create_notification(
            viewer.community.id,
            wanted_ad.creator_membership_id,
            kind="wanted_interest",
            wanted_ad_id=wanted_ad.id,
            wanted_ad_interest_id=interest.id,
            actor_membership_id=viewer.membership.id,
            actor_character_id=viewer.current_character.id,
        )
    return interest


def express_prospective_wanted_interest(
    repo: CastingRepository,
    viewer: ForumView,
    wanted_slug: str,
    *,
    prospective_character_name: str,
    note: str = "",
) -> WantedAdInterest:
    wanted_ad = repo.get_wanted_ad_by_slug(viewer.community.id, wanted_slug)
    if wanted_ad.status != "open":
        raise ValueError(f"wanted hook {wanted_ad.id} is not open")
    if wanted_ad.creator_membership_id == viewer.membership.id:
        raise ValueError("you cannot express interest in your own wanted hook")
    cleaned_name = prospective_character_name.strip()
    if not cleaned_name:
        raise ValueError("prospective character concept is required")
    interest = repo.create_wanted_ad_interest(
        viewer.community.id,
        wanted_ad.id,
        viewer.membership.id,
        character_id=None,
        prospective_character_name=cleaned_name,
        note=note.strip(),
    )
    repo.create_notification(
        viewer.community.id,
        wanted_ad.creator_membership_id,
        kind="wanted_interest",
        wanted_ad_id=wanted_ad.id,
        wanted_ad_interest_id=interest.id,
        actor_membership_id=viewer.membership.id,
        actor_character_id=(
            viewer.current_character.id if viewer.current_character is not None else None
        ),
    )
    return interest


def reserve_wanted_interest(
    repo: CastingRepository,
    viewer: ForumView,
    wanted_slug: str,
    interest_id: int,
) -> WantedAdInterest:
    wanted_ad = repo.get_wanted_ad_by_slug(viewer.community.id, wanted_slug)
    if wanted_ad.creator_membership_id != viewer.membership.id and not policies.can_manage_casting(
        viewer.membership,
        viewer.role,
    ):
        raise PermissionError(
            f"membership {viewer.membership.id} cannot manage wanted hook {wanted_ad.id}"
        )
    if wanted_ad.status != "open":
        raise ValueError(f"wanted hook {wanted_ad.id} is not open")
    interest = repo.get_wanted_ad_interest(viewer.community.id, interest_id)
    if interest.wanted_ad_id != wanted_ad.id:
        raise LookupError(f"wanted interest {interest_id} not found for wanted hook {wanted_ad.id}")
    if interest.status != "interested":
        raise ValueError(f"wanted interest {interest.id} is already {interest.status}")
    actor_character_id = wanted_actor_character_id(repo, viewer, wanted_ad)
    reserved = repo.update_wanted_ad_interest_status(
        viewer.community.id,
        interest.id,
        "reserved",
    )
    repo.update_wanted_ad_status(viewer.community.id, wanted_ad.id, "reserved")
    if reserved.membership_id != viewer.membership.id:
        repo.create_notification(
            viewer.community.id,
            reserved.membership_id,
            kind="wanted_reserved",
            wanted_ad_id=wanted_ad.id,
            wanted_ad_interest_id=reserved.id,
            actor_membership_id=viewer.membership.id,
            actor_character_id=actor_character_id,
        )
    return reserved


def create_reserve_for_wanted_interest(
    repo: CastingRepository,
    viewer: ForumView,
    wanted_slug: str,
    interest_id: int,
) -> CharacterReserve:
    wanted_ad = repo.get_wanted_ad_by_slug(viewer.community.id, wanted_slug)
    if wanted_ad.creator_membership_id != viewer.membership.id and not policies.can_manage_casting(
        viewer.membership,
        viewer.role,
    ):
        raise PermissionError(
            f"membership {viewer.membership.id} cannot manage wanted hook {wanted_ad.id}"
        )
    if wanted_ad.status != "reserved":
        raise ValueError(f"wanted hook {wanted_ad.id} is not reserved")
    interest = repo.get_wanted_ad_interest(viewer.community.id, interest_id)
    if interest.wanted_ad_id != wanted_ad.id:
        raise LookupError(f"wanted interest {interest_id} not found for wanted hook {wanted_ad.id}")
    if interest.status != "reserved":
        raise ValueError(f"wanted interest {interest.id} is not reserved")
    if interest.character_id is None:
        raise ValueError("create a character before creating a reserve")
    reserve = repo.create_character_reserve(
        viewer.community.id,
        interest.membership_id,
        interest.character_id,
        wanted_ad.title,
        wanted_ad_id=wanted_ad.id,
        wanted_ad_interest_id=interest.id,
        reserve_type="wanted",
        notes=f"Reserved from wanted hook: {wanted_ad.title}",
    )
    actor_character_id = wanted_actor_character_id(repo, viewer, wanted_ad)
    if reserve.membership_id != viewer.membership.id:
        repo.create_notification(
            viewer.community.id,
            reserve.membership_id,
            kind="reserve_created",
            wanted_ad_id=wanted_ad.id,
            wanted_ad_interest_id=interest.id,
            actor_membership_id=viewer.membership.id,
            actor_character_id=actor_character_id,
        )
    return reserve


def wanted_ad_summary(
    repo: CastingReadRepository,
    community_id: int,
    wanted_ad: WantedAd,
) -> WantedAdSummary:
    return WantedAdSummary(
        wanted_ad=wanted_ad,
        creator_membership=repo.get_membership(community_id, wanted_ad.creator_membership_id),
        creator_character=(
            repo.get_character(community_id, wanted_ad.creator_character_id)
            if wanted_ad.creator_character_id is not None
            else None
        ),
        related_material=(
            repo.get_material(community_id, wanted_ad.related_material_id)
            if wanted_ad.related_material_id is not None
            else None
        ),
        related_characters=repo.list_wanted_ad_related_characters(community_id, wanted_ad.id),
        facets=facet_tags(
            repo,
            community_id,
            repo.list_wanted_ad_facets(community_id, wanted_ad.id),
        ),
        type_label=wanted_type_label(wanted_ad.wanted_type),
    )


def wanted_ad_interest_view(
    repo: CastingReadRepository,
    community_id: int,
    interest: WantedAdInterest,
) -> WantedAdInterestView:
    return WantedAdInterestView(
        interest=interest,
        membership=repo.get_membership(community_id, interest.membership_id),
        character=(
            repo.get_character(community_id, interest.character_id)
            if interest.character_id is not None
            else None
        ),
        created_at_label=timestamp_label(interest.created_at),
    )


def wanted_ad_interest_detail_item(
    repo: CastingReadRepository,
    viewer: ForumView,
    interest: WantedAdInterest,
    *,
    can_manage: bool,
) -> WantedAdInterestDetailItem:
    room = wanted_interest_room(repo, viewer.community.id, interest.id)
    is_interested_writer = interest.membership_id == viewer.membership.id
    thread_href = wanted_interest_thread_href(repo, viewer.community.id, room)
    stage_label, stage_variant = wanted_interest_stage(interest, room)
    show_room_link = room is not None and (can_manage or is_interested_writer)
    primary_label, primary_href, secondary_label, secondary_href = wanted_interest_action(
        room,
        thread_href=thread_href,
        show_room_link=show_room_link,
    )
    return WantedAdInterestDetailItem(
        view=wanted_ad_interest_view(repo, viewer.community.id, interest),
        room=room,
        room_id=room.id if room is not None else None,
        room_status=room.status if room is not None else "",
        can_view_note=can_manage or is_interested_writer,
        can_manage=can_manage,
        can_open_room=show_room_link,
        show_room_link=show_room_link,
        stage_label=stage_label,
        stage_variant=stage_variant,
        thread_href=thread_href,
        primary_action_label=primary_label,
        primary_action_href=primary_href,
        secondary_action_label=secondary_label,
        secondary_action_href=secondary_href,
    )


def wanted_interest_room(
    repo: CastingReadRepository,
    community_id: int,
    interest_id: int,
) -> PlottingRoom | None:
    try:
        return repo.get_plotting_room_for_wanted_interest(community_id, interest_id)
    except LookupError:
        return None


def wanted_interest_thread_href(
    repo: CastingReadRepository,
    community_id: int,
    room: PlottingRoom | None,
) -> str | None:
    if room is None or room.target_thread_id is None:
        return None
    thread = repo.get_thread(community_id, room.target_thread_id)
    board = repo.get_board(community_id, thread.board_id)
    return f"/boards/{board.slug}/threads/{thread.slug}"


def wanted_interest_stage(
    interest: WantedAdInterest,
    room: PlottingRoom | None,
) -> tuple[str, str]:
    if interest.status == "reserved":
        return ("Reserved", "warning")
    if room is None:
        return ("Raised hand", "info")
    if room.status == "threaded" or room.target_thread_id is not None:
        return ("Scene started", "success")
    if room.status == "ready":
        return ("Ready for scene", "success")
    if room.status == "paused":
        return ("Waiting", "muted")
    return ("In plotting", "info")


def wanted_interest_action(
    room: PlottingRoom | None,
    *,
    thread_href: str | None,
    show_room_link: bool,
) -> tuple[str, str, str, str]:
    if room is None or not show_room_link:
        return ("", "", "", "")
    room_href = f"/plotting/{room.id}"
    if thread_href is not None:
        return ("Open scene", thread_href, "Open plotting room", room_href)
    if room.status == "ready":
        return ("Ready for scene", room_href, "", "")
    return ("Open plotting room", room_href, "", "")


def character_reserve_view(
    repo: CastingReadRepository,
    community_id: int,
    reserve: CharacterReserve,
) -> CharacterReserveView:
    return CharacterReserveView(
        reserve=reserve,
        membership=repo.get_membership(community_id, reserve.membership_id),
        character=repo.get_character(community_id, reserve.character_id),
        wanted_ad=(
            repo.get_wanted_ad(community_id, reserve.wanted_ad_id)
            if reserve.wanted_ad_id is not None
            else None
        ),
        created_at_label=timestamp_label(reserve.created_at),
    )


def can_manage_wanted_ad(viewer: ForumView, wanted_ad: WantedAd) -> bool:
    return wanted_ad.creator_membership_id == viewer.membership.id or policies.can_manage_casting(
        viewer.membership,
        viewer.role,
    )


def wanted_actor_character_id(
    repo: CastingRepository,
    viewer: ForumView,
    wanted_ad: WantedAd,
) -> int:
    if (
        viewer.current_character is not None
        and viewer.current_character.membership_id == viewer.membership.id
    ):
        return viewer.current_character.id
    if wanted_ad.creator_character_id is not None:
        creator_character = repo.get_character(viewer.community.id, wanted_ad.creator_character_id)
        if creator_character.membership_id == viewer.membership.id:
            return creator_character.id
    roster = repo.list_characters(viewer.community.id, viewer.membership.id)
    if roster:
        return roster[0].id
    raise ValueError("create a character before managing wanted hooks")
