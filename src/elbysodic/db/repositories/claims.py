"""Claim and application-template repository methods."""

from __future__ import annotations

from elbysodic.db.repositories.base import TenantBoundaryError, _last_id, _utc_now
from elbysodic.db.repositories.interactions import InteractionRepositoryMixin
from elbysodic.db.repositories.rows import (
    _application_field_value_from_row,
    _application_template_field_from_row,
    _character_claim_from_row,
    _claim_type_from_row,
)
from elbysodic.domain.models import (
    ApplicationFieldValue,
    ApplicationTemplateField,
    CharacterClaim,
    ClaimType,
)


class ClaimRepositoryMixin(InteractionRepositoryMixin):
    def create_claim_type(
        self,
        community_id: int,
        slug: str,
        name: str,
        *,
        claim_kind: str = "custom",
        description: str = "",
        visibility: str = "public",
        is_required: bool = False,
        is_exclusive: bool = False,
        sort_order: int = 0,
    ) -> ClaimType:
        self.get_community(community_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO claim_types (
                community_id,
                slug,
                name,
                claim_kind,
                description,
                visibility,
                is_required,
                is_exclusive,
                sort_order,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                slug,
                name,
                claim_kind,
                description,
                visibility,
                int(is_required),
                int(is_exclusive),
                sort_order,
                now,
                now,
            ),
        )
        self._commit()
        return self.get_claim_type(community_id, _last_id(cursor))

    def update_claim_type(
        self,
        community_id: int,
        claim_type_id: int,
        *,
        name: str,
        claim_kind: str,
        description: str = "",
        visibility: str = "public",
        is_required: bool = False,
        is_exclusive: bool = False,
        sort_order: int = 0,
    ) -> ClaimType:
        self.get_claim_type(community_id, claim_type_id)
        self.connection.execute(
            """
            UPDATE claim_types
            SET
                name = ?,
                claim_kind = ?,
                description = ?,
                visibility = ?,
                is_required = ?,
                is_exclusive = ?,
                sort_order = ?,
                updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (
                name,
                claim_kind,
                description,
                visibility,
                int(is_required),
                int(is_exclusive),
                sort_order,
                _utc_now(),
                community_id,
                claim_type_id,
            ),
        )
        self._commit()
        return self.get_claim_type(community_id, claim_type_id)

    def get_claim_type(self, community_id: int, claim_type_id: int) -> ClaimType:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slug,
                name,
                claim_kind,
                description,
                visibility,
                is_required,
                is_exclusive,
                sort_order,
                created_at,
                updated_at
            FROM claim_types
            WHERE community_id = ? AND id = ?
            """,
            (community_id, claim_type_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"claim type not found in community {community_id}: {claim_type_id}")
        return _claim_type_from_row(row)

    def get_claim_type_by_slug(self, community_id: int, slug: str) -> ClaimType:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slug,
                name,
                claim_kind,
                description,
                visibility,
                is_required,
                is_exclusive,
                sort_order,
                created_at,
                updated_at
            FROM claim_types
            WHERE community_id = ? AND slug = ?
            """,
            (community_id, slug),
        ).fetchone()
        if row is None:
            raise LookupError(f"claim type not found in community {community_id}: {slug}")
        return _claim_type_from_row(row)

    def list_claim_types(self, community_id: int) -> list[ClaimType]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slug,
                name,
                claim_kind,
                description,
                visibility,
                is_required,
                is_exclusive,
                sort_order,
                created_at,
                updated_at
            FROM claim_types
            WHERE community_id = ?
            ORDER BY sort_order, name, id
            """,
            (community_id,),
        ).fetchall()
        return [_claim_type_from_row(row) for row in rows]

    def create_character_claim(
        self,
        community_id: int,
        claim_type_id: int,
        value: str,
        label: str,
        *,
        character_id: int | None = None,
        application_id: int | None = None,
        source_reserve_id: int | None = None,
        status: str = "claimed",
        notes: str = "",
    ) -> CharacterClaim:
        claim_type = self.get_claim_type(community_id, claim_type_id)
        if character_id is not None:
            self.get_character(community_id, character_id)
        if application_id is not None:
            self.get_character_application(community_id, application_id)
        if source_reserve_id is not None:
            self.get_character_reserve(community_id, source_reserve_id)
        if claim_type.is_exclusive and status in {"claimed", "reserved"} and value:
            live_claim = self.connection.execute(
                """
                SELECT id
                FROM character_claims
                WHERE community_id = ?
                    AND claim_type_id = ?
                    AND value = ?
                    AND status IN ('claimed', 'reserved')
                """,
                (community_id, claim_type_id, value),
            ).fetchone()
            if live_claim is not None:
                raise TenantBoundaryError(f"claim value is already in use: {label}")
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO character_claims (
                community_id,
                claim_type_id,
                character_id,
                application_id,
                source_reserve_id,
                value,
                label,
                status,
                notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                claim_type_id,
                character_id,
                application_id,
                source_reserve_id,
                value,
                label,
                status,
                notes,
                now,
                now,
            ),
        )
        self._commit()
        return self.get_character_claim(community_id, _last_id(cursor))

    def update_character_claim(
        self,
        community_id: int,
        claim_id: int,
        *,
        value: str,
        label: str,
        character_id: int | None = None,
        status: str = "claimed",
        notes: str = "",
    ) -> CharacterClaim:
        claim = self.get_character_claim(community_id, claim_id)
        claim_type = self.get_claim_type(community_id, claim.claim_type_id)
        if character_id is not None:
            self.get_character(community_id, character_id)
        if claim_type.is_exclusive and status in {"claimed", "reserved"} and value:
            live_claim = self.connection.execute(
                """
                SELECT id
                FROM character_claims
                WHERE community_id = ?
                    AND claim_type_id = ?
                    AND value = ?
                    AND status IN ('claimed', 'reserved')
                    AND id != ?
                """,
                (community_id, claim.claim_type_id, value, claim_id),
            ).fetchone()
            if live_claim is not None:
                raise TenantBoundaryError(f"claim value is already in use: {label}")
        self.connection.execute(
            """
            UPDATE character_claims
            SET
                character_id = ?,
                value = ?,
                label = ?,
                status = ?,
                notes = ?,
                updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (
                character_id,
                value,
                label,
                status,
                notes,
                _utc_now(),
                community_id,
                claim_id,
            ),
        )
        self._commit()
        return self.get_character_claim(community_id, claim_id)

    def get_character_claim(self, community_id: int, claim_id: int) -> CharacterClaim:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                claim_type_id,
                character_id,
                application_id,
                source_reserve_id,
                value,
                label,
                status,
                notes,
                created_at,
                updated_at
            FROM character_claims
            WHERE community_id = ? AND id = ?
            """,
            (community_id, claim_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"character claim not found in community {community_id}: {claim_id}")
        return _character_claim_from_row(row)

    def list_character_claims(
        self,
        community_id: int,
        *,
        status: str | None = "claimed",
        claim_type_id: int | None = None,
    ) -> list[CharacterClaim]:
        if status is None and claim_type_id is None:
            query = (
                _CHARACTER_CLAIMS_BASE_QUERY
                + """
                WHERE community_id = ?
                ORDER BY claim_type_id, label, id
            """
            )
            params: tuple[object, ...] = (community_id,)
        elif status is not None and claim_type_id is None:
            query = (
                _CHARACTER_CLAIMS_BASE_QUERY
                + """
                WHERE community_id = ? AND status = ?
                ORDER BY claim_type_id, label, id
            """
            )
            params = (community_id, status)
        elif status is None and claim_type_id is not None:
            query = (
                _CHARACTER_CLAIMS_BASE_QUERY
                + """
                WHERE community_id = ? AND claim_type_id = ?
                ORDER BY claim_type_id, label, id
            """
            )
            params = (community_id, claim_type_id)
        else:
            query = (
                _CHARACTER_CLAIMS_BASE_QUERY
                + """
                WHERE community_id = ? AND status = ? AND claim_type_id = ?
                ORDER BY claim_type_id, label, id
            """
            )
            params = (community_id, status, claim_type_id)
        rows = self.connection.execute(query, params).fetchall()
        return [_character_claim_from_row(row) for row in rows]

    def list_character_claims_for_character(
        self,
        community_id: int,
        character_id: int,
        *,
        status: str | None = "claimed",
    ) -> list[CharacterClaim]:
        self.get_character(community_id, character_id)
        if status is None:
            query = (
                _CHARACTER_CLAIMS_BASE_QUERY
                + """
                WHERE community_id = ? AND character_id = ?
                ORDER BY claim_type_id, label, id
            """
            )
            params: tuple[object, ...] = (community_id, character_id)
        else:
            query = (
                _CHARACTER_CLAIMS_BASE_QUERY
                + """
                WHERE community_id = ? AND character_id = ? AND status = ?
                ORDER BY claim_type_id, label, id
            """
            )
            params = (community_id, character_id, status)
        rows = self.connection.execute(query, params).fetchall()
        return [_character_claim_from_row(row) for row in rows]

    def create_application_template_field(
        self,
        community_id: int,
        field_key: str,
        label: str,
        *,
        field_type: str = "text",
        help_text: str = "",
        placeholder: str = "",
        options_json: str = "[]",
        maps_to_claim_type_id: int | None = None,
        is_required: bool = False,
        sort_order: int = 0,
    ) -> ApplicationTemplateField:
        self.get_community(community_id)
        if maps_to_claim_type_id is not None:
            self.get_claim_type(community_id, maps_to_claim_type_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO application_template_fields (
                community_id,
                field_key,
                label,
                field_type,
                help_text,
                placeholder,
                options_json,
                maps_to_claim_type_id,
                is_required,
                sort_order,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                field_key,
                label,
                field_type,
                help_text,
                placeholder,
                options_json,
                maps_to_claim_type_id,
                int(is_required),
                sort_order,
                now,
                now,
            ),
        )
        self._commit()
        return self.get_application_template_field(community_id, _last_id(cursor))

    def update_application_template_field(
        self,
        community_id: int,
        field_id: int,
        *,
        label: str,
        field_type: str,
        help_text: str = "",
        placeholder: str = "",
        options_json: str = "[]",
        maps_to_claim_type_id: int | None = None,
        is_required: bool = False,
        sort_order: int = 0,
    ) -> ApplicationTemplateField:
        self.get_application_template_field(community_id, field_id)
        if maps_to_claim_type_id is not None:
            self.get_claim_type(community_id, maps_to_claim_type_id)
        self.connection.execute(
            """
            UPDATE application_template_fields
            SET
                label = ?,
                field_type = ?,
                help_text = ?,
                placeholder = ?,
                options_json = ?,
                maps_to_claim_type_id = ?,
                is_required = ?,
                sort_order = ?,
                updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (
                label,
                field_type,
                help_text,
                placeholder,
                options_json,
                maps_to_claim_type_id,
                int(is_required),
                sort_order,
                _utc_now(),
                community_id,
                field_id,
            ),
        )
        self._commit()
        return self.get_application_template_field(community_id, field_id)

    def get_application_template_field(
        self,
        community_id: int,
        field_id: int,
    ) -> ApplicationTemplateField:
        row = self.connection.execute(
            _APPLICATION_TEMPLATE_FIELD_BASE_QUERY
            + """
            WHERE community_id = ? AND id = ?
            """,
            (community_id, field_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"application template field not found in community {community_id}: {field_id}"
            )
        return _application_template_field_from_row(row)

    def get_application_template_field_by_key(
        self,
        community_id: int,
        field_key: str,
    ) -> ApplicationTemplateField:
        row = self.connection.execute(
            _APPLICATION_TEMPLATE_FIELD_BASE_QUERY
            + """
            WHERE community_id = ? AND field_key = ?
            """,
            (community_id, field_key),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"application template field not found in community {community_id}: {field_key}"
            )
        return _application_template_field_from_row(row)

    def list_application_template_fields(
        self,
        community_id: int,
    ) -> list[ApplicationTemplateField]:
        rows = self.connection.execute(
            _APPLICATION_TEMPLATE_FIELD_BASE_QUERY
            + """
            WHERE community_id = ?
            ORDER BY sort_order, label, id
            """,
            (community_id,),
        ).fetchall()
        return [_application_template_field_from_row(row) for row in rows]

    def set_application_field_value(
        self,
        community_id: int,
        application_id: int,
        field_id: int,
        value: str,
    ) -> ApplicationFieldValue:
        self.get_character_application(community_id, application_id)
        self.get_application_template_field(community_id, field_id)
        now = _utc_now()
        self.connection.execute(
            """
            INSERT INTO application_field_values (
                community_id,
                application_id,
                field_id,
                value,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (community_id, application_id, field_id)
            DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (
                community_id,
                application_id,
                field_id,
                value,
                now,
                now,
            ),
        )
        self._commit()
        return self.get_application_field_value(community_id, application_id, field_id)

    def get_application_field_value(
        self,
        community_id: int,
        application_id: int,
        field_id: int,
    ) -> ApplicationFieldValue:
        row = self.connection.execute(
            _APPLICATION_FIELD_VALUE_BASE_QUERY
            + """
            WHERE community_id = ? AND application_id = ? AND field_id = ?
            """,
            (community_id, application_id, field_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                "application field value not found in community "
                f"{community_id}: {application_id}/{field_id}"
            )
        return _application_field_value_from_row(row)

    def list_application_field_values(
        self,
        community_id: int,
        application_id: int,
    ) -> list[ApplicationFieldValue]:
        self.get_character_application(community_id, application_id)
        rows = self.connection.execute(
            _APPLICATION_FIELD_VALUE_BASE_QUERY
            + """
            WHERE community_id = ? AND application_id = ?
            ORDER BY field_id, id
            """,
            (community_id, application_id),
        ).fetchall()
        return [_application_field_value_from_row(row) for row in rows]


_CHARACTER_CLAIMS_BASE_QUERY = """
    SELECT
        id,
        community_id,
        claim_type_id,
        character_id,
        application_id,
        source_reserve_id,
        value,
        label,
        status,
        notes,
        created_at,
        updated_at
    FROM character_claims
"""


_APPLICATION_TEMPLATE_FIELD_BASE_QUERY = """
    SELECT
        id,
        community_id,
        field_key,
        label,
        field_type,
        help_text,
        placeholder,
        options_json,
        maps_to_claim_type_id,
        is_required,
        sort_order,
        created_at,
        updated_at
    FROM application_template_fields
"""


_APPLICATION_FIELD_VALUE_BASE_QUERY = """
    SELECT
        id,
        community_id,
        application_id,
        field_id,
        value,
        created_at,
        updated_at
    FROM application_field_values
"""
