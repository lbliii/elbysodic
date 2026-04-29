"""Writer Desk hub."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services.read_models import (
    ApplicationsDesk,
    MyThreadsDashboard,
    NotificationInbox,
    PlottingDesk,
    ThreadObligationItem,
)
from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class DeskAction:
    href: str
    label: str
    summary: str
    count: int | None = None


@dataclass(frozen=True, slots=True)
class DeskPreviewItem:
    href: str
    title: str
    meta: str
    summary: str
    badge: str | None = None


@dataclass(frozen=True, slots=True)
class DeskLane:
    anchor: str
    title: str
    summary: str
    href: str
    action_label: str
    count: int
    items: list[DeskPreviewItem]
    empty_text: str


@dataclass(frozen=True, slots=True)
class DeskOverview:
    queue: MyThreadsDashboard
    unread_notifications: int
    unread_watched_count: int
    plotting_room_count: int
    application_count: int
    lanes: list[DeskLane]
    actions: list[DeskAction]

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

    @property
    def current_focus_label(self) -> str:
        if self.queue.needs_reply:
            item = self.queue.needs_reply[0]
            return f"{item.thread.title} needs a reply"
        if self.queue.participated:
            item = self.queue.participated[0]
            return f"{item.thread.title} is active"
        return "Your roster is caught up"


def get(request: Request) -> Page:
    services = get_services()
    viewer = services.viewer()
    queue = services.my_threads()
    plotting = services.plotting_desk()
    applications = services.applications_desk()
    notifications = services.notifications(limit=5)
    unread_watched = _unread_watched_threads(queue)
    actions = _build_actions(
        queue=queue,
        unread_watched=unread_watched,
        plotting=plotting,
        applications=applications,
        unread_notifications=viewer.unread_notification_count,
    )
    lanes = _build_lanes(
        queue=queue,
        unread_watched=unread_watched,
        plotting=plotting,
        applications=applications,
        notifications=notifications,
    )
    overview = DeskOverview(
        queue=queue,
        unread_notifications=viewer.unread_notification_count,
        unread_watched_count=len(unread_watched),
        plotting_room_count=len(plotting.rooms),
        application_count=len(applications.my_applications),
        lanes=lanes,
        actions=actions,
    )
    return Page(
        "desk/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        desk=overview,
    )


def _build_actions(
    *,
    queue: MyThreadsDashboard,
    unread_watched: list[ThreadObligationItem],
    plotting: PlottingDesk,
    applications: ApplicationsDesk,
    unread_notifications: int,
) -> list[DeskAction]:
    read_href = _thread_href(unread_watched[0]) if unread_watched else "/my/threads"
    return [
        DeskAction(
            _next_queue_href(queue),
            "Reply where owed",
            "Jump straight into the scene most likely to need your words.",
            len(queue.needs_reply),
        ),
        DeskAction(
            read_href,
            "Read latest",
            "Catch up on watched scenes before deciding what to write.",
            len(unread_watched),
        ),
        DeskAction(
            "/plotting",
            "Open plotting",
            "Continue planning rooms and turn interest into play.",
            len(plotting.rooms),
        ),
        DeskAction(
            "/applications",
            "Check applications",
            "Track drafts, reviews, and accepted faces.",
            len(applications.my_applications),
        ),
        DeskAction(
            "/notifications",
            "Open inbox",
            "Mentions, replies, and collaboration pings.",
            unread_notifications,
        ),
    ]


def _build_lanes(
    *,
    queue: MyThreadsDashboard,
    unread_watched: list[ThreadObligationItem],
    plotting: PlottingDesk,
    applications: ApplicationsDesk,
    notifications: NotificationInbox,
) -> list[DeskLane]:
    application_items = applications.my_applications[:3]
    return [
        DeskLane(
            "attention",
            "Needs reply",
            "Scenes where another writer has the last beat.",
            "/my/threads",
            "Open queue",
            len(queue.needs_reply),
            _thread_preview_items(queue.needs_reply[:3], "Needs reply"),
            "Your roster is caught up for now.",
        ),
        DeskLane(
            "scenes",
            "Unread watched",
            "Threads you are watching with fresh posts to read.",
            "/my/threads",
            "Read scenes",
            len(unread_watched),
            _thread_preview_items(unread_watched[:3], "Unread"),
            "No watched scenes have fresh posts.",
        ),
        DeskLane(
            "waiting",
            "Waiting on others",
            "Scenes where your roster currently has the last word.",
            "/my/threads",
            "Review waiting",
            len(queue.waiting_on_others),
            _thread_preview_items(queue.waiting_on_others[:3], "Waiting"),
            "No active scenes are waiting on other writers for you.",
        ),
        DeskLane(
            "plotting",
            "Plotting rooms",
            "Shared rooms where interest is becoming a scene.",
            "/plotting",
            "Open plotting",
            len(plotting.rooms),
            [
                DeskPreviewItem(
                    f"/plotting/{item.room.id}",
                    item.room.title,
                    item.source_label,
                    item.room.summary or f"{len(item.participants)} participant(s)",
                    item.room.status,
                )
                for item in plotting.rooms[:3]
            ],
            "No plotting rooms are open yet.",
        ),
        DeskLane(
            "casting",
            "Applications",
            "Drafts, submissions, and accepted faces tied to this writer.",
            "/applications",
            "Open applications",
            len(applications.my_applications),
            [
                DeskPreviewItem(
                    f"/characters/{item.character.slug}",
                    item.character.name,
                    item.status_label,
                    item.character.tagline or "Character application",
                    item.status_label,
                )
                for item in application_items
            ],
            "No character drafts are in motion.",
        ),
        DeskLane(
            "notifications",
            "Notifications",
            "Mentions, replies, plotting interest, and writer pings.",
            "/notifications",
            "Open inbox",
            notifications.unread_count,
            [
                DeskPreviewItem(
                    item.href,
                    item.title,
                    item.created_at_label,
                    item.snippet,
                    "new" if item.is_unread else item.label,
                )
                for item in notifications.items[:3]
            ],
            "No notifications are waiting on you.",
        ),
    ]


def _thread_preview_items(
    items: list[ThreadObligationItem], fallback_badge: str
) -> list[DeskPreviewItem]:
    previews: list[DeskPreviewItem] = []
    for item in items:
        latest = item.latest_post
        actor = latest.author.name if latest else item.author.name
        meta = f"{item.board.name} · latest by {actor}"
        summary = latest.snippet if latest else item.thread.summary
        badge = item.badges[0].label if item.badges else fallback_badge
        previews.append(
            DeskPreviewItem(
                _thread_href(item),
                item.thread.title,
                meta,
                summary,
                badge,
            )
        )
    return previews


def _unread_watched_threads(queue: MyThreadsDashboard) -> list[ThreadObligationItem]:
    return [item for item in queue.participated if item.is_unread and not item.needs_reply]


def _next_queue_href(queue: MyThreadsDashboard) -> str:
    if queue.needs_reply:
        return _thread_href(queue.needs_reply[0])
    if queue.waiting_on_others:
        return _thread_href(queue.waiting_on_others[0], include_jump=False)
    return "/my/threads"


def _thread_href(item: ThreadObligationItem, *, include_jump: bool = True) -> str:
    anchor = f"#{item.jump_post.anchor}" if include_jump and item.jump_post else ""
    return f"/boards/{item.board.slug}/threads/{item.thread.slug}{anchor}"
