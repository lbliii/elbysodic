"""Realm claims directory.

Mutations live in ``_actions.py`` (Chirp page actions, dispatched on the
hidden ``_action`` form field). ``post()`` below is only the no-``_action``
fallback that keeps the POST method registered on this path.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus

from chirp.contracts import FormContract, contract
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services

CLAIMS_TEMPLATE = "claims/page.html"


@dataclass(frozen=True, slots=True)
class ClaimsActionForm:
    _action: str
    claim_id: str = ""
    claim_type_id: str = ""
    label: str = ""
    status: str = ""
    character_id: str = ""
    notes: str = ""
    q: str = ""


def get(request: Request) -> Page:
    return render_claims(
        request,
        status_filter=_status_filter(request),
        search_query=_search_query(request),
    )


@contract(form=FormContract(ClaimsActionForm, CLAIMS_TEMPLATE))
async def post(request: Request) -> Page:
    """Fallback — mutations dispatch via ``pages/claims/_actions.py``."""
    return render_claims(request)


def render_claims(
    request: Request,
    *,
    error: str | None = None,
    status_filter: str | None = None,
    search_query: str = "",
) -> Page:
    services = get_services(request)
    viewer = services.viewer()
    claims_page = services.claims_page(
        status_filter=status_filter,
        search_query=search_query,
    )
    return Page.mounted(
        CLAIMS_TEMPLATE,
        current_path=request.url,
        viewer=viewer,
        directory=claims_page.directory,
        can_manage=claims_page.directory.can_manage,
        characters=claims_page.characters,
        error=error,
        search_query_encoded=quote_plus(claims_page.directory.search_query),
    )


def _status_filter(request: Request) -> str | None:
    raw = str(request.query.get("status") or "").strip()
    if raw == "open":
        raw = "available"
    if raw in {"claimed", "reserved", "available"}:
        return raw
    return None


def _search_query(request: Request) -> str:
    return str(request.query.get("q") or "").strip()
