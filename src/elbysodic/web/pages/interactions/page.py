"""Realm quizzes, polls, and surveys."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services import AppServices


def get(request: Request, services: AppServices) -> Page:
    return Page.mounted(
        "interactions/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        hub=services.realm_interactions(),
    )
