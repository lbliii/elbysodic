"""Director launch checklist for opening a realm."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class LaunchActionForm:
    intent: str = ""
    email: str = ""
    invitation_id: str = ""
    launch_status: str = ""
    scene_hub_name: str = ""
    premise_summary: str = ""
    application_summary: str = ""


def get(request: Request) -> Page:
    return _render_launch(request)


@contract(form=FormContract(LaunchActionForm, "studio/launch/page.html"))
async def post(request: Request, form: LaunchActionForm) -> Page:
    if form.intent == "apply_builder":
        try:
            result = get_services(request).apply_guided_realm_builder_minimum(
                scene_hub_name=form.scene_hub_name,
                premise_summary=form.premise_summary,
                application_summary=form.application_summary,
            )
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            return _render_launch(request, builder_error=str(exc), builder_form=form)
        return _render_launch(request, builder_message=result.status_message)
    if form.intent == "revoke_invite":
        try:
            invitation_id = int(form.invitation_id)
        except ValueError:
            return _render_launch(request, invite_management_error="invitation is required")
        try:
            revoked = get_services(request).revoke_writer_invitation(invitation_id)
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except (LookupError, ValueError) as exc:
            return _render_launch(request, invite_management_error=str(exc))
        return _render_launch(
            request,
            invite_management_message=f"Invitation for {revoked.email} was revoked.",
        )
    if form.intent == "launch_status":
        try:
            updated = get_services(request).update_realm_launch_status(form.launch_status)
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            return _render_launch(request, launch_status_error=str(exc))
        return _render_launch(
            request,
            launch_status_message=f"Launch status changed to {updated.launch_status}.",
        )
    if form.intent != "create_invite":
        raise HTTPError(status=400, detail="unsupported launch action")
    try:
        created = get_services(request).create_writer_invitation(form.email)
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        return _render_launch(request, invite_error=str(exc), invite_email=form.email)
    return _render_launch(
        request,
        invite_path=created.path,
        invite_email=created.invitation.email,
    )


def _render_launch(
    request: Request,
    *,
    invite_path: str = "",
    invite_email: str = "",
    invite_error: str = "",
    builder_message: str = "",
    builder_error: str = "",
    builder_form: LaunchActionForm | None = None,
    invite_management_message: str = "",
    invite_management_error: str = "",
    launch_status_message: str = "",
    launch_status_error: str = "",
) -> Page:
    services = get_services(request)
    studio = services.director_studio()
    if not studio.can_manage:
        raise HTTPError(status=403, detail="director access is required")
    return Page.mounted(
        "studio/launch/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        studio=studio,
        launch=studio.launch_readiness,
        invite_path=invite_path,
        invite_email=invite_email,
        invite_error=invite_error,
        builder_message=builder_message,
        builder_error=builder_error,
        builder_form=builder_form or LaunchActionForm(),
        invite_items=services.writer_invitations(),
        invite_management_message=invite_management_message,
        invite_management_error=invite_management_error,
        launch_status_message=launch_status_message,
        launch_status_error=launch_status_error,
    )
