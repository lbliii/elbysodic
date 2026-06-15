from __future__ import annotations

import asyncio
import re
from pathlib import Path
from urllib.parse import urlencode

from chirp.testing import TestClient

from elbysodic.db.seed import DemoSeed, SeedPersonaContext, resolve_seed_persona
from elbysodic.services import create_services
from elbysodic.services.network import (
    PUBLIC_CATALOG_FORBIDDEN_VIEWER_FIELDS,
    PUBLIC_CATALOG_PRIVACY_CONTRACT,
)
from elbysodic.web import create_app

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DOC = ROOT / "docs" / "architecture" / "public-catalog-privacy-contract.md"
_FORM = {"Content-Type": "application/x-www-form-urlencoded"}
_CSRF_RE = re.compile(r'name="_csrf_token" value="([^"]+)"')
_NETWORK_CARD_RE = re.compile(
    r'<article class="[^"]*elbysodic-network-card[^"]*".*?</article>',
    re.DOTALL,
)


def _response_headers(response, name: str) -> list[str]:
    headers = response.headers
    if isinstance(headers, dict):
        value = headers.get(name)
        return [] if value is None else [str(value)]
    return [str(value) for key, value in headers if str(key).lower() == name.lower()]


def _cookie_values(*responses) -> dict[str, str]:
    values: dict[str, str] = {}
    for response in responses:
        for cookie in _response_headers(response, "set-cookie"):
            pair = cookie.split(";", 1)[0]
            name, _, value = pair.partition("=")
            values[name] = value
    return values


def _cookie_header(cookies: dict[str, str]) -> str:
    return "; ".join(f"{name}={value}" for name, value in cookies.items())


def _csrf_token(html: str) -> str:
    match = _CSRF_RE.search(html)
    assert match is not None
    return match.group(1)


def _dev_identity_cookie(seed: DemoSeed | SeedPersonaContext) -> str:
    return f"elbysodic_dev_identity={seed.community.id}:{seed.user.id}:{seed.membership.id}"


def _set_production_env(monkeypatch) -> None:
    monkeypatch.setenv("ELBYSODIC_ENV", "production")
    monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "x" * 32)
    monkeypatch.setenv("ELBYSODIC_ALLOWED_HOSTS", "*")
    monkeypatch.setenv("ELBYSODIC_DEMO_MODE", "1")


async def _production_login(client: TestClient, *, email: str) -> dict[str, str]:
    page = await client.get("/login?next=/network")
    cookies = _cookie_values(page)
    response = await client.post(
        "/login",
        body=urlencode(
            {
                "email": email,
                "password": "password",
                "next": "/network",
                "_csrf_token": _csrf_token(page.text),
            }
        ).encode(),
        headers={**_FORM, "Cookie": _cookie_header(cookies)},
    )
    cookies.update(_cookie_values(response))
    assert response.status == 302
    return cookies


def test_public_catalog_privacy_contract_names_allowed_and_excluded_state() -> None:
    contract = PUBLIC_CATALOG_PRIVACY_CONTRACT

    assert {
        "community_name",
        "published_premise_title",
        "published_premise_summary",
        "public_discovery_profile",
        "public_discovery_tags",
        "open_wanted_count",
        "latest_public_activity_at",
        "activity_freshness_label",
        "request_access_href",
        "invite_posture_label",
        "access_posture_label",
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
        assert card.access_posture_label
        assert card.activity_freshness_label.startswith("Public activity ")
        assert card.latest_public_activity_at


def test_public_catalog_search_uses_public_signals_not_member_continuation() -> None:
    services = create_services(path=":memory:")

    public_results = services.network_explore("first face").results
    private_results = services.network_explore("playing as rogue unread plotting rooms").results

    assert public_results
    assert private_results == []


def test_public_catalog_cards_render_safe_freshness_for_viewer_modes(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        services = create_services(path=":memory:")
        app = create_app(debug=False, services=services, dev_tools=True)

        writer = resolve_seed_persona(services.repo, "xmen_writer")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        inactive = resolve_seed_persona(services.repo, "xmen_inactive")
        cross_community = resolve_seed_persona(services.repo, "hp_director")

        async with TestClient(app) as client:
            signed_out = await client.get("/network")
        async with TestClient(app) as client:
            account_cookies = await _production_login(
                client,
                email="moira@example.com",
            )
            account_visitor = await client.get(
                "/network",
                headers={"Cookie": _cookie_header(account_cookies)},
            )
        async with TestClient(app) as client:
            same_community_member = await client.get(
                "/network",
                headers={"Cookie": _dev_identity_cookie(writer)},
            )
            staff_response = await client.get(
                "/network",
                headers={"Cookie": _dev_identity_cookie(staff)},
            )
            inactive_member = await client.get(
                "/network",
                headers={"Cookie": _dev_identity_cookie(inactive)},
            )
            cross_community_viewer = await client.get(
                "/network",
                headers={"Cookie": _dev_identity_cookie(cross_community)},
            )
        responses = {
            "signed_out": signed_out,
            "account_visitor": account_visitor,
            "same_community_member": same_community_member,
            "staff": staff_response,
            "inactive_member": inactive_member,
            "cross_community_viewer": cross_community_viewer,
        }

        assert set(responses) == set(PUBLIC_CATALOG_PRIVACY_CONTRACT.viewer_modes)
        for response in responses.values():
            card_markup = "\n".join(_NETWORK_CARD_RE.findall(response.text))
            assert card_markup
            assert response.status == 200
            assert "Request access open" in card_markup
            assert "Public activity " in card_markup
            assert "playing as" not in card_markup
            assert "Application Review Room" not in card_markup
            assert "Plotting Rooms" not in card_markup
            assert "needs reply" not in card_markup
            assert "Staff queue" not in card_markup

    asyncio.run(run())


def test_public_catalog_privacy_contract_doc_matches_service_contract() -> None:
    doc = CONTRACT_DOC.read_text()

    for signal in PUBLIC_CATALOG_PRIVACY_CONTRACT.searchable_signals:
        assert signal in doc
    for signal in PUBLIC_CATALOG_PRIVACY_CONTRACT.excluded_signals:
        assert signal in doc
    for viewer_mode in PUBLIC_CATALOG_PRIVACY_CONTRACT.viewer_modes:
        assert viewer_mode in doc
