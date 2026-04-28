"""Writer Desk hub."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services.read_models import MyThreadsDashboard
from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class DeskLink:
    href: str
    label: str
    summary: str
    lane: str
    count: int | None = None


@dataclass(frozen=True, slots=True)
class DeskOverview:
    queue: MyThreadsDashboard
    unread_notifications: int

    @property
    def needs_reply_count(self) -> int:
        return len(self.queue.needs_reply)

    @property
    def waiting_count(self) -> int:
        return len(self.queue.waiting_on_others)

    @property
    def active_count(self) -> int:
        return len(self.queue.participated)

    @property
    def started_count(self) -> int:
        return len(self.queue.started_by_me)

    @property
    def next_queue_href(self) -> str:
        if self.queue.needs_reply:
            item = self.queue.needs_reply[0]
            anchor = f"#{item.jump_post.anchor}" if item.jump_post else ""
            return f"/boards/{item.board.slug}/threads/{item.thread.slug}{anchor}"
        if self.queue.waiting_on_others:
            item = self.queue.waiting_on_others[0]
            return f"/boards/{item.board.slug}/threads/{item.thread.slug}"
        return "/my/threads"

    @property
    def next_queue_label(self) -> str:
        if self.queue.needs_reply:
            return "Open next reply"
        if self.queue.waiting_on_others:
            return "Check waiting scene"
        return "Open queue"


def get(request: Request) -> Page:
    services = get_services()
    viewer = services.viewer()
    queue = services.my_threads()
    overview = DeskOverview(
        queue=queue,
        unread_notifications=viewer.unread_notification_count,
    )
    links = [
        DeskLink(
            "/my/threads",
            "Queue",
            "Scenes you owe, scenes waiting on others, and the whole roster tracker.",
            "Writing lane",
            overview.needs_reply_count,
        ),
        DeskLink(
            "/notifications",
            "Inbox",
            "Replies, mentions, casting interest, and other pings.",
            "Attention",
            viewer.unread_notification_count,
        ),
        DeskLink(
            "/characters",
            "Roster",
            "Faces, profiles, trackers, and post presentation.",
            "Identity",
            len(viewer.roster),
        ),
        DeskLink(
            "/plotting",
            "Plotting",
            "Raised hands, rooms, and pre-scene planning.",
            "Collaboration",
        ),
        DeskLink(
            "/applications",
            "Applications",
            "Draft, submit, and track character applications.",
            "Intake",
        ),
        DeskLink(
            "/discover",
            "Discovery",
            "Find scenes, writers, and characters through world facets.",
            "Find play",
        ),
        DeskLink(
            "/casting",
            "Casting",
            "Reserves, wanted interest, and open hooks.",
            "Wanted",
        ),
    ]
    return Page(
        "desk/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        desk=overview,
        desk_links=links,
    )
