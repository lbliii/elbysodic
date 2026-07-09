"""Passkey credential repository methods for global login accounts."""

from __future__ import annotations

import sqlite3

from elbysodic.db.repositories.base import _last_id, _utc_now
from elbysodic.db.repositories.identity import IdentityRepositoryMixin
from elbysodic.db.repositories.rows import _user_passkey_credential_from_row
from elbysodic.domain.models import UserPasskeyCredential


class PasskeyRepositoryMixin(IdentityRepositoryMixin):
    """Per-user, multi-credential passkey storage.

    Passkey credentials attach to global login accounts (like
    ``user_sessions``), not to one community membership: signing in happens
    before a realm identity is selected. Tenant scope stays with membership;
    credential material stays auth-side and is redacted from exports and
    restore-check output.
    """

    def create_user_passkey_credential(
        self,
        user_id: int,
        *,
        credential_id: bytes,
        public_key: bytes,
        sign_count: int,
        transports: tuple[str, ...] = (),
        label: str = "",
    ) -> UserPasskeyCredential:
        self.get_user(user_id)
        try:
            cursor = self.connection.execute(
                """
                INSERT INTO user_passkey_credentials (
                    user_id,
                    credential_id,
                    public_key,
                    sign_count,
                    transports,
                    label,
                    created_at,
                    last_used_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    user_id,
                    credential_id,
                    public_key,
                    sign_count,
                    ",".join(part.strip() for part in transports if part.strip()),
                    label.strip(),
                    _utc_now(),
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("passkey credential is already registered") from exc
        self._commit()
        return self.get_user_passkey_credential_by_id(_last_id(cursor))

    def get_user_passkey_credential_by_id(self, passkey_id: int) -> UserPasskeyCredential:
        row = self.connection.execute(
            """
            SELECT
                id,
                user_id,
                credential_id,
                public_key,
                sign_count,
                transports,
                label,
                created_at,
                last_used_at
            FROM user_passkey_credentials
            WHERE id = ?
            """,
            (passkey_id,),
        ).fetchone()
        if row is None:
            raise LookupError(f"passkey credential not found: {passkey_id}")
        return _user_passkey_credential_from_row(row)

    def get_user_passkey_credential(self, credential_id: bytes) -> UserPasskeyCredential:
        row = self.connection.execute(
            """
            SELECT
                id,
                user_id,
                credential_id,
                public_key,
                sign_count,
                transports,
                label,
                created_at,
                last_used_at
            FROM user_passkey_credentials
            WHERE credential_id = ?
            """,
            (credential_id,),
        ).fetchone()
        if row is None:
            raise LookupError("passkey credential not found")
        return _user_passkey_credential_from_row(row)

    def list_user_passkey_credentials(self, user_id: int) -> list[UserPasskeyCredential]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                user_id,
                credential_id,
                public_key,
                sign_count,
                transports,
                label,
                created_at,
                last_used_at
            FROM user_passkey_credentials
            WHERE user_id = ?
            ORDER BY created_at, id
            """,
            (user_id,),
        ).fetchall()
        return [_user_passkey_credential_from_row(row) for row in rows]

    def update_user_passkey_credential_sign_count(
        self,
        credential_id: bytes,
        sign_count: int,
    ) -> UserPasskeyCredential:
        credential = self.get_user_passkey_credential(credential_id)
        self.connection.execute(
            """
            UPDATE user_passkey_credentials
            SET sign_count = ?,
                last_used_at = ?
            WHERE id = ?
            """,
            (sign_count, _utc_now(), credential.id),
        )
        self._commit()
        return self.get_user_passkey_credential_by_id(credential.id)

    def rename_user_passkey_credential(
        self,
        user_id: int,
        passkey_id: int,
        label: str,
    ) -> UserPasskeyCredential:
        credential = self.get_user_passkey_credential_by_id(passkey_id)
        if credential.user_id != user_id:
            raise PermissionError(f"passkey credential {passkey_id} belongs to another account")
        self.connection.execute(
            """
            UPDATE user_passkey_credentials
            SET label = ?
            WHERE id = ?
            """,
            (label.strip(), passkey_id),
        )
        self._commit()
        return self.get_user_passkey_credential_by_id(passkey_id)

    def delete_user_passkey_credential(self, user_id: int, passkey_id: int) -> None:
        credential = self.get_user_passkey_credential_by_id(passkey_id)
        if credential.user_id != user_id:
            raise PermissionError(f"passkey credential {passkey_id} belongs to another account")
        self.connection.execute(
            "DELETE FROM user_passkey_credentials WHERE id = ?",
            (passkey_id,),
        )
        self._commit()
