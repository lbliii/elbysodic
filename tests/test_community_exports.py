from __future__ import annotations

import pytest

from elbysodic.db.seed import DemoSeed, resolve_seed_persona
from elbysodic.services import AppServices, create_services


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


def test_member_cannot_create_community_export_manifest() -> None:
    services = create_services(path=":memory:")

    with pytest.raises(PermissionError, match="director access is required"):
        services.community_export_manifest()
