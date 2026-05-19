"""Director intake and claim configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.pages.shell_actions import ShellAction, ShellActions, ShellActionZone
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class IntakeEditorForm:
    intent: str
    blueprint_yaml: str = ""
    preview_fingerprint: str = ""
    name: str = ""
    claim_kind: str = ""
    sort_order: str = ""
    description: str = ""
    is_required: bool = False
    is_exclusive: bool = False
    visibility: str = "public"
    claim_type_id: str = ""
    label: str = ""
    field_type: str = ""
    maps_to_claim_type_id: str = ""
    help_text: str = ""
    placeholder: str = ""
    options: str = ""
    field_id: str = ""


def get(request: Request) -> Page:
    return _render_intake_editor(request)


@contract(form=FormContract(IntakeEditorForm, "studio/intake/page.html"))
async def post(request: Request) -> Page | Redirect:
    services = get_services(request)
    form = await request.form()
    intent = str(form.get("intent") or "")
    try:
        if intent == "preview_blueprint":
            blueprint_yaml = str(form.get("blueprint_yaml") or "")
            return _render_intake_editor(
                request,
                blueprint_yaml=blueprint_yaml,
                blueprint_preview=services.preview_program_blueprint(blueprint_yaml),
            )
        elif intent == "apply_blueprint":
            blueprint_yaml = str(form.get("blueprint_yaml") or "")
            services.apply_program_blueprint_preview(
                blueprint_yaml,
                str(form.get("preview_fingerprint") or ""),
            )
        elif intent == "create_claim_type":
            services.create_claim_type_config(
                name=str(form.get("name") or ""),
                claim_kind=str(form.get("claim_kind") or ""),
                description=str(form.get("description") or ""),
                visibility=str(form.get("visibility") or "public"),
                is_required=form.get("is_required") == "on",
                is_exclusive=form.get("is_exclusive") == "on",
                sort_order=_required_int(form.get("sort_order"), "choose a claim type order"),
            )
        elif intent == "claim_type":
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
        elif intent == "create_template_field":
            raw_claim_type_id = str(form.get("maps_to_claim_type_id") or "")
            services.create_application_template_field_config(
                label=str(form.get("label") or ""),
                field_type=str(form.get("field_type") or ""),
                help_text=str(form.get("help_text") or ""),
                placeholder=str(form.get("placeholder") or ""),
                options_json=_options_json(str(form.get("options") or "")),
                maps_to_claim_type_id=int(raw_claim_type_id) if raw_claim_type_id else None,
                is_required=form.get("is_required") == "on",
                sort_order=_required_int(form.get("sort_order"), "choose a field order"),
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


def _render_intake_editor(
    request: Request,
    *,
    error: str | None = None,
    blueprint_yaml: str = "",
    blueprint_preview: object | None = None,
) -> Page:
    services = get_services(request)
    return Page.mounted(
        "studio/intake/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        studio=services.director_studio(),
        directory=services.claims_directory(),
        onboarding=services.application_onboarding(),
        blueprint_yaml=blueprint_yaml,
        blueprint_preview=blueprint_preview,
        error=error,
        shell_actions=_intake_shell_actions(),
    )


def _required_int(raw: object, message: str) -> int:
    value = str(raw or "")
    if not value:
        raise ValueError(message)
    return int(value)


def _options_json(raw: str) -> str:
    options = [line.strip() for line in raw.splitlines() if line.strip()]
    return json.dumps(options, separators=(",", ":"))


def _intake_shell_actions() -> ShellActions:
    return ShellActions(
        controls=ShellActionZone(
            items=(
                ShellAction(
                    id="intake-studio",
                    label="Studio",
                    href="/studio",
                    icon="grid",
                    variant="secondary",
                ),
                ShellAction(
                    id="intake-operations",
                    label="Operations",
                    href="/studio/operations",
                    icon="logs",
                    variant="secondary",
                ),
            )
        )
    )
