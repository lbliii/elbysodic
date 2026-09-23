from __future__ import annotations

import asyncio
from html.parser import HTMLParser

from chirp.testing import TestClient

from elbysodic.services import create_services
from elbysodic.web import create_app


class _WorldPageMarkup(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=True)
        self.headings: dict[str, list[str]] = {"h1": [], "h2": []}
        self.links: list[tuple[str, str]] = []
        self._active: list[tuple[str, str, list[str]]] = []
        self._visible_parts: list[str] = []
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h1", "h2", "a"}:
            attributes = dict(attrs)
            self._active.append((tag, attributes.get("href", "") or "", []))
        if tag in {"a", "article", "div", "h1", "h2", "header", "p", "section", "span", "strong"}:
            self._visible_parts.append(" ")

    def handle_data(self, data: str) -> None:
        self._visible_parts.append(data)
        for _tag, _href, parts in self._active:
            parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"a", "article", "div", "h1", "h2", "header", "p", "section", "span", "strong"}:
            self._visible_parts.append(" ")
        for index in range(len(self._active) - 1, -1, -1):
            active_tag, href, parts = self._active[index]
            if active_tag != tag:
                continue
            self._active.pop(index)
            text = " ".join(" ".join(parts).split())
            if tag in self.headings:
                self.headings[tag].append(text)
            else:
                self.links.append((href, text))
            break

    @property
    def visible_text(self) -> str:
        return " ".join(" ".join(self._visible_parts).split())


def _visible_count(markup: _WorldPageMarkup, label: str, count: int) -> None:
    assert f"{label} {count}" in markup.visible_text


def test_world_guide_index_keeps_seeded_sections_and_empty_state() -> None:
    async def run() -> None:
        services = create_services(":memory:")
        app = create_app(debug=False, services=services)
        community_id = services.seed.community.id
        published = services.repo.list_materials(community_id, status="published")
        expected_pillars = sum(material.is_featured for material in published)
        expected_guides = sum(
            not material.is_featured and material.material_type in {"premise", "guide", "factions"}
            for material in published
        )
        expected_events = sum(material.material_type == "event" for material in published)

        try:
            async with TestClient(app) as client:
                seeded_response = await client.get("/world")
                assert seeded_response.status == 200
                seeded = _WorldPageMarkup(seeded_response.text)

                assert "World guide" in seeded.headings["h1"]
                assert {"Start here", "Guides", "Events"}.issubset(seeded.headings["h2"])
                assert {
                    "/world/premise",
                    "/world/b-24-winter",
                    "/world/application-guide",
                }.issubset({href for href, _text in seeded.links})
                _visible_count(seeded, "Pillars", expected_pillars)
                _visible_count(seeded, "Guides", expected_guides)
                _visible_count(seeded, "Events", expected_events)

                for material in published:
                    services.repo.update_material(
                        community_id,
                        material.id,
                        title=material.title,
                        material_type=material.material_type,
                        presentation_variant=material.presentation_variant,
                        summary=material.summary,
                        body=material.body,
                        status="draft",
                        sort_order=material.sort_order,
                        is_featured=material.is_featured,
                    )

                empty_response = await client.get("/world")
                assert empty_response.status == 200
                empty = _WorldPageMarkup(empty_response.text)

                assert "World guide" in empty.headings["h1"]
                assert "Start here" in empty.headings["h2"]
                assert "No guidebook pillars have been featured yet." in empty.visible_text
                assert not {href for href, _text in empty.links}.intersection(
                    {"/world/premise", "/world/b-24-winter", "/world/application-guide"}
                )
                _visible_count(empty, "Pillars", 0)
                _visible_count(empty, "Guides", 0)
                _visible_count(empty, "Events", 0)
        finally:
            services.close()

    asyncio.run(run())
