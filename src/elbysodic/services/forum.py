"""Service-layer commands and read models for the forum slice."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import cast

from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.db.seed import DemoSeed, seed_demo_forum
from elbysodic.domain.boards import is_community_board, is_location_board
from elbysodic.domain.models import (
    Board,
    Character,
    CharacterReserve,
    CommunityMembership,
    Material,
    Notification,
    Post,
    Role,
    Thread,
    WantedAd,
    WantedAdInterest,
)
from elbysodic.services import policies
from elbysodic.services.facets import (
    clean_facet_slugs as _clean_facet_slugs,
)
from elbysodic.services.facets import (
    current_character_facet_ids as _current_character_facet_ids,
)
from elbysodic.services.facets import (
    current_character_facet_tags as _current_character_facet_tags,
)
from elbysodic.services.facets import (
    facet_filter_groups as _facet_filter_groups,
)
from elbysodic.services.facets import (
    facet_tags as _facet_tags,
)
from elbysodic.services.facets import (
    resolve_facets as _resolve_facets,
)
from elbysodic.services.markup import post_snippet, render_post_body
from elbysodic.services.materials import (
    current_event_for_facet_ids as _current_event_for_facet_ids,
)
from elbysodic.services.materials import material_detail as _material_detail
from elbysodic.services.materials import material_summary as _material_summary
from elbysodic.services.posts import post_mention_links as _post_mention_links
from elbysodic.services.posts import post_revision_view as _post_revision_view
from elbysodic.services.posts import post_view as _post_view
from elbysodic.services.read_models import (
    APPLICATION_STATUS_LABELS,
    APPLICATION_STATUS_VARIANTS,
    MATERIAL_STATUSES,
    MATERIAL_TYPES,
    ActivityItem,
    ApplicationCharacterView,
    ApplicationsDesk,
    AttentionItem,
    BoardNavigationItem,
    BoardSummary,
    BoardThreadFilter,
    CastingDesk,
    CastingWantedItem,
    CharacterAppearance,
    CharacterProfile,
    CharacterReserveView,
    CharacterRosterCard,
    CharacterRosterDashboard,
    CharacterThreadActivity,
    CreatedThread,
    DirectorStudio,
    DiscoveryCharacterResult,
    DiscoveryThreadResult,
    EditablePostView,
    FacetTag,
    ForumView,
    LocationNavigationGroup,
    MaterialDetail,
    MaterialSummary,
    MemberDirectory,
    MemberDirectoryCard,
    MemberProfile,
    Mentionable,
    MentionableScope,
    MyThreadsDashboard,
    NotificationInbox,
    NotificationItem,
    PlotDiscovery,
    PostRevisionHistory,
    ThreadNavigationItem,
    ThreadSummary,
    ThreadView,
    WantedAdDetail,
    WantedAdInterestView,
    WantedAdSummary,
    WantedBoard,
    WorldHub,
    WriterCollaborator,
)
from elbysodic.services.read_models import (
    POSTING_MODES as POSTING_MODES,
)
from elbysodic.services.read_models import (
    THREAD_STATUSES as THREAD_STATUSES,
)
from elbysodic.services.threads import (
    board_thread_summaries as _board_thread_summaries,
)
from elbysodic.services.threads import clean_participant_ids as _clean_participant_ids
from elbysodic.services.threads import clean_posting_mode as _clean_posting_mode
from elbysodic.services.threads import clean_thread_status as _clean_thread_status
from elbysodic.services.threads import is_live_queue_thread as _is_live_queue_thread
from elbysodic.services.threads import is_unread as _is_unread
from elbysodic.services.threads import next_unread_thread as _next_unread_thread
from elbysodic.services.threads import read_thread_view as _read_thread_view
from elbysodic.services.threads import taggable_characters
from elbysodic.services.threads import thread_needs_attention as _thread_needs_attention
from elbysodic.services.threads import thread_obligations as _thread_obligations
from elbysodic.services.timestamps import timestamp_key as _timestamp_key
from elbysodic.services.timestamps import timestamp_label as _timestamp_label

DEFAULT_DATABASE_PATH = Path("var/elbysodic.sqlite3")
DATABASE_PATH_ENV = "ELBYSODIC_DB_PATH"


class AppServices:
    """Small application service facade for the dev forum."""

    def __init__(self, repo: ForumRepository, seed: DemoSeed) -> None:
        self.repo = repo
        self.seed = seed

    def viewer(self) -> ForumView:
        community = self.seed.community
        membership = self.repo.get_membership(community.id, self.seed.membership.id)
        role = self.repo.get_role(community.id, membership.role_id)
        roster = self.repo.list_characters(community.id, membership.id)
        current_character = _resolve_current_character(self.repo, membership, roster)
        navigation_boards = _board_navigation(self.repo, community.id, membership, role)
        return ForumView(
            community=community,
            membership=membership,
            role=role,
            current_character=current_character,
            roster=roster,
            navigation_boards=navigation_boards,
            location_navigation_boards=[
                item
                for item in navigation_boards
                if item.board.parent_board_id is None and is_location_board(item.board)
            ],
            location_navigation_groups=_location_navigation_groups(navigation_boards),
            community_navigation_boards=[
                item
                for item in navigation_boards
                if item.board.parent_board_id is None and is_community_board(item.board)
            ],
            unread_notification_count=self.repo.count_unread_notifications(
                community.id, membership.id
            ),
        )

    def list_boards(self) -> list[BoardSummary]:
        viewer = self.viewer()
        current_facet_ids = _current_character_facet_ids(self.repo, viewer)
        summaries: list[BoardSummary] = []
        for board in self.repo.list_boards(viewer.community.id):
            if not policies.can_view_board(viewer.membership, board, viewer.role):
                continue
            summaries.append(_board_summary(self.repo, viewer, board, current_facet_ids))
        return summaries

    def child_board_summaries(self, board: Board) -> list[BoardSummary]:
        viewer = self.viewer()
        current_facet_ids = _current_character_facet_ids(self.repo, viewer)
        return [
            _board_summary(self.repo, viewer, child, current_facet_ids)
            for child in self.repo.list_child_boards(viewer.community.id, board.id)
            if policies.can_view_board(viewer.membership, child, viewer.role)
        ]

    def sibling_board_summaries(self, board: Board) -> list[BoardSummary]:
        viewer = self.viewer()
        current_facet_ids = _current_character_facet_ids(self.repo, viewer)
        siblings = self.repo.list_child_boards(viewer.community.id, board.parent_board_id)
        return [
            _board_summary(self.repo, viewer, sibling, current_facet_ids)
            for sibling in siblings
            if sibling.id != board.id
            and is_location_board(sibling)
            and policies.can_view_board(viewer.membership, sibling, viewer.role)
        ]

    def board_summary(self, board: Board) -> BoardSummary:
        viewer = self.viewer()
        return _board_summary(
            self.repo,
            viewer,
            board,
            _current_character_facet_ids(self.repo, viewer),
        )

    def parent_board(self, board: Board) -> Board | None:
        if board.parent_board_id is None:
            return None
        viewer = self.viewer()
        parent = self.repo.get_board(viewer.community.id, board.parent_board_id)
        if not policies.can_view_board(viewer.membership, parent, viewer.role):
            return None
        return parent

    def recent_activity(self, *, limit: int = 6) -> list[ActivityItem]:
        viewer = self.viewer()
        visible_boards = {
            board.id: board
            for board in self.repo.list_boards(viewer.community.id)
            if policies.can_view_board(viewer.membership, board, viewer.role)
        }
        items: list[ActivityItem] = []
        for thread in self.repo.list_threads(viewer.community.id):
            board = visible_boards.get(thread.board_id)
            if board is None:
                continue
            for post in self.repo.list_posts(viewer.community.id, thread.id):
                post_view = _post_view(self.repo, viewer.community.id, post)
                items.append(
                    ActivityItem(
                        board=board,
                        thread=thread,
                        post=post_view,
                        snippet=post_view.snippet,
                        is_unread=_is_unread(
                            self.repo,
                            viewer.community.id,
                            viewer.membership.id,
                            thread,
                        ),
                    )
                )
        return sorted(
            items,
            key=lambda item: (_timestamp_key(item.post.post.created_at), item.post.post.id),
            reverse=True,
        )[:limit]

    def needs_attention(self, *, limit: int = 5) -> list[AttentionItem]:
        viewer = self.viewer()
        roster_character_ids = {character.id for character in viewer.roster}
        visible_boards = {
            board.id: board
            for board in self.repo.list_boards(viewer.community.id)
            if policies.can_view_board(viewer.membership, board, viewer.role)
        }
        items: list[AttentionItem] = []
        for thread in self.repo.list_threads(viewer.community.id):
            board = visible_boards.get(thread.board_id)
            if board is None:
                continue
            if not _is_live_queue_thread(thread):
                continue
            posts = self.repo.list_posts(viewer.community.id, thread.id)
            latest_post = posts[-1] if posts else None
            if latest_post is None:
                continue
            if not _thread_needs_attention(
                self.repo,
                viewer.community.id,
                viewer.membership.id,
                thread,
                latest_post,
                roster_character_ids,
            ):
                continue
            items.append(
                AttentionItem(
                    board=board,
                    thread=thread,
                    latest_post=_post_view(self.repo, viewer.community.id, latest_post),
                    reply_count=max(0, len(posts) - 1),
                    snippet=post_snippet(latest_post.body),
                )
            )
        return sorted(
            items,
            key=lambda item: (
                _timestamp_key(item.latest_post.post.created_at),
                item.latest_post.post.id,
            ),
            reverse=True,
        )[:limit]

    def my_threads(self, *, character_slug: str | None = None) -> MyThreadsDashboard:
        viewer = self.viewer()
        selected_character = self._selected_character(viewer, character_slug)
        target_ids = (
            {selected_character.id}
            if selected_character is not None
            else {character.id for character in viewer.roster}
        )
        sorted_items = _thread_obligations(self.repo, viewer, target_ids)
        return MyThreadsDashboard(
            needs_reply=[item for item in sorted_items if item.needs_reply],
            waiting_on_others=[item for item in sorted_items if item.waiting_on_others],
            started_by_me=[item for item in sorted_items if item.is_started_by_roster],
            participated=sorted_items,
            selected_character=selected_character,
            roster_activity=self._roster_activity(viewer),
        )

    def character_roster(self) -> CharacterRosterDashboard:
        viewer = self.viewer()
        return CharacterRosterDashboard(
            cards=[
                CharacterRosterCard(
                    character=character,
                    is_default=viewer.membership.default_character_id == character.id,
                    activity=self._character_activity(viewer, character),
                    application_status_label=_application_status_label(
                        character.application_status
                    ),
                    application_status_variant=_application_status_variant(
                        character.application_status
                    ),
                )
                for character in viewer.roster
            ]
        )

    def applications_desk(self) -> ApplicationsDesk:
        viewer = self.viewer()
        characters = self.repo.list_community_characters(viewer.community.id)
        character_views = [
            _application_character_view(self.repo, viewer, character) for character in characters
        ]
        materials = [
            _material_summary(self.repo, viewer.community.id, material)
            for material in self.repo.list_materials(viewer.community.id)
            if material.material_type == "application"
        ]
        return ApplicationsDesk(
            my_applications=[
                item
                for item in character_views
                if item.character.membership_id == viewer.membership.id
            ],
            review_queue=(
                [
                    item
                    for item in character_views
                    if item.character.application_status == "submitted"
                ]
                if viewer.role.is_admin
                else []
            ),
            accepted_characters=[
                item for item in character_views if item.character.application_status == "accepted"
            ],
            application_materials=materials,
            can_review=viewer.role.is_admin,
        )

    def members_directory(self) -> MemberDirectory:
        viewer = self.viewer()
        cards = [
            self._member_directory_card(viewer, membership)
            for membership in self.repo.list_memberships(viewer.community.id)
            if membership.is_active
        ]
        return MemberDirectory(cards=cards)

    def read_member(self, username: str) -> MemberProfile:
        viewer = self.viewer()
        membership = self.repo.get_membership_by_username(viewer.community.id, username)
        if not membership.is_active:
            raise LookupError(
                f"membership not found in community {viewer.community.id}: {username}"
            )
        roster = self.repo.list_characters(viewer.community.id, membership.id)
        roster_ids = {character.id for character in roster}
        active_threads = _thread_obligations(self.repo, viewer, roster_ids)
        recent_posts = _recent_character_posts(
            self.repo,
            viewer,
            roster_ids,
            limit=8,
        )
        return MemberProfile(
            membership=membership,
            role=self.repo.get_role(viewer.community.id, membership.role_id),
            roster=roster,
            default_character=_default_character(roster, membership.default_character_id),
            known_for=_known_for_characters(self.repo, viewer, roster, limit=3),
            collaborators=_writer_collaborators(
                self.repo,
                viewer,
                membership,
                roster_ids,
                limit=4,
            ),
            visible_post_count=len(_visible_character_posts(self.repo, viewer, roster_ids)),
            visible_thread_count=len(active_threads),
            active_threads=active_threads,
            started_threads=[item for item in active_threads if item.is_started_by_roster],
            recent_posts=recent_posts,
            is_current_member=membership.id == viewer.membership.id,
        )

    def board_threads(
        self,
        board_slug: str,
        *,
        filter_by: BoardThreadFilter = "all",
    ) -> tuple[Board, list[ThreadSummary]]:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        return board, _board_thread_summaries(
            self.repo,
            viewer,
            board,
            filter_by=filter_by,
        )

    def next_unread_thread(self, board_slug: str) -> ThreadNavigationItem | None:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        return _next_unread_thread(self.repo, viewer, board)

    def can_start_thread(self, board: Board) -> bool:
        viewer = self.viewer()
        return policies.can_start_thread(viewer.membership, board, viewer.role)

    def board_facets(self, board_slug: str) -> list[FacetTag]:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        return _facet_tags(
            self.repo,
            viewer.community.id,
            self.repo.list_board_facets(viewer.community.id, board.id),
        )

    def read_thread(self, board_slug: str, thread_slug: str) -> ThreadView:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        thread_view = _read_thread_view(self.repo, viewer, board, thread)
        self.repo.mark_thread_read(viewer.community.id, thread.id, viewer.membership.id)
        return thread_view

    def watch_thread(self, board_slug: str, thread_slug: str) -> None:
        viewer = self.viewer()
        _board, thread = self._visible_thread(viewer, board_slug, thread_slug)
        self.repo.watch_thread(viewer.community.id, thread.id, viewer.membership.id)

    def unwatch_thread(self, board_slug: str, thread_slug: str) -> None:
        viewer = self.viewer()
        _board, thread = self._visible_thread(viewer, board_slug, thread_slug)
        self.repo.unwatch_thread(viewer.community.id, thread.id, viewer.membership.id)

    def join_thread_as_current_character(self, board_slug: str, thread_slug: str) -> None:
        viewer = self.viewer()
        if viewer.current_character is None:
            raise ValueError("create a character before joining a scene")
        _board, thread = self._visible_thread(viewer, board_slug, thread_slug)
        if thread.status != "open" or thread.is_locked:
            raise PermissionError(f"thread {thread.id} is not open to join")
        if not policies.can_reply(viewer.membership, thread, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot join thread {thread.id}"
            )
        if not policies.can_post_as(viewer.membership, viewer.current_character):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot use character {viewer.current_character.id}"
            )
        self.repo.add_thread_participant(
            viewer.community.id,
            thread.id,
            viewer.current_character.id,
        )
        self.repo.watch_thread(viewer.community.id, thread.id, viewer.membership.id)

    def discover_plots(self, *, facet_slugs: list[str] | None = None) -> PlotDiscovery:
        viewer = self.viewer()
        active_face_facets = _current_character_facet_tags(self.repo, viewer)
        requested_slugs = _clean_facet_slugs(facet_slugs or [])
        used_active_face_lens = False
        if not requested_slugs and active_face_facets:
            requested_slugs = [
                tag.facet.slug
                for tag in active_face_facets
                if tag.group.slug in {"species", "affiliation", "location"}
            ][:3]
            used_active_face_lens = bool(requested_slugs)
        selected_facets = _resolve_facets(self.repo, viewer.community.id, requested_slugs)
        requested_slugs = [facet.slug for facet in selected_facets]
        selected_ids = [facet.id for facet in selected_facets]
        selected_tags = _facet_tags(self.repo, viewer.community.id, selected_facets)
        character_ids = (
            self.repo.list_character_ids_for_facets(viewer.community.id, selected_ids)
            if selected_ids
            else {
                character.id
                for character in self.repo.list_community_characters(viewer.community.id)
            }
        )
        thread_ids = (
            self.repo.list_thread_ids_for_facets(viewer.community.id, selected_ids)
            if selected_ids
            else {thread.id for thread in self.repo.list_threads(viewer.community.id)}
        )
        return PlotDiscovery(
            selected_facets=selected_tags,
            active_face_facets=active_face_facets,
            filter_groups=_facet_filter_groups(
                self.repo,
                viewer.community.id,
                requested_slugs,
            ),
            characters=_discovery_characters(
                self.repo,
                viewer,
                character_ids,
                selected_ids,
            ),
            open_threads=_discovery_open_threads(
                self.repo,
                viewer,
                thread_ids,
                selected_ids,
            ),
            used_active_face_lens=used_active_face_lens,
        )

    def world_hub(self) -> WorldHub:
        viewer = self.viewer()
        materials = [
            _material_summary(self.repo, viewer.community.id, material)
            for material in self.repo.list_materials(viewer.community.id)
        ]
        additional_materials = [item for item in materials if not item.material.is_featured]
        return WorldHub(
            featured=[item for item in materials if item.material.is_featured],
            guides=[
                item
                for item in additional_materials
                if item.material.material_type in {"premise", "guide", "factions"}
            ],
            events=[item for item in materials if item.material.material_type == "event"],
            application_materials=[
                item
                for item in additional_materials
                if item.material.material_type == "application"
            ],
            can_manage=viewer.role.is_admin,
        )

    def director_studio(self) -> DirectorStudio:
        viewer = self.viewer()
        material_status = None if viewer.role.is_admin else "published"
        materials = [
            _material_summary(self.repo, viewer.community.id, material)
            for material in self.repo.list_materials(
                viewer.community.id,
                status=material_status,
            )
        ]
        board_summaries = self.list_boards()
        location_boards = [
            item
            for item in board_summaries
            if item.board.parent_board_id is None and item.board.board_kind == "location"
        ]
        sublocation_boards = [
            item for item in board_summaries if item.board.board_kind == "sublocation"
        ]
        wanted_status = None if viewer.role.is_admin else "open"
        wanted_ads = [
            _wanted_ad_summary(self.repo, viewer.community.id, wanted_ad)
            for wanted_ad in self.repo.list_wanted_ads(
                viewer.community.id,
                status=wanted_status,
            )
        ]
        events = [item for item in materials if item.material.material_type == "event"]
        current_event = next((item for item in events if item.material.is_featured), None)
        if current_event is None:
            current_event = events[0] if events else None
        return DirectorStudio(
            can_manage=viewer.role.is_admin,
            materials=materials,
            draft_materials=[item for item in materials if item.material.status == "draft"],
            featured_materials=[item for item in materials if item.material.is_featured],
            events=events,
            current_event=current_event,
            application_materials=[
                item for item in materials if item.material.material_type == "application"
            ],
            location_boards=location_boards,
            sublocation_boards=sublocation_boards,
            wanted_ads=wanted_ads,
            open_wanted_ads=[item for item in wanted_ads if item.wanted_ad.status == "open"],
            applications=self.applications_desk(),
        )

    def read_material(self, material_slug: str) -> MaterialDetail:
        viewer = self.viewer()
        material = self.repo.get_material_by_slug(viewer.community.id, material_slug)
        if material.status != "published" and not viewer.role.is_admin:
            raise LookupError(
                f"material not found in community {viewer.community.id}: {material_slug}"
            )
        return _material_detail(
            self.repo,
            viewer,
            material,
            board_summary_factory=lambda board: _board_summary(
                self.repo,
                viewer,
                board,
                _current_character_facet_ids(self.repo, viewer),
            ),
            wanted_summary_factory=lambda wanted_ad: _wanted_ad_summary(
                self.repo,
                viewer.community.id,
                wanted_ad,
            ),
        )

    def current_event_for_board(self, board: Board) -> MaterialSummary | None:
        viewer = self.viewer()
        facet_ids = {
            facet.id for facet in self.repo.list_board_facets(viewer.community.id, board.id)
        }
        return _current_event_for_facet_ids(self.repo, viewer.community.id, facet_ids)

    def current_event_for_thread(self, thread: Thread, board: Board) -> MaterialSummary | None:
        viewer = self.viewer()
        facet_ids = {
            facet.id for facet in self.repo.list_thread_facets(viewer.community.id, thread.id)
        }
        facet_ids.update(
            facet.id for facet in self.repo.list_board_facets(viewer.community.id, board.id)
        )
        return _current_event_for_facet_ids(self.repo, viewer.community.id, facet_ids)

    def update_material(
        self,
        material_slug: str,
        *,
        title: str,
        material_type: str,
        summary: str,
        body: str,
        status: str = "published",
        is_featured: bool = False,
    ) -> Material:
        viewer = self.viewer()
        if not viewer.role.is_admin:
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage world materials"
            )
        material = self.repo.get_material_by_slug(viewer.community.id, material_slug)
        cleaned_title = title.strip()
        cleaned_material_type = material_type.strip()
        cleaned_status = status.strip()
        if not cleaned_title:
            raise ValueError("material title is required")
        if cleaned_material_type not in MATERIAL_TYPES:
            raise ValueError("choose a supported material type")
        if cleaned_status not in MATERIAL_STATUSES:
            raise ValueError("choose a supported material status")
        return self.repo.update_material(
            viewer.community.id,
            material.id,
            title=cleaned_title,
            material_type=cleaned_material_type,
            summary=summary.strip(),
            body=body.strip(),
            status=cleaned_status,
            sort_order=material.sort_order,
            is_featured=is_featured,
        )

    def wanted_ads(self) -> WantedBoard:
        viewer = self.viewer()
        return WantedBoard(
            open_ads=[
                _wanted_ad_summary(self.repo, viewer.community.id, wanted_ad)
                for wanted_ad in self.repo.list_wanted_ads(viewer.community.id)
            ]
        )

    def casting_desk(self) -> CastingDesk:
        viewer = self.viewer()
        active_reserves = [
            _character_reserve_view(self.repo, viewer.community.id, reserve)
            for reserve in self.repo.list_character_reserves_for_community(viewer.community.id)
        ]
        wanted_with_interest: list[CastingWantedItem] = []
        for wanted_ad in self.repo.list_wanted_ads(viewer.community.id, status=None):
            if wanted_ad.status == "archived":
                continue
            interests = [
                _wanted_ad_interest_view(self.repo, viewer.community.id, interest)
                for interest in self.repo.list_wanted_ad_interests(
                    viewer.community.id,
                    wanted_ad.id,
                )
            ]
            reserves = [
                reserve
                for reserve in active_reserves
                if reserve.reserve.wanted_ad_id == wanted_ad.id
            ]
            if not interests and not reserves:
                continue
            wanted_with_interest.append(
                CastingWantedItem(
                    wanted_ad=_wanted_ad_summary(self.repo, viewer.community.id, wanted_ad),
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

    def read_wanted_ad(self, wanted_slug: str) -> WantedAdDetail:
        viewer = self.viewer()
        wanted_ad = self.repo.get_wanted_ad_by_slug(viewer.community.id, wanted_slug)
        if wanted_ad.status == "archived":
            raise LookupError(
                f"wanted ad not found in community {viewer.community.id}: {wanted_slug}"
            )
        facets = _facet_tags(
            self.repo,
            viewer.community.id,
            self.repo.list_wanted_ad_facets(viewer.community.id, wanted_ad.id),
        )
        facet_ids = {tag.facet.id for tag in facets}
        related = []
        for candidate in self.repo.list_wanted_ads(viewer.community.id):
            if candidate.id == wanted_ad.id:
                continue
            candidate_facets = _facet_tags(
                self.repo,
                viewer.community.id,
                self.repo.list_wanted_ad_facets(viewer.community.id, candidate.id),
            )
            if facet_ids and not facet_ids.intersection({tag.facet.id for tag in candidate_facets}):
                continue
            related.append(_wanted_ad_summary(self.repo, viewer.community.id, candidate))
        interests = [
            _wanted_ad_interest_view(self.repo, viewer.community.id, interest)
            for interest in self.repo.list_wanted_ad_interests(viewer.community.id, wanted_ad.id)
        ]
        reserves = [
            _character_reserve_view(self.repo, viewer.community.id, reserve)
            for reserve in self.repo.list_character_reserves_for_wanted_ad(
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
                    if interest.interest.character_id == viewer.current_character.id
                ),
                None,
            )
        is_created_by_viewer = wanted_ad.creator_membership_id == viewer.membership.id
        return WantedAdDetail(
            wanted_ad=wanted_ad,
            creator_membership=self.repo.get_membership(
                viewer.community.id,
                wanted_ad.creator_membership_id,
            ),
            creator_character=(
                self.repo.get_character(viewer.community.id, wanted_ad.creator_character_id)
                if wanted_ad.creator_character_id is not None
                else None
            ),
            related_material=(
                self.repo.get_material(viewer.community.id, wanted_ad.related_material_id)
                if wanted_ad.related_material_id is not None
                else None
            ),
            related_characters=self.repo.list_wanted_ad_related_characters(
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
                and viewer_interest is None
                and not is_created_by_viewer
            ),
            is_created_by_viewer=is_created_by_viewer,
            can_manage=is_created_by_viewer or viewer.role.is_admin,
            rendered_body=render_post_body(
                wanted_ad.body,
                mentions=_post_mention_links(self.repo, viewer.community.id),
            ),
            type_label=_wanted_type_label(wanted_ad.wanted_type),
            related_ads=related[:4],
        )

    def express_wanted_interest(self, wanted_slug: str) -> WantedAdInterest:
        viewer = self.viewer()
        if viewer.current_character is None:
            raise ValueError("create a character before expressing interest")
        wanted_ad = self.repo.get_wanted_ad_by_slug(viewer.community.id, wanted_slug)
        if wanted_ad.status != "open":
            raise ValueError(f"wanted hook {wanted_ad.id} is not open")
        if wanted_ad.creator_membership_id == viewer.membership.id:
            raise ValueError("you cannot express interest in your own wanted hook")
        interest = self.repo.create_wanted_ad_interest(
            viewer.community.id,
            wanted_ad.id,
            viewer.membership.id,
            viewer.current_character.id,
        )
        if wanted_ad.creator_membership_id != viewer.membership.id:
            self.repo.create_notification(
                viewer.community.id,
                wanted_ad.creator_membership_id,
                kind="wanted_interest",
                wanted_ad_id=wanted_ad.id,
                wanted_ad_interest_id=interest.id,
                actor_membership_id=viewer.membership.id,
                actor_character_id=viewer.current_character.id,
            )
        return interest

    def reserve_wanted_interest(
        self,
        wanted_slug: str,
        interest_id: int,
    ) -> WantedAdInterest:
        viewer = self.viewer()
        wanted_ad = self.repo.get_wanted_ad_by_slug(viewer.community.id, wanted_slug)
        if wanted_ad.creator_membership_id != viewer.membership.id and not viewer.role.is_admin:
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage wanted hook {wanted_ad.id}"
            )
        if wanted_ad.status != "open":
            raise ValueError(f"wanted hook {wanted_ad.id} is not open")
        interest = self.repo.get_wanted_ad_interest(viewer.community.id, interest_id)
        if interest.wanted_ad_id != wanted_ad.id:
            raise LookupError(
                f"wanted interest {interest_id} not found for wanted hook {wanted_ad.id}"
            )
        if interest.status != "interested":
            raise ValueError(f"wanted interest {interest.id} is already {interest.status}")
        actor_character_id = _wanted_actor_character_id(self.repo, viewer, wanted_ad)
        reserved = self.repo.update_wanted_ad_interest_status(
            viewer.community.id,
            interest.id,
            "reserved",
        )
        self.repo.update_wanted_ad_status(viewer.community.id, wanted_ad.id, "reserved")
        if reserved.membership_id != viewer.membership.id:
            self.repo.create_notification(
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
        self,
        wanted_slug: str,
        interest_id: int,
    ) -> CharacterReserve:
        viewer = self.viewer()
        wanted_ad = self.repo.get_wanted_ad_by_slug(viewer.community.id, wanted_slug)
        if wanted_ad.creator_membership_id != viewer.membership.id and not viewer.role.is_admin:
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage wanted hook {wanted_ad.id}"
            )
        if wanted_ad.status != "reserved":
            raise ValueError(f"wanted hook {wanted_ad.id} is not reserved")
        interest = self.repo.get_wanted_ad_interest(viewer.community.id, interest_id)
        if interest.wanted_ad_id != wanted_ad.id:
            raise LookupError(
                f"wanted interest {interest_id} not found for wanted hook {wanted_ad.id}"
            )
        if interest.status != "reserved":
            raise ValueError(f"wanted interest {interest.id} is not reserved")
        reserve = self.repo.create_character_reserve(
            viewer.community.id,
            interest.membership_id,
            interest.character_id,
            wanted_ad.title,
            wanted_ad_id=wanted_ad.id,
            wanted_ad_interest_id=interest.id,
            reserve_type="wanted",
            notes=f"Reserved from wanted hook: {wanted_ad.title}",
        )
        actor_character_id = _wanted_actor_character_id(self.repo, viewer, wanted_ad)
        if reserve.membership_id != viewer.membership.id:
            self.repo.create_notification(
                viewer.community.id,
                reserve.membership_id,
                kind="reserve_created",
                wanted_ad_id=wanted_ad.id,
                wanted_ad_interest_id=interest.id,
                actor_membership_id=viewer.membership.id,
                actor_character_id=actor_character_id,
            )
        return reserve

    def notifications(self, *, limit: int = 50) -> NotificationInbox:
        viewer = self.viewer()
        items: list[NotificationItem] = []
        for notification in self.repo.list_notifications(
            viewer.community.id,
            viewer.membership.id,
            limit=limit,
        ):
            item = _notification_item(self.repo, viewer, notification)
            if item is not None:
                items.append(item)
        return NotificationInbox(
            items=items,
            unread_count=self.repo.count_unread_notifications(
                viewer.community.id,
                viewer.membership.id,
            ),
        )

    def search_mentionables(
        self,
        query: str,
        *,
        scope: str = "all",
        limit: int = 8,
    ) -> list[Mentionable]:
        viewer = self.viewer()
        mention_scope = _clean_mentionable_scope(scope)
        cleaned_query = query.strip().lstrip("@")
        if not cleaned_query:
            return []

        items: list[Mentionable] = []
        if mention_scope in {"all", "cast", "characters"}:
            excluded_memberships = [viewer.membership.id] if mention_scope == "cast" else []
            characters = self.repo.search_characters(
                viewer.community.id,
                cleaned_query,
                limit=limit,
                exclude_membership_ids=excluded_memberships,
            )
            items.extend(_character_mentionable(character) for character in characters)

        remaining = max(0, limit - len(items))
        if remaining and mention_scope in {"all", "writers", "ooc"}:
            memberships = self.repo.search_memberships(
                viewer.community.id,
                cleaned_query,
                limit=remaining,
            )
            items.extend(_membership_mentionable(membership) for membership in memberships)

        return items[:limit]

    def open_notification(self, notification_id: int) -> str:
        viewer = self.viewer()
        notification = self.repo.get_notification(viewer.community.id, notification_id)
        if notification.membership_id != viewer.membership.id:
            raise PermissionError(
                f"membership {viewer.membership.id} cannot read notification {notification.id}"
            )
        item = _notification_item(self.repo, viewer, notification)
        if item is None:
            raise LookupError(f"notification target not found: {notification.id}")
        self.repo.mark_notification_read(viewer.community.id, notification.id)
        return item.href

    def mark_all_notifications_read(self) -> None:
        viewer = self.viewer()
        self.repo.mark_all_notifications_read(viewer.community.id, viewer.membership.id)

    def set_default_character(self, character_id: int) -> ForumView:
        viewer = self.viewer()
        character = self.repo.get_character(viewer.community.id, character_id)
        if not policies.can_post_as(viewer.membership, character):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot use character {character_id}"
            )
        self.repo.set_default_character(viewer.community.id, viewer.membership.id, character_id)
        return self.viewer()

    def submit_character_application(self, character_slug: str) -> Character:
        viewer = self.viewer()
        character = self.repo.get_character_by_slug(viewer.community.id, character_slug)
        if not policies.can_post_as(viewer.membership, character):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot submit character {character.id}"
            )
        if character.application_status not in {"draft", "revision_requested"}:
            raise ValueError(
                f"character {character.id} cannot be submitted from {character.application_status}"
            )
        character = self.repo.update_character_application_status(
            viewer.community.id,
            character.id,
            "submitted",
        )
        self._notify_application_directors(viewer, character)
        return character

    def accept_character_application(self, character_slug: str) -> Character:
        viewer = self.viewer()
        if not viewer.role.is_admin:
            raise PermissionError(f"membership {viewer.membership.id} cannot review applications")
        character = self.repo.get_character_by_slug(viewer.community.id, character_slug)
        if character.application_status != "submitted":
            raise ValueError(
                f"character {character.id} cannot be accepted from {character.application_status}"
            )
        character = self.repo.update_character_application_status(
            viewer.community.id,
            character.id,
            "accepted",
        )
        self._notify_application_owner(viewer, character, "application_accepted")
        return character

    def request_character_application_revision(self, character_slug: str) -> Character:
        viewer = self.viewer()
        if not viewer.role.is_admin:
            raise PermissionError(f"membership {viewer.membership.id} cannot review applications")
        character = self.repo.get_character_by_slug(viewer.community.id, character_slug)
        if character.application_status != "submitted":
            raise ValueError(
                f"character {character.id} cannot be revised from {character.application_status}"
            )
        character = self.repo.update_character_application_status(
            viewer.community.id,
            character.id,
            "revision_requested",
        )
        self._notify_application_owner(viewer, character, "application_revision_requested")
        return character

    def read_character(self, character_slug: str) -> CharacterProfile:
        viewer = self.viewer()
        character = self.repo.get_character_by_slug(viewer.community.id, character_slug)
        owner_membership = self.repo.get_membership(viewer.community.id, character.membership_id)
        can_manage = character.membership_id == viewer.membership.id
        recent_posts = _recent_character_posts(
            self.repo,
            viewer,
            {character.id},
            limit=5,
        )
        activity = self._character_activity(viewer, character)
        return CharacterProfile(
            character=character,
            owner_membership=owner_membership,
            facets=_facet_tags(
                self.repo,
                viewer.community.id,
                self.repo.list_character_facets(viewer.community.id, character.id),
            ),
            wanted_ads=[
                _wanted_ad_summary(self.repo, viewer.community.id, wanted_ad)
                for wanted_ad in self.repo.list_wanted_ads_for_character(
                    viewer.community.id,
                    character.id,
                )
            ],
            reserves=[
                _character_reserve_view(self.repo, viewer.community.id, reserve)
                for reserve in self.repo.list_character_reserves(
                    viewer.community.id,
                    character.id,
                )
            ],
            application_status_label=_application_status_label(character.application_status),
            application_status_variant=_application_status_variant(character.application_status),
            is_default=can_manage and viewer.membership.default_character_id == character.id,
            can_manage=can_manage,
            post_count=len(_visible_character_posts(self.repo, viewer, {character.id})),
            thread_count=len(activity.started_by_character),
            activity=activity,
            recent_posts=recent_posts,
        )

    def read_post_editor(self, board_slug: str, thread_slug: str, post_id: int) -> EditablePostView:
        viewer = self.viewer()
        board, thread, post = self._editable_post(viewer, board_slug, thread_slug, post_id)
        return EditablePostView(
            board=board,
            thread=thread,
            post=_post_view(
                self.repo,
                viewer.community.id,
                post,
                viewer_membership=viewer.membership,
                viewer_role=viewer.role,
            ),
        )

    def read_post_revisions(
        self,
        board_slug: str,
        thread_slug: str,
        post_id: int,
    ) -> PostRevisionHistory:
        viewer = self.viewer()
        board, thread, post = self._editable_post(viewer, board_slug, thread_slug, post_id)
        revisions = [
            _post_revision_view(self.repo, viewer.community.id, revision)
            for revision in self.repo.list_post_revisions(viewer.community.id, post.id)
        ]
        return PostRevisionHistory(
            board=board,
            thread=thread,
            post=_post_view(
                self.repo,
                viewer.community.id,
                post,
                viewer_membership=viewer.membership,
                viewer_role=viewer.role,
            ),
            revisions=revisions,
        )

    def create_character(
        self,
        *,
        name: str,
        summary: str = "",
        avatar_url: str | None = None,
        poster_url: str | None = None,
        poster_alt: str = "",
        tagline: str = "",
        accent_color: str = "",
        make_default: bool = False,
    ) -> Character:
        viewer = self.viewer()
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("character name is required")
        cleaned_summary = summary.strip()
        cleaned_avatar_url = (avatar_url or "").strip() or None
        cleaned_poster_url = (poster_url or "").strip() or None
        cleaned_poster_alt = poster_alt.strip()
        cleaned_tagline = tagline.strip()
        cleaned_accent_color = accent_color.strip()
        slug = _unique_character_slug(self.repo, viewer.community.id, cleaned_name)
        return self.repo.create_character(
            viewer.community.id,
            viewer.membership.id,
            slug,
            cleaned_name,
            avatar_url=cleaned_avatar_url,
            poster_url=cleaned_poster_url,
            poster_alt=cleaned_poster_alt,
            tagline=cleaned_tagline,
            accent_color=cleaned_accent_color,
            summary=cleaned_summary,
            application_status="draft",
            make_default=make_default,
        )

    def update_character(
        self,
        character_slug: str,
        *,
        name: str,
        summary: str = "",
        avatar_url: str | None = None,
        poster_url: str | None = None,
        poster_alt: str = "",
        tagline: str = "",
        accent_color: str = "",
    ) -> Character:
        viewer = self.viewer()
        character = self.repo.get_character_by_slug(viewer.community.id, character_slug)
        if not policies.can_post_as(viewer.membership, character):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot update character {character.id}"
            )
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("character name is required")
        cleaned_summary = summary.strip()
        cleaned_avatar_url = (avatar_url or "").strip() or None
        cleaned_poster_url = (poster_url or "").strip() or None
        cleaned_poster_alt = poster_alt.strip()
        cleaned_tagline = tagline.strip()
        cleaned_accent_color = accent_color.strip()
        slug = character.slug
        if cleaned_name != character.name:
            slug = _unique_character_slug(
                self.repo,
                viewer.community.id,
                cleaned_name,
                current_character_id=character.id,
            )
        return self.repo.update_character(
            viewer.community.id,
            character.id,
            slug=slug,
            name=cleaned_name,
            avatar_url=cleaned_avatar_url,
            poster_url=cleaned_poster_url,
            poster_alt=cleaned_poster_alt,
            tagline=cleaned_tagline,
            accent_color=cleaned_accent_color,
            summary=cleaned_summary,
        )

    def update_post(self, board_slug: str, thread_slug: str, post_id: int, body: str) -> Post:
        viewer = self.viewer()
        _board, _thread, post = self._editable_post(viewer, board_slug, thread_slug, post_id)
        cleaned = body.strip()
        if not cleaned:
            raise ValueError("post body is required")
        if cleaned == post.body:
            return post
        self.repo.create_post_revision(
            viewer.community.id,
            post.id,
            viewer.membership.id,
            post.body,
            cleaned,
        )
        return self.repo.update_post_body(viewer.community.id, post_id, cleaned)

    def update_thread_state(
        self,
        board_slug: str,
        thread_slug: str,
        *,
        is_locked: bool | None = None,
        is_pinned: bool | None = None,
    ) -> Thread:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        if not policies.can_moderate_thread(viewer.membership, thread, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot moderate thread {thread.id}"
            )
        return self.repo.update_thread_flags(
            viewer.community.id,
            thread.id,
            is_locked=is_locked,
            is_pinned=is_pinned,
        )

    def update_thread_scene(
        self,
        board_slug: str,
        thread_slug: str,
        *,
        status: str,
        location: str = "",
        timeline: str = "",
        summary: str = "",
        posting_mode: str = "freeform",
        participant_ids: list[int] | None = None,
    ) -> Thread:
        viewer = self.viewer()
        _board, thread = self._visible_thread(viewer, board_slug, thread_slug)
        if not self._can_manage_scene(viewer, thread):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage scene {thread.id}"
            )
        cleaned_status = _clean_thread_status(status)
        cleaned_posting_mode = _clean_posting_mode(posting_mode)
        self.repo.update_thread_scene(
            viewer.community.id,
            thread.id,
            status=cleaned_status,
            location=location.strip(),
            timeline=timeline.strip(),
            summary=summary.strip(),
            posting_mode=cleaned_posting_mode,
        )
        posted_character_ids = {
            post.author_character_id
            for post in self.repo.list_posts(viewer.community.id, thread.id)
        }
        required_ids = [thread.author_character_id, *posted_character_ids]
        taggable_ids = {
            character.id
            for character in taggable_characters(
                self.repo.list_community_characters(viewer.community.id),
                viewer.roster,
            )
        }
        tag_ids = [
            character_id
            for character_id in _clean_participant_ids(participant_ids or [])
            if character_id in taggable_ids
        ]
        self.repo.set_thread_participants(
            viewer.community.id,
            thread.id,
            _clean_participant_ids([*required_ids, *tag_ids]),
        )
        return self.repo.get_thread(viewer.community.id, thread.id)

    def move_thread(
        self,
        board_slug: str,
        thread_slug: str,
        target_board_id: int,
    ) -> tuple[Board, Thread]:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        if not policies.can_moderate_thread(viewer.membership, thread, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot moderate thread {thread.id}"
            )
        target_board = self.repo.get_board(viewer.community.id, target_board_id)
        if not policies.can_view_board(viewer.membership, target_board, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot move thread into board {target_board.id}"
            )
        if target_board.id == board.id:
            return target_board, thread
        try:
            conflicting = self.repo.get_thread_by_slug(
                viewer.community.id,
                target_board.id,
                thread.slug,
            )
        except LookupError:
            conflicting = None
        if conflicting is not None and conflicting.id != thread.id:
            raise ValueError(
                f"board {target_board.slug} already has a thread at slug {thread.slug}"
            )
        moved = self.repo.move_thread(viewer.community.id, thread.id, target_board.id)
        return target_board, moved

    def reply_to_thread(
        self, board_slug: str, thread_slug: str, character_id: int, body: str
    ) -> Post:
        viewer = self.viewer()
        character = self.repo.get_character(viewer.community.id, character_id)
        if not policies.can_post_as(viewer.membership, character):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot use character {character_id}"
            )
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        if not policies.can_reply(viewer.membership, thread, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot reply to thread {thread.id}"
            )
        cleaned = body.strip()
        if not cleaned:
            raise ValueError("reply body is required")
        post = self.repo.create_post(viewer.community.id, thread.id, character.id, cleaned)
        self._notify_post_created(viewer, thread, post)
        self.repo.watch_thread(viewer.community.id, thread.id, viewer.membership.id)
        self.repo.mark_thread_read(viewer.community.id, thread.id, viewer.membership.id)
        return post

    def start_thread(
        self,
        *,
        board_slug: str,
        character_id: int,
        title: str,
        body: str,
        status: str = "active",
        location: str = "",
        timeline: str = "",
        summary: str = "",
        posting_mode: str = "freeform",
        participant_ids: list[int] | None = None,
    ) -> Thread:
        return self.start_thread_with_post(
            board_slug=board_slug,
            character_id=character_id,
            title=title,
            body=body,
            status=status,
            location=location,
            timeline=timeline,
            summary=summary,
            posting_mode=posting_mode,
            participant_ids=participant_ids,
        ).thread

    def start_thread_with_post(
        self,
        *,
        board_slug: str,
        character_id: int,
        title: str,
        body: str,
        status: str = "active",
        location: str = "",
        timeline: str = "",
        summary: str = "",
        posting_mode: str = "freeform",
        participant_ids: list[int] | None = None,
    ) -> CreatedThread:
        viewer = self.viewer()
        character = self.repo.get_character(viewer.community.id, character_id)
        if not policies.can_post_as(viewer.membership, character):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot use character {character_id}"
            )
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_start_thread(viewer.membership, board, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot start threads in board {board.id}"
            )
        cleaned_title = title.strip()
        if not cleaned_title:
            raise ValueError("thread title is required")
        cleaned_body = body.strip()
        if not cleaned_body:
            raise ValueError("opening post is required")
        cleaned_status = _clean_thread_status(status)
        cleaned_posting_mode = _clean_posting_mode(posting_mode)
        cleaned_location = location.strip()
        cleaned_timeline = timeline.strip()
        cleaned_summary = summary.strip()
        cleaned_participant_ids = _clean_participant_ids([character.id, *(participant_ids or [])])
        for participant_id in cleaned_participant_ids:
            self.repo.get_character(viewer.community.id, participant_id)
        slug = _unique_thread_slug(self.repo, viewer.community.id, board.id, cleaned_title)
        thread = self.repo.create_thread(
            viewer.community.id,
            board.id,
            character.id,
            slug,
            cleaned_title,
            status=cleaned_status,
            location=cleaned_location,
            timeline=cleaned_timeline,
            summary=cleaned_summary,
            posting_mode=cleaned_posting_mode,
        )
        self.repo.set_thread_participants(
            viewer.community.id,
            thread.id,
            cleaned_participant_ids,
        )
        post = self.repo.create_post(viewer.community.id, thread.id, character.id, cleaned_body)
        thread = self.repo.get_thread(viewer.community.id, thread.id)
        self.repo.watch_thread(viewer.community.id, thread.id, viewer.membership.id)
        self.repo.mark_thread_read(viewer.community.id, thread.id, viewer.membership.id)
        return CreatedThread(thread=thread, post=post)

    def _visible_thread(
        self,
        viewer: ForumView,
        board_slug: str,
        thread_slug: str,
    ) -> tuple[Board, Thread]:
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        return board, thread

    def _can_manage_scene(self, viewer: ForumView, thread: Thread) -> bool:
        return thread.author_membership_id == viewer.membership.id or policies.can_moderate_thread(
            viewer.membership,
            thread,
            viewer.role,
        )

    def _notify_post_created(
        self,
        viewer: ForumView,
        thread: Thread,
        post: Post,
    ) -> None:
        mentioned_memberships = _mentioned_membership_ids(
            self.repo,
            viewer.community.id,
            post.body,
        )
        watch_memberships = set(
            self.repo.list_thread_watch_membership_ids(viewer.community.id, thread.id)
        )
        actor_membership_id = viewer.membership.id
        for membership_id in mentioned_memberships:
            if membership_id != actor_membership_id:
                self.repo.create_notification(
                    viewer.community.id,
                    membership_id,
                    kind="mention",
                    thread_id=thread.id,
                    post_id=post.id,
                    actor_membership_id=actor_membership_id,
                    actor_character_id=post.author_character_id,
                )
        for membership_id in watch_memberships - mentioned_memberships:
            if membership_id != actor_membership_id:
                self.repo.create_notification(
                    viewer.community.id,
                    membership_id,
                    kind="thread_reply",
                    thread_id=thread.id,
                    post_id=post.id,
                    actor_membership_id=actor_membership_id,
                    actor_character_id=post.author_character_id,
                )

    def _editable_post(
        self,
        viewer: ForumView,
        board_slug: str,
        thread_slug: str,
        post_id: int,
    ) -> tuple[Board, Thread, Post]:
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        post = self.repo.get_post(viewer.community.id, post_id)
        if post.thread_id != thread.id:
            raise LookupError(f"post {post_id} does not belong to thread {thread.id}")
        if not policies.can_edit_post(viewer.membership, post, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot edit post {post.id}")
        return board, thread, post

    def _selected_character(
        self,
        viewer: ForumView,
        character_slug: str | None,
    ) -> Character | None:
        if not character_slug:
            return None
        character = self.repo.get_character_by_slug(viewer.community.id, character_slug)
        if character.membership_id != viewer.membership.id:
            raise PermissionError(
                f"membership {viewer.membership.id} cannot filter by character {character.id}"
            )
        return character

    def _notify_application_directors(self, viewer: ForumView, character: Character) -> None:
        for membership in self.repo.list_memberships(viewer.community.id):
            role = self.repo.get_role(viewer.community.id, membership.role_id)
            if not role.is_admin or membership.id == viewer.membership.id:
                continue
            self.repo.create_notification(
                viewer.community.id,
                membership.id,
                kind="application_submitted",
                character_id=character.id,
                actor_membership_id=viewer.membership.id,
                actor_character_id=character.id,
            )

    def _notify_application_owner(
        self,
        viewer: ForumView,
        character: Character,
        kind: str,
    ) -> None:
        actor_character_id = _application_actor_character_id(viewer, character)
        if character.membership_id == viewer.membership.id:
            return
        self.repo.create_notification(
            viewer.community.id,
            character.membership_id,
            kind=kind,
            character_id=character.id,
            actor_membership_id=viewer.membership.id,
            actor_character_id=actor_character_id,
        )

    def _character_activity(
        self,
        viewer: ForumView,
        character: Character,
    ) -> CharacterThreadActivity:
        items = _thread_obligations(self.repo, viewer, {character.id})
        return CharacterThreadActivity(
            character=character,
            needs_reply=[item for item in items if item.needs_reply],
            waiting_on_others=[item for item in items if item.waiting_on_others],
            started_by_character=[item for item in items if item.is_started_by_roster],
            participated=items,
        )

    def _roster_activity(self, viewer: ForumView) -> list[CharacterThreadActivity]:
        return [self._character_activity(viewer, character) for character in viewer.roster]

    def _member_directory_card(
        self,
        viewer: ForumView,
        membership: CommunityMembership,
    ) -> MemberDirectoryCard:
        roster = self.repo.list_characters(viewer.community.id, membership.id)
        roster_ids = {character.id for character in roster}
        active_threads = _thread_obligations(self.repo, viewer, roster_ids)
        latest_posts = _recent_character_posts(self.repo, viewer, roster_ids, limit=1)
        return MemberDirectoryCard(
            membership=membership,
            role=self.repo.get_role(viewer.community.id, membership.role_id),
            roster=roster,
            default_character=_default_character(roster, membership.default_character_id),
            known_for=_known_for_characters(self.repo, viewer, roster, limit=2),
            visible_post_count=len(_visible_character_posts(self.repo, viewer, roster_ids)),
            active_thread_count=len(active_threads),
            latest_post=latest_posts[0] if latest_posts else None,
            is_current_member=membership.id == viewer.membership.id,
        )


def create_services(path: str | Path | None = None) -> AppServices:
    database_path = _resolve_database_path(path)
    if database_path != ":memory:":
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    connection = connect(database_path, check_same_thread=False)
    create_schema(connection)
    repo = ForumRepository(connection)
    seed = seed_demo_forum(repo)
    return AppServices(repo, seed)


def initialize_database(path: str | Path | None = None, *, seed_demo: bool = True) -> Path:
    database_path = _resolve_database_path(path)
    if database_path == ":memory:":
        raise ValueError("persistent database initialization requires a filesystem path")
    resolved_path = Path(database_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(resolved_path)
    try:
        create_schema(connection)
        if seed_demo:
            seed_demo_forum(ForumRepository(connection))
    finally:
        connection.close()
    return resolved_path


def default_database_path() -> Path:
    configured = os.environ.get(DATABASE_PATH_ENV)
    if configured:
        return Path(configured)
    return DEFAULT_DATABASE_PATH


def _resolve_database_path(path: str | Path | None) -> str | Path:
    if path is None:
        return default_database_path()
    return path


def _resolve_current_character(
    repo: ForumRepository,
    membership: CommunityMembership,
    roster: list[Character],
) -> Character | None:
    if not roster:
        return None
    if membership.default_character_id is not None:
        return repo.get_character(membership.community_id, membership.default_character_id)
    return roster[0]


def _board_navigation(
    repo: ForumRepository,
    community_id: int,
    membership: CommunityMembership,
    role: Role,
) -> list[BoardNavigationItem]:
    items: list[BoardNavigationItem] = []
    for board in repo.list_boards(community_id):
        if not policies.can_view_board(membership, board, role):
            continue
        threads = repo.list_threads(community_id, board.id)
        unread_thread_count = sum(
            1 for thread in threads if _is_unread(repo, community_id, membership.id, thread)
        )
        items.append(BoardNavigationItem(board=board, unread_thread_count=unread_thread_count))
    return items


def _location_navigation_groups(
    navigation_boards: list[BoardNavigationItem],
) -> list[LocationNavigationGroup]:
    parents = [
        item
        for item in navigation_boards
        if item.board.parent_board_id is None and is_location_board(item.board)
    ]
    children_by_parent: dict[int, list[BoardNavigationItem]] = {
        item.board.id: [] for item in parents
    }
    for item in navigation_boards:
        parent_id = item.board.parent_board_id
        if parent_id is None or not is_location_board(item.board):
            continue
        if parent_id in children_by_parent:
            children_by_parent[parent_id].append(item)
    return [
        LocationNavigationGroup(
            parent=parent,
            children=children_by_parent[parent.board.id],
        )
        for parent in parents
    ]


def _board_summary(
    repo: ForumRepository,
    viewer: ForumView,
    board: Board,
    current_facet_ids: set[int],
) -> BoardSummary:
    child_boards = [
        child
        for child in repo.list_child_boards(viewer.community.id, board.id)
        if policies.can_view_board(viewer.membership, child, viewer.role)
    ]
    boards_for_activity = [board, *child_boards]
    board_facets = _facet_tags(
        repo,
        viewer.community.id,
        repo.list_board_facets(viewer.community.id, board.id),
    )
    threads_with_boards: list[tuple[Board, Thread]] = []
    posts_by_thread: dict[int, list[Post]] = {}
    for activity_board in boards_for_activity:
        for thread in repo.list_threads(viewer.community.id, activity_board.id):
            threads_with_boards.append((activity_board, thread))
            posts_by_thread[thread.id] = repo.list_posts(viewer.community.id, thread.id)
    latest_board: Board | None = None
    latest_thread: Thread | None = None
    if threads_with_boards:
        latest_board, latest_thread = max(
            threads_with_boards,
            key=lambda item: (_timestamp_key(item[1].updated_at), item[1].id),
        )
    latest_thread_posts = posts_by_thread.get(latest_thread.id, []) if latest_thread else []
    latest_post = (
        _post_view(repo, viewer.community.id, latest_thread_posts[-1])
        if latest_thread_posts
        else None
    )
    threads = [thread for _, thread in threads_with_boards]
    return BoardSummary(
        board=board,
        child_boards=child_boards,
        thread_count=len(threads),
        post_count=sum(len(posts) for posts in posts_by_thread.values()),
        unread_thread_count=sum(
            1
            for thread in threads
            if _is_unread(
                repo,
                viewer.community.id,
                viewer.membership.id,
                thread,
            )
        ),
        latest_thread=latest_thread,
        latest_board=latest_board,
        latest_post=latest_post,
        facets=board_facets,
        is_relevant_to_current_face=bool(
            current_facet_ids
            and {tag.facet.id for tag in board_facets}.intersection(current_facet_ids)
        ),
    )


def _default_character(
    roster: list[Character],
    default_character_id: int | None,
) -> Character | None:
    if default_character_id is None:
        return roster[0] if roster else None
    return next(
        (character for character in roster if character.id == default_character_id),
        roster[0] if roster else None,
    )


def _wanted_ad_summary(
    repo: ForumRepository,
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
        facets=_facet_tags(
            repo,
            community_id,
            repo.list_wanted_ad_facets(community_id, wanted_ad.id),
        ),
        type_label=_wanted_type_label(wanted_ad.wanted_type),
    )


def _wanted_type_label(wanted_type: str) -> str:
    return {
        "canon": "Canon",
        "connection": "Connection",
        "event_role": "Event Role",
        "faction_need": "Faction Need",
        "plot_role": "Plot Role",
        "rival": "Rival",
    }.get(wanted_type, wanted_type.replace("_", " ").title())


def _wanted_ad_interest_view(
    repo: ForumRepository,
    community_id: int,
    interest: WantedAdInterest,
) -> WantedAdInterestView:
    return WantedAdInterestView(
        interest=interest,
        membership=repo.get_membership(community_id, interest.membership_id),
        character=repo.get_character(community_id, interest.character_id),
        created_at_label=_timestamp_label(interest.created_at),
    )


def _character_reserve_view(
    repo: ForumRepository,
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
        created_at_label=_timestamp_label(reserve.created_at),
    )


def _application_character_view(
    repo: ForumRepository,
    viewer: ForumView,
    character: Character,
) -> ApplicationCharacterView:
    return ApplicationCharacterView(
        character=character,
        membership=repo.get_membership(viewer.community.id, character.membership_id),
        facets=_facet_tags(
            repo,
            viewer.community.id,
            repo.list_character_facets(viewer.community.id, character.id),
        ),
        reserves=[
            _character_reserve_view(repo, viewer.community.id, reserve)
            for reserve in repo.list_character_reserves(
                viewer.community.id,
                character.id,
            )
        ],
        status_label=_application_status_label(character.application_status),
        status_variant=_application_status_variant(character.application_status),
        is_owned_by_viewer=character.membership_id == viewer.membership.id,
    )


def _application_status_label(status: str) -> str:
    return APPLICATION_STATUS_LABELS.get(status, status.replace("_", " ").title())


def _application_status_variant(status: str) -> str:
    return APPLICATION_STATUS_VARIANTS.get(status, "muted")


def _application_actor_character_id(viewer: ForumView, target_character: Character) -> int:
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


def _wanted_actor_character_id(
    repo: ForumRepository,
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


def _discovery_characters(
    repo: ForumRepository,
    viewer: ForumView,
    character_ids: set[int],
    selected_facet_ids: list[int],
) -> list[DiscoveryCharacterResult]:
    selected = set(selected_facet_ids)
    results = []
    for character in repo.list_community_characters(viewer.community.id):
        if character.id not in character_ids:
            continue
        owner = repo.get_membership(viewer.community.id, character.membership_id)
        if not owner.is_active:
            continue
        facets = _facet_tags(
            repo,
            viewer.community.id,
            repo.list_character_facets(viewer.community.id, character.id),
        )
        matching_facets = [tag for tag in facets if tag.facet.id in selected]
        results.append(
            DiscoveryCharacterResult(
                character=character,
                owner_membership=owner,
                facets=facets,
                matching_facets=matching_facets,
            )
        )
    return sorted(
        results,
        key=lambda item: (
            -len(item.matching_facets),
            item.character.name,
            item.character.id,
        ),
    )


def _discovery_open_threads(
    repo: ForumRepository,
    viewer: ForumView,
    thread_ids: set[int],
    selected_facet_ids: list[int],
) -> list[DiscoveryThreadResult]:
    selected = set(selected_facet_ids)
    visible_boards = {
        board.id: board
        for board in repo.list_boards(viewer.community.id)
        if policies.can_view_board(viewer.membership, board, viewer.role)
    }
    results = []
    for thread in repo.list_threads(viewer.community.id):
        if thread.id not in thread_ids or thread.status != "open" or thread.is_locked:
            continue
        board = visible_boards.get(thread.board_id)
        if board is None:
            continue
        facets = _facet_tags(
            repo,
            viewer.community.id,
            repo.list_thread_facets(viewer.community.id, thread.id),
        )
        matching_facets = [tag for tag in facets if tag.facet.id in selected]
        posts = repo.list_posts(viewer.community.id, thread.id)
        results.append(
            DiscoveryThreadResult(
                board=board,
                thread=thread,
                author=repo.get_character(viewer.community.id, thread.author_character_id),
                participants=repo.list_thread_participants(viewer.community.id, thread.id),
                facets=facets,
                matching_facets=matching_facets,
                reply_count=max(0, len(posts) - 1),
            )
        )
    return sorted(
        results,
        key=lambda item: (
            -len(item.matching_facets),
            _timestamp_key(item.thread.updated_at),
            item.thread.id,
        ),
        reverse=True,
    )


def _visible_character_posts(
    repo: ForumRepository,
    viewer: ForumView,
    character_ids: set[int],
) -> list[CharacterAppearance]:
    if not character_ids:
        return []
    visible_boards = {
        board.id: board
        for board in repo.list_boards(viewer.community.id)
        if policies.can_view_board(viewer.membership, board, viewer.role)
    }
    items: list[CharacterAppearance] = []
    for character_id in character_ids:
        for post in repo.list_posts_by_character(viewer.community.id, character_id):
            thread = repo.get_thread(viewer.community.id, post.thread_id)
            board = visible_boards.get(thread.board_id)
            if board is None:
                continue
            items.append(
                CharacterAppearance(
                    post=_post_view(repo, viewer.community.id, post),
                    thread=thread,
                    board=board,
                )
            )
    return sorted(
        items,
        key=lambda item: (_timestamp_key(item.post.post.created_at), item.post.post.id),
        reverse=True,
    )


def _recent_character_posts(
    repo: ForumRepository,
    viewer: ForumView,
    character_ids: set[int],
    *,
    limit: int,
) -> list[CharacterAppearance]:
    return _visible_character_posts(repo, viewer, character_ids)[:limit]


def _known_for_characters(
    repo: ForumRepository,
    viewer: ForumView,
    roster: list[Character],
    *,
    limit: int,
) -> list[Character]:
    if not roster:
        return []
    appearances = _visible_character_posts(
        repo,
        viewer,
        {character.id for character in roster},
    )
    counts: dict[int, int] = {}
    latest: dict[int, tuple[str, int]] = {}
    for appearance in appearances:
        character_id = appearance.post.author.id
        counts[character_id] = counts.get(character_id, 0) + 1
        latest[character_id] = max(
            latest.get(character_id, ("", 0)),
            (
                appearance.post.post.created_at,
                appearance.post.post.id,
            ),
        )
    ranked = sorted(
        roster,
        key=lambda character: (
            counts.get(character.id, 0),
            latest.get(character.id, ("", 0)),
            character.name.lower(),
        ),
        reverse=True,
    )
    return ranked[:limit]


def _writer_collaborators(
    repo: ForumRepository,
    viewer: ForumView,
    membership: CommunityMembership,
    roster_ids: set[int],
    *,
    limit: int,
) -> list[WriterCollaborator]:
    if not roster_ids:
        return []
    visible_boards = {
        board.id: board
        for board in repo.list_boards(viewer.community.id)
        if policies.can_view_board(viewer.membership, board, viewer.role)
    }
    counts: dict[int, int] = {}
    latest: dict[int, tuple[str, int, Thread, Board]] = {}
    for thread in repo.list_threads(viewer.community.id):
        board = visible_boards.get(thread.board_id)
        if board is None:
            continue
        posts = repo.list_posts(viewer.community.id, thread.id)
        if not any(
            post.author_membership_id == membership.id or post.author_character_id in roster_ids
            for post in posts
        ):
            continue
        other_membership_ids = {
            post.author_membership_id
            for post in posts
            if post.author_membership_id != membership.id
        }
        for other_id in other_membership_ids:
            counts[other_id] = counts.get(other_id, 0) + 1
            candidate = (thread.updated_at, thread.id, thread, board)
            if candidate[:2] > latest.get(other_id, ("", 0, thread, board))[:2]:
                latest[other_id] = candidate
    collaborators: list[WriterCollaborator] = []
    for membership_id, shared_thread_count in counts.items():
        try:
            collaborator = repo.get_membership(viewer.community.id, membership_id)
        except LookupError:
            continue
        if not collaborator.is_active:
            continue
        _stamp, _thread_id, latest_thread, latest_board = latest[membership_id]
        collaborators.append(
            WriterCollaborator(
                membership=collaborator,
                shared_thread_count=shared_thread_count,
                latest_thread=latest_thread,
                latest_board=latest_board,
            )
        )
    return sorted(
        collaborators,
        key=lambda item: (
            item.shared_thread_count,
            _timestamp_key(item.latest_thread.updated_at),
            item.membership.display_name.lower(),
        ),
        reverse=True,
    )[:limit]


def _latest_thread(threads: list[Thread]) -> Thread | None:
    if not threads:
        return None
    return max(threads, key=lambda thread: (_timestamp_key(thread.updated_at), thread.id))


def _clean_mentionable_scope(value: str) -> MentionableScope:
    scope = value.strip().lower().replace("-", "_")
    if scope not in {"all", "cast", "characters", "writers", "ooc"}:
        return "all"
    return cast(MentionableScope, scope)


def _character_mentionable(character: Character) -> Mentionable:
    return Mentionable(
        kind="character",
        id=character.id,
        handle=character.slug,
        label=character.name,
        detail="Character",
        avatar_url=character.avatar_url,
        href=f"/characters/{character.slug}",
    )


def _membership_mentionable(membership: CommunityMembership) -> Mentionable:
    return Mentionable(
        kind="writer",
        id=membership.id,
        handle=membership.username,
        label=membership.display_name,
        detail=f"Writer @{membership.username}",
        avatar_url=membership.avatar_url,
        href=f"/members/{membership.username}",
    )


def _notification_item(
    repo: ForumRepository,
    viewer: ForumView,
    notification: Notification,
) -> NotificationItem | None:
    actor = repo.get_character(viewer.community.id, notification.actor_character_id)
    actor_membership = repo.get_membership(
        viewer.community.id,
        notification.actor_membership_id,
    )
    if notification.character_id is not None:
        character = repo.get_character(viewer.community.id, notification.character_id)
        match notification.kind:
            case "application_submitted":
                snippet = f"{actor.name} submitted this character for review."
            case "application_accepted":
                snippet = f"{actor.name} accepted this character application."
            case "application_revision_requested":
                snippet = f"{actor.name} requested revisions for this character application."
            case _:
                snippet = f"{actor.name} updated this character application."
        return NotificationItem(
            notification=notification,
            board=None,
            thread=None,
            post=None,
            wanted_ad=None,
            actor=actor,
            actor_membership=actor_membership,
            label=_notification_label(notification.kind),
            title=character.name,
            created_at_label=_timestamp_label(notification.created_at),
            snippet=snippet,
            href=f"/characters/{character.slug}",
        )
    if notification.wanted_ad_id is not None:
        wanted_ad = repo.get_wanted_ad(viewer.community.id, notification.wanted_ad_id)
        interest = (
            repo.get_wanted_ad_interest(
                viewer.community.id,
                notification.wanted_ad_interest_id,
            )
            if notification.wanted_ad_interest_id is not None
            else None
        )
        if notification.kind == "wanted_reserved":
            snippet = f"{actor.name} reserved this wanted hook."
        elif notification.kind == "reserve_created":
            snippet = f"{actor.name} created a reserve from this wanted hook."
        else:
            snippet = f"{actor.name} is interested in this wanted hook."
        if interest is not None and interest.note:
            snippet = interest.note
        return NotificationItem(
            notification=notification,
            board=None,
            thread=None,
            post=None,
            wanted_ad=wanted_ad,
            actor=actor,
            actor_membership=actor_membership,
            label=_notification_label(notification.kind),
            title=wanted_ad.title,
            created_at_label=_timestamp_label(notification.created_at),
            snippet=snippet,
            href=f"/wanted/{wanted_ad.slug}",
        )
    if notification.thread_id is None or notification.post_id is None:
        return None
    thread = repo.get_thread(viewer.community.id, notification.thread_id)
    board = repo.get_board(viewer.community.id, thread.board_id)
    if not policies.can_view_board(viewer.membership, board, viewer.role):
        return None
    post = repo.get_post(viewer.community.id, notification.post_id)
    post_view = _post_view(repo, viewer.community.id, post)
    return NotificationItem(
        notification=notification,
        board=board,
        thread=thread,
        post=post_view,
        wanted_ad=None,
        actor=actor,
        actor_membership=actor_membership,
        label=_notification_label(notification.kind),
        title=thread.title,
        created_at_label=post_view.created_at_label,
        snippet=post_view.snippet,
        href=f"/boards/{board.slug}/threads/{thread.slug}#{post_view.anchor}",
    )


def _notification_label(kind: str) -> str:
    match kind:
        case "mention":
            return "Mention"
        case "thread_reply":
            return "Watched thread"
        case "wanted_interest":
            return "Wanted interest"
        case "wanted_reserved":
            return "Wanted reserved"
        case "reserve_created":
            return "Reserve created"
        case "application_submitted":
            return "Application submitted"
        case "application_accepted":
            return "Application accepted"
        case "application_revision_requested":
            return "Revisions requested"
        case _:
            return "Notification"


def _mentioned_membership_ids(
    repo: ForumRepository,
    community_id: int,
    body: str,
) -> set[int]:
    mentioned: set[int] = set()
    for character in repo.list_community_characters(community_id):
        if _mentions_character(body, character):
            mentioned.add(character.membership_id)
    for membership in repo.list_memberships(community_id):
        if membership.is_active and _mentions_membership(body, membership):
            mentioned.add(membership.id)
    return mentioned


def _mentions_character(body: str, character: Character) -> bool:
    for label in {character.slug, character.name}:
        if re.search(rf"(?<![\w-])@{re.escape(label)}(?![\w-])", body, re.IGNORECASE):
            return True
    return False


def _mentions_membership(body: str, membership: CommunityMembership) -> bool:
    return bool(
        re.search(
            rf"(?<![\w-])@{re.escape(membership.username)}(?![\w-])",
            body,
            re.IGNORECASE,
        )
    )


def _unique_character_slug(
    repo: ForumRepository,
    community_id: int,
    name: str,
    *,
    current_character_id: int | None = None,
) -> str:
    base = _slugify(name)
    slug = base
    suffix = 2
    while True:
        try:
            existing = repo.get_character_by_slug(community_id, slug)
        except LookupError:
            return slug
        if existing.id == current_character_id:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1


def _unique_thread_slug(
    repo: ForumRepository,
    community_id: int,
    board_id: int,
    title: str,
) -> str:
    base = _slugify(title)
    slug = base
    suffix = 2
    while True:
        try:
            repo.get_thread_by_slug(community_id, board_id, slug)
        except LookupError:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "character"
