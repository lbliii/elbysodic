from __future__ import annotations

import asyncio
from html.parser import HTMLParser

from chirp.testing import TestClient

from elbysodic.db.seed import DemoSeed, resolve_seed_persona
from elbysodic.services import AppServices, create_services
from elbysodic.web import create_app


class _RenderedPage(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._open_links: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href") or ""
            self._open_links.append([href, ""])

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if not value:
            return
        self.text.append(value)
        for link in self._open_links:
            link[1] += value

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._open_links:
            href, label = self._open_links.pop()
            self.links.append((href, label.strip()))


async def _render_casting(services: AppServices) -> str:
    app = create_app(debug=False, services=services)
    async with TestClient(app) as client:
        response = await client.get("/casting")
    assert response.status == 200
    return response.text


def _assert_rows_match_service_read_model(services: AppServices, markup: str) -> None:
    desk = services.casting_desk()
    page = _RenderedPage()
    page.feed(markup)
    visible_text = " ".join(page.text)
    visible_links = set(page.links)
    visible_hrefs = {href for href, _label in visible_links}

    assert "Casting desk" in visible_text
    assert f"{len(desk.active_reserves)} Community reserves" in visible_text
    assert f"{len(desk.wanted_with_interest)} Hooks with interest" in visible_text
    assert f"{len(desk.my_reserves)} My active reserves" in visible_text
    if desk.active_face is None:
        assert "No face selected" in visible_text
        assert "Choose a face to personalize casting filters and claims." in visible_text
        assert "Active face reserves" not in visible_text
    else:
        assert "Active face casting" in visible_text
        assert f"{len(desk.active_face_reserves)} Active face reserves" in visible_text

    if desk.active_face_reserves:
        assert "Active face reserves" in visible_text
    if desk.wanted_with_interest:
        assert "Wanted handoffs" in visible_text
    if desk.active_reserves:
        assert "Community reserves" in visible_text

    for reserve in desk.active_reserves:
        assert reserve.character.name in visible_text
        assert reserve.reserve.title in visible_text
        assert reserve.reserve.status in visible_text
        assert f"/characters/{reserve.character.slug}" in visible_hrefs
        if reserve.wanted_ad is not None:
            assert (
                f"/wanted/{reserve.wanted_ad.slug}",
                reserve.reserve.title,
            ) in visible_links

    viewer_owned_handoffs = 0
    for item in desk.wanted_with_interest:
        wanted_ad = item.wanted_ad.wanted_ad
        assert wanted_ad.title in visible_text
        assert wanted_ad.status in visible_text
        assert (f"/wanted/{wanted_ad.slug}", wanted_ad.title) in visible_links
        viewer_owned_handoffs += int(item.is_created_by_viewer)

        for interest in item.interests:
            assert interest.display_name in visible_text
            assert interest.interest.status in visible_text
            if interest.character is not None:
                assert f"/characters/{interest.character.slug}" in visible_hrefs

        for reserve in item.reserves:
            assert reserve.character.name in visible_text
            assert f"/characters/{reserve.character.slug}" in visible_hrefs

    assert visible_text.count("mine") == viewer_owned_handoffs


def test_casting_desk_rows_follow_member_and_staff_read_models() -> None:
    async def run() -> None:
        base_services = create_services(":memory:")
        try:
            repo = base_services.repo
            for persona_key in ("xmen_writer", "xmen_staff"):
                persona = resolve_seed_persona(repo, persona_key)
                viewer_services = AppServices(
                    repo,
                    DemoSeed(
                        persona.community,
                        persona.user,
                        persona.membership,
                        persona.character,
                    ),
                )
                markup = await _render_casting(viewer_services)
                _assert_rows_match_service_read_model(viewer_services, markup)
        finally:
            base_services.close()

    asyncio.run(run())


def test_faceless_member_gets_the_empty_casting_handoff_state() -> None:
    async def run() -> None:
        base_services = create_services(":memory:")
        try:
            repo = base_services.repo
            community = repo.create_community("casting-clear", "Casting Clear")
            user = repo.create_user("casting-clear@example.com", "hash")
            role = repo.create_role(community.id, "member", "Member")
            membership = repo.create_membership(
                community.id,
                user.id,
                role.id,
                "castingclear",
                "Casting Clear",
            )
            services = AppServices(repo, DemoSeed(community, user, membership, None))
            assert services.casting_desk().wanted_with_interest == []
            assert services.casting_desk().active_reserves == []

            markup = await _render_casting(services)
            page = _RenderedPage()
            page.feed(markup)
            visible_text = " ".join(page.text)

            assert "No face selected" in visible_text
            assert "No casting handoffs need work right now." in visible_text
            assert "Active face reserves" not in visible_text
            assert "Wanted handoffs" not in visible_text
            assert "Active Reserves" not in visible_text
        finally:
            base_services.close()

    asyncio.run(run())
