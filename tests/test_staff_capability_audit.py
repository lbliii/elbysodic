from __future__ import annotations

import sqlite3

import pytest

from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.db.migrations import CURRENT_SCHEMA_VERSION
from elbysodic.db.seed import DemoSeed, resolve_seed_persona
from elbysodic.domain.capabilities import STAFF_CAPABILITIES
from elbysodic.services import AppServices, create_services


@pytest.fixture
def repo() -> ForumRepository:
    connection = connect()
    create_schema(connection)
    repository = ForumRepository(connection)
    repository.seed_default_community()
    return repository


def test_roles_persist_partial_community_scoped_capabilities(repo: ForumRepository) -> None:
    first = repo.get_community(1)
    second = repo.create_community("second-capability-realm", "Second Capability Realm")
    reviewer = repo.create_role(
        first.id,
        "application-reviewer",
        "Application Reviewer",
        capabilities={"manage_applications"},
    )
    writer = repo.create_role(second.id, "writer", "Writer")
    user = repo.create_user("scoped-capabilities@example.com", "hash")
    first_membership = repo.create_membership(
        first.id, user.id, reviewer.id, "reviewer", "Reviewer"
    )
    second_membership = repo.create_membership(second.id, user.id, writer.id, "writer", "Writer")

    assert repo.get_role(first.id, reviewer.id).capabilities == frozenset({"manage_applications"})
    assert repo.roles_for_memberships([first_membership.id, second_membership.id]) == {
        first_membership.id: reviewer,
        second_membership.id: writer,
    }
    assert repo.set_role_capabilities(
        first.id,
        reviewer.id,
        {"manage_applications", "manage_casting"},
    ).capabilities == frozenset({"manage_applications", "manage_casting"})

    with pytest.raises(ValueError, match="unknown staff capabilities"):
        repo.set_role_capabilities(first.id, reviewer.id, {"manage_everything"})
    with pytest.raises(LookupError):
        repo.set_role_capabilities(second.id, reviewer.id, {"manage_applications"})


def test_legacy_director_role_defaults_to_every_capability(repo: ForumRepository) -> None:
    role = repo.create_role(1, "director", "Director", is_admin=True)

    assert role.capabilities == STAFF_CAPABILITIES

    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        repo.connection.execute(
            """
            INSERT INTO role_capabilities (community_id, role_id, capability, created_at)
            VALUES (?, ?, 'manage_everything', 'now')
            """,
            (1, role.id),
        )


def test_staff_audit_events_are_tenant_and_actor_scoped(repo: ForumRepository) -> None:
    first = repo.get_community(1)
    second = repo.create_community("audit-second", "Audit Second")
    first_role = repo.create_role(first.id, "director", "Director", is_admin=True)
    second_role = repo.create_role(second.id, "director", "Director", is_admin=True)
    user = repo.create_user("audit@example.com", "hash")
    first_membership = repo.create_membership(
        first.id, user.id, first_role.id, "director", "Director"
    )
    second_membership = repo.create_membership(
        second.id, user.id, second_role.id, "director", "Director"
    )
    first_face = repo.create_character(
        first.id, first_membership.id, "director-face", "Director Face"
    )

    event = repo.create_staff_audit_event(
        first.id,
        first_membership.id,
        actor_character_id=first_face.id,
        capability="manage_applications",
        target_family="application",
        target_id=42,
        action="application_accepted",
        outcome="accepted",
        public_aftermath="face accepted for play",
    )

    assert repo.list_staff_audit_events(first.id, capability="manage_applications") == [event]
    assert repo.list_staff_audit_events(second.id) == []
    with pytest.raises(LookupError):
        repo.get_staff_audit_event(second.id, event.id)
    with pytest.raises(LookupError):
        repo.create_staff_audit_event(
            first.id,
            second_membership.id,
            capability="manage_world",
            target_family="community",
            action="community_updated",
            outcome="accepted",
        )
    with pytest.raises(ValueError, match="does not belong"):
        repo.create_staff_audit_event(
            first.id,
            first_membership.id,
            actor_character_id=repo.create_character(
                first.id,
                repo.create_membership(
                    first.id,
                    repo.create_user("other-audit@example.com", "hash").id,
                    first_role.id,
                    "other-audit",
                    "Other Audit",
                ).id,
                "other-face",
                "Other Face",
            ).id,
            capability="manage_world",
            target_family="community",
            action="community_updated",
            outcome="accepted",
        )


def test_schema_v24_backfills_legacy_admin_role_capabilities() -> None:
    connection = connect()
    create_schema(connection)
    connection.execute(
        "INSERT INTO communities (id, name, slug, created_at, updated_at) "
        "VALUES (1, 'Legacy', 'legacy', 'now', 'now')"
    )
    connection.execute(
        "INSERT INTO roles (id, community_id, slug, name, is_admin, created_at, updated_at) "
        "VALUES (1, 1, 'director', 'Director', 1, 'now', 'now')"
    )
    connection.execute("DROP TABLE staff_audit_events")
    connection.execute("DROP TABLE role_capabilities")
    connection.execute("DELETE FROM schema_migrations")
    connection.execute(
        "INSERT INTO schema_migrations (version, name, applied_at) "
        "VALUES (23, 'tenant-pair-storage-constraints', 'now')"
    )
    connection.execute("PRAGMA user_version = 23")
    connection.commit()

    create_schema(connection)

    capabilities = {
        row["capability"]
        for row in connection.execute(
            "SELECT capability FROM role_capabilities WHERE community_id = 1 AND role_id = 1"
        ).fetchall()
    }
    assert capabilities == STAFF_CAPABILITIES
    assert connection.execute("PRAGMA user_version").fetchone()[0] == CURRENT_SCHEMA_VERSION


def test_schema_rejects_cross_tenant_audit_actor_even_via_raw_sql(
    repo: ForumRepository,
) -> None:
    first = repo.get_community(1)
    second = repo.create_community("raw-audit-second", "Raw Audit Second")
    role = repo.create_role(second.id, "director", "Director", is_admin=True)
    user = repo.create_user("raw-audit@example.com", "hash")
    membership = repo.create_membership(second.id, user.id, role.id, "raw-audit", "Raw Audit")

    with pytest.raises(sqlite3.IntegrityError, match="tenant pair constraint failed"):
        repo.connection.execute(
            """
            INSERT INTO staff_audit_events (
                community_id, actor_membership_id, capability, target_family,
                action, outcome, created_at
            ) VALUES (?, ?, 'manage_world', 'community', 'updated', 'accepted', 'now')
            """,
            (first.id, membership.id),
        )


def test_export_records_a_durable_audit_event_and_partial_role_reads_are_scoped() -> None:
    root_services = create_services(path=":memory:")
    repo = root_services.repo
    staff = resolve_seed_persona(repo, "xmen_staff")
    staff_services = AppServices(
        repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )

    staff_services.community_export_manifest()

    export_events = staff_services.staff_audit_trail(target_family="community_export")
    assert [(event.capability, event.action, event.outcome) for event in export_events] == [
        ("manage_world", "community_export_created", "accepted")
    ]

    reviewer_role = repo.create_role(
        staff.community.id,
        "application-reviewer",
        "Application Reviewer",
        capabilities={"manage_applications"},
    )
    reviewer_user = repo.create_user("audit-reviewer@example.com", "hash")
    reviewer_membership = repo.create_membership(
        staff.community.id,
        reviewer_user.id,
        reviewer_role.id,
        "audit-reviewer",
        "Audit Reviewer",
    )
    reviewer_character = repo.create_character(
        staff.community.id,
        reviewer_membership.id,
        "audit-reviewer-face",
        "Audit Reviewer Face",
    )
    repo.create_staff_audit_event(
        staff.community.id,
        reviewer_membership.id,
        capability="manage_applications",
        target_family="application",
        target_id=reviewer_character.id,
        action="application_reviewed",
        outcome="accepted",
    )
    reviewer_services = AppServices(
        repo,
        DemoSeed(
            staff.community,
            reviewer_user,
            reviewer_membership,
            reviewer_character,
        ),
    )

    reviewer_events = reviewer_services.staff_audit_trail(capability="manage_applications")
    assert [event.action for event in reviewer_events] == ["application_reviewed"]
    with pytest.raises(PermissionError):
        reviewer_services.staff_audit_trail()
    with pytest.raises(PermissionError):
        reviewer_services.staff_audit_trail(capability="manage_world")
