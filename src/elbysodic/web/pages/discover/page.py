"""Facet-powered plot discovery."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services import AppServices


def get(request: Request, services: AppServices) -> Page:
    viewer = services.viewer()
    raw_facets = str(request.query.get("facets") or "")
    discovery = services.discover_plots(facet_slugs=[raw_facets])
    return Page.mounted(
        "discover/page.html",
        current_path=request.url,
        viewer=viewer,
        discovery=discovery,
    )
