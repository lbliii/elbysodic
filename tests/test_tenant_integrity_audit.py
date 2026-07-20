from __future__ import annotations

import pytest

from elbysodic.db.repository import ForumRepository
from elbysodic.db.seed import DemoSeed, SeedPersonaContext, resolve_seed_persona
from elbysodic.services import AppServices, create_services
from elbysodic.services.tenant_integrity import (
    format_tenant_integrity_audit_report,
    tenant_integrity_audit,
    tenant_integrity_audit_for_viewer,
)


def _allow_legacy_tenant_drift(repo: ForumRepository, table: str) -> None:
    """Disable a v23 guard while manufacturing an auditable legacy row."""

    repo.connection.execute(f"DROP TRIGGER trg_{table}_tenant_pair_insert")
    repo.connection.execute(f"DROP TRIGGER trg_{table}_tenant_pair_update")


def test_tenant_integrity_audit_reports_clean_seed_without_writes() -> None:
    services = create_services(path=":memory:")
    before_changes = services.repo.connection.total_changes

    report = tenant_integrity_audit(services.repo)

    assert report.ok is True
    assert report.findings == ()
    assert report.community_summaries == ()
    assert services.repo.connection.total_changes == before_changes


def test_tenant_integrity_audit_detects_wrong_face_authorship_without_private_text() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    hp_director = resolve_seed_persona(repo, "hp_director")
    assert writer.character is not None
    assert hp_director.character is not None
    board = repo.get_board_by_slug(writer.community.id, "new-york-city")
    thread = repo.create_thread(
        writer.community.id,
        board.id,
        writer.character.id,
        "tenant-audit-wrong-face",
        "Tenant audit wrong face",
    )
    post = repo.create_post(
        writer.community.id,
        thread.id,
        writer.character.id,
        "Private wrong-face audit body should not appear.",
    )
    _allow_legacy_tenant_drift(repo, "posts")
    repo.connection.execute(
        """
        UPDATE posts
        SET author_character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hp_director.character.id, writer.community.id, post.id),
    )
    repo.connection.commit()
    before_changes = repo.connection.total_changes

    report = tenant_integrity_audit(repo)
    formatted = format_tenant_integrity_audit_report(report)
    post_findings = [
        finding
        for finding in report.findings
        if finding.table_name == "posts" and finding.row_id == post.id
    ]

    assert len(post_findings) == 1
    assert post_findings[0].code == "tenant_pair_invalid"
    assert post_findings[0].severity == "critical"
    assert post_findings[0].community_id == writer.community.id
    assert post_findings[0].domain == "scenes"
    assert "author character does not match" in post_findings[0].reason
    assert "Private wrong-face audit body" not in formatted
    assert "hp-universe" not in formatted
    assert repo.connection.total_changes == before_changes


def test_tenant_integrity_audit_groups_findings_by_community_and_severity() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    hp_director = resolve_seed_persona(repo, "hp_director")
    assert hp_director.character is not None
    _allow_legacy_tenant_drift(repo, "community_memberships")
    repo.connection.execute(
        """
        UPDATE community_memberships
        SET role_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hp_director.membership.role_id, writer.community.id, writer.membership.id),
    )
    repo.connection.commit()

    report = tenant_integrity_audit(repo)

    assert report.ok is False
    assert report.severe_count >= 1
    assert len(report.community_summaries) == 1
    assert report.community_summaries[0].community_id == writer.community.id
    assert report.community_summaries[0].high_count >= 1
    assert any(finding.code == "membership_role_missing" for finding in report.findings)


def test_tenant_integrity_audit_reports_default_face_drift_without_identity_text() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    staff = resolve_seed_persona(repo, "xmen_staff")
    hp_director = resolve_seed_persona(repo, "hp_director")
    assert writer.character is not None
    assert staff.character is not None
    assert hp_director.character is not None

    _allow_legacy_tenant_drift(repo, "community_memberships")

    repo.connection.execute(
        """
        UPDATE community_memberships
        SET default_character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hp_director.character.id, writer.community.id, writer.membership.id),
    )
    repo.connection.execute(
        """
        UPDATE community_memberships
        SET default_character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (writer.character.id, writer.community.id, staff.membership.id),
    )
    repo.connection.commit()
    before_changes = repo.connection.total_changes

    report = tenant_integrity_audit(repo, community_id=writer.community.id)
    formatted = format_tenant_integrity_audit_report(report)
    membership_findings = {
        finding.row_id: finding
        for finding in report.findings
        if finding.table_name == "community_memberships"
    }

    assert report.ok is False
    assert report.severe_count >= 2
    assert len(report.community_summaries) == 1
    assert report.community_summaries[0].community_id == writer.community.id
    assert report.community_summaries[0].high_count >= 2
    assert membership_findings[writer.membership.id].code == "tenant_pair_invalid"
    assert membership_findings[writer.membership.id].domain == "tenant_pairs"
    assert membership_findings[writer.membership.id].reason == (
        "membership default face belongs to another community"
    )
    assert membership_findings[staff.membership.id].reason == (
        "membership default face does not belong to membership"
    )
    assert "Rogue" not in formatted
    assert "Cyclops" not in formatted
    assert "Harry" not in formatted
    assert "starlane" not in formatted
    assert "alex" not in formatted
    assert "hp-universe" not in formatted
    assert repo.connection.total_changes == before_changes


def test_tenant_integrity_audit_for_viewer_is_capability_and_community_scoped() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    staff = resolve_seed_persona(repo, "xmen_staff")
    inactive = resolve_seed_persona(repo, "xmen_inactive")
    hp_director = resolve_seed_persona(repo, "hp_director")
    assert writer.character is not None
    assert hp_director.character is not None
    board = repo.get_board_by_slug(writer.community.id, "new-york-city")
    thread = repo.create_thread(
        writer.community.id,
        board.id,
        writer.character.id,
        "tenant-audit-viewer-scope",
        "Tenant audit viewer scope",
    )
    post = repo.create_post(
        writer.community.id,
        thread.id,
        writer.character.id,
        "Viewer-scoped audit body should not appear.",
    )
    _allow_legacy_tenant_drift(repo, "posts")
    repo.connection.execute(
        """
        UPDATE posts
        SET author_character_id = ?
        WHERE community_id = ? AND id = ?
        """,
        (hp_director.character.id, writer.community.id, post.id),
    )
    repo.connection.commit()

    xmen_report = tenant_integrity_audit_for_viewer(repo, _services(repo, staff).viewer())
    hp_report = tenant_integrity_audit_for_viewer(repo, _services(repo, hp_director).viewer())

    assert any(finding.row_id == post.id for finding in xmen_report.findings)
    assert hp_report.findings == ()
    with pytest.raises(PermissionError, match="director access is required"):
        tenant_integrity_audit_for_viewer(repo, _services(repo, writer).viewer())
    with pytest.raises(PermissionError, match="not active"):
        _services(repo, inactive).viewer()


def _services(repo: ForumRepository, persona: SeedPersonaContext) -> AppServices:
    return AppServices(
        repo,
        DemoSeed(
            persona.community,
            persona.user,
            persona.membership,
            persona.character,
        ),
    )
