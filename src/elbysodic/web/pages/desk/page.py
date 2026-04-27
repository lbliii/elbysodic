"""Writer Desk hub."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class DeskLink:
    href: str
    label: str
    summary: str
    count: int | None = None


def get(request: Request) -> Page:
    services = get_services()
    viewer = services.viewer()
    links = [
        DeskLink("/my/threads", "My threads", "Scenes you are writing, owe, or watching."),
        DeskLink(
            "/notifications",
            "Notifications",
            "Replies, mentions, casting interest, and other pings.",
            viewer.unread_notification_count,
        ),
        DeskLink("/characters", "Characters", "Your roster, active face, profiles, and trackers."),
        DeskLink(
            "/applications", "Applications", "Draft, submit, and review character applications."
        ),
        DeskLink("/plotting", "Plotting", "Raised hands, rooms, and pre-scene planning."),
        DeskLink("/casting", "Casting", "Reserves, claims, wanted interest, and open hooks."),
        DeskLink(
            "/discover", "Discover", "Find scenes, writers, and characters through world facets."
        ),
    ]
    return Page(
        "desk/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        desk_links=links,
    )
