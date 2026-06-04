from __future__ import annotations

from pathlib import Path

from elbysodic.services import create_services
from elbysodic.services.network import (
    PUBLIC_CATALOG_FORBIDDEN_VIEWER_FIELDS,
    PUBLIC_CATALOG_PRIVACY_CONTRACT,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DOC = ROOT / "docs" / "architecture" / "public-catalog-privacy-contract.md"


def test_public_catalog_privacy_contract_names_allowed_and_excluded_state() -> None:
    contract = PUBLIC_CATALOG_PRIVACY_CONTRACT

    assert {
        "community_name",
        "published_premise_title",
        "published_premise_summary",
        "public_discovery_profile",
        "public_discovery_tags",
        "open_wanted_count",
        "request_access_href",
        "invite_posture_label",
    }.issubset(contract.searchable_signals)
    assert set(PUBLIC_CATALOG_FORBIDDEN_VIEWER_FIELDS).issubset(contract.excluded_signals)
    assert {
        "active_face",
        "unread_notification_count",
        "application_count",
        "plotting_room_count",
        "staff_queue",
        "private_note",
        "draft_material",
        "backstage_realm",
        "cross_community_private_state",
    }.issubset(contract.excluded_signals)
    assert set(contract.viewer_modes) == {
        "signed_out",
        "account_visitor",
        "same_community_member",
        "staff",
        "inactive_member",
        "cross_community_viewer",
    }
    assert {
        "list_materials_for_communities",
        "list_discovery_profiles_for_communities",
        "list_discovery_tags_for_communities",
        "network_program_counts",
        "public_scene_hub_community_ids",
    }.issubset(contract.batching_contract)


def test_public_catalog_cards_do_not_expose_forbidden_viewer_fields() -> None:
    services = create_services(path=":memory:")

    cards = services.network_explore().results

    assert cards
    for card in cards:
        assert all(
            not hasattr(card, field_name)
            for field_name in PUBLIC_CATALOG_PRIVACY_CONTRACT.excluded_signals
        )
        assert card.request_access_href == f"/c/{card.community.slug}/request-access"
        assert card.invite_posture_label == "Public preview"


def test_public_catalog_search_uses_public_signals_not_member_continuation() -> None:
    services = create_services(path=":memory:")

    public_results = services.network_explore("first face").results
    private_results = services.network_explore("playing as rogue unread plotting rooms").results

    assert public_results
    assert private_results == []


def test_public_catalog_privacy_contract_doc_matches_service_contract() -> None:
    doc = CONTRACT_DOC.read_text()

    for signal in PUBLIC_CATALOG_PRIVACY_CONTRACT.searchable_signals:
        assert signal in doc
    for signal in PUBLIC_CATALOG_PRIVACY_CONTRACT.excluded_signals:
        assert signal in doc
    for viewer_mode in PUBLIC_CATALOG_PRIVACY_CONTRACT.viewer_modes:
        assert viewer_mode in doc
