from __future__ import annotations

import sqlite3

import pytest

from elbysodic.db.repositories.base import TenantBoundaryError
from elbysodic.db.repository import ForumRepository
from elbysodic.db.seed import DemoSeed, SeedPersonaContext, resolve_seed_persona
from elbysodic.domain import (
    ContinuityAffectedObjectDraft,
    ContinuityAffectedObjectType,
    ContinuitySourceCitationDraft,
)
from elbysodic.services import AppServices, create_services
from elbysodic.services.continuity import (
    ContinuitySourceViewer,
    continuity_proposal_view,
)
from elbysodic.services.tenant_integrity import tenant_integrity_audit


def test_manual_continuity_lifecycle_creates_reviewed_public_canon() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    partner = resolve_seed_persona(repo, "xmen_partner")
    staff = resolve_seed_persona(repo, "xmen_staff")
    assert writer.character is not None
    assert partner.character is not None
    assert staff.character is not None
    board = repo.get_board_by_slug(writer.community.id, "new-york-city")
    thread = repo.create_thread(
        writer.community.id,
        board.id,
        writer.character.id,
        "manual-continuity-public-scene",
        "Manual continuity public scene",
        visibility="public_preview",
    )
    post = repo.create_post(
        writer.community.id,
        thread.id,
        partner.character.id,
        "The team closes the breach and accepts the consequences.",
    )
    writer_services = _services(repo, writer)
    staff_services = _services(repo, staff)

    proposal = writer_services.create_continuity_proposal(
        title="The breach is closed",
        summary="A manually proposed outcome from completed play.",
        citations=(
            ContinuitySourceCitationDraft(
                writer.community.id,
                "post",
                post.id,
                source_thread_id=thread.id,
            ),
        ),
        affected_objects=(
            ContinuityAffectedObjectDraft(
                writer.community.id,
                "character",
                writer.character.id,
            ),
        ),
        author_character_id=writer.character.id,
    )

    assert proposal.state == "draft"
    assert writer_services.submit_continuity_proposal(proposal.id).state == "submitted"
    assert writer_services.submit_continuity_proposal(proposal.id).state == "submitted"
    assert [
        event.action
        for event in repo.list_continuity_review_events(writer.community.id, proposal.id)
    ] == ["submitted"]
    assert [item.proposal.id for item in staff_services.continuity_review_queue().items] == [
        proposal.id
    ]
    revision = staff_services.review_continuity_proposal(
        proposal.id,
        action="revision_requested",
        note="Name the lasting consequence explicitly.",
    )
    assert revision.state == "revision_requested"
    assert revision.revision_note == "Name the lasting consequence explicitly."
    assert writer_services.submit_continuity_proposal(proposal.id).state == "submitted"
    approved = staff_services.review_continuity_proposal(
        proposal.id,
        action="approved",
        visibility="public",
    )

    assert approved.state == "approved"
    assert approved.visibility == "public"
    assert (
        staff_services.review_continuity_proposal(
            proposal.id,
            action="approved",
            visibility="public",
        ).id
        == proposal.id
    )
    events = repo.list_continuity_review_events(writer.community.id, proposal.id)
    assert [event.action for event in events] == [
        "submitted",
        "revision_requested",
        "submitted",
        "approved",
    ]
    assert events[-1].actor_membership_id == staff.membership.id
    assert events[-1].actor_character_id == staff.character.id
    public_view = continuity_proposal_view(
        repo,
        ContinuitySourceViewer(writer.community.id),
        proposal.id,
    )
    assert public_view.canon_entry is not None
    assert public_view.canon_entry.approved_by_membership_id == staff.membership.id
    assert public_view.citations[0].visibility.label == "post #1"
    assert public_view.citations[0].excerpt == ""
    assert public_view.review_events == ()
    with pytest.raises(ValueError, match="cannot move from approved to archived"):
        staff_services.review_continuity_proposal(
            proposal.id,
            action="archived",
        )


def test_continuity_proposal_sources_reject_cross_community_threads_posts_and_objects() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    hp = resolve_seed_persona(repo, "hp_director")
    assert writer.character is not None
    assert hp.character is not None
    board = repo.get_board_by_slug(writer.community.id, "new-york-city")
    valid_thread = repo.create_thread(
        writer.community.id,
        board.id,
        writer.character.id,
        "continuity-valid-tenant-source",
        "Continuity valid tenant source",
    )
    hp_board = repo.list_boards(hp.community.id)[0]
    hp_thread = repo.create_thread(
        hp.community.id,
        hp_board.id,
        hp.character.id,
        "continuity-cross-tenant-source",
        "Continuity cross-tenant source",
    )
    hp_post = repo.create_post(
        hp.community.id,
        hp_thread.id,
        hp.character.id,
        "This other-realm post cannot be attached.",
    )
    hp_claim_type = repo.create_claim_type(
        hp.community.id,
        "continuity-cross-tenant-claim",
        "Continuity Cross-Tenant Claim",
    )
    hp_claim = repo.create_character_claim(
        hp.community.id,
        hp_claim_type.id,
        "other-realm-claim",
        "Other Realm Claim",
        character_id=hp.character.id,
    )
    hp_material = repo.create_material(
        hp.community.id,
        "continuity-cross-tenant-material",
        "Continuity Cross-Tenant Material",
    )
    hp_plot_hook = repo.create_character_plot_hook(
        hp.community.id,
        hp.membership.id,
        hp.character.id,
        "continuity-cross-tenant-plot-hook",
        "Continuity Cross-Tenant Plot Hook",
    )
    hp_reserve = repo.create_character_reserve(
        hp.community.id,
        hp.membership.id,
        hp.character.id,
        "Continuity Cross-Tenant Reserve",
    )
    hp_wanted = repo.create_wanted_ad(
        hp.community.id,
        hp.membership.id,
        "continuity-cross-tenant-wanted",
        "Continuity Cross-Tenant Wanted",
        creator_character_id=hp.character.id,
    )
    valid_target = ContinuityAffectedObjectDraft(
        writer.community.id,
        "character",
        writer.character.id,
    )

    for citation in (
        ContinuitySourceCitationDraft(writer.community.id, "thread", hp_thread.id),
        ContinuitySourceCitationDraft(
            writer.community.id,
            "post",
            hp_post.id,
            source_thread_id=hp_thread.id,
        ),
    ):
        with pytest.raises((LookupError, TenantBoundaryError)):
            repo.create_continuity_proposal(
                writer.community.id,
                writer.membership.id,
                title="Cross-realm source",
                citations=(citation,),
                affected_objects=(valid_target,),
            )

    hp_targets: dict[ContinuityAffectedObjectType, int] = {
        "board": repo.list_boards(hp.community.id)[0].id,
        "character": hp.character.id,
        "claim": hp_claim.id,
        "material": hp_material.id,
        "plot_hook": hp_plot_hook.id,
        "reserve": hp_reserve.id,
        "thread": hp_thread.id,
        "wanted_ad": hp_wanted.id,
    }
    valid_source = ContinuitySourceCitationDraft(
        writer.community.id,
        "thread",
        valid_thread.id,
    )
    for object_type, object_id in hp_targets.items():
        with pytest.raises((LookupError, TenantBoundaryError)):
            repo.create_continuity_proposal(
                writer.community.id,
                writer.membership.id,
                title=f"Cross-realm {object_type}",
                citations=(valid_source,),
                affected_objects=(
                    ContinuityAffectedObjectDraft(
                        writer.community.id,
                        object_type,
                        object_id,
                    ),
                ),
            )

    assert repo.list_continuity_proposals(writer.community.id) == []


def test_continuity_proposal_source_visibility_matrix_redacts_private_titles_and_excerpts() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    partner = resolve_seed_persona(repo, "xmen_partner")
    outsider = resolve_seed_persona(repo, "xmen_outsider")
    staff = resolve_seed_persona(repo, "xmen_staff")
    assert writer.character is not None
    assert partner.character is not None
    board = repo.get_board_by_slug(writer.community.id, "new-york-city")
    thread = repo.create_thread(
        writer.community.id,
        board.id,
        writer.character.id,
        "continuity-private-source",
        "Private source title",
        status="private",
    )
    post = repo.create_post(
        writer.community.id,
        thread.id,
        partner.character.id,
        "Private source excerpt that must never reach an unrelated member.",
    )
    writer_services = _services(repo, writer)
    proposal = writer_services.create_continuity_proposal(
        title="Participant-only outcome",
        summary="Still awaiting review.",
        citations=(
            ContinuitySourceCitationDraft(
                writer.community.id,
                "post",
                post.id,
                source_thread_id=thread.id,
            ),
        ),
        affected_objects=(
            ContinuityAffectedObjectDraft(
                writer.community.id,
                "character",
                writer.character.id,
            ),
        ),
    )
    writer_services.submit_continuity_proposal(proposal.id)
    _services(repo, staff).review_continuity_proposal(
        proposal.id,
        action="approved",
        visibility="participants",
    )

    participant_view = _services(repo, partner).continuity_proposal_view(proposal.id)
    assert participant_view.citations[0].visibility.label == "post #1"
    assert participant_view.citations[0].excerpt.startswith("Private source excerpt")
    with pytest.raises(LookupError, match="not found"):
        _services(repo, outsider).continuity_proposal_view(proposal.id)
    with pytest.raises(LookupError, match="not found"):
        continuity_proposal_view(
            repo,
            ContinuitySourceViewer(writer.community.id),
            proposal.id,
        )


def test_continuity_review_authority_requires_active_staff_or_director_membership() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    outsider = resolve_seed_persona(repo, "xmen_outsider")
    inactive = resolve_seed_persona(repo, "xmen_inactive")
    assert writer.character is not None
    board = repo.get_board_by_slug(writer.community.id, "new-york-city")
    thread = repo.create_thread(
        writer.community.id,
        board.id,
        writer.character.id,
        "continuity-review-authority",
        "Continuity review authority",
    )
    writer_services = _services(repo, writer)
    proposal = writer_services.create_continuity_proposal(
        title="Review authority",
        summary="Only a capable active realm identity may decide this.",
        citations=(ContinuitySourceCitationDraft(writer.community.id, "thread", thread.id),),
        affected_objects=(
            ContinuityAffectedObjectDraft(
                writer.community.id,
                "character",
                writer.character.id,
            ),
        ),
    )
    writer_services.submit_continuity_proposal(proposal.id)

    with pytest.raises(PermissionError, match="manage_world"):
        _services(repo, outsider).review_continuity_proposal(
            proposal.id,
            action="approved",
        )
    with pytest.raises(PermissionError, match="not active"):
        _services(repo, inactive).viewer()


def test_continuity_notifications_filter_targets_by_source_and_affected_object_visibility() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    partner = resolve_seed_persona(repo, "xmen_partner")
    outsider = resolve_seed_persona(repo, "xmen_outsider")
    staff = resolve_seed_persona(repo, "xmen_staff")
    assert writer.character is not None
    assert partner.character is not None
    assert outsider.character is not None
    board = repo.get_board_by_slug(writer.community.id, "new-york-city")
    thread = repo.create_thread(
        writer.community.id,
        board.id,
        writer.character.id,
        "continuity-notification-private-source",
        "Continuity notification private source",
        status="private",
    )
    repo.create_post(
        writer.community.id,
        thread.id,
        partner.character.id,
        "A participant-only source beat.",
    )
    reserve = repo.create_character_reserve(
        writer.community.id,
        outsider.membership.id,
        outsider.character.id,
        "Private affected reserve",
    )
    staff_services = _services(repo, staff)
    proposal = staff_services.create_continuity_proposal(
        title="Visibility-filtered notification plan",
        summary="The backend computes recipients but does not fan out notifications.",
        citations=(ContinuitySourceCitationDraft(writer.community.id, "thread", thread.id),),
        affected_objects=(
            ContinuityAffectedObjectDraft(writer.community.id, "reserve", reserve.id),
        ),
    )

    targets = staff_services.continuity_notification_targets(proposal.id)

    target_ids = {target.membership_id for target in targets}
    assert staff.membership.id in target_ids
    assert writer.membership.id not in target_ids
    assert partner.membership.id not in target_ids
    assert outsider.membership.id not in target_ids
    assert all(
        target.source_labels == ("Continuity notification private source",) for target in targets
    )
    assert all(target.affected_labels == ("Private affected reserve",) for target in targets)
    with pytest.raises(PermissionError, match="proposal author or continuity reviewers"):
        _services(repo, writer).continuity_notification_targets(proposal.id)


def test_continuity_export_stays_single_community_and_redacts_private_review_material() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    staff = resolve_seed_persona(repo, "xmen_staff")
    hp = resolve_seed_persona(repo, "hp_director")
    assert writer.character is not None
    assert hp.character is not None
    xmen_board = repo.get_board_by_slug(writer.community.id, "new-york-city")
    xmen_thread = repo.create_thread(
        writer.community.id,
        xmen_board.id,
        writer.character.id,
        "continuity-export-source",
        "Continuity export source",
    )
    xmen_services = _services(repo, writer)
    xmen_proposal = xmen_services.create_continuity_proposal(
        title="X-Men continuity export proposal",
        summary="Private proposal summary omitted from the manifest.",
        citations=(ContinuitySourceCitationDraft(writer.community.id, "thread", xmen_thread.id),),
        affected_objects=(
            ContinuityAffectedObjectDraft(
                writer.community.id,
                "character",
                writer.character.id,
            ),
        ),
    )
    xmen_services.submit_continuity_proposal(xmen_proposal.id)
    _services(repo, staff).review_continuity_proposal(
        xmen_proposal.id,
        action="revision_requested",
        note="Private reviewer note must not be exported.",
    )
    hp_board = repo.list_boards(hp.community.id)[0]
    hp_thread = repo.create_thread(
        hp.community.id,
        hp_board.id,
        hp.character.id,
        "continuity-hp-export-source",
        "HP continuity source must not cross the export boundary",
    )
    repo.create_continuity_proposal(
        hp.community.id,
        hp.membership.id,
        title="HP continuity proposal must not cross the export boundary",
        citations=(ContinuitySourceCitationDraft(hp.community.id, "thread", hp_thread.id),),
        affected_objects=(
            ContinuityAffectedObjectDraft(hp.community.id, "character", hp.character.id),
        ),
    )

    manifest = _services(repo, staff).community_export_manifest()
    counts = {item.label: item.count for item in manifest.counts}
    rendered = repr(manifest)

    assert counts["continuity_proposals"] == 1
    assert counts["continuity_citations"] == 1
    assert counts["continuity_affected_objects"] == 1
    assert counts["continuity_review_events"] == 2
    assert all(item.community_id == writer.community.id for item in manifest.ownership)
    assert all(item.community_id == writer.community.id for item in manifest.source_links)
    assert "Private reviewer note must not be exported." not in rendered
    assert "HP continuity proposal must not cross the export boundary" not in rendered
    assert any(redaction.scope == "continuity_review_material" for redaction in manifest.redactions)


def test_continuity_review_rolls_back_state_canon_review_and_audit_on_late_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    staff = resolve_seed_persona(repo, "xmen_staff")
    assert writer.character is not None
    board = repo.get_board_by_slug(writer.community.id, "new-york-city")
    thread = repo.create_thread(
        writer.community.id,
        board.id,
        writer.character.id,
        "continuity-rollback-source",
        "Continuity rollback source",
        visibility="public_preview",
    )
    writer_services = _services(repo, writer)
    proposal = writer_services.create_continuity_proposal(
        title="Atomic continuity review",
        summary="Every review side effect commits or rolls back together.",
        citations=(ContinuitySourceCitationDraft(writer.community.id, "thread", thread.id),),
        affected_objects=(
            ContinuityAffectedObjectDraft(
                writer.community.id,
                "character",
                writer.character.id,
            ),
        ),
    )
    writer_services.submit_continuity_proposal(proposal.id)

    def fail_audit(*args: object, **kwargs: object) -> object:
        raise RuntimeError("late audit failure")

    monkeypatch.setattr(repo, "create_staff_audit_event", fail_audit)
    with pytest.raises(RuntimeError, match="late audit failure"):
        _services(repo, staff).review_continuity_proposal(
            proposal.id,
            action="approved",
            visibility="public",
        )

    persisted = repo.get_continuity_proposal(writer.community.id, proposal.id)
    assert persisted.state == "submitted"
    assert [
        event.action
        for event in repo.list_continuity_review_events(
            writer.community.id,
            proposal.id,
        )
    ] == ["submitted"]
    assert (
        repo.get_continuity_canon_entry_for_proposal(
            writer.community.id,
            proposal.id,
        )
        is None
    )


def test_continuity_storage_guards_cover_every_persisted_row_family() -> None:
    services = create_services(path=":memory:")
    trigger_names = {
        row["name"]
        for row in services.repo.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger'"
        ).fetchall()
    }
    tables = {
        "continuity_proposals",
        "continuity_source_citations",
        "continuity_affected_objects",
        "continuity_review_events",
        "canon_entries",
    }

    assert {
        f"trg_{table}_tenant_pair_{operation}"
        for table in tables
        for operation in ("insert", "update")
    }.issubset(trigger_names)

    writer = resolve_seed_persona(services.repo, "xmen_writer")
    hp = resolve_seed_persona(services.repo, "hp_director")
    now = "2026-07-20T00:00:00+00:00"
    with pytest.raises(sqlite3.IntegrityError, match="continuity_proposals"):
        services.repo.connection.execute(
            """
            INSERT INTO continuity_proposals (
                community_id, author_membership_id, title, created_at, updated_at
            ) VALUES (?, ?, 'cross-tenant raw row', ?, ?)
            """,
            (writer.community.id, hp.membership.id, now, now),
        )


def test_tenant_integrity_audit_detects_legacy_continuity_drift() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    hp = resolve_seed_persona(repo, "hp_director")
    assert writer.character is not None
    board = repo.get_board_by_slug(writer.community.id, "new-york-city")
    thread = repo.create_thread(
        writer.community.id,
        board.id,
        writer.character.id,
        "continuity-audit-source",
        "Continuity audit source",
    )
    proposal = repo.create_continuity_proposal(
        writer.community.id,
        writer.membership.id,
        title="Continuity audit proposal",
        citations=(ContinuitySourceCitationDraft(writer.community.id, "thread", thread.id),),
        affected_objects=(
            ContinuityAffectedObjectDraft(
                writer.community.id,
                "character",
                writer.character.id,
            ),
        ),
    )
    repo.connection.execute("DROP TRIGGER trg_continuity_proposals_tenant_pair_update")
    repo.connection.execute(
        "UPDATE continuity_proposals SET author_membership_id = ? WHERE id = ?",
        (hp.membership.id, proposal.id),
    )
    repo.connection.commit()

    report = tenant_integrity_audit(repo, community_id=writer.community.id)
    findings = [
        finding
        for finding in report.findings
        if finding.table_name == "continuity_proposals" and finding.row_id == proposal.id
    ]

    assert len(findings) == 1
    assert findings[0].severity == "critical"
    assert findings[0].domain == "continuity"
    assert "another community" in findings[0].reason


def _services(repo: ForumRepository, persona: SeedPersonaContext) -> AppServices:
    return AppServices(
        repo,
        DemoSeed(
            persona.community,
            persona.user,
            persona.membership,
            persona.character,
        ),
        owns_repo=False,
    )
