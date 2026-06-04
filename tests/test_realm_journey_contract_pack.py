from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOURNEY_DOC = ROOT / "docs" / "architecture" / "realm-journey-contract-tests.md"
FORUM_SLICE = ROOT / "tests" / "test_forum_slice.py"
WEB_SECURITY = ROOT / "tests" / "test_web_security.py"


REQUIRED_JOURNEY_TESTS = {
    "test_production_routes_require_session": WEB_SECURITY,
    "test_production_signed_in_non_member_sees_account_posture_on_public_realm": WEB_SECURITY,
    "test_production_signed_in_duplicate_access_request_links_existing_record": WEB_SECURITY,
    "test_production_release_smoke_core_user_flow": WEB_SECURITY,
    "test_director_invites_writer_through_first_face_handoff": FORUM_SLICE,
    "test_invited_writer_without_first_face_continues_to_application_form": FORUM_SLICE,
    "test_invitation_acceptance_uses_writer_activation_handoff": FORUM_SLICE,
    "test_invitation_acceptance_keeps_existing_account_memberships_local": FORUM_SLICE,
    "test_applications_desk_tracks_character_statuses": FORUM_SLICE,
    "test_rendered_surface_contract_parity_across_realm_viewers": FORUM_SLICE,
    "test_tenant_prefixed_thread_routes_scope_composer_redirects": FORUM_SLICE,
    "test_notifications_track_watched_thread_replies_and_open_read_state": FORUM_SLICE,
    "test_faceless_writer_does_not_count_unowned_character_notifications": FORUM_SLICE,
    "test_director_studio_surfaces_community_production_work": FORUM_SLICE,
    "test_request_identity_rejects_inactive_membership_viewer": FORUM_SLICE,
    "test_prefixed_cross_realm_recovery_switches_to_target_tenant": FORUM_SLICE,
}

REQUIRED_CONTRACT_PHRASES = {
    "public and account visitors see public-safe realm material",
    "access requests do not grant membership",
    "invite acceptance creates or reuses the global account",
    "faceless members are routed toward first-face/application work",
    "posting, notifications, and shell counts stay tied",
    "staff/director controls render only for current-community capability holders",
    "inactive and cross-community viewers fail closed",
}


def test_realm_journey_contract_pack_names_rendered_regression_tests() -> None:
    doc = JOURNEY_DOC.read_text()

    for test_name in REQUIRED_JOURNEY_TESTS:
        assert test_name in doc

    for phrase in REQUIRED_CONTRACT_PHRASES:
        assert phrase in doc


def test_realm_journey_contract_pack_keeps_required_tests_present() -> None:
    for test_name, path in REQUIRED_JOURNEY_TESTS.items():
        source = path.read_text()
        assert f"def {test_name}" in source
