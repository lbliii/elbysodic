"""Tenant-scoped staff capability audit events."""

from __future__ import annotations

from elbysodic.db.repositories.base import _last_id, _utc_now
from elbysodic.db.repositories.gateway import GatewayRepositoryMixin
from elbysodic.db.repositories.rows import _staff_audit_event_from_row
from elbysodic.domain.capabilities import STAFF_CAPABILITIES
from elbysodic.domain.models import StaffAuditEvent

AUDIT_OUTCOMES = frozenset({"accepted", "rejected", "failed"})


class AuditRepositoryMixin(GatewayRepositoryMixin):
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
    ) -> StaffAuditEvent:
        if capability not in STAFF_CAPABILITIES:
            raise ValueError(f"unknown staff capability: {capability}")
        if outcome not in AUDIT_OUTCOMES:
            raise ValueError(f"unknown audit outcome: {outcome}")
        if not target_family.strip() or not action.strip():
            raise ValueError("audit target family and action are required")
        self.get_membership(community_id, actor_membership_id)
        if actor_character_id is not None:
            character = self.get_character(community_id, actor_character_id)
            if character.membership_id != actor_membership_id:
                raise ValueError("audit character does not belong to the actor membership")
        cursor = self.connection.execute(
            """
            INSERT INTO staff_audit_events (
                community_id, actor_membership_id, actor_character_id, capability,
                target_family, target_id, action, outcome, reason, public_aftermath,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                actor_membership_id,
                actor_character_id,
                capability,
                target_family.strip(),
                target_id,
                action.strip(),
                outcome,
                reason.strip(),
                public_aftermath.strip(),
                _utc_now(),
            ),
        )
        self._commit()
        return self.get_staff_audit_event(community_id, _last_id(cursor))

    def get_staff_audit_event(self, community_id: int, event_id: int) -> StaffAuditEvent:
        row = self.connection.execute(
            """
            SELECT id, community_id, actor_membership_id, actor_character_id,
                   capability, target_family, target_id, action, outcome, reason,
                   public_aftermath, created_at
            FROM staff_audit_events
            WHERE community_id = ? AND id = ?
            """,
            (community_id, event_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"staff audit event not found in community {community_id}: {event_id}"
            )
        return _staff_audit_event_from_row(row)

    def list_staff_audit_events(
        self,
        community_id: int,
        *,
        capability: str | None = None,
        target_family: str | None = None,
        limit: int = 100,
    ) -> list[StaffAuditEvent]:
        if capability is not None and capability not in STAFF_CAPABILITIES:
            raise ValueError(f"unknown staff capability: {capability}")
        rows = self.connection.execute(
            """
            SELECT id, community_id, actor_membership_id, actor_character_id,
                   capability, target_family, target_id, action, outcome, reason,
                   public_aftermath, created_at
            FROM staff_audit_events
            WHERE community_id = ?
              AND (? IS NULL OR capability = ?)
              AND (? IS NULL OR target_family = ?)
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (
                community_id,
                capability,
                capability,
                target_family,
                target_family,
                min(max(1, limit), 500),
            ),
        ).fetchall()
        return [_staff_audit_event_from_row(row) for row in rows]
