"""Thread and scene read-model helpers."""

from __future__ import annotations

from typing import Protocol, cast

from elbysodic.domain.models import (
    Board,
    Character,
    CommunityMembership,
    Facet,
    FacetGroup,
    Post,
    Thread,
)
from elbysodic.services import policies
from elbysodic.services.episodes import EpisodeCreditsRepository, episode_credits
from elbysodic.services.facets import (
    FacetReadRepository,
    current_character_facet_ids,
    facet_tags,
    facet_tags_with_groups,
)
from elbysodic.services.posts import (
    PostViewContext,
    PostViewContextBuilder,
    PostViewRepository,
    post_view,
)
from elbysodic.services.read_models import (
    POSTING_MODES,
    THREAD_STATUSES,
    BoardThreadFilter,
    ForumView,
    PostingMode,
    ThreadNavigationItem,
    ThreadObligationItem,
    ThreadStatus,
    ThreadSummary,
    ThreadView,
)
from elbysodic.services.timestamps import timestamp_key


class ThreadReadRepository(
    EpisodeCreditsRepository,
    FacetReadRepository,
    PostViewRepository,
    Protocol,
):
    def get_board(self, community_id: int, board_id: int) -> Board: ...

    def list_boards(self, community_id: int) -> list[Board]: ...

    def list_threads(self, community_id: int, board_id: int | None = None) -> list[Thread]: ...

    def list_threads_for_boards(
        self,
        community_id: int,
        board_ids: list[int],
    ) -> dict[int, list[Thread]]: ...

    def get_thread_read_at(
        self,
        community_id: int,
        thread_id: int,
        membership_id: int,
    ) -> str | None: ...

    def thread_read_at_for_threads(
        self,
        community_id: int,
        thread_ids: list[int],
        membership_id: int,
    ) -> dict[int, str]: ...

    def list_posts(self, community_id: int, thread_id: int) -> list[Post]: ...

    def list_posts_for_threads(
        self,
        community_id: int,
        thread_ids: list[int],
    ) -> dict[int, list[Post]]: ...

    def get_character(self, community_id: int, character_id: int) -> Character: ...

    def list_characters_by_ids(
        self,
        community_id: int,
        character_ids: list[int],
    ) -> dict[int, Character]: ...

    def get_membership(
        self,
        community_id: int,
        membership_id: int,
    ) -> CommunityMembership: ...

    def list_memberships_by_ids(
        self,
        community_id: int,
        membership_ids: list[int],
    ) -> dict[int, CommunityMembership]: ...

    def list_thread_participants(self, community_id: int, thread_id: int) -> list[Character]: ...

    def list_thread_participants_for_threads(
        self,
        community_id: int,
        thread_ids: list[int],
    ) -> dict[int, list[Character]]: ...

    def list_thread_participant_ids(self, community_id: int, thread_id: int) -> set[int]: ...

    def list_facet_groups(self, community_id: int) -> list[FacetGroup]: ...

    def list_character_facets(self, community_id: int, character_id: int) -> list[Facet]: ...

    def list_thread_facets(self, community_id: int, thread_id: int) -> list[Facet]: ...

    def list_thread_facets_for_threads(
        self,
        community_id: int,
        thread_ids: list[int],
    ) -> dict[int, list[Facet]]: ...

    def list_board_facets(self, community_id: int, board_id: int) -> list[Facet]: ...

    def list_community_characters(self, community_id: int) -> list[Character]: ...

    def is_thread_watched(
        self,
        community_id: int,
        thread_id: int,
        membership_id: int,
    ) -> bool: ...


def board_thread_summaries(
    repo: ThreadReadRepository,
    viewer: ForumView,
    board: Board,
    *,
    filter_by: BoardThreadFilter = "all",
) -> list[ThreadSummary]:
    summaries = []
    current_facet_ids = current_character_facet_ids(repo, viewer)
    roster_character_ids = {character.id for character in viewer.roster}
    threads = repo.list_threads(viewer.community.id, board.id)
    thread_ids = [thread.id for thread in threads]
    posts_by_thread = repo.list_posts_for_threads(viewer.community.id, thread_ids)
    participants_by_thread = repo.list_thread_participants_for_threads(
        viewer.community.id,
        thread_ids,
    )
    facet_groups = repo.list_facet_groups(viewer.community.id)
    facets_by_thread = repo.list_thread_facets_for_threads(viewer.community.id, thread_ids)
    read_at_by_thread = repo.thread_read_at_for_threads(
        viewer.community.id,
        thread_ids,
        viewer.membership.id,
    )
    authors = repo.list_characters_by_ids(
        viewer.community.id,
        list({thread.author_character_id for thread in threads}),
    )
    author_memberships = repo.list_memberships_by_ids(
        viewer.community.id,
        list({thread.author_membership_id for thread in threads}),
    )
    post_context = PostViewContextBuilder(
        repo,
        viewer.community.id,
    ).context([post for posts in posts_by_thread.values() for post in posts])
    for thread in threads:
        summary = thread_summary(
            repo,
            viewer,
            thread,
            current_facet_ids=current_facet_ids,
            roster_character_ids=roster_character_ids,
            posts=posts_by_thread.get(thread.id, []),
            participants=participants_by_thread.get(thread.id, []),
            facet_groups=facet_groups,
            thread_facets=facets_by_thread.get(thread.id, []),
            authors=authors,
            author_memberships=author_memberships,
            post_context=post_context,
            read_at_by_thread=read_at_by_thread,
        )
        if thread_matches_filter(summary, filter_by):
            summaries.append(summary)
    return summaries


def thread_summary(
    repo: ThreadReadRepository,
    viewer: ForumView,
    thread: Thread,
    *,
    current_facet_ids: set[int],
    roster_character_ids: set[int],
    posts: list[Post] | None = None,
    participants: list[Character] | None = None,
    facet_groups: list[FacetGroup] | None = None,
    thread_facets: list[Facet] | None = None,
    authors: dict[int, Character] | None = None,
    author_memberships: dict[int, CommunityMembership] | None = None,
    post_context: PostViewContext | None = None,
    read_at_by_thread: dict[int, str] | None = None,
) -> ThreadSummary:
    posts = repo.list_posts(viewer.community.id, thread.id) if posts is None else posts
    participants = (
        repo.list_thread_participants(viewer.community.id, thread.id)
        if participants is None
        else participants
    )
    participant_ids = {character.id for character in participants}
    if facet_groups is None or thread_facets is None:
        thread_facet_tags = facet_tags(
            repo,
            viewer.community.id,
            repo.list_thread_facets(viewer.community.id, thread.id),
        )
    else:
        thread_facet_tags = facet_tags_with_groups(facet_groups, thread_facets)
    latest_post = posts[-1] if posts else None
    read_at = _read_at_for_thread(
        repo,
        viewer.community.id,
        viewer.membership.id,
        thread,
        read_at_by_thread,
    )
    first_unread = first_unread_post_from_read_at(thread, posts, read_at)
    author = (
        repo.get_character(viewer.community.id, thread.author_character_id)
        if authors is None
        else authors[thread.author_character_id]
    )
    author_membership = (
        repo.get_membership(
            viewer.community.id,
            thread.author_membership_id,
        )
        if author_memberships is None
        else author_memberships[thread.author_membership_id]
    )
    return ThreadSummary(
        thread=thread,
        author=author,
        author_membership=author_membership,
        participants=participants,
        facets=thread_facet_tags,
        is_relevant_to_current_face=bool(
            current_facet_ids
            and {tag.facet.id for tag in thread_facet_tags}.intersection(current_facet_ids)
        ),
        reply_count=max(0, len(posts) - 1),
        latest_post=(
            post_view(repo, viewer.community.id, latest_post, context=post_context)
            if latest_post
            else None
        ),
        first_unread_post=(
            post_view(repo, viewer.community.id, first_unread, context=post_context)
            if first_unread
            else None
        ),
        episode=episode_credits(repo, viewer.community.id, posts),
        is_unread=is_unread(
            repo,
            viewer.community.id,
            viewer.membership.id,
            thread,
            read_at_by_thread=read_at_by_thread,
        ),
        is_mine=thread_belongs_to_roster(
            thread,
            posts,
            roster_character_ids,
            participant_ids,
        ),
        needs_attention=(
            latest_post is not None
            and is_live_queue_thread(thread)
            and thread_needs_attention(
                repo,
                viewer.community.id,
                viewer.membership.id,
                thread,
                latest_post,
                roster_character_ids,
                read_at_by_thread=read_at_by_thread,
            )
        ),
    )


def next_unread_thread(
    repo: ThreadReadRepository,
    viewer: ForumView,
    board: Board,
) -> ThreadNavigationItem | None:
    threads = repo.list_threads(viewer.community.id, board.id)
    thread_ids = [thread.id for thread in threads]
    read_at_by_thread = repo.thread_read_at_for_threads(
        viewer.community.id,
        thread_ids,
        viewer.membership.id,
    )
    posts_by_thread = repo.list_posts_for_threads(viewer.community.id, thread_ids)
    all_posts = [post for posts in posts_by_thread.values() for post in posts]
    post_context = (
        PostViewContextBuilder(repo, viewer.community.id).context(all_posts) if all_posts else None
    )
    for thread in threads:
        if is_unread(
            repo,
            viewer.community.id,
            viewer.membership.id,
            thread,
            read_at_by_thread=read_at_by_thread,
        ):
            return thread_navigation_item(
                repo,
                viewer.community.id,
                viewer.membership.id,
                board,
                thread,
                posts=posts_by_thread.get(thread.id, []),
                read_at_by_thread=read_at_by_thread,
                post_context=post_context,
            )
    return None


def read_thread_view(
    repo: ThreadReadRepository,
    viewer: ForumView,
    board: Board,
    thread: Thread,
) -> ThreadView:
    board_threads = repo.list_threads(viewer.community.id, board.id)
    attention_threads = community_attention_threads(repo, viewer)
    roster_character_ids = {character.id for character in viewer.roster}
    previous_thread, next_thread, previous_unreplied, next_unread = thread_navigation(
        repo,
        viewer.community.id,
        viewer.membership.id,
        roster_character_ids,
        board,
        board_threads,
        attention_threads,
        thread,
    )
    unread = is_unread(repo, viewer.community.id, viewer.membership.id, thread)
    posts = [
        post_view(
            repo,
            viewer.community.id,
            post,
            viewer_membership=viewer.membership,
            viewer_role=viewer.role,
        )
        for post in repo.list_posts(viewer.community.id, thread.id)
    ]
    can_moderate = policies.can_moderate_thread(
        viewer.membership,
        thread,
        viewer.role,
    )
    can_manage_scene = can_moderate or thread.author_membership_id == viewer.membership.id
    participants = repo.list_thread_participants(viewer.community.id, thread.id)
    participant_ids = {character.id for character in participants}
    posted_character_ids = {item.post.author_character_id for item in posts}
    can_reply = policies.can_reply(viewer.membership, thread, viewer.role)
    return ThreadView(
        board=board,
        thread=thread,
        participants=participants,
        board_facets=facet_tags(
            repo,
            viewer.community.id,
            repo.list_board_facets(viewer.community.id, board.id),
        ),
        thread_facets=facet_tags(
            repo,
            viewer.community.id,
            repo.list_thread_facets(viewer.community.id, thread.id),
        ),
        taggable_characters=taggable_characters(
            repo.list_community_characters(viewer.community.id),
            viewer.roster,
        ),
        tagged_character_ids=repo.list_thread_participant_ids(
            viewer.community.id,
            thread.id,
        )
        - posted_character_ids
        - {thread.author_character_id},
        posts=posts,
        latest_post=posts[-1] if posts else None,
        episode=episode_credits(
            repo,
            viewer.community.id,
            [item.post for item in posts],
        ),
        reply_count=max(0, len(posts) - 1),
        can_reply=can_reply,
        can_join_scene=(
            viewer.current_character is not None
            and thread.status == "open"
            and not thread.is_locked
            and can_reply
            and viewer.current_character.id not in participant_ids
        ),
        can_moderate=can_moderate,
        can_manage_scene=can_manage_scene,
        moderation_boards=(
            [
                candidate
                for candidate in repo.list_boards(viewer.community.id)
                if policies.can_view_board(viewer.membership, candidate, viewer.role)
            ]
            if can_moderate
            else []
        ),
        is_unread=unread,
        previous_thread=previous_thread,
        next_thread=next_thread,
        previous_unreplied_thread=previous_unreplied,
        next_unread_thread=next_unread,
        is_watched=repo.is_thread_watched(
            viewer.community.id,
            thread.id,
            viewer.membership.id,
        ),
    )


def thread_obligations(
    repo: ThreadReadRepository,
    viewer: ForumView,
    target_character_ids: set[int],
) -> list[ThreadObligationItem]:
    if not target_character_ids:
        return []
    visible_boards = {
        board.id: board
        for board in repo.list_boards(viewer.community.id)
        if policies.can_view_board(viewer.membership, board, viewer.role)
    }
    candidate_threads = [
        thread
        for thread in repo.list_threads(viewer.community.id)
        if thread.board_id in visible_boards and is_live_queue_thread(thread)
    ]
    thread_ids = [thread.id for thread in candidate_threads]
    posts_by_thread = repo.list_posts_for_threads(viewer.community.id, thread_ids)
    participants_by_thread = repo.list_thread_participants_for_threads(
        viewer.community.id,
        thread_ids,
    )
    authors = repo.list_characters_by_ids(
        viewer.community.id,
        list({thread.author_character_id for thread in candidate_threads}),
    )
    author_memberships = repo.list_memberships_by_ids(
        viewer.community.id,
        list({thread.author_membership_id for thread in candidate_threads}),
    )
    read_at_by_thread = repo.thread_read_at_for_threads(
        viewer.community.id,
        thread_ids,
        viewer.membership.id,
    )
    post_context = PostViewContextBuilder(
        repo,
        viewer.community.id,
    ).context([post for posts in posts_by_thread.values() for post in posts])
    items = []
    for thread in candidate_threads:
        board = visible_boards[thread.board_id]
        posts = posts_by_thread.get(thread.id, [])
        participants = participants_by_thread.get(thread.id, [])
        participant_ids = {character.id for character in participants}
        if not thread_belongs_to_roster(
            thread,
            posts,
            target_character_ids,
            participant_ids,
        ):
            continue
        latest_post = posts[-1] if posts else None
        first_unread = first_unread_post_from_read_at(
            thread,
            posts,
            read_at_by_thread.get(thread.id),
        )
        last_own_post = last_roster_post(posts, target_character_ids)
        needs_reply = (
            latest_post is not None
            and latest_post.author_character_id not in target_character_ids
            and is_reply_obligation_thread(thread)
        )
        waiting_on_others = (
            latest_post is not None
            and latest_post.author_character_id in target_character_ids
            and is_reply_obligation_thread(thread)
        )
        items.append(
            ThreadObligationItem(
                board=board,
                thread=thread,
                author=authors[thread.author_character_id],
                author_membership=author_memberships[thread.author_membership_id],
                participants=participants,
                latest_post=(
                    post_view(repo, viewer.community.id, latest_post, context=post_context)
                    if latest_post
                    else None
                ),
                first_unread_post=(
                    post_view(repo, viewer.community.id, first_unread, context=post_context)
                    if first_unread
                    else None
                ),
                last_own_post=(
                    post_view(repo, viewer.community.id, last_own_post, context=post_context)
                    if last_own_post
                    else None
                ),
                episode=episode_credits(repo, viewer.community.id, posts),
                reply_count=max(0, len(posts) - 1),
                is_unread=is_unread(
                    repo,
                    viewer.community.id,
                    viewer.membership.id,
                    thread,
                    read_at_by_thread=read_at_by_thread,
                ),
                is_started_by_roster=thread.author_character_id in target_character_ids,
                needs_reply=needs_reply,
                waiting_on_others=waiting_on_others,
            )
        )
    return sorted(
        items,
        key=lambda item: (timestamp_key(item.thread.updated_at), item.thread.id),
        reverse=True,
    )


def is_unread(
    repo: ThreadReadRepository,
    community_id: int,
    membership_id: int,
    thread: Thread,
    *,
    read_at_by_thread: dict[int, str] | None = None,
) -> bool:
    read_at = _read_at_for_thread(repo, community_id, membership_id, thread, read_at_by_thread)
    if read_at is None:
        return True
    return timestamp_key(read_at) < timestamp_key(thread.updated_at)


def first_unread_post(
    repo: ThreadReadRepository,
    community_id: int,
    membership_id: int,
    thread: Thread,
    posts: list[Post],
) -> Post | None:
    read_at = repo.get_thread_read_at(community_id, thread.id, membership_id)
    return first_unread_post_from_read_at(thread, posts, read_at)


def first_unread_post_from_read_at(
    thread: Thread,
    posts: list[Post],
    read_at: str | None,
) -> Post | None:
    if not posts:
        return None
    if read_at is None:
        return posts[0]
    read_stamp = timestamp_key(read_at)
    if read_stamp >= timestamp_key(thread.updated_at):
        return None
    for post in posts:
        if timestamp_key(post.created_at) > read_stamp:
            return post
    return posts[-1]


def _read_at_for_thread(
    repo: ThreadReadRepository,
    community_id: int,
    membership_id: int,
    thread: Thread,
    read_at_by_thread: dict[int, str] | None,
) -> str | None:
    if read_at_by_thread is None:
        return repo.get_thread_read_at(community_id, thread.id, membership_id)
    return read_at_by_thread.get(thread.id)


def thread_navigation(
    repo: ThreadReadRepository,
    community_id: int,
    membership_id: int,
    roster_character_ids: set[int],
    board: Board,
    threads: list[Thread],
    attention_threads: list[tuple[Board, Thread]],
    current: Thread,
) -> tuple[
    ThreadNavigationItem | None,
    ThreadNavigationItem | None,
    ThreadNavigationItem | None,
    ThreadNavigationItem | None,
]:
    current_index = _thread_index(threads, current.id)
    if current_index is None:
        return None, None, None, None
    navigation_thread_ids = list(
        dict.fromkeys(
            [thread.id for thread in threads]
            + [candidate_thread.id for _, candidate_thread in attention_threads]
        )
    )
    posts_by_thread = repo.list_posts_for_threads(community_id, navigation_thread_ids)
    read_at_by_thread = repo.thread_read_at_for_threads(
        community_id,
        navigation_thread_ids,
        membership_id,
    )
    all_posts = [post for posts in posts_by_thread.values() for post in posts]
    post_context = (
        PostViewContextBuilder(repo, community_id).context(all_posts) if all_posts else None
    )
    previous_thread = (
        thread_navigation_item(
            repo,
            community_id,
            membership_id,
            board,
            threads[current_index - 1],
            posts=posts_by_thread.get(threads[current_index - 1].id, []),
            read_at_by_thread=read_at_by_thread,
            post_context=post_context,
        )
        if current_index > 0
        else None
    )
    next_thread = (
        thread_navigation_item(
            repo,
            community_id,
            membership_id,
            board,
            threads[current_index + 1],
            posts=posts_by_thread.get(threads[current_index + 1].id, []),
            read_at_by_thread=read_at_by_thread,
            post_context=post_context,
        )
        if current_index + 1 < len(threads)
        else None
    )
    attention_index = _thread_index(
        [candidate_thread for _, candidate_thread in attention_threads],
        current.id,
    )
    if attention_index is None:
        previous_attention_candidates = list(reversed(attention_threads))
        next_attention_candidates = attention_threads
    else:
        previous_attention_candidates = list(
            reversed(attention_threads[:attention_index]),
        ) + list(reversed(attention_threads[attention_index + 1 :]))
        next_attention_candidates = (
            attention_threads[attention_index + 1 :] + attention_threads[:attention_index]
        )
    previous_unreplied = None
    for candidate_board, thread in previous_attention_candidates:
        posts = posts_by_thread.get(thread.id, [])
        latest_post = posts[-1] if posts else None
        if (
            latest_post
            and thread_belongs_to_roster(thread, posts, roster_character_ids)
            and thread_needs_reply(thread, latest_post, roster_character_ids)
        ):
            previous_unreplied = thread_navigation_item(
                repo,
                community_id,
                membership_id,
                candidate_board,
                thread,
                posts=posts,
                read_at_by_thread=read_at_by_thread,
                post_context=post_context,
            )
            break
    next_unread = None
    for candidate_board, thread in next_attention_candidates:
        if is_unread(
            repo,
            community_id,
            membership_id,
            thread,
            read_at_by_thread=read_at_by_thread,
        ):
            next_unread = thread_navigation_item(
                repo,
                community_id,
                membership_id,
                candidate_board,
                thread,
                posts=posts_by_thread.get(thread.id, []),
                read_at_by_thread=read_at_by_thread,
                post_context=post_context,
            )
            break
    return previous_thread, next_thread, previous_unreplied, next_unread


def community_attention_threads(
    repo: ThreadReadRepository,
    viewer: ForumView,
) -> list[tuple[Board, Thread]]:
    candidates: list[tuple[Board, Thread]] = []
    visible_boards = [
        candidate_board
        for candidate_board in repo.list_boards(viewer.community.id)
        if policies.can_view_board(viewer.membership, candidate_board, viewer.role)
    ]
    threads_by_board = repo.list_threads_for_boards(
        viewer.community.id,
        [board.id for board in visible_boards],
    )
    for candidate_board in visible_boards:
        candidates.extend(
            (candidate_board, thread) for thread in threads_by_board.get(candidate_board.id, [])
        )
    return sorted(
        candidates,
        key=lambda item: (timestamp_key(item[1].updated_at), item[1].id),
        reverse=True,
    )


def thread_navigation_item(
    repo: ThreadReadRepository,
    community_id: int,
    membership_id: int,
    board: Board,
    thread: Thread,
    *,
    posts: list[Post] | None = None,
    read_at_by_thread: dict[int, str] | None = None,
    post_context: PostViewContext | None = None,
) -> ThreadNavigationItem:
    posts = repo.list_posts(community_id, thread.id) if posts is None else posts
    read_at = _read_at_for_thread(repo, community_id, membership_id, thread, read_at_by_thread)
    jump_post = first_unread_post_from_read_at(thread, posts, read_at)
    if jump_post is None and posts:
        jump_post = posts[-1]
    return ThreadNavigationItem(
        board=board,
        thread=thread,
        jump_post=(
            post_view(repo, community_id, jump_post, context=post_context) if jump_post else None
        ),
    )


def thread_belongs_to_roster(
    thread: Thread,
    posts: list[Post],
    roster_character_ids: set[int],
    participant_ids: set[int] | None = None,
) -> bool:
    if thread.author_character_id in roster_character_ids:
        return True
    if participant_ids and participant_ids.intersection(roster_character_ids):
        return True
    return any(post.author_character_id in roster_character_ids for post in posts)


def last_roster_post(posts: list[Post], roster_character_ids: set[int]) -> Post | None:
    for post in reversed(posts):
        if post.author_character_id in roster_character_ids:
            return post
    return None


def thread_needs_attention(
    repo: ThreadReadRepository,
    community_id: int,
    membership_id: int,
    thread: Thread,
    latest_post: Post,
    roster_character_ids: set[int],
    *,
    read_at_by_thread: dict[int, str] | None = None,
) -> bool:
    return (
        is_unread(
            repo,
            community_id,
            membership_id,
            thread,
            read_at_by_thread=read_at_by_thread,
        )
        and latest_post.author_character_id not in roster_character_ids
    )


def thread_needs_reply(
    thread: Thread,
    latest_post: Post,
    roster_character_ids: set[int],
) -> bool:
    return (
        is_reply_obligation_thread(thread)
        and latest_post.author_character_id not in roster_character_ids
    )


def thread_matches_filter(summary: ThreadSummary, filter_by: BoardThreadFilter) -> bool:
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


def is_live_queue_thread(thread: Thread) -> bool:
    return thread.status in {"open", "active"} and not thread.is_locked


def is_reply_obligation_thread(thread: Thread) -> bool:
    return is_live_queue_thread(thread)


def clean_thread_status(value: str) -> ThreadStatus:
    status = value.strip().lower().replace("-", "_")
    if status not in THREAD_STATUSES:
        raise ValueError("choose a valid thread status")
    return cast(ThreadStatus, status)


def clean_posting_mode(value: str) -> PostingMode:
    mode = value.strip().lower().replace("-", "_")
    if mode not in POSTING_MODES:
        raise ValueError("choose a valid posting mode")
    return cast(PostingMode, mode)


def clean_participant_ids(character_ids: list[int]) -> list[int]:
    cleaned: list[int] = []
    for character_id in character_ids:
        if character_id not in cleaned:
            cleaned.append(character_id)
    return cleaned


def taggable_characters(characters: list[Character], roster: list[Character]) -> list[Character]:
    own_membership_ids = {character.membership_id for character in roster}
    return [
        character for character in characters if character.membership_id not in own_membership_ids
    ]


def _thread_index(threads: list[Thread], thread_id: int) -> int | None:
    for index, thread in enumerate(threads):
        if thread.id == thread_id:
            return index
    return None
