from __future__ import annotations

from urllib.parse import urlsplit

from elbysodic.db.seed import (
    ORIGINAL_PREMISE_SEED_SLUGS,
    resolve_seed_persona,
    seed_demo_forum,
)
from elbysodic.services import create_services

X_MEN_ALL_STAFF_CAPABILITIES = frozenset(
    {
        "manage_applications",
        "manage_casting",
        "manage_navigation",
        "manage_threads",
        "manage_world",
    }
)
X_MEN_MODERATOR_CAPABILITIES = frozenset({"manage_threads"})


def test_xmen_moderator_seed_purpose_and_capabilities_match() -> None:
    services = create_services(path=":memory:")
    try:
        moderator = resolve_seed_persona(services.repo, "xmen_mod")
        writer = resolve_seed_persona(services.repo, "xmen_writer")
        staff = resolve_seed_persona(services.repo, "xmen_staff")

        assert moderator.persona.purpose == (
            "Thread moderation QA on readable boards: pin, lock, and move threads; "
            "update scene status and details."
        )
        assert moderator.persona.default_path == "/boards/med-bay/threads/med-bay-lights"
        assert moderator.role.is_admin is False
        assert moderator.role.capabilities == X_MEN_MODERATOR_CAPABILITIES
        assert writer.role.capabilities.isdisjoint(X_MEN_ALL_STAFF_CAPABILITIES)
        assert staff.role.is_admin is True
        assert staff.role.capabilities == X_MEN_ALL_STAFF_CAPABILITIES
    finally:
        services.close()


def test_seed_demo_forum_reconciles_an_existing_broad_moderator_role() -> None:
    services = create_services(path=":memory:")
    try:
        moderator = resolve_seed_persona(services.repo, "xmen_mod")
        services.repo.update_role(
            moderator.community.id,
            moderator.role.id,
            name="Moderator",
            is_admin=True,
            capabilities=X_MEN_ALL_STAFF_CAPABILITIES,
        )

        seed_demo_forum(services.repo)

        reconciled = resolve_seed_persona(services.repo, "xmen_mod")
        assert reconciled.role.is_admin is False
        assert reconciled.role.capabilities == X_MEN_MODERATOR_CAPABILITIES
    finally:
        services.close()


def test_seed_demo_forum_migrates_legacy_generated_realm_hero() -> None:
    services = create_services(path=":memory:")
    try:
        repo = services.repo
        community = repo.get_community_by_slug("afterlight-accord")
        repo.update_community_media(
            community.id,
            community_mark_url=community.community_mark_url,
            community_mark_alt=community.community_mark_alt,
            world_hero_image_url="/elbysodic-static/seed-media/afterlight-hero.svg",
            world_hero_image_alt=community.world_hero_image_alt,
            world_hero_treatment=community.world_hero_treatment,
            world_hero_focal_point=community.world_hero_focal_point,
            world_hero_overlay=community.world_hero_overlay,
            world_hero_height=community.world_hero_height,
        )

        seed_demo_forum(repo)

        updated = repo.get_community_by_slug("afterlight-accord")
        assert (
            updated.world_hero_image_url
            == "/elbysodic-static/seed-media/realms/afterlight-hero.jpg"
        )
    finally:
        services.close()


def test_original_premise_sample_scenes_fill_public_preview_window() -> None:
    services = create_services(path=":memory:")
    try:
        for community_slug in ORIGINAL_PREMISE_SEED_SLUGS:
            gateway = services.public_realm_gateway(community_slug)
            assert len(gateway.scene_previews) == 2

            for scene in gateway.scene_previews:
                path_parts = urlsplit(scene.href).path.strip("/").split("/")
                assert path_parts[:2] == ["c", community_slug]
                assert path_parts[2] == "boards"
                assert path_parts[4] == "threads"

                preview = services.public_scene_preview(
                    community_slug,
                    path_parts[3],
                    path_parts[5],
                )
                assert len(preview.posts) == preview.preview_limit == 4
                assert preview.total_post_count == 5
    finally:
        services.close()
