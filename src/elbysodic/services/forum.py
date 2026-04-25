"""Service-layer commands and read models for the forum slice."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.db.seed import DemoSeed, seed_demo_forum
from elbysodic.domain.models import (
    Board,
    Character,
    Community,
    CommunityMembership,
    Post,
    PostRevision,
    Role,
    Thread,
)
from elbysodic.services import policies
from elbysodic.services.markup import post_snippet, render_post_body

DEFAULT_DATABASE_PATH = Path("var/elbysodic.sqlite3")
DATABASE_PATH_ENV = "ELBYSODIC_DB_PATH"
type BoardThreadFilter = Literal["all", "unread", "attention", "mine", "pinned", "locked"]


@dataclass(frozen=True, slots=True)
class BoardSummary:
    board: Board
    thread_count: int
    post_count: int
    unread_thread_count: int
    latest_thread: Thread | None
    latest_post: PostView | None


@dataclass(frozen=True, slots=True)
class ThreadSummary:
    thread: Thread
    author: Character
    author_membership: CommunityMembership
    reply_count: int
    latest_post: PostView | None
    is_unread: bool
    is_mine: bool
    needs_attention: bool


@dataclass(frozen=True, slots=True)
class PostView:
    post: Post
    author: Character
    author_membership: CommunityMembership
    rendered_body: str
    snippet: str
    can_edit: bool
    is_edited: bool
    created_at_label: str
    updated_at_label: str
    anchor: str


@dataclass(frozen=True, slots=True)
class ActivityItem:
    board: Board
    thread: Thread
    post: PostView
    snippet: str
    is_unread: bool


@dataclass(frozen=True, slots=True)
class AttentionItem:
    board: Board
    thread: Thread
    latest_post: PostView
    reply_count: int
    snippet: str


@dataclass(frozen=True, slots=True)
class CreatedThread:
    thread: Thread
    post: Post


@dataclass(frozen=True, slots=True)
class EditablePostView:
    board: Board
    thread: Thread
    post: PostView


@dataclass(frozen=True, slots=True)
class PostRevisionView:
    revision: PostRevision
    editor_membership: CommunityMembership
    created_at_label: str


@dataclass(frozen=True, slots=True)
class PostRevisionHistory:
    board: Board
    thread: Thread
    post: PostView
    revisions: list[PostRevisionView]


@dataclass(frozen=True, slots=True)
class ThreadObligationItem:
    board: Board
    thread: Thread
    author: Character
    latest_post: PostView | None
    last_own_post: PostView | None
    reply_count: int
    is_unread: bool
    is_started_by_roster: bool
    needs_reply: bool
    waiting_on_others: bool


@dataclass(frozen=True, slots=True)
class CharacterThreadActivity:
    character: Character
    needs_reply: list[ThreadObligationItem]
    waiting_on_others: list[ThreadObligationItem]
    started_by_character: list[ThreadObligationItem]
    participated: list[ThreadObligationItem]


@dataclass(frozen=True, slots=True)
class CharacterRosterCard:
    character: Character
    is_default: bool
    activity: CharacterThreadActivity


@dataclass(frozen=True, slots=True)
class CharacterRosterDashboard:
    cards: list[CharacterRosterCard]


@dataclass(frozen=True, slots=True)
class MyThreadsDashboard:
    needs_reply: list[ThreadObligationItem]
    waiting_on_others: list[ThreadObligationItem]
    started_by_me: list[ThreadObligationItem]
    participated: list[ThreadObligationItem]
    selected_character: Character | None
    roster_activity: list[CharacterThreadActivity]


@dataclass(frozen=True, slots=True)
class CharacterAppearance:
    post: PostView
    thread: Thread
    board: Board


@dataclass(frozen=True, slots=True)
class CharacterProfile:
    character: Character
    is_default: bool
    post_count: int
    thread_count: int
    activity: CharacterThreadActivity
    recent_posts: list[CharacterAppearance]


@dataclass(frozen=True, slots=True)
class ThreadView:
    board: Board
    thread: Thread
    posts: list[PostView]
    can_reply: bool
    can_moderate: bool
    is_unread: bool


@dataclass(frozen=True, slots=True)
class ForumView:
    community: Community
    membership: CommunityMembership
    role: Role
    current_character: Character | None
    roster: list[Character]


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
        return ForumView(
            community=community,
            membership=membership,
            role=role,
            current_character=current_character,
            roster=roster,
        )

    def list_boards(self) -> list[BoardSummary]:
        viewer = self.viewer()
        summaries: list[BoardSummary] = []
        for board in self.repo.list_boards(viewer.community.id):
            if not policies.can_view_board(viewer.membership, board, viewer.role):
                continue
            threads = self.repo.list_threads(viewer.community.id, board.id)
            posts_by_thread = {
                thread.id: self.repo.list_posts(viewer.community.id, thread.id)
                for thread in threads
            }
            latest_thread = _latest_thread(threads)
            latest_thread_posts = posts_by_thread.get(latest_thread.id, []) if latest_thread else []
            latest_post = (
                _post_view(self.repo, viewer.community.id, latest_thread_posts[-1])
                if latest_thread_posts
                else None
            )
            summaries.append(
                BoardSummary(
                    board=board,
                    thread_count=len(threads),
                    post_count=sum(len(posts) for posts in posts_by_thread.values()),
                    unread_thread_count=sum(
                        1
                        for thread in threads
                        if _is_unread(
                            self.repo,
                            viewer.community.id,
                            viewer.membership.id,
                            thread,
                        )
                    ),
                    latest_thread=latest_thread,
                    latest_post=latest_post,
                )
            )
        return summaries

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
        sorted_items = self._thread_obligations(viewer, target_ids)
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
                )
                for character in viewer.roster
            ]
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

        summaries = []
        roster_character_ids = {character.id for character in viewer.roster}
        for thread in self.repo.list_threads(viewer.community.id, board.id):
            posts = self.repo.list_posts(viewer.community.id, thread.id)
            is_unread = _is_unread(
                self.repo,
                viewer.community.id,
                viewer.membership.id,
                thread,
            )
            is_mine = _thread_belongs_to_roster(thread, posts, roster_character_ids)
            latest_post = posts[-1] if posts else None
            summary = ThreadSummary(
                thread=thread,
                author=self.repo.get_character(viewer.community.id, thread.author_character_id),
                author_membership=self.repo.get_membership(
                    viewer.community.id,
                    thread.author_membership_id,
                ),
                reply_count=max(0, len(posts) - 1),
                latest_post=(
                    _post_view(self.repo, viewer.community.id, latest_post) if latest_post else None
                ),
                is_unread=is_unread,
                is_mine=is_mine,
                needs_attention=(
                    latest_post is not None
                    and _thread_needs_attention(
                        self.repo,
                        viewer.community.id,
                        viewer.membership.id,
                        thread,
                        latest_post,
                        roster_character_ids,
                    )
                ),
            )
            if _thread_matches_filter(summary, filter_by):
                summaries.append(summary)
        return board, summaries

    def can_start_thread(self, board: Board) -> bool:
        viewer = self.viewer()
        return policies.can_start_thread(viewer.membership, board, viewer.role)

    def read_thread(self, board_slug: str, thread_slug: str) -> ThreadView:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        is_unread = _is_unread(self.repo, viewer.community.id, viewer.membership.id, thread)
        posts = [
            _post_view(
                self.repo,
                viewer.community.id,
                post,
                viewer_membership=viewer.membership,
                viewer_role=viewer.role,
            )
            for post in self.repo.list_posts(viewer.community.id, thread.id)
        ]
        self.repo.mark_thread_read(viewer.community.id, thread.id, viewer.membership.id)
        return ThreadView(
            board=board,
            thread=thread,
            posts=posts,
            can_reply=policies.can_reply(viewer.membership, thread, viewer.role),
            can_moderate=policies.can_moderate_thread(
                viewer.membership,
                thread,
                viewer.role,
            ),
            is_unread=is_unread,
        )

    def set_default_character(self, character_id: int) -> ForumView:
        viewer = self.viewer()
        character = self.repo.get_character(viewer.community.id, character_id)
        if not policies.can_post_as(viewer.membership, character):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot use character {character_id}"
            )
        self.repo.set_default_character(viewer.community.id, viewer.membership.id, character_id)
        return self.viewer()

    def read_character(self, character_slug: str) -> CharacterProfile:
        viewer = self.viewer()
        character = self.repo.get_character_by_slug(viewer.community.id, character_slug)
        if character.membership_id != viewer.membership.id:
            raise PermissionError(
                f"membership {viewer.membership.id} cannot view character {character.id}"
            )
        posts = self.repo.list_posts_by_character(viewer.community.id, character.id)
        threads = self.repo.list_threads_by_character(viewer.community.id, character.id)
        recent_posts = []
        for post in posts[:5]:
            thread = self.repo.get_thread(viewer.community.id, post.thread_id)
            board = self.repo.get_board(viewer.community.id, thread.board_id)
            recent_posts.append(
                CharacterAppearance(
                    post=_post_view(self.repo, viewer.community.id, post),
                    thread=thread,
                    board=board,
                )
            )
        return CharacterProfile(
            character=character,
            is_default=viewer.membership.default_character_id == character.id,
            post_count=len(posts),
            thread_count=len(threads),
            activity=self._character_activity(viewer, character),
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
        make_default: bool = False,
    ) -> Character:
        viewer = self.viewer()
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("character name is required")
        cleaned_summary = summary.strip()
        cleaned_avatar_url = (avatar_url or "").strip() or None
        slug = _unique_character_slug(self.repo, viewer.community.id, cleaned_name)
        return self.repo.create_character(
            viewer.community.id,
            viewer.membership.id,
            slug,
            cleaned_name,
            avatar_url=cleaned_avatar_url,
            summary=cleaned_summary,
            make_default=make_default,
        )

    def update_character(
        self,
        character_slug: str,
        *,
        name: str,
        summary: str = "",
        avatar_url: str | None = None,
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
        self.repo.mark_thread_read(viewer.community.id, thread.id, viewer.membership.id)
        return post

    def start_thread(
        self,
        *,
        board_slug: str,
        character_id: int,
        title: str,
        body: str,
    ) -> Thread:
        return self.start_thread_with_post(
            board_slug=board_slug,
            character_id=character_id,
            title=title,
            body=body,
        ).thread

    def start_thread_with_post(
        self,
        *,
        board_slug: str,
        character_id: int,
        title: str,
        body: str,
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
        slug = _unique_thread_slug(self.repo, viewer.community.id, board.id, cleaned_title)
        thread = self.repo.create_thread(
            viewer.community.id,
            board.id,
            character.id,
            slug,
            cleaned_title,
        )
        post = self.repo.create_post(viewer.community.id, thread.id, character.id, cleaned_body)
        thread = self.repo.get_thread(viewer.community.id, thread.id)
        self.repo.mark_thread_read(viewer.community.id, thread.id, viewer.membership.id)
        return CreatedThread(thread=thread, post=post)

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

    def _character_activity(
        self,
        viewer: ForumView,
        character: Character,
    ) -> CharacterThreadActivity:
        items = self._thread_obligations(viewer, {character.id})
        return CharacterThreadActivity(
            character=character,
            needs_reply=[item for item in items if item.needs_reply],
            waiting_on_others=[item for item in items if item.waiting_on_others],
            started_by_character=[item for item in items if item.is_started_by_roster],
            participated=items,
        )

    def _roster_activity(self, viewer: ForumView) -> list[CharacterThreadActivity]:
        return [self._character_activity(viewer, character) for character in viewer.roster]

    def _thread_obligations(
        self,
        viewer: ForumView,
        target_character_ids: set[int],
    ) -> list[ThreadObligationItem]:
        if not target_character_ids:
            return []
        visible_boards = {
            board.id: board
            for board in self.repo.list_boards(viewer.community.id)
            if policies.can_view_board(viewer.membership, board, viewer.role)
        }
        items = []
        for thread in self.repo.list_threads(viewer.community.id):
            board = visible_boards.get(thread.board_id)
            if board is None:
                continue
            posts = self.repo.list_posts(viewer.community.id, thread.id)
            if not _thread_belongs_to_roster(thread, posts, target_character_ids):
                continue
            latest_post = posts[-1] if posts else None
            last_own_post = _last_roster_post(posts, target_character_ids)
            needs_reply = (
                latest_post is not None
                and latest_post.author_character_id not in target_character_ids
                and not thread.is_locked
            )
            waiting_on_others = (
                latest_post is not None
                and latest_post.author_character_id in target_character_ids
                and not thread.is_locked
            )
            items.append(
                ThreadObligationItem(
                    board=board,
                    thread=thread,
                    author=self.repo.get_character(
                        viewer.community.id,
                        thread.author_character_id,
                    ),
                    latest_post=(
                        _post_view(self.repo, viewer.community.id, latest_post)
                        if latest_post
                        else None
                    ),
                    last_own_post=(
                        _post_view(self.repo, viewer.community.id, last_own_post)
                        if last_own_post
                        else None
                    ),
                    reply_count=max(0, len(posts) - 1),
                    is_unread=_is_unread(
                        self.repo,
                        viewer.community.id,
                        viewer.membership.id,
                        thread,
                    ),
                    is_started_by_roster=thread.author_character_id in target_character_ids,
                    needs_reply=needs_reply,
                    waiting_on_others=waiting_on_others,
                )
            )
        return sorted(
            items,
            key=lambda item: (_timestamp_key(item.thread.updated_at), item.thread.id),
            reverse=True,
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


def _latest_thread(threads: list[Thread]) -> Thread | None:
    if not threads:
        return None
    return max(threads, key=lambda thread: (_timestamp_key(thread.updated_at), thread.id))


def _is_unread(
    repo: ForumRepository,
    community_id: int,
    membership_id: int,
    thread: Thread,
) -> bool:
    read_at = repo.get_thread_read_at(community_id, thread.id, membership_id)
    if read_at is None:
        return True
    return _timestamp_key(read_at) < _timestamp_key(thread.updated_at)


def _thread_belongs_to_roster(
    thread: Thread,
    posts: list[Post],
    roster_character_ids: set[int],
) -> bool:
    if thread.author_character_id in roster_character_ids:
        return True
    return any(post.author_character_id in roster_character_ids for post in posts)


def _last_roster_post(posts: list[Post], roster_character_ids: set[int]) -> Post | None:
    for post in reversed(posts):
        if post.author_character_id in roster_character_ids:
            return post
    return None


def _thread_needs_attention(
    repo: ForumRepository,
    community_id: int,
    membership_id: int,
    thread: Thread,
    latest_post: Post,
    roster_character_ids: set[int],
) -> bool:
    return (
        _is_unread(repo, community_id, membership_id, thread)
        and latest_post.author_character_id not in roster_character_ids
    )


def _thread_matches_filter(summary: ThreadSummary, filter_by: BoardThreadFilter) -> bool:
    match filter_by:
        case "all":
            return True
        case "unread":
            return summary.is_unread
        case "attention":
            return summary.needs_attention
        case "mine":
            return summary.is_mine
        case "pinned":
            return summary.thread.is_pinned
        case "locked":
            return summary.thread.is_locked


def _post_view(
    repo: ForumRepository,
    community_id: int,
    post: Post,
    *,
    viewer_membership: CommunityMembership | None = None,
    viewer_role: Role | None = None,
) -> PostView:
    return PostView(
        post=post,
        author=repo.get_character(community_id, post.author_character_id),
        author_membership=repo.get_membership(
            community_id,
            post.author_membership_id,
        ),
        rendered_body=render_post_body(post.body),
        snippet=post_snippet(post.body),
        can_edit=(
            viewer_membership is not None
            and policies.can_edit_post(viewer_membership, post, viewer_role)
        ),
        is_edited=_timestamp_key(post.updated_at) > _timestamp_key(post.created_at),
        created_at_label=_timestamp_label(post.created_at),
        updated_at_label=_timestamp_label(post.updated_at),
        anchor=f"post-{post.id}",
    )


def _post_revision_view(
    repo: ForumRepository,
    community_id: int,
    revision: PostRevision,
) -> PostRevisionView:
    return PostRevisionView(
        revision=revision,
        editor_membership=repo.get_membership(community_id, revision.editor_membership_id),
        created_at_label=_timestamp_label(revision.created_at),
    )


def _timestamp_key(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min


def _timestamp_label(value: str) -> str:
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError:
        return value
    hour = stamp.hour % 12 or 12
    meridiem = "AM" if stamp.hour < 12 else "PM"
    zone = stamp.tzname() or "UTC"
    return f"{stamp:%b} {stamp.day}, {stamp.year} {hour}:{stamp.minute:02d} {meridiem} {zone}"


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
