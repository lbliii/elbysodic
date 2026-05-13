"""World material detail page."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.services.forum import MATERIAL_STATUSES, MATERIAL_TYPES
from elbysodic.web.recovery import recover_missing_route
from elbysodic.web.state import get_services
from elbysodic.web.tenant import request_tenant_slug


@dataclass(frozen=True, slots=True)
class MaterialEditorForm:
    title: str
    material_type: str
    status: str = "published"
    is_featured: bool = False
    summary: str = ""
    body: str = ""


def get(request: Request, material_slug: str) -> Page:
    return _render_material(request, material_slug)


@contract(form=FormContract(MaterialEditorForm, "world/{material_slug}/page.html"))
async def post(request: Request, material_slug: str) -> Page | Redirect:
    services = get_services(request)
    form = await request.form()
    try:
        material = services.update_material(
            material_slug,
            title=str(form.get("title") or ""),
            material_type=str(form.get("material_type") or ""),
            summary=str(form.get("summary") or ""),
            body=str(form.get("body") or ""),
            status=str(form.get("status") or "published"),
            is_featured=bool(form.get("is_featured")),
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        return _render_material(
            request,
            material_slug,
            error=str(exc),
            title=str(form.get("title") or ""),
            material_type=str(form.get("material_type") or ""),
            summary=str(form.get("summary") or ""),
            body=str(form.get("body") or ""),
            status=str(form.get("status") or "published"),
            is_featured=bool(form.get("is_featured")),
        )
    return Redirect(f"/world/{material.slug}")


def _render_material(
    request: Request,
    material_slug: str,
    *,
    error: str | None = None,
    title: str | None = None,
    material_type: str | None = None,
    summary: str | None = None,
    body: str | None = None,
    status: str | None = None,
    is_featured: bool | None = None,
) -> Page:
    tenant_slug = request_tenant_slug(request)
    try:
        services = get_services(request)
        viewer = services.viewer()
    except LookupError, PermissionError:
        if tenant_slug is None:
            raise
        services = get_services(request)
        try:
            material = services.public_read_material(tenant_slug, material_slug)
            guidebook = services.public_world_hub(tenant_slug)
            community = services.public_studio_program(tenant_slug).community
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        viewer = None
    else:
        try:
            material = services.read_material(material_slug)
        except LookupError:
            return recover_missing_route(request, kind="material", slug=material_slug)
        guidebook = services.world_hub()
        community = viewer.community
    return Page.mounted(
        "world/{material_slug}/page.html",
        current_path=request.url,
        viewer=viewer,
        community=community,
        material=material,
        guidebook=guidebook,
        material_types=MATERIAL_TYPES,
        material_statuses=MATERIAL_STATUSES,
        show_community_shell=viewer is not None,
        error=error,
        title=material.material.title if title is None else title,
        material_type=material.material.material_type if material_type is None else material_type,
        summary=material.material.summary if summary is None else summary,
        body=material.material.body if body is None else body,
        status=material.material.status if status is None else status,
        is_featured=material.material.is_featured if is_featured is None else is_featured,
    )
