"""Capability-scoped staff audit trail service contract."""

from __future__ import annotations

from typing import Protocol

from elbysodic.domain.models import StaffAuditEvent
from elbysodic.services import policies
from elbysodic.services.read_models import ForumView


class StaffAuditRepository(Protocol):
    def create_staff_audit_event(
        self,
        community_id: int,
        actor_membership_id: int,
        *,
        capability: str,
        target_family: str,
        action: str,
        outcome: str,
        target_id: int | None = None,
        actor_character_id: int | None = None,
        reason: str = "",
        public_aftermath: str = "",
    ) -> StaffAuditEvent: ...

    def list_staff_audit_events(
        self,
        community_id: int,
        *,
        capability: str | None = None,
        target_family: str | None = None,
        limit: int = 100,
    ) -> list[StaffAuditEvent]: ...


def record_staff_audit_event(
    repo: StaffAuditRepository,
    viewer: ForumView,
    *,
    capability: policies.Capability,
    target_family: str,
    action: str,
    outcome: str = "accepted",
    target_id: int | None = None,
    reason: str = "",
    public_aftermath: str = "",
) -> StaffAuditEvent:
    """Record one durable event only for a capability granted to this actor."""

    diagnostic = policies.explain_capability(viewer.membership, viewer.role, capability)
    if not diagnostic.allowed:
        raise PermissionError(diagnostic.message)
    return repo.create_staff_audit_event(
        viewer.community.id,
        viewer.membership.id,
        actor_character_id=(
            viewer.current_character.id
            if viewer.current_character is not None
            and viewer.current_character.membership_id == viewer.membership.id
            else None
        ),
        capability=capability,
        target_family=target_family,
        target_id=target_id,
        action=action,
        outcome=outcome,
        reason=reason,
        public_aftermath=public_aftermath,
    )


def staff_audit_trail(
    repo: StaffAuditRepository,
    viewer: ForumView,
    *,
    capability: policies.Capability | None = None,
    target_family: str | None = None,
    limit: int = 100,
) -> list[StaffAuditEvent]:
    """Return only events within a capability the viewer may exercise."""

    required = capability or "manage_world"
    diagnostic = policies.explain_capability(viewer.membership, viewer.role, required)
    if not diagnostic.allowed:
        raise PermissionError(diagnostic.message)
    return repo.list_staff_audit_events(
        viewer.community.id,
        capability=capability,
        target_family=target_family,
        limit=limit,
    )
