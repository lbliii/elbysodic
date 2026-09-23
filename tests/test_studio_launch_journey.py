from __future__ import annotations

import asyncio
import re
from html.parser import HTMLParser

import pytest
from chirp.testing import TestClient

from elbysodic.db.seed import DemoSeed, resolve_seed_persona
from elbysodic.services import AppServices, create_services
from elbysodic.web import create_app


class _LaunchChecklistParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.items: list[tuple[str, str]] = []
        self._item: dict[str, str] | None = None
        self._capturing_label = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "li" and "elbysodic-launch-checklist__item" in (attributes.get("class") or ""):
            self._item = {"label": "", "href": ""}
        elif self._item is not None and tag == "strong":
            self._capturing_label = True
        elif self._item is not None and tag == "a":
            self._item["href"] = attributes.get("href") or ""

    def handle_data(self, data: str) -> None:
        if self._item is not None and self._capturing_label:
            self._item["label"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "strong":
            self._capturing_label = False
        elif tag == "li" and self._item is not None:
            self.items.append((self._item["label"].strip(), self._item["href"]))
            self._item = None


@pytest.mark.parametrize(
    ("launch_status", "status_copy"),
    [
        ("invite-only", "Invite-only"),
        ("public-preview", "Public preview"),
    ],
)
def test_studio_launch_checklist_destinations_and_status_clarity(
    launch_status: str,
    status_copy: str,
) -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        services.repo.update_community_launch_status(staff.community.id, launch_status)
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )

        async with TestClient(app) as client:
            launch = await client.get("/studio/launch")
            assert launch.status == 200

            current_status = re.search(
                r"<span>Current status</span>\s*<strong>(.*?)</strong>",
                launch.text,
                re.DOTALL,
            )
            readiness = re.search(
                r'<p class="elbysodic-section-kicker">Invite-only readiness</p>\s*'
                r'<h2 id="launch-checklist-heading">(.*?)</h2>',
                launch.text,
                re.DOTALL,
            )
            assert current_status is not None
            assert current_status.group(1).strip() == status_copy
            assert readiness is not None
            readiness_copy = readiness.group(1).strip()
            assert readiness_copy == "Ready for invite-only opening" or re.fullmatch(
                r"\d+ required lanes still backstage",
                readiness_copy,
            )
            assert "Use the required lanes below to prepare an invite-only opening." in launch.text

            checklist = _LaunchChecklistParser()
            checklist.feed(launch.text)
            assert dict(checklist.items) == {
                "Realm identity": "/studio/appearance#identity-appearance",
                "Scene hubs": "/studio/structure#world-structure",
                "Director materials": "/studio/content#continuity-events",
                "Intake and claims": "/studio/intake",
                "Wanted hooks": "/wanted",
                "Appearance": "/studio/appearance#appearance-theme",
                "Opening checklist": "/studio/launch#launch-checklist-heading",
            }

            for _label, href in checklist.items:
                path, _, anchor = href.partition("#")
                target = await client.get(path)
                assert target.status == 200
                if anchor:
                    assert f'id="{anchor}"' in target.text

    asyncio.run(run())
