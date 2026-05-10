"""Invite-only access posture page."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page


def get(request: Request) -> Page:
    return Page(
        "request-access/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        page_title="Request Access · Elbysodic",
        viewer=None,
        show_community_shell=False,
    )
