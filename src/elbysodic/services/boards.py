"""Board and board-thread read model assembly."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from elbysodic.domain.boards import is_community_board, is_location_board
from elbysodic.domain.models import Board, Thread
from elbysodic.services import policies
from elbysodic.services.facets import current_character_facet_ids, facet_tags
from elbysodic.services.materials import MaterialReadRepository, current_event_for_facet_ids
from elbysodic.services.posts import PostViewContextBuilder
from elbysodic.services.posts import post_view as _post_view
from elbysodic.services.read_models import BoardPage, BoardSummary, BoardThreadFilter, ForumView
from elbysodic.services.threads import (
    ThreadReadRepository,
    board_thread_summaries,
    next_unread_thread,
)
from elbysodic.services.timestamps import timestamp_key


class BoardReadRepository(ThreadReadRepository, MaterialReadRepository, Protocol):
    def get_board_by_slug(self, community_id: int, slug: str) -> Board: ...

    def list_child_boards(self, community_id: int, parent_board_id: int | None) -> list[Board]: ...

    def list_child_boards_for_boards(
        self,
        community_id: int,
        parent_board_ids: list[int],
    ) -> dict[int, list[Board]]: ...

    def count_threads(self, community_id: int, board_id: int) -> int: ...


def visible_board_summaries(
    repo: BoardReadRepository,
    viewer: ForumView,
) -> list[BoardSummary]:
    current_facet_ids = current_character_facet_ids(repo, viewer)
    visible_boards = [
        board
        for board in repo.list_boards(viewer.community.id)
        if policies.can_view_board(viewer.membership, board, viewer.role)
    ]
    return board_summaries(repo, viewer, visible_boards, current_facet_ids)


def child_board_summaries(
    repo: BoardReadRepository,
    viewer: ForumView,
    board: Board,
) -> list[BoardSummary]:
    current_facet_ids = current_character_facet_ids(repo, viewer)
    children = [
        child
        for child in repo.list_child_boards(viewer.community.id, board.id)
        if policies.can_view_board(viewer.membership, child, viewer.role)
    ]
    return board_summaries(repo, viewer, children, current_facet_ids)


def sibling_board_summaries(
    repo: BoardReadRepository,
    viewer: ForumView,
    board: Board,
) -> list[BoardSummary]:
    current_facet_ids = current_character_facet_ids(repo, viewer)
    siblings = repo.list_child_boards(viewer.community.id, board.parent_board_id)
    visible_siblings = [
        sibling
        for sibling in siblings
        if sibling.id != board.id
        and is_location_board(sibling)
        and policies.can_view_board(viewer.membership, sibling, viewer.role)
    ]
    return board_summaries(repo, viewer, visible_siblings, current_facet_ids)


def board_summary(
    repo: BoardReadRepository,
    viewer: ForumView,
    board: Board,
) -> BoardSummary:
    return board_summaries(
        repo,
        viewer,
        [board],
        current_character_facet_ids(repo, viewer),
    )[0]


def board_page(
    repo: BoardReadRepository,
    viewer: ForumView,
    board_slug: str,
    *,
    filter_by: BoardThreadFilter = "all",
) -> BoardPage:
    current_facet_ids = current_character_facet_ids(repo, viewer)
    board = repo.get_board_by_slug(viewer.community.id, board_slug)
    if not policies.can_view_board(viewer.membership, board, viewer.role):
        raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
    threads = board_thread_summaries(
        repo,
        viewer,
        board,
        filter_by=filter_by,
    )
    summary = board_summaries(repo, viewer, [board], current_facet_ids)[0]
    parent = (
        repo.get_board(viewer.community.id, board.parent_board_id)
        if board.parent_board_id is not None
        else None
    )
    if parent is not None and not policies.can_view_board(
        viewer.membership,
        parent,
        viewer.role,
    ):
        parent = None
    is_location = is_location_board(board)
    is_community = is_community_board(board)
    subboards = child_board_summaries(repo, viewer, board) if is_location else []
    sibling_boards = sibling_board_summaries(repo, viewer, board) if is_location else []
    facet_ids = {tag.facet.id for tag in summary.facets}
    current_event = (
        current_event_for_facet_ids(repo, viewer.community.id, facet_ids) if is_location else None
    )
    direct_thread_count = (
        len(threads) if filter_by == "all" else repo.count_threads(viewer.community.id, board.id)
    )
    return BoardPage(
        board=board,
        summary=summary,
        parent_board=parent,
        is_location_board=is_location,
        is_community_board=is_community,
        board_facets=summary.facets,
        subboards=subboards,
        sibling_boards=sibling_boards,
        current_event=current_event,
        threads=threads,
        direct_thread_count=direct_thread_count,
        next_unread_thread=next_unread_thread(repo, viewer, board),
        can_start_thread=policies.can_start_thread(viewer.membership, board, viewer.role),
    )


def board_summaries(
    repo: BoardReadRepository,
    viewer: ForumView,
    boards: list[Board],
    current_facet_ids: set[int],
) -> list[BoardSummary]:
    if not boards:
        return []
    board_ids = [board.id for board in boards]
    children_by_board = repo.list_child_boards_for_boards(viewer.community.id, board_ids)
    visible_children_by_board = {
        board_id: [
            child
            for child in children
            if policies.can_view_board(viewer.membership, child, viewer.role)
        ]
        for board_id, children in children_by_board.items()
    }
    activity_boards_by_summary = {
        board.id: [board, *visible_children_by_board.get(board.id, [])] for board in boards
    }
    activity_board_ids = list(
        {
            activity_board.id
            for activity_boards in activity_boards_by_summary.values()
            for activity_board in activity_boards
        }
    )
    facets_by_board = repo.list_board_facets_for_boards(viewer.community.id, board_ids)
    threads_by_board = repo.list_threads_for_boards(viewer.community.id, activity_board_ids)
    all_thread_ids = [thread.id for threads in threads_by_board.values() for thread in threads]
    posts_by_thread = repo.list_posts_for_threads(viewer.community.id, all_thread_ids)
    thread_read_at = repo.thread_read_at_for_threads(
        viewer.community.id,
        all_thread_ids,
        viewer.membership.id,
    )
    all_posts = [post for posts in posts_by_thread.values() for post in posts]
    post_context = (
        PostViewContextBuilder(repo, viewer.community.id).context(all_posts) if all_posts else None
    )
    summaries: list[BoardSummary] = []
    for board in boards:
        threads_with_boards = [
            (activity_board, thread)
            for activity_board in activity_boards_by_summary[board.id]
            for thread in threads_by_board.get(activity_board.id, [])
        ]
        latest_board: Board | None = None
        latest_thread: Thread | None = None
        if threads_with_boards:
            latest_board, latest_thread = max(
                threads_with_boards,
                key=lambda item: (timestamp_key(item[1].updated_at), item[1].id),
            )
        latest_thread_posts = posts_by_thread.get(latest_thread.id, []) if latest_thread else []
        latest_post = (
            _post_view(
                repo,
                viewer.community.id,
                latest_thread_posts[-1],
                context=post_context,
            )
            if latest_thread_posts
            else None
        )
        threads = [thread for _, thread in threads_with_boards]
        board_facets = facet_tags(
            repo,
            viewer.community.id,
            facets_by_board.get(board.id, []),
        )
        summaries.append(
            BoardSummary(
                board=board,
                child_boards=visible_children_by_board.get(board.id, []),
                thread_count=len(threads),
                post_count=sum(len(posts_by_thread.get(thread.id, [])) for thread in threads),
                unread_thread_count=sum(
                    1 for thread in threads if _is_unread_from_map(thread, thread_read_at)
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
        )
    return summaries


def board_summary_factory(
    repo: BoardReadRepository,
    viewer: ForumView,
    current_facet_ids: set[int],
) -> Callable[[Board], BoardSummary]:
    summaries_by_id: dict[int, BoardSummary] | None = None

    def factory(board: Board) -> BoardSummary:
        nonlocal summaries_by_id
        if summaries_by_id is None:
            visible_boards = [
                candidate
                for candidate in repo.list_boards(viewer.community.id)
                if policies.can_view_board(viewer.membership, candidate, viewer.role)
            ]
            summaries_by_id = {
                summary.board.id: summary
                for summary in board_summaries(repo, viewer, visible_boards, current_facet_ids)
            }
        return summaries_by_id[board.id]

    return factory


def _is_unread_from_map(thread: Thread, read_at_by_thread: dict[int, str]) -> bool:
    read_at = read_at_by_thread.get(thread.id)
    if read_at is None:
        return True
    return timestamp_key(read_at) < timestamp_key(thread.updated_at)
