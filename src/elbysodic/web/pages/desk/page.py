"""Writer Desk hub."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services.read_models import (
    ApplicationCharacterView,
    ApplicationsDesk,
    CharacterThreadActivity,
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
    actionable_roster_activity: list[CharacterThreadActivity]
    has_attention_counts: bool

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
    services = get_services(request)
    viewer = services.viewer()
    queue = services.my_threads()
    plotting = services.plotting_desk()
    applications = services.applications_desk()
    notifications = services.notifications(limit=5)
    unread_watched = _unread_watched_threads(queue)
    open_applications = _open_application_items(applications)
    actions = _build_actions(
        queue=queue,
        unread_watched=unread_watched,
        plotting=plotting,
        open_applications=open_applications,
        unread_notifications=viewer.unread_notification_count,
    )
    lanes = _build_lanes(
        queue=queue,
        unread_watched=unread_watched,
        plotting=plotting,
        open_applications=open_applications,
        notifications=notifications,
    )
    overview = DeskOverview(
        queue=queue,
        unread_notifications=viewer.unread_notification_count,
        unread_watched_count=len(unread_watched),
        plotting_room_count=len(plotting.rooms),
        application_count=len(open_applications),
        lanes=lanes,
        actions=actions,
        actionable_roster_activity=_actionable_roster_activity(queue),
        has_attention_counts=any(
            (
                len(queue.needs_reply),
                len(unread_watched),
                len(queue.waiting_on_others),
                viewer.unread_notification_count,
            )
        ),
    )
    return Page.mounted(
        "desk/page.html",
        current_path=request.url,
        viewer=viewer,
        desk=overview,
    )


def _build_actions(
    *,
    queue: MyThreadsDashboard,
    unread_watched: list[ThreadObligationItem],
    plotting: PlottingDesk,
    open_applications: list[ApplicationCharacterView],
    unread_notifications: int,
) -> list[DeskAction]:
    actions: list[DeskAction] = []
    if queue.needs_reply:
        actions.append(
            DeskAction(
                _next_queue_href(queue),
                "Reply where owed",
                "Jump straight into the next scene that needs your words.",
                len(queue.needs_reply),
            )
        )
    if unread_watched:
        actions.append(
            DeskAction(
                _thread_href(unread_watched[0]),
                "Read latest",
                "Catch up on watched scenes with fresh posts.",
                len(unread_watched),
            )
        )
    if plotting.rooms:
        actions.append(
            DeskAction(
                "/plotting",
                "Open plotting",
                "Continue planning rooms that are becoming scenes.",
                len(plotting.rooms),
            )
        )
    if open_applications:
        actions.append(
            DeskAction(
                "/applications",
                "Check applications",
                "Review drafts, submissions, or requested revisions.",
                len(open_applications),
            )
        )
    if unread_notifications:
        actions.append(
            DeskAction(
                "/notifications",
                "Open inbox",
                "Mentions, replies, and collaboration pings.",
                unread_notifications,
            )
        )
    return actions


def _build_lanes(
    *,
    queue: MyThreadsDashboard,
    unread_watched: list[ThreadObligationItem],
    plotting: PlottingDesk,
    open_applications: list[ApplicationCharacterView],
    notifications: NotificationInbox,
) -> list[DeskLane]:
    lanes: list[DeskLane] = []
    if queue.needs_reply:
        lanes.append(
            DeskLane(
                "attention",
                "Needs reply",
                "Scenes where another writer has the last beat.",
                "/my/threads",
                "Open queue",
                len(queue.needs_reply),
                _thread_preview_items(queue.needs_reply[:3], "Needs reply"),
                "",
            )
        )
    if unread_watched:
        lanes.append(
            DeskLane(
                "scenes",
                "Unread watched",
                "Threads you are watching with fresh posts to read.",
                "/my/threads",
                "Read scenes",
                len(unread_watched),
                _thread_preview_items(unread_watched[:3], "Unread"),
                "",
            )
        )
    if queue.waiting_on_others:
        lanes.append(
            DeskLane(
                "waiting",
                "Waiting on others",
                "Scenes where your roster currently has the last word.",
                "/my/threads",
                "Review waiting",
                len(queue.waiting_on_others),
                _thread_preview_items(queue.waiting_on_others[:3], "Waiting"),
                "",
            )
        )
    if plotting.rooms:
        lanes.append(
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
                "",
            )
        )
    if open_applications:
        lanes.append(
            DeskLane(
                "casting",
                "Applications",
                "Drafts, submissions, and requested revisions.",
                "/applications",
                "Open applications",
                len(open_applications),
                [
                    DeskPreviewItem(
                        f"/applications/{item.character.slug}",
                        item.character.name,
                        item.status_label,
                        item.character.tagline or "Character application",
                        item.status_label,
                    )
                    for item in open_applications[:3]
                ],
                "",
            )
        )
    unread_items = [item for item in notifications.items if item.is_unread]
    if unread_items:
        lanes.append(
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
                        "new",
                    )
                    for item in unread_items[:3]
                ],
                "",
            )
        )
    return lanes


def _open_application_items(applications: ApplicationsDesk) -> list[ApplicationCharacterView]:
    return [
        item
        for item in applications.my_applications
        if item.character.application_status in {"draft", "submitted", "revision_requested"}
    ]


def _actionable_roster_activity(queue: MyThreadsDashboard) -> list[CharacterThreadActivity]:
    return [
        activity
        for activity in queue.roster_activity
        if activity.needs_reply or activity.waiting_on_others
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
