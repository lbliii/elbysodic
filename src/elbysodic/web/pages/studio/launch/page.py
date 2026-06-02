"""Director launch checklist for opening a realm."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.domain.models import CommunityAccessRequest
from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class LaunchActionForm:
    intent: str = ""
    email: str = ""
    invitation_id: str = ""
    access_request_id: str = ""
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
    if form.intent in {"revoke_invite", "reissue_invite"}:
        try:
            invitation_id = int(form.invitation_id)
        except ValueError:
            return _render_launch(request, invite_management_error="invitation is required")
        try:
            if form.intent == "reissue_invite":
                created = get_services(request).reissue_writer_invitation(invitation_id)
                return _render_launch(
                    request,
                    invite_path=created.path,
                    invite_email=created.invitation.email,
                    invite_management_message=(
                        f"Invitation for {created.invitation.email} was reissued. "
                        "Copy the new link now."
                    ),
                )
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
            launch_status_message=f"Opening changed to {updated.launch_status}.",
        )
    if form.intent in {"review_access_request", "decline_access_request"}:
        try:
            access_request_id = int(form.access_request_id)
        except ValueError:
            return _render_launch(request, access_request_error="access request is required")
        try:
            if form.intent == "review_access_request":
                updated_request = get_services(request).review_access_request(access_request_id)
                access_request_message = (
                    f"Access request from {_access_request_label(updated_request)} was reviewed."
                )
            else:
                updated_request = get_services(request).decline_access_request(access_request_id)
                access_request_message = (
                    f"Access request from {_access_request_label(updated_request)} was declined."
                )
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except (LookupError, ValueError) as exc:
            return _render_launch(request, access_request_error=str(exc))
        return _render_launch(request, access_request_message=access_request_message)
    if form.intent == "invite_access_request":
        try:
            access_request_id = int(form.access_request_id)
        except ValueError:
            return _render_launch(request, access_request_error="access request is required")
        try:
            services = get_services(request)
            request_item = services.access_request_detail(access_request_id)
            created = services.invite_access_request(access_request_id)
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except (LookupError, ValueError) as exc:
            return _render_launch(request, access_request_error=str(exc))
        return _render_launch(
            request,
            invite_path=created.path,
            invite_email=created.invitation.email,
            access_request_message=(
                f"Invitation created from access request for {request_item.display_label}."
            ),
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


def _access_request_label(access_request: CommunityAccessRequest) -> str:
    if access_request.display_name:
        return access_request.display_name
    if access_request.account_user_id is not None:
        return "linked Elbysodic account"
    return access_request.email


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
    access_request_message: str = "",
    access_request_error: str = "",
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
        access_request_items=services.writer_access_requests(),
        invite_management_message=invite_management_message,
        invite_management_error=invite_management_error,
        launch_status_message=launch_status_message,
        launch_status_error=launch_status_error,
        access_request_message=access_request_message,
        access_request_error=access_request_error,
    )
