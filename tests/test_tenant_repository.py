from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from secrets import token_hex

import pytest

from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.db.migrations import (
    BASELINE_MIGRATION_NAME,
    CURRENT_SCHEMA_VERSION,
    MIGRATIONS,
)
from elbysodic.db.repositories.base import TenantBoundaryError
from elbysodic.db.repositories.discovery import DiscoveryTagInput


@pytest.fixture
def repo() -> ForumRepository:
    connection = connect()
    create_schema(connection)
    repository = ForumRepository(connection)
    repository.seed_default_community()
    return repository


def test_boards_are_scoped_by_community(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")

    repo.create_board(default.id, "announcements", "Announcements")
    repo.create_board(hosted.id, "announcements", "Hosted Announcements")

    assert [board.name for board in repo.list_boards(default.id)] == ["Announcements"]
    assert [board.name for board in repo.list_boards(hosted.id)] == ["Hosted Announcements"]


def test_schema_records_migration_baseline() -> None:
    connection = connect()

    create_schema(connection)
    create_schema(connection)

    rows = connection.execute(
        "SELECT version, name FROM schema_migrations ORDER BY version"
    ).fetchall()
    user_version = connection.execute("PRAGMA user_version").fetchone()[0]

    assert [dict(row) for row in rows] == [
        {
            "version": CURRENT_SCHEMA_VERSION,
            "name": BASELINE_MIGRATION_NAME,
        }
    ]
    assert user_version == CURRENT_SCHEMA_VERSION


def test_schema_migration_versions_are_contiguous_after_baseline() -> None:
    versions = [migration.version for migration in MIGRATIONS]

    assert versions == list(range(2, CURRENT_SCHEMA_VERSION + 1))
    assert len({migration.name for migration in MIGRATIONS}) == len(MIGRATIONS)


def test_schema_enforces_selected_session_identity_pair(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted-session-pair", "Hosted Session Pair")
    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    user = repo.create_user("session-pair@example.com", "hash")
    other_user = repo.create_user("other-session-pair@example.com", "hash")
    default_membership = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "session-pair",
        "Session Pair",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "session-pair",
        "Session Pair",
    )
    other_membership = repo.create_membership(
        hosted.id,
        other_user.id,
        hosted_role.id,
        "other-session-pair",
        "Other Session Pair",
    )
    session = repo.create_user_session(
        user.id,
        "session-pair-token",
        expires_at="2026-06-01T00:00:00+00:00",
    )

    repo.connection.execute(
        """
        UPDATE user_sessions
        SET selected_community_id = ?,
            selected_membership_id = ?
        WHERE id = ?
        """,
        (hosted.id, hosted_membership.id, session.id),
    )

    with pytest.raises(sqlite3.IntegrityError, match="selected session identity"):
        repo.connection.execute(
            """
            UPDATE user_sessions
            SET selected_community_id = ?,
                selected_membership_id = ?
            WHERE id = ?
            """,
            (hosted.id, default_membership.id, session.id),
        )

    with pytest.raises(sqlite3.IntegrityError, match="selected session identity"):
        repo.connection.execute(
            """
            UPDATE user_sessions
            SET selected_community_id = ?,
                selected_membership_id = ?
            WHERE id = ?
            """,
            (hosted.id, other_membership.id, session.id),
        )


def test_schema_applies_ordered_migrations_from_historical_baseline() -> None:
    connection = connect()
    create_schema(connection)
    connection.execute("DELETE FROM schema_migrations")
    connection.execute(
        """
        INSERT INTO schema_migrations (version, name, applied_at)
        VALUES (1, ?, '2026-01-01T00:00:00+00:00')
        """,
        (BASELINE_MIGRATION_NAME,),
    )
    connection.execute("PRAGMA user_version = 1")
    connection.commit()

    create_schema(connection)

    rows = connection.execute(
        "SELECT version, name FROM schema_migrations ORDER BY version"
    ).fetchall()
    user_version = connection.execute("PRAGMA user_version").fetchone()[0]

    assert [row["version"] for row in rows] == list(range(1, CURRENT_SCHEMA_VERSION + 1))
    assert [row["name"] for row in rows][1:] == [migration.name for migration in MIGRATIONS]
    assert user_version == CURRENT_SCHEMA_VERSION


def test_fresh_schema_indexes_match_ordered_migration_indexes() -> None:
    fresh = connect()
    create_schema(fresh)

    upgraded = connect()
    create_schema(upgraded)
    upgraded.execute("DROP INDEX IF EXISTS idx_user_sessions_user")
    upgraded.execute("DELETE FROM schema_migrations")
    upgraded.execute(
        """
        INSERT INTO schema_migrations (version, name, applied_at)
        VALUES (1, ?, '2026-01-01T00:00:00+00:00')
        """,
        (BASELINE_MIGRATION_NAME,),
    )
    upgraded.execute("PRAGMA user_version = 1")
    upgraded.commit()
    create_schema(upgraded)

    assert _index_names(fresh) == _index_names(upgraded)


def _index_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'index'
            AND name NOT LIKE 'sqlite_autoindex_%'
        ORDER BY name
        """
    ).fetchall()
    return {row["name"] for row in rows}


def test_schema_migrates_community_invitations_from_version_14() -> None:
    connection = connect()
    create_schema(connection)
    connection.execute("DROP INDEX IF EXISTS idx_community_invitations_lookup")
    connection.execute("DROP INDEX IF EXISTS idx_community_invitations_community")
    connection.execute("DROP TABLE IF EXISTS community_invitations")
    connection.execute("DELETE FROM schema_migrations")
    connection.execute(
        """
        INSERT INTO schema_migrations (version, name, applied_at)
        VALUES (14, 'command-submissions', '2026-01-01T00:00:00+00:00')
        """
    )
    connection.execute("PRAGMA user_version = 14")
    connection.commit()

    create_schema(connection)

    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(community_invitations)").fetchall()
    }
    indexes = _index_names(connection)
    migration = connection.execute(
        """
        SELECT name
        FROM schema_migrations
        WHERE version = 15
        """
    ).fetchone()

    assert {
        "community_id",
        "email",
        "role_id",
        "invited_by_membership_id",
        "token_hash",
        "status",
        "expires_at",
        "accepted_user_id",
        "accepted_membership_id",
    }.issubset(columns)
    assert "idx_community_invitations_lookup" in indexes
    assert "idx_community_invitations_community" in indexes
    assert migration["name"] == "community-invitations"


def test_schema_migrates_community_launch_status_from_version_15() -> None:
    connection = connect()
    connection.execute(
        """
        CREATE TABLE communities (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            host TEXT UNIQUE,
            default_theme_id INTEGER,
            identity_accent_facet_group_id INTEGER,
            community_mark_url TEXT,
            community_mark_alt TEXT NOT NULL DEFAULT '',
            world_hero_image_url TEXT,
            world_hero_image_alt TEXT NOT NULL DEFAULT '',
            world_hero_treatment TEXT NOT NULL DEFAULT 'split',
            world_hero_focal_point TEXT NOT NULL DEFAULT 'center',
            world_hero_overlay TEXT NOT NULL DEFAULT 'medium',
            world_hero_height TEXT NOT NULL DEFAULT 'standard',
            enabled_post_profile_variants TEXT NOT NULL DEFAULT '',
            enabled_post_accent_styles TEXT NOT NULL DEFAULT '',
            enabled_post_border_styles TEXT NOT NULL DEFAULT '',
            enabled_post_title_styles TEXT NOT NULL DEFAULT '',
            enabled_post_densities TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        INSERT INTO communities (
            id, name, slug, host, created_at, updated_at
        )
        VALUES (1, 'Historical Realm', 'historical-realm', NULL, '2026-01-01', '2026-01-01')
        """
    )
    connection.execute(
        """
        CREATE TABLE schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        INSERT INTO schema_migrations (version, name, applied_at)
        VALUES (15, 'community-invitations', '2026-01-01T00:00:00+00:00')
        """
    )
    connection.execute("PRAGMA user_version = 15")
    connection.commit()

    create_schema(connection)

    columns = {
        row["name"]: row for row in connection.execute("PRAGMA table_info(communities)").fetchall()
    }
    migration = connection.execute(
        """
        SELECT name
        FROM schema_migrations
        WHERE version = 16
        """
    ).fetchone()
    repo = ForumRepository(connection)

    assert columns["launch_status"]["notnull"] == 1
    assert repo.get_community(1).launch_status == "backstage"
    assert migration["name"] == "community-launch-status"


def test_schema_migrates_community_discovery_profiles_from_version_16() -> None:
    connection = connect()
    create_schema(connection)
    connection.execute("DROP INDEX IF EXISTS idx_community_discovery_tags_community")
    connection.execute("DROP INDEX IF EXISTS idx_community_discovery_tags_key")
    connection.execute("DROP TABLE IF EXISTS community_discovery_tags")
    connection.execute("DROP TABLE IF EXISTS community_discovery_profiles")
    connection.execute("DELETE FROM schema_migrations")
    connection.execute(
        """
        INSERT INTO schema_migrations (version, name, applied_at)
        VALUES (16, 'community-launch-status', '2026-01-01T00:00:00+00:00')
        """
    )
    connection.execute("PRAGMA user_version = 16")
    connection.commit()

    create_schema(connection)

    profile_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(community_discovery_profiles)").fetchall()
    }
    tag_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(community_discovery_tags)").fetchall()
    }
    migration = connection.execute(
        """
        SELECT name
        FROM schema_migrations
        WHERE version = 17
        """
    ).fetchone()
    indexes = _index_names(connection)

    assert {
        "community_id",
        "premise_archetype",
        "play_engine",
        "lore_aperture",
        "access_model",
        "application_model",
        "age_rating",
        "content_rating",
        "activity_pace",
        "activity_expectation",
        "forum_adjunct",
        "roster_posture",
        "catalog_pitch",
        "onboarding_pitch",
        "staff_pick_label",
        "featured_event_material_id",
    }.issubset(profile_columns)
    assert {"community_id", "tag_type", "tag_key", "label", "search_text"}.issubset(tag_columns)
    assert "idx_community_discovery_tags_community" in indexes
    assert "idx_community_discovery_tags_key" in indexes
    assert migration["name"] == "community-discovery-profiles"


def test_schema_migrates_community_gateway_slots_from_version_17() -> None:
    connection = connect()
    create_schema(connection)
    connection.execute("DROP INDEX IF EXISTS idx_community_gateway_slots_order")
    connection.execute("DROP TABLE IF EXISTS community_gateway_slots")
    connection.execute("DELETE FROM schema_migrations")
    connection.execute(
        """
        INSERT INTO schema_migrations (version, name, applied_at)
        VALUES (17, 'community-discovery-profiles', '2026-01-01T00:00:00+00:00')
        """
    )
    connection.execute("PRAGMA user_version = 17")
    connection.commit()

    create_schema(connection)

    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(community_gateway_slots)").fetchall()
    }
    migration = connection.execute(
        """
        SELECT name
        FROM schema_migrations
        WHERE version = 18
        """
    ).fetchone()
    indexes = _index_names(connection)

    assert {
        "id",
        "community_id",
        "slot_type",
        "target_id",
        "position",
        "label",
        "created_at",
        "updated_at",
    }.issubset(columns)
    assert "idx_community_gateway_slots_order" in indexes
    assert migration["name"] == "community-gateway-slots"


def test_schema_migrates_community_access_requests_from_version_18() -> None:
    connection = connect()
    create_schema(connection)
    connection.execute("DROP INDEX IF EXISTS idx_community_access_requests_community")
    connection.execute("DROP TABLE IF EXISTS community_access_requests")
    connection.execute("DELETE FROM schema_migrations")
    connection.execute(
        """
        INSERT INTO schema_migrations (version, name, applied_at)
        VALUES (18, 'community-gateway-slots', '2026-01-01T00:00:00+00:00')
        """
    )
    connection.execute("PRAGMA user_version = 18")
    connection.commit()

    create_schema(connection)

    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(community_access_requests)").fetchall()
    }
    migration = connection.execute(
        """
        SELECT name
        FROM schema_migrations
        WHERE version = 19
        """
    ).fetchone()
    indexes = _index_names(connection)

    assert {
        "id",
        "community_id",
        "email",
        "display_name",
        "face_concept",
        "wanted_hook",
        "notes",
        "account_user_id",
        "invitation_id",
        "status",
        "created_at",
        "updated_at",
    }.issubset(columns)
    assert "idx_community_access_requests_community" in indexes
    assert migration["name"] == "community-access-requests"


def test_schema_migrates_community_access_request_invitation_link_from_version_19() -> None:
    connection = connect()
    create_schema(connection)
    connection.execute("DELETE FROM schema_migrations")
    connection.execute(
        """
        INSERT INTO schema_migrations (version, name, applied_at)
        VALUES (19, 'community-access-requests', '2026-01-01T00:00:00+00:00')
        """
    )
    connection.execute("PRAGMA user_version = 19")
    connection.execute(
        """
        CREATE TABLE legacy_access_requests AS
        SELECT id, community_id, email, display_name, face_concept, wanted_hook,
               notes, account_user_id, status, created_at, updated_at
        FROM community_access_requests
        """
    )
    connection.execute("DROP TABLE community_access_requests")
    connection.execute("ALTER TABLE legacy_access_requests RENAME TO community_access_requests")
    connection.commit()

    create_schema(connection)

    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(community_access_requests)").fetchall()
    }
    migration = connection.execute(
        """
        SELECT name
        FROM schema_migrations
        WHERE version = 20
        """
    ).fetchone()

    assert "invitation_id" in columns
    assert migration["name"] == "community-access-request-invitation-link"


def test_schema_migrates_community_access_request_events_from_version_20() -> None:
    connection = connect()
    create_schema(connection)
    connection.execute("DROP TABLE community_access_request_events")
    connection.execute("DELETE FROM schema_migrations")
    connection.execute(
        """
        INSERT INTO schema_migrations (version, name, applied_at)
        VALUES (
            20,
            'community-access-request-invitation-link',
            '2026-01-01T00:00:00+00:00'
        )
        """
    )
    connection.execute("PRAGMA user_version = 20")
    connection.commit()

    create_schema(connection)

    columns = {
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(community_access_request_events)"
        ).fetchall()
    }
    indexes = _index_names(connection)
    migration = connection.execute(
        """
        SELECT name
        FROM schema_migrations
        WHERE version = 21
        """
    ).fetchone()

    assert {
        "id",
        "community_id",
        "access_request_id",
        "actor_membership_id",
        "event_type",
        "from_status",
        "to_status",
        "invitation_id",
        "created_at",
    }.issubset(columns)
    assert "idx_community_access_request_events_request" in indexes
    assert migration["name"] == "community-access-request-events"


def test_community_access_requests_are_tenant_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("access-hosted", "Access Hosted")
    user = repo.create_user("access-request@example.com", "hash")
    default_role = repo.create_role(default.id, "access-member", "Access Member")
    hosted_role = repo.create_role(hosted.id, "access-member", "Access Member")
    default_director = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "access-director",
        "Access Director",
    )
    hosted_director = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "access-director",
        "Access Director Elsewhere",
    )
    default_invitation = repo.create_community_invitation(
        default.id,
        email="writer@example.com",
        role_id=default_role.id,
        invited_by_membership_id=default_director.id,
        token_hash=token_hex(16),
        expires_at=None,
    )
    hosted_invitation = repo.create_community_invitation(
        hosted.id,
        email="writer@example.com",
        role_id=hosted_role.id,
        invited_by_membership_id=hosted_director.id,
        token_hash=token_hex(16),
        expires_at=None,
    )

    default_request = repo.create_community_access_request(
        default.id,
        email="writer@example.com",
        display_name="Writer",
        face_concept="Archive thief",
        wanted_hook="Sealed branch",
        notes="Interested in public memory pressure.",
        account_user_id=user.id,
    )
    repo.create_community_access_request(
        hosted.id,
        email="writer@example.com",
        display_name="Writer Elsewhere",
        face_concept="Station medic",
        wanted_hook="Docking delay",
        notes="Different realm.",
        account_user_id=user.id,
    )

    assert repo.get_community_access_request(default.id, default_request.id) == default_request
    assert repo.list_community_access_requests(default.id) == [default_request]
    assert repo.list_community_access_requests(default.id, status="pending") == [default_request]
    assert (
        repo.find_open_community_access_request(
            default.id,
            email="WRITER@example.com",
        )
        == default_request
    )
    assert (
        repo.find_open_community_access_request(
            hosted.id,
            email="writer@example.com",
        )
        is not None
    )
    reviewed = repo.update_community_access_request_status(
        default.id,
        default_request.id,
        status="reviewed",
    )
    assert reviewed.status == "reviewed"
    assert reviewed.invitation_id is None
    assert (
        repo.find_open_community_access_request(default.id, email="writer@example.com") == reviewed
    )
    with pytest.raises(LookupError, match="access request not found"):
        repo.get_community_access_request(hosted.id, default_request.id)

    reviewed_with_invitation = repo.update_community_access_request_status(
        default.id,
        default_request.id,
        status="invited",
        invitation_id=default_invitation.id,
    )
    invited_event = repo.create_community_access_request_event(
        default.id,
        default_request.id,
        event_type="invited",
        from_status="reviewed",
        to_status="invited",
        actor_membership_id=default_director.id,
        invitation_id=default_invitation.id,
    )
    assert reviewed_with_invitation.invitation_id == default_invitation.id
    repo.connection.execute(
        """
        UPDATE community_access_requests
        SET invitation_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_invitation.id, default.id, default_request.id),
    )
    repo.connection.execute(
        """
        UPDATE community_access_request_events
        SET actor_membership_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_director.id, default.id, invited_event.id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("community_access_requests", default_request.id)] == (
        "community access request invitation belongs to another community"
    )
    assert issue_map[("community_access_request_events", invited_event.id)] == (
        "community access request event actor membership belongs to another community"
    )


def test_community_access_request_status_transitions(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    role = repo.create_role(default.id, "access-member", "Access Member")
    director = repo.create_user("access-director@example.com", "hash")
    membership = repo.create_membership(
        default.id,
        director.id,
        username="accessdirector",
        display_name="Access Director",
        avatar_url="",
        role_id=role.id,
    )
    token_hash = token_hex(16)
    invitation = repo.create_community_invitation(
        default.id,
        email="transition@example.com",
        role_id=role.id,
        invited_by_membership_id=membership.id,
        token_hash=token_hash,
        expires_at=None,
    )
    access_request = repo.create_community_access_request(
        default.id,
        email="transition@example.com",
        display_name="Transition Prospect",
        face_concept="Archivist",
        wanted_hook="Seal pressure",
        notes="Needs state proof.",
    )

    with pytest.raises(ValueError, match="require an invitation"):
        repo.update_community_access_request_status(
            default.id,
            access_request.id,
            status="invited",
        )
    invited = repo.update_community_access_request_status(
        default.id,
        access_request.id,
        status="invited",
        invitation_id=invitation.id,
    )

    assert invited.status == "invited"
    assert invited.invitation_id == invitation.id
    assert (
        repo.update_community_access_request_status(
            default.id,
            access_request.id,
            status="invited",
            invitation_id=invitation.id,
        )
        == invited
    )
    with pytest.raises(ValueError, match="cannot move access request from invited to declined"):
        repo.update_community_access_request_status(
            default.id,
            access_request.id,
            status="declined",
        )


def test_discovery_profiles_and_tags_are_tenant_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("discovery-hosted", "Discovery Hosted")
    default_event = repo.create_material(
        default.id,
        "current-chapter",
        "Current Chapter",
        material_type="event",
    )
    hosted_event = repo.create_material(
        hosted.id,
        "current-chapter",
        "Current Chapter",
        material_type="event",
    )

    default_profile = repo.upsert_discovery_profile(
        default.id,
        premise_archetype="weird-town-mystery",
        play_engine="mystery-driven",
        lore_aperture="open lore",
        access_model="public preview",
        application_model="profile app",
        age_rating="21+",
        activity_pace="relaxed",
        catalog_pitch="A signal-haunted town with public rumors.",
        featured_event_material_id=default_event.id,
    )
    hosted_profile = repo.upsert_discovery_profile(
        hosted.id,
        premise_archetype="weird-town-mystery",
        play_engine="mystery-driven",
        lore_aperture="open lore",
        access_model="public preview",
        application_model="profile app",
        age_rating="21+",
        activity_pace="relaxed",
        catalog_pitch="A different realm can use the same archetype.",
        featured_event_material_id=hosted_event.id,
    )

    repo.replace_discovery_tags(
        default.id,
        (
            DiscoveryTagInput("premise", "weird-town", "Weird town", sort_order=20),
            DiscoveryTagInput("tone", "haunted", "Haunted", search_text="ghosts cryptids"),
        ),
    )
    repo.replace_discovery_tags(
        hosted.id,
        (
            DiscoveryTagInput("premise", "weird-town", "Weird town", sort_order=10),
            DiscoveryTagInput("tone", "sunny", "Sunny"),
        ),
    )

    profiles = repo.list_discovery_profiles_for_communities([default.id])
    tags = repo.list_discovery_tags_for_communities([default.id])

    assert profiles == {default.id: default_profile}
    assert hosted_profile.community_id == hosted.id
    assert [tag.tag_key for tag in tags[default.id]] == ["weird-town", "haunted"]
    assert {tag.community_id for tag in tags[default.id]} == {default.id}
    assert repo.get_discovery_tag(hosted.id, "premise", "weird-town").label == "Weird town"

    repo.connection.execute(
        """
        UPDATE community_discovery_profiles
        SET featured_event_material_id = ?
        WHERE community_id = ?
        """,
        (hosted_event.id, default.id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("community_discovery_profiles", default.id)] == (
        "community discovery profile featured event belongs to another community"
    )


def test_discovery_profile_rejects_cross_community_featured_event(
    repo: ForumRepository,
) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("discovery-cross-event", "Discovery Cross Event")
    hosted_event = repo.create_material(
        hosted.id,
        "current-chapter",
        "Current Chapter",
        material_type="event",
    )

    with pytest.raises(LookupError, match="material not found"):
        repo.upsert_discovery_profile(
            default.id,
            premise_archetype="small-town-social-web",
            featured_event_material_id=hosted_event.id,
        )


def test_discovery_rows_cascade_with_community(repo: ForumRepository) -> None:
    community = repo.create_community("discovery-cascade", "Discovery Cascade")
    repo.upsert_discovery_profile(
        community.id,
        premise_archetype="strange-frontier",
    )
    repo.upsert_discovery_tag(
        community.id,
        DiscoveryTagInput("premise", "frontier", "Strange frontier"),
    )

    repo.connection.execute("DELETE FROM communities WHERE id = ?", (community.id,))
    repo.connection.commit()

    assert (
        repo.connection.execute(
            "SELECT COUNT(*) FROM community_discovery_profiles WHERE community_id = ?",
            (community.id,),
        ).fetchone()[0]
        == 0
    )
    assert (
        repo.connection.execute(
            "SELECT COUNT(*) FROM community_discovery_tags WHERE community_id = ?",
            (community.id,),
        ).fetchone()[0]
        == 0
    )


def test_gateway_slots_are_tenant_scoped_and_validate_eligible_targets(
    repo: ForumRepository,
) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("gateway-hosted", "Gateway Hosted")
    default_role = repo.create_role(default.id, "gateway-member", "Gateway Member")
    hosted_role = repo.create_role(hosted.id, "gateway-member", "Gateway Member")
    default_user = repo.create_user("gateway-default@example.com", "hash")
    hosted_user = repo.create_user("gateway-hosted@example.com", "hash")
    default_membership = repo.create_membership(
        default.id,
        default_user.id,
        default_role.id,
        "gateway-default",
        "Gateway Default",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        hosted_user.id,
        hosted_role.id,
        "gateway-hosted",
        "Gateway Hosted",
    )
    scene_hub = repo.create_board(
        default.id,
        "public-scene-hub",
        "Public scene hub",
        board_kind="location",
    )
    private_hub = repo.create_board(
        default.id,
        "private-scene-hub",
        "Private scene hub",
        board_kind="location",
        is_private=True,
    )
    desk_board = repo.create_board(default.id, "desk-hub", "Desk hub", board_kind="desk")
    hosted_scene_hub = repo.create_board(
        hosted.id,
        "public-scene-hub",
        "Hosted public scene hub",
        board_kind="location",
    )
    wanted = repo.create_wanted_ad(
        default.id,
        default_membership.id,
        "public-wanted-hook",
        "Public wanted hook",
    )
    reserved_wanted = repo.create_wanted_ad(
        default.id,
        default_membership.id,
        "reserved-wanted-hook",
        "Reserved wanted hook",
        status="reserved",
    )
    hosted_wanted = repo.create_wanted_ad(
        hosted.id,
        hosted_membership.id,
        "public-wanted-hook",
        "Hosted public wanted hook",
    )
    material = repo.create_material(
        default.id,
        "public-guidebook-material",
        "Public guidebook material",
    )
    hosted_material = repo.create_material(
        hosted.id,
        "public-guidebook-material",
        "Hosted public guidebook material",
    )
    draft_material = repo.create_material(
        default.id,
        "draft-guidebook-material",
        "Draft guidebook material",
        status="draft",
    )

    first = repo.create_community_gateway_slot(
        default.id,
        "scene_hub",
        scene_hub.id,
        position=20,
        label="Start here",
    )
    second = repo.create_community_gateway_slot(default.id, "wanted_hook", wanted.id)
    third = repo.create_community_gateway_slot(
        default.id,
        "guidebook_material",
        material.id,
    )

    assert first.label == "Start here"
    assert second.position == 10
    assert third.slot_type == "guidebook_material"
    assert repo.list_community_gateway_slots(default.id, slot_type="scene_hub") == [first]
    assert repo.list_community_gateway_slots(hosted.id) == []

    replaced = repo.replace_community_gateway_slots(
        default.id,
        "scene_hub",
        [(scene_hub.id, "Featured place")],
    )
    assert [(slot.target_id, slot.position, slot.label) for slot in replaced] == [
        (scene_hub.id, 10, "Featured place")
    ]
    repo.delete_community_gateway_slot(default.id, replaced[0].id)
    assert repo.list_community_gateway_slots(default.id, slot_type="scene_hub") == []

    with pytest.raises(LookupError):
        repo.create_community_gateway_slot(hosted.id, "scene_hub", scene_hub.id)
    with pytest.raises(LookupError):
        repo.create_community_gateway_slot(default.id, "wanted_hook", hosted_wanted.id)
    with pytest.raises(LookupError):
        repo.delete_community_gateway_slot(hosted.id, first.id)
    with pytest.raises(ValueError, match="public scene hub board"):
        repo.create_community_gateway_slot(default.id, "scene_hub", private_hub.id)
    with pytest.raises(ValueError, match="public scene hub board"):
        repo.create_community_gateway_slot(default.id, "scene_hub", desk_board.id)
    with pytest.raises(ValueError, match="open wanted hook"):
        repo.create_community_gateway_slot(default.id, "wanted_hook", reserved_wanted.id)
    with pytest.raises(ValueError, match="published material"):
        repo.create_community_gateway_slot(
            default.id,
            "guidebook_material",
            draft_material.id,
        )
    with pytest.raises(ValueError, match="gateway slot type must be one of:"):
        repo.create_community_gateway_slot(default.id, "public_scene", hosted_scene_hub.id)

    diagnostic_scene = repo.create_community_gateway_slot(default.id, "scene_hub", scene_hub.id)
    repo.connection.execute(
        """
        UPDATE community_gateway_slots
        SET target_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_scene_hub.id, default.id, diagnostic_scene.id),
    )
    repo.connection.execute(
        """
        UPDATE community_gateway_slots
        SET target_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_wanted.id, default.id, second.id),
    )
    repo.connection.execute(
        """
        UPDATE community_gateway_slots
        SET target_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_material.id, default.id, third.id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("community_gateway_slots", diagnostic_scene.id)] == (
        "community gateway slot scene hub board belongs to another community"
    )
    assert issue_map[("community_gateway_slots", second.id)] == (
        "community gateway slot wanted hook belongs to another community"
    )
    assert issue_map[("community_gateway_slots", third.id)] == (
        "community gateway slot guidebook material belongs to another community"
    )


def test_community_invitation_lifecycle_is_tenant_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted-invitations", "Hosted Invitations")
    default_role = repo.create_role(default.id, "member", "Member")
    hosted_director_role = repo.create_role(hosted.id, "director", "Director", is_admin=True)
    hosted_member_role = repo.create_role(hosted.id, "member", "Member")
    director_user = repo.create_user("inviting-director@example.com", "hash")
    writer_user = repo.create_user("invited-writer@example.com", "hash")
    default_director = repo.create_membership(
        default.id,
        director_user.id,
        default_role.id,
        "inviting-director",
        "Inviting Director",
    )
    hosted_director = repo.create_membership(
        hosted.id,
        director_user.id,
        hosted_director_role.id,
        "inviting-director",
        "Inviting Director",
    )

    with pytest.raises(LookupError, match="membership not found"):
        repo.create_community_invitation(
            hosted.id,
            email="wrong-realm@example.com",
            role_id=hosted_member_role.id,
            invited_by_membership_id=default_director.id,
            token_hash=f"{hosted.id}:wrong-realm",
            expires_at="2026-06-01T00:00:00+00:00",
        )

    invitation = repo.create_community_invitation(
        hosted.id,
        email="invited-writer@example.com",
        role_id=hosted_member_role.id,
        invited_by_membership_id=hosted_director.id,
        token_hash=f"{hosted.id}:invitation",
        expires_at="2026-06-01T00:00:00+00:00",
    )
    membership = repo.create_membership(
        hosted.id,
        writer_user.id,
        hosted_member_role.id,
        "invited-writer",
        "Invited Writer",
    )
    accepted = repo.accept_community_invitation(
        invitation.id,
        user_id=writer_user.id,
        membership_id=membership.id,
    )
    second_invitation = repo.create_community_invitation(
        hosted.id,
        email="revoked-writer@example.com",
        role_id=hosted_member_role.id,
        invited_by_membership_id=hosted_director.id,
        token_hash=f"{hosted.id}:revoked-invitation",
        expires_at="2026-06-01T00:00:00+00:00",
    )
    revoked = repo.revoke_community_invitation(hosted.id, second_invitation.id)

    assert invitation.community_id == hosted.id
    assert (
        repo.get_community_invitation_by_token_hash(f"{hosted.id}:invitation").id == invitation.id
    )
    assert [item.id for item in repo.list_community_invitations(hosted.id)] == [
        second_invitation.id,
        invitation.id,
    ]
    assert repo.list_community_invitations(default.id) == []
    assert accepted.status == "accepted"
    assert accepted.accepted_user_id == writer_user.id
    assert accepted.accepted_membership_id == membership.id
    assert accepted.accepted_at is not None
    assert revoked.status == "revoked"
    assert revoked.revoked_at is not None

    repo.connection.execute(
        """
        UPDATE community_invitations
        SET role_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (default_role.id, hosted.id, invitation.id),
    )
    repo.connection.execute(
        """
        UPDATE community_invitations
        SET accepted_membership_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (default_director.id, hosted.id, second_invitation.id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("community_invitations", invitation.id)] == (
        "community invitation role belongs to another community"
    )
    assert issue_map[("community_invitations", second_invitation.id)] == (
        "community invitation accepted membership belongs to another community"
    )


def test_schema_migrates_existing_posts_for_thread_local_public_numbers() -> None:
    connection = connect()
    create_schema(connection)
    repository = ForumRepository(connection)
    repository.seed_default_community()
    community = repository.get_community(1)
    role = repository.create_role(community.id, "member", "Member")
    user = repository.create_user("public-numbers@example.com", "hash")
    membership = repository.create_membership(
        community.id,
        user.id,
        role.id,
        "numbers",
        "Numbers",
    )
    character = repository.create_character(community.id, membership.id, "numbers", "Numbers")
    board = repository.create_board(community.id, "numbered-scenes", "Numbered Scenes")
    first_thread = repository.create_thread(
        community.id,
        board.id,
        character.id,
        "first-scene",
        "First Scene",
    )
    second_thread = repository.create_thread(
        community.id,
        board.id,
        character.id,
        "second-scene",
        "Second Scene",
    )
    first_post = repository.create_post(community.id, first_thread.id, character.id, "First beat.")
    second_thread_post = repository.create_post(
        community.id,
        second_thread.id,
        character.id,
        "Other opener.",
    )
    reply = repository.create_post(community.id, first_thread.id, character.id, "Second beat.")

    connection.execute("DROP INDEX idx_posts_thread_post_number")
    connection.execute("ALTER TABLE posts DROP COLUMN post_number")
    connection.execute("DELETE FROM schema_migrations")
    connection.execute(
        """
        INSERT INTO schema_migrations (version, name, applied_at)
        VALUES (11, 'user-session-identity-selection', '2026-01-01T00:00:00+00:00')
        """
    )
    connection.execute("PRAGMA user_version = 11")
    connection.commit()

    create_schema(connection)

    rows = connection.execute(
        """
        SELECT thread_id, id, post_number
        FROM posts
        ORDER BY thread_id, post_number
        """
    ).fetchall()

    assert [tuple(row) for row in rows] == [
        (first_thread.id, first_post.id, 1),
        (first_thread.id, reply.id, 2),
        (second_thread.id, second_thread_post.id, 1),
    ]


def test_thread_counts_are_scoped_to_board_and_community() -> None:
    connection = connect()
    create_schema(connection)
    repository = ForumRepository(connection)
    repository.seed_default_community()
    default = repository.get_community(1)
    hosted = repository.create_community("hosted-thread-count", "Hosted Thread Count")
    default_role = repository.create_role(default.id, "member", "Member")
    hosted_role = repository.create_role(hosted.id, "member", "Member")
    user = repository.create_user("thread-count@example.com", "hash")
    default_membership = repository.create_membership(
        default.id,
        user.id,
        default_role.id,
        "thread-count",
        "Thread Count",
    )
    hosted_membership = repository.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "thread-count",
        "Thread Count",
    )
    default_character = repository.create_character(
        default.id,
        default_membership.id,
        "thread-count",
        "Thread Count",
    )
    hosted_character = repository.create_character(
        hosted.id,
        hosted_membership.id,
        "thread-count",
        "Thread Count",
    )
    default_board = repository.create_board(default.id, "scenes", "Scenes")
    other_default_board = repository.create_board(default.id, "archives", "Archives")
    hosted_board = repository.create_board(hosted.id, "scenes", "Scenes")

    repository.create_thread(default.id, default_board.id, default_character.id, "one", "One")
    repository.create_thread(default.id, default_board.id, default_character.id, "two", "Two")
    repository.create_thread(
        default.id,
        other_default_board.id,
        default_character.id,
        "archived",
        "Archived",
    )
    repository.create_thread(hosted.id, hosted_board.id, hosted_character.id, "hosted", "Hosted")

    assert repository.count_threads(default.id, default_board.id) == 2
    assert repository.count_threads(default.id) == 3
    assert repository.count_threads(hosted.id, hosted_board.id) == 1


def test_user_sessions_can_be_created_touched_and_revoked(repo: ForumRepository) -> None:
    user = repo.create_user("session@example.com", "hash")
    session = repo.create_user_session(
        user.id,
        "abc123",
        expires_at="2026-06-01T00:00:00+00:00",
    )

    stored = repo.get_user_session_by_token_hash("abc123")
    touched = repo.touch_user_session(session.id)
    repo.revoke_user_session_by_token_hash("abc123")
    revoked = repo.get_user_session_by_token_hash("abc123")

    assert stored.user_id == user.id
    assert stored.expires_at == "2026-06-01T00:00:00+00:00"
    assert touched.last_seen_at >= session.last_seen_at
    assert revoked.revoked_at is not None


def test_incomplete_command_submissions_can_be_discarded_for_retry(
    repo: ForumRepository,
) -> None:
    community = repo.get_community(1)
    role = repo.create_role(community.id, "command-member", "Command Member")
    membership = repo.create_membership(
        community.id,
        repo.create_user("command-retry@example.com", "hash").id,
        role.id,
        "command-member",
        "Command Member",
    )
    token = token_hex(16)

    assert repo.reserve_command_submission(
        community.id,
        membership.id,
        command_key="reply:danger-room:sentinel-drill",
        token=token,
    )
    assert not repo.reserve_command_submission(
        community.id,
        membership.id,
        command_key="reply:danger-room:sentinel-drill",
        token=token,
    )
    assert repo.discard_command_submission(
        community.id,
        membership.id,
        command_key="reply:danger-room:sentinel-drill",
        token=token,
    )
    assert (
        repo.get_command_submission(
            community.id,
            membership.id,
            command_key="reply:danger-room:sentinel-drill",
            token=token,
        )
        is None
    )
    assert repo.reserve_command_submission(
        community.id,
        membership.id,
        command_key="reply:danger-room:sentinel-drill",
        token=token,
    )
    repo.complete_command_submission(
        community.id,
        membership.id,
        command_key="reply:danger-room:sentinel-drill",
        token=token,
        result_path="/boards/danger-room/threads/sentinel-drill#post-4",
    )

    assert not repo.discard_command_submission(
        community.id,
        membership.id,
        command_key="reply:danger-room:sentinel-drill",
        token=token,
    )
    completed = repo.get_command_submission(
        community.id,
        membership.id,
        command_key="reply:danger-room:sentinel-drill",
        token=token,
    )

    assert completed is not None
    assert completed.result_path == "/boards/danger-room/threads/sentinel-drill#post-4"


def test_membership_role_integrity_issues_detect_cross_community_roles(
    repo: ForumRepository,
) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted-role-integrity", "Hosted Role Integrity")
    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    user = repo.create_user("role-integrity@example.com", "hash")
    membership = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "role-integrity",
        "Role Integrity",
    )

    repo.connection.execute(
        """
        UPDATE community_memberships
        SET role_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (default_role.id, hosted.id, membership.id),
    )
    repo.connection.commit()

    issues = repo.list_membership_role_integrity_issues()

    assert len(issues) == 1
    assert issues[0].community_id == hosted.id
    assert issues[0].membership_id == membership.id
    assert issues[0].role_id == default_role.id


def test_session_identity_integrity_issues_detect_cross_community_selection(
    repo: ForumRepository,
) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted-session-integrity", "Hosted Session Integrity")
    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    user = repo.create_user("session-integrity@example.com", "hash")
    default_membership = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "session-integrity",
        "Session Integrity",
    )
    repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "session-integrity",
        "Session Integrity",
    )
    session = repo.create_user_session(
        user.id,
        "session-integrity-token",
        expires_at="2026-06-01T00:00:00+00:00",
    )

    # Diagnostics still need to identify legacy/corrupt rows that predate trigger enforcement.
    repo.connection.execute("DROP TRIGGER trg_user_sessions_selected_identity_update")
    repo.connection.execute("DROP TRIGGER trg_user_sessions_selected_identity_insert")
    repo.connection.execute(
        """
        UPDATE user_sessions
        SET selected_community_id = ?,
            selected_membership_id = ?
        WHERE id = ?
        """,
        (hosted.id, default_membership.id, session.id),
    )
    repo.connection.commit()

    issues = repo.list_session_identity_integrity_issues()

    assert len(issues) == 1
    assert issues[0].session_id == session.id
    assert issues[0].selected_community_id == hosted.id
    assert issues[0].selected_membership_id == default_membership.id
    assert issues[0].reason == "selected membership belongs to another community"


def test_tenant_pair_integrity_issues_detect_wrong_face_authorship(
    repo: ForumRepository,
) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted-authorship", "Hosted Authorship")
    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    default_user = repo.create_user("authorship@example.com", "hash")
    hosted_user = repo.create_user("hosted-authorship@example.com", "hash")
    default_membership = repo.create_membership(
        default.id,
        default_user.id,
        default_role.id,
        "authorship",
        "Authorship",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        hosted_user.id,
        hosted_role.id,
        "hosted-authorship",
        "Hosted Authorship",
    )
    default_character = repo.create_character(
        default.id,
        default_membership.id,
        "authorship",
        "Authorship",
    )
    hosted_character = repo.create_character(
        hosted.id,
        hosted_membership.id,
        "hosted-authorship",
        "Hosted Authorship",
    )
    other_default_membership = repo.create_membership(
        default.id,
        repo.create_user("other-authorship@example.com", "hash").id,
        default_role.id,
        "other-authorship",
        "Other Authorship",
    )
    other_default_character = repo.create_character(
        default.id,
        other_default_membership.id,
        "other-authorship",
        "Other Authorship",
    )
    board = repo.create_board(default.id, "authorship", "Authorship")
    thread = repo.create_thread(
        default.id,
        board.id,
        default_character.id,
        "authorship",
        "Authorship",
    )
    post = repo.create_post(default.id, thread.id, default_character.id, "First beat.")
    notification = repo.create_notification(
        default.id,
        default_membership.id,
        kind="character",
        character_id=default_character.id,
        actor_membership_id=default_membership.id,
        actor_character_id=default_character.id,
    )

    with pytest.raises(LookupError, match="character not found"):
        repo.create_notification(
            default.id,
            default_membership.id,
            kind="character",
            character_id=default_character.id,
            actor_membership_id=default_membership.id,
            actor_character_id=hosted_character.id,
        )
    with pytest.raises(TenantBoundaryError, match="does not belong to membership"):
        repo.create_notification(
            default.id,
            default_membership.id,
            kind="character",
            character_id=default_character.id,
            actor_membership_id=default_membership.id,
            actor_character_id=other_default_character.id,
        )

    wanted = repo.create_wanted_ad(default.id, default_membership.id, "authorship", "Authorship")
    interest = repo.create_wanted_ad_interest(
        default.id,
        wanted.id,
        other_default_membership.id,
        other_default_character.id,
    )
    room = repo.create_plotting_room(
        default.id,
        default_membership.id,
        "Authorship Room",
        source_wanted_ad_id=wanted.id,
        source_wanted_ad_interest_id=interest.id,
    )
    participant = repo.create_plotting_room_participant(
        default.id,
        room.id,
        default_membership.id,
        character_id=default_character.id,
    )
    message = repo.create_plotting_room_message(
        default.id,
        room.id,
        default_membership.id,
        "A clean planning note.",
        author_character_id=default_character.id,
    )

    repo.connection.execute(
        """
        UPDATE threads
        SET author_character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_character.id, default.id, thread.id),
    )
    repo.connection.execute(
        """
        UPDATE posts
        SET author_character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_character.id, default.id, post.id),
    )
    repo.connection.execute(
        """
        UPDATE thread_participants
        SET character_id = ?
        WHERE community_id = ? AND thread_id = ? AND character_id = ?
        """,
        (hosted_character.id, default.id, thread.id, default_character.id),
    )
    repo.connection.execute(
        """
        UPDATE notifications
        SET actor_character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_character.id, default.id, notification.id),
    )
    repo.connection.execute(
        """
        UPDATE plotting_room_participants
        SET character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_character.id, default.id, participant.id),
    )
    repo.connection.execute(
        """
        UPDATE plotting_room_messages
        SET author_character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (other_default_character.id, default.id, message.id),
    )
    repo.connection.commit()

    issues = repo.list_tenant_pair_integrity_issues()

    issue_map = {(issue.table_name, issue.row_id): issue.reason for issue in issues}

    assert issue_map[("threads", thread.id)] == (
        "thread author character does not match community and membership"
    )
    assert issue_map[("posts", post.id)] == (
        "post author character does not match community and membership"
    )
    participant_issue = next(
        issue
        for issue in issues
        if issue.table_name == "thread_participants" and issue.community_id == default.id
    )
    assert participant_issue.reason == "thread participant character belongs to another community"
    assert issue_map[("notifications", notification.id)] == (
        "notification actor character does not match community and membership"
    )
    assert issue_map[("plotting_room_participants", participant.id)] == (
        "plotting room participant character does not match community and membership"
    )
    assert issue_map[("plotting_room_messages", message.id)] == (
        "plotting room message author character does not match community and membership"
    )


def test_notification_read_writes_are_membership_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    role = repo.create_role(default.id, "member", "Member")
    first_membership = repo.create_membership(
        default.id,
        repo.create_user("first-notify-read@example.com", "hash").id,
        role.id,
        "first-notify-read",
        "First Notify Read",
    )
    second_membership = repo.create_membership(
        default.id,
        repo.create_user("second-notify-read@example.com", "hash").id,
        role.id,
        "second-notify-read",
        "Second Notify Read",
    )
    first_character = repo.create_character(
        default.id,
        first_membership.id,
        "first-notify-read",
        "First Notify Read",
    )
    second_character = repo.create_character(
        default.id,
        second_membership.id,
        "second-notify-read",
        "Second Notify Read",
    )
    first_notification = repo.create_notification(
        default.id,
        first_membership.id,
        kind="character",
        character_id=first_character.id,
        actor_membership_id=first_membership.id,
        actor_character_id=first_character.id,
    )
    second_notification = repo.create_notification(
        default.id,
        second_membership.id,
        kind="character",
        character_id=second_character.id,
        actor_membership_id=second_membership.id,
        actor_character_id=second_character.id,
    )

    repo.mark_notifications_read(
        default.id,
        first_membership.id,
        [first_notification.id, second_notification.id],
    )

    assert repo.get_notification(default.id, first_notification.id).read_at is not None
    assert repo.get_notification(default.id, second_notification.id).read_at is None
    with pytest.raises(LookupError, match="notification not found for membership"):
        repo.mark_notification_read(
            default.id,
            first_membership.id,
            second_notification.id,
        )
    assert repo.get_notification(default.id, second_notification.id).read_at is None

    repo.mark_notification_read(default.id, second_membership.id, second_notification.id)

    assert repo.get_notification(default.id, second_notification.id).read_at is not None


def test_schema_migrates_existing_boards_for_place_navigation() -> None:
    connection = connect()
    connection.executescript(
        """
        CREATE TABLE communities (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            host TEXT UNIQUE,
            default_theme_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE boards (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            slug TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_private INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, slug)
        );
        INSERT INTO communities (id, name, slug, host, default_theme_id, created_at, updated_at)
        VALUES (1, 'Default', 'default', NULL, NULL, '2026-01-01T00:00:00', '2026-01-01T00:00:00');
        INSERT INTO boards (
            id, community_id, slug, name, description, sort_order, is_private, created_at, updated_at
        )
        VALUES (
            1, 1, 'ic', 'In Character', 'Old board shape.', 10, 0,
            '2026-01-01T00:00:00', '2026-01-01T00:00:00'
        );
        """
    )

    create_schema(connection)

    columns = {row["name"] for row in connection.execute("PRAGMA table_info(boards)").fetchall()}
    indexes = {row["name"] for row in connection.execute("PRAGMA index_list(boards)").fetchall()}
    board = connection.execute(
        """
        SELECT
            parent_board_id,
            board_kind,
            sidebar_section,
            tagline,
            image_url,
            image_alt,
            image_treatment,
            image_focal_point,
            image_overlay,
            navigation_order,
            show_in_navigation
        FROM boards
        WHERE id = 1
        """
    ).fetchone()
    sidebar_sections = connection.execute(
        """
        SELECT realm, section_key, label, sort_order, show_label, is_system
        FROM sidebar_sections
        WHERE community_id = 1
        ORDER BY realm, sort_order
        """
    ).fetchall()

    assert {
        "parent_board_id",
        "board_kind",
        "sidebar_section",
        "tagline",
        "image_url",
        "image_alt",
        "image_treatment",
        "image_focal_point",
        "image_overlay",
        "navigation_order",
        "show_in_navigation",
    }.issubset(columns)
    assert "idx_boards_parent_sort" in indexes
    assert "idx_boards_navigation" in indexes
    assert dict(board) == {
        "parent_board_id": None,
        "board_kind": "location",
        "sidebar_section": "locations",
        "tagline": "",
        "image_url": None,
        "image_alt": "",
        "image_treatment": "poster",
        "image_focal_point": "center",
        "image_overlay": "medium",
        "navigation_order": 10,
        "show_in_navigation": 1,
    }
    assert [dict(row) for row in sidebar_sections] == [
        {
            "realm": "desk",
            "section_key": "desk",
            "label": "Writer Desk",
            "sort_order": 10,
            "show_label": 0,
            "is_system": 1,
        },
        {
            "realm": "studio",
            "section_key": "studio",
            "label": "Director Studio",
            "sort_order": 20,
            "show_label": 0,
            "is_system": 1,
        },
        {
            "realm": "world",
            "section_key": "locations",
            "label": "Locations",
            "sort_order": 10,
            "show_label": 0,
            "is_system": 1,
        },
        {
            "realm": "world",
            "section_key": "community",
            "label": "Community",
            "sort_order": 20,
            "show_label": 0,
            "is_system": 1,
        },
    ]


def test_sidebar_section_config_is_scoped_by_community(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")

    default_locations = repo.update_sidebar_section(
        default.id,
        "locations",
        label="Realms",
        description="Major playable realms.",
        sort_order=4,
        show_label=True,
    )

    hosted_locations = repo.get_sidebar_section(hosted.id, "locations")

    assert default_locations.label == "Realms"
    assert default_locations.description == "Major playable realms."
    assert default_locations.sort_order == 4
    assert default_locations.show_label is True
    assert hosted_locations.label == "Locations"
    assert hosted_locations.show_label is False


def test_realm_interactions_are_scoped_and_accept_one_membership_response(
    repo: ForumRepository,
) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    user = repo.create_user("pollster@example.com", "hash")
    default_membership = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "pollster",
        "Pollster",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "pollster",
        "Pollster",
    )
    default_character = repo.create_character(
        default.id,
        default_membership.id,
        "poll-face",
        "Poll Face",
    )
    hosted_character = repo.create_character(
        hosted.id,
        hosted_membership.id,
        "hosted-poll-face",
        "Hosted Poll Face",
    )
    interaction = repo.create_realm_interaction(
        default.id,
        "sorting",
        "Sorting",
        placement="application",
    )
    question = repo.create_realm_interaction_question(
        default.id,
        interaction.id,
        "Where do you belong?",
    )
    option = repo.create_realm_interaction_option(
        default.id,
        question.id,
        "library",
        "The library",
    )
    hosted_interaction = repo.create_realm_interaction(
        hosted.id,
        "sorting",
        "Hosted Sorting",
        placement="application",
    )
    hosted_question = repo.create_realm_interaction_question(
        hosted.id,
        hosted_interaction.id,
        "Where do you belong elsewhere?",
    )
    hosted_option = repo.create_realm_interaction_option(
        hosted.id,
        hosted_question.id,
        "hosted-library",
        "The hosted library",
    )

    response = repo.submit_realm_interaction_response(
        default.id,
        interaction.id,
        default_membership.id,
        character_id=default_character.id,
        selected_option_ids={question.id: option.id},
    )
    replacement = repo.submit_realm_interaction_response(
        default.id,
        interaction.id,
        default_membership.id,
        character_id=default_character.id,
        selected_option_ids={question.id: option.id},
    )

    assert repo.get_realm_interaction_by_slug(default.id, "sorting").title == "Sorting"
    assert repo.get_realm_interaction_by_slug(hosted.id, "sorting").title == "Hosted Sorting"
    assert response.id == replacement.id
    assert response.character_id == default_character.id
    assert repo.count_realm_interaction_responses(default.id, interaction.id) == 1
    assert repo.realm_interaction_option_counts(default.id, interaction.id) == {option.id: 1}
    with pytest.raises(LookupError, match="membership not found"):
        repo.submit_realm_interaction_response(
            default.id,
            interaction.id,
            hosted_membership.id,
            selected_option_ids={question.id: option.id},
        )
    with pytest.raises(LookupError, match="character not found"):
        repo.submit_realm_interaction_response(
            default.id,
            interaction.id,
            default_membership.id,
            character_id=hosted_character.id,
            selected_option_ids={question.id: option.id},
        )
    other_user = repo.create_user("other-poll@example.com", "hash")
    other_membership = repo.create_membership(
        default.id,
        other_user.id,
        default_role.id,
        "other-poll",
        "Other Poll",
    )
    other_character = repo.create_character(
        default.id,
        other_membership.id,
        "other-poll-face",
        "Other Poll Face",
    )
    with pytest.raises(TenantBoundaryError, match="responding membership"):
        repo.submit_realm_interaction_response(
            default.id,
            interaction.id,
            default_membership.id,
            character_id=other_character.id,
            selected_option_ids={question.id: option.id},
        )

    answer_id = repo.connection.execute(
        """
        SELECT id
        FROM realm_interaction_answers
        WHERE community_id = ? AND response_id = ?
        """,
        (default.id, response.id),
    ).fetchone()["id"]
    repo.connection.execute(
        """
        UPDATE realm_interaction_responses
        SET character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_character.id, default.id, response.id),
    )
    repo.connection.execute(
        """
        UPDATE realm_interaction_answers
        SET option_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_option.id, default.id, answer_id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("realm_interaction_responses", response.id)] == (
        "realm interaction response character does not match community and membership"
    )
    assert issue_map[("realm_interaction_answers", answer_id)] == (
        "realm interaction answer option does not match question"
    )


def test_claim_types_template_fields_and_character_claims_are_scoped(
    repo: ForumRepository,
) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    user = repo.create_user("claims@example.com", "hash")
    default_membership = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "claimant",
        "Claimant",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "claimant",
        "Claimant",
    )
    default_character = repo.create_character(
        default.id,
        default_membership.id,
        "default-face",
        "Default Face",
    )
    second_default_character = repo.create_character(
        default.id,
        default_membership.id,
        "second-face",
        "Second Face",
    )
    hosted_character = repo.create_character(
        hosted.id,
        hosted_membership.id,
        "hosted-face",
        "Hosted Face",
    )

    default_face = repo.create_claim_type(
        default.id,
        "face",
        "Face Claim",
        claim_kind="face",
        is_required=True,
        is_exclusive=True,
    )
    default_faction = repo.create_claim_type(
        default.id,
        "faction",
        "Faction Claim",
        claim_kind="faction",
    )
    hosted_face = repo.create_claim_type(
        hosted.id,
        "face",
        "Hosted Face Claim",
        claim_kind="face",
        is_exclusive=True,
    )
    field = repo.create_application_template_field(
        default.id,
        "face_claim",
        "Face claim",
        field_type="text",
        maps_to_claim_type_id=default_face.id,
        is_required=True,
    )
    faction_field = repo.create_application_template_field(
        default.id,
        "faction_claim",
        "Faction claim",
        field_type="text",
        maps_to_claim_type_id=default_faction.id,
    )
    hosted_field = repo.create_application_template_field(
        hosted.id,
        "face_claim",
        "Hosted face claim",
        field_type="text",
        maps_to_claim_type_id=hosted_face.id,
    )
    application = repo.ensure_character_application(default.id, default_character.id)
    hosted_application = repo.ensure_character_application(hosted.id, hosted_character.id)
    field_value = repo.set_application_field_value(
        default.id,
        application.id,
        field.id,
        "Sample Face",
    )
    faction_field_value = repo.set_application_field_value(
        default.id,
        application.id,
        faction_field.id,
        "X-Men",
    )

    face_claim = repo.create_character_claim(
        default.id,
        default_face.id,
        "sample-face",
        "Sample Face",
        character_id=default_character.id,
    )
    repo.create_character_claim(
        default.id,
        default_faction.id,
        "x-men",
        "X-Men",
        character_id=default_character.id,
    )
    repo.create_character_claim(
        default.id,
        default_faction.id,
        "x-men",
        "X-Men",
        character_id=second_default_character.id,
    )
    repo.create_character_claim(
        hosted.id,
        hosted_face.id,
        "sample-face",
        "Sample Face",
        character_id=hosted_character.id,
    )

    assert repo.get_claim_type_by_slug(default.id, "face").name == "Face Claim"
    assert repo.get_claim_type_by_slug(hosted.id, "face").name == "Hosted Face Claim"
    assert repo.get_application_template_field_by_key(default.id, "face_claim").id == field.id
    assert (
        repo.get_application_field_value(default.id, application.id, field.id).id == field_value.id
    )
    assert [
        value.value for value in repo.list_application_field_values(default.id, application.id)
    ] == ["Sample Face", "X-Men"]
    assert len(repo.list_character_claims(default.id, claim_type_id=default_faction.id)) == 2
    assert len(repo.list_character_claims(hosted.id, claim_type_id=hosted_face.id)) == 1

    with pytest.raises(TenantBoundaryError, match="claim value is already in use"):
        repo.create_character_claim(
            default.id,
            default_face.id,
            "sample-face",
            "Duplicate Sample Face",
            character_id=second_default_character.id,
        )
    with pytest.raises(LookupError, match="claim type not found"):
        repo.get_claim_type(hosted.id, default_face.id)
    with pytest.raises(LookupError, match="claim type not found"):
        repo.create_application_template_field(
            hosted.id,
            "bad_field",
            "Bad field",
            maps_to_claim_type_id=default_face.id,
        )
    with pytest.raises(LookupError, match="application not found"):
        repo.set_application_field_value(hosted.id, application.id, field.id, "Leak")

    repo.connection.execute(
        """
        UPDATE application_template_fields
        SET maps_to_claim_type_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_face.id, default.id, field.id),
    )
    repo.connection.execute(
        """
        UPDATE application_field_values
        SET field_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_field.id, default.id, field_value.id),
    )
    repo.connection.execute(
        """
        UPDATE application_field_values
        SET application_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_application.id, default.id, faction_field_value.id),
    )
    repo.connection.execute(
        """
        UPDATE character_claims
        SET character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_character.id, default.id, face_claim.id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("character_claims", face_claim.id)] == (
        "character claim character belongs to another community"
    )
    assert issue_map[("application_template_fields", field.id)] == (
        "application template field mapped claim type belongs to another community"
    )
    assert issue_map[("application_field_values", field_value.id)] == (
        "application field value field belongs to another community"
    )
    assert issue_map[("application_field_values", faction_field_value.id)] == (
        "application field value application belongs to another community"
    )


def test_schema_migrates_plot_hook_and_prospective_interest_columns() -> None:
    connection = connect()
    connection.executescript(
        """
        CREATE TABLE wanted_ad_interests (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL,
            wanted_ad_id INTEGER NOT NULL,
            membership_id INTEGER NOT NULL,
            character_id INTEGER NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'interested',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, wanted_ad_id, membership_id, character_id)
        );
        CREATE TABLE notifications (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL,
            membership_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            thread_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            actor_membership_id INTEGER NOT NULL,
            actor_character_id INTEGER NOT NULL,
            read_at TEXT,
            created_at TEXT NOT NULL
        );
        """
    )

    create_schema(connection)

    wanted_columns = {
        row["name"]: row
        for row in connection.execute("PRAGMA table_info(wanted_ad_interests)").fetchall()
    }
    notification_columns = {
        row["name"]: row
        for row in connection.execute("PRAGMA table_info(notifications)").fetchall()
    }
    tables = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    plotting_columns = {
        row["name"]: row
        for row in connection.execute("PRAGMA table_info(plotting_rooms)").fetchall()
    }

    assert "character_plot_hooks" in tables
    assert "character_plot_hook_interests" in tables
    assert "plotting_rooms" in tables
    assert "plotting_room_participants" in tables
    assert "plotting_room_messages" in tables
    assert "applications" in tables
    assert "application_events" in tables
    assert "notes" in plotting_columns
    assert "next_step" in plotting_columns
    assert "target_board_id" in plotting_columns
    assert "target_thread_id" in plotting_columns
    assert wanted_columns["character_id"]["notnull"] == 0
    assert "prospective_character_name" in wanted_columns
    assert "character_plot_hook_id" in notification_columns
    assert "plotting_room_id" in notification_columns
    assert notification_columns["actor_character_id"]["notnull"] == 0


def test_schema_migrates_existing_characters_for_post_profile_variants() -> None:
    connection = connect()
    connection.executescript(
        """
        CREATE TABLE communities (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            host TEXT UNIQUE,
            default_theme_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE community_memberships (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            display_name TEXT NOT NULL,
            avatar_url TEXT,
            role_id INTEGER NOT NULL,
            default_character_id INTEGER,
            post_count INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            joined_at TEXT NOT NULL
        );
        CREATE TABLE characters (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL,
            membership_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            avatar_url TEXT,
            summary TEXT NOT NULL DEFAULT '',
            application_status TEXT NOT NULL DEFAULT 'accepted',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, slug)
        );
        INSERT INTO communities (id, name, slug, host, default_theme_id, created_at, updated_at)
        VALUES (1, 'Default', 'default', NULL, NULL, '2026-01-01T00:00:00', '2026-01-01T00:00:00');
        INSERT INTO community_memberships (
            id, community_id, user_id, username, display_name, role_id, joined_at
        )
        VALUES (1, 1, 1, 'writer', 'Writer', 1, '2026-01-01T00:00:00');
        INSERT INTO characters (
            id, community_id, membership_id, name, slug, avatar_url, summary, created_at, updated_at
        )
        VALUES (
            1, 1, 1, 'Rogue', 'rogue', NULL, 'Careful hands.',
            '2026-01-01T00:00:00', '2026-01-01T00:00:00'
        );
        """
    )

    create_schema(connection)

    columns = {
        row["name"]: row for row in connection.execute("PRAGMA table_info(characters)").fetchall()
    }
    community_columns = {
        row["name"]: row for row in connection.execute("PRAGMA table_info(communities)").fetchall()
    }
    character = connection.execute(
        """
        SELECT
            post_profile_variant,
            post_accent_style,
            post_border_style,
            post_title_style,
            post_density
        FROM characters
        WHERE id = 1
        """
    ).fetchone()

    assert "post_profile_variant" in columns
    assert "post_accent_style" in columns
    assert "post_border_style" in columns
    assert "post_title_style" in columns
    assert "post_density" in columns
    assert "identity_accent_facet_group_id" in community_columns
    assert "community_mark_url" in community_columns
    assert "community_mark_alt" in community_columns
    assert "world_hero_image_url" in community_columns
    assert "world_hero_image_alt" in community_columns
    assert "world_hero_treatment" in community_columns
    assert "world_hero_focal_point" in community_columns
    assert "world_hero_overlay" in community_columns
    assert "world_hero_height" in community_columns
    assert "enabled_post_profile_variants" in community_columns
    assert "enabled_post_accent_styles" in community_columns
    assert "enabled_post_border_styles" in community_columns
    assert "enabled_post_title_styles" in community_columns
    assert "enabled_post_densities" in community_columns
    assert character["post_profile_variant"] == "bio"
    assert character["post_accent_style"] == "soft"
    assert character["post_border_style"] == "hairline"
    assert character["post_title_style"] == "standard"
    assert character["post_density"] == "calm"


def test_community_identity_accent_group_is_tenant_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    default_group = repo.create_facet_group(default.id, "house", "House")
    hosted_group = repo.create_facet_group(hosted.id, "house", "House")

    updated = repo.update_community_identity_accent_group(default.id, default_group.id)

    assert updated.identity_accent_facet_group_id == default_group.id
    with pytest.raises(LookupError):
        repo.update_community_identity_accent_group(default.id, hosted_group.id)

    repo.connection.execute(
        """
        UPDATE communities
        SET identity_accent_facet_group_id = ?
        WHERE id = ?
        """,
        (hosted_group.id, default.id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("communities", default.id)] == (
        "community identity accent facet group belongs to another community"
    )


def test_community_post_style_policy_is_tenant_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")

    updated = repo.update_community_post_style_policy(
        default.id,
        enabled_post_profile_variants="bio,poster",
        enabled_post_accent_styles="soft,line",
        enabled_post_border_styles="hairline",
        enabled_post_title_styles="standard,mono",
        enabled_post_densities="calm,compact",
    )

    assert updated.enabled_post_profile_variants == "bio,poster"
    assert repo.get_community(hosted.id).enabled_post_profile_variants == ""


def test_community_media_slots_are_tenant_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")

    updated = repo.update_community_media(
        default.id,
        community_mark_url="https://example.test/mark.png",
        community_mark_alt="Board mark",
        world_hero_image_url="https://example.test/world.jpg",
        world_hero_image_alt="A foggy town square",
        world_hero_treatment="background",
        world_hero_focal_point="top",
        world_hero_overlay="heavy",
        world_hero_height="immersive",
    )

    assert updated.community_mark_url == "https://example.test/mark.png"
    assert updated.community_mark_alt == "Board mark"
    assert updated.world_hero_image_url == "https://example.test/world.jpg"
    assert updated.world_hero_image_alt == "A foggy town square"
    assert updated.world_hero_treatment == "background"
    assert updated.world_hero_focal_point == "top"
    assert updated.world_hero_overlay == "heavy"
    assert updated.world_hero_height == "immersive"
    assert repo.get_community(hosted.id).world_hero_image_url is None
    assert repo.get_community(hosted.id).world_hero_treatment == "split"


def test_board_hierarchy_is_tenant_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    parent = repo.create_board(default.id, "academy", "Academy", board_kind="location")
    hosted_parent = repo.create_board(hosted.id, "academy", "Academy", board_kind="location")

    child = repo.create_board(
        default.id,
        "med-bay",
        "Med Bay",
        parent_board_id=parent.id,
        board_kind="sublocation",
    )

    assert child.parent_board_id == parent.id
    assert [board.slug for board in repo.list_child_boards(default.id, parent.id)] == ["med-bay"]
    assert [board.slug for board in repo.list_child_boards(default.id, None)] == ["academy"]

    with pytest.raises(LookupError):
        repo.create_board(
            default.id,
            "wrong-house",
            "Wrong House",
            parent_board_id=hosted_parent.id,
        )

    repo.connection.execute(
        """
        UPDATE boards
        SET parent_board_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_parent.id, default.id, child.id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("boards", child.id)] == "board parent belongs to another community"


def test_board_cannot_parent_itself(repo: ForumRepository) -> None:
    community = repo.get_community(1)
    board = repo.create_board(community.id, "academy", "Academy", board_kind="location")

    with pytest.raises(TenantBoundaryError):
        repo.update_board(
            community.id,
            board.id,
            name=board.name,
            description=board.description,
            sort_order=board.sort_order,
            parent_board_id=board.id,
            board_kind=board.board_kind,
            tagline=board.tagline,
            image_url=board.image_url,
            image_alt=board.image_alt,
            is_private=board.is_private,
        )

    repo.connection.execute(
        """
        UPDATE boards
        SET parent_board_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (board.id, community.id, board.id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("boards", board.id)] == "board cannot be its own parent"


def test_public_identity_is_membership_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    user = repo.create_user("writer@example.com", "hash")

    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "admin", "Admin", is_admin=True)

    default_membership = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "lark",
        "Lark",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "winterglass",
        "Winterglass",
    )

    assert default_membership.username == "lark"
    assert hosted_membership.username == "winterglass"
    assert repo.get_role(hosted.id, hosted_membership.role_id).is_admin is True


def test_application_review_rooms_are_tenant_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    user = repo.create_user("application-room@example.com", "hash")
    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    default_membership = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "applicant",
        "Applicant",
    )
    other_user = repo.create_user("application-room-other@example.com", "hash")
    other_membership = repo.create_membership(
        default.id,
        other_user.id,
        default_role.id,
        "other",
        "Other",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "applicant",
        "Applicant Elsewhere",
    )
    rogue = repo.create_character(
        default.id,
        default_membership.id,
        "rogue",
        "Rogue",
        summary="Careful hands.",
        application_status="draft",
    )
    magneto = repo.create_character(
        hosted.id,
        hosted_membership.id,
        "magneto",
        "Magneto",
        application_status="draft",
    )
    jean = repo.create_character(
        default.id,
        other_membership.id,
        "jean-grey",
        "Jean Grey",
        application_status="accepted",
    )

    application = repo.ensure_character_application(default.id, rogue.id)
    updated = repo.update_character_application_draft(
        default.id,
        application.id,
        title="Rogue",
        summary="Careful hands, complicated loyalties.",
        body="I want her to test trust under pressure.",
    )
    reviewed = repo.update_character_application_review(
        default.id,
        updated.id,
        revision_notes="Clarify her first scene pressure point.",
        staff_notes="Strong concept.",
        checklist="Face claim\nStarter hook",
    )
    submitted = repo.transition_character_application_status(
        default.id,
        reviewed.id,
        status="submitted",
        actor_membership_id=default_membership.id,
        actor_character_id=rogue.id,
        note="Ready for review.",
    )
    events = repo.list_character_application_events(default.id, submitted.id)

    assert submitted.status == "submitted"
    assert repo.get_character(default.id, rogue.id).application_status == "submitted"
    assert reviewed.revision_notes == "Clarify her first scene pressure point."
    assert reviewed.staff_notes == "Strong concept."
    assert [event.note for event in events] == ["Ready for review."]

    with pytest.raises(LookupError):
        repo.ensure_character_application(default.id, magneto.id)
    with pytest.raises(LookupError):
        repo.get_character_application(hosted.id, application.id)
    with pytest.raises(TenantBoundaryError):
        repo.transition_character_application_status(
            default.id,
            submitted.id,
            status="accepted",
            actor_membership_id=default_membership.id,
            actor_character_id=jean.id,
        )
    assert repo.get_role(default.id, default_membership.role_id).is_admin is False

    event_id = events[0].id
    repo.connection.execute(
        """
        UPDATE applications
        SET membership_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_membership.id, default.id, submitted.id),
    )
    repo.connection.execute(
        """
        UPDATE application_events
        SET actor_character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (jean.id, default.id, event_id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("applications", submitted.id)] == (
        "application membership belongs to another community"
    )
    assert issue_map[("application_events", event_id)] == (
        "application event actor character does not match community and membership"
    )


def test_characters_are_membership_owned_posting_identities(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    user = repo.create_user("writer@example.com", "hash")

    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    default_membership = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "writer",
        "Writer",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "writer",
        "Writer Elsewhere",
    )

    rogue = repo.create_character(
        default.id,
        default_membership.id,
        "rogue",
        "Rogue",
        poster_url="https://example.test/rogue-poster.png",
        poster_alt="Rogue standing in the Danger Room",
        tagline="Careful hands, reckless heart.",
        accent_color="#79a889",
        post_profile_variant="dock",
        post_accent_style="glow",
        post_border_style="bracket",
        post_title_style="serif",
        post_density="dramatic",
        make_default=True,
    )
    magneto = repo.create_character(hosted.id, hosted_membership.id, "magneto", "Magneto")
    draft = repo.update_character_application_status(default.id, rogue.id, "draft")

    assert draft.application_status == "draft"
    assert draft.poster_url == "https://example.test/rogue-poster.png"
    assert draft.poster_alt == "Rogue standing in the Danger Room"
    assert draft.tagline == "Careful hands, reckless heart."
    assert draft.accent_color == "#79a889"
    assert draft.post_profile_variant == "dock"
    assert draft.post_accent_style == "glow"
    assert draft.post_border_style == "bracket"
    assert draft.post_title_style == "serif"
    assert draft.post_density == "dramatic"
    assert repo.get_character(default.id, rogue.id).application_status == "draft"
    assert repo.get_membership(default.id, default_membership.id).default_character_id == rogue.id
    assert repo.get_membership(hosted.id, hosted_membership.id).default_character_id is None
    assert repo.list_characters(default.id, default_membership.id) == [draft]
    assert repo.list_characters(hosted.id, hosted_membership.id) == [magneto]

    with pytest.raises(LookupError):
        repo.set_default_character(default.id, default_membership.id, magneto.id)


def test_character_transfer_repairs_membership_defaults(repo: ForumRepository) -> None:
    community = repo.get_community(1)
    role = repo.create_role(community.id, "member", "Member")
    first_user = repo.create_user("first-owner@example.com", "hash")
    second_user = repo.create_user("second-owner@example.com", "hash")
    first_membership = repo.create_membership(
        community.id,
        first_user.id,
        role.id,
        "first-owner",
        "First Owner",
    )
    second_membership = repo.create_membership(
        community.id,
        second_user.id,
        role.id,
        "second-owner",
        "Second Owner",
    )
    rogue = repo.create_character(
        community.id,
        first_membership.id,
        "rogue",
        "Rogue",
        make_default=True,
    )
    storm = repo.create_character(community.id, first_membership.id, "storm", "Storm")

    transferred = repo.transfer_character_membership(
        community.id,
        rogue.id,
        second_membership.id,
        make_default=True,
    )

    assert transferred.membership_id == second_membership.id
    assert repo.get_membership(community.id, first_membership.id).default_character_id == storm.id
    assert repo.get_membership(community.id, second_membership.id).default_character_id == rogue.id
    assert [
        character.slug for character in repo.list_characters(community.id, first_membership.id)
    ] == ["storm"]
    assert [
        character.slug for character in repo.list_characters(community.id, second_membership.id)
    ] == ["rogue"]


def test_character_updates_are_scoped_by_community(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    user = repo.create_user("writer@example.com", "hash")
    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    default_membership = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "writer",
        "Writer",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "writer",
        "Writer Elsewhere",
    )
    rogue = repo.create_character(default.id, default_membership.id, "rogue", "Rogue")
    repo.create_character(hosted.id, hosted_membership.id, "rogue", "Rogue Elsewhere")

    updated = repo.update_character(
        default.id,
        rogue.id,
        slug="rogue-prime",
        name="Rogue Prime",
        avatar_url="https://example.test/rogue.png",
        poster_url="https://example.test/rogue-prime-poster.png",
        poster_alt="Rogue Prime portrait",
        tagline="Nobody touches the plot without consequence.",
        accent_color="#79a889",
        summary="Still carrying the whole plot.",
        post_profile_variant="poster",
        post_accent_style="line",
        post_border_style="double",
        post_title_style="mono",
        post_density="compact",
    )

    assert updated.slug == "rogue-prime"
    assert updated.name == "Rogue Prime"
    assert updated.avatar_url == "https://example.test/rogue.png"
    assert updated.poster_url == "https://example.test/rogue-prime-poster.png"
    assert updated.poster_alt == "Rogue Prime portrait"
    assert updated.tagline == "Nobody touches the plot without consequence."
    assert updated.accent_color == "#79a889"
    assert updated.summary == "Still carrying the whole plot."
    assert updated.post_profile_variant == "poster"
    assert updated.post_accent_style == "line"
    assert updated.post_border_style == "double"
    assert updated.post_title_style == "mono"
    assert updated.post_density == "compact"
    assert repo.get_character_by_slug(hosted.id, "rogue").name == "Rogue Elsewhere"

    with pytest.raises(LookupError):
        repo.update_character(
            hosted.id,
            rogue.id,
            slug="bad",
            name="Bad",
            avatar_url=None,
            summary="Wrong community.",
        )


def test_world_facets_scope_characters_boards_and_threads(repo: ForumRepository) -> None:
    community = repo.get_community(1)
    hosted = repo.create_community("hosted-world-facets", "Hosted World Facets")
    role = repo.create_role(community.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    user = repo.create_user("writer@example.com", "hash")
    hosted_user = repo.create_user("hosted-writer@example.com", "hash")
    membership = repo.create_membership(community.id, user.id, role.id, "writer", "Writer")
    hosted_membership = repo.create_membership(
        hosted.id,
        hosted_user.id,
        hosted_role.id,
        "hosted-writer",
        "Hosted Writer",
    )
    rogue = repo.create_character(community.id, membership.id, "rogue", "Rogue")
    hosted_character = repo.create_character(
        hosted.id,
        hosted_membership.id,
        "hosted-rogue",
        "Hosted Rogue",
    )
    board = repo.create_board(community.id, "danger-room", "Danger Room")
    hosted_board = repo.create_board(hosted.id, "danger-room", "Hosted Danger Room")
    thread = repo.create_thread(
        community.id, board.id, rogue.id, "sentinel-drill", "Sentinel Drill"
    )
    second_thread = repo.create_thread(
        community.id,
        board.id,
        rogue.id,
        "blackbird-briefing",
        "Blackbird Briefing",
    )
    hosted_thread = repo.create_thread(
        hosted.id,
        hosted_board.id,
        hosted_character.id,
        "hosted-drill",
        "Hosted Drill",
    )

    species = repo.create_facet_group(community.id, "species", "Species", sort_order=10)
    affiliation = repo.create_facet_group(
        community.id,
        "affiliation",
        "Affiliation",
        sort_order=20,
    )
    hosted_group = repo.create_facet_group(hosted.id, "species", "Hosted Species")
    mutant = repo.create_facet(community.id, species.id, "mutant", "Mutant")
    x_men = repo.create_facet(community.id, affiliation.id, "x-men", "X-Men")
    hosted_facet = repo.create_facet(hosted.id, hosted_group.id, "mutant", "Hosted Mutant")

    repo.assign_character_facet(community.id, rogue.id, mutant.id)
    repo.assign_character_facet(community.id, rogue.id, x_men.id)
    repo.assign_board_facet(community.id, board.id, x_men.id)
    repo.assign_thread_facet(community.id, thread.id, x_men.id)
    repo.assign_thread_facet(community.id, second_thread.id, mutant.id)
    repo.assign_thread_facet(community.id, second_thread.id, x_men.id)

    assert [facet.slug for facet in repo.list_character_facets(community.id, rogue.id)] == [
        "mutant",
        "x-men",
    ]
    assert {
        character_id: [facet.slug for facet in facets]
        for character_id, facets in repo.list_character_facets_for_characters(
            community.id,
            [rogue.id],
        ).items()
    } == {rogue.id: ["mutant", "x-men"]}
    assert [facet.slug for facet in repo.list_board_facets(community.id, board.id)] == ["x-men"]
    assert {
        board_id: [facet.slug for facet in facets]
        for board_id, facets in repo.list_board_facets_for_boards(
            community.id,
            [board.id],
        ).items()
    } == {board.id: ["x-men"]}
    assert [facet.slug for facet in repo.list_thread_facets(community.id, thread.id)] == ["x-men"]
    assert repo.list_characters_by_ids(community.id, [rogue.id]) == {rogue.id: rogue}
    assert repo.list_memberships_by_ids(community.id, [membership.id]) == {
        membership.id: membership,
    }
    assert {
        thread_id: [facet.slug for facet in facets]
        for thread_id, facets in repo.list_thread_facets_for_threads(
            community.id,
            [thread.id, second_thread.id],
        ).items()
    } == {
        thread.id: ["x-men"],
        second_thread.id: ["mutant", "x-men"],
    }
    assert repo.list_character_ids_for_facets(community.id, [mutant.id, x_men.id]) == {rogue.id}
    assert repo.list_thread_ids_for_facets(community.id, [x_men.id]) == {
        thread.id,
        second_thread.id,
    }

    character_assignment_id = repo.connection.execute(
        """
        SELECT id
        FROM character_facets
        WHERE community_id = ? AND character_id = ? AND facet_id = ?
        """,
        (community.id, rogue.id, mutant.id),
    ).fetchone()["id"]
    board_assignment_id = repo.connection.execute(
        """
        SELECT id
        FROM board_facets
        WHERE community_id = ? AND board_id = ? AND facet_id = ?
        """,
        (community.id, board.id, x_men.id),
    ).fetchone()["id"]
    thread_assignment_id = repo.connection.execute(
        """
        SELECT id
        FROM thread_facets
        WHERE community_id = ? AND thread_id = ? AND facet_id = ?
        """,
        (community.id, thread.id, x_men.id),
    ).fetchone()["id"]
    repo.connection.execute(
        """
        UPDATE character_facets
        SET character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_character.id, community.id, character_assignment_id),
    )
    repo.connection.execute(
        """
        UPDATE board_facets
        SET facet_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_facet.id, community.id, board_assignment_id),
    )
    repo.connection.execute(
        """
        UPDATE thread_facets
        SET thread_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_thread.id, community.id, thread_assignment_id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("character_facets", character_assignment_id)] == (
        "character facet character belongs to another community"
    )
    assert issue_map[("board_facets", board_assignment_id)] == (
        "board facet facet belongs to another community"
    )
    assert issue_map[("thread_facets", thread_assignment_id)] == (
        "thread facet thread belongs to another community"
    )


def test_board_rollup_batch_reads_are_tenant_scoped(repo: ForumRepository) -> None:
    community = repo.get_community(1)
    role = repo.create_role(community.id, "rollup-member", "Rollup Member")
    user = repo.create_user("rollup@example.com", "hash")
    membership = repo.create_membership(community.id, user.id, role.id, "rollup", "Rollup")
    character = repo.create_character(community.id, membership.id, "rollup-face", "Rollup Face")
    parent = repo.create_board(community.id, "rollup-parent", "Rollup Parent")
    child = repo.create_board(
        community.id,
        "rollup-child",
        "Rollup Child",
        parent_board_id=parent.id,
    )
    other_parent = repo.create_board(community.id, "rollup-other", "Rollup Other")
    thread = repo.create_thread(community.id, parent.id, character.id, "rollup-scene", "Scene")
    child_thread = repo.create_thread(
        community.id,
        child.id,
        character.id,
        "rollup-child-scene",
        "Child Scene",
    )
    repo.create_post(community.id, thread.id, character.id, "First post.")
    repo.create_post(community.id, thread.id, character.id, "Second post.")
    repo.create_post(community.id, child_thread.id, character.id, "Child post.")
    repo.mark_thread_read(community.id, thread.id, membership.id, read_at=thread.updated_at)

    assert repo.list_child_boards_for_boards(community.id, [parent.id, other_parent.id]) == {
        parent.id: [child],
    }
    assert {
        board_id: [item.id for item in threads]
        for board_id, threads in repo.list_threads_for_boards(
            community.id,
            [parent.id, child.id],
        ).items()
    } == {
        parent.id: [thread.id],
        child.id: [child_thread.id],
    }
    assert repo.post_counts_by_thread(community.id, [thread.id, child_thread.id]) == {
        thread.id: 2,
        child_thread.id: 1,
    }
    assert repo.thread_read_at_for_threads(
        community.id,
        [thread.id, child_thread.id],
        membership.id,
    ) == {thread.id: thread.updated_at}


def test_network_catalog_batch_reads_are_tenant_scoped(repo: ForumRepository) -> None:
    community = repo.get_community(1)
    other = repo.create_community("catalog-other", "Catalog Other")
    community_premise = repo.create_material(
        community.id,
        "catalog-premise",
        "Catalog Premise",
        material_type="premise",
        summary="Public catalog pitch.",
    )
    other_premise = repo.create_material(
        other.id,
        "other-premise",
        "Other Premise",
        material_type="premise",
        summary="Other public catalog pitch.",
    )
    group = repo.create_facet_group(community.id, "mood", "Mood")
    facet = repo.create_facet(community.id, group.id, "superhero", "Superhero")
    repo.assign_material_facet(community.id, community_premise.id, facet.id)
    scene_hub = repo.create_board(community.id, "catalog-scenes", "Catalog Scenes")
    repo.create_board(other.id, "other-scenes", "Other Scenes")
    theme = repo.upsert_default_theme(
        community.id,
        slug="catalog-theme",
        name="Catalog Theme",
        tokens_json="{}",
    )
    other_theme = repo.upsert_default_theme(
        other.id,
        slug="catalog-theme",
        name="Other Catalog Theme",
        tokens_json="{}",
    )

    assert repo.public_scene_hub_community_ids([community.id]) == {community.id}
    assert repo.list_materials_for_communities([community.id]) == {
        community.id: [community_premise],
    }
    assert repo.list_material_facets_for_materials(
        [community.id],
        [community_premise.id, other_premise.id],
    ) == {(community.id, community_premise.id): [facet]}
    assert repo.list_facet_groups_for_communities([community.id]) == {community.id: [group]}
    assert repo.default_themes_for_communities([community.id]) == {community.id: theme}
    assert scene_hub.community_id == community.id

    with pytest.raises(LookupError, match="theme not found"):
        repo.set_default_theme(community.id, other_theme.id)

    repo.connection.execute(
        """
        UPDATE communities
        SET default_theme_id = ?
        WHERE id = ?
        """,
        (other_theme.id, community.id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("communities", community.id)] == (
        "community default theme belongs to another community"
    )


def test_network_membership_counts_batch_application_state(repo: ForumRepository) -> None:
    community = repo.get_community(1)
    role = repo.create_role(community.id, "network-member", "Network Member")
    user = repo.create_user("network@example.com", "hash")
    membership = repo.create_membership(community.id, user.id, role.id, "network", "Network")
    other_user = repo.create_user("network-other@example.com", "hash")
    other_membership = repo.create_membership(
        community.id,
        other_user.id,
        role.id,
        "network-other",
        "Network Other",
    )
    draft = repo.create_character(
        community.id,
        membership.id,
        "network-draft",
        "Network Draft",
        application_status="draft",
    )
    repo.create_character(
        community.id,
        other_membership.id,
        "network-submitted",
        "Network Submitted",
        application_status="submitted",
    )
    repo.create_character(
        community.id,
        other_membership.id,
        "network-accepted",
        "Network Accepted",
        application_status="accepted",
    )

    assert repo.list_communities_by_ids([community.id]) == {community.id: community}
    assert repo.roles_for_memberships([membership.id]) == {membership.id: role}
    assert repo.list_characters_for_memberships(community.id, [membership.id]) == {
        membership.id: [draft],
    }
    assert repo.network_membership_counts([membership.id]) == {
        membership.id: {
            "reviewable_application_count": 2,
            "own_application_count": 1,
            "plotting_room_count": 0,
        },
    }


def test_world_materials_are_tenant_scoped_and_facet_tagged(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    default_group = repo.create_facet_group(default.id, "affiliation", "Affiliation")
    hosted_group = repo.create_facet_group(hosted.id, "affiliation", "Affiliation")
    x_men = repo.create_facet(default.id, default_group.id, "x-men", "X-Men")
    hosted_x_men = repo.create_facet(hosted.id, hosted_group.id, "x-men", "X-Men Elsewhere")

    premise = repo.create_material(
        default.id,
        "premise",
        "Premise",
        material_type="premise",
        summary="The core hook.",
        body="Mutants face a new machine.",
        is_featured=True,
    )
    repo.create_material(
        hosted.id,
        "premise",
        "Hosted Premise",
        material_type="premise",
        summary="Different world.",
    )
    repo.assign_material_facet(default.id, premise.id, x_men.id)
    updated = repo.update_material(
        default.id,
        premise.id,
        title="Updated Premise",
        material_type="premise",
        summary="Sharper hook.",
        body="Mutants face a machine with a budget.",
        status="published",
        sort_order=5,
        is_featured=False,
    )

    assert updated.title == "Updated Premise"
    assert updated.summary == "Sharper hook."
    assert updated.is_featured is False
    assert repo.get_material_by_slug(default.id, "premise").title == "Updated Premise"
    assert repo.get_material_by_slug(hosted.id, "premise").title == "Hosted Premise"
    assert [material.title for material in repo.list_materials(default.id)] == ["Updated Premise"]
    assert [facet.slug for facet in repo.list_material_facets(default.id, premise.id)] == ["x-men"]

    with pytest.raises(LookupError):
        repo.assign_material_facet(hosted.id, premise.id, x_men.id)

    material_assignment_id = repo.connection.execute(
        """
        SELECT id
        FROM material_facets
        WHERE community_id = ? AND material_id = ? AND facet_id = ?
        """,
        (default.id, premise.id, x_men.id),
    ).fetchone()["id"]
    repo.connection.execute(
        """
        UPDATE material_facets
        SET facet_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_x_men.id, default.id, material_assignment_id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("material_facets", material_assignment_id)] == (
        "material facet facet belongs to another community"
    )


def test_wanted_ads_are_tenant_scoped_and_facet_tagged(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    default_user = repo.create_user("default@example.com", "hash")
    hosted_user = repo.create_user("hosted@example.com", "hash")
    default_membership = repo.create_membership(
        default.id,
        default_user.id,
        default_role.id,
        "writer",
        "Writer",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        hosted_user.id,
        hosted_role.id,
        "hosted",
        "Hosted",
    )
    rogue = repo.create_character(default.id, default_membership.id, "rogue", "Rogue")
    magneto = repo.create_character(default.id, default_membership.id, "magneto", "Magneto")
    hosted_character = repo.create_character(
        hosted.id,
        hosted_membership.id,
        "rogue",
        "Rogue Elsewhere",
    )
    group = repo.create_facet_group(default.id, "affiliation", "Affiliation")
    hosted_group = repo.create_facet_group(hosted.id, "affiliation", "Hosted Affiliation")
    x_men = repo.create_facet(default.id, group.id, "x-men", "X-Men")
    hosted_x_men = repo.create_facet(hosted.id, hosted_group.id, "x-men", "Hosted X-Men")

    wanted = repo.create_wanted_ad(
        default.id,
        default_membership.id,
        "rogue-rival",
        "Rogue rival",
        creator_character_id=rogue.id,
        summary="A sharp foil.",
    )
    repo.create_wanted_ad(
        hosted.id,
        hosted_membership.id,
        "rogue-rival",
        "Hosted rival",
        creator_character_id=hosted_character.id,
    )
    repo.add_wanted_ad_related_character(default.id, wanted.id, magneto.id)
    repo.assign_wanted_ad_facet(default.id, wanted.id, x_men.id)
    interest = repo.create_wanted_ad_interest(
        default.id,
        wanted.id,
        default_membership.id,
        magneto.id,
    )
    notification = repo.create_notification(
        default.id,
        default_membership.id,
        kind="wanted_interest",
        wanted_ad_id=wanted.id,
        wanted_ad_interest_id=interest.id,
        actor_membership_id=default_membership.id,
        actor_character_id=magneto.id,
    )
    hosted_wanted = repo.get_wanted_ad_by_slug(hosted.id, "rogue-rival")

    assert repo.get_wanted_ad_by_slug(default.id, "rogue-rival").title == "Rogue rival"
    assert hosted_wanted.title == "Hosted rival"
    assert [item.title for item in repo.list_wanted_ads(default.id)] == ["Rogue rival"]
    assert [facet.slug for facet in repo.list_wanted_ad_facets(default.id, wanted.id)] == ["x-men"]
    assert repo.list_wanted_ad_facets_for_wanted_ads(default.id, [wanted.id]) == {
        wanted.id: [x_men],
    }
    assert repo.list_wanted_ad_related_characters(default.id, wanted.id) == [magneto]
    assert repo.list_wanted_ad_interests(default.id, wanted.id) == [interest]
    assert repo.list_wanted_ads_for_character(default.id, rogue.id) == [wanted]
    assert repo.list_wanted_ads_for_character(default.id, magneto.id) == [wanted]
    assert notification.wanted_ad_id == wanted.id
    assert notification.wanted_ad_interest_id == interest.id
    reserved_interest = repo.update_wanted_ad_interest_status(default.id, interest.id, "reserved")
    reserved_wanted = repo.update_wanted_ad_status(default.id, wanted.id, "reserved")
    assert reserved_interest.status == "reserved"
    assert reserved_wanted.status == "reserved"
    reserve = repo.create_character_reserve(
        default.id,
        default_membership.id,
        magneto.id,
        "Rogue rival",
        wanted_ad_id=wanted.id,
        wanted_ad_interest_id=interest.id,
        notes="Reserved from wanted hook: Rogue rival",
    )
    assert repo.get_character_reserve_for_wanted_interest(default.id, interest.id) == reserve
    assert repo.list_character_reserves(default.id, magneto.id) == [reserve]
    assert repo.list_character_reserves_for_wanted_ad(default.id, wanted.id) == [reserve]
    assert repo.list_character_reserves_for_community(default.id) == [reserve]
    assert repo.list_character_reserves_for_community(hosted.id) == []

    with pytest.raises(LookupError):
        repo.assign_wanted_ad_facet(hosted.id, wanted.id, x_men.id)
    with pytest.raises(LookupError):
        repo.create_wanted_ad_interest(
            hosted.id, wanted.id, hosted_membership.id, hosted_character.id
        )
    with pytest.raises(LookupError):
        repo.create_character_reserve(
            hosted.id,
            hosted_membership.id,
            hosted_character.id,
            "Wrong forum",
            wanted_ad_id=wanted.id,
        )

    wanted_facet_assignment_id = repo.connection.execute(
        """
        SELECT id
        FROM wanted_ad_facets
        WHERE community_id = ? AND wanted_ad_id = ? AND facet_id = ?
        """,
        (default.id, wanted.id, x_men.id),
    ).fetchone()["id"]
    related_character_id = repo.connection.execute(
        """
        SELECT id
        FROM wanted_ad_related_characters
        WHERE community_id = ? AND wanted_ad_id = ? AND character_id = ?
        """,
        (default.id, wanted.id, magneto.id),
    ).fetchone()["id"]
    repo.connection.execute(
        """
        UPDATE wanted_ad_facets
        SET facet_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_x_men.id, default.id, wanted_facet_assignment_id),
    )
    repo.connection.execute(
        """
        UPDATE wanted_ad_related_characters
        SET character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_character.id, default.id, related_character_id),
    )
    repo.connection.execute(
        """
        UPDATE character_reserves
        SET membership_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_membership.id, default.id, reserve.id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("character_reserves", reserve.id)] == (
        "character reserve membership belongs to another community"
    )
    assert issue_map[("wanted_ad_facets", wanted_facet_assignment_id)] == (
        "wanted hook facet facet belongs to another community"
    )
    assert issue_map[("wanted_ad_related_characters", related_character_id)] == (
        "wanted related face character belongs to another community"
    )

    repo.connection.execute(
        """
        UPDATE wanted_ads
        SET creator_character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_character.id, default.id, wanted.id),
    )
    repo.connection.execute(
        """
        UPDATE wanted_ad_interests
        SET wanted_ad_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_wanted.id, default.id, interest.id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("wanted_ads", wanted.id)] == (
        "wanted hook creator character does not match community and membership"
    )
    assert issue_map[("wanted_ad_interests", interest.id)] == (
        "wanted interest wanted hook belongs to another community"
    )


def test_plot_hooks_and_prospective_wanted_interest_are_tenant_scoped(
    repo: ForumRepository,
) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    owner_user = repo.create_user("owner@example.com", "hash")
    prospect_user = repo.create_user("prospect@example.com", "hash")
    hosted_user = repo.create_user("hosted-prospect@example.com", "hash")
    owner = repo.create_membership(default.id, owner_user.id, role.id, "owner", "Owner")
    prospect = repo.create_membership(
        default.id,
        prospect_user.id,
        role.id,
        "prospect",
        "Prospect",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        hosted_user.id,
        hosted_role.id,
        "prospect",
        "Hosted Prospect",
    )
    rogue = repo.create_character(default.id, owner.id, "rogue", "Rogue")
    gambit = repo.create_character(default.id, prospect.id, "gambit", "Gambit")
    hosted_character = repo.create_character(hosted.id, hosted_membership.id, "rogue", "Rogue")
    group = repo.create_facet_group(default.id, "affiliation", "Affiliation")
    hosted_group = repo.create_facet_group(hosted.id, "affiliation", "Hosted Affiliation")
    x_men = repo.create_facet(default.id, group.id, "x-men", "X-Men")
    hosted_x_men = repo.create_facet(hosted.id, hosted_group.id, "x-men", "Hosted X-Men")

    hook = repo.create_character_plot_hook(
        default.id,
        owner.id,
        rogue.id,
        "old-ghosts",
        "Old ghosts",
        hook_type="relationship",
        summary="A pressure point.",
    )
    hosted_hook = repo.create_character_plot_hook(
        hosted.id,
        hosted_membership.id,
        hosted_character.id,
        "old-ghosts",
        "Hosted ghosts",
    )
    repo.assign_character_plot_hook_facet(default.id, hook.id, x_men.id)
    interest = repo.create_character_plot_hook_interest(
        default.id,
        hook.id,
        prospect.id,
        gambit.id,
    )
    notification = repo.create_notification(
        default.id,
        owner.id,
        kind="plot_hook_interest",
        character_plot_hook_id=hook.id,
        actor_membership_id=prospect.id,
        actor_character_id=gambit.id,
    )

    wanted = repo.create_wanted_ad(
        default.id,
        owner.id,
        "gambit-wanted",
        "Gambit wanted",
        creator_character_id=rogue.id,
    )
    prospective = repo.create_wanted_ad_interest(
        default.id,
        wanted.id,
        prospect.id,
        prospective_character_name="Remy LeBeau",
        note="I would app him for this.",
    )
    room = repo.create_plotting_room(
        default.id,
        owner.id,
        "Old ghosts: Gambit",
        source_plot_hook_id=hook.id,
        source_plot_hook_interest_id=interest.id,
        summary="Planning the pressure point.",
    )
    owner_participant = repo.create_plotting_room_participant(
        default.id,
        room.id,
        owner.id,
        character_id=rogue.id,
        participant_role="owner",
    )
    prospect_participant = repo.create_plotting_room_participant(
        default.id,
        room.id,
        prospect.id,
        character_id=gambit.id,
    )
    room_notification = repo.create_notification(
        default.id,
        prospect.id,
        kind="plotting_room_created",
        plotting_room_id=room.id,
        actor_membership_id=owner.id,
        actor_character_id=rogue.id,
    )
    duplicate = repo.create_wanted_ad_interest(
        default.id,
        wanted.id,
        prospect.id,
        prospective_character_name="Remy LeBeau",
    )

    assert repo.get_character_plot_hook_by_slug(default.id, rogue.id, "old-ghosts") == hook
    assert (
        repo.get_character_plot_hook_by_slug(hosted.id, hosted_character.id, "old-ghosts").title
        == "Hosted ghosts"
    )
    assert repo.list_character_plot_hooks_for_character(default.id, rogue.id) == [hook]
    assert repo.list_character_plot_hook_facets(default.id, hook.id) == [x_men]
    assert repo.list_character_plot_hook_ids_for_facets(default.id, [x_men.id]) == {hook.id}
    assert interest.character_id == gambit.id
    assert notification.character_plot_hook_id == hook.id
    assert prospective.character_id is None
    assert prospective.prospective_character_name == "Remy LeBeau"
    assert duplicate.id == prospective.id
    assert repo.get_plotting_room_for_plot_hook_interest(default.id, interest.id) == room
    assert repo.list_plotting_rooms_for_membership(default.id, prospect.id) == [room]
    assert repo.list_plotting_rooms_for_character(default.id, rogue.id) == [room]
    assert repo.list_plotting_room_participants(default.id, room.id) == [
        owner_participant,
        prospect_participant,
    ]
    assert room_notification.plotting_room_id == room.id
    default_board = repo.create_board(default.id, "planning-board", "Planning Board")
    hosted_board = repo.create_board(hosted.id, "planning-board", "Hosted Planning Board")
    planned_room = repo.update_plotting_room_plan(
        default.id,
        room.id,
        notes="Rogue and Gambit decide where the first spark lands.",
        next_step="Open a scene.",
        target_board_id=default_board.id,
        status="ready",
    )
    default_thread = repo.create_thread(
        default.id,
        default_board.id,
        rogue.id,
        "old-ghosts",
        "Old ghosts",
    )
    threaded_room = repo.attach_plotting_room_thread(default.id, room.id, default_thread.id)
    message = repo.create_plotting_room_message(
        default.id,
        room.id,
        owner.id,
        "This should start after the gala.",
        author_character_id=rogue.id,
    )

    assert planned_room.notes == "Rogue and Gambit decide where the first spark lands."
    assert planned_room.next_step == "Open a scene."
    assert planned_room.target_board_id == default_board.id
    assert threaded_room.target_thread_id == default_thread.id
    assert threaded_room.status == "threaded"
    assert repo.list_plotting_room_messages(default.id, room.id) == [message]

    with pytest.raises(LookupError):
        repo.assign_character_plot_hook_facet(hosted.id, hook.id, x_men.id)
    with pytest.raises(LookupError):
        repo.create_wanted_ad_interest(hosted.id, wanted.id, hosted_membership.id)
    with pytest.raises(LookupError):
        repo.create_plotting_room(
            hosted.id,
            hosted_membership.id,
            "Crossed room",
            source_plot_hook_id=hook.id,
            source_plot_hook_interest_id=interest.id,
        )
    with pytest.raises(LookupError):
        repo.update_plotting_room_plan(
            default.id,
            room.id,
            notes="Crossed target.",
            next_step="Nope.",
            target_board_id=hosted_board.id,
            status="ready",
        )
    hosted_thread = repo.create_thread(
        hosted.id,
        hosted_board.id,
        hosted_character.id,
        "hosted-old-ghosts",
        "Hosted old ghosts",
    )
    with pytest.raises(LookupError):
        repo.attach_plotting_room_thread(default.id, room.id, hosted_thread.id)
    with pytest.raises(LookupError):
        repo.create_plotting_room_message(
            hosted.id,
            room.id,
            hosted_membership.id,
            "Wrong room.",
        )
    with pytest.raises(LookupError):
        repo.create_plotting_room_participant(
            hosted.id,
            room.id,
            hosted_membership.id,
            character_id=hosted_character.id,
        )
    with pytest.raises(LookupError):
        repo.create_plotting_room_participant(
            default.id,
            room.id,
            hosted_membership.id,
            character_id=hosted_character.id,
        )
    with pytest.raises(TenantBoundaryError):
        repo.create_plotting_room_participant(
            default.id,
            room.id,
            owner.id,
            character_id=gambit.id,
        )
    with pytest.raises(TenantBoundaryError):
        repo.create_plotting_room_message(
            default.id,
            room.id,
            owner.id,
            "Wrong face.",
            author_character_id=gambit.id,
        )

    hook_facet_assignment_id = repo.connection.execute(
        """
        SELECT id
        FROM character_plot_hook_facets
        WHERE community_id = ? AND plot_hook_id = ? AND facet_id = ?
        """,
        (default.id, hook.id, x_men.id),
    ).fetchone()["id"]
    repo.connection.execute(
        """
        UPDATE character_plot_hook_facets
        SET facet_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_x_men.id, default.id, hook_facet_assignment_id),
    )
    repo.connection.execute(
        """
        UPDATE character_plot_hooks
        SET character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_character.id, default.id, hook.id),
    )
    repo.connection.execute(
        """
        UPDATE character_plot_hook_interests
        SET plot_hook_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_hook.id, default.id, interest.id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("character_plot_hooks", hook.id)] == (
        "plot hook character does not match community and membership"
    )
    assert issue_map[("character_plot_hook_interests", interest.id)] == (
        "plot hook interest hook belongs to another community"
    )
    assert issue_map[("character_plot_hook_facets", hook_facet_assignment_id)] == (
        "plot hook facet facet belongs to another community"
    )


def test_plotting_room_participants_are_unique_for_nullable_identity(
    repo: ForumRepository,
) -> None:
    default = repo.get_community(1)
    role = repo.create_role(default.id, "member", "Member")
    owner_user = repo.create_user("room-owner@example.com", "hash")
    prospect_user = repo.create_user("room-prospect@example.com", "hash")
    owner = repo.create_membership(default.id, owner_user.id, role.id, "owner", "Owner")
    prospect = repo.create_membership(
        default.id,
        prospect_user.id,
        role.id,
        "prospect",
        "Prospect",
    )
    wanted = repo.create_wanted_ad(default.id, owner.id, "casting-room", "Casting room")
    interest = repo.create_wanted_ad_interest(
        default.id,
        wanted.id,
        prospect.id,
        prospective_character_name="Remy LeBeau",
    )
    room = repo.create_plotting_room(
        default.id,
        owner.id,
        "Casting room",
        source_wanted_ad_id=wanted.id,
        source_wanted_ad_interest_id=interest.id,
    )

    owner_participant = repo.create_plotting_room_participant(default.id, room.id, owner.id)
    duplicate_owner = repo.create_plotting_room_participant(default.id, room.id, owner.id)
    prospect_participant = repo.create_plotting_room_participant(
        default.id,
        room.id,
        prospect.id,
        prospective_character_name="Remy LeBeau",
    )
    duplicate_prospect = repo.create_plotting_room_participant(
        default.id,
        room.id,
        prospect.id,
        prospective_character_name="Remy LeBeau",
    )

    assert duplicate_owner == owner_participant
    assert duplicate_prospect == prospect_participant
    assert repo.list_plotting_room_participants(default.id, room.id) == [
        owner_participant,
        prospect_participant,
    ]


def test_repository_rejects_unknown_story_vocabulary(repo: ForumRepository) -> None:
    community = repo.get_community(1)
    role = repo.create_role(community.id, "member", "Member")
    user = repo.create_user("vocabulary@example.com", "hash")
    membership = repo.create_membership(community.id, user.id, role.id, "writer", "Writer")
    character = repo.create_character(community.id, membership.id, "rogue", "Rogue")
    material = repo.create_material(
        community.id,
        "premise",
        "Premise",
        material_type="premise",
        summary="A valid director material.",
    )
    hook = repo.create_character_plot_hook(
        community.id,
        membership.id,
        character.id,
        "open-scene",
        "Open scene",
        hook_type="scene",
    )

    with pytest.raises(ValueError, match="material_type must be one of:"):
        repo.create_material(community.id, "cms-page", "CMS Page", material_type="cms_page")
    with pytest.raises(ValueError, match="material_type must be one of:"):
        repo.update_material(
            community.id,
            material.id,
            title=material.title,
            material_type="cms_page",
            summary=material.summary,
            body=material.body,
        )
    with pytest.raises(ValueError, match="wanted_type must be one of:"):
        repo.create_wanted_ad(
            community.id,
            membership.id,
            "generic-listing",
            "Generic listing",
            wanted_type="generic_listing",
        )
    with pytest.raises(ValueError, match="hook_type must be one of:"):
        repo.create_character_plot_hook(
            community.id,
            membership.id,
            character.id,
            "generic-hook",
            "Generic hook",
            hook_type="generic_hook",
        )
    with pytest.raises(ValueError, match="hook_type must be one of:"):
        repo.update_character_plot_hook(
            community.id,
            hook.id,
            title=hook.title,
            hook_type="generic_hook",
            summary=hook.summary,
            body=hook.body,
            status=hook.status,
        )


def test_threads_and_posts_cannot_cross_community_boundaries(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    user = repo.create_user("writer@example.com", "hash")

    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    default_membership = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "lark",
        "Lark",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "lark",
        "Lark Elsewhere",
    )
    default_character = repo.create_character(default.id, default_membership.id, "rogue", "Rogue")
    hosted_character = repo.create_character(hosted.id, hosted_membership.id, "magneto", "Magneto")
    default_board = repo.create_board(default.id, "ic", "In Character")
    hosted_board = repo.create_board(hosted.id, "ic", "In Character")

    thread = repo.create_thread(
        default.id,
        default_board.id,
        default_character.id,
        "opening-scene",
        "Opening Scene",
    )
    repo.create_thread(
        hosted.id,
        hosted_board.id,
        hosted_character.id,
        "opening-scene",
        "Opening Scene Elsewhere",
    )
    second_thread = repo.create_thread(
        default.id,
        default_board.id,
        default_character.id,
        "second-scene",
        "Second Scene",
    )
    post = repo.create_post(default.id, thread.id, default_character.id, "First post.")
    reply = repo.create_post(default.id, thread.id, default_character.id, "Second post.")
    second_thread_post = repo.create_post(
        default.id,
        second_thread.id,
        default_character.id,
        "Other scene opener.",
    )

    assert sorted(item.title for item in repo.list_threads(default.id)) == [
        "Opening Scene",
        "Second Scene",
    ]
    assert repo.get_thread(default.id, thread.id).author_character_id == default_character.id
    assert [item.body for item in repo.list_posts(default.id, thread.id)] == [
        "First post.",
        "Second post.",
    ]
    assert post.author_character_id == default_character.id
    assert post.author_membership_id == default_membership.id
    assert (post.post_number, reply.post_number, second_thread_post.post_number) == (1, 2, 1)
    assert repo.get_post_by_number(default.id, thread.id, 2) == reply

    with pytest.raises(LookupError):
        repo.create_thread(default.id, hosted_board.id, default_character.id, "bad", "Bad")

    with pytest.raises(LookupError):
        repo.create_post(hosted.id, post.id, hosted_character.id, "Wrong community.")


def test_concurrent_post_creation_assigns_unique_post_numbers(tmp_path) -> None:
    connection = connect(tmp_path / "forum.sqlite3", check_same_thread=False)
    try:
        create_schema(connection)
        repository = ForumRepository(connection)
        community = repository.seed_default_community()
        user = repository.create_user("writer@example.com", "hash")
        role = repository.create_role(community.id, "member", "Member")
        membership = repository.create_membership(
            community.id,
            user.id,
            role.id,
            "lark",
            "Lark",
        )
        character = repository.create_character(community.id, membership.id, "rogue", "Rogue")
        board = repository.create_board(community.id, "ic", "In Character")
        thread = repository.create_thread(
            community.id,
            board.id,
            character.id,
            "opening-scene",
            "Opening Scene",
        )

        def create_reply(index: int) -> int:
            return repository.create_post(
                community.id,
                thread.id,
                character.id,
                f"Concurrent beat {index}.",
            ).post_number

        with ThreadPoolExecutor(max_workers=4) as executor:
            post_numbers = list(executor.map(create_reply, range(8)))

        posts = repository.list_posts(community.id, thread.id)
    finally:
        connection.close()

    assert sorted(post_numbers) == list(range(1, 9))
    assert [post.post_number for post in posts] == list(range(1, 9))


def test_thread_flags_sort_pinned_threads_first(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    user = repo.create_user("flags@example.com", "hash")
    role = repo.create_role(default.id, "member", "Member")
    membership = repo.create_membership(default.id, user.id, role.id, "flags", "Flags")
    character = repo.create_character(default.id, membership.id, "rogue", "Rogue")
    board = repo.create_board(default.id, "ic", "In Character")

    regular = repo.create_thread(default.id, board.id, character.id, "regular", "Regular")
    pinned = repo.create_thread(
        default.id,
        board.id,
        character.id,
        "pinned",
        "Pinned",
        is_pinned=True,
    )
    locked = repo.update_thread_flags(default.id, regular.id, is_locked=True)

    assert locked.is_locked is True
    assert [thread.slug for thread in repo.list_threads(default.id, board.id)] == [
        pinned.slug,
        regular.slug,
    ]


def test_thread_scene_metadata_and_participants_are_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    user = repo.create_user("scene@example.com", "hash")
    hosted_user = repo.create_user("hosted-scene@example.com", "hash")
    role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    membership = repo.create_membership(default.id, user.id, role.id, "scene", "Scene")
    hosted_membership = repo.create_membership(
        hosted.id,
        hosted_user.id,
        hosted_role.id,
        "scene",
        "Scene Elsewhere",
    )
    rogue = repo.create_character(default.id, membership.id, "rogue", "Rogue")
    storm = repo.create_character(default.id, membership.id, "storm", "Storm")
    gambit = repo.create_character(default.id, membership.id, "gambit", "Gambit")
    hosted_rogue = repo.create_character(hosted.id, hosted_membership.id, "rogue", "Rogue")
    board = repo.create_board(default.id, "ic", "In Character")
    hosted_board = repo.create_board(hosted.id, "ic", "In Character")

    thread = repo.create_thread(
        default.id,
        board.id,
        rogue.id,
        "moonlight",
        "Moonlight",
        status="open",
        location="Lake",
        timeline="Night",
        summary="A quiet lakeside scene.",
        posting_mode="posting_order",
    )
    repo.create_thread(hosted.id, hosted_board.id, hosted_rogue.id, "moonlight", "Moonlight")
    repo.set_thread_participants(default.id, thread.id, [rogue.id, storm.id])

    stored = repo.get_thread(default.id, thread.id)
    assert stored.status == "open"
    assert stored.location == "Lake"
    assert stored.timeline == "Night"
    assert stored.summary == "A quiet lakeside scene."
    assert stored.posting_mode == "posting_order"
    assert [
        character.slug for character in repo.list_thread_participants(default.id, thread.id)
    ] == [
        "rogue",
        "storm",
    ]
    repo.create_post(default.id, thread.id, gambit.id, "Gambit joins the scene.")
    assert {
        character.slug for character in repo.list_thread_participants(default.id, thread.id)
    } == {"rogue", "storm", "gambit"}
    repo.set_thread_participants(default.id, thread.id, [rogue.id])
    assert {
        character.slug for character in repo.list_thread_participants(default.id, thread.id)
    } == {"rogue", "gambit"}

    with pytest.raises(LookupError):
        repo.add_thread_participant(default.id, thread.id, hosted_rogue.id)


def test_thread_reads_are_membership_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    user = repo.create_user("reads@example.com", "hash")
    other_user = repo.create_user("other-reads@example.com", "hash")
    role = repo.create_role(default.id, "member", "Member")
    membership = repo.create_membership(default.id, user.id, role.id, "reader", "Reader")
    other_membership = repo.create_membership(
        default.id,
        other_user.id,
        role.id,
        "other-reader",
        "Other Reader",
    )
    character = repo.create_character(default.id, membership.id, "rogue", "Rogue")
    board = repo.create_board(default.id, "ic", "In Character")
    thread = repo.create_thread(default.id, board.id, character.id, "scene", "Scene")

    repo.mark_thread_read(default.id, thread.id, membership.id, read_at="2026-01-01T00:00:00+00:00")

    assert repo.get_thread_read_at(default.id, thread.id, membership.id) == (
        "2026-01-01T00:00:00+00:00"
    )
    assert repo.get_thread_read_at(default.id, thread.id, other_membership.id) is None


def test_thread_read_and_watch_boundaries_are_tenant_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted-thread-state", "Hosted Thread State")
    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    default_membership = repo.create_membership(
        default.id,
        repo.create_user("thread-state@example.com", "hash").id,
        default_role.id,
        "thread-state",
        "Thread State",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        repo.create_user("hosted-thread-state@example.com", "hash").id,
        hosted_role.id,
        "hosted-thread-state",
        "Hosted Thread State",
    )
    default_character = repo.create_character(
        default.id,
        default_membership.id,
        "thread-state",
        "Thread State",
    )
    hosted_character = repo.create_character(
        hosted.id,
        hosted_membership.id,
        "hosted-thread-state",
        "Hosted Thread State",
    )
    default_board = repo.create_board(default.id, "thread-state", "Thread State")
    hosted_board = repo.create_board(hosted.id, "thread-state", "Hosted Thread State")
    default_thread = repo.create_thread(
        default.id,
        default_board.id,
        default_character.id,
        "thread-state",
        "Thread State",
    )
    second_default_thread = repo.create_thread(
        default.id,
        default_board.id,
        default_character.id,
        "thread-state-two",
        "Thread State Two",
    )
    hosted_thread = repo.create_thread(
        hosted.id,
        hosted_board.id,
        hosted_character.id,
        "hosted-thread-state",
        "Hosted Thread State",
    )

    repo.mark_thread_read(default.id, default_thread.id, default_membership.id)
    repo.mark_thread_read(default.id, second_default_thread.id, default_membership.id)
    repo.watch_thread(default.id, default_thread.id, default_membership.id)
    repo.watch_thread(default.id, second_default_thread.id, default_membership.id)

    with pytest.raises(LookupError, match="thread not found"):
        repo.unwatch_thread(default.id, hosted_thread.id, default_membership.id)
    with pytest.raises(LookupError, match="membership not found"):
        repo.unwatch_thread(default.id, default_thread.id, hosted_membership.id)
    repo.unwatch_thread(default.id, default_thread.id, default_membership.id)
    with pytest.raises(LookupError, match="thread watch not found"):
        repo.get_thread_watch(default.id, default_thread.id, default_membership.id)

    read_id = repo.connection.execute(
        """
        SELECT id
        FROM thread_reads
        WHERE community_id = ? AND thread_id = ? AND membership_id = ?
        """,
        (default.id, second_default_thread.id, default_membership.id),
    ).fetchone()["id"]
    watch_id = repo.connection.execute(
        """
        SELECT id
        FROM thread_watches
        WHERE community_id = ? AND thread_id = ? AND membership_id = ?
        """,
        (default.id, second_default_thread.id, default_membership.id),
    ).fetchone()["id"]
    repo.connection.execute(
        """
        UPDATE thread_reads
        SET thread_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_thread.id, default.id, read_id),
    )
    repo.connection.execute(
        """
        UPDATE thread_watches
        SET membership_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_membership.id, default.id, watch_id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("thread_reads", read_id)] == (
        "thread read thread belongs to another community"
    )
    assert issue_map[("thread_watches", watch_id)] == (
        "thread watch membership belongs to another community"
    )


def test_post_revisions_are_scoped_by_community(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    user = repo.create_user("revisions@example.com", "hash")
    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    default_membership = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "writer",
        "Writer",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "writer",
        "Writer Elsewhere",
    )
    default_character = repo.create_character(default.id, default_membership.id, "rogue", "Rogue")
    hosted_character = repo.create_character(hosted.id, hosted_membership.id, "rogue", "Rogue")
    default_board = repo.create_board(default.id, "ic", "In Character")
    hosted_board = repo.create_board(hosted.id, "ic", "In Character")
    default_thread = repo.create_thread(
        default.id, default_board.id, default_character.id, "a", "A"
    )
    hosted_thread = repo.create_thread(hosted.id, hosted_board.id, hosted_character.id, "a", "A")
    default_post = repo.create_post(default.id, default_thread.id, default_character.id, "Before.")
    hosted_post = repo.create_post(hosted.id, hosted_thread.id, hosted_character.id, "Before.")

    default_revision = repo.create_post_revision(
        default.id,
        default_post.id,
        default_membership.id,
        "Before.",
        "After.",
    )
    hosted_revision = repo.create_post_revision(
        hosted.id,
        hosted_post.id,
        hosted_membership.id,
        "Before.",
        "Elsewhere.",
    )

    assert [
        revision.new_body for revision in repo.list_post_revisions(default.id, default_post.id)
    ] == ["After."]
    assert [
        revision.new_body for revision in repo.list_post_revisions(hosted.id, hosted_post.id)
    ] == ["Elsewhere."]
    assert default_revision.community_id == default.id
    assert hosted_revision.community_id == hosted.id
    editor_revision = repo.create_post_revision(
        default.id,
        default_post.id,
        default_membership.id,
        "After.",
        "After with a typo fix.",
    )

    with pytest.raises(LookupError):
        repo.create_post_revision(
            default.id,
            hosted_post.id,
            default_membership.id,
            "Wrong.",
            "Wrong.",
        )
    with pytest.raises(LookupError):
        repo.create_post_revision(
            default.id,
            default_post.id,
            hosted_membership.id,
            "Wrong.",
            "Wrong.",
        )

    repo.connection.execute(
        """
        UPDATE post_revisions
        SET post_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_post.id, default.id, default_revision.id),
    )
    repo.connection.execute(
        """
        UPDATE post_revisions
        SET editor_membership_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hosted_membership.id, default.id, editor_revision.id),
    )
    repo.connection.commit()

    issue_map = {
        (issue.table_name, issue.row_id): issue.reason
        for issue in repo.list_tenant_pair_integrity_issues()
    }

    assert issue_map[("post_revisions", default_revision.id)] == (
        "post revision post belongs to another community"
    )
    assert issue_map[("post_revisions", editor_revision.id)] == (
        "post revision editor membership belongs to another community"
    )
