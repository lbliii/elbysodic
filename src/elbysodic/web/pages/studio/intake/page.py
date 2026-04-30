"""Director intake and claim configuration."""

from __future__ import annotations

import json

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request) -> Page:
    return _render_intake_editor(request)


async def post(request: Request) -> Page | Redirect:
    services = get_services(request)
    form = await request.form()
    intent = str(form.get("intent") or "")
    try:
        if intent == "claim_type":
            services.update_claim_type_config(
                _required_int(form.get("claim_type_id"), "choose a claim type to update"),
                name=str(form.get("name") or ""),
                claim_kind=str(form.get("claim_kind") or ""),
                description=str(form.get("description") or ""),
                visibility=str(form.get("visibility") or "public"),
                is_required=form.get("is_required") == "on",
                is_exclusive=form.get("is_exclusive") == "on",
                sort_order=_required_int(form.get("sort_order"), "choose a claim type order"),
            )
        elif intent == "template_field":
            raw_claim_type_id = str(form.get("maps_to_claim_type_id") or "")
            services.update_application_template_field_config(
                _required_int(form.get("field_id"), "choose an application field to update"),
                label=str(form.get("label") or ""),
                field_type=str(form.get("field_type") or ""),
                help_text=str(form.get("help_text") or ""),
                placeholder=str(form.get("placeholder") or ""),
                options_json=_options_json(str(form.get("options") or "")),
                maps_to_claim_type_id=int(raw_claim_type_id) if raw_claim_type_id else None,
                is_required=form.get("is_required") == "on",
                sort_order=_required_int(form.get("sort_order"), "choose a field order"),
            )
        else:
            raise HTTPError(status=400, detail=f"unknown intake editor action: {intent}")
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except (LookupError, ValueError) as exc:
        return _render_intake_editor(request, error=str(exc))
    return Redirect("/studio/intake")


def _render_intake_editor(request: Request, *, error: str | None = None) -> Page:
    services = get_services(request)
    return Page(
        "studio/intake/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=services.viewer(),
        studio=services.director_studio(),
        directory=services.claims_directory(),
        onboarding=services.application_onboarding(),
        error=error,
    )


def _required_int(raw: object, message: str) -> int:
    value = str(raw or "")
    if not value:
        raise ValueError(message)
    return int(value)


def _options_json(raw: str) -> str:
    options = [line.strip() for line in raw.splitlines() if line.strip()]
    return json.dumps(options, separators=(",", ":"))
