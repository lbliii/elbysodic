from __future__ import annotations

from elbysodic.db.seed import DemoSeed, resolve_seed_persona
from elbysodic.services import AppServices, create_services


def test_writer_activation_rollup_excludes_dedicated_application_queue() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    staff = resolve_seed_persona(repo, "xmen_staff")
    staff_services = AppServices(
        repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )
    baseline_activation_count = next(
        card.count
        for card in staff_services.director_operations().cards
        if card.title == "Writer activation"
    )
    member_role = repo.get_role_by_slug(staff.community.id, "member")
    applicant_user = repo.create_user("activation-applicant@example.com", "hash")
    applicant_membership = repo.create_membership(
        staff.community.id,
        applicant_user.id,
        member_role.id,
        "activation-applicant",
        "Activation Applicant",
    )
    pending_face = repo.create_character(
        staff.community.id,
        applicant_membership.id,
        "activation-pending-face",
        "Activation Pending Face",
        summary="A submitted face waiting for a director.",
        application_status="draft",
    )
    application = repo.ensure_character_application(staff.community.id, pending_face.id)
    repo.update_character_application_draft(
        staff.community.id,
        application.id,
        title=pending_face.name,
        summary=pending_face.summary,
        body="The application remains visible in the submitted review queue.",
    )
    repo.transition_character_application_status(
        staff.community.id,
        application.id,
        status="submitted",
        actor_membership_id=applicant_membership.id,
        actor_character_id=pending_face.id,
    )
    access_request = repo.create_community_access_request(
        staff.community.id,
        email="activation-access@example.com",
        display_name="Activation Prospect",
        face_concept="Transfer student",
        wanted_hook="Danger Room opening",
        notes="Requests a first-face application path.",
    )
    operations = staff_services.director_operations()
    cards = {card.title: card for card in operations.cards}

    activation = cards["Writer activation"]
    review = cards["Review queue"]
    assert activation.count == baseline_activation_count + 1
    assert activation.href == f"/studio/access-requests/{access_request.id}"
    assert activation.cta == "Review access request"
    assert activation.items == (
        "1 access request(s)",
        "Activation Prospect - Transfer student",
        "1 draft/revision face(s)",
    )
    assert review.count == 2
    assert review.href == f"/applications/{pending_face.slug}"
    assert "Activation Pending Face - ready" in review.items
    assert "accepted member(s) without faces" not in activation.items
    assert all("Activation Pending Face" not in item for item in activation.items)


def test_writer_activation_draft_faces_route_to_the_application_queue() -> None:
    services = create_services(path=":memory:")
    staff = resolve_seed_persona(services.repo, "xmen_staff")
    app = AppServices(
        services.repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )

    activation = next(
        card for card in app.director_operations().cards if card.title == "Writer activation"
    )

    assert activation.items == ("1 draft/revision face(s)",)
    assert activation.href == "/applications"
    assert activation.cta == "Open applications"


def test_ready_wanted_interest_is_not_repeated_in_casting_attention_card() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    staff = resolve_seed_persona(repo, "xmen_staff")
    writer = resolve_seed_persona(repo, "xmen_writer")
    app = AppServices(
        repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )
    assert writer.character is not None
    wanted = repo.create_wanted_ad(
        staff.community.id,
        staff.membership.id,
        "attention-lane-regression",
        "Attention lane regression",
        creator_character_id=staff.character.id if staff.character is not None else None,
    )
    interest = repo.create_wanted_ad_interest(
        staff.community.id,
        wanted.id,
        writer.membership.id,
        writer.character.id,
        note="A single interest should have one primary staff action.",
    )
    repo.create_plotting_room(
        staff.community.id,
        writer.membership.id,
        "Attention lane ready room",
        source_wanted_ad_id=wanted.id,
        source_wanted_ad_interest_id=interest.id,
        status="ready",
    )

    cards = {card.title: card for card in app.director_operations().cards}
    handoff_card = cards["Ready scene handoffs"]

    assert handoff_card.count == 1
    assert handoff_card.items == ("Attention lane regression - Rogue",)
    movement_card = cards.get("Hooks with movement")
    assert movement_card is None or "Attention lane regression" not in movement_card.items
