"""Invite-only access posture page."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services
from elbysodic.web.tenant import request_tenant_slug


@dataclass(frozen=True, slots=True)
class RequestAccessForm:
    intent: str = ""
    access_request_id: str = ""
    community_slug: str = ""
    email: str = ""
    display_name: str = ""
    face_concept: str = ""
    wanted_hook: str = ""
    notes: str = ""


def get(request: Request) -> Page:
    return _render_request_access(request)


def _access_request_community_slug(request: Request, form: RequestAccessForm) -> str:
    tenant_slug = request_tenant_slug(request)
    if tenant_slug is not None:
        return tenant_slug
    return form.community_slug.strip()


@contract(form=FormContract(RequestAccessForm, "request-access/page.html"))
async def post(request: Request, form: RequestAccessForm) -> Page:
    services = get_services()
    account_visitor = services.account_visitor(request)
    community_slug = _access_request_community_slug(request, form)
    if not community_slug:
        return _render_request_access(request, error="Choose a realm before requesting access.")
    if form.intent == "withdraw_access_request":
        if account_visitor is None:
            return _render_request_access(
                request,
                error="That access request is not available.",
            )
        try:
            request_id = int(form.access_request_id)
            services.withdraw_access_request_for_account(
                community_slug,
                request_id,
                account_visitor.user.id,
            )
        except LookupError, PermissionError, ValueError:
            return _render_request_access(
                request,
                error="That access request is not available.",
            )
        return _render_request_access(request, withdrawn=True)
    try:
        receipt = services.create_access_request_receipt(
            community_slug,
            email=account_visitor.user.email if account_visitor else form.email,
            display_name=form.display_name,
            face_concept=form.face_concept,
            wanted_hook=form.wanted_hook,
            notes=form.notes,
            account_user_id=account_visitor.user.id if account_visitor else None,
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except ValueError as exc:
        return _render_request_access(request, error=str(exc), form=form)
    return _render_request_access(
        request,
        form=RequestAccessForm(),
        submitted_email=receipt.submitted_email,
        submitted_account=receipt.submitted_account,
        withdraw_request_id=receipt.withdraw_request_id,
        withdraw_community_slug=(receipt.community_slug if receipt.submitted_account else ""),
    )


def _render_request_access(
    request: Request,
    *,
    error: str = "",
    form: RequestAccessForm | None = None,
    submitted_email: str = "",
    submitted_account: bool = False,
    withdraw_request_id: int | None = None,
    withdraw_community_slug: str = "",
    withdrawn: bool = False,
) -> Page:
    services = get_services()
    tenant_slug = request_tenant_slug(request)
    community = None
    if tenant_slug is not None:
        community = services.public_studio_program(tenant_slug).community
    account_visitor = services.account_visitor(request, current_community=community)
    form = form or RequestAccessForm(
        community_slug=community.slug if community else "",
        email=account_visitor.user.email if account_visitor else "",
    )
    return Page.mounted(
        "request-access/page.html",
        current_path=request.url,
        page_title=f"Request access · {community.name if community else 'Elbysodic'}",
        viewer=None,
        account_visitor=account_visitor,
        community=community,
        form=form,
        error=error,
        submitted_email=submitted_email,
        submitted_account=submitted_account,
        withdraw_request_id=withdraw_request_id,
        withdraw_community_slug=withdraw_community_slug,
        withdrawn=withdrawn,
        show_community_shell=False,
    )
