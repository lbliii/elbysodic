"""Service-layer commands and read models for the forum slice."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.db.seed import DemoSeed, seed_demo_forum
from elbysodic.domain.models import (
    Board,
    Character,
    Community,
    CommunityMembership,
    Post,
    Role,
    Thread,
)
from elbysodic.services import policies

DEFAULT_DATABASE_PATH = Path("var/elbysodic.sqlite3")
DATABASE_PATH_ENV = "ELBYSODIC_DB_PATH"


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


@dataclass(frozen=True, slots=True)
class PostView:
    post: Post
    author: Character
    author_membership: CommunityMembership
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
class CreatedThread:
    thread: Thread
    post: Post


@dataclass(frozen=True, slots=True)
class CharacterAppearance:
    post: Post
    thread: Thread
    board: Board


@dataclass(frozen=True, slots=True)
class CharacterProfile:
    character: Character
    is_default: bool
    post_count: int
    thread_count: int
    recent_posts: list[CharacterAppearance]


@dataclass(frozen=True, slots=True)
class ThreadView:
    board: Board
    thread: Thread
    posts: list[PostView]
    can_reply: bool
    is_unread: bool


@dataclass(frozen=True, slots=True)
class ForumView:
    community: Community
    membership: CommunityMembership
    role: Role
    current_character: Character
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
                        snippet=_snippet(post.body),
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

    def board_threads(self, board_slug: str) -> tuple[Board, list[ThreadSummary]]:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")

        summaries = []
        for thread in self.repo.list_threads(viewer.community.id, board.id):
            posts = self.repo.list_posts(viewer.community.id, thread.id)
            summaries.append(
                ThreadSummary(
                    thread=thread,
                    author=self.repo.get_character(viewer.community.id, thread.author_character_id),
                    author_membership=self.repo.get_membership(
                        viewer.community.id,
                        thread.author_membership_id,
                    ),
                    reply_count=max(0, len(posts) - 1),
                    latest_post=(
                        _post_view(self.repo, viewer.community.id, posts[-1]) if posts else None
                    ),
                    is_unread=_is_unread(
                        self.repo,
                        viewer.community.id,
                        viewer.membership.id,
                        thread,
                    ),
                )
            )
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
            _post_view(self.repo, viewer.community.id, post)
            for post in self.repo.list_posts(viewer.community.id, thread.id)
        ]
        self.repo.mark_thread_read(viewer.community.id, thread.id, viewer.membership.id)
        return ThreadView(
            board=board,
            thread=thread,
            posts=posts,
            can_reply=policies.can_reply(viewer.membership, thread, viewer.role),
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
            recent_posts.append(CharacterAppearance(post=post, thread=thread, board=board))
        return CharacterProfile(
            character=character,
            is_default=viewer.membership.default_character_id == character.id,
            post_count=len(posts),
            thread_count=len(threads),
            recent_posts=recent_posts,
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
) -> Character:
    if not roster:
        raise LookupError(f"membership {membership.id} does not have a character roster")
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


def _post_view(repo: ForumRepository, community_id: int, post: Post) -> PostView:
    return PostView(
        post=post,
        author=repo.get_character(community_id, post.author_character_id),
        author_membership=repo.get_membership(
            community_id,
            post.author_membership_id,
        ),
        created_at_label=_timestamp_label(post.created_at),
        updated_at_label=_timestamp_label(post.updated_at),
        anchor=f"post-{post.id}",
    )


def _snippet(value: str, *, limit: int = 130) -> str:
    cleaned = " ".join(value.split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 1].rstrip()}..."


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


def _unique_character_slug(repo: ForumRepository, community_id: int, name: str) -> str:
    base = _slugify(name)
    slug = base
    suffix = 2
    while True:
        try:
            repo.get_character_by_slug(community_id, slug)
        except LookupError:
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
