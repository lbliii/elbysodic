"""Small ordered migration runner for SQLite database upgrades."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from elbysodic.domain.capabilities import STAFF_CAPABILITIES

CURRENT_SCHEMA_VERSION = 24
BASELINE_MIGRATION_NAME = "baseline-current-schema"


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    name: str
    apply: Callable[[sqlite3.Connection], None]


def _add_plotting_room_planning_fields(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(plotting_rooms)").fetchall()
    }
    for name, definition in {
        "notes": "TEXT NOT NULL DEFAULT ''",
        "next_step": "TEXT NOT NULL DEFAULT ''",
        "target_board_id": "INTEGER REFERENCES boards(id) ON DELETE SET NULL",
        "target_thread_id": "INTEGER REFERENCES threads(id) ON DELETE SET NULL",
    }.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE plotting_rooms ADD COLUMN {name} {definition}")
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_plotting_rooms_target_thread
        ON plotting_rooms(community_id, target_thread_id)
        """
    )


def _add_plotting_room_messages(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS plotting_room_messages (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            plotting_room_id INTEGER NOT NULL REFERENCES plotting_rooms(id) ON DELETE CASCADE,
            author_membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
            author_character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_plotting_room_messages_room
        ON plotting_room_messages(community_id, plotting_room_id, id)
        """
    )


def _add_application_review_rooms(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
            character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
            source_wanted_ad_id INTEGER REFERENCES wanted_ads(id) ON DELETE SET NULL,
            source_wanted_ad_interest_id INTEGER REFERENCES wanted_ad_interests(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft',
            revision_notes TEXT NOT NULL DEFAULT '',
            staff_notes TEXT NOT NULL DEFAULT '',
            checklist TEXT NOT NULL DEFAULT '',
            submitted_at TEXT,
            reviewed_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, character_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS application_events (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
            actor_membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
            actor_character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
            from_status TEXT,
            to_status TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_applications_status
        ON applications(community_id, status, updated_at)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_applications_membership
        ON applications(community_id, membership_id, status)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_application_events_application
        ON application_events(community_id, application_id, created_at, id)
        """
    )


def _add_realm_interactions(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS realm_interactions (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            slug TEXT NOT NULL,
            title TEXT NOT NULL,
            interaction_type TEXT NOT NULL DEFAULT 'quiz',
            placement TEXT NOT NULL DEFAULT 'general',
            summary TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'open',
            result_mode TEXT NOT NULL DEFAULT 'confirmation',
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, slug)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS realm_interaction_questions (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            interaction_id INTEGER NOT NULL REFERENCES realm_interactions(id) ON DELETE CASCADE,
            prompt TEXT NOT NULL,
            help_text TEXT NOT NULL DEFAULT '',
            question_type TEXT NOT NULL DEFAULT 'single_choice',
            is_required INTEGER NOT NULL DEFAULT 1,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS realm_interaction_options (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            question_id INTEGER NOT NULL REFERENCES realm_interaction_questions(id) ON DELETE CASCADE,
            slug TEXT NOT NULL,
            label TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            result_key TEXT NOT NULL DEFAULT '',
            score INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, question_id, slug)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS realm_interaction_responses (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            interaction_id INTEGER NOT NULL REFERENCES realm_interactions(id) ON DELETE CASCADE,
            membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
            character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, interaction_id, membership_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS realm_interaction_answers (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            response_id INTEGER NOT NULL REFERENCES realm_interaction_responses(id) ON DELETE CASCADE,
            question_id INTEGER NOT NULL REFERENCES realm_interaction_questions(id) ON DELETE CASCADE,
            option_id INTEGER REFERENCES realm_interaction_options(id) ON DELETE CASCADE,
            text_answer TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            UNIQUE (community_id, response_id, question_id)
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_realm_interactions_community
        ON realm_interactions(community_id, status, placement, sort_order, title)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_realm_interaction_questions_interaction
        ON realm_interaction_questions(community_id, interaction_id, sort_order, id)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_realm_interaction_options_question
        ON realm_interaction_options(community_id, question_id, sort_order, id)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_realm_interaction_responses_interaction
        ON realm_interaction_responses(community_id, interaction_id, updated_at)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_realm_interaction_answers_response
        ON realm_interaction_answers(community_id, response_id, question_id)
        """
    )


def _add_intake_claims(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS claim_types (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            slug TEXT NOT NULL,
            name TEXT NOT NULL,
            claim_kind TEXT NOT NULL DEFAULT 'custom',
            description TEXT NOT NULL DEFAULT '',
            visibility TEXT NOT NULL DEFAULT 'public',
            is_required INTEGER NOT NULL DEFAULT 0,
            is_exclusive INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, slug)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS character_claims (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            claim_type_id INTEGER NOT NULL REFERENCES claim_types(id) ON DELETE CASCADE,
            character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
            application_id INTEGER REFERENCES applications(id) ON DELETE SET NULL,
            source_reserve_id INTEGER REFERENCES character_reserves(id) ON DELETE SET NULL,
            value TEXT NOT NULL,
            label TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'claimed',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS application_template_fields (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            field_key TEXT NOT NULL,
            label TEXT NOT NULL,
            field_type TEXT NOT NULL DEFAULT 'text',
            help_text TEXT NOT NULL DEFAULT '',
            placeholder TEXT NOT NULL DEFAULT '',
            options_json TEXT NOT NULL DEFAULT '[]',
            maps_to_claim_type_id INTEGER REFERENCES claim_types(id) ON DELETE SET NULL,
            is_required INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, field_key)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS application_field_values (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
            field_id INTEGER NOT NULL REFERENCES application_template_fields(id) ON DELETE CASCADE,
            value TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, application_id, field_id)
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_claim_types_community
        ON claim_types(community_id, sort_order, name)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_character_claims_community
        ON character_claims(community_id, status, claim_type_id, label)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_character_claims_character
        ON character_claims(community_id, character_id, status)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_application_template_fields_community
        ON application_template_fields(community_id, sort_order, label)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_application_field_values_application
        ON application_field_values(community_id, application_id, field_id)
        """
    )


def _add_community_media_slots(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(communities)").fetchall()
    }
    for name in ("community_mark_url", "world_hero_image_url"):
        if name not in columns:
            connection.execute(f"ALTER TABLE communities ADD COLUMN {name} TEXT")
    for name in ("community_mark_alt", "world_hero_image_alt"):
        if name not in columns:
            connection.execute(
                f"ALTER TABLE communities ADD COLUMN {name} TEXT NOT NULL DEFAULT ''"
            )


def _add_user_sessions(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            expires_at TEXT,
            revoked_at TEXT
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_user_sessions_user
        ON user_sessions(user_id, revoked_at, expires_at)
        """
    )


def _add_hero_treatments(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(communities)").fetchall()
    }
    for name, default in {
        "world_hero_treatment": "split",
        "world_hero_focal_point": "center",
        "world_hero_overlay": "medium",
        "world_hero_height": "standard",
    }.items():
        if name not in columns:
            connection.execute(
                f"ALTER TABLE communities ADD COLUMN {name} TEXT NOT NULL DEFAULT '{default}'"
            )


def _add_board_media_presentation(connection: sqlite3.Connection) -> None:
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(boards)").fetchall()}
    for name, default in {
        "image_treatment": "poster",
        "image_focal_point": "center",
        "image_overlay": "medium",
    }.items():
        if name not in columns:
            connection.execute(
                f"ALTER TABLE boards ADD COLUMN {name} TEXT NOT NULL DEFAULT '{default}'"
            )


def _add_user_session_identity_selection(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(user_sessions)").fetchall()
    }
    for name, definition in {
        "selected_community_id": "INTEGER REFERENCES communities(id) ON DELETE SET NULL",
        "selected_membership_id": (
            "INTEGER REFERENCES community_memberships(id) ON DELETE SET NULL"
        ),
    }.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE user_sessions ADD COLUMN {name} {definition}")


def _add_post_public_numbers(connection: sqlite3.Connection) -> None:
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(posts)").fetchall()}
    if "post_number" not in columns:
        connection.execute("ALTER TABLE posts ADD COLUMN post_number INTEGER")

    rows = connection.execute(
        """
        SELECT id, community_id, thread_id
        FROM posts
        ORDER BY community_id, thread_id, created_at, id
        """
    ).fetchall()
    next_numbers: dict[tuple[int, int], int] = {}
    for row in rows:
        key = (int(row["community_id"]), int(row["thread_id"]))
        post_number = next_numbers.get(key, 1)
        connection.execute(
            """
            UPDATE posts
            SET post_number = ?
            WHERE community_id = ? AND id = ?
            """,
            (post_number, row["community_id"], row["id"]),
        )
        next_numbers[key] = post_number + 1

    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_thread_post_number
        ON posts(community_id, thread_id, post_number)
        """
    )


def _enforce_user_session_identity_selection(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        UPDATE user_sessions
        SET selected_community_id = NULL,
            selected_membership_id = NULL
        WHERE selected_membership_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1
                FROM community_memberships AS membership
                WHERE membership.id = user_sessions.selected_membership_id
                    AND membership.community_id = user_sessions.selected_community_id
                    AND membership.user_id = user_sessions.user_id
                    AND membership.is_active = 1
            )
        """
    )
    _create_user_session_identity_triggers(connection)


def _create_user_session_identity_triggers(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TRIGGER IF NOT EXISTS trg_user_sessions_selected_identity_insert
        BEFORE INSERT ON user_sessions
        WHEN NEW.selected_membership_id IS NOT NULL
        BEGIN
            SELECT
                CASE
                    WHEN NEW.selected_community_id IS NULL THEN
                        RAISE(ABORT, 'selected session identity requires a community')
                    WHEN NOT EXISTS (
                        SELECT 1
                        FROM community_memberships AS membership
                        WHERE membership.id = NEW.selected_membership_id
                            AND membership.community_id = NEW.selected_community_id
                            AND membership.user_id = NEW.user_id
                            AND membership.is_active = 1
                    ) THEN
                        RAISE(ABORT, 'selected session identity must match user and community')
                END;
        END;

        CREATE TRIGGER IF NOT EXISTS trg_user_sessions_selected_identity_update
        BEFORE UPDATE OF user_id, selected_community_id, selected_membership_id
        ON user_sessions
        WHEN NEW.selected_membership_id IS NOT NULL
        BEGIN
            SELECT
                CASE
                    WHEN NEW.selected_community_id IS NULL THEN
                        RAISE(ABORT, 'selected session identity requires a community')
                    WHEN NOT EXISTS (
                        SELECT 1
                        FROM community_memberships AS membership
                        WHERE membership.id = NEW.selected_membership_id
                            AND membership.community_id = NEW.selected_community_id
                            AND membership.user_id = NEW.user_id
                            AND membership.is_active = 1
                    ) THEN
                        RAISE(ABORT, 'selected session identity must match user and community')
                END;
        END;
        """
    )


def _add_command_submissions(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS command_submissions (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
            command_key TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            result_path TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            UNIQUE (community_id, membership_id, command_key, token_hash)
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_command_submissions_membership
        ON command_submissions(community_id, membership_id, created_at)
        """
    )


def _add_community_invitations(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS community_invitations (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            email TEXT NOT NULL,
            role_id INTEGER NOT NULL REFERENCES roles(id),
            invited_by_membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'pending',
            expires_at TEXT,
            accepted_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            accepted_membership_id INTEGER REFERENCES community_memberships(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL,
            accepted_at TEXT,
            revoked_at TEXT
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_community_invitations_lookup
        ON community_invitations(token_hash, status, expires_at)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_community_invitations_community
        ON community_invitations(community_id, status, created_at)
        """
    )


def _add_community_launch_status(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(communities)").fetchall()
    }
    if "launch_status" not in columns:
        connection.execute(
            "ALTER TABLE communities ADD COLUMN launch_status TEXT NOT NULL DEFAULT 'backstage'"
        )


def _add_community_discovery_profiles(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS community_discovery_profiles (
            community_id INTEGER PRIMARY KEY REFERENCES communities(id) ON DELETE CASCADE,
            premise_archetype TEXT NOT NULL DEFAULT '',
            play_engine TEXT NOT NULL DEFAULT '',
            lore_aperture TEXT NOT NULL DEFAULT '',
            access_model TEXT NOT NULL DEFAULT '',
            application_model TEXT NOT NULL DEFAULT '',
            age_rating TEXT NOT NULL DEFAULT '',
            content_rating TEXT NOT NULL DEFAULT '',
            activity_pace TEXT NOT NULL DEFAULT '',
            activity_expectation TEXT NOT NULL DEFAULT '',
            forum_adjunct TEXT NOT NULL DEFAULT '',
            roster_posture TEXT NOT NULL DEFAULT '',
            catalog_pitch TEXT NOT NULL DEFAULT '',
            onboarding_pitch TEXT NOT NULL DEFAULT '',
            staff_pick_label TEXT NOT NULL DEFAULT '',
            featured_event_material_id INTEGER REFERENCES materials(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS community_discovery_tags (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            tag_type TEXT NOT NULL,
            tag_key TEXT NOT NULL,
            label TEXT NOT NULL,
            search_text TEXT NOT NULL DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, tag_type, tag_key)
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_community_discovery_tags_community
        ON community_discovery_tags(community_id, tag_type, sort_order, id)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_community_discovery_tags_key
        ON community_discovery_tags(community_id, tag_key)
        """
    )


def _add_community_gateway_slots(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS community_gateway_slots (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            slot_type TEXT NOT NULL CHECK (
                slot_type IN ('scene_hub', 'wanted_hook', 'guidebook_material')
            ),
            target_id INTEGER NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            label TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, slot_type, target_id)
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_community_gateway_slots_order
        ON community_gateway_slots(community_id, slot_type, position, id)
        """
    )


def _add_community_access_requests(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS community_access_requests (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            email TEXT NOT NULL,
            display_name TEXT NOT NULL DEFAULT '',
            face_concept TEXT NOT NULL DEFAULT '',
            wanted_hook TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            account_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_community_access_requests_community
        ON community_access_requests(community_id, status, created_at)
        """
    )


def _add_community_access_request_invitation_link(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(community_access_requests)").fetchall()
    }
    if "invitation_id" not in columns:
        connection.execute(
            """
            ALTER TABLE community_access_requests
            ADD COLUMN invitation_id INTEGER REFERENCES community_invitations(id) ON DELETE SET NULL
            """
        )


def _add_community_access_request_events(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS community_access_request_events (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            access_request_id INTEGER NOT NULL REFERENCES community_access_requests(id) ON DELETE CASCADE,
            actor_membership_id INTEGER REFERENCES community_memberships(id) ON DELETE SET NULL,
            event_type TEXT NOT NULL,
            from_status TEXT,
            to_status TEXT NOT NULL,
            invitation_id INTEGER REFERENCES community_invitations(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_community_access_request_events_request
        ON community_access_request_events(community_id, access_request_id, created_at, id)
        """
    )


def _add_user_passkey_credentials(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS user_passkey_credentials (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            credential_id BLOB NOT NULL UNIQUE,
            public_key BLOB NOT NULL,
            sign_count INTEGER NOT NULL DEFAULT 0,
            transports TEXT NOT NULL DEFAULT '',
            label TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            last_used_at TEXT
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_user_passkey_credentials_user
        ON user_passkey_credentials(user_id, created_at, id)
        """
    )


TENANT_PAIR_RULES: tuple[tuple[str, str], ...] = (
    (
        "community_memberships",
        """
        EXISTS (
            SELECT 1 FROM roles AS role
            WHERE role.id = {row}.role_id
              AND role.community_id = {row}.community_id
        )
        AND (
            {row}.default_character_id IS NULL
            OR EXISTS (
                SELECT 1 FROM characters AS character
                WHERE character.id = {row}.default_character_id
                  AND character.community_id = {row}.community_id
                  AND character.membership_id = {row}.id
            )
        )
        """,
    ),
    (
        "role_capabilities",
        """
        EXISTS (
            SELECT 1 FROM roles AS role
            WHERE role.id = {row}.role_id
              AND role.community_id = {row}.community_id
        )
        """,
    ),
    (
        "characters",
        """
        EXISTS (
            SELECT 1 FROM community_memberships AS membership
            WHERE membership.id = {row}.membership_id
              AND membership.community_id = {row}.community_id
        )
        """,
    ),
    (
        "staff_audit_events",
        """
        EXISTS (
            SELECT 1 FROM community_memberships AS actor
            WHERE actor.id = {row}.actor_membership_id
              AND actor.community_id = {row}.community_id
        )
        AND (
            {row}.actor_character_id IS NULL
            OR EXISTS (
                SELECT 1 FROM characters AS character
                WHERE character.id = {row}.actor_character_id
                  AND character.community_id = {row}.community_id
                  AND character.membership_id = {row}.actor_membership_id
            )
        )
        """,
    ),
    (
        "command_submissions",
        """
        EXISTS (
            SELECT 1 FROM community_memberships AS membership
            WHERE membership.id = {row}.membership_id
              AND membership.community_id = {row}.community_id
        )
        """,
    ),
    (
        "community_invitations",
        """
        EXISTS (SELECT 1 FROM roles AS role WHERE role.id = {row}.role_id AND role.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM community_memberships AS inviter WHERE inviter.id = {row}.invited_by_membership_id AND inviter.community_id = {row}.community_id)
        AND ({row}.accepted_membership_id IS NULL OR EXISTS (
            SELECT 1 FROM community_memberships AS accepted
            WHERE accepted.id = {row}.accepted_membership_id
              AND accepted.community_id = {row}.community_id
              AND ({row}.accepted_user_id IS NULL OR accepted.user_id = {row}.accepted_user_id)
        ))
        """,
    ),
    (
        "community_access_requests",
        """
        {row}.invitation_id IS NULL OR EXISTS (
            SELECT 1 FROM community_invitations AS invitation
            WHERE invitation.id = {row}.invitation_id
              AND invitation.community_id = {row}.community_id
              AND ({row}.account_user_id IS NULL OR invitation.accepted_user_id IS NULL OR invitation.accepted_user_id = {row}.account_user_id)
        )
        """,
    ),
    (
        "community_access_request_events",
        """
        EXISTS (SELECT 1 FROM community_access_requests AS request WHERE request.id = {row}.access_request_id AND request.community_id = {row}.community_id)
        AND ({row}.actor_membership_id IS NULL OR EXISTS (SELECT 1 FROM community_memberships AS actor WHERE actor.id = {row}.actor_membership_id AND actor.community_id = {row}.community_id))
        AND ({row}.invitation_id IS NULL OR EXISTS (SELECT 1 FROM community_invitations AS invitation WHERE invitation.id = {row}.invitation_id AND invitation.community_id = {row}.community_id))
        """,
    ),
    (
        "community_gateway_slots",
        """
        ({row}.slot_type = 'scene_hub' AND EXISTS (SELECT 1 FROM boards AS target WHERE target.id = {row}.target_id AND target.community_id = {row}.community_id))
        OR ({row}.slot_type = 'wanted_hook' AND EXISTS (SELECT 1 FROM wanted_ads AS target WHERE target.id = {row}.target_id AND target.community_id = {row}.community_id))
        OR ({row}.slot_type = 'guidebook_material' AND EXISTS (SELECT 1 FROM materials AS target WHERE target.id = {row}.target_id AND target.community_id = {row}.community_id))
        """,
    ),
    (
        "community_discovery_profiles",
        """
        {row}.featured_event_material_id IS NULL OR EXISTS (
            SELECT 1 FROM materials AS material
            WHERE material.id = {row}.featured_event_material_id
              AND material.community_id = {row}.community_id
        )
        """,
    ),
    (
        "boards",
        """
        {row}.parent_board_id IS NULL
        OR EXISTS (
            SELECT 1 FROM boards AS parent
            WHERE parent.id = {row}.parent_board_id
              AND parent.community_id = {row}.community_id
        )
        """,
    ),
    (
        "facets",
        """
        EXISTS (SELECT 1 FROM facet_groups AS facet_group WHERE facet_group.id = {row}.facet_group_id AND facet_group.community_id = {row}.community_id)
        """,
    ),
    (
        "character_facets",
        """
        EXISTS (SELECT 1 FROM characters AS character WHERE character.id = {row}.character_id AND character.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM facets AS facet WHERE facet.id = {row}.facet_id AND facet.community_id = {row}.community_id)
        """,
    ),
    (
        "board_facets",
        """
        EXISTS (SELECT 1 FROM boards AS board WHERE board.id = {row}.board_id AND board.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM facets AS facet WHERE facet.id = {row}.facet_id AND facet.community_id = {row}.community_id)
        """,
    ),
    (
        "material_facets",
        """
        EXISTS (SELECT 1 FROM materials AS material WHERE material.id = {row}.material_id AND material.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM facets AS facet WHERE facet.id = {row}.facet_id AND facet.community_id = {row}.community_id)
        """,
    ),
    (
        "wanted_ad_facets",
        """
        EXISTS (SELECT 1 FROM wanted_ads AS wanted WHERE wanted.id = {row}.wanted_ad_id AND wanted.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM facets AS facet WHERE facet.id = {row}.facet_id AND facet.community_id = {row}.community_id)
        """,
    ),
    (
        "character_plot_hook_facets",
        """
        EXISTS (SELECT 1 FROM character_plot_hooks AS hook WHERE hook.id = {row}.plot_hook_id AND hook.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM facets AS facet WHERE facet.id = {row}.facet_id AND facet.community_id = {row}.community_id)
        """,
    ),
    (
        "thread_facets",
        """
        EXISTS (SELECT 1 FROM threads AS thread WHERE thread.id = {row}.thread_id AND thread.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM facets AS facet WHERE facet.id = {row}.facet_id AND facet.community_id = {row}.community_id)
        """,
    ),
    (
        "threads",
        """
        EXISTS (
            SELECT 1 FROM boards AS board
            WHERE board.id = {row}.board_id
              AND board.community_id = {row}.community_id
        )
        AND EXISTS (
            SELECT 1 FROM community_memberships AS membership
            WHERE membership.id = {row}.author_membership_id
              AND membership.community_id = {row}.community_id
        )
        AND EXISTS (
            SELECT 1 FROM characters AS character
            WHERE character.id = {row}.author_character_id
              AND character.community_id = {row}.community_id
              AND character.membership_id = {row}.author_membership_id
        )
        """,
    ),
    (
        "posts",
        """
        EXISTS (
            SELECT 1 FROM threads AS thread
            WHERE thread.id = {row}.thread_id
              AND thread.community_id = {row}.community_id
        )
        AND EXISTS (
            SELECT 1 FROM community_memberships AS membership
            WHERE membership.id = {row}.author_membership_id
              AND membership.community_id = {row}.community_id
        )
        AND EXISTS (
            SELECT 1 FROM characters AS character
            WHERE character.id = {row}.author_character_id
              AND character.community_id = {row}.community_id
              AND character.membership_id = {row}.author_membership_id
        )
        """,
    ),
    (
        "wanted_ads",
        """
        EXISTS (
            SELECT 1 FROM community_memberships AS membership
            WHERE membership.id = {row}.creator_membership_id
              AND membership.community_id = {row}.community_id
        )
        AND (
            {row}.creator_character_id IS NULL
            OR EXISTS (
                SELECT 1 FROM characters AS character
                WHERE character.id = {row}.creator_character_id
                  AND character.community_id = {row}.community_id
                  AND character.membership_id = {row}.creator_membership_id
            )
        )
        """,
    ),
    (
        "wanted_ad_interests",
        """
        EXISTS (
            SELECT 1 FROM wanted_ads AS wanted
            WHERE wanted.id = {row}.wanted_ad_id
              AND wanted.community_id = {row}.community_id
        )
        AND EXISTS (
            SELECT 1 FROM community_memberships AS membership
            WHERE membership.id = {row}.membership_id
              AND membership.community_id = {row}.community_id
        )
        AND (
            {row}.character_id IS NULL
            OR EXISTS (
                SELECT 1 FROM characters AS character
                WHERE character.id = {row}.character_id
                  AND character.community_id = {row}.community_id
                  AND character.membership_id = {row}.membership_id
            )
        )
        """,
    ),
    (
        "character_plot_hooks",
        """
        EXISTS (
            SELECT 1 FROM community_memberships AS membership
            WHERE membership.id = {row}.author_membership_id
              AND membership.community_id = {row}.community_id
        )
        AND EXISTS (
            SELECT 1 FROM characters AS character
            WHERE character.id = {row}.character_id
              AND character.community_id = {row}.community_id
              AND character.membership_id = {row}.author_membership_id
        )
        """,
    ),
    (
        "character_plot_hook_interests",
        """
        EXISTS (
            SELECT 1 FROM character_plot_hooks AS hook
            WHERE hook.id = {row}.plot_hook_id
              AND hook.community_id = {row}.community_id
        )
        AND EXISTS (
            SELECT 1 FROM characters AS character
            WHERE character.id = {row}.character_id
              AND character.community_id = {row}.community_id
              AND character.membership_id = {row}.membership_id
        )
        """,
    ),
    (
        "applications",
        """
        EXISTS (
            SELECT 1 FROM characters AS character
            WHERE character.id = {row}.character_id
              AND character.community_id = {row}.community_id
              AND character.membership_id = {row}.membership_id
        )
        AND (
            {row}.source_wanted_ad_id IS NULL
            OR EXISTS (
                SELECT 1 FROM wanted_ads AS wanted
                WHERE wanted.id = {row}.source_wanted_ad_id
                  AND wanted.community_id = {row}.community_id
            )
        )
        AND (
            {row}.source_wanted_ad_interest_id IS NULL
            OR EXISTS (
                SELECT 1 FROM wanted_ad_interests AS interest
                WHERE interest.id = {row}.source_wanted_ad_interest_id
                  AND interest.community_id = {row}.community_id
                  AND (
                      {row}.source_wanted_ad_id IS NULL
                      OR interest.wanted_ad_id = {row}.source_wanted_ad_id
                  )
            )
        )
        """,
    ),
    (
        "application_template_fields",
        """
        {row}.maps_to_claim_type_id IS NULL OR EXISTS (
            SELECT 1 FROM claim_types AS claim_type
            WHERE claim_type.id = {row}.maps_to_claim_type_id
              AND claim_type.community_id = {row}.community_id
        )
        """,
    ),
    (
        "application_field_values",
        """
        EXISTS (SELECT 1 FROM applications AS application WHERE application.id = {row}.application_id AND application.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM application_template_fields AS field WHERE field.id = {row}.field_id AND field.community_id = {row}.community_id)
        """,
    ),
    (
        "application_events",
        """
        EXISTS (
            SELECT 1 FROM applications AS application
            WHERE application.id = {row}.application_id
              AND application.community_id = {row}.community_id
        )
        AND EXISTS (
            SELECT 1 FROM community_memberships AS membership
            WHERE membership.id = {row}.actor_membership_id
              AND membership.community_id = {row}.community_id
        )
        AND (
            {row}.actor_character_id IS NULL
            OR EXISTS (
                SELECT 1 FROM characters AS character
                WHERE character.id = {row}.actor_character_id
                  AND character.community_id = {row}.community_id
                  AND character.membership_id = {row}.actor_membership_id
            )
        )
        """,
    ),
    (
        "character_reserves",
        """
        EXISTS (
            SELECT 1 FROM characters AS character
            WHERE character.id = {row}.character_id
              AND character.community_id = {row}.community_id
              AND character.membership_id = {row}.membership_id
        )
        AND (
            {row}.wanted_ad_id IS NULL
            OR EXISTS (
                SELECT 1 FROM wanted_ads AS wanted
                WHERE wanted.id = {row}.wanted_ad_id
                  AND wanted.community_id = {row}.community_id
            )
        )
        AND (
            {row}.wanted_ad_interest_id IS NULL
            OR EXISTS (
                SELECT 1 FROM wanted_ad_interests AS interest
                WHERE interest.id = {row}.wanted_ad_interest_id
                  AND interest.community_id = {row}.community_id
                  AND interest.membership_id = {row}.membership_id
                  AND (
                      {row}.wanted_ad_id IS NULL
                      OR interest.wanted_ad_id = {row}.wanted_ad_id
                  )
            )
        )
        """,
    ),
    (
        "wanted_ad_related_characters",
        """
        EXISTS (SELECT 1 FROM wanted_ads AS wanted WHERE wanted.id = {row}.wanted_ad_id AND wanted.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM characters AS character WHERE character.id = {row}.character_id AND character.community_id = {row}.community_id)
        """,
    ),
    (
        "character_claims",
        """
        EXISTS (
            SELECT 1 FROM claim_types AS claim_type
            WHERE claim_type.id = {row}.claim_type_id
              AND claim_type.community_id = {row}.community_id
        )
        AND (
            {row}.character_id IS NULL
            OR EXISTS (
                SELECT 1 FROM characters AS character
                WHERE character.id = {row}.character_id
                  AND character.community_id = {row}.community_id
            )
        )
        AND (
            {row}.application_id IS NULL
            OR EXISTS (
                SELECT 1 FROM applications AS application
                WHERE application.id = {row}.application_id
                  AND application.community_id = {row}.community_id
                  AND ({row}.character_id IS NULL OR application.character_id = {row}.character_id)
            )
        )
        AND (
            {row}.source_reserve_id IS NULL
            OR EXISTS (
                SELECT 1 FROM character_reserves AS reserve
                WHERE reserve.id = {row}.source_reserve_id
                  AND reserve.community_id = {row}.community_id
                  AND ({row}.character_id IS NULL OR reserve.character_id = {row}.character_id)
            )
        )
        """,
    ),
    (
        "plotting_rooms",
        """
        EXISTS (
            SELECT 1 FROM community_memberships AS membership
            WHERE membership.id = {row}.owner_membership_id
              AND membership.community_id = {row}.community_id
        )
        AND ({row}.source_plot_hook_id IS NULL OR EXISTS (
            SELECT 1 FROM character_plot_hooks AS hook
            WHERE hook.id = {row}.source_plot_hook_id
              AND hook.community_id = {row}.community_id
        ))
        AND ({row}.source_plot_hook_interest_id IS NULL OR EXISTS (
            SELECT 1 FROM character_plot_hook_interests AS interest
            WHERE interest.id = {row}.source_plot_hook_interest_id
              AND interest.community_id = {row}.community_id
              AND ({row}.source_plot_hook_id IS NULL OR interest.plot_hook_id = {row}.source_plot_hook_id)
        ))
        AND ({row}.source_wanted_ad_id IS NULL OR EXISTS (
            SELECT 1 FROM wanted_ads AS wanted
            WHERE wanted.id = {row}.source_wanted_ad_id
              AND wanted.community_id = {row}.community_id
        ))
        AND ({row}.source_wanted_ad_interest_id IS NULL OR EXISTS (
            SELECT 1 FROM wanted_ad_interests AS interest
            WHERE interest.id = {row}.source_wanted_ad_interest_id
              AND interest.community_id = {row}.community_id
              AND ({row}.source_wanted_ad_id IS NULL OR interest.wanted_ad_id = {row}.source_wanted_ad_id)
        ))
        AND ({row}.target_board_id IS NULL OR EXISTS (
            SELECT 1 FROM boards AS board
            WHERE board.id = {row}.target_board_id
              AND board.community_id = {row}.community_id
        ))
        AND ({row}.target_thread_id IS NULL OR EXISTS (
            SELECT 1 FROM threads AS thread
            WHERE thread.id = {row}.target_thread_id
              AND thread.community_id = {row}.community_id
              AND ({row}.target_board_id IS NULL OR thread.board_id = {row}.target_board_id)
        ))
        """,
    ),
    (
        "plotting_room_participants",
        """
        EXISTS (
            SELECT 1 FROM plotting_rooms AS room
            WHERE room.id = {row}.plotting_room_id
              AND room.community_id = {row}.community_id
        )
        AND EXISTS (
            SELECT 1 FROM community_memberships AS membership
            WHERE membership.id = {row}.membership_id
              AND membership.community_id = {row}.community_id
        )
        AND ({row}.character_id IS NULL OR EXISTS (
            SELECT 1 FROM characters AS character
            WHERE character.id = {row}.character_id
              AND character.community_id = {row}.community_id
              AND character.membership_id = {row}.membership_id
        ))
        """,
    ),
    (
        "plotting_room_messages",
        """
        EXISTS (
            SELECT 1 FROM plotting_rooms AS room
            WHERE room.id = {row}.plotting_room_id
              AND room.community_id = {row}.community_id
        )
        AND EXISTS (
            SELECT 1 FROM community_memberships AS membership
            WHERE membership.id = {row}.author_membership_id
              AND membership.community_id = {row}.community_id
        )
        AND ({row}.author_character_id IS NULL OR EXISTS (
            SELECT 1 FROM characters AS character
            WHERE character.id = {row}.author_character_id
              AND character.community_id = {row}.community_id
              AND character.membership_id = {row}.author_membership_id
        ))
        """,
    ),
    (
        "thread_participants",
        """
        EXISTS (SELECT 1 FROM threads AS thread WHERE thread.id = {row}.thread_id AND thread.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM characters AS character WHERE character.id = {row}.character_id AND character.community_id = {row}.community_id)
        """,
    ),
    (
        "post_revisions",
        """
        EXISTS (SELECT 1 FROM posts AS post WHERE post.id = {row}.post_id AND post.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM community_memberships AS editor WHERE editor.id = {row}.editor_membership_id AND editor.community_id = {row}.community_id)
        """,
    ),
    (
        "realm_interaction_questions",
        """
        EXISTS (SELECT 1 FROM realm_interactions AS interaction WHERE interaction.id = {row}.interaction_id AND interaction.community_id = {row}.community_id)
        """,
    ),
    (
        "realm_interaction_options",
        """
        EXISTS (SELECT 1 FROM realm_interaction_questions AS question WHERE question.id = {row}.question_id AND question.community_id = {row}.community_id)
        """,
    ),
    (
        "realm_interaction_responses",
        """
        EXISTS (SELECT 1 FROM realm_interactions AS interaction WHERE interaction.id = {row}.interaction_id AND interaction.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM community_memberships AS membership WHERE membership.id = {row}.membership_id AND membership.community_id = {row}.community_id)
        AND ({row}.character_id IS NULL OR EXISTS (SELECT 1 FROM characters AS character WHERE character.id = {row}.character_id AND character.community_id = {row}.community_id AND character.membership_id = {row}.membership_id))
        """,
    ),
    (
        "realm_interaction_answers",
        """
        EXISTS (
            SELECT 1 FROM realm_interaction_responses AS response
            JOIN realm_interaction_questions AS question ON question.id = {row}.question_id
            WHERE response.id = {row}.response_id
              AND response.community_id = {row}.community_id
              AND question.community_id = {row}.community_id
              AND question.interaction_id = response.interaction_id
        )
        AND ({row}.option_id IS NULL OR EXISTS (SELECT 1 FROM realm_interaction_options AS option WHERE option.id = {row}.option_id AND option.community_id = {row}.community_id AND option.question_id = {row}.question_id))
        """,
    ),
    (
        "reactions",
        """
        EXISTS (SELECT 1 FROM posts AS post WHERE post.id = {row}.post_id AND post.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM community_memberships AS membership WHERE membership.id = {row}.membership_id AND membership.community_id = {row}.community_id)
        """,
    ),
    (
        "thread_reads",
        """
        EXISTS (SELECT 1 FROM threads AS thread WHERE thread.id = {row}.thread_id AND thread.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM community_memberships AS membership WHERE membership.id = {row}.membership_id AND membership.community_id = {row}.community_id)
        """,
    ),
    (
        "thread_watches",
        """
        EXISTS (SELECT 1 FROM threads AS thread WHERE thread.id = {row}.thread_id AND thread.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM community_memberships AS membership WHERE membership.id = {row}.membership_id AND membership.community_id = {row}.community_id)
        """,
    ),
    (
        "notifications",
        """
        EXISTS (SELECT 1 FROM community_memberships AS membership WHERE membership.id = {row}.membership_id AND membership.community_id = {row}.community_id)
        AND EXISTS (SELECT 1 FROM community_memberships AS actor WHERE actor.id = {row}.actor_membership_id AND actor.community_id = {row}.community_id)
        AND ({row}.thread_id IS NULL OR EXISTS (SELECT 1 FROM threads AS thread WHERE thread.id = {row}.thread_id AND thread.community_id = {row}.community_id))
        AND ({row}.post_id IS NULL OR EXISTS (SELECT 1 FROM posts AS post WHERE post.id = {row}.post_id AND post.community_id = {row}.community_id AND ({row}.thread_id IS NULL OR post.thread_id = {row}.thread_id)))
        AND ({row}.wanted_ad_id IS NULL OR EXISTS (SELECT 1 FROM wanted_ads AS wanted WHERE wanted.id = {row}.wanted_ad_id AND wanted.community_id = {row}.community_id))
        AND ({row}.wanted_ad_interest_id IS NULL OR EXISTS (SELECT 1 FROM wanted_ad_interests AS interest WHERE interest.id = {row}.wanted_ad_interest_id AND interest.community_id = {row}.community_id AND ({row}.wanted_ad_id IS NULL OR interest.wanted_ad_id = {row}.wanted_ad_id)))
        AND ({row}.character_plot_hook_id IS NULL OR EXISTS (SELECT 1 FROM character_plot_hooks AS hook WHERE hook.id = {row}.character_plot_hook_id AND hook.community_id = {row}.community_id))
        AND ({row}.plotting_room_id IS NULL OR EXISTS (SELECT 1 FROM plotting_rooms AS room WHERE room.id = {row}.plotting_room_id AND room.community_id = {row}.community_id))
        AND ({row}.character_id IS NULL OR EXISTS (SELECT 1 FROM characters AS character WHERE character.id = {row}.character_id AND character.community_id = {row}.community_id))
        AND ({row}.actor_character_id IS NULL OR EXISTS (SELECT 1 FROM characters AS character WHERE character.id = {row}.actor_character_id AND character.community_id = {row}.community_id AND character.membership_id = {row}.actor_membership_id))
        """,
    ),
)

COMMUNITY_TENANT_PAIR_PREDICATE = """
({row}.default_theme_id IS NULL OR EXISTS (
    SELECT 1 FROM themes AS theme
    WHERE theme.id = {row}.default_theme_id
      AND theme.community_id = {row}.id
))
AND ({row}.identity_accent_facet_group_id IS NULL OR EXISTS (
    SELECT 1 FROM facet_groups AS facet_group
    WHERE facet_group.id = {row}.identity_accent_facet_group_id
      AND facet_group.community_id = {row}.id
))
"""


def ensure_tenant_pair_triggers(connection: sqlite3.Connection) -> None:
    """Install storage guards for acceptance-critical tenant pairings."""

    for table, predicate_template in TENANT_PAIR_RULES:
        predicate = " ".join(predicate_template.format(row="NEW").split())
        message = f"tenant pair constraint failed: {table}"
        connection.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS trg_{table}_tenant_pair_insert
            BEFORE INSERT ON {table}
            WHEN NOT ({predicate})
            BEGIN
                SELECT RAISE(ABORT, '{message}');
            END
            """
        )
        connection.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS trg_{table}_tenant_pair_update
            BEFORE UPDATE ON {table}
            WHEN NEW.community_id != OLD.community_id OR NOT ({predicate})
            BEGIN
                SELECT RAISE(ABORT, '{message}');
            END
            """
        )
    community_predicate = " ".join(COMMUNITY_TENANT_PAIR_PREDICATE.format(row="NEW").split())
    connection.execute(
        f"""
        CREATE TRIGGER IF NOT EXISTS trg_communities_tenant_pair_update
        BEFORE UPDATE ON communities
        WHEN NEW.id != OLD.id OR NOT ({community_predicate})
        BEGIN
            SELECT RAISE(ABORT, 'tenant pair constraint failed: communities');
        END
        """
    )


def _enforce_tenant_pair_constraints(connection: sqlite3.Connection) -> None:
    for table, predicate_template in TENANT_PAIR_RULES:
        predicate = " ".join(predicate_template.format(row="candidate").split())
        # Both fragments come from the closed, code-owned rule tuple above; no
        # runtime or operator input can reach this migration query.
        query = (
            f"SELECT candidate.rowid AS row_id FROM {table} AS candidate "  # noqa: S608
            f"WHERE NOT ({predicate}) LIMIT 1"
        )
        invalid = connection.execute(query).fetchone()
        if invalid is not None:
            raise sqlite3.IntegrityError(
                "tenant pair migration blocked: "
                f"{table} row {invalid['row_id']} requires repair; run the tenant integrity audit"
            )
    community_predicate = " ".join(COMMUNITY_TENANT_PAIR_PREDICATE.format(row="candidate").split())
    # The predicate is a code-owned constant, not runtime or operator input.
    community_query = (
        "SELECT candidate.rowid AS row_id FROM communities AS candidate "  # noqa: S608
        f"WHERE NOT ({community_predicate}) LIMIT 1"
    )
    invalid_community = connection.execute(community_query).fetchone()
    if invalid_community is not None:
        raise sqlite3.IntegrityError(
            "tenant pair migration blocked: "
            f"communities row {invalid_community['row_id']} requires repair; "
            "run the tenant integrity audit"
        )
    ensure_tenant_pair_triggers(connection)


def _add_role_capabilities_and_staff_audit_events(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS role_capabilities (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            capability TEXT NOT NULL CHECK (capability IN (
                'manage_applications',
                'manage_casting',
                'manage_navigation',
                'manage_threads',
                'manage_world'
            )),
            created_at TEXT NOT NULL,
            UNIQUE (community_id, role_id, capability)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS staff_audit_events (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            actor_membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
            actor_character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
            capability TEXT NOT NULL CHECK (capability IN (
                'manage_applications',
                'manage_casting',
                'manage_navigation',
                'manage_threads',
                'manage_world'
            )),
            target_family TEXT NOT NULL CHECK (length(trim(target_family)) > 0),
            target_id INTEGER,
            action TEXT NOT NULL CHECK (length(trim(action)) > 0),
            outcome TEXT NOT NULL CHECK (outcome IN ('accepted', 'rejected', 'failed')),
            reason TEXT NOT NULL DEFAULT '',
            public_aftermath TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_role_capabilities_role
        ON role_capabilities(community_id, role_id, capability)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_staff_audit_events_community
        ON staff_audit_events(community_id, created_at, id)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_staff_audit_events_actor
        ON staff_audit_events(community_id, actor_membership_id, created_at, id)
        """
    )
    now = datetime.now(UTC).isoformat(timespec="seconds")
    for capability in sorted(STAFF_CAPABILITIES):
        connection.execute(
            """
            INSERT OR IGNORE INTO role_capabilities (
                community_id, role_id, capability, created_at
            )
            SELECT community_id, id, ?, ?
            FROM roles
            WHERE is_admin = 1
            """,
            (capability, now),
        )


MIGRATIONS: tuple[Migration, ...] = (
    Migration(2, "plotting-room-planning-fields", _add_plotting_room_planning_fields),
    Migration(3, "plotting-room-messages", _add_plotting_room_messages),
    Migration(4, "application-review-rooms", _add_application_review_rooms),
    Migration(5, "realm-interactions", _add_realm_interactions),
    Migration(6, "intake-claims", _add_intake_claims),
    Migration(7, "community-media-slots", _add_community_media_slots),
    Migration(8, "user-sessions", _add_user_sessions),
    Migration(9, "hero-treatments", _add_hero_treatments),
    Migration(10, "board-media-presentation", _add_board_media_presentation),
    Migration(11, "user-session-identity-selection", _add_user_session_identity_selection),
    Migration(12, "post-public-numbers", _add_post_public_numbers),
    Migration(
        13,
        "enforce-user-session-identity-selection",
        _enforce_user_session_identity_selection,
    ),
    Migration(14, "command-submissions", _add_command_submissions),
    Migration(15, "community-invitations", _add_community_invitations),
    Migration(16, "community-launch-status", _add_community_launch_status),
    Migration(17, "community-discovery-profiles", _add_community_discovery_profiles),
    Migration(18, "community-gateway-slots", _add_community_gateway_slots),
    Migration(19, "community-access-requests", _add_community_access_requests),
    Migration(
        20,
        "community-access-request-invitation-link",
        _add_community_access_request_invitation_link,
    ),
    Migration(21, "community-access-request-events", _add_community_access_request_events),
    Migration(22, "user-passkey-credentials", _add_user_passkey_credentials),
    Migration(23, "tenant-pair-storage-constraints", _enforce_tenant_pair_constraints),
    Migration(
        24,
        "role-capabilities-and-staff-audit-events",
        _add_role_capabilities_and_staff_audit_events,
    ),
)


def apply_migrations(connection: sqlite3.Connection) -> None:
    """Record the current schema baseline and apply future ordered migrations."""

    _ensure_migration_table(connection)
    applied_versions = _applied_versions(connection)
    if not applied_versions:
        _record_migration(connection, CURRENT_SCHEMA_VERSION, BASELINE_MIGRATION_NAME)
        applied_versions.update(migration.version for migration in MIGRATIONS)
        applied_versions.add(CURRENT_SCHEMA_VERSION)

    baseline_version = max(applied_versions)
    for migration in sorted(MIGRATIONS, key=lambda item: item.version):
        if migration.version in applied_versions or migration.version <= baseline_version:
            continue
        migration.apply(connection)
        _record_migration(connection, migration.version, migration.name)
        applied_versions.add(migration.version)

    connection.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")


def _ensure_migration_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )


def _applied_versions(connection: sqlite3.Connection) -> set[int]:
    rows = connection.execute("SELECT version FROM schema_migrations").fetchall()
    return {int(row["version"]) for row in rows}


def _record_migration(connection: sqlite3.Connection, version: int, name: str) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO schema_migrations (version, name, applied_at)
        VALUES (?, ?, ?)
        """,
        (version, name, datetime.now(UTC).isoformat(timespec="seconds")),
    )
