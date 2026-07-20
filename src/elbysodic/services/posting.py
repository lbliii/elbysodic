"""Composer search and posting workflows."""

from __future__ import annotations

import re
from contextlib import AbstractContextManager
from typing import Protocol, cast

from elbysodic.domain.models import (
    Board,
    Character,
    CommunityMembership,
    Post,
    PostRevision,
    Thread,
    ThreadParticipant,
    ThreadWatch,
)
from elbysodic.services import policies
from elbysodic.services.notifications import (
    NotificationRepository,
    notify_post_created,
)
from elbysodic.services.posts import post_revision_view, post_view
from elbysodic.services.read_models import (
    CreatedThread,
    EditablePostView,
    ForumView,
    Mentionable,
    MentionableScope,
    PostRevisionHistory,
)
from elbysodic.services.threads import (
    clean_participant_ids,
    clean_posting_mode,
    clean_thread_status,
    clean_thread_visibility,
    taggable_characters,
)


class PostingRepository(NotificationRepository, Protocol):
    def transaction(self) -> AbstractContextManager[None]: ...

    def get_board_by_slug(self, community_id: int, slug: str) -> Board: ...

    def get_thread_by_slug(self, community_id: int, board_id: int, slug: str) -> Thread: ...

    def create_thread(
        self,
        community_id: int,
        board_id: int,
        author_character_id: int,
        slug: str,
        title: str,
        *,
        status: str = "active",
        visibility: str = "members",
        location: str = "",
        timeline: str = "",
        summary: str = "",
        posting_mode: str = "freeform",
    ) -> Thread: ...

    def update_thread_scene(
        self,
        community_id: int,
        thread_id: int,
        *,
        status: str,
        visibility: str | None = None,
        location: str = "",
        timeline: str = "",
        summary: str = "",
        posting_mode: str = "freeform",
    ) -> Thread: ...

    def list_threads(self, community_id: int, board_id: int | None = None) -> list[Thread]: ...

    def set_thread_participants(
        self,
        community_id: int,
        thread_id: int,
        character_ids: list[int],
    ) -> list[Character]: ...

    def add_thread_participant(
        self,
        community_id: int,
        thread_id: int,
        character_id: int,
    ) -> ThreadParticipant: ...

    def create_post(
        self,
        community_id: int,
        thread_id: int,
        author_character_id: int,
        body: str,
    ) -> Post: ...

    def list_posts(self, community_id: int, thread_id: int) -> list[Post]: ...

    def get_post_by_number(self, community_id: int, thread_id: int, post_number: int) -> Post: ...

    def create_post_revision(
        self,
        community_id: int,
        post_id: int,
        editor_membership_id: int,
        previous_body: str,
        new_body: str,
    ) -> PostRevision: ...

    def update_post_body(self, community_id: int, post_id: int, body: str) -> Post: ...

    def list_post_revisions(self, community_id: int, post_id: int) -> list[PostRevision]: ...

    def watch_thread(
        self,
        community_id: int,
        thread_id: int,
        membership_id: int,
    ) -> ThreadWatch: ...

    def mark_thread_read(self, community_id: int, thread_id: int, membership_id: int) -> None: ...

    def search_characters(
        self,
        community_id: int,
        query: str,
        *,
        limit: int = 10,
        exclude_membership_ids: list[int] | None = None,
    ) -> list[Character]: ...

    def search_memberships(
        self,
        community_id: int,
        query: str,
        *,
        limit: int = 10,
    ) -> list[CommunityMembership]: ...

    def list_community_characters(self, community_id: int) -> list[Character]: ...


def search_mentionables(
    repo: PostingRepository,
    viewer: ForumView,
    query: str,
    *,
    scope: str = "all",
    limit: int = 8,
) -> list[Mentionable]:
    mention_scope = clean_mentionable_scope(scope)
    cleaned_query = query.strip().lstrip("@")
    if not cleaned_query:
        return []

    items: list[Mentionable] = []
    if mention_scope in {"all", "cast", "characters"}:
        excluded_memberships = [viewer.membership.id] if mention_scope == "cast" else []
        characters = repo.search_characters(
            viewer.community.id,
            cleaned_query,
            limit=limit,
            exclude_membership_ids=excluded_memberships,
        )
        items.extend(character_mentionable(character) for character in characters)

    remaining = max(0, limit - len(items))
    if remaining and mention_scope in {"all", "writers", "ooc"}:
        memberships = repo.search_memberships(
            viewer.community.id,
            cleaned_query,
            limit=remaining,
        )
        items.extend(membership_mentionable(membership) for membership in memberships)

    return items[:limit]


def read_post_editor(
    repo: PostingRepository,
    viewer: ForumView,
    board_slug: str,
    thread_slug: str,
    post_number: int,
) -> EditablePostView:
    board, thread, post = editable_post(repo, viewer, board_slug, thread_slug, post_number)
    return EditablePostView(
        board=board,
        thread=thread,
        post=post_view(
            repo,
            viewer.community.id,
            post,
            viewer_membership=viewer.membership,
            viewer_role=viewer.role,
        ),
    )


def read_post_revisions(
    repo: PostingRepository,
    viewer: ForumView,
    board_slug: str,
    thread_slug: str,
    post_number: int,
) -> PostRevisionHistory:
    board, thread, post = editable_post(repo, viewer, board_slug, thread_slug, post_number)
    revisions = [
        post_revision_view(repo, viewer.community.id, revision)
        for revision in repo.list_post_revisions(viewer.community.id, post.id)
    ]
    return PostRevisionHistory(
        board=board,
        thread=thread,
        post=post_view(
            repo,
            viewer.community.id,
            post,
            viewer_membership=viewer.membership,
            viewer_role=viewer.role,
        ),
        revisions=revisions,
    )


def update_post(
    repo: PostingRepository,
    viewer: ForumView,
    board_slug: str,
    thread_slug: str,
    post_number: int,
    body: str,
) -> Post:
    _board, _thread, post = editable_post(repo, viewer, board_slug, thread_slug, post_number)
    cleaned = body.strip()
    if not cleaned:
        raise ValueError("post body is required")
    if cleaned == post.body:
        return post
    repo.create_post_revision(
        viewer.community.id,
        post.id,
        viewer.membership.id,
        post.body,
        cleaned,
    )
    return repo.update_post_body(viewer.community.id, post.id, cleaned)


def update_thread_scene(
    repo: PostingRepository,
    viewer: ForumView,
    board_slug: str,
    thread_slug: str,
    *,
    status: str,
    visibility: str | None = None,
    location: str = "",
    timeline: str = "",
    summary: str = "",
    posting_mode: str = "freeform",
    participant_ids: list[int] | None = None,
) -> Thread:
    _board, thread = visible_thread(repo, viewer, board_slug, thread_slug)
    if not can_manage_scene(viewer, thread):
        raise PermissionError(f"membership {viewer.membership.id} cannot manage scene {thread.id}")
    cleaned_status = clean_thread_status(status)
    cleaned_visibility = None if visibility is None else clean_thread_visibility(visibility)
    cleaned_posting_mode = clean_posting_mode(posting_mode)
    repo.update_thread_scene(
        viewer.community.id,
        thread.id,
        status=cleaned_status,
        visibility=cleaned_visibility,
        location=location.strip(),
        timeline=timeline.strip(),
        summary=summary.strip(),
        posting_mode=cleaned_posting_mode,
    )
    posted_character_ids = {
        post.author_character_id for post in repo.list_posts(viewer.community.id, thread.id)
    }
    required_ids = [thread.author_character_id, *posted_character_ids]
    taggable_ids = {
        character.id
        for character in taggable_characters(
            repo.list_community_characters(viewer.community.id),
            viewer.roster,
        )
    }
    tag_ids = [
        character_id
        for character_id in clean_participant_ids(participant_ids or [])
        if character_id in taggable_ids
    ]
    repo.set_thread_participants(
        viewer.community.id,
        thread.id,
        clean_participant_ids([*required_ids, *tag_ids]),
    )
    return repo.get_thread(viewer.community.id, thread.id)


def join_thread_as_current_character(
    repo: PostingRepository,
    viewer: ForumView,
    board_slug: str,
    thread_slug: str,
) -> None:
    if viewer.current_character is None:
        raise ValueError("create a character before joining a scene")
    _board, thread = visible_thread(repo, viewer, board_slug, thread_slug)
    if thread.status != "open" or thread.is_locked:
        raise PermissionError(f"thread {thread.id} is not open to join")
    if not policies.can_reply(viewer.membership, thread, viewer.role):
        raise PermissionError(f"membership {viewer.membership.id} cannot join thread {thread.id}")
    if not policies.can_story_act_as(viewer.membership, viewer.current_character):
        raise PermissionError(
            f"membership {viewer.membership.id} cannot use character {viewer.current_character.id}"
        )
    repo.add_thread_participant(
        viewer.community.id,
        thread.id,
        viewer.current_character.id,
    )
    repo.watch_thread(viewer.community.id, thread.id, viewer.membership.id)


def reply_to_thread(
    repo: PostingRepository,
    viewer: ForumView,
    board_slug: str,
    thread_slug: str,
    character_id: int,
    body: str,
) -> Post:
    character = repo.get_character(viewer.community.id, character_id)
    if not policies.can_story_act_as(viewer.membership, character):
        raise PermissionError(
            f"membership {viewer.membership.id} cannot use character {character_id}"
        )
    _board, thread = visible_thread(repo, viewer, board_slug, thread_slug)
    if not policies.can_reply(viewer.membership, thread, viewer.role):
        raise PermissionError(
            f"membership {viewer.membership.id} cannot reply to thread {thread.id}"
        )
    cleaned = body.strip()
    if not cleaned:
        raise ValueError("reply body is required")
    with repo.transaction():
        post = repo.create_post(viewer.community.id, thread.id, character.id, cleaned)
        notify_post_created(repo, viewer, thread, post)
        repo.watch_thread(viewer.community.id, thread.id, viewer.membership.id)
        repo.mark_thread_read(viewer.community.id, thread.id, viewer.membership.id)
    return post


def start_thread(
    repo: PostingRepository,
    viewer: ForumView,
    *,
    board_slug: str,
    character_id: int,
    title: str,
    body: str,
    status: str = "active",
    visibility: str = "members",
    location: str = "",
    timeline: str = "",
    summary: str = "",
    posting_mode: str = "freeform",
    participant_ids: list[int] | None = None,
) -> CreatedThread:
    character = repo.get_character(viewer.community.id, character_id)
    if not policies.can_story_act_as(viewer.membership, character):
        raise PermissionError(
            f"membership {viewer.membership.id} cannot use character {character_id}"
        )
    board = repo.get_board_by_slug(viewer.community.id, board_slug)
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
    cleaned_status = clean_thread_status(status)
    cleaned_visibility = clean_thread_visibility(visibility)
    cleaned_posting_mode = clean_posting_mode(posting_mode)
    taggable_ids = {
        item.id
        for item in taggable_characters(
            repo.list_community_characters(viewer.community.id),
            viewer.roster,
        )
    }
    tag_ids = [
        participant_id
        for participant_id in clean_participant_ids(participant_ids or [])
        if participant_id in taggable_ids
    ]
    cleaned_participant_ids = clean_participant_ids([character.id, *tag_ids])
    slug = unique_thread_slug(repo, viewer.community.id, board.id, cleaned_title)
    with repo.transaction():
        thread = repo.create_thread(
            viewer.community.id,
            board.id,
            character.id,
            slug,
            cleaned_title,
            status=cleaned_status,
            visibility=cleaned_visibility,
            location=location.strip(),
            timeline=timeline.strip(),
            summary=summary.strip(),
            posting_mode=cleaned_posting_mode,
        )
        repo.set_thread_participants(
            viewer.community.id,
            thread.id,
            cleaned_participant_ids,
        )
        post = repo.create_post(viewer.community.id, thread.id, character.id, cleaned_body)
        thread = repo.get_thread(viewer.community.id, thread.id)
        repo.watch_thread(viewer.community.id, thread.id, viewer.membership.id)
        repo.mark_thread_read(viewer.community.id, thread.id, viewer.membership.id)
    return CreatedThread(thread=thread, post=post)


def visible_thread(
    repo: PostingRepository,
    viewer: ForumView,
    board_slug: str,
    thread_slug: str,
) -> tuple[Board, Thread]:
    board = repo.get_board_by_slug(viewer.community.id, board_slug)
    if not policies.can_view_board(viewer.membership, board, viewer.role):
        raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
    thread = repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
    return board, thread


def editable_post(
    repo: PostingRepository,
    viewer: ForumView,
    board_slug: str,
    thread_slug: str,
    post_number: int,
) -> tuple[Board, Thread, Post]:
    board, thread = visible_thread(repo, viewer, board_slug, thread_slug)
    post = repo.get_post_by_number(viewer.community.id, thread.id, post_number)
    if not policies.can_edit_post(viewer.membership, post, viewer.role):
        raise PermissionError(f"membership {viewer.membership.id} cannot edit post {post.id}")
    return board, thread, post


def can_manage_scene(viewer: ForumView, thread: Thread) -> bool:
    return thread.author_membership_id == viewer.membership.id or policies.can_moderate_thread(
        viewer.membership,
        thread,
        viewer.role,
    )


def clean_mentionable_scope(value: str) -> MentionableScope:
    scope = value.strip().lower().replace("-", "_")
    if scope not in {"all", "cast", "characters", "writers", "ooc"}:
        return "all"
    return cast(MentionableScope, scope)


def character_mentionable(character: Character) -> Mentionable:
    return Mentionable(
        kind="character",
        id=character.id,
        handle=character.slug,
        label=character.name,
        detail="Character",
        avatar_url=character.avatar_url,
        href=f"/characters/{character.slug}",
    )


def membership_mentionable(membership: CommunityMembership) -> Mentionable:
    return Mentionable(
        kind="writer",
        id=membership.id,
        handle=membership.username,
        label=membership.display_name,
        detail=f"Writer @{membership.username}",
        avatar_url=membership.avatar_url,
        href=f"/members/{membership.username}",
    )


def unique_thread_slug(
    repo: PostingRepository,
    community_id: int,
    board_id: int,
    title: str,
) -> str:
    base = slugify(title)
    slug = base
    suffix = 2
    while True:
        try:
            repo.get_thread_by_slug(community_id, board_id, slug)
        except LookupError:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "thread"
