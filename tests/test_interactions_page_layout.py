from __future__ import annotations

import asyncio
from unittest.mock import patch

from chirp.testing import TestClient

from elbysodic.web import create_app
from tests.test_forum_slice import _seeded_services


def test_realm_artifacts_index_keeps_heading_and_open_card() -> None:
    async def run() -> None:
        app = create_app(debug=False, services=_seeded_services())
        async with TestClient(app) as client:
            page = await client.get("/interactions")

        assert page.status == 200
        assert (
            'class="elbysodic-interaction-index elbysodic-stack elbysodic-stack--lg"' in page.text
        )
        assert "Realm Artifacts</h2>" in page.text
        assert "Quizzes, polls, and surveys directors can use" in page.text
        assert 'class="elbysodic-interaction-grid"' in page.text
        assert 'class="elbysodic-interaction-card"' in page.text
        assert 'href="/interactions/pressure-lane-finder"' in page.text
        assert "Pressure Lane Finder" in page.text
        assert "No realm artifacts are open yet." not in page.text

    asyncio.run(run())


def test_realm_artifacts_index_keeps_empty_state() -> None:
    async def run() -> None:
        services = _seeded_services()
        app = create_app(debug=False, services=services)
        with patch.object(services.repo, "list_realm_interactions", return_value=[]):
            async with TestClient(app) as client:
                page = await client.get("/interactions")

        assert page.status == 200
        assert "Realm Artifacts</h2>" in page.text
        assert 'class="elbysodic-interaction-empty"' in page.text
        assert "No realm artifacts are open yet." in page.text
        assert 'class="elbysodic-interaction-card"' not in page.text

    asyncio.run(run())
