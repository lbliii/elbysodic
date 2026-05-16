"""Character and application-status repository methods."""

from __future__ import annotations

import json
from collections import defaultdict

from elbysodic.db.repositories.base import TenantBoundaryError, _last_id, _utc_now
from elbysodic.db.repositories.identity import IdentityRepositoryMixin
from elbysodic.db.repositories.rows import (
    _character_application_event_from_row,
    _character_application_from_row,
    _character_from_row,
    _community_from_row,
)
from elbysodic.domain.models import (
    Character,
    CharacterApplication,
    CharacterApplicationEvent,
    Community,
    CommunityMembership,
)


class CharacterRepositoryMixin(IdentityRepositoryMixin):
    def create_character(
        self,
        community_id: int,
        membership_id: int,
        slug: str,
        name: str,
        avatar_url: str | None = None,
        poster_url: str | None = None,
        poster_alt: str = "",
        tagline: str = "",
        accent_color: str = "",
        summary: str = "",
        post_profile_variant: str = "bio",
        post_accent_style: str = "soft",
        post_border_style: str = "hairline",
        post_title_style: str = "standard",
        post_density: str = "calm",
        *,
        application_status: str = "accepted",
        make_default: bool = False,
    ) -> Character:
        self.get_membership(community_id, membership_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO characters (
                community_id,
                membership_id,
                slug,
                name,
                avatar_url,
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                post_accent_style,
                post_border_style,
                post_title_style,
                post_density,
                application_status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                membership_id,
                slug,
                name,
                avatar_url,
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                post_accent_style,
                post_border_style,
                post_title_style,
                post_density,
                application_status,
                now,
                now,
            ),
        )
        character = self.get_character(community_id, _last_id(cursor))
        if make_default:
            self.set_default_character(community_id, membership_id, character.id)
            character = self.get_character(community_id, character.id)
        self._commit()
        return character

    def get_character(self, community_id: int, character_id: int) -> Character:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                name,
                slug,
                avatar_url,
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                post_accent_style,
                post_border_style,
                post_title_style,
                post_density,
                application_status,
                created_at,
                updated_at
            FROM characters
            WHERE community_id = ? AND id = ?
            """,
            (community_id, character_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"character not found in community {community_id}: {character_id}")
        return _character_from_row(row)

    def list_characters_by_ids(
        self,
        community_id: int,
        character_ids: list[int],
    ) -> dict[int, Character]:
        if not character_ids:
            return {}
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                name,
                slug,
                avatar_url,
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                post_accent_style,
                post_border_style,
                post_title_style,
                post_density,
                application_status,
                created_at,
                updated_at
            FROM characters
            WHERE community_id = ?
              AND id IN (SELECT value FROM json_each(?))
            """,
            (community_id, json.dumps(character_ids)),
        ).fetchall()
        return {int(row["id"]): _character_from_row(row) for row in rows}

    def get_character_by_slug(self, community_id: int, slug: str) -> Character:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                name,
                slug,
                avatar_url,
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                post_accent_style,
                post_border_style,
                post_title_style,
                post_density,
                application_status,
                created_at,
                updated_at
            FROM characters
            WHERE community_id = ? AND slug = ?
            """,
            (community_id, slug),
        ).fetchone()
        if row is None:
            raise LookupError(f"character not found in community {community_id}: {slug}")
        return _character_from_row(row)

    def list_character_communities_by_slug(self, slug: str) -> list[Community]:
        rows = self.connection.execute(
            """
            SELECT DISTINCT
                communities.id,
                communities.name,
                communities.slug,
                communities.host,
                communities.launch_status,
                communities.default_theme_id,
                communities.identity_accent_facet_group_id,
                communities.community_mark_url,
                communities.community_mark_alt,
                communities.world_hero_image_url,
                communities.world_hero_image_alt,
                communities.world_hero_treatment,
                communities.world_hero_focal_point,
                communities.world_hero_overlay,
                communities.world_hero_height,
                communities.enabled_post_profile_variants,
                communities.enabled_post_accent_styles,
                communities.enabled_post_border_styles,
                communities.enabled_post_title_styles,
                communities.enabled_post_densities,
                communities.created_at,
                communities.updated_at
            FROM communities
            JOIN characters ON characters.community_id = communities.id
            JOIN community_memberships
              ON community_memberships.community_id = characters.community_id
             AND community_memberships.id = characters.membership_id
            WHERE characters.slug = ?
              AND community_memberships.is_active = 1
            ORDER BY communities.name, communities.id
            """,
            (slug,),
        ).fetchall()
        return [_community_from_row(row) for row in rows]

    def update_character(
        self,
        community_id: int,
        character_id: int,
        *,
        slug: str,
        name: str,
        avatar_url: str | None,
        poster_url: str | None = None,
        poster_alt: str = "",
        tagline: str = "",
        accent_color: str = "",
        summary: str = "",
        post_profile_variant: str = "bio",
        post_accent_style: str = "soft",
        post_border_style: str = "hairline",
        post_title_style: str = "standard",
        post_density: str = "calm",
    ) -> Character:
        self.get_character(community_id, character_id)
        self.connection.execute(
            """
            UPDATE characters
            SET
                slug = ?,
                name = ?,
                avatar_url = ?,
                poster_url = ?,
                poster_alt = ?,
                tagline = ?,
                accent_color = ?,
                summary = ?,
                post_profile_variant = ?,
                post_accent_style = ?,
                post_border_style = ?,
                post_title_style = ?,
                post_density = ?,
                updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (
                slug,
                name,
                avatar_url,
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                post_accent_style,
                post_border_style,
                post_title_style,
                post_density,
                _utc_now(),
                community_id,
                character_id,
            ),
        )
        self._commit()
        return self.get_character(community_id, character_id)

    def transfer_character_membership(
        self,
        community_id: int,
        character_id: int,
        membership_id: int,
        *,
        make_default: bool = False,
    ) -> Character:
        character = self.get_character(community_id, character_id)
        self.get_membership(community_id, membership_id)
        old_membership = self.get_membership(community_id, character.membership_id)
        if character.membership_id == membership_id:
            if make_default and old_membership.default_character_id != character_id:
                self.set_default_character(community_id, membership_id, character_id)
            return self.get_character(community_id, character_id)

        self.connection.execute(
            """
            UPDATE characters
            SET membership_id = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (membership_id, _utc_now(), community_id, character_id),
        )
        if old_membership.default_character_id == character_id:
            replacement = self.connection.execute(
                """
                SELECT id
                FROM characters
                WHERE community_id = ?
                  AND membership_id = ?
                  AND id != ?
                ORDER BY name, id
                LIMIT 1
                """,
                (community_id, old_membership.id, character_id),
            ).fetchone()
            self.connection.execute(
                """
                UPDATE community_memberships
                SET default_character_id = ?
                WHERE community_id = ? AND id = ?
                """,
                (
                    replacement["id"] if replacement is not None else None,
                    community_id,
                    old_membership.id,
                ),
            )
        new_membership = self.get_membership(community_id, membership_id)
        if make_default or new_membership.default_character_id is None:
            self.connection.execute(
                """
                UPDATE community_memberships
                SET default_character_id = ?
                WHERE community_id = ? AND id = ?
                """,
                (character_id, community_id, membership_id),
            )
        self._commit()
        return self.get_character(community_id, character_id)

    def update_character_application_status(
        self,
        community_id: int,
        character_id: int,
        application_status: str,
    ) -> Character:
        self.get_character(community_id, character_id)
        self.connection.execute(
            """
            UPDATE characters
            SET application_status = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (application_status, _utc_now(), community_id, character_id),
        )
        self.connection.execute(
            """
            UPDATE applications
            SET status = ?, updated_at = ?
            WHERE community_id = ? AND character_id = ?
            """,
            (application_status, _utc_now(), community_id, character_id),
        )
        self._commit()
        return self.get_character(community_id, character_id)

    def ensure_character_application(
        self,
        community_id: int,
        character_id: int,
        *,
        source_wanted_ad_id: int | None = None,
        source_wanted_ad_interest_id: int | None = None,
    ) -> CharacterApplication:
        character = self.get_character(community_id, character_id)
        if source_wanted_ad_id is not None:
            self._ensure_row_in_community("wanted_ads", community_id, source_wanted_ad_id)
        if source_wanted_ad_interest_id is not None:
            self._ensure_row_in_community(
                "wanted_ad_interests",
                community_id,
                source_wanted_ad_interest_id,
            )
        existing = self.get_character_application_for_character_or_none(
            community_id,
            character_id,
        )
        if existing is not None:
            return existing
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO applications (
                community_id,
                membership_id,
                character_id,
                source_wanted_ad_id,
                source_wanted_ad_interest_id,
                title,
                summary,
                body,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                character.membership_id,
                character.id,
                source_wanted_ad_id,
                source_wanted_ad_interest_id,
                character.name,
                character.summary,
                "",
                character.application_status,
                now,
                now,
            ),
        )
        self._commit()
        return self.get_character_application(community_id, _last_id(cursor))

    def get_character_application(
        self,
        community_id: int,
        application_id: int,
    ) -> CharacterApplication:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                character_id,
                source_wanted_ad_id,
                source_wanted_ad_interest_id,
                title,
                summary,
                body,
                status,
                revision_notes,
                staff_notes,
                checklist,
                submitted_at,
                reviewed_at,
                created_at,
                updated_at
            FROM applications
            WHERE community_id = ? AND id = ?
            """,
            (community_id, application_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"application not found in community {community_id}: {application_id}"
            )
        return _character_application_from_row(row)

    def get_character_application_for_character(
        self,
        community_id: int,
        character_id: int,
    ) -> CharacterApplication:
        application = self.get_character_application_for_character_or_none(
            community_id,
            character_id,
        )
        if application is None:
            raise LookupError(
                f"application not found in community {community_id}: character {character_id}"
            )
        return application

    def get_character_application_for_character_or_none(
        self,
        community_id: int,
        character_id: int,
    ) -> CharacterApplication | None:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                character_id,
                source_wanted_ad_id,
                source_wanted_ad_interest_id,
                title,
                summary,
                body,
                status,
                revision_notes,
                staff_notes,
                checklist,
                submitted_at,
                reviewed_at,
                created_at,
                updated_at
            FROM applications
            WHERE community_id = ? AND character_id = ?
            """,
            (community_id, character_id),
        ).fetchone()
        return _character_application_from_row(row) if row is not None else None

    def update_character_application_draft(
        self,
        community_id: int,
        application_id: int,
        *,
        title: str,
        summary: str,
        body: str,
    ) -> CharacterApplication:
        application = self.get_character_application(community_id, application_id)
        self.connection.execute(
            """
            UPDATE applications
            SET title = ?, summary = ?, body = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (title, summary, body, _utc_now(), community_id, application_id),
        )
        self.connection.execute(
            """
            UPDATE characters
            SET summary = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (summary, _utc_now(), community_id, application.character_id),
        )
        self._commit()
        return self.get_character_application(community_id, application_id)

    def update_character_application_review(
        self,
        community_id: int,
        application_id: int,
        *,
        revision_notes: str,
        staff_notes: str,
        checklist: str,
    ) -> CharacterApplication:
        self.get_character_application(community_id, application_id)
        self.connection.execute(
            """
            UPDATE applications
            SET revision_notes = ?, staff_notes = ?, checklist = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (
                revision_notes,
                staff_notes,
                checklist,
                _utc_now(),
                community_id,
                application_id,
            ),
        )
        self._commit()
        return self.get_character_application(community_id, application_id)

    def transition_character_application_status(
        self,
        community_id: int,
        application_id: int,
        *,
        status: str,
        actor_membership_id: int,
        actor_character_id: int | None,
        note: str = "",
    ) -> CharacterApplication:
        application = self.get_character_application(community_id, application_id)
        self.get_membership(community_id, actor_membership_id)
        if actor_character_id is not None:
            actor = self.get_character(community_id, actor_character_id)
            if actor.membership_id != actor_membership_id:
                raise TenantBoundaryError(
                    f"character {actor_character_id} does not belong to membership {actor_membership_id}"
                )
        now = _utc_now()
        submitted_at = now if status == "submitted" else application.submitted_at
        reviewed_at = now if status in {"accepted", "rejected", "revision_requested"} else None
        self.connection.execute(
            """
            UPDATE applications
            SET status = ?, submitted_at = ?, reviewed_at = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (status, submitted_at, reviewed_at, now, community_id, application_id),
        )
        self.connection.execute(
            """
            UPDATE characters
            SET application_status = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (status, now, community_id, application.character_id),
        )
        cursor = self.connection.execute(
            """
            INSERT INTO application_events (
                community_id,
                application_id,
                actor_membership_id,
                actor_character_id,
                from_status,
                to_status,
                note,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                application_id,
                actor_membership_id,
                actor_character_id,
                application.status,
                status,
                note,
                now,
            ),
        )
        self._commit()
        self.get_character_application_event(community_id, _last_id(cursor))
        return self.get_character_application(community_id, application_id)

    def get_character_application_event(
        self,
        community_id: int,
        event_id: int,
    ) -> CharacterApplicationEvent:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                application_id,
                actor_membership_id,
                actor_character_id,
                from_status,
                to_status,
                note,
                created_at
            FROM application_events
            WHERE community_id = ? AND id = ?
            """,
            (community_id, event_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"application event not found in community {community_id}: {event_id}"
            )
        return _character_application_event_from_row(row)

    def list_character_application_events(
        self,
        community_id: int,
        application_id: int,
    ) -> list[CharacterApplicationEvent]:
        self.get_character_application(community_id, application_id)
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                application_id,
                actor_membership_id,
                actor_character_id,
                from_status,
                to_status,
                note,
                created_at
            FROM application_events
            WHERE community_id = ? AND application_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (community_id, application_id),
        ).fetchall()
        return [_character_application_event_from_row(row) for row in rows]

    def _ensure_row_in_community(self, table: str, community_id: int, row_id: int) -> None:
        if table == "wanted_ads":
            row = self.connection.execute(
                "SELECT id FROM wanted_ads WHERE community_id = ? AND id = ?",
                (community_id, row_id),
            ).fetchone()
        elif table == "wanted_ad_interests":
            row = self.connection.execute(
                "SELECT id FROM wanted_ad_interests WHERE community_id = ? AND id = ?",
                (community_id, row_id),
            ).fetchone()
        else:
            raise ValueError(f"unknown community-scoped table: {table}")
        if row is None:
            raise LookupError(f"{table} row not found in community {community_id}: {row_id}")

    def list_characters(self, community_id: int, membership_id: int) -> list[Character]:
        self.get_membership(community_id, membership_id)
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                name,
                slug,
                avatar_url,
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                post_accent_style,
                post_border_style,
                post_title_style,
                post_density,
                application_status,
                created_at,
                updated_at
            FROM characters
            WHERE community_id = ? AND membership_id = ?
            ORDER BY name, id
            """,
            (community_id, membership_id),
        ).fetchall()
        return [_character_from_row(row) for row in rows]

    def list_characters_for_memberships(
        self,
        community_id: int,
        membership_ids: list[int],
    ) -> dict[int, list[Character]]:
        if not membership_ids:
            return {}
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                name,
                slug,
                avatar_url,
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                post_accent_style,
                post_border_style,
                post_title_style,
                post_density,
                application_status,
                created_at,
                updated_at
            FROM characters
            WHERE community_id = ?
              AND membership_id IN (SELECT value FROM json_each(?))
            ORDER BY membership_id, name, id
            """,
            (community_id, json.dumps(membership_ids)),
        ).fetchall()
        characters_by_membership: dict[int, list[Character]] = defaultdict(list)
        for row in rows:
            character = _character_from_row(row)
            characters_by_membership[character.membership_id].append(character)
        return dict(characters_by_membership)

    def list_community_characters(self, community_id: int) -> list[Character]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                name,
                slug,
                avatar_url,
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                post_accent_style,
                post_border_style,
                post_title_style,
                post_density,
                application_status,
                created_at,
                updated_at
            FROM characters
            WHERE community_id = ?
            ORDER BY name, id
            """,
            (community_id,),
        ).fetchall()
        return [_character_from_row(row) for row in rows]

    def search_characters(
        self,
        community_id: int,
        query: str,
        *,
        limit: int = 8,
        exclude_membership_ids: list[int] | None = None,
    ) -> list[Character]:
        normalized = query.strip().lower().lstrip("@")
        if not normalized:
            return []
        excluded_ids = exclude_membership_ids or []
        like = f"%{normalized}%"
        prefix = f"{normalized}%"
        fetch_limit = limit + len(excluded_ids) + 16
        rows = self.connection.execute(
            """
            SELECT
                characters.id,
                characters.community_id,
                characters.membership_id,
                characters.name,
                characters.slug,
                characters.avatar_url,
                characters.poster_url,
                characters.poster_alt,
                characters.tagline,
                characters.accent_color,
                characters.summary,
                characters.post_profile_variant,
                characters.post_accent_style,
                characters.post_border_style,
                characters.post_title_style,
                characters.post_density,
                characters.application_status,
                characters.created_at,
                characters.updated_at
            FROM characters
            JOIN community_memberships
              ON community_memberships.community_id = characters.community_id
             AND community_memberships.id = characters.membership_id
            WHERE characters.community_id = ?
              AND community_memberships.is_active = 1
              AND (
                lower(characters.slug) LIKE ?
                OR lower(characters.name) LIKE ?
              )
            ORDER BY
                CASE
                  WHEN lower(characters.slug) = ? THEN 0
                  WHEN lower(characters.slug) LIKE ? THEN 1
                  WHEN lower(characters.name) LIKE ? THEN 2
                  ELSE 3
                END,
                characters.name,
                characters.id
            LIMIT ?
            """,
            (community_id, like, like, normalized, prefix, prefix, fetch_limit),
        ).fetchall()
        excluded_id_set = set(excluded_ids)
        return [
            _character_from_row(row) for row in rows if row["membership_id"] not in excluded_id_set
        ][:limit]

    def set_default_character(
        self,
        community_id: int,
        membership_id: int,
        character_id: int,
    ) -> CommunityMembership:
        character = self.get_character(community_id, character_id)
        if character.membership_id != membership_id:
            raise LookupError(
                f"character {character_id} does not belong to membership {membership_id}"
            )
        self.connection.execute(
            """
            UPDATE community_memberships
            SET default_character_id = ?
            WHERE community_id = ? AND id = ?
            """,
            (character_id, community_id, membership_id),
        )
        self._commit()
        return self.get_membership(community_id, membership_id)
