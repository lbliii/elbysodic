"""Start a realm-local character application."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class NewApplicationForm:
    name: str = ""
    summary: str = ""
    body: str = ""
    facet_slugs: str = ""


def get(request: Request) -> Page:
    return _render_new_application(request)


@contract(form=FormContract(NewApplicationForm, "applications/new/page.html"))
async def post(request: Request) -> Page | Redirect:
    form = await request.form()
    services = get_services(request)
    name = str(form.get("name") or "")
    summary = str(form.get("summary") or "")
    body = str(form.get("body") or "")
    facet_slugs = _facet_slugs(form)
    try:
        character = services.create_character(
            name=name,
            summary=summary,
            application_body=body,
            facet_slugs=facet_slugs,
            make_default=services.viewer().current_character is None,
        )
    except ValueError as exc:
        return _render_new_application(
            request,
            error=str(exc),
            name=name,
            summary=summary,
            body=body,
            selected_facet_slugs=facet_slugs,
        )
    return Redirect(f"/applications/{character.slug}")


def _render_new_application(
    request: Request,
    *,
    error: str | None = None,
    name: str = "",
    summary: str = "",
    body: str = "",
    selected_facet_slugs: list[str] | None = None,
) -> Page:
    services = get_services(request)
    return Page(
        "applications/new/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=services.viewer(),
        onboarding=services.application_onboarding(),
        error=error,
        name=name,
        summary=summary,
        body=body,
        selected_facet_slugs=selected_facet_slugs or [],
    )


def _facet_slugs(form: object) -> list[str]:
    values: list[object]
    get_list = getattr(form, "get_list", None)
    getlist = getattr(form, "getlist", None)
    if callable(get_list):
        values = list(get_list("facet_slugs"))
    elif callable(getlist):
        values = list(getlist("facet_slugs"))
    else:
        raw = getattr(form, "get", lambda _name: None)("facet_slugs")
        values = [] if raw is None else [raw]
    slugs: list[str] = []
    for value in values:
        slug = str(value or "").strip()
        if slug and slug not in slugs:
            slugs.append(slug)
    return slugs
