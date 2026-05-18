"""Curated community gateway slot repository methods."""

from __future__ import annotations

from collections.abc import Sequence

from elbysodic.db.repositories.base import _last_id, _next_update_stamp, _utc_now
from elbysodic.db.repositories.discovery import DiscoveryRepositoryMixin
from elbysodic.db.repositories.rows import _community_gateway_slot_from_row
from elbysodic.domain.models import CommunityGatewaySlot

GATEWAY_SLOT_SCENE_HUB = "scene_hub"
GATEWAY_SLOT_WANTED_HOOK = "wanted_hook"
GATEWAY_SLOT_GUIDEBOOK_MATERIAL = "guidebook_material"

SUPPORTED_GATEWAY_SLOT_TYPES = frozenset(
    {
        GATEWAY_SLOT_SCENE_HUB,
        GATEWAY_SLOT_WANTED_HOOK,
        GATEWAY_SLOT_GUIDEBOOK_MATERIAL,
    }
)

PUBLIC_SCENE_HUB_BOARD_KINDS = frozenset({"community", "location", "sublocation"})


class GatewayRepositoryMixin(DiscoveryRepositoryMixin):
    def create_community_gateway_slot(
        self,
        community_id: int,
        slot_type: str,
        target_id: int,
        *,
        position: int | None = None,
        label: str = "",
    ) -> CommunityGatewaySlot:
        normalized_type = _require_gateway_slot_type(slot_type)
        self._validate_gateway_slot_target(community_id, normalized_type, target_id)
        resolved_position = (
            self._next_gateway_slot_position(community_id, normalized_type)
            if position is None
            else position
        )
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO community_gateway_slots (
                community_id,
                slot_type,
                target_id,
                position,
                label,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                normalized_type,
                target_id,
                resolved_position,
                label.strip(),
                now,
                now,
            ),
        )
        self._commit()
        return self.get_community_gateway_slot(community_id, _last_id(cursor))

    def get_community_gateway_slot(
        self,
        community_id: int,
        slot_id: int,
    ) -> CommunityGatewaySlot:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slot_type,
                target_id,
                position,
                label,
                created_at,
                updated_at
            FROM community_gateway_slots
            WHERE community_id = ? AND id = ?
            """,
            (community_id, slot_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"gateway slot not found in community {community_id}: {slot_id}")
        return _community_gateway_slot_from_row(row)

    def list_community_gateway_slots(
        self,
        community_id: int,
        *,
        slot_type: str | None = None,
    ) -> list[CommunityGatewaySlot]:
        self.get_community(community_id)
        if slot_type is None:
            rows = self.connection.execute(
                """
                SELECT
                    id,
                    community_id,
                    slot_type,
                    target_id,
                    position,
                    label,
                    created_at,
                    updated_at
                FROM community_gateway_slots
                WHERE community_id = ?
                ORDER BY slot_type, position, id
                """,
                (community_id,),
            ).fetchall()
        else:
            normalized_type = _require_gateway_slot_type(slot_type)
            rows = self.connection.execute(
                """
                SELECT
                    id,
                    community_id,
                    slot_type,
                    target_id,
                    position,
                    label,
                    created_at,
                    updated_at
                FROM community_gateway_slots
                WHERE community_id = ? AND slot_type = ?
                ORDER BY position, id
                """,
                (community_id, normalized_type),
            ).fetchall()
        return [_community_gateway_slot_from_row(row) for row in rows]

    def update_community_gateway_slot(
        self,
        community_id: int,
        slot_id: int,
        *,
        position: int,
        label: str = "",
    ) -> CommunityGatewaySlot:
        slot = self.get_community_gateway_slot(community_id, slot_id)
        self._validate_gateway_slot_target(community_id, slot.slot_type, slot.target_id)
        self.connection.execute(
            """
            UPDATE community_gateway_slots
            SET position = ?, label = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (
                position,
                label.strip(),
                _next_update_stamp(slot.updated_at),
                community_id,
                slot.id,
            ),
        )
        self._commit()
        return self.get_community_gateway_slot(community_id, slot.id)

    def delete_community_gateway_slot(self, community_id: int, slot_id: int) -> None:
        self.get_community_gateway_slot(community_id, slot_id)
        self.connection.execute(
            """
            DELETE FROM community_gateway_slots
            WHERE community_id = ? AND id = ?
            """,
            (community_id, slot_id),
        )
        self._commit()

    def replace_community_gateway_slots(
        self,
        community_id: int,
        slot_type: str,
        targets: Sequence[tuple[int, str]],
    ) -> list[CommunityGatewaySlot]:
        normalized_type = _require_gateway_slot_type(slot_type)
        self.get_community(community_id)
        for target_id, _label in targets:
            self._validate_gateway_slot_target(community_id, normalized_type, target_id)
        now = _utc_now()
        with self.transaction():
            self.connection.execute(
                """
                DELETE FROM community_gateway_slots
                WHERE community_id = ? AND slot_type = ?
                """,
                (community_id, normalized_type),
            )
            for index, (target_id, label) in enumerate(targets):
                self.connection.execute(
                    """
                    INSERT INTO community_gateway_slots (
                        community_id,
                        slot_type,
                        target_id,
                        position,
                        label,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        community_id,
                        normalized_type,
                        target_id,
                        (index + 1) * 10,
                        label.strip(),
                        now,
                        now,
                    ),
                )
        return self.list_community_gateway_slots(community_id, slot_type=normalized_type)

    def _next_gateway_slot_position(self, community_id: int, slot_type: str) -> int:
        row = self.connection.execute(
            """
            SELECT COALESCE(MAX(position), 0) AS max_position
            FROM community_gateway_slots
            WHERE community_id = ? AND slot_type = ?
            """,
            (community_id, slot_type),
        ).fetchone()
        return int(row["max_position"]) + 10

    def _validate_gateway_slot_target(
        self,
        community_id: int,
        slot_type: str,
        target_id: int,
    ) -> None:
        if slot_type == GATEWAY_SLOT_SCENE_HUB:
            board = self.get_board(community_id, target_id)
            if board.is_private or board.board_kind not in PUBLIC_SCENE_HUB_BOARD_KINDS:
                raise ValueError("scene hub gateway slots require a public scene hub board")
            return
        if slot_type == GATEWAY_SLOT_WANTED_HOOK:
            wanted = self.get_wanted_ad(community_id, target_id)
            if wanted.status != "open":
                raise ValueError("wanted hook gateway slots require an open wanted hook")
            return
        if slot_type == GATEWAY_SLOT_GUIDEBOOK_MATERIAL:
            material = self.get_material(community_id, target_id)
            if material.status != "published":
                raise ValueError("guidebook gateway slots require a published material")
            return
        _require_gateway_slot_type(slot_type)


def _require_gateway_slot_type(slot_type: str) -> str:
    normalized = slot_type.strip()
    if normalized not in SUPPORTED_GATEWAY_SLOT_TYPES:
        allowed = ", ".join(sorted(SUPPORTED_GATEWAY_SLOT_TYPES))
        raise ValueError(f"gateway slot type must be one of: {allowed}")
    return normalized
