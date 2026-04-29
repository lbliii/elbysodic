"""Start a realm-local character application."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.services.read_models import ApplicationTemplateFieldView
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
    onboarding = services.application_onboarding()
    field_values: dict[int, str] = {}
    facet_slugs = _facet_slugs(form)
    if not name.strip():
        return _render_new_application(
            request,
            error="character name is required",
            name=name,
            summary=summary,
            body=body,
            field_values=field_values,
            selected_facet_slugs=facet_slugs,
        )
    try:
        field_values = _template_field_values(form, onboarding.template_fields)
        application_body = _application_body_with_template_fields(
            body,
            field_values,
            onboarding.template_fields,
        )
        character = services.create_character(
            name=name,
            summary=summary,
            application_body=application_body,
            application_field_values=field_values,
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
            field_values=field_values,
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
    field_values: dict[int, str] | None = None,
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
        field_values=field_values or {},
        selected_facet_slugs=selected_facet_slugs or [],
    )


def _template_field_values(
    form: object,
    fields: list[ApplicationTemplateFieldView],
) -> dict[int, str]:
    values: dict[int, str] = {}
    for field_view in fields:
        field = field_view.field
        value = str(getattr(form, "get", lambda _name: "")(f"application_field_{field.id}") or "")
        value = value.strip()
        if field.is_required and not value:
            raise ValueError(f"{field.label} is required")
        if value:
            values[field.id] = value[:5000]
    return values


def _application_body_with_template_fields(
    body: str,
    field_values: dict[int, str],
    fields: list[ApplicationTemplateFieldView],
) -> str:
    lines = [body.strip()] if body.strip() else []
    structured_lines = []
    for field_view in fields:
        field = field_view.field
        value = field_values.get(field.id, "")
        if value:
            structured_lines.append(f"{field.label}: {value}")
    if structured_lines:
        if lines:
            lines.append("")
        lines.append("Application fields")
        lines.extend(structured_lines)
    return "\n".join(lines)


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
