"""Wanted hook detail page.

Mutations live in ``_actions.py`` (Chirp page actions, dispatched on the
hidden ``_action`` form field). ``post()`` below is only the no-``_action``
fallback that keeps the POST method registered on this path.
"""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.recovery import recover_missing_route
from elbysodic.web.state import get_services
from elbysodic.web.tenant import request_tenant_slug

WANTED_TEMPLATE = "wanted/{wanted_slug}/page.html"


@dataclass(frozen=True, slots=True)
class WantedActionForm:
    _action: str
    prospective_character_name: str = ""
    note: str = ""
    status: str = ""
    interest_id: str = ""


def get(request: Request, wanted_slug: str) -> Page:
    return _render_wanted(request, wanted_slug)


@contract(form=FormContract(WantedActionForm, WANTED_TEMPLATE))
async def post(request: Request, wanted_slug: str) -> Page:
    """Fallback — mutations dispatch via ``pages/wanted/{wanted_slug}/_actions.py``."""
    return _render_wanted(request, wanted_slug)


def _render_wanted(request: Request, wanted_slug: str) -> Page:
    tenant_slug = request_tenant_slug(request)
    try:
        services = get_services(request)
        viewer = services.viewer()
    except LookupError, PermissionError:
        if tenant_slug is None:
            raise
        services = get_services()
        try:
            wanted = services.public_read_wanted_ad(tenant_slug, wanted_slug)
            community = services.public_studio_program(tenant_slug).community
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        viewer = None
    else:
        try:
            wanted = services.read_wanted_ad(wanted_slug)
        except LookupError:
            return recover_missing_route(request, kind="wanted", slug=wanted_slug)
        community = viewer.community
    return Page.mounted(
        WANTED_TEMPLATE,
        current_path=request.url,
        viewer=viewer,
        account_visitor=(
            None
            if viewer is not None
            else services.account_visitor(request, current_community=community)
        ),
        community=community,
        request_access_href=(
            f"/c/{tenant_slug}/request-access" if tenant_slug is not None else "/request-access"
        ),
        wanted=wanted,
        show_community_shell=viewer is not None,
    )
