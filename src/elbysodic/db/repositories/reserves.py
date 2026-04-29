"""Character reserve repository methods."""

from __future__ import annotations

from elbysodic.db.repositories.base import TenantBoundaryError, _utc_now
from elbysodic.db.repositories.plotting import PlottingRepositoryMixin
from elbysodic.db.repositories.rows import _character_reserve_from_row
from elbysodic.domain.models import CharacterReserve


class ReserveRepositoryMixin(PlottingRepositoryMixin):
    def create_character_reserve(
        self,
        community_id: int,
        membership_id: int,
        character_id: int,
        title: str,
        *,
        wanted_ad_id: int | None = None,
        wanted_ad_interest_id: int | None = None,
        reserve_type: str = "wanted",
        notes: str = "",
        status: str = "active",
    ) -> CharacterReserve:
        self.get_membership(community_id, membership_id)
        character = self.get_character(community_id, character_id)
        if character.membership_id != membership_id:
            raise TenantBoundaryError(
                f"character {character_id} does not belong to membership {membership_id}"
            )
        if wanted_ad_id is not None:
            self.get_wanted_ad(community_id, wanted_ad_id)
        if wanted_ad_interest_id is not None:
            interest = self.get_wanted_ad_interest(community_id, wanted_ad_interest_id)
            if interest.character_id is None:
                raise TenantBoundaryError(
                    f"wanted interest {wanted_ad_interest_id} has no reserved character yet"
                )
            if interest.membership_id != membership_id or interest.character_id != character_id:
                raise TenantBoundaryError(
                    f"wanted interest {wanted_ad_interest_id} does not belong to reserve owner"
                )
            if wanted_ad_id is not None and interest.wanted_ad_id != wanted_ad_id:
                raise TenantBoundaryError(
                    f"wanted interest {wanted_ad_interest_id} does not belong to wanted ad {wanted_ad_id}"
                )
        now = _utc_now()
        self.connection.execute(
            """
            INSERT OR IGNORE INTO character_reserves (
                community_id,
                membership_id,
                character_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                reserve_type,
                title,
                notes,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                membership_id,
                character_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                reserve_type,
                title,
                notes,
                status,
                now,
                now,
            ),
        )
        self.connection.commit()
        if wanted_ad_interest_id is not None:
            return self.get_character_reserve_for_wanted_interest(
                community_id,
                wanted_ad_interest_id,
            )
        row = self.connection.execute(
            """
            SELECT MAX(id) AS id
            FROM character_reserves
            WHERE community_id = ? AND membership_id = ? AND character_id = ?
            """,
            (community_id, membership_id, character_id),
        ).fetchone()
        return self.get_character_reserve(community_id, int(row["id"]))

    def get_character_reserve(
        self,
        community_id: int,
        reserve_id: int,
    ) -> CharacterReserve:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                character_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                reserve_type,
                title,
                notes,
                status,
                created_at,
                updated_at
            FROM character_reserves
            WHERE community_id = ? AND id = ?
            """,
            (community_id, reserve_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"character reserve not found in community {community_id}: {reserve_id}"
            )
        return _character_reserve_from_row(row)

    def get_character_reserve_for_wanted_interest(
        self,
        community_id: int,
        wanted_ad_interest_id: int,
    ) -> CharacterReserve:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                character_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                reserve_type,
                title,
                notes,
                status,
                created_at,
                updated_at
            FROM character_reserves
            WHERE community_id = ? AND wanted_ad_interest_id = ?
            """,
            (community_id, wanted_ad_interest_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"character reserve not found in community {community_id}: {wanted_ad_interest_id}"
            )
        return _character_reserve_from_row(row)

    def list_character_reserves(
        self,
        community_id: int,
        character_id: int,
        *,
        status: str | None = "active",
    ) -> list[CharacterReserve]:
        self.get_character(community_id, character_id)
        where = "WHERE community_id = ? AND character_id = ?"
        params: tuple[object, ...] = (community_id, character_id)
        if status is not None:
            where = f"{where} AND status = ?"
            params = (*params, status)
        rows = self.connection.execute(
            f"""
            SELECT
                id,
                community_id,
                membership_id,
                character_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                reserve_type,
                title,
                notes,
                status,
                created_at,
                updated_at
            FROM character_reserves
            {where}
            ORDER BY created_at DESC, id DESC
            """,
            params,
        ).fetchall()
        return [_character_reserve_from_row(row) for row in rows]

    def list_character_reserves_for_wanted_ad(
        self,
        community_id: int,
        wanted_ad_id: int,
        *,
        status: str | None = "active",
    ) -> list[CharacterReserve]:
        self.get_wanted_ad(community_id, wanted_ad_id)
        where = "WHERE community_id = ? AND wanted_ad_id = ?"
        params: tuple[object, ...] = (community_id, wanted_ad_id)
        if status is not None:
            where = f"{where} AND status = ?"
            params = (*params, status)
        rows = self.connection.execute(
            f"""
            SELECT
                id,
                community_id,
                membership_id,
                character_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                reserve_type,
                title,
                notes,
                status,
                created_at,
                updated_at
            FROM character_reserves
            {where}
            ORDER BY created_at DESC, id DESC
            """,
            params,
        ).fetchall()
        return [_character_reserve_from_row(row) for row in rows]

    def list_character_reserves_for_community(
        self,
        community_id: int,
        *,
        status: str | None = "active",
    ) -> list[CharacterReserve]:
        self.get_community(community_id)
        where = "WHERE community_id = ?"
        params: tuple[object, ...] = (community_id,)
        if status is not None:
            where = f"{where} AND status = ?"
            params = (*params, status)
        rows = self.connection.execute(
            f"""
            SELECT
                id,
                community_id,
                membership_id,
                character_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                reserve_type,
                title,
                notes,
                status,
                created_at,
                updated_at
            FROM character_reserves
            {where}
            ORDER BY updated_at DESC, created_at DESC, id DESC
            """,
            params,
        ).fetchall()
        return [_character_reserve_from_row(row) for row in rows]
