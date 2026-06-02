"""Realm claims directory."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.db.repositories.base import TenantBoundaryError
from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class ClaimsActionForm:
    intent: str = ""
    claim_id: str = ""
    claim_type_id: str = ""
    label: str = ""
    status: str = ""
    character_id: str = ""
    notes: str = ""
    q: str = ""


def get(request: Request) -> Page:
    return _render_claims(
        request,
        status_filter=_status_filter(request),
        search_query=_search_query(request),
    )


@contract(form=FormContract(ClaimsActionForm, "claims/page.html"))
async def post(request: Request) -> Page | Redirect:
    services = get_services(request)
    form = await request.form()
    intent = str(form.get("intent") or "")
    try:
        if intent == "create_claim":
            raw_character_id = str(form.get("character_id") or "")
            services.create_director_claim(
                _required_int(form.get("claim_type_id"), "choose a claim type"),
                label=str(form.get("label") or ""),
                status=str(form.get("status") or "claimed"),
                character_id=int(raw_character_id) if raw_character_id else None,
                notes=str(form.get("notes") or ""),
            )
        elif intent == "update_claim":
            raw_character_id = str(form.get("character_id") or "")
            services.update_director_claim(
                _required_int(form.get("claim_id"), "choose a claim to update"),
                label=str(form.get("label") or ""),
                status=str(form.get("status") or "claimed"),
                character_id=int(raw_character_id) if raw_character_id else None,
                notes=str(form.get("notes") or ""),
            )
        else:
            raise HTTPError(status=400, detail=f"unknown claims action: {intent}")
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except (LookupError, ValueError, TenantBoundaryError) as exc:
        return _render_claims(request, error=str(exc))
    return Redirect("/claims")


def _render_claims(
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
        "claims/page.html",
        current_path=request.url,
        viewer=viewer,
        directory=claims_page.directory,
        can_manage=claims_page.directory.can_manage,
        characters=claims_page.characters,
        error=error,
        search_query_encoded=quote_plus(claims_page.directory.search_query),
    )


def _required_int(raw: object, message: str) -> int:
    value = str(raw or "")
    if not value:
        raise ValueError(message)
    return int(value)


def _status_filter(request: Request) -> str | None:
    raw = str(request.query.get("status") or "").strip()
    if raw == "open":
        raw = "available"
    if raw in {"claimed", "reserved", "available"}:
        return raw
    return None


def _search_query(request: Request) -> str:
    return str(request.query.get("q") or "").strip()
