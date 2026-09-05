from __future__ import annotations

from elbysodic.db.seed import SeedPersonaContext, resolve_seed_persona
from elbysodic.services import create_services
from elbysodic.services.continuity import (
    ContinuitySourceReference,
    ContinuitySourceViewer,
    continuity_source_visibility,
    public_continuity_source_visibility,
)


def test_public_continuity_sources_hide_private_scenes_posts_and_drafts() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    community_id = writer.community.id
    assert writer.character is not None
    public_location = repo.get_board_by_slug(community_id, "new-york-city")
    private_board = repo.create_board(
        community_id,
        "continuity-private-lab",
        "Continuity Private Lab",
        is_private=True,
    )
    public_thread = repo.create_thread(
        community_id,
        public_location.id,
        writer.character.id,
        "continuity-public-scene",
        "Continuity public scene",
        visibility="public_preview",
    )
    public_post = repo.create_post(
        community_id,
        public_thread.id,
        writer.character.id,
        "A public scene beat eligible for citation.",
    )
    private_thread = repo.create_thread(
        community_id,
        private_board.id,
        writer.character.id,
        "continuity-private-scene",
        "Continuity private scene",
    )
    private_post = repo.create_post(
        community_id,
        private_thread.id,
        writer.character.id,
        "A private scene beat that must not leak.",
    )
    draft_material = repo.create_material(
        community_id,
        "continuity-draft-material",
        "Continuity Draft Material",
        status="draft",
    )

    public_location_result = public_continuity_source_visibility(
        repo,
        community_id,
        ContinuitySourceReference(community_id, "location", public_location.id),
    )
    public_post_result = public_continuity_source_visibility(
        repo,
        community_id,
        ContinuitySourceReference(
            community_id,
            "post",
            public_post.id,
            source_thread_id=public_thread.id,
        ),
    )
    private_thread_result = public_continuity_source_visibility(
        repo,
        community_id,
        ContinuitySourceReference(community_id, "scene", private_thread.id),
    )
    private_post_result = public_continuity_source_visibility(
        repo,
        community_id,
        ContinuitySourceReference(
            community_id,
            "post",
            private_post.id,
            source_thread_id=private_thread.id,
        ),
    )
    draft_material_result = public_continuity_source_visibility(
        repo,
        community_id,
        ContinuitySourceReference(community_id, "material", draft_material.id),
    )

    assert public_location_result.visible is True
    assert public_location_result.label == "New York City"
    assert public_post_result.visible is True
    assert public_post_result.label == "post #1"
    assert private_thread_result.status == "hidden"
    assert private_thread_result.label == ""
    assert private_post_result.status == "hidden"
    assert private_post_result.label == ""
    assert draft_material_result.status == "hidden"
    assert draft_material_result.label == ""


def test_private_scene_sources_are_visible_to_participants_and_staff_only() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    outsider = resolve_seed_persona(repo, "xmen_outsider")
    staff = resolve_seed_persona(repo, "xmen_staff")
    community_id = writer.community.id
    assert writer.character is not None
    public_location = repo.get_board_by_slug(community_id, "new-york-city")
    private_thread = repo.create_thread(
        community_id,
        public_location.id,
        writer.character.id,
        "continuity-participant-scene",
        "Continuity participant scene",
        status="private",
    )
    private_post = repo.create_post(
        community_id,
        private_thread.id,
        writer.character.id,
        "Participant-visible private source.",
    )
    thread_reference = ContinuitySourceReference(community_id, "scene", private_thread.id)
    post_reference = ContinuitySourceReference(
        community_id,
        "post",
        private_post.id,
        source_thread_id=private_thread.id,
    )

    participant_result = continuity_source_visibility(repo, _viewer(writer), thread_reference)
    outsider_result = continuity_source_visibility(repo, _viewer(outsider), thread_reference)
    staff_result = continuity_source_visibility(repo, _viewer(staff), post_reference)

    assert participant_result.visible is True
    assert participant_result.label == "Continuity participant scene"
    assert outsider_result.status == "hidden"
    assert outsider_result.label == ""
    assert staff_result.visible is True
    assert staff_result.label == "post #1"


def test_continuity_source_gate_hides_inactive_and_cross_community_viewers() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    inactive = resolve_seed_persona(repo, "xmen_inactive")
    hp = repo.get_community_by_slug("hp-universe")
    assert writer.character is not None
    location = repo.get_board_by_slug(writer.community.id, "new-york-city")

    inactive_result = continuity_source_visibility(
        repo,
        _viewer(inactive),
        ContinuitySourceReference(writer.community.id, "location", location.id),
    )
    cross_community_result = continuity_source_visibility(
        repo,
        ContinuitySourceViewer(community_id=hp.id),
        ContinuitySourceReference(writer.community.id, "location", location.id),
    )

    assert inactive_result.status == "inactive_viewer"
    assert inactive_result.label == ""
    assert cross_community_result.status == "cross_community"
    assert cross_community_result.label == ""


def test_claim_and_reserve_sources_keep_private_review_state_out_of_lower_tiers() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    outsider = resolve_seed_persona(repo, "xmen_outsider")
    staff = resolve_seed_persona(repo, "xmen_staff")
    community_id = writer.community.id
    assert writer.character is not None
    private_claim_type = repo.create_claim_type(
        community_id,
        "continuity-private-claim",
        "Continuity Private Claim",
        visibility="staff",
    )
    private_claim = repo.create_character_claim(
        community_id,
        private_claim_type.id,
        "restricted-claim",
        "Restricted Claim",
        character_id=writer.character.id,
        notes="Claim notes that must stay private.",
    )
    reserve = repo.create_character_reserve(
        community_id,
        writer.membership.id,
        writer.character.id,
        "Continuity private reserve",
        notes="Reserve notes that must stay private.",
    )

    public_claim = public_continuity_source_visibility(
        repo,
        community_id,
        ContinuitySourceReference(community_id, "claim", private_claim.id),
    )
    outsider_reserve = continuity_source_visibility(
        repo,
        _viewer(outsider),
        ContinuitySourceReference(community_id, "reserve", reserve.id),
    )
    owner_reserve = continuity_source_visibility(
        repo,
        _viewer(writer),
        ContinuitySourceReference(community_id, "reserve", reserve.id),
    )
    staff_claim = continuity_source_visibility(
        repo,
        _viewer(staff),
        ContinuitySourceReference(community_id, "claim", private_claim.id),
    )

    assert public_claim.status == "hidden"
    assert public_claim.label == ""
    assert outsider_reserve.status == "hidden"
    assert outsider_reserve.label == ""
    assert owner_reserve.visible is True
    assert owner_reserve.label == "Continuity private reserve"
    assert staff_claim.visible is True
    assert staff_claim.label == "Restricted Claim"


def test_continuity_source_gate_rejects_malformed_location_and_post_references() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = resolve_seed_persona(repo, "xmen_writer")
    community_id = writer.community.id
    assert writer.character is not None
    community_board = repo.get_board_by_slug(community_id, "announcements")
    location = repo.get_board_by_slug(community_id, "new-york-city")
    first_thread = repo.create_thread(
        community_id,
        location.id,
        writer.character.id,
        "continuity-first-thread",
        "Continuity first thread",
    )
    second_thread = repo.create_thread(
        community_id,
        location.id,
        writer.character.id,
        "continuity-second-thread",
        "Continuity second thread",
    )
    post = repo.create_post(
        community_id,
        first_thread.id,
        writer.character.id,
        "Post that belongs to the first thread.",
    )

    malformed_location = continuity_source_visibility(
        repo,
        _viewer(writer),
        ContinuitySourceReference(community_id, "location", community_board.id),
    )
    malformed_post = continuity_source_visibility(
        repo,
        _viewer(writer),
        ContinuitySourceReference(
            community_id,
            "post",
            post.id,
            source_thread_id=second_thread.id,
        ),
    )

    assert malformed_location.status == "malformed"
    assert malformed_location.label == ""
    assert malformed_post.status == "malformed"
    assert malformed_post.label == ""


def _viewer(persona: SeedPersonaContext) -> ContinuitySourceViewer:
    return ContinuitySourceViewer(
        community_id=persona.community.id,
        membership=persona.membership,
        role=persona.role,
    )
