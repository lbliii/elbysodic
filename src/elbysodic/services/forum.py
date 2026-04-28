"""Service-layer commands and read models for the forum slice."""

from __future__ import annotations

import os
import re
from pathlib import Path

from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.db.seed import DemoSeed, seed_demo_forum
from elbysodic.domain.boards import (
    BOARD_KIND_GUIDANCE,
    BOARD_KIND_LABELS,
    BOARD_KIND_REALMS,
    BOARD_KIND_SIDEBAR_LABELS,
    BoardKind,
    is_community_board,
    is_location_board,
    normalize_board_kind,
)
from elbysodic.domain.models import (
    Board,
    Character,
    CharacterReserve,
    Community,
    CommunityMembership,
    Material,
    Post,
    Role,
    Thread,
    WantedAdInterest,
)
from elbysodic.services import policies
from elbysodic.services.applications import (
    accept_character_application as _accept_character_application,
)
from elbysodic.services.applications import applications_desk as _applications_desk
from elbysodic.services.applications import (
    request_character_application_revision as _request_character_application_revision,
)
from elbysodic.services.applications import (
    submit_character_application as _submit_character_application,
)
from elbysodic.services.casting import casting_desk as _casting_desk
from elbysodic.services.casting import (
    create_reserve_for_wanted_interest as _create_reserve_for_wanted_interest,
)
from elbysodic.services.casting import (
    express_prospective_wanted_interest as _express_prospective_wanted_interest,
)
from elbysodic.services.casting import express_wanted_interest as _express_wanted_interest
from elbysodic.services.casting import read_wanted_ad as _read_wanted_ad
from elbysodic.services.casting import reserve_wanted_interest as _reserve_wanted_interest
from elbysodic.services.casting import wanted_ad_summary as _wanted_ad_summary
from elbysodic.services.casting import wanted_board as _wanted_board
from elbysodic.services.discovery import discover_plots as _discover_plots
from elbysodic.services.facets import (
    current_character_facet_ids as _current_character_facet_ids,
)
from elbysodic.services.facets import (
    facet_tags as _facet_tags,
)
from elbysodic.services.identity import character_profile as _character_profile
from elbysodic.services.identity import (
    character_roster_dashboard as _character_roster_dashboard,
)
from elbysodic.services.identity import member_directory as _member_directory
from elbysodic.services.identity import member_profile as _member_profile
from elbysodic.services.identity import roster_activity as _roster_activity
from elbysodic.services.identity import selected_character as _selected_character
from elbysodic.services.markup import post_snippet
from elbysodic.services.materials import (
    current_event_for_facet_ids as _current_event_for_facet_ids,
)
from elbysodic.services.materials import material_detail as _material_detail
from elbysodic.services.materials import material_summary as _material_summary
from elbysodic.services.notifications import (
    mark_all_notifications_read as _mark_all_notifications_read,
)
from elbysodic.services.notifications import notification_inbox as _notification_inbox
from elbysodic.services.notifications import open_notification as _open_notification
from elbysodic.services.plot_hooks import (
    create_plot_hook as _create_plot_hook,
)
from elbysodic.services.plot_hooks import express_plot_hook_interest as _express_plot_hook_interest
from elbysodic.services.plot_hooks import read_plot_hook as _read_plot_hook
from elbysodic.services.plot_hooks import update_plot_hook as _update_plot_hook
from elbysodic.services.plotting import (
    create_plotting_room_from_plot_hook_interest as _create_plotting_room_from_plot_hook_interest,
)
from elbysodic.services.plotting import (
    create_plotting_room_from_wanted_interest as _create_plotting_room_from_wanted_interest,
)
from elbysodic.services.plotting import plotting_desk as _plotting_desk
from elbysodic.services.plotting import read_plotting_room as _read_plotting_room
from elbysodic.services.posting import join_thread_as_current_character as _join_thread
from elbysodic.services.posting import read_post_editor as _read_post_editor
from elbysodic.services.posting import read_post_revisions as _read_post_revisions
from elbysodic.services.posting import reply_to_thread as _reply_to_thread
from elbysodic.services.posting import search_mentionables as _search_mentionables
from elbysodic.services.posting import start_thread as _start_thread
from elbysodic.services.posting import update_post as _update_post
from elbysodic.services.posting import update_thread_scene as _update_thread_scene
from elbysodic.services.posts import post_view as _post_view
from elbysodic.services.read_models import (
    MATERIAL_STATUSES,
    MATERIAL_TYPES,
    POST_ACCENT_STYLES,
    POST_BORDER_STYLES,
    POST_DENSITIES,
    POST_PROFILE_VARIANTS,
    POST_STYLE_PRESETS,
    POST_TITLE_STYLES,
    ActivityItem,
    ApplicationsDesk,
    AttentionItem,
    BoardNavigationItem,
    BoardSummary,
    BoardTaxonomyItem,
    BoardThreadFilter,
    CastingDesk,
    CharacterPlotHookDetail,
    CharacterProfile,
    CharacterRosterDashboard,
    CreatedThread,
    DirectorStudio,
    EditablePostView,
    FacetTag,
    ForumView,
    LocationNavigationGroup,
    MaterialDetail,
    MaterialSummary,
    MemberDirectory,
    MemberProfile,
    Mentionable,
    MyThreadsDashboard,
    NavigationPreviewItem,
    NavigationPreviewSection,
    NotificationInbox,
    PlotDiscovery,
    PlottingDesk,
    PlottingRoomDetail,
    PostRevisionHistory,
    PostStylePolicy,
    ThreadNavigationItem,
    ThreadSummary,
    ThreadView,
    WantedAdDetail,
    WantedAdSummary,
    WantedBoard,
    WorldHub,
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
from elbysodic.services.threads import is_live_queue_thread as _is_live_queue_thread
from elbysodic.services.threads import is_unread as _is_unread
from elbysodic.services.threads import next_unread_thread as _next_unread_thread
from elbysodic.services.threads import read_thread_view as _read_thread_view
from elbysodic.services.threads import thread_needs_attention as _thread_needs_attention
from elbysodic.services.threads import thread_obligations as _thread_obligations
from elbysodic.services.timestamps import timestamp_key as _timestamp_key

DEFAULT_DATABASE_PATH = Path("var/elbysodic.sqlite3")
DATABASE_PATH_ENV = "ELBYSODIC_DB_PATH"


class AppServices:
    """Small application service facade for the dev forum."""

    def __init__(self, repo: ForumRepository, seed: DemoSeed) -> None:
        self.repo = repo
        self.seed = seed

    def viewer(self) -> ForumView:
        community = self.repo.get_community(self.seed.community.id)
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
            desk_navigation_boards=[
                item for item in navigation_boards if item.board.board_kind == "desk"
            ],
            studio_navigation_boards=[
                item for item in navigation_boards if item.board.board_kind == "staff"
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
        selected_character = _selected_character(self.repo, viewer, character_slug)
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
            roster_activity=_roster_activity(self.repo, viewer),
        )

    def character_roster(self) -> CharacterRosterDashboard:
        viewer = self.viewer()
        return _character_roster_dashboard(self.repo, viewer)

    def applications_desk(self) -> ApplicationsDesk:
        viewer = self.viewer()
        return _applications_desk(self.repo, viewer)

    def members_directory(self) -> MemberDirectory:
        viewer = self.viewer()
        return _member_directory(self.repo, viewer)

    def read_member(self, username: str) -> MemberProfile:
        viewer = self.viewer()
        return _member_profile(self.repo, viewer, username)

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
        _join_thread(self.repo, self.viewer(), board_slug, thread_slug)

    def discover_plots(self, *, facet_slugs: list[str] | None = None) -> PlotDiscovery:
        return _discover_plots(self.repo, self.viewer(), facet_slugs=facet_slugs)

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
        boards_by_id = {item.board.id: item.board for item in board_summaries}
        child_counts: dict[int, int] = {item.board.id: 0 for item in board_summaries}
        for item in board_summaries:
            if item.board.parent_board_id is not None:
                child_counts[item.board.parent_board_id] = (
                    child_counts.get(item.board.parent_board_id, 0) + 1
                )
        board_taxonomy = [
            _board_taxonomy_item(
                summary,
                parent=(
                    boards_by_id.get(summary.board.parent_board_id)
                    if summary.board.parent_board_id is not None
                    else None
                ),
                child_count=child_counts.get(summary.board.id, 0),
            )
            for summary in board_summaries
        ]
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
        facet_groups = self.repo.list_facet_groups(viewer.community.id)
        identity_accent_group = next(
            (
                group
                for group in facet_groups
                if group.id == viewer.community.identity_accent_facet_group_id
            ),
            None,
        )
        return DirectorStudio(
            can_manage=viewer.role.is_admin,
            facet_groups=facet_groups,
            identity_accent_group=identity_accent_group,
            post_style_policy=_post_style_policy(viewer.community),
            materials=materials,
            draft_materials=[item for item in materials if item.material.status == "draft"],
            featured_materials=[item for item in materials if item.material.is_featured],
            events=events,
            current_event=current_event,
            application_materials=[
                item for item in materials if item.material.material_type == "application"
            ],
            board_taxonomy=board_taxonomy,
            navigation_preview_sections=_navigation_preview_sections(
                board_taxonomy,
                current_event=current_event,
                unread_notification_count=viewer.unread_notification_count,
                active_face=viewer.current_character,
                open_wanted_ads=[item for item in wanted_ads if item.wanted_ad.status == "open"],
            ),
            location_boards=location_boards,
            sublocation_boards=sublocation_boards,
            wanted_ads=wanted_ads,
            open_wanted_ads=[item for item in wanted_ads if item.wanted_ad.status == "open"],
            applications=self.applications_desk(),
        )

    def update_board_taxonomy(
        self,
        board_id: int,
        *,
        board_kind: str,
        parent_board_id: int | None,
    ) -> Board:
        viewer = self.viewer()
        if not viewer.role.is_admin:
            raise PermissionError(f"membership {viewer.membership.id} cannot manage boards")
        board = self.repo.get_board(viewer.community.id, board_id)
        normalized_kind = normalize_board_kind(board_kind)
        normalized_parent_id = _validate_board_parent(
            self.repo.list_boards(viewer.community.id),
            board,
            normalized_kind,
            parent_board_id,
        )
        return self.repo.update_board(
            viewer.community.id,
            board.id,
            name=board.name,
            description=board.description,
            sort_order=board.sort_order,
            parent_board_id=normalized_parent_id,
            board_kind=normalized_kind,
            tagline=board.tagline,
            image_url=board.image_url,
            image_alt=board.image_alt,
            is_private=board.is_private,
        )

    def update_board_navigation(
        self,
        board_id: int,
        *,
        navigation_order: int,
        show_in_navigation: bool,
    ) -> Board:
        viewer = self.viewer()
        if not viewer.role.is_admin:
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage board navigation"
            )
        board = self.repo.get_board(viewer.community.id, board_id)
        return self.repo.update_board(
            viewer.community.id,
            board.id,
            name=board.name,
            description=board.description,
            sort_order=board.sort_order,
            parent_board_id=board.parent_board_id,
            board_kind=board.board_kind,
            tagline=board.tagline,
            image_url=board.image_url,
            image_alt=board.image_alt,
            is_private=board.is_private,
            navigation_order=navigation_order,
            show_in_navigation=show_in_navigation,
        )

    def update_identity_accent_group(self, facet_group_id: int | None) -> None:
        viewer = self.viewer()
        if not viewer.role.is_admin:
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage community direction"
            )
        self.repo.update_community_identity_accent_group(
            viewer.community.id,
            facet_group_id,
        )

    def post_style_policy(self) -> PostStylePolicy:
        return _post_style_policy(self.viewer().community)

    def update_post_style_policy(
        self,
        *,
        enabled_post_profile_variants: list[str],
        enabled_post_accent_styles: list[str],
        enabled_post_border_styles: list[str],
        enabled_post_title_styles: list[str],
        enabled_post_densities: list[str],
    ) -> None:
        viewer = self.viewer()
        if not viewer.role.is_admin:
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage post style policy"
            )
        self.repo.update_community_post_style_policy(
            viewer.community.id,
            enabled_post_profile_variants=",".join(
                _clean_enabled_style_values(
                    enabled_post_profile_variants,
                    POST_PROFILE_VARIANTS,
                    "post profile variants",
                )
            ),
            enabled_post_accent_styles=",".join(
                _clean_enabled_style_values(
                    enabled_post_accent_styles,
                    POST_ACCENT_STYLES,
                    "post accent styles",
                )
            ),
            enabled_post_border_styles=",".join(
                _clean_enabled_style_values(
                    enabled_post_border_styles,
                    POST_BORDER_STYLES,
                    "post border styles",
                )
            ),
            enabled_post_title_styles=",".join(
                _clean_enabled_style_values(
                    enabled_post_title_styles,
                    POST_TITLE_STYLES,
                    "post title styles",
                )
            ),
            enabled_post_densities=",".join(
                _clean_enabled_style_values(
                    enabled_post_densities,
                    POST_DENSITIES,
                    "post densities",
                )
            ),
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
        return _wanted_board(self.repo, self.viewer())

    def casting_desk(self) -> CastingDesk:
        return _casting_desk(self.repo, self.viewer())

    def read_wanted_ad(self, wanted_slug: str) -> WantedAdDetail:
        return _read_wanted_ad(self.repo, self.viewer(), wanted_slug)

    def express_wanted_interest(self, wanted_slug: str) -> WantedAdInterest:
        return _express_wanted_interest(self.repo, self.viewer(), wanted_slug)

    def express_prospective_wanted_interest(
        self,
        wanted_slug: str,
        *,
        prospective_character_name: str,
        note: str = "",
    ) -> WantedAdInterest:
        return _express_prospective_wanted_interest(
            self.repo,
            self.viewer(),
            wanted_slug,
            prospective_character_name=prospective_character_name,
            note=note,
        )

    def reserve_wanted_interest(
        self,
        wanted_slug: str,
        interest_id: int,
    ) -> WantedAdInterest:
        return _reserve_wanted_interest(self.repo, self.viewer(), wanted_slug, interest_id)

    def create_reserve_for_wanted_interest(
        self,
        wanted_slug: str,
        interest_id: int,
    ) -> CharacterReserve:
        return _create_reserve_for_wanted_interest(
            self.repo,
            self.viewer(),
            wanted_slug,
            interest_id,
        )

    def notifications(self, *, limit: int = 50) -> NotificationInbox:
        return _notification_inbox(self.repo, self.viewer(), limit=limit)

    def search_mentionables(
        self,
        query: str,
        *,
        scope: str = "all",
        limit: int = 8,
    ) -> list[Mentionable]:
        return _search_mentionables(self.repo, self.viewer(), query, scope=scope, limit=limit)

    def open_notification(self, notification_id: int) -> str:
        return _open_notification(self.repo, self.viewer(), notification_id)

    def mark_all_notifications_read(self) -> None:
        _mark_all_notifications_read(self.repo, self.viewer())

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
        return _submit_character_application(self.repo, viewer, character_slug)

    def accept_character_application(self, character_slug: str) -> Character:
        viewer = self.viewer()
        return _accept_character_application(self.repo, viewer, character_slug)

    def request_character_application_revision(self, character_slug: str) -> Character:
        viewer = self.viewer()
        return _request_character_application_revision(self.repo, viewer, character_slug)

    def read_character(self, character_slug: str) -> CharacterProfile:
        viewer = self.viewer()
        return _character_profile(self.repo, viewer, character_slug)

    def read_plot_hook(self, character_slug: str, hook_slug: str) -> CharacterPlotHookDetail:
        return _read_plot_hook(self.repo, self.viewer(), character_slug, hook_slug)

    def create_plot_hook(
        self,
        character_slug: str,
        *,
        title: str,
        hook_type: str,
        summary: str,
        body: str,
        facet_slugs: list[str],
    ):
        return _create_plot_hook(
            self.repo,
            self.viewer(),
            character_slug,
            title=title,
            hook_type=hook_type,
            summary=summary,
            body=body,
            facet_slugs=facet_slugs,
        )

    def update_plot_hook(
        self,
        character_slug: str,
        hook_slug: str,
        *,
        title: str,
        hook_type: str,
        summary: str,
        body: str,
        status: str,
        facet_slugs: list[str],
    ):
        return _update_plot_hook(
            self.repo,
            self.viewer(),
            character_slug,
            hook_slug,
            title=title,
            hook_type=hook_type,
            summary=summary,
            body=body,
            status=status,
            facet_slugs=facet_slugs,
        )

    def express_plot_hook_interest(self, character_slug: str, hook_slug: str):
        return _express_plot_hook_interest(self.repo, self.viewer(), character_slug, hook_slug)

    def plotting_desk(self) -> PlottingDesk:
        return _plotting_desk(self.repo, self.viewer())

    def read_plotting_room(self, room_id: int) -> PlottingRoomDetail:
        return _read_plotting_room(self.repo, self.viewer(), room_id)

    def create_plotting_room_from_plot_hook_interest(
        self,
        character_slug: str,
        hook_slug: str,
        interest_id: int,
    ):
        return _create_plotting_room_from_plot_hook_interest(
            self.repo,
            self.viewer(),
            character_slug,
            hook_slug,
            interest_id,
        )

    def create_plotting_room_from_wanted_interest(self, wanted_slug: str, interest_id: int):
        return _create_plotting_room_from_wanted_interest(
            self.repo,
            self.viewer(),
            wanted_slug,
            interest_id,
        )

    def read_post_editor(self, board_slug: str, thread_slug: str, post_id: int) -> EditablePostView:
        return _read_post_editor(self.repo, self.viewer(), board_slug, thread_slug, post_id)

    def read_post_revisions(
        self,
        board_slug: str,
        thread_slug: str,
        post_id: int,
    ) -> PostRevisionHistory:
        return _read_post_revisions(self.repo, self.viewer(), board_slug, thread_slug, post_id)

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
        post_profile_variant: str = "bio",
        post_accent_style: str = "soft",
        post_border_style: str = "hairline",
        post_title_style: str = "standard",
        post_density: str = "calm",
        post_style_preset: str = "",
        make_default: bool = False,
    ) -> Character:
        viewer = self.viewer()
        style_policy = _post_style_policy(viewer.community)
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("character name is required")
        cleaned_summary = summary.strip()
        cleaned_avatar_url = (avatar_url or "").strip() or None
        cleaned_poster_url = (poster_url or "").strip() or None
        cleaned_poster_alt = poster_alt.strip()
        cleaned_tagline = tagline.strip()
        cleaned_accent_color = accent_color.strip()
        (
            post_profile_variant,
            post_accent_style,
            post_border_style,
            post_title_style,
            post_density,
        ) = _apply_post_style_preset(
            post_style_preset.strip(),
            post_profile_variant=post_profile_variant,
            post_accent_style=post_accent_style,
            post_border_style=post_border_style,
            post_title_style=post_title_style,
            post_density=post_density,
        )
        cleaned_post_profile_variant = post_profile_variant.strip() or "bio"
        _ensure_enabled_style_value(
            cleaned_post_profile_variant,
            style_policy.enabled_profile_variants,
            POST_PROFILE_VARIANTS,
            "post profile variant",
        )
        cleaned_post_accent_style = post_accent_style.strip() or "soft"
        _ensure_enabled_style_value(
            cleaned_post_accent_style,
            style_policy.enabled_accent_styles,
            POST_ACCENT_STYLES,
            "post accent style",
        )
        cleaned_post_border_style = post_border_style.strip() or "hairline"
        _ensure_enabled_style_value(
            cleaned_post_border_style,
            style_policy.enabled_border_styles,
            POST_BORDER_STYLES,
            "post border style",
        )
        cleaned_post_title_style = post_title_style.strip() or "standard"
        _ensure_enabled_style_value(
            cleaned_post_title_style,
            style_policy.enabled_title_styles,
            POST_TITLE_STYLES,
            "post title style",
        )
        cleaned_post_density = post_density.strip() or "calm"
        _ensure_enabled_style_value(
            cleaned_post_density,
            style_policy.enabled_densities,
            POST_DENSITIES,
            "post density",
        )
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
            post_profile_variant=cleaned_post_profile_variant,
            post_accent_style=cleaned_post_accent_style,
            post_border_style=cleaned_post_border_style,
            post_title_style=cleaned_post_title_style,
            post_density=cleaned_post_density,
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
        post_profile_variant: str = "bio",
        post_accent_style: str = "soft",
        post_border_style: str = "hairline",
        post_title_style: str = "standard",
        post_density: str = "calm",
        post_style_preset: str = "",
    ) -> Character:
        viewer = self.viewer()
        style_policy = _post_style_policy(viewer.community)
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
        (
            post_profile_variant,
            post_accent_style,
            post_border_style,
            post_title_style,
            post_density,
        ) = _apply_post_style_preset(
            post_style_preset.strip(),
            post_profile_variant=post_profile_variant,
            post_accent_style=post_accent_style,
            post_border_style=post_border_style,
            post_title_style=post_title_style,
            post_density=post_density,
        )
        cleaned_post_profile_variant = post_profile_variant.strip() or "bio"
        _ensure_enabled_style_value(
            cleaned_post_profile_variant,
            style_policy.enabled_profile_variants,
            POST_PROFILE_VARIANTS,
            "post profile variant",
            current_value=character.post_profile_variant,
        )
        cleaned_post_accent_style = post_accent_style.strip() or "soft"
        _ensure_enabled_style_value(
            cleaned_post_accent_style,
            style_policy.enabled_accent_styles,
            POST_ACCENT_STYLES,
            "post accent style",
            current_value=character.post_accent_style,
        )
        cleaned_post_border_style = post_border_style.strip() or "hairline"
        _ensure_enabled_style_value(
            cleaned_post_border_style,
            style_policy.enabled_border_styles,
            POST_BORDER_STYLES,
            "post border style",
            current_value=character.post_border_style,
        )
        cleaned_post_title_style = post_title_style.strip() or "standard"
        _ensure_enabled_style_value(
            cleaned_post_title_style,
            style_policy.enabled_title_styles,
            POST_TITLE_STYLES,
            "post title style",
            current_value=character.post_title_style,
        )
        cleaned_post_density = post_density.strip() or "calm"
        _ensure_enabled_style_value(
            cleaned_post_density,
            style_policy.enabled_densities,
            POST_DENSITIES,
            "post density",
            current_value=character.post_density,
        )
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
            post_profile_variant=cleaned_post_profile_variant,
            post_accent_style=cleaned_post_accent_style,
            post_border_style=cleaned_post_border_style,
            post_title_style=cleaned_post_title_style,
            post_density=cleaned_post_density,
        )

    def update_post(self, board_slug: str, thread_slug: str, post_id: int, body: str) -> Post:
        return _update_post(self.repo, self.viewer(), board_slug, thread_slug, post_id, body)

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
        return _update_thread_scene(
            self.repo,
            self.viewer(),
            board_slug,
            thread_slug,
            status=status,
            location=location,
            timeline=timeline,
            summary=summary,
            posting_mode=posting_mode,
            participant_ids=participant_ids,
        )

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
        return _reply_to_thread(
            self.repo, self.viewer(), board_slug, thread_slug, character_id, body
        )

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
        return _start_thread(
            self.repo,
            self.viewer(),
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
        )

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
    boards = sorted(
        repo.list_boards(community_id),
        key=lambda board: (board.navigation_order, board.name, board.id),
    )
    for board in boards:
        if not board.show_in_navigation:
            continue
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


def _latest_thread(threads: list[Thread]) -> Thread | None:
    if not threads:
        return None
    return max(threads, key=lambda thread: (_timestamp_key(thread.updated_at), thread.id))


def _post_style_policy(community: Community) -> PostStylePolicy:
    return PostStylePolicy(
        enabled_profile_variants=tuple(
            _stored_style_values(
                community.enabled_post_profile_variants,
                POST_PROFILE_VARIANTS,
            )
        ),
        enabled_accent_styles=tuple(
            _stored_style_values(
                community.enabled_post_accent_styles,
                POST_ACCENT_STYLES,
            )
        ),
        enabled_border_styles=tuple(
            _stored_style_values(
                community.enabled_post_border_styles,
                POST_BORDER_STYLES,
            )
        ),
        enabled_title_styles=tuple(
            _stored_style_values(
                community.enabled_post_title_styles,
                POST_TITLE_STYLES,
            )
        ),
        enabled_densities=tuple(
            _stored_style_values(
                community.enabled_post_densities,
                POST_DENSITIES,
            )
        ),
    )


def _stored_style_values(raw_values: str, allowed_values: tuple[str, ...]) -> list[str]:
    values = [value.strip() for value in raw_values.split(",") if value.strip()]
    cleaned = [value for value in values if value in allowed_values]
    return cleaned or list(allowed_values)


def _clean_enabled_style_values(
    values: list[str],
    allowed_values: tuple[str, ...],
    label: str,
) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        candidate = value.strip()
        if candidate in allowed_values and candidate not in cleaned:
            cleaned.append(candidate)
    if not cleaned:
        raise ValueError(f"choose at least one {label}")
    return cleaned


def _board_taxonomy_item(
    summary: BoardSummary,
    *,
    parent: Board | None,
    child_count: int,
) -> BoardTaxonomyItem:
    kind = normalize_board_kind(summary.board.board_kind)
    return BoardTaxonomyItem(
        summary=summary,
        parent=parent,
        child_count=child_count,
        kind_label=BOARD_KIND_LABELS[kind],
        realm_label=BOARD_KIND_REALMS[kind],
        sidebar_label=BOARD_KIND_SIDEBAR_LABELS[kind],
        guidance=BOARD_KIND_GUIDANCE[kind],
    )


def _validate_board_parent(
    boards: list[Board],
    board: Board,
    board_kind: BoardKind,
    parent_board_id: int | None,
) -> int | None:
    if board_kind != "sublocation":
        return None
    if parent_board_id is None:
        raise ValueError("choose a parent location for sublocations")
    boards_by_id = {candidate.id: candidate for candidate in boards}
    parent = boards_by_id.get(parent_board_id)
    if parent is None:
        raise LookupError(
            f"board parent not found in community {board.community_id}: {parent_board_id}"
        )
    if parent.id == board.id:
        raise ValueError("board cannot be its own parent")
    if parent.parent_board_id is not None or parent.board_kind != "location":
        raise ValueError("choose a major location parent for sublocations")
    return parent.id


def _navigation_preview_sections(
    board_taxonomy: list[BoardTaxonomyItem],
    *,
    current_event: MaterialSummary | None,
    unread_notification_count: int,
    active_face: Character | None,
    open_wanted_ads: list[WantedAdSummary],
) -> list[NavigationPreviewSection]:
    location_items = [
        NavigationPreviewItem(
            label=item.board.name,
            href=item.summary.href,
            source_label="Board-derived",
            behavior_label=(
                f"{item.child_count} sublocations" if item.child_count else "Major location"
            ),
            count=item.summary.unread_thread_count or None,
        )
        for item in board_taxonomy
        if item.board.show_in_navigation
        and item.board.parent_board_id is None
        and item.board.board_kind == "location"
    ]
    community_items = [
        NavigationPreviewItem(
            label=item.board.name,
            href=item.summary.href,
            source_label="Board-derived",
            behavior_label=item.kind_label,
            count=item.summary.unread_thread_count or None,
        )
        for item in board_taxonomy
        if item.board.show_in_navigation
        and item.board.parent_board_id is None
        and item.board.board_kind in {"community", "archive"}
    ]
    desk_board_items = [
        NavigationPreviewItem(
            label=item.board.name,
            href=item.summary.href,
            source_label="Board-derived",
            behavior_label=item.kind_label,
            count=item.summary.unread_thread_count or None,
        )
        for item in board_taxonomy
        if item.board.show_in_navigation and item.board.board_kind == "desk"
    ]
    staff_board_items = [
        NavigationPreviewItem(
            label=item.board.name,
            href=item.summary.href,
            source_label="Board-derived",
            behavior_label=item.kind_label,
            count=item.summary.unread_thread_count or None,
        )
        for item in board_taxonomy
        if item.board.show_in_navigation and item.board.board_kind == "staff"
    ]
    studio_items = [
        NavigationPreviewItem("Overview", "/studio", "App-owned", "Realm home"),
        NavigationPreviewItem(
            "Board taxonomy",
            "/studio#board-taxonomy",
            "App-owned",
            "Production control",
        ),
        NavigationPreviewItem(
            "Navigation composer",
            "/studio#navigation-composer",
            "App-owned",
            "Production preview",
        ),
        NavigationPreviewItem("Guidebook", "/world", "App-owned", "Cross-realm shortcut"),
        NavigationPreviewItem("World map", "/", "App-owned", "Cross-realm shortcut"),
        NavigationPreviewItem("Applications", "/applications", "App-owned", "Production queue"),
        NavigationPreviewItem("Wanted board", "/wanted", "App-owned", "Casting surface"),
        NavigationPreviewItem("Casting desk", "/casting", "App-owned", "Casting queue"),
    ]
    if current_event is not None:
        studio_items.append(
            NavigationPreviewItem(
                current_event.material.title,
                f"/world/{current_event.material.slug}",
                "Material-derived",
                "Current event",
            )
        )
    studio_items.extend(staff_board_items)
    return [
        NavigationPreviewSection(
            realm_label="World",
            title="World sidebar",
            description=(
                "App-owned gateways stay fixed; board-derived location and community "
                "links follow taxonomy and sort order."
            ),
            items=[
                NavigationPreviewItem("Overview", "/", "App-owned", "Realm home"),
                NavigationPreviewItem(
                    "Locations",
                    "/locations",
                    "App-owned",
                    "Location index",
                    len(location_items),
                ),
                *location_items,
                NavigationPreviewItem(
                    "Community",
                    "/community",
                    "App-owned",
                    "Community index",
                    len(community_items),
                ),
                NavigationPreviewItem("Members", "/members", "App-owned", "Directory"),
                *community_items,
            ],
        ),
        NavigationPreviewSection(
            realm_label="Writer Desk",
            title="Desk sidebar",
            description=(
                "Writing operations stay app-owned; future desk boards can join this lane "
                "without becoming world locations."
            ),
            items=[
                NavigationPreviewItem("Overview", "/desk", "App-owned", "Realm home"),
                NavigationPreviewItem("Queue", "/my/threads", "App-owned", "Writing lane"),
                NavigationPreviewItem(
                    "Inbox",
                    "/notifications",
                    "App-owned",
                    "Attention surface",
                    unread_notification_count or None,
                ),
                NavigationPreviewItem("Roster", "/characters", "App-owned", "Identity lane"),
                NavigationPreviewItem("Plotting", "/plotting", "App-owned", "Collaboration"),
                NavigationPreviewItem("Applications", "/applications", "App-owned", "Intake"),
                NavigationPreviewItem("Discovery", "/discover", "App-owned", "Find play"),
                *desk_board_items,
            ],
        ),
        NavigationPreviewSection(
            realm_label="Studio",
            title="Studio sidebar",
            description=(
                "Director production controls stay visible; staff boards can be added as "
                "board-derived Studio lanes."
            ),
            items=studio_items,
        ),
        NavigationPreviewSection(
            realm_label="Wanted",
            title="Casting sidebar",
            description=(
                "Casting navigation stays lean: app-owned surfaces first, then the active "
                "face and context-specific wants."
            ),
            items=[
                NavigationPreviewItem("Wanted board", "/wanted", "App-owned", "Realm home"),
                NavigationPreviewItem("Casting desk", "/casting", "App-owned", "Pipeline"),
                NavigationPreviewItem("Applications", "/applications", "App-owned", "Intake"),
                NavigationPreviewItem(
                    active_face.name if active_face else "Active face",
                    f"/characters/{active_face.slug}" if active_face else "/characters",
                    "Identity-derived",
                    "Current lens" if active_face else "Choose a face",
                ),
                NavigationPreviewItem(
                    "Open wants",
                    "/wanted",
                    "Wanted-derived",
                    "Context list",
                    len(open_wanted_ads) or None,
                ),
            ],
        ),
    ]


def _ensure_enabled_style_value(
    value: str,
    enabled_values: tuple[str, ...],
    allowed_values: tuple[str, ...],
    label: str,
    *,
    current_value: str | None = None,
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{label} is not supported")
    if value not in enabled_values and value != current_value:
        raise ValueError(f"{label} is not available in this community")


def _apply_post_style_preset(
    preset_slug: str,
    *,
    post_profile_variant: str,
    post_accent_style: str,
    post_border_style: str,
    post_title_style: str,
    post_density: str,
) -> tuple[str, str, str, str, str]:
    preset = POST_STYLE_PRESETS.get(preset_slug)
    if preset is None:
        return (
            post_profile_variant,
            post_accent_style,
            post_border_style,
            post_title_style,
            post_density,
        )
    return (
        preset["post_profile_variant"],
        preset["post_accent_style"],
        preset["post_border_style"],
        preset["post_title_style"],
        preset["post_density"],
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


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "character"
