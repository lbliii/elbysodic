"""Director Studio hub."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request) -> Page:
    return _render_studio(request)


async def post(request: Request) -> Page | Redirect:
    services = get_services()
    form = await request.form()
    raw_group_id = str(form.get("identity_accent_facet_group_id") or "")
    try:
        facet_group_id = int(raw_group_id) if raw_group_id else None
        services.update_identity_accent_group(facet_group_id)
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except (LookupError, ValueError) as exc:
        return _render_studio(request, error=str(exc))
    return Redirect("/studio")


def _render_studio(request: Request, *, error: str | None = None) -> Page:
    services = get_services()
    studio = services.director_studio()
    return Page(
        "studio/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=services.viewer(),
        studio=studio,
        error=error,
    )
