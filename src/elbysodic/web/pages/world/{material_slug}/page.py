"""World material detail page."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request, material_slug: str) -> Page:
    services = get_services()
    try:
        material = services.read_material(material_slug)
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    return Page(
        "world/{material_slug}/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=services.viewer(),
        material=material,
        guidebook=services.world_hub(),
    )
