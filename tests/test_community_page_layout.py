from __future__ import annotations

import asyncio

from chirp.testing import TestClient

from tests.test_forum_slice import _app


def test_community_page_keeps_board_table_and_recent_pulse() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            page = await client.get("/community")

        assert page.status == 200
        assert 'class="elbysodic-community-page elbysodic-stack elbysodic-stack--xl"' in page.text
        assert "Writer room and record" in page.text
        assert "Community table</h2>" in page.text
        assert "Operational boards use compact rows" in page.text
        assert "Announcements" in page.text
        assert 'class="elbysodic-community-table"' in page.text
        assert "Recent community pulse</h2>" in page.text
        assert "A lightweight log of visible publishing activity." in page.text
        assert 'class="elbysodic-activity-log"' in page.text

    asyncio.run(run())
