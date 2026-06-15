from __future__ import annotations

import pytest

from elbysodic.db.seed import DemoSeed, resolve_seed_persona
from elbysodic.services import AppServices, create_services
from elbysodic.services.auth import session_token_hash
from elbysodic.services.exports import (
    CommunityExportDomain,
    CommunityExportManifest,
    CommunityExportPrivacyTier,
    CommunityExportProfile,
)


def test_director_export_manifest_is_tenant_scoped_and_redacted() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    staff = resolve_seed_persona(repo, "xmen_staff")
    hp = repo.get_community_by_slug("hp-universe")
    repo.create_community_access_request(
        staff.community.id,
        email="xmen-export@example.com",
        display_name="X-Men Export Prospect",
        face_concept="X-Men private export concept",
        wanted_hook="X-Men private wanted hook",
        notes="X-Men private request note",
    )
    repo.create_community_access_request(
        hp.id,
        email="hp-export@example.com",
        display_name="HP Export Prospect",
        face_concept="HP private export concept",
        wanted_hook="HP private wanted hook",
        notes="HP private request note",
    )
    staff_services = AppServices(
        repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )

    manifest = staff_services.community_export_manifest()
    counts = {item.label: item.count for item in manifest.counts}
    rendered_manifest = repr(manifest)

    assert manifest.community_slug == "x-men-apocalypse"
    assert all(item.community_id == manifest.community_id for item in manifest.counts)
    assert all(item.community_id == manifest.community_id for item in manifest.ownership)
    assert all(link.community_id == manifest.community_id for link in manifest.source_links)
    assert all(redaction.community_id == manifest.community_id for redaction in manifest.redactions)
    assert counts["memberships"] > 0
    assert counts["characters"] > 0
    assert counts["threads"] > 0
    assert counts["posts"] > 0
    assert counts["access_requests"] >= 1
    assert all(link.href.startswith("/c/x-men-apocalypse/") for link in manifest.source_links)
    assert {redaction.scope for redaction in manifest.redactions} >= {
        "access_requests",
        "global_users",
        "invitations",
        "sessions",
    }
    assert any(
        item.kind == "post" and item.membership_id is not None and item.character_id is not None
        for item in manifest.ownership
    )
    assert "xmen-export@example.com" not in rendered_manifest
    assert "X-Men private request note" not in rendered_manifest
    assert "HP private request note" not in rendered_manifest
    assert "hp-export@example.com" not in rendered_manifest
    assert "HP Universe" not in rendered_manifest
    assert "dev-password-hash" not in rendered_manifest


def test_export_privacy_profiles_are_tenant_scoped() -> None:
    services = create_services(path=":memory:")
    staff = resolve_seed_persona(services.repo, "xmen_staff")
    staff_services = AppServices(
        services.repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )

    manifest = staff_services.community_export_manifest()
    profiles = {profile.tier: profile for profile in manifest.privacy_profiles}

    assert set(profiles) == {"public", "member", "staff", "director_archive"}
    for profile in profiles.values():
        assert profile.community_id == manifest.community_id
        assert profile.community_slug == manifest.community_slug
        profile_domains = (
            *profile.included_domains,
            *profile.excluded_domains,
            *profile.sensitive_domains,
        )
        assert all(domain.community_id == manifest.community_id for domain in profile_domains)


def test_public_export_profile_includes_only_public_safe_realm_domains() -> None:
    manifest = _staff_export_manifest()
    public = _profile(manifest.privacy_profiles, "public")

    assert _domain_names(public.included_domains) == {
        "realm_profile",
        "published_roster",
        "open_wanted_hooks",
        "claimed_claims",
        "published_material_metadata",
    }
    assert {
        "member_identities",
        "private_notes",
        "staff_queues",
        "inactive_identities",
        "draft_materials",
        "notification_rows",
        "cross_community_records",
    }.issubset(_domain_names(public.excluded_domains))
    assert public.sensitive_domains == ()


def test_member_export_profile_excludes_staff_and_other_writer_private_state() -> None:
    manifest = _staff_export_manifest()
    member = _profile(manifest.privacy_profiles, "member")

    assert {
        "realm_profile",
        "published_roster",
        "member_visible_threads",
        "member_visible_posts",
        "open_wanted_hooks",
        "claimed_claims",
        "published_material_metadata",
    }.issubset(_domain_names(member.included_domains))
    assert {
        "other_writer_private_records",
        "private_notes",
        "staff_queues",
        "inactive_identities",
        "draft_materials",
        "notification_rows",
        "cross_community_records",
    }.issubset(_domain_names(member.excluded_domains))
    assert member.sensitive_domains == ()


def test_staff_export_profile_is_current_community_operational_state() -> None:
    manifest = _staff_export_manifest()
    staff = _profile(manifest.privacy_profiles, "staff")

    assert {
        "memberships",
        "roles",
        "characters",
        "boards_threads_posts",
        "materials",
        "claims_reserves_wanted",
        "plot_hooks_plotting_rooms",
        "staff_queues",
    }.issubset(_domain_names(staff.included_domains))
    assert {
        "global_users",
        "sessions",
        "raw_invitation_tokens",
        "notification_rows",
        "cross_community_records",
    }.issubset(_domain_names(staff.excluded_domains))
    assert {
        "memberships",
        "roles",
        "draft_materials",
        "staff_queues",
    }.issubset(_domain_names(staff.sensitive_domains))


def test_director_archive_profile_names_sensitive_domains_and_cross_tenant_exclusions() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    staff = resolve_seed_persona(repo, "xmen_staff")
    hp = repo.get_community_by_slug("hp-universe")
    repo.create_community_access_request(
        hp.id,
        email="hp-archive-profile@example.com",
        display_name="HP Archive Profile Prospect",
        face_concept="HP profile face concept",
        wanted_hook="HP profile wanted hook",
        notes="HP profile private note",
    )
    staff_services = AppServices(
        repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )

    manifest = staff_services.community_export_manifest()
    director = _profile(manifest.privacy_profiles, "director_archive")
    rendered_director_profile = repr(director)

    assert {
        "access_request_metadata",
        "invitations",
        "notification_rows",
        "staff_queues",
    }.issubset(_domain_names(director.included_domains))
    assert {
        "memberships",
        "roles",
        "inactive_identities",
        "draft_materials",
        "private_plotting_rooms",
        "access_request_metadata",
        "invitations",
        "notification_rows",
        "staff_queues",
    }.issubset(_domain_names(director.sensitive_domains))
    assert {
        "global_users",
        "sessions",
        "password_hashes",
        "raw_invitation_tokens",
        "applicant_private_notes",
        "cross_community_records",
    }.issubset(_domain_names(director.excluded_domains))
    assert "HP Archive Profile Prospect" not in rendered_director_profile
    assert "HP profile private note" not in rendered_director_profile


def test_export_manifest_redacts_auth_material_and_cross_realm_shared_account() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    staff = resolve_seed_persona(repo, "xmen_staff")
    hp = repo.get_community_by_slug("hp-universe")
    shared_user = repo.create_user("shared-export@example.com", "secret-export-password-hash")
    xmen_role = repo.create_role(staff.community.id, "export-member", "Export Member")
    hp_role = repo.create_role(hp.id, "export-member", "Export Member")
    xmen_membership = repo.create_membership(
        staff.community.id,
        shared_user.id,
        xmen_role.id,
        "shared-export-xmen",
        "Shared Export X-Men",
    )
    hp_membership = repo.create_membership(
        hp.id,
        shared_user.id,
        hp_role.id,
        "shared-export-hp",
        "Shared Export HP",
    )
    xmen_character = repo.create_character(
        staff.community.id,
        xmen_membership.id,
        "shared-export-xmen-face",
        "Shared Export X-Men Face",
    )
    hp_character = repo.create_character(
        hp.id,
        hp_membership.id,
        "shared-export-hp-face",
        "Shared Export HP Face",
    )
    session_probe = "session-redaction-fixture"
    session_hash = session_token_hash(session_probe)
    repo.create_user_session(
        shared_user.id,
        session_hash,
        expires_at="2026-07-01T00:00:00+00:00",
    )
    invite_probe = "invite-redaction-fixture"
    invite_hash = session_token_hash(invite_probe)
    repo.create_community_invitation(
        staff.community.id,
        email="invite-export@example.com",
        role_id=xmen_role.id,
        invited_by_membership_id=staff.membership.id,
        token_hash=invite_hash,
        expires_at="2026-07-01T00:00:00+00:00",
    )
    staff_services = AppServices(
        repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )

    manifest = staff_services.community_export_manifest()
    rendered_manifest = repr(manifest)

    assert all(item.community_id == staff.community.id for item in manifest.counts)
    assert all(item.community_id == staff.community.id for item in manifest.ownership)
    assert all(link.community_id == staff.community.id for link in manifest.source_links)
    assert all(redaction.community_id == staff.community.id for redaction in manifest.redactions)
    assert any(
        item.kind == "character"
        and item.record_id == xmen_character.id
        and item.membership_id == xmen_membership.id
        and item.character_id == xmen_character.id
        for item in manifest.ownership
    )
    assert all(item.record_id != hp_character.id for item in manifest.ownership)
    assert "Shared Export X-Men Face" in rendered_manifest
    assert "Shared Export HP Face" not in rendered_manifest
    assert "shared-export@example.com" not in rendered_manifest
    assert "secret-export-password-hash" not in rendered_manifest
    assert session_probe not in rendered_manifest
    assert session_hash not in rendered_manifest
    assert invite_probe not in rendered_manifest
    assert invite_hash not in rendered_manifest
    assert "invite-export@example.com" not in rendered_manifest


def test_export_manifest_omits_cross_realm_source_links() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    staff = resolve_seed_persona(repo, "xmen_staff")
    hp_director = resolve_seed_persona(repo, "hp_director")
    hp = repo.get_community_by_slug("hp-universe")
    hp_board = repo.create_board(
        hp.id,
        "hp-export-only-board",
        "HP Export Only Board",
        description="A cross-realm board that must not enter X-Men export provenance.",
    )
    hp_material = repo.create_material(
        hp.id,
        "hp-export-only-material",
        "HP Export Only Material",
        material_type="guide",
        summary="A cross-realm guide that must not enter X-Men export provenance.",
    )
    hp_wanted = repo.create_wanted_ad(
        hp.id,
        hp_director.membership.id,
        "hp-export-only-wanted",
        "HP Export Only Wanted",
    )
    staff_services = AppServices(
        repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )

    manifest = staff_services.community_export_manifest()
    rendered_manifest = repr(manifest)

    assert all(link.community_id == staff.community.id for link in manifest.source_links)
    assert all(link.href.startswith("/c/x-men-apocalypse/") for link in manifest.source_links)
    assert all(
        link.record_id not in {hp_board.id, hp_material.id, hp_wanted.id}
        for link in manifest.source_links
    )
    assert "/c/hp-universe/" not in rendered_manifest
    assert "HP Export Only Board" not in rendered_manifest
    assert "HP Export Only Material" not in rendered_manifest
    assert "HP Export Only Wanted" not in rendered_manifest


def test_member_cannot_create_community_export_manifest() -> None:
    services = create_services(path=":memory:")

    with pytest.raises(PermissionError, match="director access is required"):
        services.community_export_manifest()


def _staff_export_manifest() -> CommunityExportManifest:
    services = create_services(path=":memory:")
    staff = resolve_seed_persona(services.repo, "xmen_staff")
    staff_services = AppServices(
        services.repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )
    return staff_services.community_export_manifest()


def _profile(
    profiles: tuple[CommunityExportProfile, ...],
    tier: CommunityExportPrivacyTier,
) -> CommunityExportProfile:
    for profile in profiles:
        if profile.tier == tier:
            return profile
    raise AssertionError(f"missing export privacy profile for tier: {tier}")


def _domain_names(domains: tuple[CommunityExportDomain, ...]) -> set[str]:
    return {domain.name for domain in domains}
