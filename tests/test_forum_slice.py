from __future__ import annotations

import asyncio
import json
import logging
import re
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from urllib.parse import urlencode, urljoin

import pytest
from chirp.app import App
from chirp.http.request import RequestUrlScope
from chirp.http.response import Response
from chirp.testing import TestClient
from chirp_ui.alpine import check_alpine_runtime

from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.db.schema import SynchronizedConnection
from elbysodic.db.seed import DemoSeed, resolve_seed_persona, seed_demo_forum
from elbysodic.domain import Community, Thread
from elbysodic.services import AppServices, create_services, default_database_path
from elbysodic.services.access import TENANT_SLUG_CACHE_KEY
from elbysodic.services.auth import hash_password
from elbysodic.services.notifications import (
    count_visible_unread_notifications,
    mark_all_notifications_read,
    visible_unread_notification_counts,
)
from elbysodic.services.operations import (
    OperationsInspectionConfig,
    RestoreCheckCount,
    RestoreCheckReadback,
    RestoreCheckResult,
    format_restore_check_report,
    format_restore_plan_report,
    operations_inspection,
    restore_check_database,
    restore_plan_from_check,
)
from elbysodic.web import create_app
from elbysodic.web.state import get_services
from elbysodic.web.tenant import request_scoped_path, scope_response_urls
from elbysodic.web.worker_draining import active_plotting_streams, emit_worker_draining
from tests._db_lifecycle import preserve_test_connection, release_test_connection
from tests._sql_probe import trace_sql

_FORM = {"Content-Type": "application/x-www-form-urlencoded"}
_SEEDED_TEMPLATE_CONNECTION: sqlite3.Connection | None = None
_SEEDED_TEMPLATE_SEED: DemoSeed | None = None


@pytest.fixture(scope="module", autouse=True)
def _close_seeded_template_connection() -> Any:
    yield
    global _SEEDED_TEMPLATE_CONNECTION
    global _SEEDED_TEMPLATE_SEED
    if _SEEDED_TEMPLATE_CONNECTION is not None:
        release_test_connection(_SEEDED_TEMPLATE_CONNECTION)
        _SEEDED_TEMPLATE_CONNECTION.close()
    _SEEDED_TEMPLATE_CONNECTION = None
    _SEEDED_TEMPLATE_SEED = None


def _sidebar_board_count(html: str, board_slug: str) -> int:
    match = re.search(
        rf'<a class="[^"]*elbysodic-sidebar-link[^"]*"\s+href="(?:/c/[^"]+)?/boards/{re.escape(board_slug)}"[^>]*>'
        r"(?P<body>.*?)</a>",
        html,
        re.DOTALL,
    )
    assert match is not None
    count = re.search(
        r'<span class="elbysodic-sidebar-count">(?P<count>\d+)</span>',
        match.group("body"),
    )
    return int(count.group("count")) if count is not None else 0


def _response_header(response: Any, name: str) -> str:
    headers = response.headers
    if isinstance(headers, dict):
        return str(headers[name])
    for key, value in headers:
        if str(key).lower() == name.lower():
            return str(value)
    raise AssertionError(f"response header not found: {name}")


def _csrf_token(html: str) -> str:
    match = re.search(r'name="_csrf_token" value="([^"]+)"', html)
    assert match is not None
    return match.group(1)


async def _stylesheet_text_with_imports(
    client: TestClient,
    path: str = "/elbysodic-static/elbysodic-theme.css",
    *,
    seen: set[str] | None = None,
) -> str:
    seen = seen or set()
    if path in seen:
        return ""
    seen.add(path)
    response = await client.get(path)
    assert response.status == 200
    text = response.text
    imported = [
        await _stylesheet_text_with_imports(client, urljoin(path, href), seen=seen)
        for href in re.findall(r'@import\s+url\("([^"]+)"\);', text)
    ]
    return text + "\n".join(imported)


async def _switch_membership(
    client: TestClient,
    membership: Any,
    next_url: str,
    *,
    character_id: str = "0",
) -> Any:
    return await client.post(
        "/identity",
        body=urlencode(
            {
                "intent": "switch_membership",
                "membership_id": str(membership.id),
                "character_id": character_id,
                "next": next_url,
            }
        ).encode(),
        headers=_FORM,
    )


def _response_headers(response: Any, name: str) -> list[str]:
    headers = response.headers
    if isinstance(headers, dict):
        value = headers.get(name)
        return [] if value is None else [str(value)]
    values = []
    for key, value in headers:
        if str(key).lower() == name.lower():
            values.append(str(value))
    return values


def _style_block(html: str, style_id: str) -> str:
    match = re.search(
        rf'<style id="{re.escape(style_id)}">(?P<body>.*?)</style>',
        html,
        re.DOTALL,
    )
    assert match is not None
    return match.group("body")


def _oob_block(html: str, target_id: str) -> str:
    match = re.search(
        rf'<div id="{re.escape(target_id)}" hx-swap-oob="innerHTML">(?P<body>.*?)</div>',
        html,
        re.DOTALL,
    )
    assert match is not None
    return match.group("body")


def _oob_outer_block(html: str, target_id: str) -> str:
    start = re.search(
        rf'<div id="{re.escape(target_id)}"[^>]*hx-swap-oob="true"[^>]*>',
        html,
        re.DOTALL,
    )
    assert start is not None
    body_start = start.end()
    depth = 1
    for match in re.finditer(r"</?div\b[^>]*>", html[body_start:], re.DOTALL):
        if match.group(0).startswith("</"):
            depth -= 1
            if depth == 0:
                return html[body_start : body_start + match.start()]
        else:
            depth += 1
    raise AssertionError(f"OOB block {target_id!r} was not closed")


def _input_value(html: str, name: str) -> str:
    match = re.search(
        rf'<input[^>]+name="{re.escape(name)}"[^>]+value="(?P<value>[^"]*)"',
        html,
    )
    assert match is not None
    return match.group("value")


def _page_content(html: str) -> str:
    marker = '<div id="page-content">'
    start = html.find(marker)
    assert start >= 0
    return html[start:]


def _raw_memory_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _seeded_template() -> tuple[sqlite3.Connection, DemoSeed]:
    global _SEEDED_TEMPLATE_CONNECTION, _SEEDED_TEMPLATE_SEED

    if _SEEDED_TEMPLATE_CONNECTION is None or _SEEDED_TEMPLATE_SEED is None:
        connection = _raw_memory_connection()
        create_schema(connection)
        repository = ForumRepository(_synchronized_connection(connection))
        seed = seed_demo_forum(repository)
        connection.commit()
        preserve_test_connection(connection)
        _SEEDED_TEMPLATE_CONNECTION = connection
        _SEEDED_TEMPLATE_SEED = seed

    return _SEEDED_TEMPLATE_CONNECTION, _SEEDED_TEMPLATE_SEED


def _seeded_services() -> AppServices:
    template_connection, seed = _seeded_template()
    connection = _raw_memory_connection()
    template_connection.backup(connection)
    return AppServices(ForumRepository(_synchronized_connection(connection)), seed)


def _synchronized_connection(connection: sqlite3.Connection) -> sqlite3.Connection:
    return cast(sqlite3.Connection, SynchronizedConnection(connection))


def _app():
    return create_app(debug=False, services=_seeded_services())


def _outsider_services(
    services: AppServices, *, prefix: str = "outsider"
) -> tuple[AppServices, int]:
    repo = services.repo
    community = services.seed.community
    role = repo.get_role_by_slug(community.id, "member")
    user = repo.create_user(f"{prefix}@example.com", "hash")
    membership = repo.create_membership(
        community.id,
        user.id,
        role.id,
        prefix,
        prefix.title(),
    )
    character = repo.create_character(
        community.id,
        membership.id,
        f"{prefix}-face",
        f"{prefix.title()} Face",
        make_default=True,
    )
    membership = repo.get_membership(community.id, membership.id)
    return AppServices(repo, DemoSeed(community, user, membership, character)), character.id


def _faceless_services(services: AppServices, *, prefix: str = "faceless") -> AppServices:
    repo = services.repo
    community = services.seed.community
    role = repo.get_role_by_slug(community.id, "member")
    user = repo.create_user(f"{prefix}@example.com", "hash")
    membership = repo.create_membership(
        community.id,
        user.id,
        role.id,
        prefix,
        prefix.title(),
    )
    return AppServices(repo, DemoSeed(community, user, membership, None))


def _link_seed_plotting_room_to_sentinel(services: AppServices):
    repo = services.repo
    community = services.seed.community
    membership = services.seed.membership
    character = services.seed.default_character
    assert character is not None
    board = repo.get_board_by_slug(community.id, "danger-room")
    thread = repo.get_thread_by_slug(community.id, board.id, "sentinel-drill")
    wanted = repo.create_wanted_ad(
        community.id,
        membership.id,
        "sentinel-drill-tactics-hook",
        "Sentinel drill tactics handoff",
        creator_character_id=character.id,
        summary="Coordinate the danger room beat before the next reply.",
    )
    interest = repo.create_wanted_ad_interest(
        community.id,
        wanted.id,
        membership.id,
        character.id,
        note="Rogue can carry this scene beat.",
    )
    room = repo.create_plotting_room(
        community.id,
        membership.id,
        "Sentinel drill tactics table",
        source_wanted_ad_id=wanted.id,
        source_wanted_ad_interest_id=interest.id,
        summary="Plan Rogue's next danger room beat before posting.",
        status="ready",
    )
    repo.create_plotting_room_participant(
        community.id,
        room.id,
        membership.id,
        character_id=character.id,
        participant_role="owner",
    )
    return repo.attach_plotting_room_thread(community.id, room.id, thread.id)


def _scale_board_services(*, thread_count: int = 30) -> AppServices:
    connection = connect(check_same_thread=False)
    create_schema(connection)
    repo = ForumRepository(connection)
    community = repo.seed_default_community("Scale Realm")
    role = repo.create_role(community.id, "member", "Member")
    user = repo.create_user("scale-writer@example.com", "hash")
    membership = repo.create_membership(community.id, user.id, role.id, "scale", "Scale")
    viewer_character = repo.create_character(
        community.id,
        membership.id,
        "scale-face",
        "Scale Face",
        make_default=True,
    )
    authors = [viewer_character]
    for index in range(5):
        author_user = repo.create_user(f"scale-author-{index}@example.com", "hash")
        author_membership = repo.create_membership(
            community.id,
            author_user.id,
            role.id,
            f"scale-author-{index}",
            f"Scale Author {index}",
        )
        authors.append(
            repo.create_character(
                community.id,
                author_membership.id,
                f"scale-author-{index}",
                f"Scale Author {index}",
            )
        )
    facet_group = repo.create_facet_group(community.id, "scale-lens", "Scale Lens")
    facets = [
        repo.create_facet(community.id, facet_group.id, f"scale-{index}", f"Scale {index}")
        for index in range(3)
    ]
    board = repo.create_board(community.id, "scale-yard", "Scale Yard")
    repo.assign_board_facet(community.id, board.id, facets[0].id)
    for index in range(thread_count):
        author = authors[index % len(authors)]
        thread = repo.create_thread(
            community.id,
            board.id,
            author.id,
            f"scale-thread-{index}",
            f"Scale Thread {index}",
        )
        repo.assign_thread_facet(community.id, thread.id, facets[index % len(facets)].id)
        repo.create_post(
            community.id,
            thread.id,
            author.id,
            f"Opening post for scale thread {index}.",
        )
        repo.create_post(
            community.id,
            thread.id,
            authors[(index + 1) % len(authors)].id,
            f"Reply for scale thread {index} mentioning @Scale.",
        )
    membership = repo.get_membership(community.id, membership.id)
    return AppServices(repo, DemoSeed(community, user, membership, viewer_character))


def _scale_network_services(*, community_count: int = 12) -> AppServices:
    services = create_services(path=":memory:")
    for index in range(community_count):
        _add_hosted_membership(
            services,
            slug=f"network-scale-{index}",
            user_id=services.seed.user.id,
            username=f"network-scale-{index}",
        )
    return services


def _add_hosted_membership(
    services: AppServices,
    *,
    slug: str = "hosted",
    user_id: int | None = None,
    username: str = "hosted-lane",
    is_admin: bool = False,
) -> tuple[Community, int, int, int]:
    repo = services.repo
    community = repo.create_community(slug, "Hosted Program", host=f"{slug}.test")
    role = repo.create_role(
        community.id,
        "director" if is_admin else "member",
        "Director" if is_admin else "Member",
        is_admin=is_admin,
    )
    if user_id is None:
        user = repo.create_user(f"{slug}@example.com", "hash")
        user_id = user.id
    membership = repo.create_membership(
        community.id,
        user_id,
        role.id,
        username,
        "Hosted Lane",
    )
    character = repo.create_character(
        community.id,
        membership.id,
        "hosted-face",
        "Hosted Face",
        make_default=True,
    )
    return community, user_id, membership.id, character.id


def _dev_request(headers: dict[str, str]) -> SimpleNamespace:
    return SimpleNamespace(headers=headers)


def test_default_database_path_uses_railway_volume_when_available(monkeypatch) -> None:
    monkeypatch.delenv("ELBYSODIC_DB_PATH", raising=False)
    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", "/app/var")

    assert default_database_path() == Path("/app/var/elbysodic.sqlite3")


def test_explicit_database_path_overrides_railway_volume(monkeypatch) -> None:
    monkeypatch.setenv("ELBYSODIC_DB_PATH", "/app/custom/forum.sqlite3")
    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", "/app/var")

    assert default_database_path() == Path("/app/custom/forum.sqlite3")


def test_unknown_external_host_falls_back_to_default_community() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get(
                "/",
                headers={"host": "elbysodic-demo.up.railway.app"},
            )

        assert response.status == 200
        assert "X-Men Apocalypse" in response.text
        assert "Rogue" in response.text

    asyncio.run(run())


def test_unknown_external_host_is_rejected_after_default_community_has_host() -> None:
    services = create_services(path=":memory:")
    services.repo.connection.execute(
        "UPDATE communities SET host = ? WHERE id = ?",
        ("demo.example.com", services.seed.community.id),
    )
    services.repo.connection.commit()

    with pytest.raises(LookupError, match=r"community not found for host: unknown\.example\.com"):
        services.for_request(_dev_request({"host": "unknown.example.com"}))


def test_health_check_does_not_require_registered_community_host() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get(
                "/health",
                headers={"host": "elbysodic-demo.up.railway.app"},
            )

        assert response.status == 200
        assert response.text == "ok\n"
        assert "app;dur=" in _response_header(response, "Server-Timing")
        assert float(_response_header(response, "X-Elbysodic-Route-Time-Ms")) >= 0

    asyncio.run(run())


def test_framework_probes_bypass_login_and_cover_sqlite(tmp_path: Path) -> None:
    async def run() -> None:
        services = create_services(path=tmp_path / "probe.sqlite3", seed_demo=False)
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            livez = await client.get("/livez")
            ready = await client.get("/ready")

        assert livez.status == 200
        assert livez.text == "ok"
        assert ready.status == 200
        assert ready.text == "ready"
        assert "Server-Timing" not in _response_headers(livez, "Server-Timing")
        assert "Server-Timing" not in _response_headers(ready, "Server-Timing")

    asyncio.run(run())


def test_concurrent_rendered_get_navigation_stays_stable(tmp_path: Path) -> None:
    async def run() -> None:
        services = create_services(path=tmp_path / "rapid-navigation.sqlite3")
        app = create_app(debug=False, services=services)
        routes = [
            ("/network", "Find a realm that fits the story you want to write."),
            ("/c/rl-nyc/my/threads", "RL NYC"),
            ("/c/rl-small-town/boards/town-hall?filter=mine", "RL Small Town"),
            ("/c/jurassic-park-universe/world", "Jurassic Park Universe"),
            ("/c/x-men-apocalypse/boards/danger-room", "X-Men Apocalypse"),
            ("/c/rl-nyc/claims", "RL NYC"),
        ]

        async with TestClient(app) as client:
            for path, _expected in routes:
                warm = await client.get(path)
                assert warm.status == 200

            async def fetch(path: str, expected: str) -> tuple[str, int, str]:
                response = await client.get(path)
                return path, response.status, response.text if expected in response.text else ""

            responses = await asyncio.gather(
                *(fetch(path, expected) for path, expected in routes * 2)
            )

        for path, status, expected_text in responses:
            assert status == 200, path
            assert expected_text, path

    asyncio.run(run())


def test_rendered_get_navigation_does_not_write_to_database() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        app = create_app(debug=False, services=services)
        routes = (
            "/network",
            "/c/rl-nyc/my/threads",
            "/c/rl-small-town/boards/town-hall?filter=mine",
            "/c/x-men-apocalypse/boards/danger-room",
        )

        async with TestClient(app) as client:
            for path in routes:
                with trace_sql(services.repo.connection) as trace:
                    response = await client.get(path)
                assert response.status == 200, path
                assert trace.writes == [], path

    asyncio.run(run())


def test_rendered_route_query_budgets_are_tracked() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        app = create_app(debug=False, services=services)
        budgets = {
            "/network": 105,
            "/c/x-men-apocalypse": 345,
            "/c/x-men-apocalypse/locations": 150,
            "/c/x-men-apocalypse/community": 305,
            "/c/x-men-apocalypse/world/b-24-winter": 155,
            "/c/rl-nyc/my/threads": 80,
            "/c/rl-small-town/boards/town-hall?filter=mine": 105,
            "/c/x-men-apocalypse/boards/danger-room": 180,
            "/c/rl-nyc/claims": 70,
        }

        async with TestClient(app) as client:
            for path, budget in budgets.items():
                warm = await client.get(path)
                assert warm.status == 200, path

                with trace_sql(services.repo.connection) as trace:
                    response = await client.get(path)

                assert response.status == 200, path
                assert trace.count <= budget, path

    asyncio.run(run())


def test_board_thread_batch_render_preserves_scene_cards() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get("/c/x-men-apocalypse/boards/danger-room")

        assert response.status == 200
        assert "X-Men Apocalypse" in response.text
        assert "Danger Room" in response.text
        assert "Cast" in response.text
        assert "writer" in response.text
        assert "town-hall" not in response.text

    asyncio.run(run())


def test_scaled_board_page_stays_within_batched_query_budget() -> None:
    async def run() -> None:
        services = _scale_board_services(thread_count=30)
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            warm = await client.get("/c/x-men-apocalypse/boards/scale-yard")
            assert warm.status == 200

            with trace_sql(services.repo.connection) as trace:
                response = await client.get("/c/x-men-apocalypse/boards/scale-yard")

        assert response.status == 200
        assert "Scale Yard" in response.text
        assert "Scale Thread 29" in response.text
        assert trace.count <= 150

    asyncio.run(run())


def test_writer_queue_batch_render_preserves_lenses() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            active_face = await client.get("/c/rl-nyc/my/threads")
            whole_roster = await client.get("/c/rl-nyc/my/threads?character=all")

        assert active_face.status == 200
        assert whole_roster.status == 200
        assert "My threads" in active_face.text
        assert "Queue lens: active face" in active_face.text
        assert "Needs reply" in active_face.text or "Queue clear" in active_face.text
        assert "Queue lens: whole roster" in whole_roster.text
        assert "Waiting" in whole_roster.text or "Queue clear" in whole_roster.text

    asyncio.run(run())


def test_scaled_my_threads_stays_within_batched_query_budget() -> None:
    async def run() -> None:
        services = _scale_board_services(thread_count=30)
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            warm = await client.get("/c/x-men-apocalypse/my/threads")
            assert warm.status == 200

            with trace_sql(services.repo.connection) as trace:
                response = await client.get("/c/x-men-apocalypse/my/threads")

        assert response.status == 200
        assert "Scale Realm" in response.text
        assert "Scale Thread 0" in response.text
        assert trace.count <= 100

    asyncio.run(run())


def test_public_network_catalog_hides_member_state(monkeypatch: pytest.MonkeyPatch) -> None:
    async def run() -> None:
        monkeypatch.setenv("ELBYSODIC_ENV", "production")
        monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "x" * 32)
        monkeypatch.setenv("ELBYSODIC_ALLOWED_HOSTS", "*")
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            response = await client.get("/network")

        assert response.status == 200
        assert "Explore" in response.text
        assert "playing as" not in response.text
        assert "Dev personas" not in response.text
        assert "Log out" not in response.text
        assert "unread" not in response.text

    asyncio.run(run())


def test_scaled_signed_in_network_stays_within_batched_query_budget() -> None:
    async def run() -> None:
        services = _scale_network_services(community_count=12)
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            warm = await client.get("/network")
            assert warm.status == 200

            with trace_sql(services.repo.connection) as trace:
                response = await client.get("/network")

        assert response.status == 200
        assert "Find a realm that fits the story you want to write." in response.text
        assert "Hosted Program" in response.text
        assert trace.count <= 85

    asyncio.run(run())


def test_visible_unread_notification_counts_use_batched_membership_query() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    assert services.seed.default_character is not None
    contexts = [
        (
            services.seed.community.id,
            services.seed.membership,
            repo.get_role(services.seed.community.id, services.seed.membership.role_id),
            services.seed.default_character.id,
        )
    ]
    for index in range(12):
        community, _user_id, membership_id, character_id = _add_hosted_membership(
            services,
            slug=f"notify-scale-{index}",
            user_id=services.seed.user.id,
            username=f"notify-scale-{index}",
        )
        membership = repo.get_membership(community.id, membership_id)
        contexts.append(
            (
                community.id,
                membership,
                repo.get_role(community.id, membership.role_id),
                character_id,
            )
        )
    for community_id, membership, _role, character_id in contexts:
        repo.create_notification(
            community_id,
            membership.id,
            kind="application_accepted",
            character_id=character_id,
            actor_membership_id=membership.id,
            actor_character_id=character_id,
        )

    with trace_sql(repo.connection) as trace:
        counts = visible_unread_notification_counts(
            repo,
            [(community_id, membership, role) for community_id, membership, role, _ in contexts],
        )

    assert counts == {membership.id: 1 for _community_id, membership, _role, _ in contexts}
    batch_queries = [
        statement
        for statement in trace.statements
        if "JOIN requested" in statement and "notifications.read_at IS NULL" in statement
    ]
    per_membership_notification_queries = [
        statement
        for statement in trace.statements
        if "FROM notifications" in statement
        and "WHERE community_id" in statement
        and "membership_id" in statement
        and "LIMIT" in statement
    ]
    assert len(batch_queries) == 1
    assert per_membership_notification_queries == []


def test_mark_all_notifications_read_has_no_visible_count_cap() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    viewer = services.viewer()
    assert services.seed.default_character is not None
    other_membership = repo.create_membership(
        viewer.community.id,
        repo.create_user("hidden-notify@example.com", "hash").id,
        viewer.membership.role_id,
        "hidden-notify",
        "Hidden Notify",
    )
    hidden_character = repo.create_character(
        viewer.community.id,
        other_membership.id,
        "hidden-notify-face",
        "Hidden Notify Face",
    )

    with repo.transaction():
        for _index in range(1001):
            repo.create_notification(
                viewer.community.id,
                viewer.membership.id,
                kind="application_accepted",
                character_id=services.seed.default_character.id,
                actor_membership_id=viewer.membership.id,
                actor_character_id=services.seed.default_character.id,
            )
        hidden_notification = repo.create_notification(
            viewer.community.id,
            viewer.membership.id,
            kind="application_accepted",
            character_id=hidden_character.id,
            actor_membership_id=other_membership.id,
            actor_character_id=hidden_character.id,
        )

    assert (
        count_visible_unread_notifications(
            repo,
            viewer.community.id,
            viewer.membership,
            viewer.role,
        )
        == 1001
    )

    with trace_sql(repo.connection) as trace:
        mark_all_notifications_read(repo, viewer)

    assert (
        count_visible_unread_notifications(
            repo,
            viewer.community.id,
            viewer.membership,
            viewer.role,
        )
        == 0
    )
    assert repo.count_unread_notifications(viewer.community.id, viewer.membership.id) == 1
    assert repo.get_notification(viewer.community.id, hidden_notification.id).read_at is None
    notification_updates = [
        statement
        for statement in trace.statements
        if statement.strip().upper().startswith("UPDATE notifications".upper())
    ]
    # SQLite's trace callback repeats the originating statement while row
    # triggers execute; the operation is still one distinct bulk UPDATE.
    assert len(set(notification_updates)) == 1
    assert "json_each" in notification_updates[0]


def test_request_identity_resolves_membership_inside_selected_community() -> None:
    services = create_services(path=":memory:")
    community, user_id, membership_id, character_id = _add_hosted_membership(
        services,
        user_id=services.seed.user.id,
    )

    scoped = services.for_request(
        _dev_request(
            {
                "x-elbysodic-community": community.slug,
                "x-elbysodic-user-id": str(user_id),
            }
        )
    )

    viewer = scoped.viewer()
    assert viewer.community.id == community.id
    assert viewer.membership.id == membership_id
    assert viewer.current_character is not None
    assert viewer.current_character.id == character_id
    assert viewer.current_character.community_id == community.id


def test_request_identity_does_not_leak_roles_between_communities() -> None:
    services = create_services(path=":memory:")
    community, user_id, _membership_id, _character_id = _add_hosted_membership(
        services,
        user_id=services.seed.user.id,
        is_admin=False,
    )

    default_viewer = services.viewer()
    hosted_viewer = services.for_request(
        _dev_request(
            {
                "host": "hosted.test",
                "x-elbysodic-user-id": str(user_id),
            }
        )
    ).viewer()

    assert default_viewer.community.id != hosted_viewer.community.id
    assert hosted_viewer.community.id == community.id
    assert hosted_viewer.role.community_id == community.id
    assert not hosted_viewer.role.is_admin


def test_request_identity_rejects_membership_that_belongs_to_another_user() -> None:
    services = create_services(path=":memory:")
    community, _user_id, membership_id, _character_id = _add_hosted_membership(services)
    other_user = services.repo.create_user("other-hosted@example.com", "hash")

    with pytest.raises(PermissionError, match="does not belong to user"):
        services.for_request(
            _dev_request(
                {
                    "x-elbysodic-community": community.slug,
                    "x-elbysodic-membership-id": str(membership_id),
                    "x-elbysodic-user-id": str(other_user.id),
                }
            )
        )


def test_request_identity_rejects_inactive_membership_viewer() -> None:
    services = create_services(path=":memory:")
    community, user_id, membership_id, _character_id = _add_hosted_membership(services)
    services.repo.connection.execute(
        "UPDATE community_memberships SET is_active = 0 WHERE community_id = ? AND id = ?",
        (community.id, membership_id),
    )
    services.repo.connection.commit()

    scoped = services.for_request(
        _dev_request(
            {
                "x-elbysodic-community": community.slug,
                "x-elbysodic-user-id": str(user_id),
            }
        )
    )

    with pytest.raises(PermissionError, match="is not active"):
        scoped.viewer()


def test_request_scoped_page_renders_selected_community_membership() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )
        community, user_id, _membership_id, _character_id = _add_hosted_membership(
            services,
            user_id=services.seed.user.id,
        )

        async with TestClient(app) as client:
            default_members = await client.get("/members")
            hosted_members = await client.get(
                "/members",
                headers={
                    "x-elbysodic-community": community.slug,
                    "x-elbysodic-user-id": str(user_id),
                },
            )

        assert default_members.status == 200
        assert hosted_members.status == 200
        assert "X-Men Apocalypse" in default_members.text
        assert "Hosted Program" in hosted_members.text
        assert "Hosted Lane" in hosted_members.text
        assert "Hosted Face" in hosted_members.text
        assert "Cyclops" not in hosted_members.text

    asyncio.run(run())


def test_tenant_prefixed_route_resolves_community_before_local_slug() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get("/c/jurassic-park-universe/boards/paddock-twelve")

        assert response.status == 200
        assert "Jurassic Park Universe" in response.text
        assert "Paddock Twelve" in response.text
        assert (
            'class="elbysodic-community-brand__name">Jurassic Park Universe</span>' in response.text
        )

    asyncio.run(run())


def test_tenant_prefixed_route_overrides_development_community_header() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get(
                "/c/jurassic-park-universe/world/paddock-twelve-incident",
                headers={"x-elbysodic-community": "x-men-apocalypse"},
            )

        assert response.status == 200
        assert "Jurassic Park Universe" in response.text
        assert "Current Event: Paddock Twelve" in response.text
        assert (
            'class="elbysodic-community-brand__name">Jurassic Park Universe</span>' in response.text
        )

    asyncio.run(run())


def test_tenant_prefixed_route_keeps_scoped_links_inside_prefix() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get("/c/jurassic-park-universe/boards/paddock-twelve")

        assert response.status == 200
        assert 'href="/c/jurassic-park-universe"' in response.text
        assert 'href="/c/jurassic-park-universe/world"' in response.text
        assert 'href="/c/jurassic-park-universe/boards/paddock-twelve/threads/new"' in response.text
        assert (
            'name="next" value="/c/jurassic-park-universe/boards/paddock-twelve"' in response.text
        )
        assert "/login?next=%2Fboards%2Fpaddock-twelve" not in response.text
        assert (
            "/login?next=%2Fc%2Fjurassic-park-universe%2Fboards%2Fpaddock-twelve"
            not in response.text
        )
        assert 'href="/elbysodic-static/elbysodic-theme.css' in response.text
        assert 'href="/c/jurassic-park-universe/elbysodic-static' not in response.text

    asyncio.run(run())


def test_tenant_scoping_preserves_authored_form_values() -> None:
    response = Response(
        """
        <a href="/world">World</a>
        <a href="/" data-elbysodic-global-link>Global home</a>
        <a href="/claims?status=claimed&amp;q=magneto">Filtered claims</a>
        <form action="/boards/danger-room/threads/new">
          <input name="title" value="/not-a-route">
          <input name="next" value="/boards/danger-room">
          <input name="return_to" value="/claims?status=claimed&amp;q=magneto">
        </form>
        """,
        content_type="text/html",
    )

    scoped = scope_response_urls(response, "x-men-apocalypse")

    assert isinstance(scoped.body, str)
    assert 'href="/c/x-men-apocalypse/world"' in scoped.body
    assert 'href="/" data-elbysodic-global-link' in scoped.body
    assert 'href="/c/x-men-apocalypse/claims?status=claimed&amp;q=magneto"' in scoped.body
    assert 'action="/c/x-men-apocalypse/boards/danger-room/threads/new"' in scoped.body
    assert 'name="title" value="/not-a-route"' in scoped.body
    assert 'name="next" value="/c/x-men-apocalypse/boards/danger-room"' in scoped.body
    assert (
        'name="return_to" value="/c/x-men-apocalypse/claims?status=claimed&amp;q=magneto"'
        in scoped.body
    )


def test_request_scoped_path_uses_chirp_url_scope() -> None:
    request = SimpleNamespace(url_scope=RequestUrlScope("/c/x-men-apocalypse"))

    def scoped_url(path: str) -> str:
        return request.url_scope.apply(path)

    request.scoped_url = scoped_url

    assert request_scoped_path(request, "/mentionables/search") == (
        "/c/x-men-apocalypse/mentionables/search"
    )
    assert request_scoped_path(request, "/c/x-men-apocalypse/world") == (
        "/c/x-men-apocalypse/world"
    )


def test_composer_forms_save_drafts_on_submit_instead_of_clearing_early() -> None:
    composer_paths = [
        Path("src/elbysodic/web/pages/boards/{board_slug}/threads/new/page.html"),
        Path("src/elbysodic/web/pages/boards/{board_slug}/threads/{thread_slug}/page.html"),
        Path(
            "src/elbysodic/web/pages/boards/{board_slug}/threads/{thread_slug}/posts/"
            "{post_id}/edit/page.html"
        ),
    ]

    for path in composer_paths:
        template = path.read_text(encoding="utf-8")
        assert '@submit="clearDraft()"' not in template
        assert '@submit="submitDraft()"' in template


def test_unknown_tenant_prefix_returns_not_found() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get("/c/not-a-program/world")

        assert response.status == 404
        assert "We could not find that realm." in response.text
        assert "not-a-program is not a program on this studio network" in response.text
        assert "Open Studio Network" in response.text

    asyncio.run(run())


def test_tenant_prefix_does_not_wrap_app_global_routes() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            login = await client.get("/c/x-men-apocalypse/login")
            malformed_login = await client.get("/c/x-men-apocalypse//login")
            malformed_network = await client.get("/c/x-men-apocalypse//network")
            malformed_health = await client.get("/c/x-men-apocalypse//health")
            malformed_request_access = await client.get("/c/x-men-apocalypse//request-access")
            malformed_world = await client.get("/c/x-men-apocalypse//world")
            health = await client.get("/c/x-men-apocalypse/health")
            static = await client.get("/c/x-men-apocalypse/elbysodic-static/elbysodic-theme.css")

        assert login.status == 404
        assert malformed_login.status == 404
        assert malformed_network.status == 404
        assert malformed_health.status == 404
        assert malformed_request_access.status == 404
        assert malformed_world.status == 404
        assert health.status == 404
        assert static.status == 404

    asyncio.run(run())


def test_boosted_main_navigation_uses_chirp_shell_outlet() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get(
                "/wanted/brotherhood-rival-for-rogue",
                headers={
                    "HX-Request": "true",
                    "HX-Boosted": "true",
                    "HX-Target": "main",
                },
            )

        assert response.status == 200
        assert 'id="page-content"' in response.text
        assert 'id="page-root"' in response.text
        assert "HX-Reselect" not in response.headers

    asyncio.run(run())


def test_shell_brand_navigation_uses_full_boundary_navigation() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get("/boards/cerebro")

        assert response.status == 200
        realm_switcher = re.search(
            r'<summary class="elbysodic-realm-switcher__summary"'
            r'[^>]*aria-label="Realm switcher: X-Men Apocalypse"',
            response.text,
        )
        assert realm_switcher is not None
        product_home_link = re.search(
            r'<a class="[^"]*elbysodic-realm-switcher__link[^"]*"'
            r'\s+href="/"[^>]*data-elbysodic-global-link[^>]*hx-boost="false"',
            response.text,
        )
        assert product_home_link is not None
        assert "<strong>Elbysodic</strong>" in response.text
        assert "<small>Network home</small>" in response.text
        assert re.search(
            r'<a class="[^"]*elbysodic-primary-rail__link[^"]*"\s+href="/locations"'
            r'[^>]*aria-label="Locations"[^>]*hx-sync="#main:replace"',
            response.text,
        )
        assert re.search(
            r'<a class="[^"]*elbysodic-sidebar-destination[^"]*"\s+href="/locations"'
            r'[^>]*hx-sync="#main:replace"',
            response.text,
        )

    asyncio.run(run())


def test_tenant_prefixed_boosted_main_navigation_keeps_links_in_chirp_shell_outlet() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get(
                "/c/jurassic-park-universe/boards/paddock-twelve",
                headers={
                    "HX-Request": "true",
                    "HX-Boosted": "true",
                    "HX-Target": "main",
                },
            )

        assert response.status == 200
        assert 'id="page-content"' in response.text
        assert 'id="page-root"' in response.text
        assert 'href="/c/jurassic-park-universe/boards/paddock-twelve/threads/new"' in response.text
        assert "HX-Reselect" not in response.headers

    asyncio.run(run())


def test_tenant_prefixed_identity_and_casting_routes_scope_rendered_links() -> None:
    async def run() -> None:
        app = _app()
        community_slug = get_services().seed.community.slug

        async with TestClient(app) as client:
            character = await client.get(f"/c/{community_slug}/characters/rogue")
            wanted = await client.get(f"/c/{community_slug}/wanted/brotherhood-rival-for-rogue")
            application = await client.get(f"/c/{community_slug}/applications/new")

        assert character.status == 200
        assert "Rogue" in character.text
        assert f'href="/c/{community_slug}/my/threads?character=rogue"' in character.text
        assert f'href="/c/{community_slug}/wanted/brotherhood-rival-for-rogue"' in character.text

        assert wanted.status == 200
        assert "Brotherhood rival from Rogue" in wanted.text
        assert f'href="/c/{community_slug}/characters/rogue"' in wanted.text
        assert (
            f'name="next" value="/c/{community_slug}/wanted/brotherhood-rival-for-rogue"'
            in wanted.text
        )

        assert application.status == 200
        assert "Start a face" in application.text
        assert "Create draft face" in application.text
        assert 'data-elbysodic-submit-label="Creating draft face..."' in application.text
        assert f'href="/c/{community_slug}/applications"' in application.text
        assert 'href="/elbysodic-static/elbysodic-theme.css' in application.text
        assert f'href="/c/{community_slug}/elbysodic-static' not in application.text

    asyncio.run(run())


def test_tenant_prefixed_thread_routes_scope_composer_redirects() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        community_slug = services.seed.community.slug
        character = services.viewer().current_character
        assert character is not None

        async with TestClient(app) as client:
            thread = await client.get(
                f"/c/{community_slug}/boards/danger-room/threads/sentinel-drill"
            )
            composer = await client.get(f"/c/{community_slug}/boards/danger-room/threads/new")
            created = await client.post(
                f"/c/{community_slug}/boards/danger-room/threads/new",
                body=urlencode(
                    {
                        "character_id": str(character.id),
                        "title": "Tenant Prefix Drill",
                        "status": "active",
                        "location": "Danger Room",
                        "timeline": "After class",
                        "summary": "A prefixed composer regression.",
                        "posting_mode": "freeform",
                        "body": "Opening from a tenant-prefixed composer.",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert thread.status == 200
        assert "Sentinel drill after midnight" in thread.text
        assert 'data-elbysodic-submit-label="Posting..."' in thread.text
        assert f'href="/c/{community_slug}/boards/danger-room"' in thread.text
        assert (
            f'name="next" value="/c/{community_slug}/boards/danger-room/threads/sentinel-drill"'
            in thread.text
        )

        assert composer.status == 200
        assert "Start scene" in composer.text
        assert 'data-elbysodic-submit-label="Starting scene..."' in composer.text
        assert f'href="/c/{community_slug}/boards/danger-room"' in composer.text
        assert f"/c/{community_slug}/mentionables/search" in composer.text

        assert created.status == 302
        assert _response_header(created, "location").startswith(
            f"/c/{community_slug}/boards/danger-room/threads/tenant-prefix-drill#post-"
        )

    asyncio.run(run())


def test_identity_switcher_persists_dev_membership_cookie() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        network_option = next(
            option
            for option in services.viewer().identity_options
            if option.community.slug == "hp-universe"
        )

        async with TestClient(app) as client:
            before = await client.get("/notifications")
            switch = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(network_option.membership.id),
                        "character_id": "0",
                        "next": "/notifications",
                    }
                ).encode(),
                headers=_FORM,
            )
            set_cookie = _response_header(switch, "set-cookie")
            cookie = set_cookie.split(";", 1)[0]
            after = await client.get("/notifications", headers={"Cookie": cookie})

        assert before.status == 200
        assert "X-Men Universe" not in before.text
        assert "HP Universe" in before.text
        assert "Jurassic Park Universe" in before.text
        assert "RL NYC" in before.text
        assert "RL Small Town" in before.text
        assert switch.status == 302
        assert "elbysodic_dev_identity=" in set_cookie
        assert "data-elbysodic-submit-group" in before.text
        assert 'data-elbysodic-submit-label="Entering HP Universe..."' in before.text
        assert after.status == 200
        assert '<span class="elbysodic-community-brand__name">HP Universe</span>' in after.text
        assert "Director in HP Universe" in after.text
        assert "playing as Rowan Ash" in after.text
        assert '<style id="elbysodic-program-theme">' in after.text
        assert "--chirpui-accent: #c8a6ff;" in after.text
        assert "--chirpui-ui-font-family: Georgia, serif;" in after.text

    asyncio.run(run())


def test_identity_resolution_reports_sources_for_tenant_and_cookie_recovery() -> None:
    services = create_services(path=":memory:")
    resolver = services._identity_resolver
    hp = services.repo.get_community_by_slug("hp-universe")
    hp_membership = services.repo.get_membership_for_user(hp.id, services.seed.user.id)
    tenant_request = SimpleNamespace(
        headers={},
        cookies={"elbysodic_dev_identity": f"{hp.id}:{services.seed.user.id}:999999"},
        _cache={TENANT_SLUG_CACHE_KEY: hp.slug},
    )

    resolution = resolver.resolve_with_details(tenant_request)

    assert resolution.context.community_id == hp.id
    assert resolution.context.membership_id == hp_membership.id
    assert resolution.community_source == "tenant_prefix"
    assert resolution.user_source == "dev_cookie"
    assert resolution.membership_source == "user_membership"
    assert resolution.recovery_reason == "stale dev membership"
    assert resolution.is_session_backed is False


def test_tenant_prefixed_board_handles_invalid_membership_role_as_identity_failure() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        small_town = services.repo.get_community_by_slug("rl-small-town")
        membership = services.repo.get_membership_for_user(
            small_town.id,
            services.seed.user.id,
        )
        xmen_role = services.repo.get_role_by_slug(services.seed.community.id, "member")
        services.repo.connection.execute(
            "DROP TRIGGER trg_community_memberships_tenant_pair_update"
        )
        services.repo.connection.execute(
            """
            UPDATE community_memberships
            SET role_id = ?
            WHERE community_id = ? AND id = ?
            """,
            (xmen_role.id, small_town.id, membership.id),
        )
        services.repo.connection.commit()
        cookie = f"elbysodic_dev_identity={small_town.id}:{services.seed.user.id}:{membership.id}"

        async with TestClient(app) as client:
            full = await client.get(
                "/c/rl-small-town/boards/town-hall?filter=mine",
                headers={"Cookie": cookie},
            )
            fragment = await client.get(
                "/c/rl-small-town/boards/town-hall?filter=mine",
                headers={
                    "Cookie": cookie,
                    "HX-Request": "true",
                    "HX-Boosted": "true",
                    "HX-Target": "main",
                },
            )

        assert full.status == 403
        assert "That realm membership needs staff attention." in full.text
        assert "Your identity did not change." in full.text
        assert "Internal Server Error" not in full.text
        assert "playing as" not in full.text
        assert fragment.status == 403
        assert 'data-status="403"' in fragment.text
        assert "That realm membership needs staff attention." in fragment.text

    asyncio.run(run())


def test_dev_personas_are_gated_by_development_tools() -> None:
    async def run() -> None:
        disabled_app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=False,
        )

        async with TestClient(disabled_app) as client:
            disabled = await client.get("/dev/personas")
        enabled_app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )
        async with TestClient(enabled_app) as client:
            enabled = await client.get("/dev/personas")

        assert disabled.status == 404
        assert enabled.status == 200
        assert "Dev Personas" in enabled.text
        assert "xmen_staff" in enabled.text
        assert "HP director" in enabled.text
        assert "inactive" in enabled.text

    asyncio.run(run())


def test_htmx_timing_harness_is_gated_by_development_tools() -> None:
    async def run() -> None:
        disabled_app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=False,
        )
        async with TestClient(disabled_app) as client:
            disabled = await client.get("/")

        enabled_app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )
        async with TestClient(enabled_app) as client:
            enabled = await client.get("/")

        assert disabled.status == 200
        assert enabled.status == 200
        assert "elbysodic-htmx-timing.js" not in disabled.text
        assert "elbysodic-htmx-timing.js" in enabled.text

    asyncio.run(run())


def test_seed_persona_matrix_names_multi_community_role_differences() -> None:
    services = create_services(path=":memory:")
    xmen_writer = resolve_seed_persona(services.repo, "xmen_writer")
    hp_director = resolve_seed_persona(services.repo, "hp_director")
    nyc_writer = resolve_seed_persona(services.repo, "nyc_writer")
    harbor_director = resolve_seed_persona(services.repo, "harbor_director")
    signal_director = resolve_seed_persona(services.repo, "signal_director")
    wayfarer_director = resolve_seed_persona(services.repo, "wayfarer_director")
    inactive = resolve_seed_persona(services.repo, "xmen_inactive")

    assert (
        xmen_writer.user.id
        == hp_director.user.id
        == nyc_writer.user.id
        == harbor_director.user.id
        == signal_director.user.id
        == wayfarer_director.user.id
    )
    assert xmen_writer.community.slug == "x-men-apocalypse"
    assert xmen_writer.role.name == "Member"
    assert not xmen_writer.role.is_admin
    assert hp_director.community.slug == "hp-universe"
    assert hp_director.role.name == "Director"
    assert hp_director.role.is_admin
    assert nyc_writer.community.slug == "rl-nyc"
    assert nyc_writer.role.name == "Member"
    assert not nyc_writer.role.is_admin
    assert harbor_director.community.slug == "harbor-society"
    assert harbor_director.role.name == "Director"
    assert harbor_director.character is not None
    assert harbor_director.character.name == "Maris Vale"
    assert signal_director.community.slug == "signal-creek"
    assert signal_director.role.is_admin
    assert wayfarer_director.community.slug == "wayfarer-station"
    assert wayfarer_director.persona.default_path == "/studio/discovery"
    assert inactive.membership.username == "sleepingstar"
    assert not inactive.membership.is_active
    assert inactive.character is not None
    assert inactive.character.name == "Sleeping Star"


def test_dev_persona_switcher_can_change_seeded_user_and_membership() -> None:
    async def run() -> None:
        app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )

        async with TestClient(app) as client:
            page = await client.get("/dev/personas")
            switch = await client.post(
                "/dev/personas",
                body=urlencode(
                    {
                        "persona_key": "xmen_staff",
                        "next": "/studio",
                    }
                ).encode(),
                headers=_FORM,
            )
            set_cookie = _response_header(switch, "set-cookie")
            cookie = set_cookie.split(";", 1)[0]
            studio = await client.get("/studio", headers={"Cookie": cookie})

        assert page.status == 200
        assert "X-Men staff" in page.text
        assert switch.status == 302
        assert _response_header(switch, "location") == "/studio"
        assert "elbysodic_dev_identity=" in set_cookie
        assert "HttpOnly" in set_cookie
        assert "SameSite=lax" in set_cookie
        assert studio.status == 200
        assert "Staff in X-Men Apocalypse" in studio.text
        assert "playing as Moira MacTaggert" in studio.text
        assert 'href="/studio/appearance"' in studio.text
        assert "Director Studio is visible as a preview" not in studio.text

    asyncio.run(run())


def test_dev_persona_switcher_refuses_inactive_seed_persona() -> None:
    async def run() -> None:
        app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )

        async with TestClient(app) as client:
            response = await client.post(
                "/dev/personas",
                body=urlencode(
                    {
                        "persona_key": "xmen_inactive",
                        "next": "/members",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert response.status == 403

    asyncio.run(run())


def test_login_route_creates_account_session_and_membership_context() -> None:
    async def run() -> None:
        app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )

        async with TestClient(app) as client:
            page = await client.get("/login?next=/studio")
            login = await client.post(
                "/login",
                body=urlencode(
                    {
                        "email": "moira@example.com",
                        "password": "password",
                        "next": "/studio",
                    }
                ).encode(),
                headers=_FORM,
            )
            set_cookies = _response_headers(login, "set-cookie")
            cookie_header = "; ".join(cookie.split(";", 1)[0] for cookie in set_cookies)
            studio = await client.get("/studio", headers={"Cookie": cookie_header})

        assert page.status == 200
        assert "Invite/demo accounts use password" in page.text
        assert "/elbysodic-static/brand/elbysodic-mark.svg" in page.text
        assert login.status == 302
        assert _response_header(login, "location") == "/studio"
        assert any(cookie.startswith("elbysodic_session=") for cookie in set_cookies)
        assert any(cookie.startswith("elbysodic_dev_identity=") for cookie in set_cookies)
        assert studio.status == 200
        assert "Staff in X-Men Apocalypse" in studio.text
        assert 'href="/studio/appearance"' in studio.text

    asyncio.run(run())


def test_session_user_overrides_forged_dev_identity_cookie() -> None:
    async def run() -> None:
        app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )
        services = get_services()
        community = services.seed.community
        moira = services.repo.get_membership_by_username(community.id, "moira")

        async with TestClient(app) as client:
            login = await client.post(
                "/login",
                body=urlencode(
                    {
                        "email": "writer@example.com",
                        "password": "password",
                        "next": "/studio",
                    }
                ).encode(),
                headers=_FORM,
            )
            session_cookie = next(
                cookie.split(";", 1)[0]
                for cookie in _response_headers(login, "set-cookie")
                if cookie.startswith("elbysodic_session=")
            )
            forged_identity = f"elbysodic_dev_identity={community.id}:{moira.user_id}:{moira.id}"
            studio = await client.get(
                "/studio",
                headers={"Cookie": f"{session_cookie}; {forged_identity}"},
            )

        assert studio.status == 200
        assert "Member in X-Men Apocalypse" in studio.text
        assert "Director Studio is visible as a preview" in studio.text
        assert "Staff in X-Men Apocalypse" not in studio.text

    asyncio.run(run())


def test_logout_revokes_session_and_clears_identity_cookies() -> None:
    async def run() -> None:
        app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )

        async with TestClient(app) as client:
            login = await client.post(
                "/login",
                body=urlencode(
                    {
                        "email": "moira@example.com",
                        "password": "password",
                        "next": "/studio",
                    }
                ).encode(),
                headers=_FORM,
            )
            cookie_header = "; ".join(
                cookie.split(";", 1)[0] for cookie in _response_headers(login, "set-cookie")
            )
            logout = await client.get("/logout", headers={"Cookie": cookie_header})

        set_cookies = _response_headers(logout, "set-cookie")
        assert logout.status == 302
        assert _response_header(logout, "location") == "/login"
        assert any(
            cookie.startswith("elbysodic_session=") and "Max-Age=0" in cookie
            for cookie in set_cookies
        )
        assert any(
            cookie.startswith("elbysodic_dev_identity=") and "Max-Age=0" in cookie
            for cookie in set_cookies
        )

    asyncio.run(run())


def test_stale_dev_identity_cookie_falls_back_to_membership_for_program() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        community = services.repo.get_community_by_slug("jurassic-park-universe")
        stale_cookie = f"elbysodic_dev_identity={community.id}:1:999999"

        async with TestClient(app) as client:
            response = await client.get("/applications", headers={"Cookie": stale_cookie})

        assert response.status == 200
        assert (
            '<span class="elbysodic-community-brand__name">Jurassic Park Universe</span>'
            in response.text
        )
        assert '<style id="elbysodic-program-theme">' in response.text
        assert "--chirpui-accent: #6bbf7a;" in response.text

    asyncio.run(run())


def test_product_shell_does_not_inherit_current_program_theme() -> None:
    async def run() -> None:
        app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)
        cookie = f"elbysodic_dev_identity={hp.id}:1:{hp_membership.id}"

        async with TestClient(app) as client:
            network = await client.get("/network", headers={"Cookie": cookie})
            community = await client.get("/notifications", headers={"Cookie": cookie})

        assert network.status == 200
        assert community.status == 200
        assert "--chirpui-accent: #c8a6ff;" not in _style_block(
            network.text, "elbysodic-program-theme"
        )
        assert "--chirpui-sidebar-width: 0rem;" in _style_block(
            network.text, "elbysodic-product-shell"
        )
        assert "--chirpui-accent: #c8a6ff;" in _style_block(
            community.text, "elbysodic-program-theme"
        )
        assert "--chirpui-sidebar-width: 0rem;" not in _style_block(
            community.text, "elbysodic-product-shell"
        )

    asyncio.run(run())


def test_boosted_shell_navigation_carries_theme_boundary_oob() -> None:
    async def run() -> None:
        app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)
        cookie = f"elbysodic_dev_identity={hp.id}:1:{hp_membership.id}"
        hx_headers = {
            "Cookie": cookie,
            "HX-Request": "true",
            "HX-Boosted": "true",
            "HX-Target": "main",
        }

        async with TestClient(app) as client:
            network = await client.get("/network", headers=hx_headers)
            community = await client.get("/notifications", headers=hx_headers)

        assert network.status == 200
        assert community.status == 200
        assert "--chirpui-accent: #c8a6ff;" not in _oob_block(
            network.text, "elbysodic-program-theme"
        )
        assert "--chirpui-sidebar-width: 0rem;" in _oob_block(
            network.text, "elbysodic-product-shell"
        )
        assert 'id="page-root" hx-boost="false"' in network.text
        assert "--chirpui-accent: #c8a6ff;" in _oob_block(community.text, "elbysodic-program-theme")
        assert "--chirpui-sidebar-width: 0rem;" not in _oob_block(
            community.text, "elbysodic-product-shell"
        )

    asyncio.run(run())


def test_application_room_for_other_program_renders_realm_recovery() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)
        cookie = f"elbysodic_dev_identity={hp.id}:1:{hp_membership.id}"

        async with TestClient(app) as client:
            response = await client.get(
                "/applications/asha-bennett",
                headers={"Cookie": cookie},
            )

        assert response.status == 200
        assert '<span class="elbysodic-community-brand__name">HP Universe</span>' in response.text
        assert "That face lives in Jurassic Park Universe." in response.text
        assert "Switch to Jurassic Park Universe" in response.text
        assert 'name="next" value="/applications/asha-bennett"' in response.text
        assert 'href="/applications"' in response.text

    asyncio.run(run())


def test_cross_realm_character_url_renders_switchable_recovery() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)
        cookie = f"elbysodic_dev_identity={hp.id}:1:{hp_membership.id}"

        async with TestClient(app) as client:
            response = await client.get(
                "/characters/asha-bennett",
                headers={"Cookie": cookie},
            )

        assert response.status == 200
        assert "That face lives in Jurassic Park Universe." in response.text
        assert 'name="next" value="/characters/asha-bennett"' in response.text
        assert "Open Roster" in response.text

    asyncio.run(run())


def test_cross_realm_character_recovery_ignores_inactive_faces() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hosted, _user_id, inactive_membership_id, _character_id = _add_hosted_membership(
            services,
            slug="retired-program",
            user_id=services.seed.user.id,
            username="retired-realm",
        )
        services.repo.create_character(
            hosted.id,
            inactive_membership_id,
            "retired-cross-face",
            "Retired Cross Face",
        )
        services.repo.connection.execute(
            "UPDATE community_memberships SET is_active = 0 WHERE community_id = ? AND id = ?",
            (hosted.id, inactive_membership_id),
        )
        services.repo.connection.commit()

        async with TestClient(app) as client:
            response = await client.get("/characters/retired-cross-face")

        assert response.status == 200
        assert "That face is not in X-Men Apocalypse." in response.text
        assert "That face lives in Hosted Program." not in response.text
        assert "Switch to Hosted Program" not in response.text

    asyncio.run(run())


def test_cross_realm_character_recovery_hides_non_switchable_program_names() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hosted, _user_id, membership_id, _character_id = _add_hosted_membership(
            services,
            slug="private-program",
            username="private-realm",
        )
        services.repo.create_character(
            hosted.id,
            membership_id,
            "private-cross-face",
            "Private Cross Face",
        )

        async with TestClient(app) as client:
            response = await client.get("/characters/private-cross-face")

        assert response.status == 200
        assert "That face is not in X-Men Apocalypse." in response.text
        assert "That face lives in Hosted Program." not in response.text
        assert "private-program" not in response.text
        assert "Switch to Hosted Program" not in response.text

    asyncio.run(run())


def test_cross_realm_material_url_renders_switchable_recovery() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)
        cookie = f"elbysodic_dev_identity={hp.id}:1:{hp_membership.id}"

        async with TestClient(app) as client:
            response = await client.get(
                "/world/paddock-twelve-incident",
                headers={"Cookie": cookie},
            )

        assert response.status == 200
        assert "That world material lives in Jurassic Park Universe." in response.text
        assert 'name="next" value="/world/paddock-twelve-incident"' in response.text
        assert "Open Guidebook" in response.text

    asyncio.run(run())


def test_prefixed_cross_realm_recovery_switches_to_target_tenant() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        jurassic = services.repo.get_community_by_slug("jurassic-park-universe")
        jurassic_membership = services.repo.get_membership_for_user(
            jurassic.id,
            services.seed.user.id,
        )

        async with TestClient(app) as client:
            recovery = await client.get(
                f"/c/{services.seed.community.slug}/world/paddock-twelve-incident",
            )
            switch = await _switch_membership(
                client,
                jurassic_membership,
                "/c/jurassic-park-universe/world/paddock-twelve-incident",
            )

        assert recovery.status == 200
        assert "/elbysodic-static/brand/elbysodic-mark.svg" in recovery.text
        assert "That world material lives in Jurassic Park Universe." in recovery.text
        assert (
            'name="next" value="/c/jurassic-park-universe/world/paddock-twelve-incident"'
            in recovery.text
        )
        assert f'href="/c/{services.seed.community.slug}/world"' in recovery.text
        assert switch.status == 302
        assert (
            _response_header(switch, "location")
            == "/c/jurassic-park-universe/world/paddock-twelve-incident"
        )

    asyncio.run(run())


def test_identity_switch_sanitizes_cross_realm_next_url() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)

        async with TestClient(app) as client:
            response = await _switch_membership(client, hp_membership, "/applications/asha-bennett")

        assert response.status == 302
        assert _response_header(response, "location") == "/applications"

    asyncio.run(run())


def test_identity_switch_sanitizes_cross_realm_plotting_board_and_thread_urls() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)
        cases = (
            ("/plotting/1", "/plotting"),
            ("/c/x-men-apocalypse/plotting/1", "/c/hp-universe/plotting"),
            ("/boards/danger-room", "/locations"),
            (
                "/c/x-men-apocalypse/boards/danger-room/threads/sentinel-drill",
                "/c/hp-universe/locations",
            ),
        )

        async with TestClient(app) as client:
            responses = [
                (await _switch_membership(client, hp_membership, next_url), expected_location)
                for next_url, expected_location in cases
            ]

        for response, expected_location in responses:
            assert response.status == 302
            assert _response_header(response, "location") == expected_location

    asyncio.run(run())


def test_network_directory_lists_programs_and_realm_entry_actions() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.get("/network")

        assert response.status == 200
        assert "Find a realm that fits the story you want to write." in response.text
        assert "Open for browsing" in response.text
        assert "Start with a wanted hook" in response.text
        assert "Start with a current chapter" in response.text
        assert "Home hub" not in response.text
        assert "X-Men Apocalypse" in response.text
        assert "HP Universe" in response.text
        assert "Jurassic Park Universe" in response.text
        assert "RL NYC" in response.text
        assert "RL Small Town" in response.text
        assert "Harbor Society" in response.text
        assert "Signal Creek" in response.text
        assert "Nocturne Row" in response.text
        assert "Crownfall" in response.text
        assert "Afterlight Accord" in response.text
        assert "Brightline" in response.text
        assert "Emberhouse" in response.text
        assert "Gaslight Ward" in response.text
        assert "Wayfarer Station" in response.text
        assert "your current realm is marked when it appears" in response.text
        assert "Request access open" in response.text
        assert "Public activity " in response.text
        assert "Application guide ready" in response.text
        assert "Claims configured" in response.text
        assert "/applications/new" not in response.text
        assert "Start application" not in response.text
        assert 'class="elbysodic-network-card__realm-link"' in response.text
        assert 'aria-label="Preview Jurassic Park Universe"' in response.text
        assert 'class="elbysodic-network-card__icon-action' in response.text
        assert 'aria-label="Read chapter"' in response.text
        assert 'aria-label="Open calls"' in response.text
        assert "elbysodic-network-card__tooltip" in response.text
        assert 'title="Open calls"' not in response.text
        assert "elbysodic-network-search__control" in response.text
        assert "premise, pace, hooks, roster shape" in response.text
        assert "urban supernatural" in response.text
        assert "weird-town mystery" in response.text
        assert "small-town social web" in response.text
        assert "Explore by discovery profile" in response.text
        assert "Premise engine" in response.text
        assert "Play engine" in response.text
        assert "Lore aperture" in response.text
        assert "Start here" in response.text
        assert "Pace and touchpoints" in response.text
        assert "Small Town Social Web" in response.text
        assert "Weird Town Mystery" in response.text
        assert "Court And Faction Fantasy" in response.text
        assert "court" in response.text
        assert "fame" in response.text
        assert "face you want to wear next" not in response.text
        assert "elbysodic-network-card__mark" in response.text
        assert "XMA" in response.text
        assert 'href="/c/jurassic-park-universe/characters" aria-label="3 faces"' in response.text
        assert 'href="/c/jurassic-park-universe/wanted" aria-label="2 wanted"' in response.text
        assert 'href="/c/jurassic-park-universe/world/paddock-twelve-incident"' in response.text

    asyncio.run(run())


def test_network_explore_search_filters_programs() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.get("/network?q=magic school")

        assert response.status == 200
        assert 'value="magic school"' in response.text
        assert "1</strong>\n  <span>realms found</span>" in response.text
        assert "HP Universe" in response.text

    asyncio.run(run())


def test_global_search_renders_public_realm_results() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.get("/search?q=magic school")

        assert response.status == 200
        assert "Search All realms" in response.text
        assert "elbysodic-search-section__header" in response.text
        assert "HP Universe" in response.text
        assert "2 wanted · 3 faces" in response.text
        assert 'href="/c/hp-universe"' in response.text

    asyncio.run(run())


def test_community_search_scopes_to_public_realm_results() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.get("/c/harbor-society/search?q=ledger")

        assert response.status == 200
        assert "Search Harbor Society" in response.text
        assert 'action="/c/harbor-society/search"' in response.text
        assert 'href="/search?q=ledger"' in response.text
        assert "The Ledger Page Under Table Six" in response.text
        assert "Scenes" in response.text
        assert "Try a place, scene, face, hook, or guidebook title." not in response.text

    asyncio.run(run())


def test_original_premise_discovery_routes_support_persona_qa() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        public_app = create_app(debug=False, services=services, dev_tools=True)
        async with TestClient(public_app) as client:
            network = await client.get("/network?q=weird-town mystery")

        assert network.status == 200
        assert "Signal Creek" in network.text
        assert "Weird Town Mystery" in network.text
        assert "face you want to wear next" not in network.text

        persona_expectations = (
            ("harbor_director", "Harbor Society", "Small Town Social Web"),
            ("signal_director", "Signal Creek", "Weird Town Mystery"),
            ("wayfarer_director", "Wayfarer Station", "Strange Frontier"),
        )
        for persona_key, community_name, archetype_label in persona_expectations:
            persona = resolve_seed_persona(services.repo, persona_key)
            persona_app = create_app(
                debug=False,
                services=AppServices(
                    services.repo,
                    DemoSeed(
                        persona.community,
                        persona.user,
                        persona.membership,
                        persona.character,
                    ),
                ),
                dev_tools=True,
            )
            async with TestClient(persona_app) as client:
                studio = await client.get("/studio/discovery")
                realm = await client.get(f"/c/{persona.community.slug}")

            assert persona.persona.default_path == "/studio/discovery"
            assert studio.status == 200
            assert "Discovery profile" in studio.text
            assert community_name in studio.text
            assert archetype_label in studio.text
            assert realm.status == 200
            assert community_name in realm.text

    asyncio.run(run())


def test_original_premise_entry_paths_support_first_face_and_wanted_browsing() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        route_expectations = (
            ("harbor-society", "reporter-source-at-the-club", "Reporter source"),
            ("signal-creek", "cult-survivor-who-remembers-1998", "Cult survivor"),
            ("nocturne-row", "blood-bank-whistleblower", "Blood-bank whistleblower"),
            ("crownfall", "black-market-mage", "Black-market mage"),
            ("afterlight-accord", "archive-thief", "Archive thief"),
            ("brightline", "crisis-photographer", "Crisis photographer"),
            ("emberhouse", "black-market-supplier", "Black-market supplier"),
            ("gaslight-ward", "disgraced-fiance", "Disgraced fiance"),
            ("wayfarer-station", "corporate-auditor", "Corporate auditor"),
        )
        for community_slug, wanted_slug, wanted_title in route_expectations:
            community = services.repo.get_community_by_slug(community_slug)
            role = services.repo.get_role_by_slug(community.id, "member")
            user = services.repo.create_user(f"{community.slug}-applicant@example.com", "hash")
            membership = services.repo.create_membership(
                community.id,
                user.id,
                role.id,
                f"{community.slug}-applicant",
                f"{community.name} Applicant",
            )
            app = create_app(
                debug=False,
                services=AppServices(
                    services.repo,
                    DemoSeed(community, user, membership, None),
                ),
            )
            fields = services.repo.list_application_template_fields(community.id)

            async with TestClient(app) as client:
                hub = await client.get(f"/c/{community.slug}")
                wanted_board = await client.get(f"/c/{community.slug}/wanted")
                wanted_detail = await client.get(f"/c/{community.slug}/wanted/{wanted_slug}")
                applications = await client.get(f"/c/{community.slug}/applications")
                first_face = await client.get(f"/c/{community.slug}/applications/new")

            assert hub.status == 200
            assert community.name in hub.text
            assert "Wanted" in hub.text

            assert wanted_board.status == 200
            assert wanted_title in wanted_board.text
            assert f'href="/c/{community.slug}/wanted/{wanted_slug}"' in wanted_board.text

            assert wanted_detail.status == 200
            assert wanted_title in wanted_detail.text
            assert 'name="prospective_character_name"' in wanted_detail.text
            assert "Pitch a new face for this" in wanted_detail.text

            assert applications.status == 200
            assert "Start application" in applications.text
            assert "Application Guide" in applications.text

            assert first_face.status == 200
            assert "Start a face" in first_face.text
            assert "Face name" in first_face.text
            assert f"This will become your first active face in {community.name}" in first_face.text
            assert "Director fields" in first_face.text
            assert fields
            assert fields[0].label in first_face.text

    asyncio.run(run())


def test_network_directory_enter_realm_sets_identity_cookie() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)

        async with TestClient(app) as client:
            response = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(hp_membership.id),
                        "character_id": "0",
                        "next": "/c/hp-universe",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert response.status == 302
        assert _response_header(response, "location") == "/c/hp-universe"
        assert "elbysodic_dev_identity=" in _response_header(response, "set-cookie")

    asyncio.run(run())


def test_original_premise_gateways_surface_premise_entry_and_scene_hubs() -> None:
    services = _seeded_services()
    boilerplate_copy = (
        "Public preview copy is safe to read before a writer has a face here.",
        "Public places, institutions, and social rooms have visible doors into play.",
        "Published premise, event, or guide material can ground an application.",
        "Public scene previews show story motion without exposing private queues or member obligations.",
        "Public-safe entry paths for reading, fitting, and requesting access.",
        "Start with the public story promise before choosing a face.",
        "Relationships, roles, rivals, and scenario requests already want a writer.",
        "Wanted thread start",
        "wanted-hook style opener tests",
        "public chapter pressure",
        "public story pressure",
        "Open calls can enter through",
        "ready for public scene browsing",
        "Play readiness",
        "Guidebook path",
        "Scene hubs ready",
        "Playable doors into the premise",
        "Active scene hub",
        "Hot scene hub",
        "1 public threads",
        "Ready for first scenes",
    )
    internal_planning_copy = (
        "landing surface",
        "tone/current pulse",
        "public posture",
        "entry into writing",
        "preview readiness",
        "setup readiness",
        "read model",
        "surface contract",
        "public-safe",
        "entry path",
        "workflow state",
    )

    gateway_expectations = {
        "harbor-society": (
            "The gala vote, family ties, town jobs, and quiet debts are already in motion.",
            "Shoreline Club",
            "Small Town Social Web",
            "reporter-source-at-the-club",
        ),
        "signal-creek": (
            "The midnight signal gives newcomers a reason to ask questions before town memory closes ranks.",
            "Blackridge Observatory",
            "Weird Town Mystery",
            "cult-survivor-who-remembers-1998",
        ),
        "nocturne-row": (
            "The treaty breach gives every faction, witness, and bystander a reason to move before daylight.",
            "Emberline District",
            "Urban Supernatural Pressure Cooker",
            "blood-bank-whistleblower",
        ),
        "wayfarer-station": (
            "The missing convoy has already tightened supplies, stirred old debts, and made the station listen.",
            "Docking Ring",
            "Strange Frontier",
            "corporate-auditor",
        ),
    }

    for community_slug, (
        onboarding_pitch,
        scene_hub,
        premise_label,
        wanted_slug,
    ) in gateway_expectations.items():
        gateway = services.public_realm_gateway(community_slug)

        assert gateway.hero.title == gateway.program.community.name
        assert gateway.hero.kicker == f"{premise_label} - Public preview"
        assert gateway.hero.lead == gateway.premise.catalog_pitch
        assert gateway.hero.now_playing_label in {"Current chapter", "Standing premise"}
        assert gateway.hero.first_face_path == onboarding_pitch
        assert gateway.hero.primary_action.label == "Browse open calls"
        assert gateway.hero.primary_action.href == f"/c/{community_slug}/wanted"
        assert gateway.hero.secondary_action is not None
        assert gateway.hero.secondary_action.href.startswith(f"/c/{community_slug}/world")
        assert gateway.premise.onboarding_pitch == onboarding_pitch
        assert gateway.premise.premise_label == premise_label
        assert gateway.story_frame.eyebrow == premise_label
        assert gateway.story_frame.access_label == "Public preview"
        assert gateway.story_frame.rating_label
        assert gateway.story_frame.cadence_label
        assert gateway.story_frame.writing_expectation
        assert gateway.story_frame.roster_posture
        assert gateway.story_frame.audience_label == "Public visitor"
        assert gateway.story_frame.audience_summary
        assert gateway.story_frame.premise_stage_label
        assert gateway.story_frame.featured_signal
        assert gateway.story_frame.cast_signal
        assert gateway.story_frame.places_signal
        assert gateway.story_frame.wanted_pressure
        assert gateway.story_frame.next_action.label == "Browse open calls"
        assert {contract.mode for contract in gateway.story_frame.audience_contracts} == {
            "public_visitor",
            "account_visitor",
            "member",
            "staff",
            "director",
            "inactive_member",
            "cross_community_viewer",
        }
        assert gateway.premise_stage.title
        assert not gateway.premise_stage.title.lower().startswith(("current chapter:", "premise:"))
        assert gateway.premise_stage.summary
        assert gateway.premise_stage.playable_pressure
        assert gateway.premise_evolution.premise_title
        assert gateway.premise_evolution.premise_summary
        assert gateway.premise_evolution.inciting_incident
        assert gateway.premise_evolution.current_pressure_title
        assert not gateway.premise_evolution.current_pressure_title.lower().startswith(
            ("current chapter:", "premise:")
        )
        assert gateway.premise_evolution.current_pressure_summary
        assert gateway.premise_evolution.consequences
        assert gateway.premise_evolution.next_openings
        assert gateway.premise_evolution.source_href
        assert gateway.premise_evolution.source_kind in {
            "event",
            "premise",
            "guide",
            "fallback",
        }
        assert gateway.social_lanes
        assert gateway.cast_members
        assert all(
            not item.display_title.lower().startswith(("current chapter:", "premise:"))
            for item in gateway.guidebook_previews
        )
        assert gateway.signals
        assert "Open calls" in {signal.title for signal in gateway.signals}
        assert "Scene hubs ready" in {signal.title for signal in gateway.signals}
        gateway_text = " ".join(
            [
                *(signal.summary for signal in gateway.signals),
                *(path.summary for path in gateway.entry_paths),
            ]
        )
        assert not any(copy in gateway_text for copy in boilerplate_copy)
        if community_slug == "harbor-society":
            assert "Read Founders Gala first to understand the chapter in motion." in gateway_text
            assert "Shoreline Club" in gateway_text
            assert "The Shoreline Vote" in gateway_text
            assert gateway.premise_evolution.has_current_pressure
            assert gateway.premise_evolution.current_pressure_title == "Founders Gala"
            assert (
                gateway.premise_evolution.inciting_incident
                == gateway.premise_evolution.current_pressure_summary
            )
            assert "The Ledger Page Under Table Six" in gateway.premise_evolution.consequences
            assert "Breakfast Before The Vote" in gateway.premise_evolution.consequences
            assert "Reporter source at the club" in gateway.premise_evolution.next_openings
        expected_scene_titles = {
            "harbor-society": {
                "The Ledger Page Under Table Six",
                "Breakfast Before The Vote",
            },
            "signal-creek": {
                "The Voice On The Old Feed",
                "Diner Map Of Missing Hours",
            },
            "nocturne-row": {
                "Witness Video At Last Call",
                "Emergency Court Before Dawn",
            },
        }
        assert scene_hub in {hub.board.name for hub in gateway.scene_hubs}
        assert all(
            hub.emphasis in {"normal", "featured", "hot", "high_activity"}
            for hub in gateway.scene_hubs
        )
        assert {path.title for path in gateway.entry_paths} >= {
            "Read the premise",
            "Browse open calls",
            "Request access",
        }
        assert {path.href for path in gateway.entry_paths} >= {
            f"/c/{community_slug}/wanted",
            f"/c/{community_slug}/request-access",
        }
        assert gateway.wanted_previews
        assert all(
            "wanted" not in preview.type_label.lower() for preview in gateway.wanted_previews
        )
        assert all(
            preview.related_label is None
            or not preview.related_label.lower().startswith(("current chapter:", "premise:"))
            for preview in gateway.wanted_previews
        )
        assert any(
            preview.href == f"/c/{community_slug}/wanted/{wanted_slug}"
            for preview in gateway.wanted_previews
        )
        assert all(preview.summary for preview in gateway.wanted_previews)
        assert all(not hub.board.is_private for hub in gateway.scene_hubs)
        if community_slug in expected_scene_titles:
            scene_titles = {preview.title for preview in gateway.scene_previews}
            assert expected_scene_titles[community_slug] <= scene_titles
        if community_slug == "harbor-society":
            harbor_scene_summaries = {preview.summary for preview in gateway.scene_previews}
            assert any("auction covered a private debt" in text for text in harbor_scene_summaries)
            assert any("donor calls and campaign flyers" in text for text in harbor_scene_summaries)

    async def run() -> None:
        app = create_app(debug=False, services=AppServices(services.repo, None))
        async with TestClient(app) as client:
            for community_slug, (
                onboarding_pitch,
                scene_hub,
                premise_label,
                wanted_slug,
            ) in gateway_expectations.items():
                response = await client.get(f"/c/{community_slug}")
                content = _page_content(response.text)

                assert response.status == 200
                assert "What has changed" in content
                assert "Where the story is opening" in content
                assert 'aria-label="Realm at a glance"' in response.text
                assert "Play readiness" not in content
                assert "Public preview" in content
                if community_slug == "harbor-society":
                    assert "21+ / 2/2/2" in content
                assert premise_label in content
                assert onboarding_pitch in content
                assert "Places" in content
                assert "Choose a setting" in content
                assert "Guidebook" in content
                assert "Know the world" in content
                assert "Find your place here" not in content
                assert "Featured faces" not in content
                assert "Social map" not in content
                assert 'aria-labelledby="realm-social-title"' not in response.text
                assert 'id="realm-social-title"' not in response.text
                if community_slug == "harbor-society":
                    assert "Town Power Map" in content
                    assert (
                        "White jackets, old money, and a membership vote that turns manners into weapons."
                        in content
                    )
                    assert "Family Claim" not in content
                    assert "Faction Claim" not in content
                    assert "Old family, newcomer tie, or married-in pressure." not in content
                    assert "Member, staff, guest, donor, or applicant posture." not in content
                    assert "Public workplace, civic office, or service lane." not in content
                assert scene_hub in content
                if community_slug == "harbor-society":
                    assert "The Ledger Page Under Table Six" in content
                    assert "Breakfast Before The Vote" in content
                    assert "Reporter source at the club" in content
                    for path in (
                        "/world",
                        "/world/founders-gala",
                        "/wanted",
                    ):
                        related_response = await client.get(f"/c/{community_slug}{path}")
                        related_content = _page_content(related_response.text)
                        assert related_response.status == 200
                        assert "Founders Gala" in related_content
                        assert "Current Chapter:" not in related_content
                        assert "Premise:" not in related_content
                        assert "public-safe" not in related_content.lower()
                        assert "surface contract" not in related_content.lower()
                if community_slug == "signal-creek":
                    assert "The Voice On The Old Feed" in content
                    assert "Diner Map Of Missing Hours" in content
                if community_slug == "nocturne-row":
                    assert "Witness Video At Last Call" in content
                    assert "Emergency Court Before Dawn" in content
                assert f"/c/{community_slug}/wanted" in content
                assert f"/c/{community_slug}/wanted/{wanted_slug}" in content
                assert "Characters and connections wanted" in content
                assert "Public scenes carrying the premise" not in content
                assert "Ways in before a writer has a face here" not in content
                assert "What to know before a first face" not in content
                assert "Where a new face can attach" not in content
                assert "Open roles with story pressure" not in content
                assert "Open roles and ties" not in content
                assert "Wanted hook" not in content
                assert "Scene hub" not in content
                assert "Already in the room" not in content
                assert "Ways to belong" not in content
                assert "Current Chapter:" not in content
                assert "Premise:" not in content
                assert not any(copy in content for copy in boilerplate_copy)
                assert not any(copy in content.lower() for copy in internal_planning_copy)
                assert "Faces" not in content
                assert "Guides" not in content
                assert "application review" not in content.lower()
                assert "staff controls" not in content.lower()
                assert "active face" not in content.lower()

    asyncio.run(run())


def test_original_premise_seed_archives_legacy_gateway_scaffold_threads() -> None:
    services = _seeded_services()
    repo = services.repo
    community = repo.get_community_by_slug("harbor-society")
    club = repo.get_board_by_slug(community.id, "shoreline-club")
    main_street = repo.get_board_by_slug(community.id, "main-street")
    maris = repo.get_character_by_slug(community.id, "maris-vale")
    celia = repo.get_character_by_slug(community.id, "celia-fairbourne")
    legacy_opening = repo.create_thread(
        community.id,
        club.id,
        maris.id,
        "opening-pressure",
        "Opening pressure",
        summary="Legacy scaffold scene that should leave the public hub.",
    )
    legacy_followup = repo.create_thread(
        community.id,
        main_street.id,
        celia.id,
        "wanted-thread-start",
        "Wanted thread start",
        summary="Legacy wanted-hook style opener should leave the public hub.",
    )

    seed_demo_forum(repo)

    assert repo.get_thread(community.id, legacy_opening.id).status == "archived"
    assert repo.get_thread(community.id, legacy_followup.id).status == "archived"
    gateway = services.public_realm_gateway("harbor-society")
    scene_titles = {preview.title for preview in gateway.scene_previews}
    assert "Opening pressure" not in scene_titles
    assert "Wanted thread start" not in scene_titles


def test_public_realm_gateway_contract_uses_fallbacks_and_denies_backstage() -> None:
    services = _seeded_services()
    app = create_app(debug=False, services=services)
    repo = services.repo
    public_community = repo.create_community("quiet-harbor", "Quiet Harbor")
    repo.create_material(
        public_community.id,
        "quiet-harbor-premise",
        "Quiet Harbor Premise",
        material_type="premise",
        summary="A quiet realm where the public premise and one scene hub are enough to begin.",
    )
    repo.create_material(
        public_community.id,
        "quiet-harbor-draft-event",
        "Draft Event: Locked Harbor",
        material_type="event",
        summary="Director-only pressure that must stay out of the public gateway.",
        status="draft",
    )
    repo.create_board(
        public_community.id,
        "main-street",
        "Main Street",
        tagline="Errands, porch conversations, and first faces.",
    )
    repo.update_community_launch_status(public_community.id, "public-preview")

    gateway = services.public_realm_gateway(public_community.slug)

    assert gateway.premise.premise_label == "Premise-led realm"
    assert gateway.atmosphere.label == "Standing premise"
    assert gateway.premise_evolution.has_current_pressure is False
    assert gateway.premise_evolution.source_kind == "premise"
    assert gateway.premise_evolution.current_pressure_title == "Quiet Harbor Premise"
    assert gateway.premise_evolution.next_openings.startswith("Read the public premise")
    assert "Locked Harbor" not in gateway.premise_evolution.current_pressure_title
    assert "Director-only pressure" not in gateway.premise_evolution.current_pressure_summary
    assert gateway.hero.primary_action.label == "Request access"
    assert gateway.hero.primary_action.href == "/c/quiet-harbor/request-access"
    assert gateway.hero.primary_action.is_hx_boost_safe is False
    assert gateway.story_frame.audience_label == "Public visitor"
    assert gateway.story_frame.next_action.label == "Request access"
    assert gateway.story_frame.premise_stage_label == "Story promise: Quiet Harbor Premise"
    assert gateway.story_frame.featured_signal == "Standing premise: Quiet Harbor Premise"
    assert gateway.story_frame.places_signal == "1 public place in play."
    assert gateway.story_frame.wanted_pressure == "No public wanted pressure is open right now."
    assert gateway.hero.secondary_action is not None
    assert gateway.hero.secondary_action.label == "Read premise"
    assert gateway.wanted_previews == ()
    assert {signal.title for signal in gateway.signals} >= {
        "Public preview",
        "Start here",
        "Scene hubs ready",
    }

    backstage = repo.create_community("backstage-realm", "Backstage Realm")
    repo.create_material(
        backstage.id,
        "backstage-premise",
        "Backstage Premise",
        material_type="premise",
        summary="This should not be enough without public-preview launch status.",
    )
    repo.create_board(backstage.id, "backstage-yard", "Backstage Yard")

    with pytest.raises(LookupError):
        services.public_realm_gateway(backstage.slug)

    async def run() -> None:
        async with TestClient(app) as client:
            response = await client.get("/c/quiet-harbor")
            content = _page_content(response.text)

            assert response.status == 200
            assert "Quiet Harbor Premise" in content
            assert "Public preview" in content
            assert "Standing premise: Quiet Harbor Premise" in content
            assert "1 public place in play." in content
            assert "No public wanted pressure is open right now." in content
            assert 'aria-label="Realm at a glance"' in response.text
            assert "Locked Harbor" not in content
            assert "Director-only pressure" not in content
            assert "Main Street" in content
            assert "Request access" in content
            assert "/c/quiet-harbor/request-access" in response.text
            assert "elbysodic-realm-gateway-hero__fallback" in response.text
            assert "Wanted hooks" not in content
            assert "Browse 0 wanted hooks" not in content
            assert "active face" not in content.lower()
            assert "staff controls" not in content.lower()

    asyncio.run(run())


def test_public_realm_gateway_scene_previews_hide_private_threads() -> None:
    services = _seeded_services()
    repo = services.repo
    community = services.seed.community
    public_board = repo.get_board_by_slug(community.id, "danger-room")
    private_board = repo.get_board_by_slug(community.id, "staff-room")
    rogue = repo.get_character_by_slug(community.id, "rogue")
    private_thread = repo.create_thread(
        community.id,
        private_board.id,
        rogue.id,
        "private-gateway-scene",
        "Private gateway scene",
        status="open",
        summary="Private story motion that should not reach public previews.",
    )
    public_thread = repo.create_thread(
        community.id,
        public_board.id,
        rogue.id,
        "public-gateway-scene",
        "Public gateway scene",
        status="open",
        visibility="public_preview",
        summary="A public scene that can safely invite first-face readers.",
    )
    repo.create_post(
        community.id,
        public_thread.id,
        rogue.id,
        "A public opening beat makes this a real scene preview.",
    )

    gateway = services.public_realm_gateway(community.slug)

    assert any(preview.title == public_thread.title for preview in gateway.scene_previews)
    assert all(preview.title != private_thread.title for preview in gateway.scene_previews)
    assert all(
        preview.href.startswith(f"/c/{community.slug}/boards/")
        for preview in gateway.scene_previews
    )

    async def run() -> None:
        app = create_app(debug=False, services=AppServices(services.repo, None))
        async with TestClient(app) as client:
            response = await client.get(f"/c/{community.slug}")
            content = _page_content(response.text)

            assert response.status == 200
            assert "Scenes" in content
            assert "Underway now" in content
            assert "Public gateway scene" in content
            assert "Private gateway scene" not in content
            assert "Private story motion" not in content

    asyncio.run(run())


def test_realm_gateway_home_tolerates_missing_scene_previews(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_realm_gateway = AppServices.realm_gateway

    def legacy_realm_gateway(self: AppServices) -> SimpleNamespace:
        gateway = original_realm_gateway(self)
        return SimpleNamespace(
            program=gateway.program,
            guidebook=gateway.guidebook,
            hero=gateway.hero,
            premise=gateway.premise,
            story_frame=gateway.story_frame,
            premise_stage=gateway.premise_stage,
            atmosphere=gateway.atmosphere,
            signals=gateway.signals,
            scene_hubs=gateway.scene_hubs,
            entry_paths=gateway.entry_paths,
            social_lanes=gateway.social_lanes,
            cast_members=gateway.cast_members,
            wanted_previews=gateway.wanted_previews,
            continuation=gateway.continuation,
        )

    monkeypatch.setattr(AppServices, "realm_gateway", legacy_realm_gateway)

    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.get("/c/x-men-apocalypse")
            content = _page_content(response.text)

            assert response.status == 200
            assert "X-Men Apocalypse" in content
            assert "Choose a setting" in content
            assert "Playable now" not in content

    asyncio.run(run())


def test_public_realm_gateway_ranks_active_scene_hubs_before_limit() -> None:
    services = _seeded_services()
    repo = services.repo
    community = repo.create_community("ranked-gateway", "Ranked Gateway")
    role = repo.create_role(community.id, "member", "Member")
    user = repo.create_user("ranked-gateway@example.com", "hash")
    membership = repo.create_membership(
        community.id,
        user.id,
        role.id,
        "ranked-writer",
        "Ranked Writer",
    )
    character = repo.create_character(community.id, membership.id, "ranked-face", "Ranked Face")
    repo.create_material(
        community.id,
        "premise",
        "Ranked Gateway Premise",
        material_type="premise",
        summary="A public premise for ranked scene hubs.",
    )
    for index in range(4):
        repo.create_board(
            community.id,
            f"quiet-hub-{index}",
            f"Quiet Hub {index}",
            sort_order=index,
            image_url=f"/quiet-{index}.svg",
        )
    hot_board = repo.create_board(
        community.id,
        "fifth-active-hub",
        "Fifth Active Hub",
        sort_order=99,
    )
    for index in range(3):
        repo.create_thread(
            community.id,
            hot_board.id,
            character.id,
            f"active-hub-scene-{index}",
            f"Active hub scene {index}",
            status="open",
            visibility="public_preview",
        )
    repo.update_community_launch_status(community.id, "public-preview")

    gateway = services.public_realm_gateway(community.slug)

    assert "Fifth Active Hub" in {hub.board.name for hub in gateway.scene_hubs}
    active_hub = next(hub for hub in gateway.scene_hubs if hub.board.name == "Fifth Active Hub")
    assert active_hub.emphasis == "hot"
    assert active_hub.public_thread_count == 3
    assert len(gateway.scene_hubs) == 4


def test_public_realm_gateway_uses_curated_slots_before_fallbacks() -> None:
    services = _seeded_services()
    repo = services.repo
    community = repo.create_community("curated-gateway", "Curated Gateway")
    role = repo.create_role(community.id, "member", "Member")
    user = repo.create_user("curated-gateway@example.com", "hash")
    membership = repo.create_membership(
        community.id,
        user.id,
        role.id,
        "curated-director",
        "Curated Director",
    )
    repo.create_material(
        community.id,
        "premise",
        "Curated Gateway Premise",
        material_type="premise",
        summary="A public premise for curated gateway slots.",
    )
    boards = [
        repo.create_board(
            community.id,
            f"gateway-hub-{index}",
            f"Gateway Hub {index}",
            tagline=f"Gateway hub {index} scene pressure.",
            sort_order=index,
        )
        for index in range(5)
    ]
    stale_board = repo.create_board(
        community.id,
        "stale-gateway-hub",
        "Stale Gateway Hub",
        tagline="This place should disappear when made private.",
    )
    wanted_ads = [
        repo.create_wanted_ad(
            community.id,
            membership.id,
            f"gateway-hook-{index}",
            f"Gateway Hook {index}",
            summary=f"Gateway hook {index} wants a first face.",
        )
        for index in range(5)
    ]
    stale_wanted = repo.create_wanted_ad(
        community.id,
        membership.id,
        "stale-gateway-hook",
        "Stale Gateway Hook",
        summary="This hook should disappear when archived.",
    )
    materials = [
        repo.create_material(
            community.id,
            f"gateway-guide-{index}",
            f"Gateway Guide {index}",
            summary=f"Gateway guide {index} grounds a first face.",
            sort_order=index,
        )
        for index in range(5)
    ]
    stale_material = repo.create_material(
        community.id,
        "stale-gateway-guide",
        "Stale Gateway Guide",
        summary="This guide should disappear when drafted.",
    )
    repo.update_community_launch_status(community.id, "public-preview")

    repo.create_community_gateway_slot(community.id, "scene_hub", stale_board.id, position=1)
    repo.create_community_gateway_slot(community.id, "scene_hub", boards[4].id, position=2)
    repo.create_community_gateway_slot(community.id, "wanted_hook", stale_wanted.id, position=1)
    repo.create_community_gateway_slot(community.id, "wanted_hook", wanted_ads[4].id, position=2)
    repo.create_community_gateway_slot(
        community.id,
        "guidebook_material",
        stale_material.id,
        position=1,
    )
    repo.create_community_gateway_slot(
        community.id,
        "guidebook_material",
        materials[4].id,
        position=2,
    )
    repo.update_board(
        community.id,
        stale_board.id,
        name=stale_board.name,
        description=stale_board.description,
        tagline=stale_board.tagline,
        sort_order=stale_board.sort_order,
        board_kind=stale_board.board_kind,
        is_private=True,
    )
    repo.update_wanted_ad_status(community.id, stale_wanted.id, "archived")
    repo.update_material(
        community.id,
        stale_material.id,
        title=stale_material.title,
        material_type=stale_material.material_type,
        summary=stale_material.summary,
        body=stale_material.body,
        status="draft",
        sort_order=stale_material.sort_order,
        is_featured=stale_material.is_featured,
    )

    gateway = services.public_realm_gateway(community.slug)

    assert gateway.scene_hubs[0].board.id == boards[4].id
    assert gateway.wanted_previews[0].title == wanted_ads[4].title
    assert gateway.guidebook_previews[0].material.material.id == materials[4].id
    assert all(hub.board.id != stale_board.id for hub in gateway.scene_hubs)
    assert all(preview.title != stale_wanted.title for preview in gateway.wanted_previews)
    assert all(
        item.material.material.id != stale_material.id for item in gateway.guidebook_previews
    )

    async def run() -> None:
        app = create_app(debug=False, services=AppServices(services.repo, None))
        async with TestClient(app) as client:
            response = await client.get("/c/curated-gateway")
            content = _page_content(response.text)

            assert response.status == 200
            assert content.index("Gateway Hub 4") < content.index("Gateway Hub 0")
            assert content.index("Gateway Hook 4") < content.index("Gateway Hook 0")
            assert "Gateway Guide 4" in content
            assert "Gateway Guide 0" in content
            assert "Stale Gateway Hub" not in content
            assert "Stale Gateway Hook" not in content
            assert "Stale Gateway Guide" not in content

    asyncio.run(run())


def test_studio_gateway_curation_updates_public_home_slots() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        staff_services = AppServices(
            services.repo,
            DemoSeed(staff.community, staff.user, staff.membership, staff.character),
        )
        community = staff.community
        board = services.repo.get_board_by_slug(community.id, "danger-room")
        wanted = services.repo.get_wanted_ad_by_slug(
            community.id,
            "human-un-liaison-for-b24",
        )
        material = services.repo.get_material_by_slug(community.id, "b-24-winter")
        app = create_app(debug=False, services=staff_services)

        async with TestClient(app) as client:
            studio = await client.get("/studio/structure")
            save = await client.post(
                "/studio/structure",
                body=urlencode(
                    {
                        "intent": "gateway_curation",
                        "scene_hub_target_id": str(board.id),
                        f"scene_hub_position_{board.id}": "1",
                        "wanted_hook_target_id": str(wanted.id),
                        f"wanted_hook_position_{wanted.id}": "1",
                        "guidebook_material_target_id": str(material.id),
                        f"guidebook_material_position_{material.id}": "1",
                    }
                ).encode(),
                headers=_FORM,
            )
            updated_studio = await client.get("/studio/structure")
            home = await client.get("/c/x-men-apocalypse")

        assert studio.status == 200
        assert "Home spotlight audit" in studio.text
        assert "Danger Room" in studio.text
        assert "Human UN liaison for B-24 talks" in studio.text
        assert "B-24 Winter" in studio.text
        assert "Selected spotlight" in studio.text
        assert "Spotlight library" in studio.text
        assert "Realm home preview" in studio.text
        assert "Add to spotlight" in studio.text
        assert "This is the cross-realm audit view." in studio.text
        assert "data-elbysodic-spotlight-composer" in studio.text
        assert "data-elbysodic-spotlight-selected-list" in studio.text
        assert "data-elbysodic-spotlight-library-list" in studio.text
        assert "data-elbysodic-spotlight-preview-list" in studio.text
        assert "data-elbysodic-gateway-curation-list" in studio.text
        assert "data-elbysodic-gateway-curation-item" in studio.text
        assert "data-elbysodic-gateway-curation-position" in studio.text
        assert "Board map audit and bulk repair" in studio.text
        assert "Single-board edits belong on the board" in studio.text
        assert save.status == 302
        assert _response_header(save, "location") == "/studio/structure#gateway-curation"

        slots = services.repo.list_community_gateway_slots(community.id)
        assert {(slot.slot_type, slot.target_id, slot.position) for slot in slots} >= {
            ("scene_hub", board.id, 10),
            ("wanted_hook", wanted.id, 10),
            ("guidebook_material", material.id, 10),
        }
        assert re.search(
            rf'name="scene_hub_target_id"[^>]*value="{board.id}"[^>]*checked',
            updated_studio.text,
        )
        assert re.search(
            rf'name="scene_hub_position_{board.id}"[^>]*value="10"',
            updated_studio.text,
        )
        assert home.status == 200
        gateway = staff_services.public_realm_gateway(community.slug)
        assert gateway.scene_hubs[0].board.id == board.id
        assert gateway.wanted_previews[0].title == wanted.title
        assert gateway.guidebook_previews[0].material.material.id == material.id

    asyncio.run(run())


def test_studio_gateway_curation_rejects_invalid_selected_order() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        staff_services = AppServices(
            services.repo,
            DemoSeed(staff.community, staff.user, staff.membership, staff.character),
        )
        board = services.repo.get_board_by_slug(staff.community.id, "danger-room")
        app = create_app(debug=False, services=staff_services)

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/structure",
                body=urlencode(
                    {
                        "intent": "gateway_curation",
                        "scene_hub_target_id": str(board.id),
                        f"scene_hub_position_{board.id}": "0",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert response.status == 200
        assert "spotlight order must be a positive number" in response.text
        assert (
            services.repo.list_community_gateway_slots(
                staff.community.id,
                slot_type="scene_hub",
            )
            == []
        )

    asyncio.run(run())


def test_identity_dropdown_switches_to_canonical_community_path() -> None:
    async def run() -> None:
        app = _app()
        community_slug = get_services().seed.community.slug

        async with TestClient(app) as client:
            response = await client.get(f"/c/{community_slug}")

        assert response.status == 200
        assert f'name="next" value="/c/{community_slug}"' in response.text
        assert 'name="next" value="/c/hp-universe"' in response.text
        assert 'name="next" value="/c/jurassic-park-universe"' in response.text
        assert 'name="next" value="/boards/' not in response.text

    asyncio.run(run())


def test_forum_pages_render_seeded_boards_and_thread() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            index = await client.get("/c/x-men-apocalypse")
            assert index.status == 200
            assert "X-Men Apocalypse" in index.text
            assert "Staff Room" not in index.text
            assert "Continue writing as Rogue" in index.text
            assert 'href="/c/x-men-apocalypse/desk"' in index.text
            assert 'href="/c/x-men-apocalypse/characters/rogue"' in index.text
            assert "elbysodic-identity-menu" in index.text
            assert '@click.outside="open = false"' in index.text
            assert "elbysodic-identity-menu__hero" in index.text
            assert "elbysodic-identity-menu__quick-links" in index.text
            assert "elbysodic-identity-menu__notification-link" in index.text
            assert "elbysodic-identity-menu__theme-row" in index.text
            assert "playing as Rogue" in index.text
            assert "Recent activity" not in index.text
            assert "Latest details:" not in index.text
            assert "elbysodic-community-table" not in index.text
            assert "elbysodic-community-row" not in index.text
            assert "elbysodic-activity-log" not in index.text
            assert "elbysodic-activity-log-item" not in index.text
            assert _sidebar_board_count(index.text, "plotting") == 1

            board = await client.get("/boards/plotting")
            assert board.status == 200
            assert "Open thread roster" in board.text
            assert "Started by" in board.text
            assert "Latest" in board.text
            assert 'id="board-thread-region"' in board.text
            assert 'hx-target="#board-thread-region"' in board.text
            assert 'hx-select="#board-thread-region"' in board.text
            assert 'hx-disinherit="hx-select hx-target hx-swap"' in board.text
            assert 'hx-sync="closest nav:replace"' in board.text
            assert 'hx-swap="outerHTML show:none"' in board.text
            assert "chirpui-breadcrumbs" in board.text
            assert "chirpui-filter-group" in board.text
            assert "chirpui-filter-chip" in board.text
            assert "chirpui-facet-chip" in board.text
            assert "First unread" in board.text
            assert "#post-" in board.text
            assert "new replies" in board.text
            assert "min read" in board.text
            assert "written by" in board.text
            assert "Next unread" in board.text
            assert "Magneto" in board.text
            assert (
                'class="chirpui-tooltip chirpui-tooltip--top '
                'elbysodic-latest__tooltip"' in board.text
            )
            assert 'data-tooltip="Latest details:' in board.text

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200
            assert 'id="post-' in thread.text
            assert "chirpui-thread-reader-layout" in thread.text
            assert "chirpui-breadcrumbs" in thread.text
            assert "Runtime" in thread.text
            assert "writers" in thread.text
            assert "min read" in thread.text
            assert "Drop your available characters here" in thread.text
            assert "Rogue" in thread.text
            assert "Magneto" in thread.text
            assert "/members/starlane" in thread.text
            assert "caught up" in thread.text
            assert _sidebar_board_count(thread.text, "plotting") == 0

    asyncio.run(run())


def test_seeded_world_surfaces_place_hierarchy() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            locations = await client.get("/c/x-men-apocalypse/locations")
            assert locations.status == 200
            assert "/boards/xavier-institute" in locations.text
            assert "/boards/med-bay" in locations.text
            assert "Locations" in locations.text

            academy = await client.get("/boards/xavier-institute")
            assert academy.status == 200
            assert "Sublocations" in academy.text
            assert "Med Bay" in academy.text
            assert "Cerebro" in academy.text
            assert "Danger Room" in academy.text

            med_bay = await client.get("/boards/med-bay")
            assert med_bay.status == 200
            assert "Xavier Institute" in med_bay.text
            assert "Nearby locations" in med_bay.text
            assert "The med-bay lights stay on" in med_bay.text

    asyncio.run(run())


def test_root_renders_elbysodic_network_home_not_default_community() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            root = await client.get("/")

        assert root.status == 200
        assert "/elbysodic-static/brand/elbysodic-favicon.svg" in root.text
        assert "/elbysodic-static/brand/elbysodic-mark-small.svg" in root.text
        assert '<span class="elbysodic-community-brand__name">Elbysodic</span>' in root.text
        assert "Explore realms" in root.text
        assert "Featured realm" in root.text
        assert "Top 10 realms" in root.text
        assert "Premise engines" not in root.text
        assert "Small-town social webs" in root.text
        assert "Weird-town mysteries" in root.text
        assert "Mystery and current chapters" not in root.text
        assert 'class="elbysodic-network-home-tile__rank"' in root.text
        assert "Rank 1" in root.text
        assert "<span>5 wanted · 8 faces</span>" in root.text
        landscape_tiles = re.findall(
            r'<article class="[^"]*elbysodic-network-home-tile--landscape[^"]*"[^>]*>.*?</article>',
            root.text,
            re.DOTALL,
        )
        assert landscape_tiles
        assert not any("wanted ·" in tile or "faces</span>" in tile for tile in landscape_tiles)
        assert "Search by premise, pace, hooks, and chapters in motion." not in root.text
        assert "Search story fit" not in root.text
        assert 'class="elbysodic-topbar-search" action="/search"' in root.text
        assert "All realms" in root.text
        assert "Your desk is one click away." not in root.text
        assert "Open Writer Desk" not in root.text
        assert "What can move next." not in root.text
        assert "Memberships on this account." not in root.text
        assert "Choose the realm you are writing in." not in root.text
        assert "Explore Elbysodic" not in root.text
        assert 'aria-label="Community"' not in root.text
        assert 'class="chirpui-sidebar elbysodic-sidebar"' not in root.text
        assert 'href="/c/afterlight-accord"' in root.text
        assert 'href="/c/x-men-apocalypse/desk"' not in root.text
        assert "Afterlight Accord" in root.text

    asyncio.run(run())


def test_shell_groups_community_modes_in_topbar_and_context_in_sidebar() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            index = await client.get("/c/x-men-apocalypse")

            assert index.status == 200
            assert "/elbysodic-static/brand/elbysodic-favicon.svg" in index.text
            assert "/elbysodic-static/brand/elbysodic-mark-one-color-dark.svg" in index.text
            assert "/elbysodic-static/seed-media/xmen-mark.svg" in index.text
            assert 'alt="X-Men Apocalypse academy signal mark"' in index.text
            assert (
                '<span class="elbysodic-community-brand__name">X-Men Apocalypse</span>'
                in index.text
            )
            assert 'class="elbysodic-realm-switcher__summary"' in index.text
            assert 'aria-label="Realm switcher: X-Men Apocalypse"' in index.text
            assert "<strong>Elbysodic</strong>" in index.text
            assert "<small>Network home</small>" in index.text
            assert "<strong>Explore realms</strong>" in index.text
            assert 'data-rail-tooltip="Built on Elbysodic"' in index.text
            assert re.search(
                r'<a class="elbysodic-primary-rail__link elbysodic-primary-rail__link--platform"\s+href="/"',
                index.text,
            )
            assert "data-elbysodic-global-link" in index.text
            assert 'href="/c/x-men-apocalypse"' in index.text
            assert 'href="/c/x-men-apocalypse/desk"' in index.text
            assert 'aria-label="Primary community rooms"' in index.text
            assert 'aria-label="Global"' in index.text
            assert (
                'class="elbysodic-topbar-search" action="/c/x-men-apocalypse/search"' in index.text
            )
            assert "Search X-Men Apocalypse" in index.text
            assert "XMA" in index.text
            assert "Know the world" in index.text
            assert "Characters and connections wanted" in index.text
            assert "Browse all open calls" in index.text
            identity_summary = re.search(
                r'<summary class="elbysodic-identity-menu__summary"[^>]*>(?P<body>.*?)</summary>',
                index.text,
                re.S,
            )
            assert identity_summary is not None
            assert "elbysodic-identity-menu__summary-avatar" in identity_summary.group("body")
            assert "elbysodic-identity-menu__copy" not in identity_summary.group("body")
            assert 'class="elbysodic-primary-rail"' in index.text
            assert ">Home</a>" not in index.text
            assert re.search(
                r'<a class="elbysodic-primary-rail__link"\s+href="/c/x-men-apocalypse/locations"[^>]*aria-label="Locations"',
                index.text,
            )
            assert ">Play</a>" not in index.text
            assert 'aria-label="Wanted"' in index.text
            assert re.search(
                r'<a class="elbysodic-topnav__link"\s+href="/network"[^>]*>Explore</a>',
                index.text,
            )
            topbar = re.search(
                r'<nav class="elbysodic-topnav elbysodic-topnav--global"[^>]*>(?P<body>.*?)</nav>',
                index.text,
                re.S,
            )
            assert topbar is not None
            assert 'href="/"' not in topbar.group("body")
            assert 'href="/world"' not in topbar.group("body")
            assert 'href="/wanted"' not in topbar.group("body")
            assert 'href="/desk"' not in topbar.group("body")
            assert 'href="/studio"' not in topbar.group("body")
            assert '<span class="chirpui-sidebar__section-title">On World Home</span>' in index.text
            assert '<span class="chirpui-sidebar__label">Locations</span>' in index.text
            assert '<span class="chirpui-sidebar__label">Guidebook</span>' in index.text
            assert '<span class="chirpui-sidebar__label">Community</span>' in index.text
            assert "elbysodic-mobile-realm-nav" not in index.text
            assert 'class="elbysodic-topnav__link" href="/notifications"' not in index.text

    asyncio.run(run())


def test_seeded_program_homepage_uses_community_media_and_world_status() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)
        cookie = f"elbysodic_dev_identity={hp.id}:1:{hp_membership.id}"

        async with TestClient(app) as client:
            xmen = await client.get("/c/x-men-apocalypse")
            hp_home = await client.get("/c/hp-universe", headers={"Cookie": cookie})

        assert xmen.status == 200
        assert "elbysodic-realm-gateway-hero" in xmen.text
        assert "/elbysodic-static/seed-media/xmen-hero.svg" in xmen.text
        assert 'alt="Snow-lit academy and B-24 signal lines"' in xmen.text
        assert "Current Event: B-24 Winter" in xmen.text
        assert "Iceman is infected with B-24" in xmen.text

        assert hp_home.status == 200
        assert "elbysodic-realm-gateway-hero" in hp_home.text
        assert "/elbysodic-static/seed-media/hp-mark.svg" in hp_home.text
        assert "/elbysodic-static/seed-media/hp-hero.svg" in hp_home.text
        assert 'alt="Glass staircase rising through castle stacks"' in hp_home.text
        assert "Current Event: No Reflection" in hp_home.text
        assert (
            "One student has gone missing, and every portrait remembers a different last sighting."
            in hp_home.text
        )
        assert "The school has reopened under a fragile truce" not in hp_home.text

    asyncio.run(run())


def test_new_realm_locations_use_actionable_empty_states() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.get("/c/rl-nyc/locations")

        assert response.status == 200
        content = _page_content(response.text)
        assert "chirpui-section-header" in content
        assert "No scenes have opened here yet." in content
        assert 'href="/c/rl-nyc/boards/brooklyn/threads/new"' in content
        assert 'href="/c/rl-nyc/boards/queens-night-market/threads/new"' in content
        assert "Recent activity" not in content

    asyncio.run(run())


def test_seeded_location_boards_have_media_throughlines() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        expected = {
            services.seed.community.slug: 6,
            "hp-universe": 3,
            "jurassic-park-universe": 4,
            "rl-nyc": 3,
            "rl-small-town": 4,
        }

        for community_slug, minimum in expected.items():
            community = repo.get_community_by_slug(community_slug)
            location_boards = [
                board
                for board in repo.list_boards(community.id)
                if board.board_kind == "location" and board.image_url
            ]
            assert len(location_boards) >= minimum
            assert all(board.image_alt for board in location_boards)
            assert all(
                board.image_url is not None
                and board.image_url.startswith("/elbysodic-static/seed-media/locations/")
                for board in location_boards
            )

        hp = repo.get_community_by_slug("hp-universe")
        hp_membership = repo.get_membership_for_user(hp.id, 1)
        hp_cookie = f"elbysodic_dev_identity={hp.id}:1:{hp_membership.id}"

        async with TestClient(app) as client:
            home = await client.get("/c/x-men-apocalypse")
            hp_home = await client.get("/c/hp-universe", headers={"Cookie": hp_cookie})
            xavier = await client.get("/boards/xavier-institute")

        assert home.status == 200
        assert "/elbysodic-static/seed-media/locations/xmen-xavier-institute.svg" in home.text
        assert 'alt="Snowbound academy windows under B-24 signal arcs"' in home.text
        assert hp_home.status == 200
        assert "/elbysodic-static/seed-media/locations/hp-castle-corridors.svg" in hp_home.text
        assert 'alt="Castle corridor with shifting stairs and portrait light"' in hp_home.text
        assert xavier.status == 200
        assert "/elbysodic-static/seed-media/locations/xmen-xavier-institute.svg" in xavier.text

    asyncio.run(run())


def test_seeded_location_media_does_not_overwrite_custom_board_media() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    community = services.seed.community
    board = repo.get_board_by_slug(community.id, "xavier-institute")

    repo.update_board(
        community.id,
        board.id,
        name=board.name,
        description=board.description,
        sort_order=board.sort_order,
        parent_board_id=board.parent_board_id,
        board_kind=board.board_kind,
        sidebar_section=board.sidebar_section,
        tagline=board.tagline,
        image_url="https://example.test/custom-academy.jpg",
        image_alt="Custom academy image",
        is_private=board.is_private,
        navigation_order=board.navigation_order,
        show_in_navigation=board.show_in_navigation,
    )

    seed_demo_forum(repo)

    updated = repo.get_board_by_slug(community.id, "xavier-institute")
    assert updated.image_url == "https://example.test/custom-academy.jpg"
    assert updated.image_alt == "Custom academy image"


def test_text_first_board_media_treatment_keeps_image_out_of_public_stage() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        board = repo.get_board_by_slug(community.id, "xavier-institute")
        repo.update_board(
            community.id,
            board.id,
            name=board.name,
            description=board.description,
            sort_order=board.sort_order,
            parent_board_id=board.parent_board_id,
            board_kind=board.board_kind,
            sidebar_section=board.sidebar_section,
            tagline=board.tagline,
            image_url="https://example.test/text-first.jpg",
            image_alt="Text first image",
            image_treatment="text",
            image_focal_point="right",
            image_overlay="light",
            is_private=board.is_private,
            navigation_order=board.navigation_order,
            show_in_navigation=board.show_in_navigation,
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/xavier-institute")

        assert page.status == 200
        assert "elbysodic-board-media-treatment--text" in page.text
        assert "elbysodic-board-media-focal--right" in page.text
        assert "elbysodic-board-media-overlay--light" in page.text
        assert 'src="https://example.test/text-first.jpg"' not in page.text

    asyncio.run(run())


def test_writer_desk_hub_keeps_meta_tools_reachable() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            desk = await client.get("/desk")

            assert desk.status == 200
            assert "Writer Desk" in desk.text
            assert "Return to a scene, catch up on reading, or move a plot forward." in desk.text
            assert "Writing as Rogue" not in desk.text
            assert "Pick up where you left off" in desk.text
            assert "By face" in desk.text
            assert "Everything else" in desk.text
            assert "elbysodic-page-pulse--desk" in desk.text
            assert "Read latest" in desk.text
            assert "Unread watched" in desk.text
            assert "Waiting on others" in desk.text
            assert "Desk shortcuts" not in desk.text
            assert "Check applications" not in desk.text
            assert "Accepted" not in desk.text
            assert "0 open" not in desk.text
            assert "playing as Rogue" in desk.text
            assert "Queue" in desk.text
            assert "Inbox" in desk.text
            assert "Roster" in desk.text
            assert "Discovery" in desk.text
            assert "/my/threads" in desk.text
            assert "/notifications" in desk.text
            assert "/characters" in desk.text
            assert "/applications" in desk.text
            assert "/discover" in desk.text

    asyncio.run(run())


def test_writer_hubs_give_faceless_members_a_first_face_path() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        faceless_services = _faceless_services(services)
        app = create_app(debug=False, services=faceless_services)
        async with TestClient(app) as client:
            realm_home = await client.get("/c/x-men-apocalypse")
            desk = await client.get("/desk")
            threads = await client.get("/my/threads")
            roster = await client.get("/characters")
            applications = await client.get("/applications")

            assert realm_home.status == 200
            assert "Start with a first face" in realm_home.text
            assert "You are a member of X-Men Apocalypse" in realm_home.text
            assert "Finish a first" in realm_home.text
            assert 'href="/c/x-men-apocalypse/applications/new"' in realm_home.text
            assert 'href="/c/x-men-apocalypse/wanted"' in realm_home.text
            assert 'href="/c/x-men-apocalypse/locations"' in realm_home.text

            assert desk.status == 200
            assert "Start with a first face" in desk.text
            assert "No faces on your roster yet." in desk.text
            assert "Start first face" in desk.text
            assert 'href="/applications/new"' in desk.text
            assert "Your roster is caught up" not in desk.text

            assert threads.status == 200
            assert "Roster replies" in threads.text
            assert "No active thread queue yet." in threads.text
            assert "Thread history" not in threads.text

            assert roster.status == 200
            assert "No faces on your roster yet." in roster.text
            assert "Add face" in roster.text
            assert "Add character" not in roster.text

            assert applications.status == 200
            assert "No application drafts need work." in applications.text
            assert "Start application" in applications.text
            assert "Accepted faces live in the roster." in applications.text

    asyncio.run(run())


def test_writer_desk_keeps_first_face_application_active() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        applicant_services = _faceless_services(services, prefix="applicant")
        character = applicant_services.repo.create_character(
            applicant_services.seed.community.id,
            applicant_services.seed.membership.id,
            "draft-face",
            "Draft Face",
            application_status="draft",
        )
        applicant_services.repo.ensure_character_application(
            applicant_services.seed.community.id,
            character.id,
        )
        app = create_app(debug=False, services=applicant_services)

        async with TestClient(app) as client:
            desk = await client.get("/desk")
            home = await client.get("/c/x-men-apocalypse")

        assert desk.status == 200
        assert "Finish Draft Face" in desk.text
        assert "Continue application" in desk.text
        assert 'href="/applications/draft-face"' in desk.text
        assert "Your roster is caught up" not in desk.text
        assert "Caught up" not in desk.text

        assert home.status == 200
        assert "Finish Draft Face" in home.text
        assert "Complete the draft and submit this face for director review." in home.text
        assert 'href="/c/x-men-apocalypse/applications/draft-face"' in home.text
        assert 'href="/c/x-men-apocalypse/applications"' in home.text

    asyncio.run(run())


def test_writer_activation_read_model_tracks_first_face_states() -> None:
    services = _faceless_services(create_services(path=":memory:"), prefix="activation")

    no_face = services.writer_activation()
    assert no_face.stage == "needs_face"
    assert no_face.primary_href == "/applications/new"
    assert no_face.needs_first_face

    draft = services.repo.create_character(
        services.seed.community.id,
        services.seed.membership.id,
        "activation-face",
        "Activation Face",
        application_status="draft",
    )
    services.repo.ensure_character_application(services.seed.community.id, draft.id)
    services._invalidate_viewer()
    draft_state = services.writer_activation()
    assert draft_state.stage == "application_draft"
    assert draft_state.primary_href == "/applications/activation-face"
    assert draft_state.open_application_count == 1

    accepted = services.repo.update_character_application_status(
        services.seed.community.id,
        draft.id,
        "accepted",
    )
    services.repo.set_default_character(
        services.seed.community.id,
        services.seed.membership.id,
        accepted.id,
    )
    services._invalidate_viewer()
    accepted_state = services.writer_activation()
    assert accepted_state.stage == "accepted_no_scene"
    assert accepted_state.primary_href == "/claims"
    assert accepted_state.accepted_face_count == 1
    assert accepted_state.claim_gap_count >= 1


def test_first_playable_openings_hide_closed_and_private_candidates() -> None:
    services, _ = _outsider_services(create_services(path=":memory:"), prefix="opening")
    community = services.seed.community
    repo = services.repo
    repo.create_material(
        community.id,
        "draft-application-only",
        "Draft Application Only",
        material_type="application",
        summary="Draft-only intake note.",
        body="Draft-only intake note.",
        status="draft",
    )
    repo.create_wanted_ad(
        community.id,
        services.seed.membership.id,
        "my-own-hook",
        "My Own Hook",
        status="open",
    )
    repo.create_wanted_ad(
        community.id,
        services.seed.membership.id,
        "closed-hook",
        "Closed Hook",
        status="archived",
    )

    openings = services.first_playable_openings(limit=20)
    hrefs = {item.href for item in openings}
    labels = {item.label for item in openings}

    assert "/world/draft-application-only" not in hrefs
    assert "/wanted/my-own-hook" not in hrefs
    assert "/wanted/closed-hook" not in hrefs
    assert any(item.kind == "wanted" for item in openings)
    assert "Draft Application Only" not in labels


def test_writer_activation_recommends_specific_opening_after_acceptance() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    community = repo.create_community("activation-openings", "Activation Openings")
    role = repo.create_role(community.id, "member", "Member")
    user = repo.create_user("activation-openings@example.com", "hash")
    membership = repo.create_membership(
        community.id,
        user.id,
        role.id,
        "activation-openings",
        "Activation Openings",
    )
    character = repo.create_character(
        community.id,
        membership.id,
        "accepted-face",
        "Accepted Face",
        application_status="accepted",
        make_default=True,
    )
    other_user = repo.create_user("activation-hook-owner@example.com", "hash")
    other_membership = repo.create_membership(
        community.id,
        other_user.id,
        role.id,
        "hook-owner",
        "Hook Owner",
    )
    repo.create_wanted_ad(
        community.id,
        other_membership.id,
        "scene-partner",
        "Scene Partner",
        summary="A specific wanted hook for the accepted face.",
        wanted_type="plot_role",
        status="open",
    )

    activation = AppServices(
        repo,
        DemoSeed(community, user, membership, character),
    ).writer_activation()

    assert activation.stage == "accepted_no_scene"
    assert activation.headline == "Start with Scene Partner"
    assert activation.summary == "A specific wanted hook for the accepted face."
    assert activation.primary_label == "Open plot role"
    assert activation.primary_href == "/wanted/scene-partner"


def test_first_face_activation_surfaces_claim_and_reserve_work() -> None:
    async def run() -> None:
        services, character_id = _outsider_services(
            create_services(path=":memory:"),
            prefix="claimwork",
        )
        community = services.seed.community
        repo = services.repo
        repo.create_claim_type(
            community.id,
            "required-face-name",
            "Required Face Name",
            is_required=True,
        )
        repo.create_character_reserve(
            community.id,
            services.seed.membership.id,
            character_id,
            "Reserved wanted lane",
            status="active",
        )
        app = create_app(debug=False, services=services)

        activation = services.writer_activation()
        openings = services.first_playable_openings(limit=4)
        async with TestClient(app) as client:
            desk = await client.get("/desk")

        assert activation.stage == "accepted_no_scene"
        assert activation.primary_href == "/claims"
        assert activation.claim_gap_count >= 1
        assert activation.reserve_count == 1
        assert any(item.kind == "claims" and item.href == "/claims" for item in openings)
        assert any(item.kind == "reserves" for item in openings)
        assert desk.status == 200
        assert "Settle first-face claims" in desk.text
        assert "Required face claims" in desk.text
        assert "Active reserves" in desk.text

    asyncio.run(run())


def test_director_studio_surfaces_community_production_work() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            studio = await client.get("/studio")
            operations = await client.get("/studio/operations")
            structure = await client.get("/studio/structure")
            appearance = await client.get("/studio/appearance")
            content = await client.get("/studio/content")

            assert studio.status == 200
            assert "Director Studio" in studio.text
            assert "<h1>Studio</h1>" in studio.text
            assert "Run X-Men Apocalypse without carrying every control at once." in studio.text
            assert "Needs attention" in studio.text
            assert "No director queues need attention right now." in studio.text
            assert "Production calm" in studio.text
            assert "Studio rooms" in studio.text
            assert "Operations" in studio.text
            assert "Discovery profile" in studio.text
            assert "Structure" in studio.text
            assert "Intake" in studio.text
            assert "Appearance" in studio.text
            assert "Content" in studio.text
            assert 'href="/studio/operations"' in studio.text
            assert 'href="/studio/launch"' in studio.text
            assert 'href="/studio/discovery"' in studio.text
            assert 'href="/studio/structure"' in studio.text
            assert 'href="/studio/intake"' in studio.text
            assert 'href="/studio/appearance"' in studio.text
            assert 'href="/studio/content"' in studio.text
            assert 'id="chirp-shell-actions"' in studio.text
            assert "Daily director console" not in studio.text
            assert 'id="world-structure"' not in _page_content(studio.text)
            assert 'id="navigation"' not in _page_content(studio.text)
            assert 'id="identity-appearance"' not in _page_content(studio.text)
            assert 'id="casting-applications"' not in _page_content(studio.text)
            assert 'id="continuity-events"' not in _page_content(studio.text)
            assert structure.status == 200
            assert "data-elbysodic-spotlight-composer" not in structure.text
            assert "Board map" in structure.text
            assert "Board map audit" in structure.text
            assert "Sidebar audit" in structure.text
            assert "Navigation Health" in structure.text
            assert "Check the sidebars people will actually see" in structure.text
            assert "Goal</strong>" in structure.text
            assert "Help visitors move from the realm overview" in structure.text
            assert "Keep director production rooms and staff boards separate" in structure.text
            assert "Fixed route" in structure.text
            assert "App-owned" not in structure.text
            assert "World sidebar" in structure.text
            assert "Desk sidebar" in structure.text
            assert "Studio sidebar" in structure.text
            assert "Casting sidebar" in structure.text
            assert "Announcements" in structure.text
            assert 'href="/studio/boards/announcements"' in structure.text
            assert appearance.status == 200
            assert "Identity and appearance" in appearance.text
            assert "Inherited accents" in appearance.text
            assert content.status == 200
            assert "Content at a glance" in content.text
            assert "Guidebook" in content.text
            assert "Locations" in content.text
            assert "Current event" in content.text
            assert "Applications and hooks" in content.text
            assert 'href="/world/b-24-winter"' in content.text
            assert 'href="/applications"' in content.text
            assert 'href="/wanted"' in content.text
            assert "Current event" in content.text
            assert operations.status == 200
            assert "Director desk" in operations.text
            assert '<h1 id="operations-heading">Operations</h1>' in operations.text
            assert "Technical checks" in operations.text
            assert '<details class="elbysodic-operations-diagnostics">' in operations.text
            assert "No director operations need attention right now." in operations.text
            assert "Operations clear" in operations.text
            assert "Review queue" not in operations.text
            assert "Claim conflicts" not in operations.text
            assert "Active reserves" not in operations.text
            assert "Hooks with movement" not in operations.text
            assert "Ready for scene" not in operations.text
            assert "Staff notifications" not in operations.text
            assert "Production health" not in operations.text
            assert "Draft materials" not in operations.text
            assert "Dry-run intake" not in operations.text
            assert "Release smoke" not in operations.text
            assert "Community builder checklist" not in operations.text
            assert "Ready to review" not in operations.text

        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        staff_app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )
        async with TestClient(staff_app) as staff_client:
            launch = await staff_client.get("/studio/launch")

        assert launch.status == 200
        assert "Open realm" in launch.text
        assert "Open the realm with the writing surface intact." in launch.text
        assert "Opening checklist" in launch.text
        assert 'class="elbysodic-launch-checklist"' in launch.text
        assert "elbysodic-launch-checklist__item--ready" in launch.text
        assert "elbysodic-launch-checklist__copy" in launch.text
        assert "Realm identity" in launch.text
        assert "Scene hubs" in launch.text
        assert "Director materials" in launch.text
        assert "Intake and claims" in launch.text
        assert "Wanted hooks" in launch.text
        assert "Appearance" in launch.text
        assert "Invite-only before public self-serve." in launch.text
        assert "Open Studio" not in _page_content(launch.text)
        assert 'href="/studio/intake#program-blueprint-preview"' in launch.text

    asyncio.run(run())


def test_director_context_controls_live_on_home_and_board_surfaces() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        staff_app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )

        async with TestClient(staff_app) as client:
            home = await client.get("/c/x-men-apocalypse")
            board = await client.get("/boards/xavier-institute")

        writer = resolve_seed_persona(services.repo, "xmen_writer")
        writer_app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(writer.community, writer.user, writer.membership, writer.character),
            ),
        )
        async with TestClient(writer_app) as client:
            writer_home = await client.get("/c/x-men-apocalypse")
            writer_board = await client.get("/boards/xavier-institute")

        assert home.status == 200
        assert "Edit realm home" in home.text
        assert "elbysodic-realm-gateway__director-tools" in home.text
        assert "/studio/structure#gateway-curation" in home.text
        assert "/studio/discovery" in home.text
        assert board.status == 200
        assert "Manage place" in board.text
        assert "elbysodic-director-context" not in board.text
        assert "/studio/boards/xavier-institute" in board.text
        assert "/studio/structure#board-taxonomy" in board.text

        assert writer_home.status == 200
        assert "Edit realm home" not in writer_home.text
        assert writer_board.status == 200
        assert "Manage place" not in writer_board.text
        assert "/studio/boards/xavier-institute" not in writer_board.text

    asyncio.run(run())


def test_studio_operations_tracks_writer_activation_oversight() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        role = services.repo.get_role_by_slug(staff.community.id, "member")
        user = services.repo.create_user("activation-watch@example.com", "hash")
        services.repo.create_membership(
            staff.community.id,
            user.id,
            role.id,
            "activation-watch",
            "Activation Watch",
        )
        access_request = services.repo.create_community_access_request(
            staff.community.id,
            email="prospect@example.com",
            display_name="Prospect",
            face_concept="Transfer student",
            wanted_hook="Danger Room opening",
            notes="Needs an invitation.",
        )
        staff_services = AppServices(
            services.repo,
            DemoSeed(staff.community, staff.user, staff.membership, staff.character),
        )
        app = create_app(
            debug=False,
            services=staff_services,
        )

        operations_model = staff_services.director_operations()
        parity = {row.label: row for row in operations_model.parity_rows}
        async with TestClient(app) as client:
            operations = await client.get("/studio/operations")

        assert [(lane.label, lane.href) for lane in operations_model.lanes] == [
            ("Needs decision", f"/studio/access-requests/{access_request.id}")
        ]
        assert parity["Launch"].first_action_href == f"/studio/access-requests/{access_request.id}"
        assert parity["Launch"].list_href == "/studio/launch#access-requests"
        assert parity["Notifications"].count == staff_services.viewer().unread_notification_count
        assert parity["Runtime diagnostics"].diagnostic_scope == "hidden from this viewer"
        assert operations.status == 200
        assert "Writer activation" in operations.text
        assert "Operations attention lanes" in operations.text
        assert "Needs decision" in operations.text
        assert f'href="/studio/access-requests/{access_request.id}"' in operations.text
        assert 'href="#director-operation-signals"' not in operations.text
        assert "Queues that should move before writers stall." in operations.text
        assert "<em>Blocked</em>" not in operations.text
        assert "<em>Watching</em>" not in operations.text
        assert "Operations queue shortcuts" in operations.text
        assert 'href="/applications"' in operations.text
        assert 'href="/casting"' in operations.text
        assert 'href="/plotting#interest-inbox"' in operations.text
        assert 'href="/studio/launch#access-requests"' in operations.text
        assert "Queue contracts" in operations.text
        assert f'href="/studio/access-requests/{access_request.id}"' in operations.text
        assert "director launch capability" in operations.text
        assert "own visible unread targets only" in operations.text
        assert "hidden targets do not affect visible page windows" in operations.text
        assert "1 access request(s)" in operations.text
        assert "Prospect - Transfer student" in operations.text
        assert "accepted member(s) without faces" in operations.text
        assert "Invites, first faces, applications, raised hands, and first-scene handoffs." in (
            operations.text
        )

    asyncio.run(run())


def test_studio_launch_moderates_access_requests() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        access_request = services.repo.create_community_access_request(
            staff.community.id,
            email="launch-prospect@example.com",
            display_name="Launch Prospect",
            face_concept="Exchange student",
            wanted_hook="Danger Room opening",
            notes="Can post weekly.",
        )
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )

        async with TestClient(app) as client:
            launch = await client.get("/studio/launch")
            reviewed = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "review_access_request",
                        "access_request_id": str(access_request.id),
                    }
                ).encode(),
                headers=_FORM,
            )
            launch_after_review = await client.get("/studio/launch")
            declined = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "decline_access_request",
                        "access_request_id": str(access_request.id),
                    }
                ).encode(),
                headers=_FORM,
            )
            launch_after_decline = await client.get("/studio/launch")

        assert launch.status == 200
        assert "Access requests" in launch.text
        assert "launch-prospect@example.com" in launch.text
        assert "Exchange student" in launch.text
        assert "Mark reviewed" in launch.text
        assert "Decline request" in launch.text
        assert "elbysodic-studio-actions" in launch.text
        assert "elbysodic-network-card__actions" not in launch.text
        assert (
            launch.text.count('class="chirpui-field chirpui-field--outlined elbysodic-form-field"')
            >= 4
        )
        assert '<input class="chirpui-field__input" name="scene_hub_name"' in launch.text
        assert '<textarea class="chirpui-field__input" name="premise_summary"' in launch.text
        assert '<textarea class="chirpui-field__input" name="application_summary"' in launch.text
        assert '<input class="chirpui-field__input" name="email" type="email"' in launch.text
        assert reviewed.status == 200
        assert "was reviewed" in reviewed.text
        assert "Reviewed" in launch_after_review.text
        assert "Decline request" in launch_after_review.text
        assert declined.status == 200
        assert "was declined" in declined.text
        assert "Declined" in launch_after_decline.text
        assert "Mark reviewed" not in launch_after_decline.text
        declined_request = services.repo.get_community_access_request(
            staff.community.id,
            access_request.id,
        )
        events = services.repo.list_community_access_request_events(
            staff.community.id,
            access_request.id,
        )
        invitations = services.repo.list_community_invitations(staff.community.id)
        assert declined_request.status == "declined"
        assert declined_request.invitation_id is None
        assert [event.event_type for event in events] == ["submitted", "reviewed", "declined"]
        assert [(event.from_status, event.to_status) for event in events] == [
            (None, "pending"),
            ("pending", "reviewed"),
            ("reviewed", "declined"),
        ]
        assert events[-1].actor_membership_id == staff.membership.id
        assert events[-1].invitation_id is None
        assert invitations == []

        replayed_decline = AppServices(
            services.repo,
            DemoSeed(staff.community, staff.user, staff.membership, staff.character),
        ).decline_access_request(access_request.id)

        assert replayed_decline == declined_request
        assert (
            services.repo.list_community_access_request_events(
                staff.community.id,
                access_request.id,
            )
            == events
        )
        assert services.repo.list_community_invitations(staff.community.id) == []

        async with TestClient(app) as client:
            archived_response = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "archive_access_request",
                        "access_request_id": str(access_request.id),
                    }
                ).encode(),
                headers=_FORM,
            )

        archived_request = services.repo.get_community_access_request(
            staff.community.id,
            access_request.id,
        )
        archived_events = services.repo.list_community_access_request_events(
            staff.community.id,
            access_request.id,
        )

        assert archived_response.status == 200
        assert "was archived" in archived_response.text
        assert archived_request.status == "archived"
        assert [event.event_type for event in archived_events] == [
            "submitted",
            "reviewed",
            "declined",
            "archived",
        ]

    asyncio.run(run())


def test_access_request_submission_reuses_open_request_for_email() -> None:
    services = create_services(path=":memory:")
    account = services.repo.create_user("prospect@example.com", "hash")

    first = services.create_access_request(
        "afterlight-accord",
        email="Prospect@Example.com",
        display_name="Prospect One",
        face_concept="Archive thief",
        wanted_hook="Sealed branch",
        notes="First note.",
    )
    second = services.create_access_request(
        "afterlight-accord",
        email="prospect@example.com",
        display_name="Prospect Two",
        face_concept="Forbidden envoy",
        wanted_hook="Transit gate",
        notes="Second note.",
        account_user_id=account.id,
    )
    community = services.repo.get_community_by_slug("afterlight-accord")

    assert second.id == first.id
    assert second.account_user_id == account.id
    assert services.repo.list_community_access_requests(community.id) == [second]
    assert second.email == "prospect@example.com"
    assert second.display_name == "Prospect One"
    with pytest.raises(LookupError):
        services.repo.get_membership_for_user(community.id, account.id)


def test_director_reads_access_request_detail() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        access_request = services.repo.create_community_access_request(
            staff.community.id,
            email="detail-prospect@example.com",
            display_name="Detail Prospect",
            face_concept="Secret transfer",
            wanted_hook="Archive opening",
            notes="PRIVATE ACCESS NOTE: detail room only.",
        )
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )

        async with TestClient(app) as client:
            launch = await client.get("/studio/launch")
            detail = await client.get(f"/studio/access-requests/{access_request.id}")

        assert launch.status == 200
        assert f'href="/studio/access-requests/{access_request.id}"' in launch.text
        assert detail.status == 200
        assert "Access request" in detail.text
        assert "First-face context" in detail.text
        assert "detail-prospect@example.com" in detail.text
        assert "Secret transfer" in detail.text
        assert "PRIVATE ACCESS NOTE" in detail.text
        assert "Create invitation" in detail.text

    asyncio.run(run())


def test_director_access_request_queue_labels_linked_accounts_without_email() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        account = services.repo.create_user("linked-account@example.com", "hash")
        access_request = services.repo.create_community_access_request(
            staff.community.id,
            email=account.email,
            display_name="Linked Account Prospect",
            face_concept="Nocturne exchange student",
            wanted_hook="Danger Room opening",
            notes="Already has an Elbysodic account.",
            account_user_id=account.id,
        )
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )

        async with TestClient(app) as client:
            launch = await client.get("/studio/launch")
            detail = await client.get(f"/studio/access-requests/{access_request.id}")

        assert launch.status == 200
        assert detail.status == 200
        for response in (launch, detail):
            assert "Linked Account Prospect" in response.text
            assert "Linked Elbysodic account" in response.text
            assert "Elbysodic account on file" in response.text
            assert "linked-account@example.com" not in response.text

    asyncio.run(run())


def test_access_request_detail_shows_linked_invitation_status() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        access_request = services.repo.create_community_access_request(
            staff.community.id,
            email="linked-prospect@example.com",
            display_name="Linked Prospect",
            face_concept="Linked transfer",
            wanted_hook="Linked opening",
            notes="Ready for invitation.",
        )
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )

        async with TestClient(app) as client:
            invited = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "invite_access_request",
                        "access_request_id": str(access_request.id),
                    }
                ).encode(),
                headers=_FORM,
            )
            updated = services.repo.get_community_access_request(
                staff.community.id,
                access_request.id,
            )
            detail = await client.get(f"/studio/access-requests/{access_request.id}")

        assert invited.status == 200
        assert updated.invitation_id is not None
        assert f"#{updated.invitation_id} · Pending" in detail.text
        assert "Reissue invitation" in detail.text
        assert "Revoke invitation" in detail.text

    asyncio.run(run())


def test_access_request_detail_shows_activity_history() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        access_request = services.repo.create_community_access_request(
            staff.community.id,
            email="activity-prospect@example.com",
            display_name="Activity Prospect",
            face_concept="Activity transfer",
            wanted_hook="Activity opening",
            notes="Ready for review.",
        )
        account = services.repo.create_user("activity-prospect@example.com", "hash")
        services.repo.link_community_access_request_account_user(
            staff.community.id,
            access_request.id,
            account.id,
        )
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )

        async with TestClient(app) as client:
            reviewed = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "review_access_request",
                        "access_request_id": str(access_request.id),
                    }
                ).encode(),
                headers=_FORM,
            )
            invited = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "invite_access_request",
                        "access_request_id": str(access_request.id),
                    }
                ).encode(),
                headers=_FORM,
            )
            detail = await client.get(f"/studio/access-requests/{access_request.id}")

        events = services.repo.list_community_access_request_events(
            staff.community.id,
            access_request.id,
        )
        assert reviewed.status == 200
        assert invited.status == 200
        assert [event.event_type for event in events] == [
            "submitted",
            "account_linked",
            "reviewed",
            "invited",
        ]
        assert "Requested access" in detail.text
        assert "Account linked" in detail.text
        assert "Existing request linked to an Elbysodic account" in detail.text
        assert "Marked for review" in detail.text
        assert "Invitation created" in detail.text
        assert f"with invitation #{events[-1].invitation_id}" in detail.text

    asyncio.run(run())


def test_access_request_detail_denies_non_director() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        writer = resolve_seed_persona(services.repo, "xmen_writer")
        access_request = services.repo.create_community_access_request(
            staff.community.id,
            email="hidden-prospect@example.com",
            display_name="Hidden Prospect",
            face_concept="Hidden transfer",
            wanted_hook="Hidden opening",
            notes="PRIVATE ACCESS NOTE: staff-only.",
        )
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(writer.community, writer.user, writer.membership, writer.character),
            ),
        )

        async with TestClient(app) as client:
            response = await client.get(f"/studio/access-requests/{access_request.id}")

        assert response.status == 403
        assert "hidden-prospect@example.com" not in response.text
        assert "Hidden transfer" not in response.text
        assert "PRIVATE ACCESS NOTE" not in response.text

    asyncio.run(run())


def test_access_request_detail_denies_inactive_and_cross_community_director() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        inactive = resolve_seed_persona(services.repo, "xmen_inactive")
        hp_director = resolve_seed_persona(services.repo, "hp_director")
        account = services.repo.create_user("boundary-prospect@example.com", "hash")
        access_request = services.repo.create_community_access_request(
            staff.community.id,
            email="boundary-prospect@example.com",
            display_name="Boundary Prospect",
            face_concept="Boundary transfer",
            wanted_hook="Boundary opening",
            notes="PRIVATE ACCESS NOTE: cross-viewer detail room only.",
        )
        services.repo.link_community_access_request_account_user(
            staff.community.id,
            access_request.id,
            account.id,
        )
        staff_services = AppServices(
            services.repo,
            DemoSeed(staff.community, staff.user, staff.membership, staff.character),
        )
        staff_services.review_access_request(access_request.id)
        created = staff_services.invite_access_request(access_request.id)

        denied_viewers = [
            (
                inactive,
                403,
            ),
            (
                hp_director,
                404,
            ),
        ]
        responses = []
        for persona, expected_status in denied_viewers:
            app = create_app(
                debug=False,
                services=AppServices(
                    services.repo,
                    DemoSeed(
                        persona.community,
                        persona.user,
                        persona.membership,
                        persona.character,
                    ),
                ),
            )
            async with TestClient(app) as client:
                response = await client.get(f"/studio/access-requests/{access_request.id}")
            assert response.status == expected_status
            responses.append(response)

        for response in responses:
            for hidden in (
                "boundary-prospect@example.com",
                "Boundary Prospect",
                "Boundary transfer",
                "Boundary opening",
                "PRIVATE ACCESS NOTE",
                "Linked Elbysodic account",
                "Elbysodic account on file",
                "Requested access",
                "Account linked",
                "Marked for review",
                "Invitation created",
                f"#{created.invitation.id} · Pending",
            ):
                assert hidden not in response.text

    asyncio.run(run())


def test_studio_launch_invites_writer_from_access_request() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        access_request = services.repo.create_community_access_request(
            staff.community.id,
            email="invite-prospect@example.com",
            display_name="Invite Prospect",
            face_concept="Transfer student",
            wanted_hook="Archive opening",
            notes="Ready for invite-only access.",
        )
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )

        async with TestClient(app) as client:
            launch = await client.get("/studio/launch")
            invited = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "invite_access_request",
                        "access_request_id": str(access_request.id),
                    }
                ).encode(),
                headers=_FORM,
            )
            launch_after = await client.get("/studio/launch")

        updated = services.repo.get_community_access_request(staff.community.id, access_request.id)
        invitations = services.repo.list_community_invitations(staff.community.id)

        assert launch.status == 200
        assert "Create invitation" in launch.text
        assert invited.status == 200
        assert "Invitation created from access request for Invite Prospect." in (invited.text)
        assert "/invite/" in invited.text
        assert updated.status == "invited"
        assert updated.invitation_id is not None
        assert invitations[0].id == updated.invitation_id
        assert invitations[0].email == "invite-prospect@example.com"
        assert "Invited" in launch_after.text
        assert f"Invitation #{updated.invitation_id} created" in launch_after.text
        assert "Pending" in launch_after.text
        assert "Studio keeps the token hash only" in launch_after.text
        assert "Decline request" not in launch_after.text

    asyncio.run(run())


def test_access_request_invite_replay_fails_without_duplicate_invitation() -> None:
    services = create_services(path=":memory:")
    staff = resolve_seed_persona(services.repo, "xmen_staff")
    request = services.repo.create_community_access_request(
        staff.community.id,
        email="replay-prospect@example.com",
        display_name="Replay Prospect",
        face_concept="Replay transfer",
        wanted_hook="Replay opening",
        notes="Should only receive one invitation.",
    )
    director_services = AppServices(
        services.repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )

    created = director_services.invite_access_request(request.id)
    before_request = services.repo.get_community_access_request(staff.community.id, request.id)
    before_invitations = services.repo.list_community_invitations(staff.community.id)
    before_events = services.repo.list_community_access_request_events(
        staff.community.id,
        request.id,
    )

    with pytest.raises(ValueError, match="only pending or reviewed access requests"):
        director_services.invite_access_request(request.id)

    after_request = services.repo.get_community_access_request(staff.community.id, request.id)
    after_invitations = services.repo.list_community_invitations(staff.community.id)
    after_events = services.repo.list_community_access_request_events(
        staff.community.id,
        request.id,
    )

    assert before_request.status == "invited"
    assert before_request.invitation_id == created.invitation.id
    assert after_request == before_request
    assert after_invitations == before_invitations
    assert after_events == before_events
    assert [event.event_type for event in after_events] == ["submitted", "invited"]


def test_access_request_invitation_rolls_back_when_status_update_fails(monkeypatch) -> None:
    services = create_services(path=":memory:")
    staff = resolve_seed_persona(services.repo, "xmen_staff")
    request = services.repo.create_community_access_request(
        staff.community.id,
        email="rollback-prospect@example.com",
        display_name="Rollback Prospect",
        face_concept="Rollback transfer",
        wanted_hook="Rollback opening",
        notes="Should stay pending.",
    )
    director_services = AppServices(
        services.repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )
    before_invitation_ids = {
        invitation.id for invitation in services.repo.list_community_invitations(staff.community.id)
    }

    def fail_status_update(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated access-request update failure")

    monkeypatch.setattr(
        services.repo,
        "update_community_access_request_status",
        fail_status_update,
    )

    with pytest.raises(RuntimeError, match="simulated access-request update failure"):
        director_services.invite_access_request(request.id)

    after_request = services.repo.get_community_access_request(staff.community.id, request.id)
    after_invitation_ids = {
        invitation.id for invitation in services.repo.list_community_invitations(staff.community.id)
    }
    events = services.repo.list_community_access_request_events(staff.community.id, request.id)

    assert after_request.status == "pending"
    assert after_request.invitation_id is None
    assert after_invitation_ids == before_invitation_ids
    assert [event.event_type for event in events] == ["submitted"]


def test_access_request_acceptance_updates_lifecycle_without_exposing_token() -> None:
    services = create_services(path=":memory:")
    staff = resolve_seed_persona(services.repo, "xmen_staff")
    request = services.repo.create_community_access_request(
        staff.community.id,
        email="accepted-prospect@example.com",
        display_name="Accepted Prospect",
        face_concept="Accepted transfer",
        wanted_hook="Accepted opening",
        notes="Private acceptance context.",
    )
    director_services = AppServices(
        services.repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )

    created = director_services.invite_access_request(request.id)
    accepted = director_services.accept_invitation(
        created.token,
        password="-".join(("accepted", "password")),
        username="accepted-prospect",
        display_name="Accepted Prospect",
    )

    updated = services.repo.get_community_access_request(staff.community.id, request.id)
    events = services.repo.list_community_access_request_events(staff.community.id, request.id)
    memberships = services.repo.list_memberships_for_user(accepted.identity.user_id)

    assert updated.status == "accepted"
    assert updated.invitation_id == created.invitation.id
    assert [event.event_type for event in events] == ["submitted", "invited", "accepted"]
    assert events[-1].invitation_id == created.invitation.id
    assert created.token not in repr(updated)
    assert created.token not in repr(events)
    assert [(membership.community_id, membership.user_id) for membership in memberships] == [
        (staff.community.id, accepted.identity.user_id)
    ]


def test_access_request_invitation_reissue_and_revoke_keep_request_linked() -> None:
    services = create_services(path=":memory:")
    staff = resolve_seed_persona(services.repo, "xmen_staff")
    request = services.repo.create_community_access_request(
        staff.community.id,
        email="linked-reissue@example.com",
        display_name="Linked Reissue",
        face_concept="Signal keeper",
        wanted_hook="Reissue opening",
        notes="Keep lifecycle history private.",
    )
    director_services = AppServices(
        services.repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )
    original = director_services.invite_access_request(request.id)

    reissued = director_services.reissue_writer_invitation(original.invitation.id)
    after_reissue = services.repo.get_community_access_request(staff.community.id, request.id)
    old_invitation = services.repo.get_community_invitation(
        staff.community.id,
        original.invitation.id,
    )

    assert old_invitation.status == "revoked"
    assert after_reissue.status == "invited"
    assert after_reissue.invitation_id == reissued.invitation.id
    assert reissued.token != original.token

    revoked = director_services.revoke_writer_invitation(reissued.invitation.id)
    after_revoke = services.repo.get_community_access_request(staff.community.id, request.id)
    events = services.repo.list_community_access_request_events(staff.community.id, request.id)

    assert revoked.status == "revoked"
    assert after_revoke.status == "reviewed"
    assert after_revoke.invitation_id == reissued.invitation.id
    assert [event.event_type for event in events] == [
        "submitted",
        "invited",
        "invitation_reissued",
        "invitation_revoked",
    ]


def test_access_request_withdraw_expire_and_archive_are_idempotent() -> None:
    services = create_services(path=":memory:")
    staff = resolve_seed_persona(services.repo, "xmen_staff")
    account = services.repo.create_user("withdraw-request@example.com", "hash")
    other_account = services.repo.create_user("other-withdraw@example.com", "hash")
    request = services.create_access_request(
        staff.community.slug,
        email=account.email,
        display_name="Withdraw Prospect",
        face_concept="Quiet transfer",
        wanted_hook="Withdrawal opening",
        notes="Private withdrawal context.",
        account_user_id=account.id,
    )
    director_services = AppServices(
        services.repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )
    created = director_services.invite_access_request(request.id)

    with pytest.raises(PermissionError, match="access request is not available"):
        services.withdraw_access_request_for_account(
            staff.community.slug,
            request.id,
            other_account.id,
        )

    withdrawn = services.withdraw_access_request_for_account(
        staff.community.slug,
        request.id,
        account.id,
    )
    withdrawn_again = services.withdraw_access_request_for_account(
        staff.community.slug,
        request.id,
        account.id,
    )
    revoked_invitation = services.repo.get_community_invitation(
        staff.community.id,
        created.invitation.id,
    )
    archived = director_services.archive_access_request(request.id)
    archived_again = director_services.archive_access_request(request.id)
    events = services.repo.list_community_access_request_events(staff.community.id, request.id)

    assert withdrawn == withdrawn_again
    assert withdrawn.status == "withdrawn"
    assert revoked_invitation.status == "revoked"
    assert archived == archived_again
    assert archived.status == "archived"
    assert [event.event_type for event in events] == [
        "submitted",
        "invited",
        "withdrawn",
        "archived",
    ]
    assert services.repo.list_memberships_for_user(account.id) == []

    expiring = services.repo.create_community_access_request(
        staff.community.id,
        email="expire-request@example.com",
        display_name="Expire Prospect",
        face_concept="Stale transfer",
        wanted_hook="Expired opening",
        notes="Stale private context.",
    )
    expired = director_services.expire_access_request(expiring.id)
    expired_again = director_services.expire_access_request(expiring.id)

    assert expired == expired_again
    assert expired.status == "expired"
    assert [
        event.event_type
        for event in services.repo.list_community_access_request_events(
            staff.community.id,
            expiring.id,
        )
    ] == ["submitted", "expired"]


def test_account_linked_access_request_requires_matching_global_email() -> None:
    services = create_services(path=":memory:")
    account = services.repo.create_user("account-owner@example.com", "hash")

    with pytest.raises(PermissionError, match="cannot be linked to this account"):
        services.create_access_request(
            "afterlight-accord",
            email="different-applicant@example.com",
            display_name="Wrong account",
            face_concept="Wrong link",
            wanted_hook="Wrong opening",
            notes="Must not persist.",
            account_user_id=account.id,
        )

    community = services.repo.get_community_by_slug("afterlight-accord")
    assert services.repo.list_community_access_requests(community.id) == []
    assert services.repo.list_memberships_for_user(account.id) == []


def test_realm_launch_room_marks_empty_configured_realm_backstage() -> None:
    async def run() -> None:
        connection = connect(":memory:", check_same_thread=False)
        create_schema(connection)
        repo = ForumRepository(connection)
        community = repo.create_community("starter-realm", "Starter Realm")
        role = repo.create_role(community.id, "director", "Director", is_admin=True)
        user = repo.create_user("starter-director@example.com", "hash")
        membership = repo.create_membership(
            community.id,
            user.id,
            role.id,
            "starter-director",
            "Starter Director",
        )
        app = create_app(
            debug=False,
            services=AppServices(repo, DemoSeed(community, user, membership, None)),
        )
        repo.update_community_launch_status(community.id, "public-preview")

        async with TestClient(app) as client:
            studio = await client.get("/studio")
            launch = await client.get("/studio/launch")

        public_directory = AppServices(repo, None).public_studio_network()

        assert studio.status == 302
        assert _response_header(studio, "location") == "/studio/launch"
        assert launch.status == 200
        assert "Starter Realm" in launch.text
        assert "required lanes still backstage" in launch.text
        assert "Scene hubs" in launch.text
        assert "Director materials" in launch.text
        assert "Intake and claims" in launch.text
        assert "Needed" in launch.text
        assert "Open the realm with the writing surface intact." in launch.text
        assert all(program.community.id != community.id for program in public_directory.programs)

    asyncio.run(run())


def test_guided_realm_builder_creates_minimum_opening_packet() -> None:
    async def run() -> None:
        connection = connect(":memory:", check_same_thread=False)
        create_schema(connection)
        repo = ForumRepository(connection)
        community = repo.create_community("builder-realm", "Builder Realm")
        role = repo.create_role(community.id, "director", "Director", is_admin=True)
        user = repo.create_user("builder-director@example.com", "hash")
        membership = repo.create_membership(
            community.id,
            user.id,
            role.id,
            "builder-director",
            "Builder Director",
        )
        app = create_app(
            debug=False,
            services=AppServices(repo, DemoSeed(community, user, membership, None)),
        )

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "apply_builder",
                        "scene_hub_name": "Opening Scenes",
                        "premise_summary": "A city of masks opens for new threads.",
                        "application_summary": "Bring a face, hooks, limits, and claims.",
                    }
                ).encode(),
                headers=_FORM,
            )
            launch = await client.get("/studio/launch")

        board = repo.get_board_by_slug(community.id, "opening-scenes")
        premise = repo.get_material_by_slug(community.id, "realm-premise")
        application = repo.get_material_by_slug(community.id, "application-guide")

        assert response.status == 200
        assert (
            "Opening packet added scene hub, premise material, application guide." in response.text
        )
        assert "Ready for invite-only opening" in launch.text
        assert board.community_id == community.id
        assert board.board_kind == "location"
        assert not board.is_private
        assert premise.material_type == "premise"
        assert premise.status == "published"
        assert premise.summary == "A city of masks opens for new threads."
        assert application.material_type == "application"
        assert application.summary == "Bring a face, hooks, limits, and claims."
        assert repo.get_default_theme(community.id) is not None

    asyncio.run(run())


def test_director_can_update_discovery_profile_from_studio() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )

        async with TestClient(app) as client:
            editor = await client.get("/studio/discovery")
            updated = await client.post(
                "/studio/discovery",
                body=urlencode(
                    {
                        "premise_archetype": "weird-town-mystery",
                        "play_engine": "mystery-driven",
                        "lore_aperture": "open-lore",
                        "access_model": "public-preview",
                        "application_model": "profile-app",
                        "age_rating": "18+",
                        "content_rating": "3/3/3",
                        "activity_pace": "weekly",
                        "activity_expectation": "weekly clue scenes and rumor prompts",
                        "forum_adjunct": "forum-first",
                        "roster_posture": "locals, skeptics, staff, and original faces",
                        "catalog_pitch": "A testable mystery posture for public catalog cards.",
                        "onboarding_pitch": "Start with a rumor, a clue, or a wanted hook.",
                        "staff_pick_label": "Mystery test pick",
                        "discovery_tags": (
                            "premise|studio-mystery|Studio mystery|director edited mystery signal"
                        ),
                    }
                ).encode(),
                headers=_FORM,
            )
            restored = await client.get("/studio/discovery")

        profile = services.repo.get_discovery_profile(staff.community.id)
        tags = services.repo.list_discovery_tags_for_communities([staff.community.id])[
            staff.community.id
        ]
        results = services.network_explore("studio-mystery").results

        assert editor.status == 200
        assert "Discovery profile" in editor.text
        assert "X-Men Apocalypse" in editor.text
        assert "data-elbysodic-discovery-preview-form" in editor.text
        assert "data-elbysodic-discovery-preview-card" in editor.text
        assert "data-elbysodic-preview-summary" in editor.text
        assert "data-elbysodic-preview-tags" in editor.text
        assert updated.status == 302
        assert _response_header(updated, "location") == "/studio/discovery"
        assert restored.status == 200
        assert "This is how the realm appears in Network Explore." in restored.text
        assert 'class="elbysodic-network-card' in restored.text
        assert "A testable mystery posture for public catalog cards." in restored.text
        assert profile.premise_archetype == "weird-town-mystery"
        assert profile.featured_event_material_id is not None
        assert [tag.tag_key for tag in tags] == ["studio-mystery"]
        assert [card.community.slug for card in results] == ["x-men-apocalypse"]

    asyncio.run(run())


def test_discovery_profile_editor_requires_director_membership() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        writer = resolve_seed_persona(services.repo, "xmen_writer")
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(writer.community, writer.user, writer.membership, writer.character),
            ),
        )

        async with TestClient(app) as client:
            editor = await client.get("/studio/discovery")
            updated = await client.post(
                "/studio/discovery",
                body=urlencode(
                    {
                        "premise_archetype": "weird-town-mystery",
                        "play_engine": "mystery-driven",
                        "lore_aperture": "open-lore",
                        "access_model": "public-preview",
                        "application_model": "profile-app",
                        "age_rating": "18+",
                        "content_rating": "3/3/3",
                        "activity_pace": "weekly",
                        "forum_adjunct": "forum-first",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert editor.status == 403
        assert updated.status == 403

    asyncio.run(run())


def test_director_can_update_realm_launch_status() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )

        async with TestClient(app) as client:
            updated = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "launch_status",
                        "launch_status": "invite-only",
                    }
                ).encode(),
                headers=_FORM,
            )
            invite_only = services.repo.get_community(staff.community.id)
            public_directory = services.public_studio_network()
            restored = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "launch_status",
                        "launch_status": "public-preview",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert updated.status == 200
        assert "Opening changed to invite-only." in updated.text
        assert invite_only.launch_status == "invite-only"
        assert all(
            program.community.id != staff.community.id for program in public_directory.programs
        )
        assert restored.status == 200
        assert "Opening changed to public-preview." in restored.text
        assert services.repo.get_community(staff.community.id).launch_status == "public-preview"

    asyncio.run(run())


def test_director_invites_writer_through_first_face_handoff() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )

        async with TestClient(app) as client:
            launch = await client.get("/studio/launch")
            created = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "create_invite",
                        "email": "new-writer@example.com",
                    }
                ).encode(),
                headers=_FORM,
            )
            match = re.search(r'href="(?P<href>/invite/[^"]+)"', created.text)
            assert match is not None
            invite_href = match.group("href")
            invite = await client.get(invite_href)
            accepted = await client.post(
                invite_href,
                body=urlencode(
                    {
                        "username": "new-writer",
                        "display_name": "New Writer",
                        "password": "writer-password",
                        "first_face_name": "First Face",
                    }
                ).encode(),
                headers=_FORM,
            )
            set_cookie = _response_header(accepted, "set-cookie")
            cookie = set_cookie.split(";", 1)[0]
            desk = await client.get("/c/x-men-apocalypse/desk", headers={"Cookie": cookie})
            replay = await client.get(invite_href)

        community = services.seed.community
        user = services.repo.get_user_by_email("new-writer@example.com")
        membership = services.repo.get_membership_for_user(community.id, user.id)
        character = services.repo.get_character_by_slug(community.id, "first-face")
        invitations = services.repo.list_community_invitations(community.id)

        assert launch.status == 200
        assert "Invite one writer into this realm." in launch.text
        assert created.status == 200
        assert "Invitation ready for new-writer@example.com" in created.text
        assert "Delivery is copy-only for this alpha slice." in created.text
        assert "Copy this link now; Studio stores only the token hash." in created.text
        assert "Raw link is no longer available here." in created.text
        assert invite.status == 200
        assert "This invitation is for new-writer@example.com" in invite.text
        assert accepted.status == 302
        assert _response_header(accepted, "location") == "/c/x-men-apocalypse/desk"
        assert "elbysodic_session=" in set_cookie
        assert desk.status == 200
        assert "playing as First Face" in desk.text
        assert replay.status == 403
        assert user.password_hash.startswith("$argon2id$")
        assert membership.username == "new-writer"
        assert membership.default_character_id == character.id
        assert character.membership_id == membership.id
        assert invitations[0].status == "accepted"
        assert invitations[0].accepted_membership_id == membership.id

    asyncio.run(run())


def test_invitation_acceptance_rolls_back_when_session_creation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    staff = resolve_seed_persona(repo, "xmen_staff")
    staff_services = AppServices(
        repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )
    access_request = repo.create_community_access_request(
        staff.community.id,
        email="rollback-invite@example.com",
        display_name="Rollback Invite",
        face_concept="Rollback face",
        wanted_hook="Rollback opening",
        notes="Acceptance must roll back all lifecycle writes.",
    )
    created = staff_services.invite_access_request(access_request.id)
    session_count_before = repo.connection.execute("SELECT COUNT(*) FROM user_sessions").fetchone()[
        0
    ]

    def fail_session_creation(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("simulated invite session failure")

    monkeypatch.setattr(staff_services, "_create_session_for_user", fail_session_creation)

    with pytest.raises(RuntimeError, match="simulated invite session failure"):
        staff_services.accept_invitation(
            created.token,
            username="rollback-invite",
            display_name="Rollback Invite",
            password="-".join(("writer", "password")),
            first_face_name="Rollback Face",
        )

    invitation = repo.get_community_invitation(staff.community.id, created.invitation.id)
    session_count_after = repo.connection.execute("SELECT COUNT(*) FROM user_sessions").fetchone()[
        0
    ]

    assert invitation.status == "pending"
    assert invitation.accepted_user_id is None
    assert invitation.accepted_membership_id is None
    assert invitation.accepted_at is None
    unchanged_request = repo.get_community_access_request(
        staff.community.id,
        access_request.id,
    )
    assert unchanged_request.status == "invited"
    assert unchanged_request.invitation_id == invitation.id
    assert [
        event.event_type
        for event in repo.list_community_access_request_events(
            staff.community.id,
            access_request.id,
        )
    ] == ["submitted", "invited"]
    assert session_count_after == session_count_before
    with pytest.raises(LookupError):
        repo.get_user_by_email("rollback-invite@example.com")
    with pytest.raises(LookupError):
        repo.get_membership_by_username(staff.community.id, "rollback-invite")
    with pytest.raises(LookupError):
        repo.get_character_by_slug(staff.community.id, "rollback-face")
    assert not repo.connection.in_transaction


def test_director_can_revoke_pending_writer_invitation() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )

        async with TestClient(app) as client:
            created = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "create_invite",
                        "email": "revoked-writer@example.com",
                    }
                ).encode(),
                headers=_FORM,
            )
            match = re.search(r'href="(?P<href>/invite/[^"]+)"', created.text)
            assert match is not None
            invite_href = match.group("href")
            invitations = services.repo.list_community_invitations(staff.community.id)
            revoked = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "revoke_invite",
                        "invitation_id": str(invitations[0].id),
                    }
                ).encode(),
                headers=_FORM,
            )
            denied = await client.get(invite_href)

        invitation = services.repo.get_community_invitation(
            staff.community.id,
            invitations[0].id,
        )

        assert created.status == 200
        assert "revoked-writer@example.com" in created.text
        assert "Revoke invitation" in created.text
        assert revoked.status == 200
        assert "Invitation for revoked-writer@example.com was revoked." in revoked.text
        assert "Revoked" in revoked.text
        assert "Reissue invitation" not in revoked.text
        assert "Revoke invitation" not in revoked.text
        assert denied.status == 403
        assert invitation.status == "revoked"
        assert invitation.revoked_at is not None

    asyncio.run(run())


def test_director_can_reissue_pending_writer_invitation() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )

        async with TestClient(app) as client:
            created = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "create_invite",
                        "email": "reissue-writer@example.com",
                    }
                ).encode(),
                headers=_FORM,
            )
            invitations = services.repo.list_community_invitations(staff.community.id)
            reissued = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "reissue_invite",
                        "invitation_id": str(invitations[0].id),
                    }
                ).encode(),
                headers=_FORM,
            )

        invitations_after = services.repo.list_community_invitations(staff.community.id)
        old_invitation = services.repo.get_community_invitation(
            staff.community.id,
            invitations[0].id,
        )

        assert created.status == 200
        assert "Reissue invitation" in created.text
        assert reissued.status == 200
        assert "Invitation for reissue-writer@example.com was reissued." in reissued.text
        assert "Copy the new link now." in reissued.text
        assert "/invite/" in reissued.text
        assert old_invitation.status == "revoked"
        assert old_invitation.revoked_at is not None
        assert len(invitations_after) == 2
        assert invitations_after[0].status == "pending"
        assert invitations_after[0].email == "reissue-writer@example.com"

    asyncio.run(run())


def test_writer_invitation_reissue_policy_is_pending_only_and_hash_only() -> None:
    services = create_services(path=":memory:")
    staff = resolve_seed_persona(services.repo, "xmen_staff")
    staff_services = AppServices(
        services.repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )

    pending = staff_services.create_writer_invitation("lost-link@example.com")
    reissued = staff_services.reissue_writer_invitation(pending.invitation.id)
    old_pending = services.repo.get_community_invitation(
        staff.community.id,
        pending.invitation.id,
    )
    new_pending = services.repo.get_community_invitation(
        staff.community.id,
        reissued.invitation.id,
    )

    accepted = staff_services.create_writer_invitation("accepted-reissue@example.com")
    staff_services.accept_invitation(
        accepted.token,
        username="accepted-reissue",
        display_name="Accepted Reissue",
        password="-".join(("writer", "password")),
    )
    revoked = staff_services.create_writer_invitation("revoked-reissue@example.com")
    staff_services.revoke_writer_invitation(revoked.invitation.id)
    expired = staff_services.create_writer_invitation("expired-reissue@example.com")
    services.repo.connection.execute(
        """
        UPDATE community_invitations
        SET expires_at = '2026-01-01T00:00:00+00:00'
        WHERE community_id = ? AND id = ?
        """,
        (staff.community.id, expired.invitation.id),
    )
    services.repo.connection.commit()

    assert old_pending.status == "revoked"
    assert old_pending.revoked_at is not None
    assert new_pending.status == "pending"
    assert new_pending.email == "lost-link@example.com"
    assert reissued.token != pending.token
    assert pending.token not in old_pending.token_hash
    assert reissued.token not in new_pending.token_hash
    with pytest.raises(ValueError, match="only pending invitations can be reissued"):
        staff_services.reissue_writer_invitation(accepted.invitation.id)
    with pytest.raises(ValueError, match="only pending invitations can be reissued"):
        staff_services.reissue_writer_invitation(revoked.invitation.id)
    with pytest.raises(ValueError, match="only pending invitations can be reissued"):
        staff_services.reissue_writer_invitation(expired.invitation.id)


def test_expired_writer_invitation_cannot_be_accepted_or_revoked() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )

        async with TestClient(app) as client:
            created = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "create_invite",
                        "email": "expired-writer@example.com",
                    }
                ).encode(),
                headers=_FORM,
            )
            match = re.search(r'href="(?P<href>/invite/[^"]+)"', created.text)
            assert match is not None
            invitations = services.repo.list_community_invitations(staff.community.id)
            services.repo.connection.execute(
                """
                UPDATE community_invitations
                SET expires_at = '2026-01-01T00:00:00+00:00'
                WHERE community_id = ? AND id = ?
                """,
                (staff.community.id, invitations[0].id),
            )
            services.repo.connection.commit()
            expired_page = await client.get(match.group("href"))
            launch = await client.get("/studio/launch")

        assert created.status == 200
        assert expired_page.status == 403
        assert launch.status == 200
        assert "expired-writer@example.com" in launch.text
        assert "Expired" in launch.text
        assert "Reissue invitation" not in launch.text
        assert "Revoke invitation" not in launch.text

    asyncio.run(run())


def test_invited_writer_without_first_face_continues_to_application_form() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )

        async with TestClient(app) as client:
            created = await client.post(
                "/studio/launch",
                body=urlencode(
                    {
                        "intent": "create_invite",
                        "email": "no-face-writer@example.com",
                    }
                ).encode(),
                headers=_FORM,
            )
            match = re.search(r'href="(?P<href>/invite/[^"]+)"', created.text)
            assert match is not None
            accepted = await client.post(
                match.group("href"),
                body=urlencode(
                    {
                        "username": "no-face-writer",
                        "display_name": "No Face Writer",
                        "password": "writer-password",
                        "first_face_name": "",
                    }
                ).encode(),
                headers=_FORM,
            )
            cookie = _response_header(accepted, "set-cookie").split(";", 1)[0]
            application = await client.get(
                "/c/x-men-apocalypse/applications/new",
                headers={"Cookie": cookie},
            )
            desk = await client.get("/c/x-men-apocalypse/desk", headers={"Cookie": cookie})

        membership = services.repo.get_membership_for_user(
            staff.community.id,
            services.repo.get_user_by_email("no-face-writer@example.com").id,
        )

        assert accepted.status == 302
        assert _response_header(accepted, "location") == "/c/x-men-apocalypse/applications/new"
        assert membership.default_character_id is None
        assert application.status == 200
        assert "Start a face" in application.text
        assert "Face name" in application.text
        assert "This will become your first active face in X-Men Apocalypse" in application.text
        assert desk.status == 200
        assert "Start with a first face" in desk.text

    asyncio.run(run())


def test_invitation_acceptance_uses_writer_activation_handoff() -> None:
    services = create_services(path=":memory:")
    staff = resolve_seed_persona(services.repo, "xmen_staff")
    staff_services = AppServices(
        services.repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )
    created = staff_services.create_writer_invitation("activation-invite@example.com")

    accepted = staff_services.accept_invitation(
        created.token,
        username="activation-invite",
        display_name="Activation Invite",
        password="writer-" + "password",
    )

    assert accepted.activation.stage == "needs_face"
    assert accepted.activation.primary_href == "/applications/new"
    assert accepted.next_path == "/c/x-men-apocalypse/applications/new"


def test_invitation_acceptance_keeps_existing_account_memberships_local() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    staff = resolve_seed_persona(repo, "xmen_staff")
    hp = repo.get_community_by_slug("hp-universe")
    hp_role = repo.create_role(hp.id, "cross-realm-member", "Cross Realm Member")
    invite_password = "writer-" + "password"
    user = repo.create_user("cross-realm-invite@example.com", hash_password(invite_password))
    hp_membership = repo.create_membership(
        hp.id,
        user.id,
        hp_role.id,
        "cross-realm-hp",
        "Cross Realm HP",
    )
    hp_character = repo.create_character(
        hp.id,
        hp_membership.id,
        "cross-realm-hp-face",
        "Cross Realm HP Face",
        make_default=True,
    )
    staff_services = AppServices(
        repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )
    created = staff_services.create_writer_invitation("cross-realm-invite@example.com")

    accepted = staff_services.accept_invitation(
        created.token,
        username="cross-realm-xmen",
        display_name="Cross Realm X-Men",
        password=invite_password,
        first_face_name="Cross Realm X-Men Face",
    )

    xmen_membership = repo.get_membership_for_user(staff.community.id, user.id)
    xmen_character = repo.get_character_by_slug(staff.community.id, "cross-realm-x-men-face")
    refreshed_hp_membership = repo.get_membership(hp.id, hp_membership.id)

    assert accepted.identity.user_id == user.id
    assert accepted.identity.community_id == staff.community.id
    assert accepted.identity.membership_id == xmen_membership.id
    assert accepted.first_character == xmen_character
    assert accepted.next_path == "/c/x-men-apocalypse/desk"
    assert xmen_membership.user_id == user.id
    assert xmen_membership.default_character_id == xmen_character.id
    assert xmen_character.membership_id == xmen_membership.id
    assert refreshed_hp_membership.default_character_id == hp_character.id
    assert repo.get_character(hp.id, hp_character.id).membership_id == hp_membership.id
    assert repo.list_community_invitations(staff.community.id)[0].accepted_user_id == user.id


def test_realm_launch_room_requires_director_membership() -> None:
    async def run() -> None:
        connection = connect(":memory:", check_same_thread=False)
        create_schema(connection)
        repo = ForumRepository(connection)
        community = repo.create_community("starter-realm", "Starter Realm")
        director_role = repo.create_role(community.id, "director", "Director", is_admin=True)
        member_role = repo.create_role(community.id, "member", "Member", is_admin=False)
        director_user = repo.create_user("starter-director@example.com", "hash")
        repo.create_membership(
            community.id,
            director_user.id,
            director_role.id,
            "starter-director",
            "Starter Director",
        )
        member_user = repo.create_user("starter-member@example.com", "hash")
        member_membership = repo.create_membership(
            community.id,
            member_user.id,
            member_role.id,
            "starter-member",
            "Starter Member",
        )
        app = create_app(
            debug=False,
            services=AppServices(repo, DemoSeed(community, member_user, member_membership, None)),
        )

        async with TestClient(app) as client:
            launch = await client.get("/studio/launch")

        assert launch.status == 403
        assert "Open the realm with the writing surface intact." not in launch.text
        assert "Opening checklist" not in launch.text

    asyncio.run(run())


def test_studio_operations_hides_review_queue_from_non_staff_members() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = services.seed.community
        member_role = repo.get_role_by_slug(community.id, "member")
        applicant_user = repo.create_user("privacy-applicant@example.com", "hash")
        applicant_membership = repo.create_membership(
            community.id,
            applicant_user.id,
            member_role.id,
            "privacy-applicant",
            "Privacy Applicant",
        )
        applicant_face = repo.create_character(
            community.id,
            applicant_membership.id,
            "privacy-queue-face",
            "Privacy Queue Face",
            summary="A submitted face that only staff should triage.",
            application_status="draft",
        )
        application = repo.ensure_character_application(community.id, applicant_face.id)
        repo.update_character_application_draft(
            community.id,
            application.id,
            title="Privacy Queue Face",
            summary="A submitted face that only staff should triage.",
            body="Private application body should not leak through Studio operations.",
        )
        repo.transition_character_application_status(
            community.id,
            application.id,
            status="submitted",
            actor_membership_id=applicant_membership.id,
            actor_character_id=applicant_face.id,
            note="Submitted for director review.",
        )

        member_services, _character_id = _outsider_services(
            services,
            prefix="studio-operations-member",
        )
        member_app = create_app(debug=False, services=member_services)
        async with TestClient(member_app) as member_client:
            member_operations = await member_client.get("/studio/operations")

        alex_membership = repo.get_membership_by_username(community.id, "alex")
        alex_user = repo.get_user(alex_membership.user_id)
        cyclops = repo.get_character_by_slug(community.id, "cyclops")
        staff_app = create_app(
            debug=False,
            services=AppServices(repo, DemoSeed(community, alex_user, alex_membership, cyclops)),
        )
        async with TestClient(staff_app) as staff_client:
            staff_operations = await staff_client.get("/studio/operations")

        assert member_operations.status == 200
        assert "read-only" in member_operations.text
        assert "Privacy Queue Face" not in member_operations.text
        assert "Private application body should not leak" not in member_operations.text
        assert "0 ready apps" in member_operations.text
        assert "Queue contracts" in member_operations.text
        assert "Technical checks" in member_operations.text
        assert "queue names hidden from non-staff" in member_operations.text
        assert "Live check" not in member_operations.text
        assert "Database path" not in member_operations.text
        assert "Database directory" not in member_operations.text
        assert "Volume mount" not in member_operations.text
        assert "Journal mode" not in member_operations.text
        assert "Integrity check" not in member_operations.text
        assert "Public-ready realms" not in member_operations.text
        assert "Seed demo mode" not in member_operations.text
        assert staff_operations.status == 200
        assert "Technical checks" in staff_operations.text
        assert "Privacy Queue Face - ready" in staff_operations.text
        assert "ready apps" in staff_operations.text
        assert "Live check" in staff_operations.text
        assert "Runtime and persistence" in staff_operations.text
        assert "Database path" in staff_operations.text
        assert "Database directory" in staff_operations.text
        assert "Database file" in staff_operations.text
        assert "Volume mount" in staff_operations.text
        assert "Journal mode" in staff_operations.text
        assert "Integrity check" in staff_operations.text
        assert "ok" in staff_operations.text
        assert "Queue contracts" in staff_operations.text
        assert "visible to managers only" in staff_operations.text
        assert "Schema" in staff_operations.text
        assert "Public-ready realms" in staff_operations.text
        assert "Seed demo mode" in staff_operations.text
        assert "Auto seed demo" in staff_operations.text
        assert "Opening" in staff_operations.text

    asyncio.run(run())


def test_studio_intake_previews_program_blueprint_yaml_without_hydration() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)
        before_count = repo.connection.execute(
            "SELECT COUNT(*) FROM communities",
        ).fetchone()[0]
        blueprint_yaml = """
elbysodic_blueprint: 1
program:
  slug: x-men-apocalypse
  name: X-Men Apocalypse
  role:
    slug: staff
    name: Staff
    is_admin: true
characters:
  - slug: blueprint-render-face
    name: Blueprint Render Face
    summary: Florist and town council note-taker.
boards:
  - slug: blueprint-render-main-street
    name: Blueprint Render Main Street
    kind: location
    tagline: One stoplight, twelve opinions.
    description: The town's public spine.
materials:
  - slug: blueprint-render-premise
    title: Blueprint Render Premise
    type: premise
    summary: A small-town ensemble.
    body: Founder's Week should be a cozy pressure cooker.
wanted:
  - slug: blueprint-render-returning-sibling
    title: Blueprint Render Returning Sibling
    type: relationship
    related_material: blueprint-render-premise
    summary: A homecoming character with history.
    body: Someone left, came back, and knows where the deed is hidden.
appearance:
  post_style:
    profile_variant: poster
    accent_style: line
    border_style: hairline
    title_style: serif
    density: calm
  material_variants:
    premise: chapter
"""

        async with TestClient(app) as client:
            page = await client.get("/studio/intake")
            assert 'id="chirp-shell-actions"' in page.text
            assert 'href="/studio"' in page.text
            assert 'href="/studio/operations"' in page.text
            response = await client.post(
                "/studio/intake",
                body=urlencode(
                    {
                        "intent": "preview_blueprint",
                        "blueprint_yaml": blueprint_yaml,
                    }
                ).encode(),
                headers=_FORM,
            )
            preview = admin_services.preview_program_blueprint(blueprint_yaml)
            stale_apply = await client.post(
                "/studio/intake",
                body=urlencode(
                    {
                        "intent": "apply_blueprint",
                        "blueprint_yaml": blueprint_yaml,
                        "preview_fingerprint": "stale-preview",
                        "apply_mode": "create_only",
                    }
                ).encode(),
                headers=_FORM,
            )
            applied = await client.post(
                "/studio/intake",
                body=urlencode(
                    {
                        "intent": "apply_blueprint",
                        "blueprint_yaml": blueprint_yaml,
                        "preview_fingerprint": preview.preview_fingerprint,
                        "apply_mode": "create_only",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert page.status == 200
        assert "Reviewed YAML intake" in page.text
        assert response.status == 200
        assert "valid dry run" in response.text
        assert "1 program" in response.text
        assert "1 starter faces" in response.text
        assert "1 scene hubs" in response.text
        assert "1 materials" in response.text
        assert "1 wanted hooks" in response.text
        assert "1 appearance" in response.text
        assert "postbit: poster rail, hairline frame; 1 guidebook variants" in response.text
        assert "Hydration diff preview" in response.text
        assert "Preview fingerprint:" in response.text
        assert "Preflight: 4 create actions, 3 update actions." in response.text
        assert "update</strong> program: X-Men Apocalypse" in response.text
        assert "create</strong> scene hub: Blueprint Render Main Street" in response.text
        assert "create</strong> wanted hook: Blueprint Render Returning Sibling" in response.text
        assert "Hydration status: nothing has been applied from this preview." in response.text
        assert "Apply readiness review" in response.text
        assert (
            "Preflight resolved 4 create, 3 update, 0 skip, 0 blocked, and 0 warning actions."
            in (response.text)
        )
        assert "No live face or wanted-hook collisions need explicit update mode." in response.text
        assert "Explicit update replaces only current-realm rows" in response.text
        assert "Starter faces and wanted hooks are owned by the importing director" in (
            response.text
        )
        assert "Apply uses one rollback-tested transaction" in response.text
        assert "Collision mode" in response.text
        assert "Create only — stop on live collisions" in response.text
        assert "Apply reviewed blueprint" in response.text
        assert stale_apply.status == 200
        assert "Program Blueprint preview changed; preview again before applying." in (
            stale_apply.text
        )
        assert applied.status == 200
        assert "Blueprint applied in create only mode." in applied.text
        assert "Current-realm rows and the accepted audit event committed together." in (
            applied.text
        )
        assert "Apply reviewed blueprint" not in applied.text
        after_count = repo.connection.execute(
            "SELECT COUNT(*) FROM communities",
        ).fetchone()[0]
        assert after_count == before_count
        assert repo.get_character_by_slug(community.id, "blueprint-render-face").name == (
            "Blueprint Render Face"
        )
        assert repo.get_board_by_slug(community.id, "blueprint-render-main-street").name == (
            "Blueprint Render Main Street"
        )
        assert repo.get_material_by_slug(community.id, "blueprint-render-premise").title == (
            "Blueprint Render Premise"
        )

    asyncio.run(run())


def test_director_studio_updates_sidebar_section_language() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/structure",
                body=urlencode(
                    {
                        "intent": "sidebar_section",
                        "section_key": "locations",
                        "label": "Realms",
                        "description": "The board's playable map language.",
                        "sort_order": 3,
                        "show_label": "on",
                    }
                ).encode(),
                headers=_FORM,
            )

            assert response.status == 302
            section = repo.get_sidebar_section(community.id, "locations")
            assert section.label == "Realms"
            assert section.description == "The board's playable map language."
            assert section.sort_order == 3
            assert section.show_label is True

            locations = await client.get("/locations")
            assert locations.status == 200
            assert 'class="chirpui-sidebar__section-title">Realms</span>' in locations.text
            assert re.search(
                r'<a class="[^"]*elbysodic-sidebar-destination[^"]*"'
                r'[^>]*href="/locations"[^>]*>\s*'
                r'<span class="chirpui-sidebar__icon">.*?</span>\s*'
                r'<span class="chirpui-sidebar__label">Realms</span>',
                locations.text,
                re.S,
            )

            studio = await client.get("/studio/structure")
            assert studio.status == 200
            assert "playable map language" in studio.text
            assert "Realms" in studio.text

    asyncio.run(run())


def test_navigation_health_flags_confusing_sidebar_shapes() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    community = repo.get_community(services.seed.community.id)
    xavier = repo.get_board_by_slug(community.id, "xavier-institute")
    med_bay = repo.get_board_by_slug(community.id, "med-bay")
    announcements = repo.get_board_by_slug(community.id, "announcements")
    staff_room = repo.get_board_by_slug(community.id, "staff-room")

    repo.update_board(
        community.id,
        xavier.id,
        name=xavier.name,
        description=xavier.description,
        sort_order=xavier.sort_order,
        parent_board_id=xavier.parent_board_id,
        board_kind=xavier.board_kind,
        sidebar_section=xavier.sidebar_section,
        tagline=xavier.tagline,
        image_url=xavier.image_url,
        image_alt=xavier.image_alt,
        is_private=xavier.is_private,
        navigation_order=xavier.navigation_order,
        show_in_navigation=False,
    )
    repo.update_board(
        community.id,
        med_bay.id,
        name=med_bay.name,
        description=med_bay.description,
        sort_order=med_bay.sort_order,
        parent_board_id=med_bay.parent_board_id,
        board_kind=med_bay.board_kind,
        sidebar_section="community",
        tagline=med_bay.tagline,
        image_url=med_bay.image_url,
        image_alt=med_bay.image_alt,
        is_private=med_bay.is_private,
        navigation_order=med_bay.navigation_order,
        show_in_navigation=True,
    )
    repo.update_board(
        community.id,
        announcements.id,
        name=announcements.name,
        description=announcements.description,
        sort_order=announcements.sort_order,
        parent_board_id=announcements.parent_board_id,
        board_kind=announcements.board_kind,
        sidebar_section="locations",
        tagline=announcements.tagline,
        image_url=announcements.image_url,
        image_alt=announcements.image_alt,
        is_private=True,
        navigation_order=announcements.navigation_order,
        show_in_navigation=True,
    )
    repo.update_board(
        community.id,
        staff_room.id,
        name=staff_room.name,
        description=staff_room.description,
        sort_order=staff_room.sort_order,
        parent_board_id=staff_room.parent_board_id,
        board_kind=staff_room.board_kind,
        sidebar_section="studio",
        tagline=staff_room.tagline,
        image_url=staff_room.image_url,
        image_alt=staff_room.image_alt,
        is_private=False,
        navigation_order=staff_room.navigation_order,
        show_in_navigation=True,
    )
    repo.update_sidebar_section(
        community.id,
        "studio",
        label="Director Studio",
        description="Director lanes.",
        sort_order=20,
        show_label=True,
    )

    user = repo.get_user_by_email("moira@example.com")
    membership = repo.get_membership_by_username(community.id, "moira")
    character = repo.get_character_by_slug(community.id, "moira-mactaggert")
    admin_services = AppServices(
        repo,
        DemoSeed(community, user, membership, character),
    )
    studio = admin_services.director_studio()
    titles = {warning.title for warning in studio.navigation_warnings}

    assert "Hidden parent with visible children" in titles
    assert "Visible child under hidden parent" in titles
    assert "Place outside the map" in titles
    assert "Community board in the location map" in titles
    assert "Private board in a public-facing section" in titles
    assert "Public board in Studio" in titles
    assert studio.navigation_attention_count == 1
    assert studio.navigation_warning_count >= 4
    assert studio.navigation_note_count >= 1


def test_director_studio_updates_board_taxonomy() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)
        announcements = repo.get_board_by_slug(community.id, "announcements")
        xavier = repo.get_board_by_slug(community.id, "xavier-institute")

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/structure",
                body=urlencode(
                    {
                        "intent": "board_taxonomy",
                        "board_id": announcements.id,
                        "board_kind": "sublocation",
                        "parent_board_id": xavier.id,
                        "navigation_order": 99,
                        "show_in_navigation": "on",
                    }
                ).encode(),
                headers=_FORM,
            )

            assert response.status == 302
            updated = repo.get_board(community.id, announcements.id)
            assert updated.board_kind == "sublocation"
            assert updated.parent_board_id == xavier.id
            assert updated.sidebar_section == "locations"
            assert updated.navigation_order == 99
            assert updated.show_in_navigation is True

            invalid = await client.post(
                "/studio/structure",
                body=urlencode(
                    {
                        "intent": "board_taxonomy",
                        "board_id": announcements.id,
                        "board_kind": "sublocation",
                        "parent_board_id": "",
                        "navigation_order": 99,
                        "show_in_navigation": "on",
                    }
                ).encode(),
                headers=_FORM,
            )

            assert invalid.status == 200
            assert "choose a parent location for sublocations" in invalid.text

    asyncio.run(run())


def test_director_studio_hides_board_from_navigation_without_hiding_route() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)
        announcements = repo.get_board_by_slug(community.id, "announcements")

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/structure",
                body=urlencode(
                    {
                        "intent": "board_taxonomy",
                        "board_id": announcements.id,
                        "board_kind": "community",
                        "parent_board_id": "",
                        "navigation_order": 40,
                    }
                ).encode(),
                headers=_FORM,
            )

            assert response.status == 302
            updated = repo.get_board(community.id, announcements.id)
            assert updated.show_in_navigation is False
            assert updated.navigation_order == 40
            assert updated.sidebar_section == "community"

            community_page = await client.get("/community")
            assert community_page.status == 200
            assert not re.search(
                r'<a class="[^"]*elbysodic-sidebar-link[^"]*"'
                r' href="/boards/announcements"',
                community_page.text,
            )

            board_page = await client.get("/boards/announcements")
            assert board_page.status == 200
            assert "Announcements" in board_page.text

    asyncio.run(run())


def test_studio_board_editor_updates_board_identity_and_navigation() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)
        xavier = repo.get_board_by_slug(community.id, "xavier-institute")

        async with TestClient(app) as client:
            editor = await client.get("/studio/boards/announcements")
            assert editor.status == 200
            assert "Board editor" in editor.text
            assert "Edit Announcements" in editor.text
            assert "Show in sidebar navigation" in editor.text
            assert "Sidebar placement" in editor.text
            assert "Image treatment" in editor.text
            assert "Image focal point" in editor.text
            assert "Overlay strength" in editor.text
            assert "Composer effect" in editor.text
            assert "Back to Studio" not in _page_content(editor.text)
            assert 'href="/boards/announcements"' in editor.text

            response = await client.post(
                "/studio/boards/announcements",
                body=urlencode(
                    {
                        "name": "Director Notices",
                        "board_kind": "sublocation",
                        "parent_board_id": xavier.id,
                        "tagline": "What changed, and why.",
                        "description": "Formal staff notices for the current continuity.",
                        "image_url": "https://example.test/notices.jpg",
                        "image_alt": "Notice board under red light",
                        "image_treatment": "background",
                        "image_focal_point": "top",
                        "image_overlay": "heavy",
                        "sort_order": 12,
                        "navigation_order": 7,
                        "sidebar_section": "locations",
                        "show_in_navigation": "on",
                        "is_private": "on",
                    }
                ).encode(),
                headers=_FORM,
            )
            board_page = await client.get("/boards/announcements")
            parent_page = await client.get("/boards/xavier-institute")
            editor_after = await client.get("/studio/boards/announcements")

            assert response.status == 302
            assert dict(response.headers)["location"] == "/studio/boards/announcements"
            updated = repo.get_board_by_slug(community.id, "announcements")
            assert updated.name == "Director Notices"
            assert updated.board_kind == "sublocation"
            assert updated.parent_board_id == xavier.id
            assert updated.tagline == "What changed, and why."
            assert updated.description == "Formal staff notices for the current continuity."
            assert updated.image_url == "https://example.test/notices.jpg"
            assert updated.image_alt == "Notice board under red light"
            assert updated.image_treatment == "background"
            assert updated.image_focal_point == "top"
            assert updated.image_overlay == "heavy"
            assert updated.sort_order == 12
            assert updated.navigation_order == 7
            assert updated.sidebar_section == "locations"
            assert updated.show_in_navigation is True
            assert updated.is_private is True
            assert board_page.status == 200
            assert 'src="https://example.test/notices.jpg"' in board_page.text
            assert 'alt="Notice board under red light"' in board_page.text
            assert "elbysodic-board-media-treatment--background" in board_page.text
            assert "elbysodic-board-media-focal--top" in board_page.text
            assert "elbysodic-board-media-overlay--heavy" in board_page.text
            assert "url('https://example.test/notices.jpg')" not in board_page.text
            assert parent_page.status == 200
            assert 'src="https://example.test/notices.jpg"' in parent_page.text
            assert 'alt="Notice board under red light"' in parent_page.text
            assert editor_after.status == 200
            assert 'src="https://example.test/notices.jpg"' in editor_after.text
            assert 'alt="Notice board under red light"' in editor_after.text
            assert 'option value="background" selected' in editor_after.text
            assert 'option value="top" selected' in editor_after.text
            assert 'option value="heavy" selected' in editor_after.text

    asyncio.run(run())


def test_studio_board_editor_requires_alt_text_for_board_media() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/boards/announcements",
                body=urlencode(
                    {
                        "name": "Announcements",
                        "board_kind": "community",
                        "parent_board_id": "",
                        "tagline": "Staff notes.",
                        "description": "Formal staff notices for the current continuity.",
                        "image_url": "https://example.test/notices.jpg",
                        "image_alt": "",
                        "image_treatment": "poster",
                        "image_focal_point": "center",
                        "image_overlay": "medium",
                        "sort_order": 10,
                        "navigation_order": 10,
                        "sidebar_section": "community",
                        "show_in_navigation": "on",
                    }
                ).encode(),
                headers=_FORM,
            )

        updated = repo.get_board_by_slug(community.id, "announcements")
        assert response.status == 200
        assert "board image alt text is required when an image URL is set" in response.text
        assert updated.image_url is None
        assert updated.image_alt == ""

    asyncio.run(run())


def test_studio_board_editor_rejects_unsupported_board_media_controls() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/boards/announcements",
                body=urlencode(
                    {
                        "name": "Announcements",
                        "board_kind": "community",
                        "parent_board_id": "",
                        "tagline": "Staff notes.",
                        "description": "Formal staff notices for the current continuity.",
                        "image_url": "https://example.test/notices.jpg",
                        "image_alt": "Notice board under red light",
                        "image_treatment": "raw-css",
                        "image_focal_point": "center",
                        "image_overlay": "medium",
                        "sort_order": 10,
                        "navigation_order": 10,
                        "sidebar_section": "community",
                        "show_in_navigation": "on",
                    }
                ).encode(),
                headers=_FORM,
            )

        updated = repo.get_board_by_slug(community.id, "announcements")
        assert response.status == 200
        assert "choose a supported board image treatment" in response.text
        assert updated.image_url is None
        assert updated.image_treatment == "poster"

    asyncio.run(run())


def test_studio_board_editor_validates_sublocation_parent() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/boards/announcements",
                body=urlencode(
                    {
                        "name": "Announcements",
                        "board_kind": "sublocation",
                        "parent_board_id": "",
                        "tagline": "",
                        "description": "Needs a parent.",
                        "image_url": "",
                        "image_alt": "",
                        "image_treatment": "poster",
                        "image_focal_point": "center",
                        "image_overlay": "medium",
                        "sort_order": 10,
                        "navigation_order": 10,
                        "sidebar_section": "locations",
                        "show_in_navigation": "on",
                    }
                ).encode(),
                headers=_FORM,
            )

            assert response.status == 200
            assert "choose a parent location for sublocations" in response.text
            assert "Board editor" in response.text

    asyncio.run(run())


def test_board_sidebar_section_controls_direct_board_sidebar_realm() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        applications = repo.get_board_by_slug(community.id, "applications")
        repo.update_board(
            community.id,
            applications.id,
            name=applications.name,
            description=applications.description,
            sort_order=applications.sort_order,
            parent_board_id=applications.parent_board_id,
            board_kind=applications.board_kind,
            sidebar_section="studio",
            tagline=applications.tagline,
            image_url=applications.image_url,
            image_alt=applications.image_alt,
            is_private=applications.is_private,
            navigation_order=applications.navigation_order,
            show_in_navigation=applications.show_in_navigation,
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            board_page = await client.get("/boards/applications")

            assert board_page.status == 200
            assert 'href="/studio/structure"' in board_page.text
            assert re.search(
                r'<a class="[^"]*elbysodic-sidebar-link[^"]*"'
                r'[^>]*href="/boards/applications"[^>]*aria-current="page"',
                board_page.text,
            )
            assert "Structure" in board_page.text

    asyncio.run(run())


def test_sidebar_modes_follow_major_product_paths() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            world = await client.get("/boards/xavier-institute")
            assert world.status == 200
            assert "World Map" not in world.text
            assert "Locations" in world.text
            assert "Sublocations" in world.text
            assert "Wanted board" not in world.text
            assert "data-elbysodic-sidebar-toggle" in world.text
            assert "chirpui-app-shell__sidebar-resize" in world.text
            assert "elbysodic-sidebar-destination" in world.text
            assert 'href="/locations"' in world.text
            assert 'href="/community"' in world.text
            assert 'class="chirpui-sidebar elbysodic-sidebar"' in world.text
            assert "elbysodic-mobile-nav-trigger" in world.text
            assert "elbysodic-mobile-shell-drawer" in world.text
            assert '<h2 class="chirpui-drawer__title">Navigation</h2>' in world.text
            assert "elbysodic-mobile-realm-nav" not in world.text

            locations = await client.get("/locations")
            assert locations.status == 200
            assert "Playable world map" in locations.text
            assert "A place-first scan of the realm" in locations.text
            assert "Major locations" in locations.text
            assert "/boards/xavier-institute" in locations.text
            assert "Location signals are tuned to the active face." not in locations.text
            assert "Community table" not in locations.text
            assert "Your location scenes are caught up for now." not in locations.text

            community = await client.get("/community")
            assert community.status == 200
            assert "elbysodic-world-hero--poster" in community.text
            assert "/elbysodic-static/seed-media/xmen-hero.svg" in community.text
            assert 'alt="Snow-lit academy and B-24 signal lines"' in community.text
            assert "Writer room and record" in community.text
            assert "Current Event: B-24 Winter" in community.text
            assert "Iceman is infected with B-24" in community.text
            assert "Community table" in community.text
            assert "Announcements" in community.text
            assert "Playable world map" not in community.text

            guidebook = await client.get("/world")
            assert guidebook.status == 200
            assert "Guidebook" in guidebook.text
            assert "Start Here" in guidebook.text
            assert "World Map" not in guidebook.text
            assert 'class="chirpui-sidebar__section-title">On World Home</span>' in guidebook.text
            assert 'class="chirpui-sidebar__section-title">Guidebook Index</span>' in guidebook.text
            assert 'class="chirpui-sidebar__section-title">Start Here</span>' not in guidebook.text
            assert 'class="chirpui-sidebar__section-title">Guides</span>' in guidebook.text
            assert 'class="chirpui-sidebar__section-title">Events</span>' in guidebook.text
            assert '<h2 class="chirpui-drawer__title">Navigation</h2>' in guidebook.text

            desk = await client.get("/desk")
            assert desk.status == 200
            assert "Writer Desk" in desk.text
            assert "Queue" in desk.text
            assert "Inbox" in desk.text
            assert "Roster" in desk.text
            assert "World Map" not in desk.text
            assert 'class="chirpui-sidebar__section-title">On Your Desk</span>' in desk.text
            assert '<h2 class="chirpui-drawer__title">Navigation</h2>' in desk.text

            studio = await client.get("/studio")
            assert studio.status == 200
            assert "Director Studio" in studio.text
            assert "Production" in studio.text
            assert "Studio rooms" in studio.text
            assert "World Map" not in studio.text
            assert 'class="chirpui-sidebar__section-title">In Studio</span>' not in studio.text
            assert 'class="chirpui-sidebar__section-title">Production</span>' not in studio.text
            assert 'aria-label="Studio"' not in studio.text
            assert '<h2 class="chirpui-drawer__title">Navigation</h2>' in studio.text

            wanted = await client.get("/wanted")
            assert wanted.status == 200
            assert "Casting" in wanted.text
            assert "Wanted board" not in wanted.text
            assert "Open Wants" in wanted.text
            assert "World Map" not in wanted.text
            assert 'class="chirpui-sidebar__section-title">In Wanted</span>' in wanted.text
            assert '<h2 class="chirpui-drawer__title">Navigation</h2>' in wanted.text

        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        staff_app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )
        async with TestClient(staff_app) as staff_client:
            staff_studio = await staff_client.get("/studio")

        assert staff_studio.status == 200
        assert 'aria-label="Studio"' in staff_studio.text
        assert 'class="chirpui-sidebar__section-title">In Studio</span>' in staff_studio.text
        assert 'class="chirpui-sidebar__section-title">Production</span>' not in staff_studio.text

    asyncio.run(run())


def test_sidebar_hidden_preference_is_cookie_backed_and_server_rendered() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            world = await client.get("/boards/xavier-institute")
            assert world.status == 200
            assert 'var cookieName = "elbysodic_sidebar_hidden_v2";' in world.text
            assert "elbysodic-theme.css?v=sticky-topbar-1" in world.text
            assert "elbysodic-shell.js?v=sidebar-rail-toggle-1" in world.text
            assert "elbysodic-composer.js?v=scene-context-inspector-1" in world.text
            assert 'id="elbysodic-sidebar-cookie-state"' not in world.text
            assert 'aria-label="Primary community rooms"' in world.text
            assert 'aria-label="Hide navigation"' in world.text
            assert 'aria-expanded="true"' in world.text

            hidden_world = await client.get(
                "/boards/xavier-institute",
                headers={"Cookie": "elbysodic_sidebar_hidden_v2=true"},
            )
            assert hidden_world.status == 200
            assert 'id="elbysodic-sidebar-cookie-state"' in hidden_world.text
            assert (
                "--chirpui-sidebar-width: var(--elbysodic-primary-rail-width)" in hidden_world.text
            )
            assert 'aria-label="Primary community rooms"' in hidden_world.text
            assert 'aria-label="Show navigation"' in hidden_world.text
            assert 'aria-expanded="false"' in hidden_world.text

            stylesheet_text = await _stylesheet_text_with_imports(client)
            assert "--elbysodic-primary-rail-width" in stylesheet_text
            assert ".chirpui-app-shell__topbar" in stylesheet_text
            assert "position: sticky;" in stylesheet_text
            assert '.elbysodic-primary-rail__link[aria-current="page"]' in stylesheet_text
            assert ".elbysodic-primary-rail__toggle" not in stylesheet_text
            assert ".elbysodic-app-shell--sidebar-hidden .chirpui-app-shell" in stylesheet_text
            assert ".elbysodic-app-shell--sidebar-hidden.chirpui-app-shell" in stylesheet_text
            assert "@media (min-width: 48.001rem) and (max-width: 72rem)" in stylesheet_text
            assert (
                "--chirpui-sidebar-width: var(--elbysodic-primary-rail-width);" in stylesheet_text
            )

            script = await client.get("/elbysodic-static/elbysodic-shell.js")
            assert script.status == 200
            assert 'const COOKIE_NAME = "elbysodic_sidebar_hidden_v2";' in script.text
            assert 'document.getElementById("elbysodic-sidebar-cookie-state")' in script.text
            assert 'querySelectorAll("[data-elbysodic-sidebar-toggle]")' in script.text
            assert "serverStyle.disabled = !hidden" in script.text
            assert "document.documentElement.classList.toggle(HIDDEN_CLASS, hidden)" in script.text
            assert 'window.localStorage.removeItem("chirpui-sidebar-collapsed")' in script.text
            assert 'form[method="post"], form[method="POST"]' in script.text
            assert "htmx:responseError" in script.text
            assert "resetSubmitGuard" in script.text

            composer = await client.get("/elbysodic-static/elbysodic-composer.js")
            assert composer.status == 200
            assert "data-elbysodic-sidebar-toggle" not in composer.text

    asyncio.run(run())


def test_world_map_sidebar_anchors_current_location_branch() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            parent = await client.get("/boards/new-york-city")
            assert parent.status == 200
            assert re.search(
                r'class="[^"]*elbysodic-sidebar-tree__link--active[^"]*"'
                r'[^>]*href="/boards/new-york-city"',
                parent.text,
            )
            assert "/boards/frozen-midtown" in parent.text

            child = await client.get("/boards/frozen-midtown")
            assert child.status == 200
            assert re.search(
                r'class="[^"]*elbysodic-sidebar-tree__link--branch[^"]*"'
                r'[^>]*href="/boards/new-york-city"',
                child.text,
            )
            assert re.search(
                r'class="[^"]*elbysodic-sidebar-tree__link--active[^"]*"'
                r'[^>]*href="/boards/frozen-midtown"',
                child.text,
            )
            frozen_link = re.search(
                r'<a class="[^"]*elbysodic-sidebar-tree__link[^"]*"'
                r'[^>]*href="/boards/frozen-midtown"[^>]*>',
                child.text,
            )
            assert frozen_link is not None
            assert "hx-target" not in frozen_link.group(0)
            assert 'aria-label="Place path"' in child.text

    asyncio.run(run())


def test_board_pages_render_location_stage_and_place_tiles() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            academy = await client.get("/boards/xavier-institute")

            assert academy.status == 200
            assert "elbysodic-board-stage" in academy.text
            assert "elbysodic-board-media--xavier-institute" in academy.text
            assert "elbysodic-location-compass" in academy.text
            assert "Life at Xavier Institute" in academy.text
            assert "Relevant to the active face" in academy.text
            assert "Scenes here" in academy.text
            assert "No direct scenes yet" in academy.text
            assert 'aria-label="Med Bay · Relevant to active face"' in academy.text
            assert (
                'class="chirpui-tooltip chirpui-tooltip--left '
                'elbysodic-board-poster__face-signal-hint"' in academy.text
            )
            assert (
                'data-tooltip="Relevant to the active face: this location '
                'shares one of their world lenses."' in academy.text
            )
            assert "Total" in academy.text
            assert "The first scene opened here will appear below." in academy.text
            assert "elbysodic-director-context" not in academy.text
            assert "Doors" in academy.text
            assert "Nearby" in academy.text
            assert 'id="sublocations"' in academy.text
            assert 'id="nearby"' in academy.text
            assert "Choose a door inside Xavier Institute" in academy.text
            assert "Xavier Institute scenes" in academy.text
            assert "No scenes have opened directly here yet." in academy.text
            assert "Start scene here" in academy.text
            assert "Sublocations" in academy.text
            assert "elbysodic-board-poster--tile" in academy.text

            midtown = await client.get("/boards/frozen-midtown")

            assert midtown.status == 200
            assert "elbysodic-board-media--frozen-midtown" in midtown.text
            assert "Nearby" in midtown.text
            assert "New York City" in midtown.text
            assert "/boards/transit-tunnels" in midtown.text

    asyncio.run(run())


def test_quiet_location_page_keeps_actions_visible_without_empty_door_sections() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = services.seed.community
        repo.create_board(
            community.id,
            "quiet-courtyard",
            "Quiet Courtyard",
            "A low-pressure place for slower scenes and first meetings.",
            board_kind="location",
            tagline="A softer corner of the grounds.",
            sort_order=999,
        )
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            page = await client.get("/boards/quiet-courtyard")

        assert page.status == 200
        assert "elbysodic-location-compass" in page.text
        assert "Open for scenes" in page.text
        assert "No direct scenes yet" in page.text
        assert "The first scene opened here will appear below." in page.text
        assert 'href="#sublocations"' not in page.text
        assert 'id="sublocations"' not in page.text
        assert "No scenes have opened directly here yet." in page.text
        assert "Start scene here" in page.text

    asyncio.run(run())


def test_community_board_pages_use_community_language_and_sidebar_state() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            announcements = await client.get("/boards/announcements")

            assert announcements.status == 200
            assert "Community board" in announcements.text
            assert "Threads here" in announcements.text
            assert "Direct threads in this board." in announcements.text
            assert "Location hub" not in announcements.text
            assert "Other major locations" not in announcements.text
            assert "Current event in this location" not in announcements.text
            assert "World Map" not in announcements.text
            assert re.search(
                r'<a class="[^"]*elbysodic-sidebar-destination[^"]*"'
                r'[^>]*href="/community"[^>]*aria-current="page"',
                announcements.text,
            )

    asyncio.run(run())


def test_topbar_marks_active_community_mode() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            world = await client.get("/boards/xavier-institute")
            assert world.status == 200
            assert re.search(
                r'<a class="[^"]*elbysodic-primary-rail__link[^"]*"'
                r'\s+href="/locations"[^>]*aria-label="Locations"[^>]*aria-current="page"',
                world.text,
            )

            guidebook = await client.get("/world")
            assert guidebook.status == 200
            assert not re.search(
                r'<a class="[^"]*elbysodic-primary-rail__link[^"]*"'
                r'\s+href="/locations"[^>]*aria-label="Locations"[^>]*aria-current="page"',
                guidebook.text,
            )
            assert re.search(
                r'<a class="[^"]*elbysodic-primary-rail__link[^"]*"'
                r'\s+href="/"[^>]*aria-label="World Home"[^>]*aria-current="page"',
                guidebook.text,
            )

            desk = await client.get("/desk")
            assert desk.status == 200
            assert re.search(
                r'<a class="[^"]*elbysodic-primary-rail__link[^"]*"'
                r'\s+href="/desk"[^>]*aria-label="Desk"[^>]*aria-current="page"',
                desk.text,
            )

            wanted = await client.get("/wanted")
            assert wanted.status == 200
            assert re.search(
                r'<a class="[^"]*elbysodic-primary-rail__link[^"]*"'
                r'\s+href="/wanted"[^>]*aria-label="Wanted"[^>]*aria-current="page"',
                wanted.text,
            )

            claims = await client.get("/claims?status=reserved&q=magneto")
            assert claims.status == 200
            assert re.search(
                r'<a class="[^"]*elbysodic-primary-rail__link[^"]*"'
                r'\s+href="/wanted"[^>]*aria-label="Wanted"[^>]*aria-current="page"',
                claims.text,
            )
            assert re.search(
                r'<a class="[^"]*chirpui-sidebar__link[^"]*"'
                r'\s+href="/claims"[^>]*aria-current="page"',
                claims.text,
            )

            studio = await client.get("/studio/content")
            assert studio.status == 200
            assert not re.search(
                r'<a class="[^"]*elbysodic-primary-rail__link[^"]*"'
                r'\s+href="/studio"[^>]*aria-label="Studio"[^>]*aria-current="page"',
                studio.text,
            )

            notifications = await client.get("/notifications")
            assert notifications.status == 200
            assert re.search(
                r'<a class="[^"]*elbysodic-primary-rail__link[^"]*"'
                r'\s+href="/desk"[^>]*aria-label="Desk"[^>]*aria-current="page"',
                notifications.text,
            )
            assert re.search(
                r'class="[^"]*elbysodic-identity-menu__notification-link--active[^"]*"'
                r'[^>]*href="/notifications"',
                notifications.text,
            )

        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        staff_app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )
        async with TestClient(staff_app) as staff_client:
            staff_studio = await staff_client.get("/studio")

        assert staff_studio.status == 200
        assert re.search(
            r'<a class="[^"]*elbysodic-primary-rail__link[^"]*"'
            r'\s+href="/studio"[^>]*aria-label="Studio"[^>]*aria-current="page"',
            staff_studio.text,
        )

    asyncio.run(run())


def test_parent_board_summaries_roll_up_child_activity_but_thread_lists_stay_direct() -> None:
    connection = connect(check_same_thread=False)
    create_schema(connection)
    repo = ForumRepository(connection)
    community = repo.seed_default_community("Hierarchy Test")
    role = repo.create_role(community.id, "member", "Member")
    user = repo.create_user("writer@example.com", "hash")
    membership = repo.create_membership(community.id, user.id, role.id, "writer", "Writer")
    character = repo.create_character(
        community.id,
        membership.id,
        "active-face",
        "Active Face",
        make_default=True,
    )
    parent = repo.create_board(
        community.id,
        "academy",
        "Academy",
        description="A school under emergency power.",
        board_kind="location",
        image_url="https://example.test/academy.jpg",
        image_alt="Academy under emergency lights",
    )
    child = repo.create_board(
        community.id,
        "med-bay",
        "Med Bay",
        parent_board_id=parent.id,
        board_kind="sublocation",
    )
    parent_thread = repo.create_thread(
        community.id,
        parent.id,
        character.id,
        "hallway-scene",
        "Hallway Scene",
    )
    repo.create_post(community.id, parent_thread.id, character.id, "A direct academy scene.")
    child_thread = repo.create_thread(
        community.id,
        child.id,
        character.id,
        "med-bay-scene",
        "Med Bay Scene",
    )
    repo.create_post(community.id, child_thread.id, character.id, "A child-location scene.")
    services = AppServices(
        repo,
        DemoSeed(
            community=community,
            user=user,
            membership=repo.get_membership(community.id, membership.id),
            default_character=character,
        ),
    )

    summaries = {summary.board.slug: summary for summary in services.list_boards()}
    _, direct_threads = services.board_threads("academy")

    assert summaries["academy"].thread_count == 2
    assert summaries["academy"].post_count == 2
    assert summaries["academy"].has_children is True
    assert summaries["academy"].latest_thread == child_thread
    assert [item.thread.title for item in direct_threads] == ["Hallway Scene"]


def test_scene_context_contract_wraps_thread_location_and_grounding_state() -> None:
    connection = connect(check_same_thread=False)
    create_schema(connection)
    repo = ForumRepository(connection)
    community = repo.seed_default_community("Scene Context Test")
    role = repo.create_role(community.id, "member", "Member")
    user = repo.create_user("writer@example.com", "hash")
    membership = repo.create_membership(community.id, user.id, role.id, "writer", "Writer")
    character = repo.create_character(
        community.id,
        membership.id,
        "active-face",
        "Active Face",
        make_default=True,
    )
    parent = repo.create_board(
        community.id,
        "academy",
        "Academy",
        description="A school under emergency power.",
        board_kind="location",
        image_url="https://example.test/academy.jpg",
        image_alt="Academy under emergency lights",
    )
    child = repo.create_board(
        community.id,
        "med-bay",
        "Med Bay",
        parent_board_id=parent.id,
        board_kind="sublocation",
    )
    current = repo.create_thread(
        community.id,
        child.id,
        character.id,
        "after-the-blackout",
        "After the Blackout",
        summary="Emergency power changes the room.",
    )
    repo.create_post(community.id, current.id, character.id, "The lights came back wrong.")
    nearby = repo.create_thread(
        community.id,
        child.id,
        character.id,
        "breakfast-before-debrief",
        "Breakfast Before Debrief",
    )
    repo.create_post(community.id, nearby.id, character.id, "Coffee waits by the door.")
    services = AppServices(
        repo,
        DemoSeed(
            community=community,
            user=user,
            membership=repo.get_membership(community.id, membership.id),
            default_character=character,
        ),
    )

    scene_context = services.read_scene_context("med-bay", "after-the-blackout")

    assert scene_context.thread_view.thread == current
    assert scene_context.parent_board == parent
    assert scene_context.current_event is None
    assert scene_context.location_lane.board == child
    assert scene_context.location_lane.parent_board == parent
    assert scene_context.location_lane.placement_path == (parent, child)
    assert scene_context.location_lane.place_headline_board == parent
    assert scene_context.location_lane.placement_trail_boards == (child,)
    assert scene_context.location_lane.sidebar_section_label == "Locations"
    assert scene_context.location_lane.current_item is not None
    assert scene_context.location_lane.current_item.summary.thread == current
    assert not scene_context.location_lane.attention_items
    assert not scene_context.location_lane.active_items
    assert {item.summary.thread.title for item in scene_context.location_lane.items} == {
        "Breakfast Before Debrief",
    }
    assert scene_context.location_lane.items[0].waiting_on_others
    assert scene_context.grounding.board == child
    assert scene_context.grounding.parent_board == parent
    assert scene_context.grounding.participants == [character]
    assert scene_context.grounding.visibility_label == "member-visible scene"
    assert scene_context.grounding.current_event is None
    assert scene_context.media_band is not None
    assert scene_context.media_band.source_board == parent
    assert scene_context.media_band.source_label == "Inherited location media"
    assert scene_context.media_band.heading == "Med Bay scene atmosphere"
    assert scene_context.media_band.summary == "A school under emergency power."
    assert scene_context.media_band.is_inherited is True
    assert scene_context.writer_activity is not None
    assert scene_context.writer_activity.selected_character == character
    assert not scene_context.writer_activity.needs_reply
    assert [item.thread.title for item in scene_context.writer_activity.waiting_on_others] == [
        "Breakfast Before Debrief",
    ]
    assert scene_context.writer_activity.visible_count == 1
    assert repo.get_thread_read_at(community.id, current.id, membership.id) is not None


def test_thread_page_renders_inherited_scene_media_as_hero_background() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")

        content = _page_content(page.text)
        assert page.status == 200
        assert "elbysodic-scene-media-band" not in content
        assert "elbysodic-thread-stage--with-media" in content
        assert "elbysodic-thread-stage__media" in content
        assert "Sentinel drill after midnight" in content
        assert "Inherited location media" not in content
        assert "Danger Room scene atmosphere" not in content
        assert "/elbysodic-static/seed-media/locations/xmen-xavier-institute.svg" in content
        assert 'alt="Snowbound academy windows under B-24 signal arcs"' in content
        assert 'aria-label="Open scene actions and context"' in content

    asyncio.run(run())


def test_scene_media_band_respects_text_first_location_media() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        board = repo.get_board_by_slug(community.id, "xavier-institute")
        repo.update_board(
            community.id,
            board.id,
            name=board.name,
            description=board.description,
            sort_order=board.sort_order,
            parent_board_id=board.parent_board_id,
            board_kind=board.board_kind,
            sidebar_section=board.sidebar_section,
            tagline=board.tagline,
            image_url=board.image_url,
            image_alt=board.image_alt,
            image_treatment="text",
            image_focal_point=board.image_focal_point,
            image_overlay=board.image_overlay,
            is_private=board.is_private,
            navigation_order=board.navigation_order,
            show_in_navigation=board.show_in_navigation,
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")

        content = _page_content(page.text)
        assert page.status == 200
        assert "elbysodic-scene-media-band" not in content
        assert "elbysodic-thread-stage--with-media" not in content
        assert "elbysodic-thread-stage__media" not in content

    asyncio.run(run())


def test_thread_page_renders_location_scene_lane() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")

        content = _page_content(page.text)
        assert page.status == 200
        assert "elbysodic-thread-context-sidebar" in page.text
        sidebar_match = re.search(
            r'<aside class="elbysodic-thread-context-sidebar"[\s\S]*?</aside>',
            page.text,
        )
        assert sidebar_match is not None
        sidebar_content = sidebar_match.group(0)
        assert "elbysodic-scenes-here-drawer" in content
        assert "Scenes here" in content
        assert "Danger Room" in content
        assert "Xavier Institute" in content
        assert "Sentinel drill after midnight" not in sidebar_content
        assert "Moonlight skirmish" not in sidebar_content
        assert "No other soft beats queued in this lane." in sidebar_content
        assert "Toolbar QA Works" not in sidebar_content
        assert "Fastball special practice" not in content
        assert 'aria-current="page"' not in sidebar_content
        assert "current scene" not in sidebar_content
        assert "watching" in content

    asyncio.run(run())


def test_boosted_thread_navigation_updates_contextual_sidebar_oob() -> None:
    async def run() -> None:
        app = _app()
        headers = {
            "HX-Request": "true",
            "HX-Boosted": "true",
            "HX-Target": "main",
        }

        async with TestClient(app) as client:
            board_page = await client.get("/boards/danger-room", headers=headers)
            thread_page = await client.get(
                "/boards/danger-room/threads/sentinel-drill",
                headers=headers,
            )

        assert board_page.status == 200
        board_sidebar = _oob_outer_block(board_page.text, "elbysodic-shell-sidebar-content")
        assert "elbysodic-thread-context-sidebar" not in board_sidebar
        assert "Locations" in board_sidebar

        assert thread_page.status == 200
        thread_sidebar = _oob_outer_block(thread_page.text, "elbysodic-shell-sidebar-content")
        assert "elbysodic-thread-context-sidebar" in thread_sidebar
        assert "Open scenes" in thread_sidebar
        assert "Sentinel drill after midnight" not in thread_sidebar
        assert "Moonlight skirmish" not in thread_sidebar
        assert "No other soft beats queued in this lane." in thread_sidebar
        assert "Fastball special practice" not in thread_sidebar
        thread_primary_content = _page_content(thread_page.text).split(
            '<div id="elbysodic-shell-sidebar-content"',
            maxsplit=1,
        )[0]
        assert "elbysodic-thread-context-sidebar" not in thread_primary_content

    asyncio.run(run())


def test_thread_page_renders_scene_grounding_for_owner() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")

        content = _page_content(page.text)
        assert page.status == 200
        assert "elbysodic-scene-context-layout__grounding" in content
        assert "elbysodic-scene-context-drawer" in content
        assert "Scene context" in content
        assert "Grounding" in content
        assert "Danger Room" in content
        assert "Inside" in content
        assert "Xavier Institute" in content
        assert "Present faces" in content
        assert "Rogue is waiting" in content
        assert "Status" in content
        assert "Active" in content
        assert "Mode" in content
        assert "Posting order" in content
        assert "Visibility" in content
        assert "public preview scene" in content
        assert "The first four posts are visible to people browsing while signed out." in content
        assert "Linked story objects" in content
        assert "Staff controls" not in content

    asyncio.run(run())


def test_scene_grounding_renders_visible_plotting_room_story_link() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        linked_room = _link_seed_plotting_room_to_sentinel(services)
        scene_context = services.read_scene_context("danger-room", "sentinel-drill")
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")

        content = _page_content(page.text)
        assert scene_context.grounding.story_links
        assert scene_context.grounding.story_links[0].title == linked_room.title
        assert scene_context.grounding.story_links[0].href == f"/plotting/{linked_room.id}"
        assert page.status == 200
        assert "Linked story objects" in content
        assert "Reviewed wanted hooks, plotters, and canon links will surface here" not in content
        assert "Sentinel drill tactics table" in content
        assert "Plan Rogue&#39;s next danger room beat before posting." in content
        assert f'href="/plotting/{linked_room.id}"' in content
        assert "Threaded" in content
        assert "Wanted hook source" in content
        assert "Planning faces" in content
        assert "Rogue" in content

    asyncio.run(run())


def test_scene_grounding_hides_plotting_room_from_non_participants() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        _link_seed_plotting_room_to_sentinel(services)
        outsider_services, _character_id = _outsider_services(
            services,
            prefix="scene-plotting-outsider",
        )
        outsider_context = outsider_services.read_scene_context("danger-room", "sentinel-drill")
        app = create_app(debug=False, services=outsider_services)

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")

        content = _page_content(page.text)
        assert not outsider_context.grounding.story_links
        assert page.status == 200
        assert "Linked story objects" in content
        assert "Sentinel drill tactics table" not in content
        assert "Plan Rogue&#39;s next danger room beat before posting." not in content
        assert "Reviewed wanted hooks, plotters, and canon links will surface here" in content

    asyncio.run(run())


def test_scene_context_shell_preserves_reader_landmarks_and_controls() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")
            stylesheet_text = await _stylesheet_text_with_imports(client)

        assert page.status == 200
        html = page.text
        assert 'aria-label="Scenes in this location"' in html
        assert 'aria-label="Scene context"' in html or 'aria-label="Scene context panel"' in html
        assert "elbysodic-scenes-here-trigger" in html
        assert "elbysodic-scene-context-trigger" in html
        assert 'id="elbysodic-scenes-here-drawer"' in html
        assert 'id="elbysodic-scene-context-drawer"' in html
        assert "Scenes here" in html
        assert "Scene context" in html
        assert "Needs your reply" in html
        assert "Grounding context" in html
        assert "What needs you" in html
        assert 'id="elbysodic-writer-activity-drawer"' in html
        assert "After this scene" in html
        assert "Continue through your Desk queue" in html
        assert "elbysodic-thread-attention-nav__link--scenes" in html
        assert 'aria-label="Open scene actions and context"' in html
        assert "elbysodic-scene-actions-menu" in html
        assert "elbysodic-scene-reply-anchor" not in html
        assert "Take turns respecting the queued beat" not in html
        assert "faces are tagged on the cast line" not in html
        assert "Mark caught up" in html
        assert "Since you last read" in html
        assert "elbysodic-scene-reader-breadcrumbs" in html
        assert "elbysodic-scene-context-inspector-toggle" in html
        assert "In Locations" in html
        assert "Place hierarchy for this lane" in html
        assert 'href="/boards/xavier-institute"' in html
        assert 'href="/boards/danger-room"' in html
        assert "Next unread" in html
        assert 'for="reply-character"' in html
        assert "elbysodic-scene-composer-face-select" in html
        assert re.search(r'<span>Reply as</span>\s*<select[^>]+id="reply-character"', html)
        assert "Drafts autosave locally in this community." in html
        assert "Write Rogue's reply..." in html
        assert "elbysodic-scene-composer-tools" in html
        assert html.index('id="reply-composer"') < html.index("After this scene")
        assert 'name="intent" value="mark_caught_up"' in html
        assert 'name="intent" value="reply"' in html
        assert 'name="idempotency_key"' in html
        assert 'hx-boost="false"' in html
        assert (
            ".elbysodic-scene-context-layout .elbysodic-scene-context-layout__grounding"
            in stylesheet_text
        )
        assert ".elbysodic-thread-context-sidebar .elbysodic-scene-lane" in stylesheet_text
        assert "grid-template-rows: auto minmax(0, 1fr);" in stylesheet_text
        assert "max-height: none;" in stylesheet_text
        assert ".elbysodic-thread-context-sidebar .elbysodic-scene-lane-row" in stylesheet_text
        assert "padding: 0.48rem 0.5rem;" in stylesheet_text
        assert ".elbysodic-scene-lane__path-chip:hover" in stylesheet_text
        assert "text-decoration: none;" in stylesheet_text
        assert "position: fixed;" in stylesheet_text
        assert "transform: translateX(calc(100% + 1rem));" in stylesheet_text
        assert "grid-template-columns: minmax(0, 1fr) minmax(17rem, 23rem);" not in stylesheet_text

    asyncio.run(run())


def test_scene_management_controls_live_in_grounding_tray() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")

        assert page.status == 200
        content = _page_content(page.text)
        reader_before_grounding = content.split(
            'class="elbysodic-scene-context-layout__grounding',
            maxsplit=1,
        )[0]
        assert "Scene management" not in reader_before_grounding
        assert "Reader actions" not in reader_before_grounding
        assert 'id="scene-management"' not in content
        assert 'id="scene-context-docked-scene-management"' in content
        assert 'id="scene-context-drawer-scene-management"' in content
        assert "elbysodic-scene-grounding__section--reader-actions" in content
        assert "elbysodic-scene-grounding__section--operations" in content
        assert re.search(r"(?:Watch|Unwatch) thread", content)
        assert "Read latest" in content
        assert "Tag cast" in content

    asyncio.run(run())


def test_thread_page_renders_member_scoped_scene_writer_activity_drawer() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        other_community = repo.create_community("other-activity-realm", "Other Activity Realm")
        other_role = repo.create_role(other_community.id, "member", "Member")
        other_membership = repo.create_membership(
            other_community.id,
            services.seed.user.id,
            other_role.id,
            "other-activity",
            "Other Activity",
        )
        other_face = repo.create_character(
            other_community.id,
            other_membership.id,
            "other-activity-face",
            "Other Activity Face",
            make_default=True,
        )
        other_writer = repo.create_user("other-activity-writer@example.com", "hash")
        other_writer_membership = repo.create_membership(
            other_community.id,
            other_writer.id,
            other_role.id,
            "other-activity-writer",
            "Other Activity Writer",
        )
        other_writer_face = repo.create_character(
            other_community.id,
            other_writer_membership.id,
            "other-activity-counterpart",
            "Other Activity Counterpart",
        )
        other_board = repo.create_board(
            other_community.id,
            "other-activity-board",
            "Other Activity Board",
        )
        other_thread = repo.create_thread(
            other_community.id,
            other_board.id,
            other_face.id,
            "other-activity-obligation",
            "Other Realm Obligation",
        )
        repo.create_post(other_community.id, other_thread.id, other_face.id, "Cross-realm opener.")
        repo.create_post(
            other_community.id,
            other_thread.id,
            other_writer_face.id,
            "This other realm reply should stay out of this scene drawer.",
        )
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")

        content = _page_content(page.text)
        assert page.status == 200
        assert "elbysodic-writer-activity-drawer" in content
        assert "What needs you" in content
        assert "Writing as Rogue" in content
        assert "Current scene" in content
        assert "Watching" in content
        assert "New replies" in content or "Caught up" in content
        assert "Needs reply" in content
        assert "Waiting" in content
        assert "Open Desk queue" in content
        assert "/my/threads" in content
        assert "Other Realm Obligation" not in content
        assert "This other realm reply should stay out of this scene drawer." not in content
        assert "Reserve expiring" not in content
        assert "Claim reviewed" not in content

    asyncio.run(run())


def test_scene_writer_activity_drawer_hides_for_faceless_members() -> None:
    async def run() -> None:
        services = _faceless_services(create_services(path=":memory:"), prefix="scene-activity")
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")

        content = _page_content(page.text)
        assert page.status == 200
        assert "Create a character first" in content
        assert "elbysodic-writer-activity-drawer" not in content
        assert "What needs you" not in content
        assert "Writing as" not in content

    asyncio.run(run())


def test_scene_reader_since_last_read_divider_when_membership_reads_behind_latest_post() -> None:
    async def run() -> None:
        connection = connect(check_same_thread=False)
        create_schema(connection)
        repo = ForumRepository(connection)
        community = repo.seed_default_community("Unread Divider Smoke")
        role = repo.create_role(community.id, "member", "Member")
        reader_user = repo.create_user("reader-divider@example.com", "hash")
        reader_membership = repo.create_membership(
            community.id,
            reader_user.id,
            role.id,
            "reader-divider",
            "Reader Divider",
        )
        reader_face = repo.create_character(
            community.id,
            reader_membership.id,
            "reader-divider-face",
            "Reader Divider Face",
            make_default=True,
        )
        writer_user = repo.create_user("writer-divider@example.com", "hash")
        writer_membership = repo.create_membership(
            community.id,
            writer_user.id,
            role.id,
            "writer-divider",
            "Writer Divider",
        )
        writer_face = repo.create_character(
            community.id,
            writer_membership.id,
            "writer-divider-face",
            "Writer Divider Face",
        )
        board = repo.create_board(
            community.id,
            "divider-field",
            "Divider Field",
            board_kind="location",
        )
        thread = repo.create_thread(
            community.id,
            board.id,
            writer_face.id,
            "divider-thread",
            "Divider Scene",
            status="active",
        )
        _p1 = repo.create_post(community.id, thread.id, writer_face.id, "first beat")
        _p2 = repo.create_post(community.id, thread.id, writer_face.id, "second beat")
        _p3 = repo.create_post(
            community.id,
            thread.id,
            writer_face.id,
            "third beat awaiting reader",
        )
        repo.mark_thread_read(
            community.id,
            thread.id,
            reader_membership.id,
            read_at="1999-01-01T00:00:00+00:00",
        )
        reader_membership_row = repo.get_membership(community.id, reader_membership.id)
        services = AppServices(
            repo,
            DemoSeed(
                community=community,
                user=reader_user,
                membership=reader_membership_row,
                default_character=reader_face,
            ),
        )
        app = create_app(debug=False, services=services)
        async with TestClient(app) as client:
            page = await client.get("/boards/divider-field/threads/divider-thread")
        content = _page_content(page.text)
        assert page.status == 200
        assert "Since you last read" in content

    asyncio.run(run())


def test_scene_grounding_for_ordinary_member_hides_staff_management_copy() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        outsider_services, _character_id = _outsider_services(services)
        app = create_app(debug=False, services=outsider_services)

        async with TestClient(app) as client:
            page = await client.get("/c/x-men-apocalypse/boards/danger-room/threads/sentinel-drill")

        content = _page_content(page.text)
        assert page.status == 200
        assert "Scene context" in content
        assert "Reading as Outsider Face" in content
        assert "public preview scene" in content
        assert "staff-manageable member-visible scene" not in content
        assert "Staff controls" not in content
        assert "Scene management" not in content

    asyncio.run(run())


def test_scene_grounding_for_staff_uses_service_owned_visibility_copy() -> None:
    async def run() -> None:
        connection = connect(check_same_thread=False)
        create_schema(connection)
        repo = ForumRepository(connection)
        community = repo.seed_default_community("Grounding Staff Test")
        staff_role = repo.create_role(community.id, "staff", "Staff", is_admin=True)
        member_role = repo.create_role(community.id, "member", "Member")
        staff_user = repo.create_user("staff-grounding@example.com", "hash")
        staff_membership = repo.create_membership(
            community.id,
            staff_user.id,
            staff_role.id,
            "staff-grounding",
            "Staff Grounding",
        )
        staff_character = repo.create_character(
            community.id,
            staff_membership.id,
            "staff-face",
            "Staff Face",
            make_default=True,
        )
        writer_user = repo.create_user("writer-grounding@example.com", "hash")
        writer_membership = repo.create_membership(
            community.id,
            writer_user.id,
            member_role.id,
            "writer-grounding",
            "Writer Grounding",
        )
        writer_character = repo.create_character(
            community.id,
            writer_membership.id,
            "writer-face",
            "Writer Face",
        )
        board = repo.create_board(
            community.id,
            "staff-visible-location",
            "Staff Visible Location",
            board_kind="location",
        )
        thread = repo.create_thread(
            community.id,
            board.id,
            writer_character.id,
            "staff-visible-scene",
            "Staff Visible Scene",
        )
        repo.create_post(community.id, thread.id, writer_character.id, "Staff can read this.")
        services = AppServices(
            repo,
            DemoSeed(
                community=community,
                user=staff_user,
                membership=repo.get_membership(community.id, staff_membership.id),
                default_character=staff_character,
            ),
        )
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            page = await client.get("/boards/staff-visible-location/threads/staff-visible-scene")

        content = _page_content(page.text)
        assert page.status == 200
        assert "Scene context" in content
        assert "staff-manageable member-visible scene" in content
        assert "Members can read this scene; staff controls remain in management panels." in content
        assert "Staff controls" in content

    asyncio.run(run())


def test_scene_lane_keeps_private_board_threads_out_of_visible_scene_context() -> None:
    async def run() -> None:
        connection = connect(check_same_thread=False)
        create_schema(connection)
        repo = ForumRepository(connection)
        community = repo.seed_default_community("Scene Lane Privacy Test")
        role = repo.create_role(community.id, "member", "Member")
        user = repo.create_user("reader@example.com", "hash")
        membership = repo.create_membership(community.id, user.id, role.id, "reader", "Reader")
        character = repo.create_character(
            community.id,
            membership.id,
            "reader-face",
            "Reader Face",
            make_default=True,
        )
        public_board = repo.create_board(
            community.id,
            "public-med-bay",
            "Public Med Bay",
            board_kind="location",
        )
        private_board = repo.create_board(
            community.id,
            "staff-infirmary",
            "Staff Infirmary",
            board_kind="location",
            is_private=True,
        )
        public_thread = repo.create_thread(
            community.id,
            public_board.id,
            character.id,
            "visible-checkup",
            "Visible Checkup",
        )
        repo.create_post(community.id, public_thread.id, character.id, "A public scene opens.")
        private_thread = repo.create_thread(
            community.id,
            private_board.id,
            character.id,
            "private-director-notes",
            "Private Director Notes",
        )
        repo.create_post(
            community.id,
            private_thread.id,
            character.id,
            "Private scene context should not leak.",
        )
        services = AppServices(
            repo,
            DemoSeed(
                community=community,
                user=user,
                membership=repo.get_membership(community.id, membership.id),
                default_character=character,
            ),
        )
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            page = await client.get("/boards/public-med-bay/threads/visible-checkup")
            private_page = await client.get(
                "/boards/staff-infirmary/threads/private-director-notes"
            )

        content = _page_content(page.text)
        assert page.status == 200
        assert "Visible Checkup" in content
        assert "Private Director Notes" not in content
        assert "Staff Infirmary" not in content
        assert "Private scene context should not leak." not in content
        assert "Scene context" in content
        assert private_page.status == 403

    asyncio.run(run())


def test_scene_lane_watch_state_uses_batched_lookup() -> None:
    services = _scale_board_services(thread_count=30)
    board = services.repo.get_board_by_slug(services.seed.community.id, "scale-yard")
    for thread in services.repo.list_threads(services.seed.community.id, board.id)[::2]:
        services.repo.watch_thread(
            services.seed.community.id,
            thread.id,
            services.seed.membership.id,
        )

    with trace_sql(services.repo.connection) as trace:
        scene_context = services.read_scene_context("scale-yard", "scale-thread-0")

    counts = trace.normalized_counts()
    watched_batch_queries = [
        count
        for sql, count in counts.items()
        if "FROM thread_watches" in sql and "json_each" in sql
    ]
    watched_scalar_queries = [
        count
        for sql, count in counts.items()
        if "FROM thread_watches" in sql and "json_each" not in sql
    ]
    post_batch_queries = [
        count for sql, count in counts.items() if "FROM posts" in sql and "json_each" in sql
    ]
    post_scalar_queries = [
        count for sql, count in counts.items() if "FROM posts" in sql and "json_each" not in sql
    ]
    assert len(scene_context.location_lane.items) == 29
    assert scene_context.location_lane.current_item is not None
    assert scene_context.location_lane.current_item.summary.thread.slug == "scale-thread-0"
    assert scene_context.writer_activity is not None
    assert any(item.is_watched for item in scene_context.location_lane.items)
    assert sum(watched_batch_queries) == 1
    assert sum(watched_scalar_queries) == 1
    assert sum(post_batch_queries) <= 3
    assert sum(post_scalar_queries) <= 2


def test_discovery_defaults_to_active_face_lens_and_filters_facets() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            discover = await client.get("/discover")
            assert discover.status == 200
            assert "Plot discovery" in discover.text
            assert "chirpui-facet-chip" in discover.text
            assert "Prioritizing active-face matches" in discover.text
            assert "Mutant" in discover.text
            assert "X-Men" in discover.text
            assert "Academy" in discover.text
            assert "Rogue" in discover.text
            assert "Bolivar Trask" not in discover.text

            human_un = await client.get("/discover?facets=human,united-nations")
            assert human_un.status == 200
            assert "Bolivar Trask" in human_un.text
            assert "Moira MacTaggert" in human_un.text
            assert 'href="/characters/rogue">Rogue' not in human_un.text

    asyncio.run(run())


def test_world_materials_render_pillars_events_and_application_guides() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            world = await client.get("/world")
            assert world.status == 200
            assert "World guide" in world.text
            assert "Premise" in world.text
            assert "Application Guide" in world.text
            assert "Current Event: B-24 Winter" in world.text
            assert "Guidebook pulse" in world.text
            assert 'href="/world/premise"' in world.text
            assert 'href="/world/b-24-winter"' in world.text
            assert "United Nations" in world.text
            assert "elbysodic-material-card--premise" in world.text
            assert "elbysodic-material-card--application" in world.text
            assert "elbysodic-current-event-card--event" in world.text

            event = await client.get("/world/b-24-winter")
            assert event.status == 200
            assert "elbysodic-material-hero--event" in event.text
            assert "chirpui-detail-header" in event.text
            assert "chirpui-chip-group" in event.text
            assert "elbysodic-material-detail-shell--event" in event.text
            assert "Iceman is infected with B-24" in event.text
            assert "Evil Lab" in event.text
            assert "Wanted hooks" in event.text
            assert "Active scenes" in event.text
            assert "Locations" in event.text
            assert "Related guidebook" in event.text
            assert "elbysodic-studio-facts" in event.text
            assert "Featured" in event.text
            assert "Carry this event into play" in event.text
            assert 'aria-label="Guide sections"' in event.text
            assert 'href="#event-actions"' in event.text
            assert 'id="canon"' in event.text
            assert "Enter scene" in event.text
            assert "Answer hook" in event.text
            assert "Explore location" in event.text
            assert "Open discovery" in event.text
            assert "What changed" in event.text
            assert "elbysodic-continuity-timeline" in event.text
            assert "elbysodic-continuity-timeline__title-link" in event.text
            assert "Event opened" in event.text
            assert "chirpui-inline-counter__label" in event.text
            assert ">replies</span>" in event.text

            location = await client.get("/boards/frozen-midtown")
            assert location.status == 200
            assert "Happening here" in location.text
            assert 'href="/world/b-24-winter"' in location.text

            scene = await client.get("/boards/frozen-midtown/threads/frozen-avenue-evacuation")
            assert scene.status == 200
            assert "Current event" in scene.text
            assert 'href="/world/b-24-winter"' in scene.text

            missing = await client.get("/world/not-a-material")
            assert missing.status == 200
            assert "That world material is not in X-Men Apocalypse." in missing.text
            assert "Open Guidebook" in missing.text

    asyncio.run(run())


def test_draft_world_materials_are_staff_only_on_rendered_routes() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        community = services.seed.community
        services.repo.create_material(
            community.id,
            "director-only-event",
            "Director Only Event",
            material_type="event",
            summary="This draft should stay inside Studio.",
            body="Private director continuity that should not leak.",
            status="draft",
        )
        member_services, _member_character_id = _outsider_services(
            services,
            prefix="draft-material-member",
        )
        member_app = create_app(debug=False, services=member_services)
        async with TestClient(member_app) as member_client:
            member_world = await member_client.get("/world")
            member_direct = await member_client.get("/world/director-only-event")

        alex_membership = services.repo.get_membership_by_username(community.id, "alex")
        alex_user = services.repo.get_user(alex_membership.user_id)
        cyclops = services.repo.get_character_by_slug(community.id, "cyclops")
        alex_services = AppServices(
            services.repo,
            DemoSeed(community, alex_user, alex_membership, cyclops),
        )
        staff_app = create_app(debug=False, services=alex_services)
        async with TestClient(staff_app) as staff_client:
            staff_studio = await staff_client.get("/studio")
            staff_direct = await staff_client.get("/world/director-only-event")

        assert member_world.status == 200
        assert "Director Only Event" not in member_world.text
        assert "Private director continuity that should not leak." not in member_direct.text
        assert "That world material is not in X-Men Apocalypse." in member_direct.text
        assert staff_studio.status == 200
        assert "Director Only Event" in staff_studio.text
        assert staff_direct.status == 200
        assert "Director Only Event" in staff_direct.text
        assert "Private director continuity that should not leak." in staff_direct.text
        assert "Edit guidebook page" in staff_direct.text

    asyncio.run(run())


def test_directors_can_publish_draft_materials_from_studio_queue() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        draft_event = repo.create_material(
            community.id,
            "new-canon-pulse",
            "New Canon Pulse",
            material_type="event",
            summary="Director draft for the next canon beat.",
            body="A production note waiting for publication.",
            status="draft",
        )
        member_services, _member_character_id = _outsider_services(
            services,
            prefix="studio-material-member",
        )
        member_app = create_app(debug=False, services=member_services)
        async with TestClient(member_app) as member_client:
            forbidden = await member_client.post(
                "/studio/content",
                body=urlencode(
                    {
                        "intent": "material_status",
                        "material_slug": draft_event.slug,
                        "status": "published",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert forbidden.status == 403
        assert repo.get_material_by_slug(community.id, draft_event.slug).status == "draft"

        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)
        async with TestClient(app) as client:
            studio = await client.get("/studio/content")
            assert studio.status == 200
            assert "New Canon Pulse" in studio.text
            assert "Publish as current" in studio.text

            response = await client.post(
                "/studio/content",
                body=urlencode(
                    {
                        "intent": "material_status",
                        "material_slug": draft_event.slug,
                        "status": "published",
                        "is_featured": "on",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert response.status == 302
            assert _response_header(response, "location") == "/studio/content#continuity-events"

            world = await client.get("/world/new-canon-pulse")
            studio_after = await client.get("/studio/content")

        updated = repo.get_material_by_slug(community.id, draft_event.slug)
        old_event = repo.get_material_by_slug(community.id, "b-24-winter")
        assert updated.status == "published"
        assert updated.is_featured is True
        assert old_event.is_featured is False
        current_event = admin_services.director_studio().current_event
        assert current_event is not None
        assert current_event.material.slug == draft_event.slug
        assert world.status == 200
        assert "New Canon Pulse" in world.text
        assert studio_after.status == 200
        assert "New Canon Pulse" in studio_after.text

    asyncio.run(run())


def test_applications_desk_tracks_character_statuses() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            applications = await client.get("/applications")
            assert applications.status == 200
            assert "Applications" in applications.text
            assert "Active application work" in applications.text
            assert "No application drafts need work." in applications.text
            assert 'href="/applications/rogue"' not in applications.text
            assert '<span class="chirpui-badge__text">Accepted</span>' not in applications.text
            assert "Application Guide" in applications.text
            assert 'href="/world/application-guide"' in applications.text

            roster = await client.get("/characters")
            assert roster.status == 200
            assert "Accepted" in roster.text
            assert "Start a draft application" in roster.text
            assert 'href="/applications"' not in _page_content(roster.text)

            response = await client.post(
                "/characters",
                body=urlencode(
                    {
                        "_action": "create_character",
                        "name": "Jubilee",
                        "summary": "Fireworks, mall instincts, and a very loud jacket.",
                        "avatar_url": "",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert response.status == 302

            services = get_services()
            character = services.repo.get_character_by_slug(
                services.seed.community.id,
                "jubilee",
            )
            assert character.application_status == "draft"

            draft_view = await client.get("/applications")
            assert draft_view.status == 200
            assert "Jubilee" in draft_view.text
            assert "Draft" in draft_view.text
            assert "Submit application" in draft_view.text
            assert 'href="/applications/jubilee"' in draft_view.text

            room = await client.get("/applications/jubilee")
            assert room.status == 200
            assert "Application Review Room" in room.text
            assert "Applicant Notes" in room.text
            assert "Save notes" in room.text

            save_room = await client.post(
                "/applications/jubilee",
                body=urlencode(
                    {
                        "intent": "save_application",
                        "summary": "Fireworks, mall instincts, and a very loud jacket.",
                        "body": "Jubilee is looking for a found-family first scene.",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert save_room.status == 302
            application = services.repo.get_character_application_for_character(
                services.seed.community.id,
                character.id,
            )
            assert application.body == "Jubilee is looking for a found-family first scene."

            submit_response = await client.post(
                "/applications",
                body=urlencode(
                    {
                        "intent": "submit_application",
                        "character_slug": "jubilee",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert submit_response.status == 302
            assert (
                services.repo.get_character_by_slug(
                    services.seed.community.id,
                    "jubilee",
                ).application_status
                == "submitted"
            )
            outsider_services, _outsider_character_id = _outsider_services(
                services,
                prefix="application-outsider",
            )
            outsider_app = create_app(debug=False, services=outsider_services)
            async with TestClient(outsider_app) as outsider_client:
                outsider_room = await outsider_client.get("/applications/jubilee")

            assert outsider_room.status == 403
            assert "Jubilee is looking for a found-family first scene." not in outsider_room.text
            assert "Director Review" not in outsider_room.text

            alex_membership = services.repo.get_membership_by_username(
                services.seed.community.id,
                "alex",
            )
            alex_user = services.repo.get_user(alex_membership.user_id)
            cyclops = services.repo.get_character_by_slug(
                services.seed.community.id,
                "cyclops",
            )
            alex_services = AppServices(
                services.repo,
                DemoSeed(services.seed.community, alex_user, alex_membership, cyclops),
            )
            assert any(
                item.label == "Application submitted" and item.title == "Jubilee"
                for item in alex_services.notifications().items
            )

            alex_app = create_app(debug=False, services=alex_services)
            async with TestClient(alex_app) as alex_client:
                review = await alex_client.get("/applications")
                assert review.status == 200
                assert "Review Queue" in review.text
                assert "Jubilee" in review.text
                assert "Accept" in review.text
                assert "Request revisions" in review.text
                assert 'name="intent" value="request_revision"' not in review.text

                review_room = await alex_client.get("/applications/jubilee")
                assert review_room.status == 200
                assert "Director Review" in review_room.text
                assert "Jubilee is looking for a found-family first scene." in review_room.text

                save_review = await alex_client.post(
                    "/applications/jubilee",
                    body=urlencode(
                        {
                            "intent": "save_review",
                            "revision_notes": "",
                            "staff_notes": "Voice is clear.",
                            "checklist": "Starter hook\nCast tie",
                        }
                    ).encode(),
                    headers=_FORM,
                )
                assert save_review.status == 302

                accept_response = await alex_client.post(
                    "/applications/jubilee",
                    body=urlencode(
                        {
                            "intent": "accept_application",
                        }
                    ).encode(),
                    headers=_FORM,
                )
                assert accept_response.status == 302

                revision_response = await alex_client.post(
                    "/applications/kitty-pryde",
                    body=urlencode(
                        {
                            "intent": "request_revision",
                            "revision_notes": "Add one concrete school-life pressure point.",
                        }
                    ).encode(),
                    headers=_FORM,
                )
                assert revision_response.status == 302

            assert (
                services.repo.get_character_by_slug(
                    services.seed.community.id,
                    "jubilee",
                ).application_status
                == "accepted"
            )
            applicant_app = create_app(
                debug=False, services=AppServices(services.repo, services.seed)
            )
            async with TestClient(applicant_app) as applicant_client:
                accepted_room = await applicant_client.get("/applications/jubilee")
            assert accepted_room.status == 200
            assert "Jubilee is looking for a found-family first scene." in accepted_room.text
            assert "Accepted face handoff" in accepted_room.text
            assert "Your first scene path is active" in accepted_room.text
            assert "Open the next scene attached to your roster." in accepted_room.text
            assert "Open scene" in accepted_room.text
            assert "Settle claims and reserves" in accepted_room.text
            assert 'href="/claims"' in accepted_room.text
            assert "Answer open calls" in accepted_room.text
            assert 'href="/wanted"' in accepted_room.text
            assert "Find a first scene" in accepted_room.text
            assert 'href="/locations"' in accepted_room.text
            assert "Director Review" not in accepted_room.text
            assert "Voice is clear." not in accepted_room.text
            assert "Starter hook" not in accepted_room.text
            assert "Cast tie" not in accepted_room.text
            assert any(
                item.label == "Application accepted" and item.title == "Jubilee"
                for item in services.notifications().items
            )
            accepted_application = services.repo.get_character_application_for_character(
                services.seed.community.id,
                character.id,
            )
            assert accepted_application.staff_notes == "Voice is clear."
            assert accepted_application.checklist == "Starter hook\nCast tie"
            assert [
                event.to_status
                for event in services.repo.list_character_application_events(
                    services.seed.community.id,
                    accepted_application.id,
                )
            ] == ["accepted", "submitted"]

            mira_membership = services.repo.get_membership_by_username(
                services.seed.community.id,
                "mira",
            )
            mira_user = services.repo.get_user(mira_membership.user_id)
            kitty = services.repo.get_character_by_slug(
                services.seed.community.id,
                "kitty-pryde",
            )
            assert kitty.application_status == "revision_requested"
            mira_services = AppServices(
                services.repo,
                DemoSeed(services.seed.community, mira_user, mira_membership, kitty),
            )
            assert any(
                item.label == "Revisions requested" and item.title == "Kitty Pryde"
                for item in mira_services.notifications().items
            )

            mira_app = create_app(debug=False, services=mira_services)
            async with TestClient(mira_app) as mira_client:
                mira_applications = await mira_client.get("/applications")
                assert mira_applications.status == 200
                assert "Resubmit application" in mira_applications.text
                kitty_room = await mira_client.get("/applications/kitty-pryde")
                assert kitty_room.status == 200
                assert "Add one concrete school-life pressure point." in kitty_room.text

                resubmit_response = await mira_client.post(
                    "/applications",
                    body=urlencode(
                        {
                            "intent": "submit_application",
                            "character_slug": "kitty-pryde",
                        }
                    ).encode(),
                    headers=_FORM,
                )
                assert resubmit_response.status == 302
            assert (
                services.repo.get_character_by_slug(
                    services.seed.community.id,
                    "kitty-pryde",
                ).application_status
                == "submitted"
            )

    asyncio.run(run())


def test_wanted_ads_render_board_detail_and_character_hub() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            wanted = await client.get("/wanted")
            assert wanted.status == 200
            assert "Wanted" in wanted.text
            assert "Brotherhood rival from Rogue" in wanted.text
            assert "Human UN liaison for B-24 talks" in wanted.text
            assert 'href="/wanted/brotherhood-rival-for-rogue"' in wanted.text
            assert "Open casting desk" not in _page_content(wanted.text)
            assert 'href="/casting"' not in _page_content(wanted.text)
            assert "elbysodic-thread-signal" not in wanted.text
            assert "United Nations" in wanted.text

            detail = await client.get("/wanted/brotherhood-rival-for-rogue")
            assert detail.status == 200
            assert "chirpui-detail-header" in detail.text
            assert "elbysodic-wanted-detail__signal" in detail.text
            assert "chirpui-facet-chip" in detail.text
            assert "chirpui-scope-switcher" not in detail.text
            assert "Rogue needs someone who remembers" in detail.text
            assert 'href="/characters/rogue"' in detail.text
            assert 'href="/world/factions"' in detail.text
            assert "Complicated Romance" in detail.text

            character = await client.get("/characters/rogue")
            assert character.status == 200
            assert "Plotter" in character.text
            assert "Scenes" in character.text
            assert "Brotherhood rival from Rogue" in character.text
            assert 'href="/wanted"' in character.text

            open_hook = await client.get("/wanted/human-un-liaison-for-b24")
            assert open_hook.status == 200
            assert 'data-elbysodic-submit-label="Sending interest..."' in open_hook.text
            assert 'data-elbysodic-command-kind="express_wanted_interest"' in open_hook.text
            assert 'data-elbysodic-actor-shape="current-face"' in open_hook.text
            assert "Raise interest as Rogue" in open_hook.text

            interest_response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert interest_response.status == 302

            interested = await client.get("/wanted/human-un-liaison-for-b24")
            assert interested.status == 200
            assert "Rogue is interested in this hook." in interested.text
            assert "Interest and reserves" in interested.text
            assert "Interest" in interested.text
            assert "elbysodic-lifecycle-section" in interested.text

            services = get_services()
            repo = services.repo
            community = services.seed.community
            wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
            rogue = repo.get_character_by_slug(community.id, "rogue")
            interest = repo.get_wanted_ad_interest_for_character(
                community.id,
                wanted_ad.id,
                rogue.id,
            )
            assert interest.character_id == rogue.id

            charlie_membership = repo.get_membership_by_username(community.id, "charlie")
            charlie_user = repo.get_user(charlie_membership.user_id)
            xavier = repo.get_character_by_slug(community.id, "charles-xavier")
            charlie_services = AppServices(
                repo,
                DemoSeed(community, charlie_user, charlie_membership, xavier),
            )
            inbox = charlie_services.notifications()
            assert inbox.unread_count == 1
            assert inbox.items[0].label == "Wanted interest"
            assert inbox.items[0].title == "Human UN liaison for B-24 talks"
            assert inbox.items[0].href == "/wanted/human-un-liaison-for-b24"

            charlie_app = create_app(debug=False, services=charlie_services)
            async with TestClient(charlie_app) as charlie_client:
                creator_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")
                assert creator_view.status == 200
                assert "Reserve for Rogue" in creator_view.text

                reserve_response = await charlie_client.post(
                    "/wanted/human-un-liaison-for-b24",
                    body=f"intent=reserve_interest&interest_id={interest.id}".encode(),
                    headers=_FORM,
                )
                assert reserve_response.status == 302

                reserved_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")
                assert reserved_view.status == 200
                assert "reserved" in reserved_view.text
                assert "Create reserve" in reserved_view.text
                assert "Reserve for Rogue" not in reserved_view.text

                reserve_create = await charlie_client.post(
                    "/wanted/human-un-liaison-for-b24",
                    body=f"intent=create_reserve&interest_id={interest.id}".encode(),
                    headers=_FORM,
                )
                assert reserve_create.status == 302

                reserve_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")
                assert reserve_view.status == 200
                assert "Reserve created" in reserve_view.text
                assert "Reserves" in reserve_view.text
                assert "elbysodic-lifecycle-list" in reserve_view.text
                assert (
                    "Reserved from wanted hook: Human UN liaison for B-24 talks"
                    in reserve_view.text
                )

            assert (
                repo.get_wanted_ad_interest_for_character(
                    community.id,
                    wanted_ad.id,
                    rogue.id,
                ).status
                == "reserved"
            )
            assert repo.get_wanted_ad(community.id, wanted_ad.id).status == "reserved"
            reserve = repo.get_character_reserve_for_wanted_interest(community.id, interest.id)
            assert reserve.character_id == rogue.id

            lane_inbox = AppServices(repo, services.seed).notifications()
            assert any(item.label == "Wanted reserved" for item in lane_inbox.items)
            assert any(item.label == "Reserve created" for item in lane_inbox.items)

            profile_app = create_app(debug=False, services=AppServices(repo, services.seed))
            async with TestClient(profile_app) as profile_client:
                profile = await profile_client.get("/characters/rogue")
                assert profile.status == 200
                assert "Reserves" in profile.text
                assert "Human UN liaison for B-24 talks" in profile.text
                casting = await profile_client.get("/casting")
                assert casting.status == 200
                assert "Casting desk" in casting.text
                assert "elbysodic-casting-desk-hero__identity" in casting.text
                assert "Active face casting" in casting.text
                assert "Wanted handoffs" in casting.text
                assert "Active Reserves" in casting.text
                assert "Human UN liaison for B-24 talks" in casting.text
                assert "Active face reserves" in casting.text
                assert "Browse wanted" not in _page_content(casting.text)
                assert "Open face" not in _page_content(casting.text)

            charlie_app = create_app(debug=False, services=charlie_services)
            async with TestClient(charlie_app) as charlie_client:
                filled_response = await charlie_client.post(
                    "/wanted/human-un-liaison-for-b24",
                    body=urlencode(
                        {
                            "intent": "update_lifecycle_status",
                            "status": "filled",
                        }
                    ).encode(),
                    headers=_FORM,
                )
                filled_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")

                archive_response = await charlie_client.post(
                    "/wanted/human-un-liaison-for-b24",
                    body=urlencode(
                        {
                            "intent": "update_lifecycle_status",
                            "status": "archived",
                        }
                    ).encode(),
                    headers=_FORM,
                )
                archived_manager_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")

                reopen_response = await charlie_client.post(
                    "/wanted/human-un-liaison-for-b24",
                    body=urlencode(
                        {
                            "intent": "update_lifecycle_status",
                            "status": "open",
                        }
                    ).encode(),
                    headers=_FORM,
                )

            outsider_services, _outsider_character_id = _outsider_services(
                services,
                prefix="wanted-archive-outsider",
            )
            archived_wanted = services.repo.update_wanted_ad_status(
                community.id,
                wanted_ad.id,
                "archived",
            )
            outsider_app = create_app(debug=False, services=outsider_services)
            async with TestClient(outsider_app) as outsider_client:
                archived_outsider_view = await outsider_client.get(
                    "/wanted/human-un-liaison-for-b24"
                )
                archived_wanted_board = await outsider_client.get("/wanted")

            reopened = services.repo.update_wanted_ad_status(
                community.id,
                wanted_ad.id,
                "open",
            )

            assert filled_response.status == 302
            assert "Manage hook" in filled_view.text
            assert '<option value="filled" selected>Filled</option>' in filled_view.text
            assert archive_response.status == 302
            assert archived_manager_view.status == 200
            assert (
                '<option value="archived" selected>Archived</option>' in archived_manager_view.text
            )
            assert reopen_response.status == 302
            assert archived_wanted.status == "archived"
            assert archived_outsider_view.status == 200
            assert "That wanted hook is not in X-Men Apocalypse." in archived_outsider_view.text
            assert "Human UN liaison for B-24 talks" not in archived_wanted_board.text
            assert reopened.status == "open"

            missing = await client.get("/wanted/not-a-hook")
            assert missing.status == 200
            assert "That wanted hook is not in X-Men Apocalypse." in missing.text
            assert "Open Wanted" in missing.text

    asyncio.run(run())


def test_public_wanted_routes_hide_non_open_hooks() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community_by_slug("x-men-apocalypse")
        wanted = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        repo.update_wanted_ad_status(community.id, wanted.id, "filled")
        app = create_app(debug=False, services=AppServices(repo, None))

        async with TestClient(app) as client:
            public_board = await client.get("/c/x-men-apocalypse/wanted")
            public_detail = await client.get("/c/x-men-apocalypse/wanted/human-un-liaison-for-b24")

        assert public_board.status == 200
        assert "Human UN liaison for B-24 talks" not in public_board.text
        assert public_detail.status == 404
        assert "Human UN liaison for B-24 talks" not in public_detail.text

    asyncio.run(run())


def test_handoff_desks_collapse_empty_work_sections() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            casting = await client.get("/casting")
            plotting = await client.get("/plotting")

        assert casting.status == 200
        assert "No casting handoffs need work right now." in _page_content(casting.text)
        assert "No raised hands yet." not in _page_content(casting.text)
        assert "No active reserves right now." not in _page_content(casting.text)

        assert plotting.status == 200
        assert "No plotting handoffs need work right now." in _page_content(plotting.text)
        assert "Nothing is at the planning table yet." not in _page_content(plotting.text)
        assert "Nothing is waiting for a room." not in _page_content(plotting.text)

    asyncio.run(run())


def test_structured_wanted_casting_packet_renders_for_rent_week_hook() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            detail = await client.get("/c/rl-nyc/wanted/ex-bandmate-with-the-old-lease")

        assert detail.status == 200
        assert "In play" in detail.text
        assert "What this role brings into play" in detail.text
        assert "Why this matters" in detail.text
        assert "First scene invitations" in detail.text
        assert "Relationship lanes" in detail.text
        assert "Negotiables" in detail.text
        assert "Their name is still on a lease" in detail.text
        assert "A hallway confrontation after the building meeting." in detail.text
        assert "Romance is optional" in detail.text

    asyncio.run(run())


def test_application_start_form_creates_draft_face_and_review_room() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        community = services.seed.community
        facet = services.repo.get_facet_by_slug(community.id, "x-men")
        fields = {
            field.field_key: field
            for field in services.repo.list_application_template_fields(community.id)
        }

        async with TestClient(app) as client:
            form = await client.get("/applications/new")
            response = await client.post(
                "/applications/new",
                body=urlencode(
                    {
                        "name": "Jean Grey",
                        "summary": "A powerful telepath trying to stay gentle.",
                        "body": "Looking for school pressure, found family, and dangerous rescue work.",
                        "facet_slugs": [facet.slug],
                        f"application_field_{fields['face_claim'].id}": "Famke Janssen",
                        f"application_field_{fields['faction_claim'].id}": "X-Men",
                        f"application_field_{fields['power_claim'].id}": "Telepathy",
                    },
                    doseq=True,
                ).encode(),
                headers=_FORM,
            )
            room = await client.get("/applications/jean-grey")
            applications = await client.get("/applications")

        character = services.repo.get_character_by_slug(community.id, "jean-grey")
        application = services.repo.get_character_application_for_character(
            community.id,
            character.id,
        )
        field_values = services.repo.list_application_field_values(community.id, application.id)
        facets = services.repo.list_character_facets(community.id, character.id)

        assert form.status == 200
        assert "Begin a new face" in form.text
        assert "Application Guide" in form.text
        assert "After this face is accepted" in form.text
        assert "Claims and reserves" in form.text
        assert 'href="/claims"' in form.text
        assert "Open calls" in form.text
        assert 'href="/wanted"' in form.text
        assert "First scene" in form.text
        assert 'href="/locations"' in form.text
        assert "Director fields" in form.text
        assert "Face claim" in form.text
        assert response.status == 302
        assert _response_header(response, "location") == "/applications/jean-grey"
        assert character.application_status == "draft"
        assert application.summary == "A powerful telepath trying to stay gentle."
        assert "dangerous rescue work" in application.body
        assert "Application fields" in application.body
        assert "Face claim: Famke Janssen" in application.body
        assert "Primary faction: X-Men" in application.body
        assert {value.value for value in field_values} == {
            "Famke Janssen",
            "Telepathy",
            "X-Men",
        }
        assert [assigned.slug for assigned in facets] == ["x-men"]
        assert room.status == 200
        assert "Jean Grey" in room.text
        assert "Director fields" in room.text
        assert "Famke Janssen" in room.text
        assert "Draft" in room.text
        assert applications.status == 200
        assert "Jean Grey" in applications.text

        async with TestClient(app) as client:
            conflict_save_response = await client.post(
                "/applications/jean-grey",
                body=urlencode(
                    {
                        "intent": "save_application",
                        "summary": "A powerful telepath trying to stay gentle.",
                        "body": "Trying a visual that directors should catch.",
                        f"application_field_{fields['face_claim'].id}": "Magneto Visual",
                        f"application_field_{fields['faction_claim'].id}": "X-Men",
                        f"application_field_{fields['power_claim'].id}": "Telekinesis",
                    }
                ).encode(),
                headers=_FORM,
            )
            conflict_room = await client.get("/applications/jean-grey")
            conflict_applications = await client.get("/applications")
            conflict_submit_response = await client.post(
                "/applications",
                body=urlencode(
                    {
                        "intent": "submit_application",
                        "character_slug": "jean-grey",
                    }
                ).encode(),
                headers=_FORM,
            )
            save_response = await client.post(
                "/applications/jean-grey",
                body=urlencode(
                    {
                        "intent": "save_application",
                        "summary": "A powerful telepath trying to stay gentle.",
                        "body": "Updated notes for school pressure and rescue work.",
                        f"application_field_{fields['face_claim'].id}": "Sophie Turner",
                        f"application_field_{fields['faction_claim'].id}": "X-Men",
                        f"application_field_{fields['power_claim'].id}": "Telekinesis",
                    }
                ).encode(),
                headers=_FORM,
            )
            submit_response = await client.post(
                "/applications",
                body=urlencode(
                    {
                        "intent": "submit_application",
                        "character_slug": "jean-grey",
                    }
                ).encode(),
                headers=_FORM,
            )
        assert save_response.status == 302
        assert conflict_save_response.status == 302
        assert conflict_room.status == 200
        assert "Already claimed" in conflict_room.text
        assert "Exclusive claim conflict: choose a different value" in conflict_room.text
        assert "before this face can be accepted" in conflict_room.text
        assert 'href="/characters/magneto"' in conflict_room.text
        assert conflict_applications.status == 200
        assert "1 claim conflict" in conflict_applications.text
        assert "First conflict is held by Magneto." in conflict_applications.text
        assert conflict_submit_response.status == 400
        assert "Face claim is already claimed: Magneto Visual" in conflict_submit_response.text
        updated_field_values = services.repo.list_application_field_values(
            community.id,
            application.id,
        )
        assert {value.value for value in updated_field_values} == {
            "Sophie Turner",
            "Telekinesis",
            "X-Men",
        }
        assert submit_response.status == 302

        alex_membership = services.repo.get_membership_by_username(community.id, "alex")
        alex_user = services.repo.get_user(alex_membership.user_id)
        cyclops = services.repo.get_character_by_slug(community.id, "cyclops")
        alex_services = AppServices(
            services.repo,
            DemoSeed(community, alex_user, alex_membership, cyclops),
        )
        alex_app = create_app(debug=False, services=alex_services)
        async with TestClient(alex_app) as alex_client:
            review_room = await alex_client.get("/applications/jean-grey")
            accept_response = await alex_client.post(
                "/applications/jean-grey",
                body=urlencode({"intent": "accept_application"}).encode(),
                headers=_FORM,
            )
            claims = await alex_client.get("/claims")

        accepted_claims = services.repo.list_character_claims_for_character(
            community.id,
            character.id,
            status=None,
        )
        assert review_room.status == 200
        assert "Intake Fields" in review_room.text
        assert accept_response.status == 302
        assert {claim.label for claim in accepted_claims} == {
            "Sophie Turner",
            "Telekinesis",
            "X-Men",
        }
        assert {claim.value for claim in accepted_claims} == {
            "sophie-turner",
            "telekinesis",
            "x-men",
        }
        assert claims.status == 200
        assert "Sophie Turner" in claims.text

    asyncio.run(run())


def test_application_start_rolls_back_when_review_room_creation_fails(monkeypatch) -> None:
    services = _faceless_services(create_services(path=":memory:"), prefix="rollback-app")
    community = services.seed.community
    membership = services.seed.membership

    def fail_application_creation(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated application room failure")

    monkeypatch.setattr(
        services.repo,
        "ensure_character_application",
        fail_application_creation,
    )

    with pytest.raises(RuntimeError, match="simulated application room failure"):
        services.create_character(
            name="Rollback Face",
            summary="This draft should not survive a late failure.",
            application_body="This application should not survive either.",
            make_default=True,
        )

    assert services.repo.list_characters(community.id, membership.id) == []
    assert services.repo.get_membership(community.id, membership.id).default_character_id is None
    with pytest.raises(LookupError):
        services.repo.get_character_by_slug(community.id, "rollback-face")


def test_application_acceptance_rolls_back_claims_and_status_on_late_failure(
    monkeypatch,
) -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    community = services.seed.community
    fields = {
        field.field_key: field for field in repo.list_application_template_fields(community.id)
    }
    character = services.create_character(
        name="Acceptance Rollback Face",
        summary="A submitted face used to prove atomic staff acceptance.",
        application_body="Mapped claims must roll back with a late notification failure.",
        application_field_values={
            fields["face_claim"].id: "Acceptance Rollback Visual",
            fields["faction_claim"].id: "Acceptance Rollback Faction",
        },
    )
    services.submit_character_application(character.slug)
    staff = resolve_seed_persona(repo, "xmen_staff")
    staff_services = AppServices(
        repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )

    def fail_notification(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated application acceptance notification failure")

    monkeypatch.setattr(repo, "create_notification", fail_notification)

    with pytest.raises(
        RuntimeError,
        match="simulated application acceptance notification failure",
    ):
        staff_services.accept_character_application(character.slug)

    stored = repo.get_character(community.id, character.id)
    claims = repo.list_character_claims_for_character(community.id, character.id, status=None)
    assert stored.application_status == "submitted"
    assert claims == []
    assert not repo.connection.in_transaction
    assert repo.get_character_by_slug(community.id, character.slug).id == character.id


def test_application_review_flags_mapped_claim_conflicts_before_accept() -> None:
    async def run() -> None:
        _app()
        services = get_services()
        community = services.seed.community
        fields = {
            field.field_key: field
            for field in services.repo.list_application_template_fields(community.id)
        }
        expected_revision_note = (
            "Please revise the mapped claim details before we can accept this face.\n"
            "- Face claim: Magneto Visual is already held by Magneto."
        )
        character = services.create_character(
            name="Duplicate Face",
            summary="A test applicant with a taken visual reference.",
            application_body="Staff should see the collision before accepting.",
            application_field_values={
                fields["face_claim"].id: "Magneto Visual",
                fields["faction_claim"].id: "X-Men",
            },
        )
        application = services.repo.get_character_application_for_character(
            community.id,
            character.id,
        )
        services.repo.transition_character_application_status(
            community.id,
            application.id,
            status="submitted",
            actor_membership_id=services.seed.membership.id,
            actor_character_id=character.id,
            note="Imported submitted application.",
        )

        alex_membership = services.repo.get_membership_by_username(community.id, "alex")
        alex_user = services.repo.get_user(alex_membership.user_id)
        cyclops = services.repo.get_character_by_slug(community.id, "cyclops")
        alex_services = AppServices(
            services.repo,
            DemoSeed(community, alex_user, alex_membership, cyclops),
        )
        alex_app = create_app(debug=False, services=alex_services)
        async with TestClient(alex_app) as alex_client:
            applications = await alex_client.get("/applications")
            review_room = await alex_client.get("/applications/duplicate-face")
            accept_response = await alex_client.post(
                "/applications/duplicate-face",
                body=urlencode({"intent": "accept_application"}).encode(),
                headers=_FORM,
            )
            revision_response = await alex_client.post(
                "/applications/duplicate-face",
                body=urlencode(
                    {
                        "intent": "request_revision",
                        "revision_notes": expected_revision_note,
                    }
                ).encode(),
                headers=_FORM,
            )

        duplicate = services.repo.get_character_by_slug(community.id, "duplicate-face")
        duplicate_application = services.repo.get_character_application_for_character(
            community.id,
            duplicate.id,
        )

        assert review_room.status == 200
        assert applications.status == 200
        assert "1 claim conflict" in applications.text
        assert "First conflict is held by Magneto." in applications.text
        assert "Already claimed" in review_room.text
        assert "Resolve exclusive claims before accepting" in review_room.text
        assert "Please revise the mapped claim details" in review_room.text
        assert "Review claims" in review_room.text
        assert (
            '<button type="submit"\n                class="chirpui-btn chirpui-btn--primary"\n                disabled>'
            in review_room.text
        )
        assert "Held by" in review_room.text
        assert 'href="/characters/magneto"' in review_room.text
        assert "Shared lane" in review_room.text
        assert accept_response.status == 400
        assert "Face claim is already claimed: Magneto Visual" in accept_response.text
        assert revision_response.status == 302
        assert duplicate.application_status == "revision_requested"
        assert duplicate_application.revision_notes == expected_revision_note

    asyncio.run(run())


def test_application_start_form_preserves_validation_errors_and_unique_slugs() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        community = services.seed.community
        fields = {
            field.field_key: field
            for field in services.repo.list_application_template_fields(community.id)
        }
        dynamic_fields = {
            f"application_field_{fields['face_claim'].id}": "Echo Visual",
            f"application_field_{fields['faction_claim'].id}": "X-Men",
        }

        async with TestClient(app) as client:
            invalid = await client.post(
                "/applications/new",
                body=urlencode({"name": "", "summary": "A concept"}).encode(),
                headers=_FORM,
            )
            missing_required_field = await client.post(
                "/applications/new",
                body=urlencode(
                    {
                        "name": "Missing Claim",
                        "summary": "A concept",
                    }
                ).encode(),
                headers=_FORM,
            )
            duplicate_claim = await client.post(
                "/applications/new",
                body=urlencode(
                    {
                        "name": "Duplicate Face",
                        "summary": "A concept with a taken face claim.",
                        f"application_field_{fields['face_claim'].id}": "Magneto Visual",
                        f"application_field_{fields['faction_claim'].id}": "X-Men",
                    }
                ).encode(),
                headers=_FORM,
            )
            first = await client.post(
                "/applications/new",
                body=urlencode(
                    {
                        "name": "Echo",
                        "summary": "First draft",
                        **dynamic_fields,
                    }
                ).encode(),
                headers=_FORM,
            )
            second = await client.post(
                "/applications/new",
                body=urlencode(
                    {
                        "name": "Echo",
                        "summary": "Second draft",
                        **dynamic_fields,
                    }
                ).encode(),
                headers=_FORM,
            )

        assert invalid.status == 200
        assert "character name is required" in invalid.text
        assert missing_required_field.status == 200
        assert "Face claim is required" in missing_required_field.text
        assert duplicate_claim.status == 200
        assert (
            "Some claims need another choice before you create this draft." in duplicate_claim.text
        )
        assert "Already claimed" in duplicate_claim.text
        assert "Held by" in duplicate_claim.text
        assert 'href="/characters/magneto"' in duplicate_claim.text
        assert "Shared lane" in duplicate_claim.text
        assert first.status == 302
        assert _response_header(first, "location") == "/applications/echo"
        assert second.status == 302
        assert _response_header(second, "location") == "/applications/echo-2"
        assert services.repo.get_character_by_slug(community.id, "echo").name == "Echo"
        assert services.repo.get_character_by_slug(community.id, "echo-2").name == "Echo"
        assert "duplicate-face" not in [
            character.slug for character in services.repo.list_community_characters(community.id)
        ]

    asyncio.run(run())


def test_direct_application_path_switches_to_realm_form() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)

        async with TestClient(app) as client:
            network = await client.get("/network")
            response = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(hp_membership.id),
                        "character_id": "0",
                        "next": "/c/hp-universe/applications/new",
                    }
                ).encode(),
                headers=_FORM,
            )
            set_cookie = _response_header(response, "set-cookie").split(";", 1)[0]
            form = await client.get(
                "/c/hp-universe/applications/new", headers={"Cookie": set_cookie}
            )

        assert network.status == 200
        assert "/applications/new" not in network.text
        assert "Start application" not in network.text
        assert response.status == 302
        assert _response_header(response, "location") == "/c/hp-universe/applications/new"
        assert form.status == 200
        assert '<span class="elbysodic-community-brand__name">HP Universe</span>' in form.text
        assert "Begin a new face" in form.text

    asyncio.run(run())


def test_claims_directory_renders_seeded_claims_and_studio_summary() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            claims = await client.get("/claims")
            open_claims = await client.get("/claims?status=available")
            magneto_claims = await client.get("/claims?q=magneto")
            claimed_brotherhood = await client.get("/claims?status=claimed&q=brotherhood")
            no_results = await client.get("/claims?q=not-a-real-claim")
            studio = await client.get("/studio/content")

        assert claims.status == 200
        assert "What is claimed, reserved, and open." in claims.text
        assert "Claimed" in claims.text
        assert "Reserved" in claims.text
        assert "Open slots" in claims.text
        assert "Face Claim" in claims.text
        assert "Faction Claim" in claims.text
        assert "Magneto visual reference" in claims.text
        assert "Brotherhood" in claims.text
        assert "Collected by Face claim on the application template." in claims.text
        assert open_claims.status == 200
        assert "What is claimed, reserved, and open." in open_claims.text
        assert "X-Men" in open_claims.text
        assert "Magneto visual reference" not in open_claims.text
        assert "No available claims match this type yet." in open_claims.text
        assert magneto_claims.status == 200
        assert "Magneto visual reference" in magneto_claims.text
        assert "Rogue visual reference" not in magneto_claims.text
        assert 'href="/claims?status=claimed&amp;q=magneto"' in magneto_claims.text
        assert claimed_brotherhood.status == 200
        assert "Brotherhood" in claimed_brotherhood.text
        assert "Rogue visual reference" not in claimed_brotherhood.text
        assert no_results.status == 200
        assert 'value="not-a-real-claim"' in no_results.text
        assert 'No claims match "not-a-real-claim" in this type.' in no_results.text
        assert studio.status == 200
        assert "Intake tables" in studio.text
        assert 'href="/claims"' in studio.text

    asyncio.run(run())


def test_rendered_surface_contract_parity_across_realm_viewers() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        xmen = services.seed.community
        xmen_writer = services.seed
        xmen_staff = resolve_seed_persona(repo, "xmen_staff")
        hp_director = resolve_seed_persona(repo, "hp_director")
        xmen_inactive = resolve_seed_persona(repo, "xmen_inactive")
        assert xmen_writer.default_character is not None
        assert xmen_staff.character is not None
        assert hp_director.character is not None

        xmen_face_claim = repo.get_claim_type_by_slug(xmen.id, "face")
        repo.create_character_claim(
            xmen.id,
            xmen_face_claim.id,
            "private-contract-face",
            "Private Contract Face",
            character_id=xmen_writer.default_character.id,
            status="claimed",
            notes="PRIVATE REALM CONTRACT NOTE",
        )
        hp_claim_type = repo.create_claim_type(
            hp_director.community.id,
            "contract-face",
            "Contract Face",
            claim_kind="face",
            description="HP-only parity claim type.",
            visibility="public",
        )
        repo.create_character_claim(
            hp_director.community.id,
            hp_claim_type.id,
            "cross-realm-only-face",
            "Cross-Realm Only Face",
            character_id=hp_director.character.id,
            status="claimed",
            notes="HP DIRECTOR CONTRACT NOTE",
        )
        repo.create_notification(
            xmen.id,
            xmen_writer.membership.id,
            kind="application_accepted",
            character_id=xmen_writer.default_character.id,
            actor_membership_id=xmen_staff.membership.id,
            actor_character_id=xmen_staff.character.id,
        )

        member_services = AppServices(repo, xmen_writer)
        staff_services = AppServices(
            repo,
            DemoSeed(
                xmen_staff.community,
                xmen_staff.user,
                xmen_staff.membership,
                xmen_staff.character,
            ),
        )
        hp_services = AppServices(
            repo,
            DemoSeed(
                hp_director.community,
                hp_director.user,
                hp_director.membership,
                hp_director.character,
            ),
        )
        inactive_services = AppServices(
            repo,
            DemoSeed(
                xmen_inactive.community,
                xmen_inactive.user,
                xmen_inactive.membership,
                xmen_inactive.character,
            ),
        )

        async with TestClient(create_app(debug=False, services=member_services)) as client:
            member_home = await client.get("/c/x-men-apocalypse")
            member_claims = await client.get("/claims")
            member_roster = await client.get("/characters")
            member_notifications = await client.get("/notifications")
            member_wanted = await client.get("/wanted")
            member_thread = await client.get("/boards/danger-room/threads/sentinel-drill")

        async with TestClient(create_app(debug=False, services=staff_services)) as client:
            staff_home = await client.get("/c/x-men-apocalypse")
            staff_claims = await client.get("/claims")
            staff_studio = await client.get("/studio")

        async with TestClient(create_app(debug=False, services=hp_services)) as client:
            hp_home = await client.get("/c/x-men-apocalypse")
            hp_own_home = await client.get(f"/c/{hp_director.community.slug}")
            hp_claims = await client.get("/claims")
            hp_roster = await client.get("/characters")
            hp_notifications = await client.get("/notifications")

        async with TestClient(create_app(debug=False, services=inactive_services)) as client:
            inactive_home = await client.get("/c/x-men-apocalypse")
            inactive_claims = await client.get("/claims")
            inactive_notifications = await client.get("/notifications")

        assert member_home.status == 200
        assert "playing as Rogue" in member_home.text
        assert "Pick up where you left off" in _page_content(member_home.text)
        assert "Continue writing as Rogue" in _page_content(member_home.text)
        assert 'href="/c/x-men-apocalypse/desk"' in member_home.text
        assert "Cross-Realm Only Face" not in member_home.text
        assert "HP DIRECTOR CONTRACT NOTE" not in member_home.text

        staff_home_content = _page_content(staff_home.text)
        assert staff_home.status == 200
        assert "Staff" in staff_home_content or "Director" in staff_home_content
        assert "Edit realm home" in staff_home_content
        assert "/studio/structure#gateway-curation" in staff_home_content
        assert "HP DIRECTOR CONTRACT NOTE" not in staff_home_content

        hp_home_content = _page_content(hp_home.text)
        assert hp_home.status == 200
        assert "Cross-Realm Only Face" not in hp_home_content
        assert "HP DIRECTOR CONTRACT NOTE" not in hp_home_content

        hp_own_home_content = _page_content(hp_own_home.text)
        assert hp_own_home.status == 200
        assert "Director" in hp_own_home_content
        assert "Manage home spotlight" in hp_own_home_content

        member_claims_content = _page_content(member_claims.text)
        assert member_claims.status == 200
        assert "Private Contract Face" in member_claims_content
        assert "PRIVATE REALM CONTRACT NOTE" not in member_claims_content
        assert "Edit claim" not in member_claims_content
        assert "Cross-Realm Only Face" not in member_claims_content
        assert "HP DIRECTOR CONTRACT NOTE" not in member_claims_content

        staff_claims_content = _page_content(staff_claims.text)
        assert staff_claims.status == 200
        assert "Private Contract Face" in staff_claims_content
        assert "PRIVATE REALM CONTRACT NOTE" in staff_claims_content
        assert "Edit claim" in staff_claims_content
        assert "Cross-Realm Only Face" not in staff_claims_content

        hp_claims_content = _page_content(hp_claims.text)
        assert hp_claims.status == 200
        assert "Cross-Realm Only Face" in hp_claims_content
        assert "HP DIRECTOR CONTRACT NOTE" in hp_claims_content
        assert "Private Contract Face" not in hp_claims_content
        assert "PRIVATE REALM CONTRACT NOTE" not in hp_claims_content

        member_roster_content = _page_content(member_roster.text)
        hp_roster_content = _page_content(hp_roster.text)
        assert member_roster.status == 200
        assert "Your roster" in member_roster_content
        assert "Rogue" in member_roster_content
        assert "Rowan Ash" not in member_roster_content
        assert hp_roster.status == 200
        assert "Rowan Ash" in hp_roster_content
        assert "Rogue" not in hp_roster_content

        member_notifications_content = _page_content(member_notifications.text)
        hp_notifications_content = _page_content(hp_notifications.text)
        assert member_notifications.status == 200
        assert "Application accepted" in member_notifications_content
        assert "Rogue" in member_notifications_content
        assert hp_notifications.status == 200
        assert "Application accepted" not in hp_notifications_content
        assert "Rogue" not in hp_notifications_content

        member_wanted_content = _page_content(member_wanted.text)
        member_thread_content = _page_content(member_thread.text)
        assert member_wanted.status == 200
        assert "Brotherhood rival from Rogue" in member_wanted_content
        assert "PRIVATE REALM CONTRACT NOTE" not in member_wanted_content
        assert member_thread.status == 200
        assert "Reply as" in member_thread_content
        assert "Rogue profile" in member_thread_content
        assert "Edit claim" not in member_thread_content
        assert "PRIVATE REALM CONTRACT NOTE" not in member_thread_content

        assert staff_studio.status == 200
        assert "Studio" in staff_studio.text
        assert "Review" in staff_studio.text
        assert "HP DIRECTOR CONTRACT NOTE" not in staff_studio.text

        assert inactive_home.status == 200
        assert "sleepingstar" not in inactive_home.text
        assert "Sleeping Star" not in inactive_home.text
        assert "playing as Sleeping Star" not in inactive_home.text
        assert inactive_claims.status == 403
        assert inactive_notifications.status == 403
        assert "Private Contract Face" not in inactive_claims.text
        assert "Rogue" not in inactive_notifications.text

    asyncio.run(run())


def test_director_can_record_manual_claims_from_claims_directory() -> None:
    async def run() -> None:
        _app()
        services = get_services()
        community = services.seed.community
        face_claim = services.repo.get_claim_type_by_slug(community.id, "face")
        alex_membership = services.repo.get_membership_by_username(community.id, "alex")
        alex_user = services.repo.get_user(alex_membership.user_id)
        cyclops = services.repo.get_character_by_slug(community.id, "cyclops")
        alex_services = AppServices(
            services.repo,
            DemoSeed(community, alex_user, alex_membership, cyclops),
        )
        alex_app = create_app(debug=False, services=alex_services)

        async with TestClient(alex_app) as client:
            directory = await client.get("/claims")
            response = await client.post(
                "/claims",
                body=urlencode(
                    {
                        "_action": "create_claim",
                        "claim_type_id": str(face_claim.id),
                        "label": "Cyclops tactical visor",
                        "status": "claimed",
                        "character_id": str(cyclops.id),
                        "notes": "Manual director correction after importing old claims.",
                    }
                ).encode(),
                headers=_FORM,
            )
            created_claim = next(
                claim
                for claim in services.repo.list_character_claims_for_character(
                    community.id,
                    cyclops.id,
                    status=None,
                )
                if claim.label == "Cyclops tactical visor"
            )
            update_response = await client.post(
                "/claims",
                body=urlencode(
                    {
                        "_action": "update_claim",
                        "claim_id": str(created_claim.id),
                        "label": "Cyclops visor reserve",
                        "status": "reserved",
                        "character_id": "",
                        "notes": "Holding the visual slot during a costume refresh.",
                    }
                ).encode(),
                headers=_FORM,
            )
            updated_directory = await client.get("/claims")
            reserved_directory = await client.get("/claims?status=reserved")
        member_app = create_app(debug=False, services=AppServices(services.repo, services.seed))
        async with TestClient(member_app) as member_client:
            member_directory = await member_client.get("/claims")

        manual_claim = services.repo.get_character_claim(
            community.id,
            created_claim.id,
        )
        cyclops_claims = services.repo.list_character_claims_for_character(
            community.id,
            cyclops.id,
            status=None,
        )

        assert directory.status == 200
        assert "Record claim" in directory.text
        assert "Cyclops" in directory.text
        assert 'name="_action" value="create_claim"' in directory.text
        assert 'name="_action" value="update_claim"' in directory.text
        assert 'name="intent" value="create_claim"' not in directory.text
        assert 'name="intent" value="update_claim"' not in directory.text
        assert response.status == 302
        assert update_response.status == 302
        assert manual_claim.label == "Cyclops visor reserve"
        assert manual_claim.value == "cyclops-visor-reserve"
        assert manual_claim.status == "reserved"
        assert manual_claim.character_id is None
        assert manual_claim.notes == "Holding the visual slot during a costume refresh."
        assert all(claim.id != created_claim.id for claim in cyclops_claims)
        assert updated_directory.status == 200
        assert "Edit claim" in updated_directory.text
        assert "Cyclops visor reserve" in updated_directory.text
        assert "Holding the visual slot during a costume refresh." in updated_directory.text
        assert "Save claim" in updated_directory.text
        assert member_directory.status == 200
        assert "Cyclops visor reserve" in member_directory.text
        assert "Holding the visual slot during a costume refresh." not in member_directory.text
        assert "Save claim" not in member_directory.text
        assert reserved_directory.status == 200
        assert "Cyclops visor reserve" in reserved_directory.text
        assert "Cyclops tactical visor" not in reserved_directory.text

    asyncio.run(run())


def test_studio_intake_editor_updates_claims_and_application_fields() -> None:
    async def run() -> None:
        _app()
        services = get_services()
        community = services.seed.community
        face_claim = services.repo.get_claim_type_by_slug(community.id, "face")
        faction_field = services.repo.get_application_template_field_by_key(
            community.id,
            "faction_claim",
        )
        alex_membership = services.repo.get_membership_by_username(community.id, "alex")
        alex_user = services.repo.get_user(alex_membership.user_id)
        cyclops = services.repo.get_character_by_slug(community.id, "cyclops")
        alex_services = AppServices(
            services.repo,
            DemoSeed(community, alex_user, alex_membership, cyclops),
        )
        alex_app = create_app(debug=False, services=alex_services)

        async with TestClient(alex_app) as client:
            editor = await client.get("/studio/intake")
            create_claim_response = await client.post(
                "/studio/intake",
                body=urlencode(
                    {
                        "intent": "create_claim_type",
                        "name": "Birthright Claim",
                        "claim_kind": "lineage",
                        "description": "Legacy, family, or inheritance pressure.",
                        "sort_order": "25",
                        "is_required": "on",
                        "is_exclusive": "on",
                        "visibility": "public",
                    }
                ).encode(),
                headers=_FORM,
            )
            created_claim = services.repo.get_claim_type_by_slug(community.id, "birthright-claim")
            create_field_response = await client.post(
                "/studio/intake",
                body=urlencode(
                    {
                        "intent": "create_template_field",
                        "label": "Birthright",
                        "field_type": "text",
                        "maps_to_claim_type_id": str(created_claim.id),
                        "sort_order": "35",
                        "help_text": "Name the legacy pressure this face brings into play.",
                        "placeholder": "Summers family, royal line, inherited title...",
                        "options": "",
                        "is_required": "on",
                    }
                ).encode(),
                headers=_FORM,
            )
            claim_response = await client.post(
                "/studio/intake",
                body=urlencode(
                    {
                        "intent": "claim_type",
                        "claim_type_id": str(face_claim.id),
                        "name": "Visual Claim",
                        "claim_kind": "face",
                        "description": "The visual reference directors reserve.",
                        "sort_order": "5",
                        "is_required": "on",
                        "is_exclusive": "on",
                        "visibility": "public",
                    }
                ).encode(),
                headers=_FORM,
            )
            field_response = await client.post(
                "/studio/intake",
                body=urlencode(
                    {
                        "intent": "template_field",
                        "field_id": str(faction_field.id),
                        "label": "Story lane",
                        "field_type": "select",
                        "maps_to_claim_type_id": str(faction_field.maps_to_claim_type_id),
                        "sort_order": "15",
                        "help_text": "Choose the pressure lane directors should route first.",
                        "placeholder": "",
                        "options": "X-Men\nBrotherhood\nCivilian\nOther",
                        "is_required": "on",
                    }
                ).encode(),
                headers=_FORM,
            )
            updated_editor = await client.get("/studio/intake")
            studio = await client.get("/studio")
            claims = await client.get("/claims")
            application_form = await client.get("/applications/new")

        updated_face_claim = services.repo.get_claim_type(community.id, face_claim.id)
        updated_faction_field = services.repo.get_application_template_field(
            community.id,
            faction_field.id,
        )
        created_field = services.repo.get_application_template_field_by_key(
            community.id,
            "birthright",
        )

        assert editor.status == 200
        assert "Claims and application fields" in editor.text
        assert create_claim_response.status == 302
        assert create_field_response.status == 302
        assert claim_response.status == 302
        assert field_response.status == 302
        assert created_claim.name == "Birthright Claim"
        assert created_claim.claim_kind == "lineage"
        assert created_claim.is_exclusive
        assert created_field.label == "Birthright"
        assert created_field.maps_to_claim_type_id == created_claim.id
        assert updated_face_claim.name == "Visual Claim"
        assert updated_face_claim.sort_order == 5
        assert updated_faction_field.label == "Story lane"
        assert updated_faction_field.options_json == '["X-Men","Brotherhood","Civilian","Other"]'
        assert updated_editor.status == 200
        assert "Add claim type" in updated_editor.text
        assert "Add application field" in updated_editor.text
        assert "Birthright Claim" in updated_editor.text
        assert "Birthright" in updated_editor.text
        assert "Visual Claim" in updated_editor.text
        assert "Story lane" in updated_editor.text
        assert studio.status == 200
        assert 'href="/studio/intake"' in studio.text
        assert claims.status == 200
        assert "Birthright Claim" in claims.text
        assert "Visual Claim" in claims.text
        assert application_form.status == 200
        assert "Story lane" in application_form.text
        assert "Birthright" in application_form.text
        assert "Other" in application_form.text

    asyncio.run(run())


def test_realm_interactions_render_submit_and_link_from_applications() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        community = services.seed.community
        interaction = services.repo.get_realm_interaction_by_slug(
            community.id,
            "pressure-lane-finder",
        )
        question = services.repo.list_realm_interaction_questions(
            community.id,
            interaction.id,
        )[0]
        option = services.repo.list_realm_interaction_options(
            community.id,
            question.id,
        )[0]

        async with TestClient(app) as client:
            hub = await client.get("/interactions")
            detail = await client.get("/interactions/pressure-lane-finder")
            application = await client.get("/applications/new")
            response = await client.post(
                "/interactions/pressure-lane-finder",
                body=urlencode({f"question_{question.id}": str(option.id)}).encode(),
                headers=_FORM,
            )
            updated = await client.get("/interactions/pressure-lane-finder")

        stored = services.repo.get_realm_interaction_response_for_membership(
            community.id,
            interaction.id,
            services.seed.membership.id,
        )

        assert hub.status == 200
        assert "Realm Artifacts" in hub.text
        assert "Pressure Lane Finder" in hub.text
        assert detail.status == 200
        assert "When the world turns against mutants" in detail.text
        assert application.status == 200
        assert "Optional realm quizzes" in application.text
        assert "Pressure Lane Finder" in application.text
        assert response.status == 302
        assert _response_header(response, "location") == "/interactions/pressure-lane-finder"
        assert stored is not None
        assert updated.status == 200
        assert "You responded" in updated.text

    asyncio.run(run())


def test_character_plot_hooks_render_create_and_notify_interest() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            character = await client.get("/characters/rogue")
            assert character.status == 200
            assert "Old ghosts, new lines" in character.text
            assert "New plot hook" in character.text

            response = await client.post(
                "/characters/rogue",
                body=urlencode(
                    {
                        "intent": "create_plot_hook",
                        "plot_hook_title": "Coffee before the crisis",
                        "plot_hook_type": "scene",
                        "plot_hook_summary": "A quieter beat before the event pressure.",
                        "plot_hook_body": "Rogue wants a low-stakes conversation before B-24.",
                        "plot_hook_facets": "x-men",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert response.status == 302

            detail = await client.get("/characters/rogue/hooks/coffee-before-the-crisis")
            assert detail.status == 200
            assert "Coffee before the crisis" in detail.text
            assert "You created this hook." in detail.text

            discover = await client.get("/discover?facets=x-men")
            assert discover.status == 200
            assert "Plot hooks" in discover.text
            assert "Coffee before the crisis" in discover.text

            services = get_services()
            outsider_services, outsider_character_id = _outsider_services(
                services,
                prefix="hookfan",
            )
            outsider_app = create_app(debug=False, services=outsider_services)
            async with TestClient(outsider_app) as outsider_client:
                outsider_detail = await outsider_client.get(
                    "/characters/rogue/hooks/coffee-before-the-crisis"
                )
                assert outsider_detail.status == 200
                assert "I'm interested as Hookfan Face" in outsider_detail.text

                interest = await outsider_client.post(
                    "/characters/rogue/hooks/coffee-before-the-crisis",
                    body=b"intent=express_interest",
                    headers=_FORM,
                )
                assert interest.status == 302

            owner_inbox = AppServices(services.repo, services.seed).notifications()
            assert any(item.label == "Plot hook interest" for item in owner_inbox.items)

            repo = services.repo
            community = services.seed.community
            hook = repo.get_character_plot_hook_by_slug(
                community.id,
                repo.get_character_by_slug(community.id, "rogue").id,
                "coffee-before-the-crisis",
            )
            interest = repo.list_character_plot_hook_interests(community.id, hook.id)[0]
            leak_services, _leak_character_id = _outsider_services(
                services,
                prefix="hookleak",
            )
            leak_notification = repo.create_notification(
                community.id,
                leak_services.seed.membership.id,
                kind="plot_hook_interest",
                character_plot_hook_id=hook.id,
                actor_membership_id=outsider_services.seed.membership.id,
                actor_character_id=outsider_character_id,
            )
            leak_app = create_app(debug=False, services=leak_services)
            async with TestClient(leak_app) as leak_client:
                leak_inbox = await leak_client.get("/notifications")
                leak_mark_all = await leak_client.post(
                    "/notifications",
                    body=b"_action=mark_all_read",
                    headers=_FORM,
                )
                leak_open = await leak_client.post(
                    "/notifications",
                    body=urlencode(
                        {
                            "_action": "open",
                            "notification_id": str(leak_notification.id),
                        }
                    ).encode(),
                    headers=_FORM,
                )

            assert leak_services.viewer().unread_notification_count == 0
            assert leak_services.notifications().unread_count == 0
            assert leak_inbox.status == 200
            assert "No notifications are waiting on you." in leak_inbox.text
            assert "Coffee before the crisis" not in leak_inbox.text
            assert "Hookfan Face" not in leak_inbox.text
            assert leak_mark_all.status == 302
            assert repo.get_notification(community.id, leak_notification.id).read_at is None
            assert leak_open.status == 404

            owner_app = create_app(debug=False, services=AppServices(repo, services.seed))
            async with TestClient(owner_app) as owner_client:
                creator_detail = await owner_client.get(
                    "/characters/rogue/hooks/coffee-before-the-crisis"
                )
                assert creator_detail.status == 200
                assert "Interest and rooms" in creator_detail.text
                assert "elbysodic-lifecycle-section" in creator_detail.text
                assert "Start plotting room" in creator_detail.text

                room_response = await owner_client.post(
                    "/characters/rogue/hooks/coffee-before-the-crisis",
                    body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                    headers=_FORM,
                )
                assert room_response.status == 302

                room = repo.get_plotting_room_for_plot_hook_interest(community.id, interest.id)
                room_page = await owner_client.get(f"/plotting/{room.id}")
                assert room_page.status == 200
                assert "Coffee before the crisis: Hookfan Face" in room_page.text
                assert "Hookfan Face" in room_page.text

                plotting = await owner_client.get("/plotting")
                assert plotting.status == 200
                assert "Plotting rooms" in plotting.text
                assert "Open plotting room" in plotting.text
                assert "Active face plotter" not in _page_content(plotting.text)
                assert "Discover hooks" not in _page_content(plotting.text)
                assert "Find plot hooks" not in _page_content(plotting.text)

                profile = await owner_client.get("/characters/rogue")
                assert profile.status == 200
                assert "Plotting now" in profile.text
                assert "Coffee before the crisis: Hookfan Face" in profile.text

            assert (
                repo.get_character_plot_hook_interest(community.id, interest.id).status
                == "plotting"
            )

            outsider_inbox = outsider_services.notifications()
            assert any(item.label == "Plotting room" for item in outsider_inbox.items)

    asyncio.run(run())


def test_unaccepted_faces_cannot_take_story_actions() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    community = services.seed.community
    assert services.seed.default_character is not None
    character = repo.update_character_application_status(
        community.id,
        services.seed.default_character.id,
        "submitted",
    )
    thread = repo.get_thread_by_slug(
        community.id,
        repo.get_board_by_slug(community.id, "danger-room").id,
        "sentinel-drill",
    )
    role = repo.get_role_by_slug(community.id, "member")
    other_user = repo.create_user("story-counterparty@example.com", "hash")
    other_membership = repo.create_membership(
        community.id,
        other_user.id,
        role.id,
        "storycounter",
        "Story Counter",
    )
    other_character = repo.create_character(
        community.id,
        other_membership.id,
        "story-counter-face",
        "Story Counter Face",
    )
    repo.create_character_plot_hook(
        community.id,
        other_membership.id,
        other_character.id,
        "outside-hook",
        "Outside hook",
        summary="A hook for someone else.",
    )
    repo.create_wanted_ad(
        community.id,
        other_membership.id,
        "outside-wanted",
        "Outside wanted",
        summary="A wanted hook for someone else.",
    )

    with pytest.raises(PermissionError):
        services.start_thread(
            board_slug="danger-room",
            character_id=character.id,
            title="Submitted face scene",
            body="This should wait for acceptance.",
        )
    with pytest.raises(PermissionError):
        services.reply_to_thread("danger-room", thread.slug, character.id, "Not yet.")
    with pytest.raises(PermissionError):
        services.create_plot_hook(
            character.slug,
            title="Submitted face hook",
            hook_type="scene",
            summary="This should wait.",
            body="This should wait for acceptance.",
            facet_slugs=[],
        )
    with pytest.raises(PermissionError):
        services.express_plot_hook_interest("story-counter-face", "outside-hook")
    with pytest.raises(PermissionError):
        services.express_wanted_interest("outside-wanted")


def test_wanted_hooks_accept_prospective_character_interest() -> None:
    async def run() -> None:
        _app()
        services = get_services()
        faceless_services = _faceless_services(services, prefix="newface")
        faceless_app = create_app(debug=False, services=faceless_services)
        async with TestClient(faceless_app) as faceless_client:
            wanted = await faceless_client.get("/wanted/human-un-liaison-for-b24")
            assert wanted.status == 200
            assert "Pitch a new face for this" in wanted.text

            response = await faceless_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=urlencode(
                    {
                        "intent": "express_prospective_interest",
                        "prospective_character_name": "Val Cooper",
                        "note": "I would app her as a UN pressure point.",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert response.status == 302

        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        newface_membership = repo.get_membership_by_username(community.id, "newface")
        prospective = repo.get_prospective_wanted_ad_interest_for_membership(
            community.id,
            wanted_ad.id,
            newface_membership.id,
        )
        assert prospective.character_id is None
        assert prospective.prospective_character_name == "Val Cooper"

        outsider_services, _outsider_character_id = _outsider_services(
            services,
            prefix="wanted-note-outsider",
        )
        outsider_app = create_app(debug=False, services=outsider_services)
        notification = repo.create_notification(
            community.id,
            outsider_services.seed.membership.id,
            kind="wanted_interest",
            wanted_ad_id=wanted_ad.id,
            wanted_ad_interest_id=prospective.id,
            actor_membership_id=newface_membership.id,
            actor_character_id=None,
        )
        async with TestClient(outsider_app) as outsider_client:
            outsider_view = await outsider_client.get("/wanted/human-un-liaison-for-b24")
            outsider_inbox = await outsider_client.get("/notifications")
            open_attempt = await outsider_client.post(
                "/notifications",
                body=urlencode(
                    {
                        "_action": "open",
                        "notification_id": str(notification.id),
                    }
                ).encode(),
                headers=_FORM,
            )
            assert outsider_view.status == 200
            assert outsider_inbox.status == 200
            assert "Val Cooper" in outsider_view.text
            assert "I would app her as a UN pressure point." not in outsider_view.text
            assert "I would app her as a UN pressure point." not in outsider_inbox.text
            assert open_attempt.status == 404

        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_services = AppServices(
            repo,
            DemoSeed(community, charlie_user, charlie_membership, xavier),
        )
        creator_app = create_app(debug=False, services=charlie_services)
        async with TestClient(creator_app) as creator_client:
            creator_view = await creator_client.get("/wanted/human-un-liaison-for-b24")
            assert creator_view.status == 200
            assert "Val Cooper" in creator_view.text
            assert "I would app her as a UN pressure point." in creator_view.text
            assert "Reserve for Val Cooper" in creator_view.text

            reserve = await creator_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=reserve_interest&interest_id={prospective.id}".encode(),
                headers=_FORM,
            )
            assert reserve.status == 302

            reserved_view = await creator_client.get("/wanted/human-un-liaison-for-b24")
            assert reserved_view.status == 200
            assert "Create the character before making a reserve record." in reserved_view.text

        inbox = charlie_services.notifications()
        assert any(item.label == "Wanted interest" for item in inbox.items)

    asyncio.run(run())


def test_wanted_interest_rolls_back_when_notification_fanout_fails(monkeypatch) -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    community = services.seed.community
    wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
    assert services.seed.default_character is not None

    def fail_notification(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated wanted-interest notification failure")

    monkeypatch.setattr(repo, "create_notification", fail_notification)

    with pytest.raises(RuntimeError, match="simulated wanted-interest notification failure"):
        services.express_wanted_interest(wanted_ad.slug)

    with pytest.raises(LookupError):
        repo.get_wanted_ad_interest_for_character(
            community.id,
            wanted_ad.id,
            services.seed.default_character.id,
        )
    assert not repo.connection.in_transaction
    assert repo.get_wanted_ad(community.id, wanted_ad.id).status == "open"


def test_plotting_room_start_rolls_back_room_participants_and_interest(
    monkeypatch,
) -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    community = services.seed.community
    wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
    interest = services.express_wanted_interest(wanted_ad.slug)
    staff = resolve_seed_persona(repo, "xmen_staff")
    staff_services = AppServices(
        repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )

    def fail_notification(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated plotting-room notification failure")

    monkeypatch.setattr(repo, "create_notification", fail_notification)

    with pytest.raises(RuntimeError, match="simulated plotting-room notification failure"):
        staff_services.create_plotting_room_from_wanted_interest(wanted_ad.slug, interest.id)

    with pytest.raises(LookupError):
        repo.get_plotting_room_for_wanted_interest(community.id, interest.id)
    assert repo.get_wanted_ad_interest(community.id, interest.id).status == "interested"
    assert not repo.connection.in_transaction
    assert repo.get_wanted_ad(community.id, wanted_ad.id).status == "open"


def test_plot_hook_room_start_rolls_back_room_participants_and_hook(monkeypatch) -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    community = services.seed.community
    assert services.seed.default_character is not None
    hook = services.create_plot_hook(
        services.seed.default_character.slug,
        title="Rollback Hook Room",
        hook_type="scene",
        summary="A hook used to prove atomic plotting-room creation.",
        body="The room and every participant must disappear on a late failure.",
        facet_slugs=[],
    )
    outsider_services, _outsider_character_id = _outsider_services(
        services,
        prefix="rollback-hook-room",
    )
    interest = outsider_services.express_plot_hook_interest(
        services.seed.default_character.slug,
        hook.slug,
    )

    def fail_notification(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated plot-hook room notification failure")

    monkeypatch.setattr(repo, "create_notification", fail_notification)

    with pytest.raises(RuntimeError, match="simulated plot-hook room notification failure"):
        services.create_plotting_room_from_plot_hook_interest(
            services.seed.default_character.slug,
            hook.slug,
            interest.id,
        )

    with pytest.raises(LookupError):
        repo.get_plotting_room_for_plot_hook_interest(community.id, interest.id)
    assert repo.get_character_plot_hook_interest(community.id, interest.id).status == "interested"
    assert repo.get_character_plot_hook(community.id, hook.id).status == "open"
    assert not repo.connection.in_transaction


def test_plotting_rooms_start_from_wanted_interest() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert response.status == 302

        services = get_services()
        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        rogue = repo.get_character_by_slug(community.id, "rogue")
        interest = repo.get_wanted_ad_interest_for_character(community.id, wanted_ad.id, rogue.id)
        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_services = AppServices(
            repo,
            DemoSeed(community, charlie_user, charlie_membership, xavier),
        )
        charlie_app = create_app(debug=False, services=charlie_services)
        async with TestClient(charlie_app) as charlie_client:
            creator_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")
            assert creator_view.status == 200
            assert "Start plotting room" in creator_view.text

            room_response = await charlie_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                headers=_FORM,
            )
            assert room_response.status == 302

            room = repo.get_plotting_room_for_wanted_interest(community.id, interest.id)
            updated_detail = await charlie_client.get("/wanted/human-un-liaison-for-b24")
            assert updated_detail.status == 200
            assert "In plotting" in updated_detail.text
            assert "Open plotting room" in updated_detail.text
            room_page = await charlie_client.get(f"/plotting/{room.id}")
            assert room_page.status == 200
            assert "Human UN liaison for B-24 talks: Rogue" in room_page.text
            assert "Charles Xavier" in room_page.text
            assert "Rogue" in room_page.text

            plotting = await charlie_client.get("/plotting")
            assert plotting.status == 200
            assert "Interest" in plotting.text
            assert "Open plotting room" in plotting.text
            assert "Active face plotter" not in _page_content(plotting.text)
            assert "Browse wanted" not in _page_content(plotting.text)

        lane_inbox = AppServices(repo, services.seed).notifications()
        assert any(item.label == "Plotting room" for item in lane_inbox.items)
        assert repo.get_wanted_ad_interest(community.id, interest.id).status == "plotting"

    asyncio.run(run())


def test_tenant_prefixed_plotting_room_scopes_live_and_plan_routes() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert response.status == 302

        services = get_services()
        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        rogue = repo.get_character_by_slug(community.id, "rogue")
        interest = repo.get_wanted_ad_interest_for_character(community.id, wanted_ad.id, rogue.id)
        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_services = AppServices(
            repo,
            DemoSeed(community, charlie_user, charlie_membership, xavier),
        )
        charlie_app = create_app(debug=False, services=charlie_services)
        async with TestClient(charlie_app) as charlie_client:
            room_response = await charlie_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                headers=_FORM,
            )
            assert room_response.status == 302

            room = repo.get_plotting_room_for_wanted_interest(community.id, interest.id)
            room_page = await charlie_client.get(f"/c/{community.slug}/plotting/{room.id}")
            stream_task = asyncio.create_task(
                charlie_client.sse(
                    f"/c/{community.slug}/plotting/{room.id}/stream",
                    max_events=2,
                )
            )
            await asyncio.sleep(0.05)
            message = await charlie_client.post(
                f"/c/{community.slug}/plotting/{room.id}",
                body=urlencode(
                    {
                        "intent": "post_message",
                        "body": "Charles opens the planning thread.",
                    }
                ).encode(),
                headers=_FORM,
            )
            stream = await stream_task
            saved = await charlie_client.post(
                f"/c/{community.slug}/plotting/{room.id}",
                body=urlencode(
                    {
                        "intent": "save_plan",
                        "notes": "Talk through the UN pressure point.",
                        "next_step": "Pick the first scene.",
                        "status": "brainstorming",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert room_page.status == 200
        assert "Human UN liaison for B-24 talks: Rogue" in room_page.text
        assert f'href="/c/{community.slug}/plotting"' in room_page.text
        assert f'sse-connect="/c/{community.slug}/plotting/{room.id}/stream"' in room_page.text
        assert f'hx-post="/c/{community.slug}/plotting/{room.id}"' in room_page.text
        assert 'hx-sync="this:replace"' in room_page.text
        assert 'data-elbysodic-submit-label="Sending..."' in room_page.text
        assert message.status == 302
        assert stream.status == 200
        assert stream.events[0].event == "plotting-room-ready"
        assert f'href="/c/{community.slug}/characters/charles-xavier"' in stream.events[1].data
        assert "Charles opens the planning thread." in stream.events[1].data
        assert saved.status == 302
        assert _response_header(saved, "location") == f"/c/{community.slug}/plotting/{room.id}"

    asyncio.run(run())


def test_plotting_room_sse_ready_event_uses_safe_channel() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert response.status == 302

        services = get_services()
        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        rogue = repo.get_character_by_slug(community.id, "rogue")
        interest = repo.get_wanted_ad_interest_for_character(community.id, wanted_ad.id, rogue.id)
        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_app = create_app(
            debug=False,
            services=AppServices(
                repo,
                DemoSeed(community, charlie_user, charlie_membership, xavier),
            ),
        )
        async with TestClient(charlie_app) as charlie_client:
            room_response = await charlie_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                headers=_FORM,
            )
            assert room_response.status == 302

            room = repo.get_plotting_room_for_wanted_interest(community.id, interest.id)
            stream = await charlie_client.sse(
                f"/plotting/{room.id}/stream",
                max_events=1,
                timeout=1.0,
            )

        assert stream.status == 200
        ready_events = [event for event in stream.events if event.event == "plotting-room-ready"]
        assert len(ready_events) == 1
        event = ready_events[0]
        assert event.data == "connected"
        assert event.event is not None
        assert "\r" not in event.event
        assert "\n" not in event.event
        assert "\x00" not in event.event

    asyncio.run(run())


def test_plotting_room_sse_closes_cleanly_on_worker_draining(caplog) -> None:
    caplog.set_level(logging.INFO, logger="pounce.elbysodic")

    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert response.status == 302

        services = get_services()
        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        rogue = repo.get_character_by_slug(community.id, "rogue")
        interest = repo.get_wanted_ad_interest_for_character(community.id, wanted_ad.id, rogue.id)
        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_app = create_app(
            debug=False,
            services=AppServices(
                repo,
                DemoSeed(community, charlie_user, charlie_membership, xavier),
            ),
        )
        async with TestClient(charlie_app) as charlie_client:
            room_response = await charlie_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                headers=_FORM,
            )
            assert room_response.status == 302

            room = repo.get_plotting_room_for_wanted_interest(community.id, interest.id)
            stream_path = f"/plotting/{room.id}/stream"
            stream_task = asyncio.create_task(
                charlie_client.sse(stream_path, max_events=5, disconnect_after=5.0)
            )
            await asyncio.sleep(0.1)
            assert active_plotting_streams() == 1

            message = await charlie_client.post(
                f"/plotting/{room.id}",
                body=urlencode(
                    {
                        "intent": "post_message",
                        "body": "Queued before reload drain.",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert message.status == 302
            await asyncio.sleep(0.1)

            await emit_worker_draining(charlie_app)
            stream = await stream_task
            assert active_plotting_streams() == 0

            room_page = await charlie_client.get(f"/plotting/{room.id}")
            assert 'sse-close="pounce.worker.draining"' in room_page.text

        assert stream.status == 200
        event_names = [event.event for event in stream.events]
        assert "plotting-room-ready" in event_names
        message_events = [
            event for event in stream.events if event.event == "plotting-room-message"
        ]
        assert len(message_events) == 1
        assert "Queued before reload drain." in message_events[0].data
        close_events = [event for event in stream.events if event.event == "pounce.worker.draining"]
        assert len(close_events) == 1
        assert close_events[0].data == "complete"
        messages = [record.getMessage() for record in caplog.records]
        assert "event=worker_draining plotting_streams_active=1" in messages
        assert "event=plotting_stream_closed plotting_streams_active=0" in messages

    asyncio.run(run())


def test_tenant_prefixed_plotting_room_id_does_not_leak_cross_realm_room() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert response.status == 302

        services = get_services()
        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        rogue = repo.get_character_by_slug(community.id, "rogue")
        interest = repo.get_wanted_ad_interest_for_character(community.id, wanted_ad.id, rogue.id)
        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_services = AppServices(
            repo,
            DemoSeed(community, charlie_user, charlie_membership, xavier),
        )
        charlie_app = create_app(debug=False, services=charlie_services)
        async with TestClient(charlie_app) as charlie_client:
            room_response = await charlie_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                headers=_FORM,
            )
            assert room_response.status == 302

        room = repo.get_plotting_room_for_wanted_interest(community.id, interest.id)
        hp = resolve_seed_persona(repo, "hp_director")
        hp_app = create_app(
            debug=False,
            services=AppServices(
                repo,
                DemoSeed(hp.community, hp.user, hp.membership, hp.character),
            ),
        )
        async with TestClient(hp_app) as hp_client:
            wrong_realm = await hp_client.get(f"/c/hp-universe/plotting/{room.id}")

        assert wrong_realm.status == 200
        assert "That planning room is not in HP Universe." in wrong_realm.text
        assert "Human UN liaison for B-24 talks: Rogue" not in wrong_realm.text
        assert "Charles opens the planning thread." not in wrong_realm.text

    asyncio.run(run())


def test_plotting_room_plan_can_turn_into_scene() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert response.status == 302

        services = get_services()
        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        rogue = repo.get_character_by_slug(community.id, "rogue")
        interest = repo.get_wanted_ad_interest_for_character(community.id, wanted_ad.id, rogue.id)
        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_services = AppServices(
            repo,
            DemoSeed(community, charlie_user, charlie_membership, xavier),
        )
        charlie_app = create_app(debug=False, services=charlie_services)
        async with TestClient(charlie_app) as charlie_client:
            room_response = await charlie_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                headers=_FORM,
            )
            assert room_response.status == 302

        room = repo.get_plotting_room_for_wanted_interest(community.id, interest.id)
        plotting_board = repo.get_board_by_slug(community.id, "plotting")
        lane_app = create_app(debug=False, services=services)
        async with TestClient(lane_app) as lane_client:
            room_page = await lane_client.get(f"/plotting/{room.id}")
            assert room_page.status == 200
            assert "Room notes" in room_page.text
            assert "Start scene" not in room_page.text

            save_plan = await lane_client.post(
                f"/plotting/{room.id}",
                body=urlencode(
                    {
                        "intent": "save_plan",
                        "status": "ready",
                        "target_board_id": plotting_board.id,
                        "next_step": "Charles opens with the invitation.",
                        "notes": "Rogue arrives with a guarded yes.",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert save_plan.status == 302

            message_response = await lane_client.post(
                f"/plotting/{room.id}",
                body=urlencode(
                    {
                        "intent": "post_message",
                        "body": "I can play Rogue guarded but curious.",
                    }
                ).encode(),
                headers={**_FORM, "HX-Request": "true"},
            )
            assert message_response.status == 200
            assert "plotting-room-composer" in message_response.text

        updated_room = repo.get_plotting_room(community.id, room.id)
        assert updated_room.status == "ready"
        assert updated_room.target_board_id == plotting_board.id
        assert updated_room.next_step == "Charles opens with the invitation."
        assert updated_room.notes == "Rogue arrives with a guarded yes."
        messages = repo.list_plotting_room_messages(community.id, room.id)
        assert len(messages) == 1
        assert messages[0].body == "I can play Rogue guarded but curious."

        outsider_services, _character_id = _outsider_services(services, prefix="roomcrasher")
        outsider_app = create_app(debug=False, services=outsider_services)
        async with TestClient(outsider_app) as outsider_client:
            denied = await outsider_client.get(f"/plotting/{room.id}")
            assert denied.status == 403

        charlie_app = create_app(debug=False, services=charlie_services)
        async with TestClient(charlie_app) as charlie_client:
            ready_detail = await charlie_client.get("/wanted/human-un-liaison-for-b24")
            assert ready_detail.status == 200
            assert "Ready for scene" in ready_detail.text
            refreshed = await charlie_client.get(f"/plotting/{room.id}")
            assert refreshed.status == 200
            assert "Rogue arrives with a guarded yes." in refreshed.text
            assert "I can play Rogue guarded but curious." in refreshed.text
            assert f'sse-connect="/plotting/{room.id}/stream"' in refreshed.text
            assert "Start scene" in refreshed.text

            stream = await charlie_client.sse(
                f"/plotting/{room.id}/stream",
                max_events=1,
                timeout=1.0,
            )
            assert stream.status == 200
            assert stream.events[0].event == "plotting-room-ready"

            scene = await charlie_client.post(
                f"/plotting/{room.id}",
                body=urlencode(
                    {
                        "intent": "start_scene",
                        "board_id": plotting_board.id,
                        "character_id": xavier.id,
                        "title": "B-24 Liaison Debrief",
                        "summary": "Charles and Rogue turn the liaison hook into a scene.",
                        "location": "Xavier Institute",
                        "timeline": "After B-24",
                        "body": "Charles sets tea down and waits for Rogue to decide.",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert scene.status == 302

            threaded_room = repo.get_plotting_room(community.id, room.id)
            assert threaded_room.status == "threaded"
            assert threaded_room.target_thread_id is not None
            created_thread = repo.get_thread(community.id, threaded_room.target_thread_id)
            assert created_thread.title == "B-24 Liaison Debrief"
            assert created_thread.summary == "Charles and Rogue turn the liaison hook into a scene."
            assert created_thread.location == "Xavier Institute"
            assert created_thread.timeline == "After B-24"
            assert {
                character.slug
                for character in repo.list_thread_participants(
                    community.id,
                    created_thread.id,
                )
            } == {"charles-xavier", "rogue"}

            threaded_page = await charlie_client.get(f"/plotting/{room.id}")
            assert threaded_page.status == 200
            assert "Open scene" in threaded_page.text
            assert f"/boards/plotting/threads/{created_thread.slug}" in threaded_page.text
            assert "Start scene" not in threaded_page.text

            threaded_detail = await charlie_client.get("/wanted/human-un-liaison-for-b24")
            assert threaded_detail.status == 200
            assert "Scene started" in threaded_detail.text
            assert "Open scene" in threaded_detail.text
            assert f"/boards/plotting/threads/{created_thread.slug}" in threaded_detail.text

        lane_inbox = services.notifications()
        assert any(item.label == "Scene started" for item in lane_inbox.items)

    asyncio.run(run())


def test_plotting_room_scene_handoff_rolls_back_on_attach_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert response.status == 302

        services = get_services()
        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        rogue = repo.get_character_by_slug(community.id, "rogue")
        interest = repo.get_wanted_ad_interest_for_character(community.id, wanted_ad.id, rogue.id)
        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_services = AppServices(
            repo,
            DemoSeed(community, charlie_user, charlie_membership, xavier),
        )
        charlie_app = create_app(debug=False, services=charlie_services)
        async with TestClient(charlie_app) as charlie_client:
            room_response = await charlie_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                headers=_FORM,
            )
            assert room_response.status == 302

        room = repo.get_plotting_room_for_wanted_interest(community.id, interest.id)
        plotting_board = repo.get_board_by_slug(community.id, "plotting")

        def fail_attach(*_args, **_kwargs):
            raise RuntimeError("forced attach failure")

        monkeypatch.setattr(repo, "attach_plotting_room_thread", fail_attach)
        with pytest.raises(RuntimeError, match="forced attach failure"):
            charlie_services.create_thread_from_plotting_room(
                room.id,
                board_id=plotting_board.id,
                character_id=xavier.id,
                title="Rollback Liaison Debrief",
                summary="This scene should not persist.",
                location="Xavier Institute",
                timeline="After B-24",
                body="Charles starts a scene that should roll back.",
            )

        rolled_back_room = repo.get_plotting_room(community.id, room.id)
        assert rolled_back_room.target_thread_id is None
        assert rolled_back_room.status == "brainstorming"
        assert all(
            thread.title != "Rollback Liaison Debrief"
            for thread in repo.list_threads(community.id, plotting_board.id)
        )

    asyncio.run(run())


def test_plotting_room_notifications_do_not_leak_to_non_participants() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert response.status == 302

        services = get_services()
        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        rogue = repo.get_character_by_slug(community.id, "rogue")
        interest = repo.get_wanted_ad_interest_for_character(community.id, wanted_ad.id, rogue.id)
        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_services = AppServices(
            repo,
            DemoSeed(community, charlie_user, charlie_membership, xavier),
        )
        charlie_app = create_app(debug=False, services=charlie_services)
        async with TestClient(charlie_app) as charlie_client:
            room_response = await charlie_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                headers=_FORM,
            )
            assert room_response.status == 302

        room = repo.get_plotting_room_for_wanted_interest(community.id, interest.id)
        outsider_services, _character_id = _outsider_services(services, prefix="room-notify")
        notification = repo.create_notification(
            community.id,
            outsider_services.seed.membership.id,
            kind="plotting_room_created",
            plotting_room_id=room.id,
            actor_membership_id=charlie_membership.id,
            actor_character_id=xavier.id,
        )
        outsider_app = create_app(debug=False, services=outsider_services)
        async with TestClient(outsider_app) as outsider_client:
            inbox = await outsider_client.get("/notifications")
            open_attempt = await outsider_client.post(
                "/notifications",
                body=urlencode(
                    {
                        "_action": "open",
                        "notification_id": str(notification.id),
                    }
                ).encode(),
                headers=_FORM,
            )
            room_attempt = await outsider_client.get(f"/plotting/{room.id}")

        assert outsider_services.viewer().unread_notification_count == 0
        assert outsider_services.notifications().unread_count == 0
        assert inbox.status == 200
        assert "No notifications are waiting on you." in inbox.text
        assert "Find hooks" not in inbox.text
        assert 'href="/characters/room-notify-face#plotter"' not in inbox.text
        assert room.title not in inbox.text
        assert "Human UN liaison for B-24 talks: Rogue" not in inbox.text
        assert open_attempt.status == 404
        assert room_attempt.status == 403

    asyncio.run(run())


def test_faceless_writer_does_not_count_unowned_character_notifications() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        user = repo.create_user("faceless-notify@example.com", "hash")
        faceless = repo.create_membership(
            community.id,
            user.id,
            role.id,
            "facelessnotify",
            "Faceless Notify",
        )
        staff = resolve_seed_persona(repo, "xmen_staff")
        assert staff.character is not None
        target = repo.get_character_by_slug(community.id, "rogue")
        repo.create_notification(
            community.id,
            faceless.id,
            kind="application_submitted",
            character_id=target.id,
            actor_membership_id=staff.membership.id,
            actor_character_id=staff.character.id,
        )
        faceless_services = AppServices(repo, DemoSeed(community, user, faceless, None))
        faceless_app = create_app(debug=False, services=faceless_services)

        async with TestClient(faceless_app) as client:
            home = await client.get("/")
            inbox = await client.get("/notifications")

        assert faceless_services.viewer().current_character is None
        assert faceless_services.viewer().unread_notification_count == 0
        assert faceless_services.notifications().unread_count == 0
        assert home.status == 200
        assert "elbysodic-identity-menu__summary-badge" not in home.text
        assert inbox.status == 200
        assert "No notifications are waiting on you." in inbox.text
        assert "Rogue" not in inbox.text

    asyncio.run(run())


def test_faceless_identity_option_hides_unowned_character_notification_count() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        active = services.seed
        faceless_community = repo.create_community(
            "faceless-option-notify",
            "Faceless Option Notify",
        )
        role = repo.create_role(faceless_community.id, "member", "Member")
        faceless = repo.create_membership(
            faceless_community.id,
            active.user.id,
            role.id,
            "faceless-option",
            "Faceless Option",
        )
        actor_user = repo.create_user("faceless-option-actor@example.com", "hash")
        actor = repo.create_membership(
            faceless_community.id,
            actor_user.id,
            role.id,
            "faceless-option-actor",
            "Faceless Option Actor",
        )
        target = repo.create_character(
            faceless_community.id,
            actor.id,
            "faceless-option-target",
            "Faceless Option Target",
        )
        repo.create_notification(
            faceless_community.id,
            faceless.id,
            kind="application_submitted",
            character_id=target.id,
            actor_membership_id=actor.id,
            actor_character_id=target.id,
        )
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            home = await client.get("/")

        viewer = services.viewer()
        option = next(item for item in viewer.identity_options if item.membership.id == faceless.id)
        option_match = re.search(
            r'<button class="[^"]*elbysodic-identity-switcher__option[^"]*"'
            r"[^>]*>\s*<span>\s*<strong>Faceless Option Notify</strong>.*?</button>",
            home.text,
            re.DOTALL,
        )

        assert option.current_character is None
        assert option.unread_notification_count == 0
        assert home.status == 200
        assert option_match is not None
        assert "<b>" not in option_match.group(0)
        assert "Faceless Option Target" not in home.text

    asyncio.run(run())


def test_inactive_membership_notifications_do_not_render_identity_option_counts() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        active = services.seed
        inactive_community = repo.create_community("inactive-notify", "Inactive Notify")
        role = repo.create_role(inactive_community.id, "member", "Member")
        inactive = repo.create_membership(
            inactive_community.id,
            active.user.id,
            role.id,
            "inactive-notify",
            "Inactive Notify",
        )
        repo.connection.execute(
            "UPDATE community_memberships SET is_active = 0 WHERE community_id = ? AND id = ?",
            (inactive_community.id, inactive.id),
        )
        repo.connection.commit()
        inactive = repo.get_membership(inactive_community.id, inactive.id)
        target = repo.get_character_by_slug(active.community.id, "rogue")
        repo.create_notification(
            active.community.id,
            active.membership.id,
            kind="application_accepted",
            character_id=target.id,
            actor_membership_id=active.membership.id,
            actor_character_id=target.id,
        )
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            home = await client.get("/")

        viewer = services.viewer()
        assert not inactive.is_active
        assert viewer.unread_notification_count == 1
        assert all(option.membership.id != inactive.id for option in viewer.identity_options)
        assert home.status == 200
        assert "Inactive Notify" not in home.text

    asyncio.run(run())


def test_thread_cards_jump_to_first_unread_then_latest() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        membership = services.seed.membership
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("jump@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "jumpwriter",
            "Jump Writer",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "jump-face",
            "Jump Face",
        )
        board = repo.get_board_by_slug(community.id, "plotting")
        thread = repo.get_thread_by_slug(community.id, board.id, "open-thread-roster")
        repo.mark_thread_read(
            community.id,
            thread.id,
            membership.id,
            read_at="2026-01-01T00:00:00+00:00",
        )
        first_unread = repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "First unread beat.",
        )
        latest_unread = repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "Latest unread beat.",
        )
        repo.connection.execute(
            """
            UPDATE posts
            SET created_at = '2025-12-31T23:59:00+00:00',
                updated_at = '2025-12-31T23:59:00+00:00'
            WHERE community_id = ? AND thread_id = ? AND id NOT IN (?, ?)
            """,
            (community.id, thread.id, first_unread.id, latest_unread.id),
        )
        repo.connection.execute(
            """
            UPDATE posts
            SET created_at = '2026-01-01T00:00:01+00:00',
                updated_at = '2026-01-01T00:00:01+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, first_unread.id),
        )
        repo.connection.execute(
            """
            UPDATE posts
            SET created_at = '2026-01-01T00:00:02+00:00',
                updated_at = '2026-01-01T00:00:02+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, latest_unread.id),
        )
        repo.connection.execute(
            """
            UPDATE threads
            SET updated_at = '2026-01-01T00:00:02+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, thread.id),
        )
        repo.connection.commit()

        async with TestClient(app) as client:
            board_response = await client.get("/boards/plotting")
            assert board_response.status == 200
            assert "First unread" in board_response.text
            assert (
                f"/boards/plotting/threads/open-thread-roster#post-{first_unread.post_number}"
                in board_response.text
            )
            assert (
                f"/boards/plotting/threads/open-thread-roster#post-{latest_unread.post_number}"
                not in board_response.text
            )

            thread_response = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread_response.status == 200

            board_after_read = await client.get("/boards/plotting")
            assert board_after_read.status == 200
            assert "Jump to latest" in board_after_read.text
            assert (
                f"/boards/plotting/threads/open-thread-roster#post-{latest_unread.post_number}"
                in board_after_read.text
            )

    asyncio.run(run())


def test_board_page_next_unread_jumps_to_first_unread_post() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        membership = services.seed.membership
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("board-next@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "boardnext",
            "Board Next",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "board-next-face",
            "Board Next Face",
        )
        board = repo.create_board(community.id, "board-next", "Board Next")
        thread = repo.create_thread(
            community.id,
            board.id,
            outsider.id,
            "board-next-thread",
            "Board Next Thread",
        )
        repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "The board-level thread exists.",
        )
        repo.connection.execute(
            """
            UPDATE posts
            SET created_at = '2026-01-01T00:00:00+00:00',
                updated_at = '2026-01-01T00:00:00+00:00'
            WHERE community_id = ? AND thread_id = ?
            """,
            (community.id, thread.id),
        )
        repo.connection.execute(
            """
            UPDATE threads
            SET updated_at = '2026-01-01T00:00:00+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, thread.id),
        )
        repo.connection.commit()
        repo.mark_thread_read(
            community.id,
            thread.id,
            membership.id,
            read_at="2026-01-01T00:00:00+00:00",
        )
        post = repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "The board-level next unread target.",
        )
        repo.connection.execute(
            """
            UPDATE posts
            SET created_at = '2026-01-01T00:00:01+00:00',
                updated_at = '2026-01-01T00:00:01+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, post.id),
        )
        repo.connection.execute(
            """
            UPDATE threads
            SET updated_at = '2026-01-01T00:00:01+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, thread.id),
        )
        repo.connection.commit()

        async with TestClient(app) as client:
            page = await client.get("/boards/board-next")
            assert page.status == 200
            assert "Next unread here" in page.text
            assert (
                f"/boards/board-next/threads/board-next-thread#post-{post.post_number}" in page.text
            )

            thread_response = await client.get("/boards/board-next/threads/board-next-thread")
            assert thread_response.status == 200

            caught_up = await client.get("/boards/board-next")
            assert "Next unread" not in caught_up.text

    asyncio.run(run())


def test_reading_thread_clears_unread_marker_for_membership() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            board_before = await client.get("/boards/plotting")
            assert "new replies" in board_before.text

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200

            board_after = await client.get("/boards/plotting")
            assert ">new replies<" not in board_after.text

    asyncio.run(run())


def test_thread_watch_toggle_controls_thread_notifications() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200
            assert "chirpui-thread-reader-layout" in thread.text
            assert "Watch thread" in thread.text

            watched = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=b"intent=watch",
                headers=_FORM,
            )
            assert watched.status == 302

            watched_thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert "watching" in watched_thread.text
            assert "Unwatch thread" in watched_thread.text

            unwatched = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=b"intent=unwatch",
                headers=_FORM,
            )
            assert unwatched.status == 302

            unwatched_thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert "Watch thread" in unwatched_thread.text
            assert "Unwatch thread" not in unwatched_thread.text

    asyncio.run(run())


def test_notifications_track_watched_thread_replies_and_open_read_state() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        services.watch_thread("plotting", "open-thread-roster")
        outsider_services, outsider_character_id = _outsider_services(services, prefix="notify")
        post = outsider_services.reply_to_thread(
            "plotting",
            "open-thread-roster",
            outsider_character_id,
            "A watched reply arrives.",
        )

        async with TestClient(app) as client:
            index = await client.get("/c/x-men-apocalypse")
            assert index.status == 200
            assert "Notifications" in index.text
            assert "elbysodic-sidebar-count" in index.text

            notifications = await client.get("/notifications")
            assert notifications.status == 200
            assert "Watched thread" in notifications.text
            assert "A watched reply arrives." in notifications.text
            assert "Notify Face" in notifications.text
            assert "new" in notifications.text
            assert 'name="_action" value="mark_all_read"' in notifications.text
            assert 'name="_action" value="open"' in notifications.text

            item = services.notifications().items[0]
            marked_all = await client.post(
                "/notifications",
                body=b"_action=mark_all_read",
                headers=_FORM,
            )
            assert marked_all.status == 302
            assert (
                services.repo.get_notification(
                    services.seed.community.id,
                    item.notification.id,
                ).read_at
                is not None
            )

            opened = await client.post(
                "/notifications",
                body=f"_action=open&notification_id={item.notification.id}".encode(),
                headers=_FORM,
            )
            assert opened.status == 302
            assert dict(opened.headers)["location"] == (
                f"/boards/plotting/threads/open-thread-roster#post-{post.post_number}"
            )
            assert services.viewer().unread_notification_count == 0

    asyncio.run(run())


def test_reply_notification_failure_rolls_back_post(monkeypatch: pytest.MonkeyPatch) -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    services.watch_thread("plotting", "open-thread-roster")
    board = repo.get_board_by_slug(services.seed.community.id, "plotting")
    thread = repo.get_thread_by_slug(
        services.seed.community.id,
        board.id,
        "open-thread-roster",
    )
    before_posts = repo.list_posts(services.seed.community.id, thread.id)
    outsider_services, outsider_character_id = _outsider_services(
        services,
        prefix="rollback-notify",
    )

    def fail_create_notification(*args: object, **kwargs: object) -> object:
        raise RuntimeError("notification fanout failed")

    monkeypatch.setattr(repo, "create_notification", fail_create_notification)
    with pytest.raises(RuntimeError, match="notification fanout failed"):
        outsider_services.reply_to_thread(
            "plotting",
            "open-thread-roster",
            outsider_character_id,
            "This reply should roll back with notification fanout.",
        )

    after_posts = repo.list_posts(services.seed.community.id, thread.id)

    assert [post.id for post in after_posts] == [post.id for post in before_posts]
    assert (
        repo.count_unread_notifications(
            services.seed.community.id,
            services.seed.membership.id,
        )
        == 0
    )


def test_notification_inbox_limit_applies_after_visibility_filtering() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        viewer = services.viewer()
        assert viewer.current_character is not None
        outsider_services, outsider_character_id = _outsider_services(
            services,
            prefix="notifywindow",
        )
        visible_post = outsider_services.reply_to_thread(
            "plotting",
            "open-thread-roster",
            outsider_character_id,
            "A visible reply survives hidden notification noise.",
        )
        repo.create_notification(
            community.id,
            viewer.membership.id,
            kind="thread_reply",
            thread_id=visible_post.thread_id,
            post_id=visible_post.id,
            actor_membership_id=outsider_services.seed.membership.id,
            actor_character_id=outsider_character_id,
        )
        private_board = repo.create_board(
            community.id,
            "notify-window-private",
            "Notify Window Private",
            is_private=True,
        )
        private_thread = repo.create_thread(
            community.id,
            private_board.id,
            outsider_character_id,
            "notify-window-private-thread",
            "Notify window private thread",
        )
        for index in range(55):
            private_post = repo.create_post(
                community.id,
                private_thread.id,
                outsider_character_id,
                f"Hidden private notification {index}",
            )
            repo.create_notification(
                community.id,
                viewer.membership.id,
                kind="thread_reply",
                thread_id=private_thread.id,
                post_id=private_post.id,
                actor_membership_id=outsider_services.seed.membership.id,
                actor_character_id=outsider_character_id,
            )

        inbox = services.notification_center(limit=1).inbox
        async with TestClient(app) as client:
            response = await client.get("/notifications")

        assert services.viewer().unread_notification_count == 1
        assert inbox.unread_count == 1
        assert [item.post.post.id for item in inbox.items if item.post is not None] == [
            visible_post.id
        ]
        assert response.status == 200
        assert "A visible reply survives hidden notification noise." in response.text
        assert "Hidden private notification" not in response.text
        assert "No notifications are waiting on you." not in response.text

    asyncio.run(run())


def test_mentions_notify_character_owner_without_thread_watch() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        outsider_services, outsider_character_id = _outsider_services(services, prefix="mention")
        outsider_services.reply_to_thread(
            "plotting",
            "open-thread-roster",
            outsider_character_id,
            "Hey @Rogue, the plotting board needs you.",
        )

        async with TestClient(app) as client:
            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200
            assert 'href="/characters/rogue"' in thread.text
            assert 'data-mention-kind="character"' in thread.text

            notifications = await client.get("/notifications")
            assert notifications.status == 200
            assert "Mention" in notifications.text
            assert "Hey @Rogue, the plotting board needs you." in notifications.text
            assert "Mention Face" in notifications.text

    asyncio.run(run())


def test_writer_mentions_notify_membership_without_thread_watch() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        outsider_services, outsider_character_id = _outsider_services(
            services,
            prefix="writermention",
        )
        outsider_services.reply_to_thread(
            "plotting",
            "open-thread-roster",
            outsider_character_id,
            "Looping in @starlane for the OOC planning bit.",
        )

        async with TestClient(app) as client:
            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200
            assert 'href="/members/starlane"' in thread.text
            assert 'data-mention-kind="writer"' in thread.text

            notifications = await client.get("/notifications")
            assert notifications.status == 200
            assert "Mention" in notifications.text
            assert "Looping in @starlane for the OOC planning bit." in notifications.text
            assert "Writermention Face" in notifications.text

    asyncio.run(run())


def test_members_directory_and_profile_show_visible_community_cast() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        viewer = services.viewer()
        character = viewer.current_character
        assert character is not None
        private_board = repo.create_board(
            community.id,
            "private-lab",
            "Private Lab",
            is_private=True,
        )
        private_thread = repo.create_thread(
            community.id,
            private_board.id,
            character.id,
            "private-notes",
            "Private notes",
        )
        repo.create_post(
            community.id,
            private_thread.id,
            character.id,
            "Private activity should stay private.",
        )
        role = repo.get_role_by_slug(community.id, "member")
        inactive_user = repo.create_user("retired@example.com", "hash")
        inactive_membership = repo.create_membership(
            community.id,
            inactive_user.id,
            role.id,
            "retiredlane",
            "Retired Lane",
        )
        repo.create_character(
            community.id,
            inactive_membership.id,
            "retired-face",
            "Retired Face",
            summary="Retired profile copy should not render.",
        )
        repo.connection.execute(
            "UPDATE community_memberships SET is_active = 0 WHERE community_id = ? AND id = ?",
            (community.id, inactive_membership.id),
        )
        repo.connection.commit()

        async with TestClient(app) as client:
            directory = await client.get("/members")
            assert directory.status == 200
            assert "Members" in directory.text
            assert "Lane" in directory.text
            assert "@starlane" in directory.text
            assert "Known for" in directory.text
            assert "Rogue" in directory.text
            assert "/members/starlane" in directory.text
            assert "Private activity should stay private." not in directory.text
            assert "Retired Lane" not in directory.text
            assert "Retired Face" not in directory.text

            profile = await client.get("/members/starlane")
            assert profile.status == 200
            assert "Featured face: Rogue" in profile.text
            assert "Known For" in profile.text
            assert "Current Roles" in profile.text
            assert "Collaborators" in profile.text
            assert "Visible posts" in profile.text
            assert "Open thread roster" in profile.text
            assert "/characters/rogue" in profile.text
            assert "Private notes" not in profile.text
            assert "Private activity should stay private." not in profile.text

            missing = await client.get("/members/nope")
            assert missing.status == 404
            inactive_member = await client.get("/members/retiredlane")
            assert inactive_member.status == 404
            inactive_character = await client.get("/characters/retired-face")
            assert inactive_character.status == 200
            assert "That face is not in X-Men Apocalypse." in inactive_character.text
            assert "Retired profile copy should not render." not in inactive_character.text

    asyncio.run(run())


def test_external_character_profile_links_to_owning_member_without_edit_controls() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        outsider_services, outsider_character_id = _outsider_services(
            services,
            prefix="castmate",
        )
        assert outsider_services is not None
        assert outsider_character_id > 0

        async with TestClient(app) as client:
            profile = await client.get("/characters/castmate-face")
            assert profile.status == 200
            assert "Castmate Face" in profile.text
            assert "/members/castmate" in profile.text
            assert "Edit character" not in profile.text
            assert "Set current face" not in profile.text
            assert "View writer" in profile.text

    asyncio.run(run())


def test_thread_page_links_previous_next_and_next_unread_threads() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        membership = services.seed.membership
        viewer = services.viewer()
        character = viewer.current_character
        assert character is not None
        board = repo.create_board(community.id, "navigation", "Navigation")
        newer = repo.create_thread(community.id, board.id, character.id, "newer", "Newer thread")
        current = repo.create_thread(
            community.id, board.id, character.id, "middle", "Middle thread"
        )
        older = repo.create_thread(community.id, board.id, character.id, "older", "Older thread")
        repo.create_post(community.id, newer.id, character.id, "Newer post.")
        repo.create_post(community.id, current.id, character.id, "Middle post.")
        older_post = repo.create_post(community.id, older.id, character.id, "Older post.")
        repo.connection.execute(
            """
            UPDATE threads
            SET updated_at = CASE id
                WHEN ? THEN '2026-01-01T00:03:00+00:00'
                WHEN ? THEN '2026-01-01T00:02:00+00:00'
                WHEN ? THEN '2026-01-01T00:01:00+00:00'
                ELSE updated_at
            END
            WHERE community_id = ? AND board_id = ?
            """,
            (newer.id, current.id, older.id, community.id, board.id),
        )
        repo.connection.commit()
        repo.mark_thread_read(community.id, newer.id, membership.id)
        role = repo.get_role_by_slug(community.id, "member")
        attention_user = repo.create_user("nav-attention@example.com", "hash")
        attention_membership = repo.create_membership(
            community.id,
            attention_user.id,
            role.id,
            "navattention",
            "Nav Attention",
        )
        attention_character = repo.create_character(
            community.id,
            attention_membership.id,
            "nav-attention-face",
            "Nav Attention Face",
        )
        repo.create_post(
            community.id,
            newer.id,
            attention_character.id,
            "A nearby scene needs a reply.",
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/navigation/threads/middle")
            assert page.status == 200
            assert "Scenes here" in page.text
            assert "Scene continuation" in page.text
            assert "Previous unreplied" in page.text
            assert "Newer thread" in page.text
            assert "/boards/navigation/threads/newer" in page.text
            assert "Older thread" in page.text
            assert "Next unread" in page.text
            assert f"/boards/navigation/threads/older#post-{older_post.post_number}" in page.text

    asyncio.run(run())


def test_thread_page_bottom_next_unread_uses_visible_community_queue() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        membership = services.seed.membership
        viewer = services.viewer()
        character = viewer.current_character
        assert character is not None
        for existing_thread in repo.list_threads(community.id):
            repo.mark_thread_read(community.id, existing_thread.id, membership.id)
        current_board = repo.create_board(community.id, "current-nav", "Current Nav")
        unread_board = repo.create_board(community.id, "unread-nav", "Unread Nav")
        current = repo.create_thread(
            community.id,
            current_board.id,
            character.id,
            "current-scene",
            "Current scene",
        )
        unread = repo.create_thread(
            community.id,
            unread_board.id,
            character.id,
            "elsewhere-scene",
            "Elsewhere scene",
        )
        repo.create_post(community.id, current.id, character.id, "Current post.")
        unread_post = repo.create_post(
            community.id,
            unread.id,
            character.id,
            "Unread elsewhere.",
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/current-nav/threads/current-scene")
            assert page.status == 200
            assert "Next unread" in page.text
            assert (
                f"/boards/unread-nav/threads/elsewhere-scene#post-{unread_post.post_number}"
                in page.text
            )

    asyncio.run(run())


def test_board_thread_filters_use_roster_participation() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("outsider@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "outsider",
            "Outsider",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "outsider-face",
            "Outsider Face",
        )
        board = repo.get_board_by_slug(community.id, "plotting")
        outside_thread = repo.create_thread(
            community.id,
            board.id,
            outsider.id,
            "outsider-plot",
            "Outsider plot",
        )
        repo.create_post(
            community.id,
            outside_thread.id,
            outsider.id,
            "A visible thread from another writer.",
        )

        async with TestClient(app) as client:
            all_threads = await client.get("/boards/plotting")
            assert all_threads.status == 200
            assert "Outsider plot" in all_threads.text
            assert "?filter=mine" in all_threads.text
            assert "?filter=unread" in all_threads.text
            assert "?filter=attention" in all_threads.text

            mine = await client.get("/boards/plotting?filter=mine")
            assert mine.status == 200
            assert "Open thread roster" in mine.text
            assert "Outsider plot" not in mine.text
            assert "mine" in mine.text

            pinned = await client.get("/boards/plotting?filter=pinned")
            assert pinned.status == 200
            assert "No pinned threads here." in pinned.text
            assert "elbysodic-board-empty" in pinned.text

            locked = await client.get("/boards/announcements?filter=locked")
            assert locked.status == 200
            assert "Welcome to the rebuild" in locked.text
            assert "locked" in locked.text

    asyncio.run(run())


def test_attention_surfaces_threads_where_someone_else_posted_last() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("attention@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "attention",
            "Attention",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "attention-face",
            "Attention Face",
        )
        board = repo.get_board_by_slug(community.id, "plotting")
        thread = repo.get_thread_by_slug(community.id, board.id, "open-thread-roster")
        repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "A different writer nudges the plot forward.",
        )

        async with TestClient(app) as client:
            desk = await client.get("/c/x-men-apocalypse/desk")
            assert desk.status == 200
            assert "Needs reply" in desk.text
            assert "Open thread roster" in desk.text
            assert "Attention Face" in desk.text
            assert "A different writer nudges the plot forward." in desk.text

            board_attention = await client.get("/boards/plotting?filter=attention")
            assert board_attention.status == 200
            assert "Open thread roster" in board_attention.text
            assert "needs reply" in board_attention.text

            thread_response = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread_response.status == 200

            cleared = await client.get("/boards/plotting?filter=attention")
            assert cleared.status == 200
            assert "No scene turns need your roster here." in cleared.text
            assert "elbysodic-board-empty" in cleared.text
            locations = await client.get("/locations")
            assert "Open thread roster" not in locations.text

            desk_after_read = await client.get("/c/x-men-apocalypse/desk")
            assert "Queue clear" in desk_after_read.text or "caught up" in desk_after_read.text

    asyncio.run(run())


def test_my_threads_tracks_obligations_after_threads_are_read() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("obligation@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "obligation",
            "Obligation",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "obligation-face",
            "Obligation Face",
        )
        board = repo.get_board_by_slug(community.id, "plotting")
        thread = repo.get_thread_by_slug(community.id, board.id, "open-thread-roster")
        repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "A different writer puts the ball back in your court.",
        )

        async with TestClient(app) as client:
            read_thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert read_thread.status == 200

            dashboard = await client.get("/my/threads?character=all")
            assert dashboard.status == 200
            assert "My threads" in dashboard.text
            assert "Needs reply" in dashboard.text
            assert "Waiting on others" in dashboard.text
            assert "Started by me" in dashboard.text
            assert "All participated" in dashboard.text
            assert "Open thread roster" in dashboard.text
            assert "Obligation Face" in dashboard.text
            assert "elbysodic-thread-card__poster" in dashboard.text
            assert "elbysodic-scene-cast--stacked" in dashboard.text
            assert "elbysodic-thread-card__metrics" in dashboard.text
            assert "elbysodic-queue-history" in dashboard.text
            assert "needs reply" in dashboard.text
            assert "Sentinel drill after midnight" in dashboard.text
            assert "waiting" in dashboard.text
            assert "Welcome to the rebuild" not in dashboard.text
            assert "/boards/plotting/threads/open-thread-roster#post-" in dashboard.text

    asyncio.run(run())


def test_my_threads_defaults_to_current_face_lens() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            dashboard = await client.get("/my/threads")
            whole_roster = await client.get("/my/threads?character=all")

        assert dashboard.status == 200
        assert "My threads" in dashboard.text
        assert "Active face first" in dashboard.text
        assert "Queue lens: active face" in dashboard.text
        assert "Rogue's writing lane" not in dashboard.text
        assert 'href="/my/threads?character=all"' in dashboard.text
        assert "Open thread roster" in dashboard.text
        assert "Welcome to the rebuild" not in dashboard.text
        assert whole_roster.status == 200
        assert "My threads" in whole_roster.text
        assert "Queue lens: whole roster" in whole_roster.text

    asyncio.run(run())


def test_locked_seed_thread_suppresses_reply_composer() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )

        async with TestClient(app) as client:
            thread = await client.get("/boards/announcements/threads/welcome-to-the-rebuild")
            assert thread.status == 200
            assert "locked" in thread.text
            assert "Thread locked" in thread.text
            assert "Post reply" not in thread.text

            response = await client.post(
                "/boards/announcements/threads/welcome-to-the-rebuild",
                body=f"character_id={storm.id}&body=Staff+update.".encode(),
                headers=_FORM,
            )
            assert response.status == 200
            assert "cannot reply" in response.text

    asyncio.run(run())


def test_identity_route_changes_default_character_face() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )

        async with TestClient(app) as client:
            response = await client.post(
                "/identity",
                body=f"character_id={storm.id}&next=/".encode(),
                headers=_FORM,
            )
            assert response.status == 302

            index = await client.get("/c/x-men-apocalypse")
            assert "playing as Storm" in index.text

    asyncio.run(run())


def test_theme_stylesheet_is_loaded_and_theme_aware() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            index = await client.get("/c/x-men-apocalypse")
            assert index.status == 200
            assert "/elbysodic-static/elbysodic-theme.css" in index.text

            stylesheet_text = await _stylesheet_text_with_imports(client)
            assert '[data-theme="light"]' in stylesheet_text
            assert '[data-theme="system"]' in stylesheet_text
            assert ".elbysodic-realm-cast-card__copy" in stylesheet_text
            assert "padding-inline-start: 0.15rem;" in stylesheet_text

    asyncio.run(run())


def test_character_roster_and_profiles_are_community_scoped() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            roster = await client.get("/characters")
            assert roster.status == 200
            assert "Your roster" in roster.text
            assert "Rogue" in roster.text
            assert "Storm" in roster.text
            assert "Magneto" in roster.text

            profile = await client.get("/characters/rogue")
            assert profile.status == 200
            assert "Power-stealing brawler with a careful heart." in profile.text
            assert "Sentinel drill after midnight" in profile.text
            assert "#post-" in profile.text

    asyncio.run(run())


def test_character_activity_center_tracks_identity_specific_threads() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            roster = await client.get("/characters")
            assert roster.status == 200
            assert "Needs Rogue" in roster.text
            assert "Waiting on Magneto" in roster.text
            assert "/my/threads?character=rogue" in roster.text

            profile = await client.get("/characters/rogue")
            assert profile.status == 200
            assert "Write as Rogue" in profile.text
            assert "active-face defaults on" in profile.text
            assert "Reply as Rogue" in profile.text
            assert "Find play for Rogue" not in _page_content(profile.text)
            assert "Casting as Rogue" not in _page_content(profile.text)
            assert "Browse wanted" not in _page_content(profile.text)
            assert "Scenes" in profile.text
            assert "Open filtered queue" in profile.text
            assert "Open thread roster" in profile.text
            assert "Sentinel drill after midnight" in profile.text
            assert "needs reply" in profile.text
            assert "waiting" in profile.text

            filtered = await client.get("/my/threads?character=rogue")
            assert filtered.status == 200
            assert "Character threads" in filtered.text
            assert "Rogue · 1" in filtered.text
            assert "Open thread roster" in filtered.text
            assert "Sentinel drill after midnight" in filtered.text
            assert "Welcome to the rebuild" not in filtered.text

    asyncio.run(run())


def test_character_roster_can_create_new_default_character() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/characters",
                body=(
                    b"_action=create_character"
                    b"&name=Jean+Grey&summary=Telepath+with+a+plot-problem.&make_default=on"
                ),
                headers=_FORM,
            )
            assert response.status == 302

            profile = await client.get("/characters/jean-grey")
            assert profile.status == 200
            assert "Jean Grey" in profile.text
            assert "Telepath with a plot-problem." in profile.text

            index = await client.get("/c/x-men-apocalypse")
            assert "playing as Jean Grey" in index.text

    asyncio.run(run())


def test_character_roster_create_validation_error_rerenders_form_block() -> None:
    """The create_character page action negotiates error rendering (#249).

    A plain POST keeps the legacy behavior (200 full-page re-render with the
    error and submitted values); an htmx POST gets a 422 ValidationError that
    re-renders only the ``character_create_form`` block.
    """

    async def run() -> None:
        app = _app()
        payload = {
            "_action": "create_character",
            "name": "",
            "summary": "A face with no name.",
        }

        async with TestClient(app) as client:
            plain = await client.post(
                "/characters",
                body=urlencode(payload).encode(),
                headers=_FORM,
            )
            assert plain.status == 200
            assert "chirpui-field__error" in plain.text
            assert "A face with no name." in plain.text
            assert "Your roster" in plain.text

            htmx = await client.post(
                "/characters",
                body=urlencode(payload).encode(),
                headers={**_FORM, "HX-Request": "true"},
            )
            assert htmx.status == 422
            assert 'id="new-character"' in htmx.text
            assert "chirpui-field__error" in htmx.text
            assert "A face with no name." in htmx.text
            assert "<html" not in htmx.text.lower()

    asyncio.run(run())


def test_character_profile_can_set_current_face() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            pending_profile = await client.get("/characters/storm")
            assert pending_profile.status == 200
            assert "set current for discovery" in pending_profile.text
            assert "Make Storm current" in pending_profile.text

            response = await client.post(
                "/characters/storm",
                body=b"intent=set_default",
                headers=_FORM,
            )
            assert response.status == 302
            assert dict(response.headers)["location"] == "/characters/storm"

            profile = await client.get("/characters/storm")
            assert "current" in profile.text
            assert "active-face defaults on" in profile.text
            assert "Find play for Storm" not in _page_content(profile.text)

            index = await client.get("/c/x-men-apocalypse")
            assert "playing as Storm" in index.text

    asyncio.run(run())


def test_character_profile_can_edit_owned_character() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.post(
                "/characters/rogue",
                body=(
                    b"intent=save"
                    b"&name=Rogue+Prime"
                    b"&avatar_url=https%3A%2F%2Fexample.test%2Frogue.png"
                    b"&accent_source=custom"
                    b"&accent_color=%2379a889"
                    b"&post_profile_variant=poster"
                    b"&post_accent_style=line"
                    b"&post_border_style=double"
                    b"&post_title_style=mono"
                    b"&post_density=compact"
                    b"&summary=Still+carrying+the+whole+plot."
                ),
                headers=_FORM,
            )
            assert response.status == 302
            assert dict(response.headers)["location"] == "/characters/rogue-prime"

            profile = await client.get("/characters/rogue-prime")
            assert profile.status == 200
            assert "Rogue Prime" in profile.text
            assert "Still carrying the whole plot." in profile.text
            assert "https://example.test/rogue.png" in profile.text
            assert "Post preview" in profile.text
            assert "Custom accent" in profile.text

            thread = await client.get("/boards/danger-room/threads/sentinel-drill")
            assert "Rogue Prime" in thread.text
            assert "elbysodic-post-profile--poster" in thread.text
            assert "elbysodic-post-accent--line" in thread.text
            assert "elbysodic-post-border--double" in thread.text
            assert "elbysodic-post-title--mono" in thread.text
            assert "elbysodic-post-density--compact" in thread.text
            assert "Rogue drops from the observation gantry" in thread.text

    asyncio.run(run())


def test_character_style_preset_applies_approved_post_tokens() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.post(
                "/characters",
                body=urlencode(
                    {
                        "_action": "create_character",
                        "name": "Jean Grey",
                        "summary": "Telepath with a plot-problem.",
                        "post_style_preset": "faction-dossier",
                    }
                ).encode(),
                headers=_FORM,
            )

            assert response.status == 302
            profile = await client.get("/characters/jean-grey")
            assert profile.status == 200
            assert "Post preview" in profile.text
            assert 'value="crest" selected' in profile.text
            assert 'value="block" selected' in profile.text
            assert 'value="double" selected' in profile.text
            assert 'value="mono" selected' in profile.text
            assert 'value="compact" selected' in profile.text

    asyncio.run(run())


def test_post_shell_inherits_identity_accent_from_facet_group() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            thread = await client.get("/boards/danger-room/threads/moonlight-skirmish")
            roster = await client.get("/characters")
            profile = await client.get("/characters/storm")

            assert thread.status == 200
            assert 'style="--elbysodic-character-accent: #60a5fa"' in thread.text
            assert 'style="--elbysodic-character-accent: #79a889"' in thread.text
            assert roster.status == 200
            assert "Affiliation: X-Men" in roster.text
            assert 'style="--elbysodic-character-accent: #60a5fa"' in roster.text
            assert profile.status == 200
            assert "Inherited accent" in profile.text
            assert "Affiliation: X-Men" in profile.text

    asyncio.run(run())


def test_thread_reader_uses_editorial_poster_wrap_without_losing_post_contracts() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            thread = await client.get("/boards/danger-room/threads/moonlight-skirmish")
            stylesheet_text = await _stylesheet_text_with_imports(client)

        content = _page_content(thread.text)
        assert thread.status == 200
        assert "elbysodic-post-list--editorial-wrap" in content
        assert 'data-elbysodic-post-reader-mode="poster-wrap"' in content
        assert "elbysodic-post-profile--bio" in content
        assert "elbysodic-post-profile--poster" in content
        assert "elbysodic-post-profile--dock" in content
        assert "elbysodic-post-density--dramatic" in content
        assert "elbysodic-post-density--compact" in content
        assert "elbysodic-post__author-name" in content
        assert "<time datetime=" in content
        assert 'aria-label="Permalink to post 1"' in content
        assert 'href="/boards/danger-room/threads/moonlight-skirmish/posts/3/edit"' in content
        assert 'writer <a class="chirpui-link" href="/members/' in content
        assert 'style="--elbysodic-character-accent:' in content
        assert ".elbysodic-post-list--editorial-wrap .elbysodic-post__poster" in stylesheet_text
        assert (
            ".elbysodic-post-list--editorial-wrap > .elbysodic-post-border--hairline"
            in stylesheet_text
        )
        assert "outline-color: transparent;" in stylesheet_text
        assert ".elbysodic-post-list--editorial-wrap > .chirpui-surface:hover" in stylesheet_text
        assert "inline-size: min(100%, 54rem);" in stylesheet_text
        assert "justify-self: center;" in stylesheet_text
        assert "@media (min-width: 64rem)" in stylesheet_text
        assert ".elbysodic-scene-composer-tools" in stylesheet_text
        assert "min-height: 8.5rem;" in stylesheet_text
        assert ".elbysodic-post__author-name" in stylesheet_text
        assert ":where(time, .chirpui-link)" in stylesheet_text
        assert (
            ".elbysodic-post-list--editorial-wrap .elbysodic-post__meta-actions" in stylesheet_text
        )
        assert "opacity: 0;" in stylesheet_text
        assert "pointer-events: none;" in stylesheet_text
        assert "float: inline-start;" in stylesheet_text
        assert "float: inline-end;" in stylesheet_text
        assert "aspect-ratio: var(--elbysodic-ratio-poster);" in stylesheet_text
        assert ".elbysodic-post-profile--poster:hover" in stylesheet_text
        assert "position: absolute;" in stylesheet_text

    asyncio.run(run())


def test_studio_post_style_policy_filters_character_controls() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/appearance",
                body=urlencode(
                    {
                        "intent": "post_style_policy",
                        "enabled_post_profile_variants": "bio",
                        "enabled_post_accent_styles": "soft",
                        "enabled_post_border_styles": "hairline",
                        "enabled_post_title_styles": "standard",
                        "enabled_post_densities": "calm",
                    }
                ).encode(),
                headers=_FORM,
            )

            assert response.status == 302
            roster = await client.get("/characters")
            assert roster.status == 200
            assert '<option value="bio" selected>' in roster.text
            assert '<option value="poster"' not in roster.text

            denied = await client.post(
                "/characters",
                body=urlencode(
                    {
                        "_action": "create_character",
                        "name": "Bobby Drake",
                        "summary": "Ice and bad timing.",
                        "post_profile_variant": "poster",
                        "post_accent_style": "soft",
                        "post_border_style": "hairline",
                        "post_title_style": "standard",
                        "post_density": "calm",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert denied.status == 200
            assert "post profile variant is not available" in denied.text

    asyncio.run(run())


def test_studio_can_set_identity_accent_source() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)
        species = repo.get_facet_group_by_slug(community.id, "species")

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/appearance",
                body=f"identity_accent_facet_group_id={species.id}".encode(),
                headers=_FORM,
            )

            assert response.status == 302
            assert dict(response.headers)["location"] == "/studio/appearance#identity-appearance"
            assert repo.get_community(community.id).identity_accent_facet_group_id == species.id

    asyncio.run(run())


def test_director_studio_updates_default_theme_tokens() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)
        body = {
            "intent": "default_theme",
            "theme_slug": "gothic-folk-horror",
            "theme_name": "Gothic Folk Horror",
            "theme_typography_display": "serif",
            "theme_typography_body": "serif",
            "theme_typography_mono": "mono",
            "theme_radius": "square",
            "theme_density": "dramatic",
            "theme_texture": "scanline",
            "theme_light_bg": "#f7f0e8",
            "theme_light_bg_subtle": "#eadfd5",
            "theme_light_surface": "#fffaf4",
            "theme_light_surface_elevated": "#f1e4d9",
            "theme_light_border": "#c8a994",
            "theme_light_text": "#261b18",
            "theme_light_text_muted": "#705c54",
            "theme_light_accent": "#7a2639",
            "theme_light_accent_hover": "#5a1a29",
            "theme_light_accent_dim": "#b36a78",
            "theme_light_accent_secondary": "#315f55",
            "theme_light_success": "#3f7557",
            "theme_light_warning": "#94651d",
            "theme_light_error": "#963333",
            "theme_dark_bg": "#100d0f",
            "theme_dark_bg_subtle": "#1b1518",
            "theme_dark_surface": "#241b20",
            "theme_dark_surface_elevated": "#30242a",
            "theme_dark_border": "#6a4b55",
            "theme_dark_text": "#f7ece7",
            "theme_dark_text_muted": "#c9b2ac",
            "theme_dark_accent": "#d98aa0",
            "theme_dark_accent_hover": "#efafbf",
            "theme_dark_accent_dim": "#7c4050",
            "theme_dark_accent_secondary": "#8ec0a0",
            "theme_dark_success": "#8ec0a0",
            "theme_dark_warning": "#d7ad63",
            "theme_dark_error": "#ec8b8b",
        }

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/appearance",
                body=urlencode(body).encode(),
                headers=_FORM,
            )
            index = await client.get("/c/x-men-apocalypse")

        theme = repo.get_default_theme(community.id)
        assert response.status == 302
        assert _response_header(response, "location") == "/studio/appearance#appearance-theme"
        assert theme is not None
        assert theme.slug == "gothic-folk-horror"
        assert theme.name == "Gothic Folk Horror"
        tokens = json.loads(theme.tokens_json)
        assert tokens["texture"] == "scanline"
        assert tokens["density"] == "dramatic"
        assert tokens["typography"]["display"] == "serif"
        assert tokens["dark"]["accent"] == "#d98aa0"
        assert index.status == 200
        assert "--chirpui-accent: #d98aa0;" in index.text
        assert "--elbysodic-program-density: dramatic;" in index.text

    asyncio.run(run())


def test_director_studio_surfaces_theme_health_warnings() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        admin_services.update_default_theme(
            slug="low-contrast",
            name="Low Contrast",
            typography_display="system",
            typography_body="system",
            typography_mono="mono",
            radius="sm",
            density="calm",
            texture="none",
            light={
                "bg": "#f0f0f0",
                "bg_subtle": "#eeeeee",
                "surface": "#f2f2f2",
                "surface_elevated": "#f3f3f3",
                "border": "#dddddd",
                "text": "#f1f1f1",
                "text_muted": "#eeeeee",
                "accent": "#f0eeee",
                "accent_hover": "#e8e8e8",
                "accent_dim": "#eeeeee",
                "accent_secondary": "#eeeeee",
                "success": "#eeeeee",
                "warning": "#eeeeee",
                "error": "#eeeeee",
            },
            dark={
                "bg": "#101010",
                "bg_subtle": "#161616",
                "surface": "#181818",
                "surface_elevated": "#202020",
                "border": "#343434",
                "text": "#f8f8f8",
                "text_muted": "#bbbbbb",
                "accent": "#d98aa0",
                "accent_hover": "#efafbf",
                "accent_dim": "#7c4050",
                "accent_secondary": "#8ec0a0",
                "success": "#8ec0a0",
                "warning": "#d7ad63",
                "error": "#ec8b8b",
            },
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            studio = await client.get("/studio/appearance")

        assert studio.status == 200
        assert "Theme Health" in studio.text
        assert "Guidebook body text may be hard to read" in studio.text
        assert "Muted metadata may fade too far back" in studio.text
        assert "Accent actions may not stand out" in studio.text

    asyncio.run(run())


def test_director_studio_updates_world_hero_media() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/appearance",
                body=urlencode(
                    {
                        "intent": "community_media",
                        "community_mark_url": "https://example.test/mark.png",
                        "community_mark_alt": "X-Men mark",
                        "world_hero_image_url": "https://example.test/world.jpg",
                        "world_hero_image_alt": "A fog-covered academy at night",
                        "world_hero_treatment": "background",
                        "world_hero_focal_point": "top",
                        "world_hero_overlay": "heavy",
                        "world_hero_height": "immersive",
                    }
                ).encode(),
                headers=_FORM,
            )
            home = await client.get("/c/x-men-apocalypse")
            studio = await client.get("/studio/appearance")

        updated = repo.get_community(community.id)
        assert response.status == 302
        assert _response_header(response, "location") == "/studio/appearance#appearance-media"
        assert updated.world_hero_image_url == "https://example.test/world.jpg"
        assert updated.world_hero_treatment == "background"
        assert updated.world_hero_focal_point == "top"
        assert updated.world_hero_overlay == "heavy"
        assert updated.world_hero_height == "immersive"
        assert home.status == 200
        assert "elbysodic-realm-gateway-hero__media" in home.text
        assert 'src="https://example.test/world.jpg"' in home.text
        assert 'alt="A fog-covered academy at night"' in home.text
        assert studio.status == 200
        assert "Community media" in studio.text
        assert "https://example.test/world.jpg" in studio.text
        assert '<option value="background" selected>Full background</option>' in studio.text

    asyncio.run(run())


def test_director_studio_rejects_unsupported_hero_treatment() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/appearance",
                body=urlencode(
                    {
                        "intent": "community_media",
                        "community_mark_url": "",
                        "community_mark_alt": "",
                        "world_hero_image_url": "https://example.test/world.jpg",
                        "world_hero_image_alt": "A fog-covered academy at night",
                        "world_hero_treatment": "raw-css",
                        "world_hero_focal_point": "center",
                        "world_hero_overlay": "medium",
                        "world_hero_height": "standard",
                    }
                ).encode(),
                headers=_FORM,
            )

        updated = repo.get_community(community.id)
        assert response.status == 200
        assert "world hero treatment is not supported" in response.text
        assert updated.world_hero_treatment == "split"

    asyncio.run(run())


def test_reply_uses_selected_character() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )

        async with TestClient(app) as client:
            response = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=f"character_id={storm.id}&body=Lightning+answers.".encode(),
                headers=_FORM,
            )
            assert response.status == 302
            assert dict(response.headers)["location"].startswith(
                "/boards/plotting/threads/open-thread-roster#post-"
            )

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert "Lightning answers." in thread.text
            assert "Storm" in thread.text
            assert 'role="toolbar"' in thread.text
            assert 'aria-label="Bold"' in thread.text

    asyncio.run(run())


def test_thread_posts_render_safe_markup() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )
        body = (
            "**Lightning** answers.\n\n"
            "> Hold the line.\n\n"
            "[Briefing](https://example.test/briefing) "
            '<script>alert("x")</script>'
        )

        async with TestClient(app) as client:
            response = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=urlencode({"character_id": storm.id, "body": body}).encode(),
                headers=_FORM,
            )
            assert response.status == 302

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert "<strong>Lightning</strong> answers." in thread.text
            assert "<blockquote><p>Hold the line.</p></blockquote>" in thread.text
            assert 'href="https://example.test/briefing"' in thread.text
            assert '<script>alert("x")</script>' not in thread.text
            assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in thread.text

    asyncio.run(run())


def test_writer_can_edit_own_post_with_safe_markup() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )

        async with TestClient(app) as client:
            created = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=urlencode({"character_id": storm.id, "body": "Original typo."}).encode(),
                headers=_FORM,
            )
            assert created.status == 302
            post_number = dict(created.headers)["location"].split("#post-")[1]

            edit_form = await client.get(
                f"/boards/plotting/threads/open-thread-roster/posts/{post_number}/edit"
            )
            assert edit_form.status == 200
            assert "Edit post" in edit_form.text
            assert "Original typo." in edit_form.text
            assert "edit-post-composer-config" in edit_form.text
            assert 'role="toolbar"' in edit_form.text
            assert 'aria-label="Bold"' in edit_form.text

            edited = await client.post(
                f"/boards/plotting/threads/open-thread-roster/posts/{post_number}/edit",
                body=urlencode(
                    {
                        "body": (
                            '**Updated** line.\n\n> Edited safely.\n\n<script>alert("x")</script>'
                        )
                    }
                ).encode(),
                headers=_FORM,
            )
            assert edited.status == 302
            assert dict(edited.headers)["location"] == (
                f"/boards/plotting/threads/open-thread-roster#post-{post_number}"
            )

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert "Original typo." not in thread.text
            assert "<strong>Updated</strong> line." in thread.text
            assert "<blockquote><p>Edited safely.</p></blockquote>" in thread.text
            assert '<script>alert("x")</script>' not in thread.text
            assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in thread.text
            assert "edited" in thread.text
            assert f"/posts/{post_number}/revisions" in thread.text
            assert f"/posts/{post_number}/edit" in thread.text

            revisions = await client.get(
                f"/boards/plotting/threads/open-thread-roster/posts/{post_number}/revisions"
            )
            assert revisions.status == 200
            assert "Post history" in revisions.text
            assert "Revision 1" in revisions.text
            assert "Original typo." in revisions.text
            assert "**Updated** line." in revisions.text
            assert "/members/starlane" in revisions.text

    asyncio.run(run())


def test_noop_post_edit_does_not_create_revision() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )

        async with TestClient(app) as client:
            created = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=urlencode({"character_id": storm.id, "body": "Already polished."}).encode(),
                headers=_FORM,
            )
            assert created.status == 302
            post_number = int(dict(created.headers)["location"].split("#post-")[1])
            board = repo.get_board_by_slug(services.seed.community.id, "plotting")
            thread = repo.get_thread_by_slug(
                services.seed.community.id,
                board.id,
                "open-thread-roster",
            )
            original = repo.get_post_by_number(
                services.seed.community.id,
                thread.id,
                post_number,
            )

            edited = await client.post(
                f"/boards/plotting/threads/open-thread-roster/posts/{post_number}/edit",
                body=urlencode({"body": "Already polished."}).encode(),
                headers=_FORM,
            )
            assert edited.status == 302

            unchanged = repo.get_post(services.seed.community.id, original.id)
            assert unchanged.updated_at == original.updated_at
            assert repo.list_post_revisions(services.seed.community.id, original.id) == []

    asyncio.run(run())


def test_writer_cannot_edit_someone_elses_post() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("not-yours@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "notyours",
            "Not Yours",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "not-yours-face",
            "Not Yours Face",
        )
        board = repo.get_board_by_slug(community.id, "plotting")
        thread = repo.get_thread_by_slug(community.id, board.id, "open-thread-roster")
        outsider_post = repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "This belongs to another writer.",
        )

        async with TestClient(app) as client:
            edit_form = await client.get(
                "/boards/plotting/threads/open-thread-roster/posts/"
                f"{outsider_post.post_number}/edit"
            )
            assert edit_form.status == 403

            edited = await client.post(
                "/boards/plotting/threads/open-thread-roster/posts/"
                f"{outsider_post.post_number}/edit",
                body=urlencode({"body": "Trying to overwrite."}).encode(),
                headers=_FORM,
            )
            assert edited.status == 403
            assert repo.get_post(community.id, outsider_post.id).body == (
                "This belongs to another writer."
            )
            assert repo.list_post_revisions(community.id, outsider_post.id) == []

    asyncio.run(run())


def test_locked_threads_still_allow_editing_own_existing_post() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        board = repo.get_board_by_slug(community.id, "announcements")
        thread = repo.get_thread_by_slug(community.id, board.id, "welcome-to-the-rebuild")
        post = repo.list_posts(community.id, thread.id)[0]

        async with TestClient(app) as client:
            response = await client.post(
                "/boards/announcements/threads/welcome-to-the-rebuild/posts/"
                f"{post.post_number}/edit",
                body=urlencode({"body": "Updated staff note."}).encode(),
                headers=_FORM,
            )
            assert response.status == 302

            restored = await client.get("/boards/announcements/threads/welcome-to-the-rebuild")
            assert "Updated staff note." in restored.text
            assert "Thread locked" in restored.text

    asyncio.run(run())


def test_staff_can_pin_and_lock_threads() -> None:
    async def run() -> None:
        app, repo, community, thread = _moderation_app(is_admin=True)

        async with TestClient(app) as client:
            page = await client.get("/boards/ic/threads/moderation-queue")
            assert page.status == 200
            assert "Staff controls" in page.text
            assert 'id="thread-staff-controls"' not in page.text
            assert 'id="scene-context-docked-thread-staff-controls"' in page.text
            assert "Pin thread" in page.text
            assert "Lock thread" in page.text
            assert "Move thread" in page.text

            pinned = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=pin",
                headers=_FORM,
            )
            assert pinned.status == 302
            assert repo.get_thread(community.id, thread.id).is_pinned is True

            locked = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=lock",
                headers=_FORM,
            )
            assert locked.status == 302
            assert repo.get_thread(community.id, thread.id).is_locked is True

            updated = await client.get("/boards/ic/threads/moderation-queue")
            assert "pinned" in updated.text
            assert "locked" in updated.text
            assert "Unpin thread" in updated.text
            assert "Unlock thread" in updated.text

            unpinned = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=unpin",
                headers=_FORM,
            )
            assert unpinned.status == 302
            assert repo.get_thread(community.id, thread.id).is_pinned is False

            unlocked = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=unlock",
                headers=_FORM,
            )
            assert unlocked.status == 302
            assert repo.get_thread(community.id, thread.id).is_locked is False

    asyncio.run(run())


def test_staff_can_move_thread_without_rewriting_thread_history() -> None:
    async def run() -> None:
        app, repo, community, thread = _moderation_app(is_admin=True)
        target_board = repo.get_board_by_slug(community.id, "archive")
        original = repo.get_thread(community.id, thread.id)
        post = repo.list_posts(community.id, thread.id)[0]
        repo.create_post_revision(
            community.id,
            post.id,
            post.author_membership_id,
            "Old wording.",
            post.body,
        )
        repo.mark_thread_read(
            community.id,
            thread.id,
            post.author_membership_id,
            read_at="2026-01-01T00:00:00+00:00",
        )

        async with TestClient(app) as client:
            response = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=f"intent=move&target_board_id={target_board.id}".encode(),
                headers=_FORM,
            )
            assert response.status == 302
            assert dict(response.headers)["location"] == "/boards/archive/threads/moderation-queue"

            moved = repo.get_thread(community.id, thread.id)
            assert moved.board_id == target_board.id
            assert moved.slug == original.slug
            assert moved.title == original.title
            assert moved.updated_at == original.updated_at
            assert [restored.body for restored in repo.list_posts(community.id, moved.id)] == [
                "A thread ready for staff tools."
            ]
            assert len(repo.list_post_revisions(community.id, post.id)) == 1
            assert repo.get_thread_read_at(community.id, moved.id, post.author_membership_id) == (
                "2026-01-01T00:00:00+00:00"
            )

            new_page = await client.get("/boards/archive/threads/moderation-queue")
            assert new_page.status == 200
            assert "Archive" in new_page.text
            assert "A thread ready for staff tools." in new_page.text

    asyncio.run(run())


def test_regular_members_cannot_manage_thread_lifecycle() -> None:
    async def run() -> None:
        app, repo, community, thread = _moderation_app(is_admin=False)
        target_board = repo.get_board_by_slug(community.id, "archive")

        async with TestClient(app) as client:
            page = await client.get("/boards/ic/threads/moderation-queue")
            assert page.status == 200
            assert "Staff controls" not in page.text

            lock_response = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=lock",
                headers=_FORM,
            )
            assert lock_response.status == 403

            move_response = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=f"intent=move&target_board_id={target_board.id}".encode(),
                headers=_FORM,
            )
            assert move_response.status == 403
            assert repo.get_thread(community.id, thread.id).is_locked is False
            assert repo.get_thread(community.id, thread.id).is_pinned is False
            assert repo.get_thread(community.id, thread.id).board_id != target_board.id

    asyncio.run(run())


def test_start_thread_creates_opening_post_as_selected_character() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        roster = services.viewer().roster
        magneto = next(character for character in roster if character.name == "Magneto")
        rogue = next(character for character in roster if character.name == "Rogue")
        xavier = services.repo.get_character_by_slug(
            services.seed.community.id,
            "charles-xavier",
        )

        async with TestClient(app) as client:
            form = await client.get("/boards/danger-room/threads/new")
            assert form.status == 200
            assert "Start scene" in form.text
            assert "elbysodicComposer" in form.text
            assert "thread-composer-config" in form.text
            assert "Post as" in form.text
            assert "Scene summary" in form.text
            assert "Tag cast" in form.text
            assert "elbysodicMentionPicker" in form.text
            assert "/mentionables/search" in form.text
            assert (
                re.search(
                    rf'<input type="checkbox"\s+name="participant_ids"\s+value="{magneto.id}"',
                    form.text,
                )
                is None
            )
            assert "Open to join" in form.text
            assert "Who can read" in form.text
            assert "Public preview — first 4 posts" in form.text
            assert re.search(r'<option value="members"\s+selected>', form.text)
            assert "Posting order" in form.text
            assert 'role="toolbar"' in form.text
            assert 'aria-label="Bold"' in form.text
            assert 'aria-label="Italic"' in form.text
            assert 'aria-label="Quote"' in form.text
            assert 'aria-label="Link"' in form.text
            assert "Power-stealing brawler with a careful heart." in form.text
            key = _input_value(form.text, "idempotency_key")

            response = await client.post(
                "/boards/danger-room/threads/new",
                body=urlencode(
                    {
                        "character_id": magneto.id,
                        "participant_ids": [xavier.id, rogue.id],
                        "title": "Metal and Memory",
                        "status": "open",
                        "visibility": "public_preview",
                        "location": "Sublevel 3",
                        "timeline": "Before breakfast",
                        "summary": "Magneto tags Xavier into an unreasonable simulation.",
                        "posting_mode": "posting_order",
                        "body": "Magneto sets the simulation to unfair.",
                        "idempotency_key": key,
                    },
                    doseq=True,
                ).encode(),
                headers=_FORM,
            )
            duplicate = await client.post(
                "/boards/danger-room/threads/new",
                body=urlencode(
                    {
                        "character_id": magneto.id,
                        "title": "Metal and Memory Duplicate",
                        "body": "This duplicate should not be posted.",
                        "idempotency_key": key,
                    },
                    doseq=True,
                ).encode(),
                headers=_FORM,
            )
            assert response.status == 302
            assert dict(response.headers)["location"].startswith(
                "/boards/danger-room/threads/metal-and-memory#post-"
            )
            assert duplicate.status == 302
            assert dict(duplicate.headers)["location"] == dict(response.headers)["location"]

            thread = await client.get("/boards/danger-room/threads/metal-and-memory")
            assert thread.status == 200
            assert "Metal and Memory" in thread.text
            assert "Magneto sets the simulation to unfair." in thread.text
            assert "Magneto" in thread.text
            assert "Post reply" in thread.text
            assert "elbysodic-scene-composer-tools" in thread.text
            assert "open to join" in thread.text
            assert "Sublevel 3" in thread.text
            assert "Before breakfast" in thread.text
            assert "Magneto tags Xavier into an unreasonable simulation." in thread.text
            assert "/characters/charles-xavier" in thread.text
            created_thread = services.repo.get_thread_by_slug(
                services.seed.community.id,
                services.repo.get_board_by_slug(services.seed.community.id, "danger-room").id,
                "metal-and-memory",
            )
            assert {
                character.slug
                for character in services.repo.list_thread_participants(
                    services.seed.community.id,
                    created_thread.id,
                )
            } == {"magneto", "charles-xavier"}
            assert created_thread.visibility == "public_preview"

            board = await client.get("/boards/danger-room")
            assert "Metal and Memory" in board.text
            assert "Metal and Memory Duplicate" not in board.text
            assert "Started by" in board.text
            assert "open to join" in board.text
            assert "Sublevel 3" in board.text
            assert "Latest" in board.text
            assert "/members/starlane" in board.text

    asyncio.run(run())


def test_start_thread_validation_error_discards_idempotency_reservation() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        character = services.viewer().current_character
        assert character is not None

        async with TestClient(app) as client:
            form = await client.get("/boards/danger-room/threads/new")
            key = _input_value(form.text, "idempotency_key")
            invalid = await client.post(
                "/boards/danger-room/threads/new",
                body=urlencode(
                    {
                        "character_id": character.id,
                        "title": "",
                        "body": "This body should not reserve the command forever.",
                        "idempotency_key": key,
                    }
                ).encode(),
                headers=_FORM,
            )
            corrected = await client.post(
                "/boards/danger-room/threads/new",
                body=urlencode(
                    {
                        "character_id": character.id,
                        "title": "Retryable Scene Command",
                        "body": "The corrected scene can reuse the rendered key.",
                        "idempotency_key": key,
                    }
                ).encode(),
                headers=_FORM,
            )

        assert invalid.status == 200
        assert "thread title is required" in invalid.text
        assert corrected.status == 302
        assert dict(corrected.headers)["location"].startswith(
            "/boards/danger-room/threads/retryable-scene-command#post-"
        )
        board = services.repo.get_board_by_slug(services.seed.community.id, "danger-room")
        thread = services.repo.get_thread_by_slug(
            services.seed.community.id,
            board.id,
            "retryable-scene-command",
        )
        posts = services.repo.list_posts(services.seed.community.id, thread.id)
        assert [post.body for post in posts] == ["The corrected scene can reuse the rendered key."]

    asyncio.run(run())


def test_reply_idempotency_key_prevents_duplicate_posts() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        board = repo.get_board_by_slug(community.id, "danger-room")
        thread = repo.get_thread_by_slug(community.id, board.id, "sentinel-drill")
        character = services.viewer().current_character
        assert character is not None
        before_count = len(repo.list_posts(community.id, thread.id))

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")
            assert page.status == 200
            assert 'data-elbysodic-command-kind="reply"' in page.text
            assert 'data-elbysodic-actor-shape="explicit-character"' in page.text
            assert 'data-elbysodic-idempotency="command-token"' in page.text
            key = _input_value(page.text, "idempotency_key")
            first = await client.post(
                "/boards/danger-room/threads/sentinel-drill",
                body=urlencode(
                    {
                        "character_id": str(character.id),
                        "body": "Rogue checks the duplicate-submit guard.",
                        "idempotency_key": key,
                    }
                ).encode(),
                headers=_FORM,
            )
            duplicate = await client.post(
                "/boards/danger-room/threads/sentinel-drill",
                body=urlencode(
                    {
                        "character_id": str(character.id),
                        "body": "This duplicate should not create another post.",
                        "idempotency_key": key,
                    }
                ).encode(),
                headers=_FORM,
            )

        assert first.status == 302
        assert duplicate.status == 302
        assert dict(duplicate.headers)["location"] == dict(first.headers)["location"]
        posts = repo.list_posts(community.id, thread.id)
        assert len(posts) == before_count + 1
        assert posts[-1].body == "Rogue checks the duplicate-submit guard."

    asyncio.run(run())


def test_reply_validation_error_discards_idempotency_reservation() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        board = repo.get_board_by_slug(community.id, "danger-room")
        thread = repo.get_thread_by_slug(community.id, board.id, "sentinel-drill")
        character = services.viewer().current_character
        assert character is not None
        before_count = len(repo.list_posts(community.id, thread.id))

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")
            key = _input_value(page.text, "idempotency_key")
            invalid = await client.post(
                "/boards/danger-room/threads/sentinel-drill",
                body=urlencode(
                    {
                        "character_id": str(character.id),
                        "body": "",
                        "idempotency_key": key,
                    }
                ).encode(),
                headers=_FORM,
            )
            corrected = await client.post(
                "/boards/danger-room/threads/sentinel-drill",
                body=urlencode(
                    {
                        "character_id": str(character.id),
                        "body": "Rogue retries after a validation miss.",
                        "idempotency_key": key,
                    }
                ).encode(),
                headers=_FORM,
            )

        assert invalid.status == 200
        assert "reply body is required" in invalid.text
        assert corrected.status == 302
        assert dict(corrected.headers)["location"].endswith(f"#post-{before_count + 1}")
        posts = repo.list_posts(community.id, thread.id)
        assert len(posts) == before_count + 1
        assert posts[-1].body == "Rogue retries after a validation miss."

    asyncio.run(run())


def test_mentionable_search_supports_character_and_writer_scopes() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            cast = await client.get("/mentionables/search?q=char&scope=cast")
            assert cast.status == 200
            cast_payload = json.loads(cast.body)
            assert cast_payload["items"][0]["kind"] == "character"
            assert cast_payload["items"][0]["handle"] == "charles-xavier"

            tenant_cast = await client.get(
                "/c/x-men-apocalypse/mentionables/search?q=char&scope=cast"
            )
            assert tenant_cast.status == 200
            tenant_cast_payload = json.loads(tenant_cast.body)
            assert (
                tenant_cast_payload["items"][0]["href"]
                == "/c/x-men-apocalypse/characters/charles-xavier"
            )

            own_roster = await client.get("/mentionables/search?q=rogue&scope=cast")
            assert own_roster.status == 200
            assert json.loads(own_roster.body)["items"] == []

            ooc = await client.get("/mentionables/search?q=star&scope=ooc")
            assert ooc.status == 200
            ooc_payload = json.loads(ooc.body)
            assert ooc_payload["items"][0]["kind"] == "writer"
            assert ooc_payload["items"][0]["handle"] == "starlane"

            tenant_ooc = await client.get(
                "/c/x-men-apocalypse/mentionables/search?q=star&scope=ooc"
            )
            assert tenant_ooc.status == 200
            tenant_ooc_payload = json.loads(tenant_ooc.body)
            assert tenant_ooc_payload["items"][0]["href"] == "/c/x-men-apocalypse/members/starlane"

    asyncio.run(run())


def test_open_thread_can_be_joined_as_active_face() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        plotting = repo.get_board_by_slug(community.id, "plotting")
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        thread = repo.create_thread(
            community.id,
            plotting.id,
            xavier.id,
            "telepathy-office-hours",
            "Telepathy office hours",
            status="open",
            summary="Charles opens the study for whoever needs to talk.",
        )
        repo.create_post(
            community.id,
            thread.id,
            xavier.id,
            "Charles leaves the study door open and waits.",
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/plotting/threads/telepathy-office-hours")
            assert page.status == 200
            assert "Join as Rogue" in page.text
            assert "watching" not in page.text

            joined = await client.post(
                "/boards/plotting/threads/telepathy-office-hours",
                body=b"intent=join_scene",
                headers=_FORM,
            )
            assert joined.status == 302

            assert {
                character.slug
                for character in repo.list_thread_participants(community.id, thread.id)
            } == {"charles-xavier", "rogue"}
            assert repo.is_thread_watched(community.id, thread.id, services.seed.membership.id)

            joined_page = await client.get("/boards/plotting/threads/telepathy-office-hours")
            assert joined_page.status == 200
            assert "Join as Rogue" not in joined_page.text
            assert "2 faces present" in joined_page.text
            assert "watching" in joined_page.text

    asyncio.run(run())


def test_non_open_threads_do_not_show_join_action() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        danger_room = repo.get_board_by_slug(community.id, "danger-room")
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        thread = repo.create_thread(
            community.id,
            danger_room.id,
            xavier.id,
            "closed-practice",
            "Closed practice",
            status="active",
        )
        repo.create_post(
            community.id,
            thread.id,
            xavier.id,
            "This practice has already started.",
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/closed-practice")
            assert page.status == 200
            assert "Join as Rogue" not in page.text

    asyncio.run(run())


def test_thread_view_hides_unspecified_scene_metadata() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        author_user = repo.create_user("quiet-scene-author@example.com", "hash")
        author_membership = repo.create_membership(
            community.id,
            author_user.id,
            role.id,
            "quietauthor",
            "Quiet Author",
        )
        author = repo.create_character(
            community.id,
            author_membership.id,
            "quiet-author-face",
            "Quiet Author Face",
        )
        board = repo.get_board_by_slug(community.id, "danger-room")
        thread = repo.create_thread(
            community.id,
            board.id,
            author.id,
            "quiet-default-scene",
            "Quiet default scene",
        )
        repo.create_post(
            community.id,
            thread.id,
            author.id,
            "Rogue waits for someone else to make the first bad decision.",
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/quiet-default-scene")
            assert page.status == 200
            assert "Scene details" not in _page_content(page.text)
            assert "Scene management" not in page.text
            assert "Unspecified" not in page.text
            assert "Freeform" not in page.text
            assert "open to join" not in page.text

    asyncio.run(run())


def test_thread_starter_can_manage_scene_cast() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        board = repo.get_board_by_slug(community.id, "danger-room")
        thread = repo.get_thread_by_slug(community.id, board.id, "sentinel-drill")
        kitty = repo.get_character_by_slug(community.id, "kitty-pryde")
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")
            assert page.status == 200
            assert "Scene management" in page.text
            assert "Tag cast" in page.text
            assert "Charles Xavier" in page.text
            assert "Public preview — first 4 posts" in page.text

            response = await client.post(
                "/boards/danger-room/threads/sentinel-drill",
                body=urlencode(
                    {
                        "intent": "scene",
                        "status": "paused",
                        "visibility": "members",
                        "posting_mode": "freeform",
                        "location": "West lawn",
                        "timeline": "After inspection",
                        "summary": "Rogue calls a timeout before the simulation gets personal.",
                        "participant_ids": str(kitty.id),
                    }
                ).encode(),
                headers=_FORM,
            )
            assert response.status in {302, 303}

            updated = repo.get_thread(community.id, thread.id)
            assert updated.status == "paused"
            assert updated.visibility == "members"
            assert updated.location == "West lawn"
            assert updated.timeline == "After inspection"
            assert updated.summary == "Rogue calls a timeout before the simulation gets personal."
            assert updated.posting_mode == "freeform"
            assert {
                character.slug
                for character in repo.list_thread_participants(community.id, thread.id)
            } == {"rogue", "kitty-pryde"}
            assert xavier.id not in repo.list_thread_participant_ids(community.id, thread.id)

            rendered = await client.get("/boards/danger-room/threads/sentinel-drill")
            assert rendered.status == 200
            assert "paused" in rendered.text
            assert "West lawn" in rendered.text
            assert "After inspection" in rendered.text
            assert "Rogue calls a timeout before the simulation gets personal." in rendered.text

    asyncio.run(run())


def test_file_backed_services_persist_created_threads(tmp_path: Path) -> None:
    db_path = tmp_path / "elbysodic.sqlite3"
    services = create_services(path=db_path)
    viewer = services.viewer()
    assert viewer.current_character is not None

    thread = services.start_thread(
        board_slug="danger-room",
        character_id=viewer.current_character.id,
        title="Persistent Moonlight",
        body="This scene survives the next service boot.",
    )

    restarted = create_services(path=db_path)
    restored = restarted.read_thread("danger-room", thread.slug)
    assert restored.thread.title == "Persistent Moonlight"
    assert [post.post.body for post in restored.posts] == [
        "This scene survives the next service boot."
    ]
    assert len(restarted.viewer().roster) == 3


def test_start_thread_rolls_back_when_late_write_fails(monkeypatch) -> None:
    services = create_services(path=":memory:")
    viewer = services.viewer()
    assert viewer.current_character is not None
    board = services.repo.get_board_by_slug(viewer.community.id, "danger-room")

    def thread_write_snapshot() -> dict[str, list[tuple[object, ...]]]:
        connection = services.repo.connection
        community_id = viewer.community.id
        return {
            "threads": [
                tuple(row)
                for row in connection.execute(
                    """
                    SELECT id, board_id, author_membership_id, author_character_id, slug, title
                    FROM threads
                    WHERE community_id = ?
                    ORDER BY id
                    """,
                    (community_id,),
                ).fetchall()
            ],
            "posts": [
                tuple(row)
                for row in connection.execute(
                    """
                    SELECT id, thread_id, post_number, author_membership_id,
                           author_character_id, body
                    FROM posts
                    WHERE community_id = ?
                    ORDER BY id
                    """,
                    (community_id,),
                ).fetchall()
            ],
            "thread_participants": [
                tuple(row)
                for row in connection.execute(
                    """
                    SELECT id, thread_id, character_id
                    FROM thread_participants
                    WHERE community_id = ?
                    ORDER BY id
                    """,
                    (community_id,),
                ).fetchall()
            ],
            "thread_watches": [
                tuple(row)
                for row in connection.execute(
                    """
                    SELECT id, thread_id, membership_id
                    FROM thread_watches
                    WHERE community_id = ?
                    ORDER BY id
                    """,
                    (community_id,),
                ).fetchall()
            ],
            "thread_reads": [
                tuple(row)
                for row in connection.execute(
                    """
                    SELECT id, thread_id, membership_id, read_at
                    FROM thread_reads
                    WHERE community_id = ?
                    ORDER BY id
                    """,
                    (community_id,),
                ).fetchall()
            ],
            "notifications": [
                tuple(row)
                for row in connection.execute(
                    """
                    SELECT id, membership_id, kind, thread_id, post_id, actor_membership_id,
                           actor_character_id
                    FROM notifications
                    WHERE community_id = ?
                    ORDER BY id
                    """,
                    (community_id,),
                ).fetchall()
            ],
        }

    before = thread_write_snapshot()

    def fail_mark_thread_read(
        community_id: int,
        thread_id: int,
        membership_id: int,
    ) -> None:
        raise RuntimeError("simulated read-state failure")

    monkeypatch.setattr(services.repo, "mark_thread_read", fail_mark_thread_read)

    with pytest.raises(RuntimeError, match="simulated read-state failure"):
        services.start_thread(
            board_slug="danger-room",
            character_id=viewer.current_character.id,
            title="Rollback Drill",
            body="This scene should not survive a failed read-state write.",
        )

    after = thread_write_snapshot()
    assert after == before
    assert not services.repo.connection.in_transaction
    assert "rollback-drill" not in [
        thread.slug for thread in services.repo.list_threads(viewer.community.id, board.id)
    ]
    assert "This scene should not survive a failed read-state write." not in {
        row["body"]
        for row in services.repo.connection.execute(
            """
            SELECT body
            FROM posts
            WHERE community_id = ?
            """,
            (viewer.community.id,),
        )
    }


def test_repository_transaction_rolls_back_nested_mixin_writes() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    community = services.viewer().community

    def fail_nested_transaction() -> None:
        with repo.transaction():
            repo.create_material(
                community.id,
                "nested-rollback-guide",
                "Nested Rollback Guide",
                material_type="guide",
                summary="This guide should roll back with the outer transaction.",
            )
            with repo.transaction():
                repo.create_board(
                    community.id,
                    "nested-rollback-board",
                    "Nested Rollback Board",
                    board_kind="community",
                    description="This board should not survive the failed transaction.",
                )
            raise RuntimeError("simulated nested transaction failure")

    with pytest.raises(RuntimeError, match="simulated nested transaction failure"):
        fail_nested_transaction()

    assert not repo.connection.in_transaction
    with pytest.raises(LookupError):
        repo.get_material_by_slug(community.id, "nested-rollback-guide")
    with pytest.raises(LookupError):
        repo.get_board_by_slug(community.id, "nested-rollback-board")


def test_startup_seed_preserves_director_edited_boards_and_materials(tmp_path: Path) -> None:
    db_path = tmp_path / "elbysodic.sqlite3"
    services = create_services(path=db_path)
    repo = services.repo
    community = services.viewer().community
    board = repo.get_board_by_slug(community.id, "danger-room")
    material = repo.get_material_by_slug(community.id, "b-24-winter")

    repo.update_board(
        community.id,
        board.id,
        name="Danger Room After Hours",
        description="A director-customized simulation wing.",
        sort_order=board.sort_order,
        parent_board_id=board.parent_board_id,
        board_kind=board.board_kind,
        sidebar_section=board.sidebar_section,
        tagline="Custom director pressure.",
        image_url="/custom-danger-room.webp",
        image_alt="Custom Danger Room art",
        image_treatment=board.image_treatment,
        image_focal_point=board.image_focal_point,
        image_overlay=board.image_overlay,
        is_private=board.is_private,
        navigation_order=board.navigation_order,
        show_in_navigation=board.show_in_navigation,
    )
    repo.update_material(
        community.id,
        material.id,
        title="B-24 Winter Custom Briefing",
        material_type=material.material_type,
        summary="Director-edited event summary.",
        body="Director-edited event body.",
        status=material.status,
        sort_order=material.sort_order,
        is_featured=material.is_featured,
    )

    restarted = create_services(path=db_path)
    restored_board = restarted.repo.get_board_by_slug(community.id, "danger-room")
    restored_material = restarted.repo.get_material_by_slug(community.id, "b-24-winter")

    assert restored_board.name == "Danger Room After Hours"
    assert restored_board.description == "A director-customized simulation wing."
    assert restored_board.tagline == "Custom director pressure."
    assert restored_board.image_url == "/custom-danger-room.webp"
    assert restored_board.image_alt == "Custom Danger Room art"
    assert restored_material.title == "B-24 Winter Custom Briefing"
    assert restored_material.summary == "Director-edited event summary."
    assert restored_material.body == "Director-edited event body."


def test_file_backed_operations_inspection_reports_wal_and_integrity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("RAILWAY_VOLUME_MOUNT_PATH", raising=False)
    monkeypatch.delenv("ELBYSODIC_AUTO_SEED_DEMO", raising=False)
    services = create_services(path=tmp_path / "elbysodic.sqlite3")

    inspection = operations_inspection(
        services.repo,
        services.viewer(),
        OperationsInspectionConfig(environment="test", secure_cookies=True),
    )

    assert inspection.database_path.endswith("elbysodic.sqlite3")
    assert inspection.journal_mode.lower() == "wal"
    assert inspection.integrity_check == "ok"
    assert inspection.latest_migration_version == inspection.current_schema_version
    assert inspection.community_count > 0
    assert inspection.public_ready_realm_count > 0
    assert inspection.database_parent_path == str(tmp_path)
    assert inspection.database_parent_present
    assert inspection.database_file_present
    assert inspection.volume_mount_path == "not configured"
    assert not inspection.volume_mount_present
    assert inspection.demo_mode_enabled
    assert not inspection.auto_seed_demo_enabled


def test_restore_check_database_reports_redacted_service_readback(tmp_path: Path) -> None:
    db_path = tmp_path / "restore-check.sqlite3"
    services = create_services(path=db_path)
    repo = services.repo
    viewer = services.viewer()
    assert viewer.current_character is not None
    staff = resolve_seed_persona(repo, "xmen_staff")
    staff_services = AppServices(
        repo,
        DemoSeed(staff.community, staff.user, staff.membership, staff.character),
    )
    secret_user = repo.create_user("secret-restore@example.com", "secret-password-hash")
    repo.create_user_session(
        secret_user.id,
        "secret-session-token",
        expires_at="2026-06-01T00:00:00+00:00",
    )
    repo.create_user_passkey_credential(
        secret_user.id,
        credential_id=b"secret-passkey-credential-id",
        public_key=b"secret-passkey-public-key",
        sign_count=9,
        transports=("internal",),
        label="Secret Passkey Label",
    )
    repo.create_material(
        viewer.community.id,
        "private-restore-note",
        "Private Restore Note",
        material_type="guide",
        summary="Do not emit this summary.",
        body="Do not emit this material body.",
        status="draft",
    )
    services.start_thread(
        board_slug="danger-room",
        character_id=viewer.current_character.id,
        title="Restore Check Scene",
        body="Do not emit this post body.",
    )
    repo.create_community_access_request(
        viewer.community.id,
        email="secret-request@example.com",
        display_name="Secret Requester",
        face_concept="Do not emit this face concept.",
        wanted_hook="Do not emit this wanted hook.",
        notes="Do not emit this private access-request note.",
    )
    invitation = staff_services.create_writer_invitation("secret-invite@example.com")
    services.close()

    result = restore_check_database(db_path)
    report = format_restore_check_report(result)
    plan_report = format_restore_plan_report(restore_plan_from_check(result))
    combined_report = f"{report}\n{plan_report}"

    assert result.ok is True
    assert result.opened_read_only is True
    assert result.integrity_check == "ok"
    assert result.sqlite_user_version == result.current_schema_version
    assert result.latest_migration_version == result.current_schema_version
    assert result.community_count > 0
    assert "restore-check ok" in report
    assert "- users:" in report
    assert "- passkey credentials: 1" in report
    assert "- thread rows: ok" in report
    assert "secret-restore@example.com" not in combined_report
    assert "secret-password-hash" not in combined_report
    assert "secret-session-token" not in combined_report
    assert "Secret Passkey Label" not in combined_report
    assert "secret-passkey-credential-id" not in combined_report
    assert "secret-passkey-public-key" not in combined_report
    assert "secret-request@example.com" not in combined_report
    assert "Secret Requester" not in combined_report
    assert "Do not emit this face concept." not in combined_report
    assert "Do not emit this wanted hook." not in combined_report
    assert "Do not emit this private access-request note." not in combined_report
    assert "secret-invite@example.com" not in combined_report
    assert invitation.token not in combined_report
    assert invitation.invitation.token_hash not in combined_report
    assert "Do not emit this summary." not in combined_report
    assert "Do not emit this material body." not in combined_report
    assert "Do not emit this post body." not in combined_report


def test_restore_plan_from_check_orders_read_only_operator_steps(tmp_path: Path) -> None:
    db_path = tmp_path / "restore-plan.sqlite3"
    services = create_services(path=db_path)
    repo = services.repo
    viewer = services.viewer()
    assert viewer.current_character is not None
    secret_user = repo.create_user("secret-plan@example.com", "secret-password-hash")
    repo.create_user_session(secret_user.id, "secret-plan-token")
    services.start_thread(
        board_slug="danger-room",
        character_id=viewer.current_character.id,
        title="Restore Plan Scene",
        body="Do not emit this restore plan body.",
    )
    services.close()

    result = restore_check_database(db_path)
    plan = restore_plan_from_check(result)
    report = format_restore_plan_report(plan)

    assert plan.status == "ready"
    assert plan.blockers == ()
    assert plan.steps == tuple(
        sorted(plan.steps, key=lambda step: (step.order, step.domain, step.title))
    )
    assert plan.human_confirmation_steps
    assert {step.domain for step in plan.human_confirmation_steps} >= {
        "auth posture",
        "claims/reserves",
        "continuity",
        "export",
        "wanted",
    }
    assert "restore-plan ready" in report
    assert "secret-plan@example.com" not in report
    assert "secret-password-hash" not in report
    assert "secret-plan-token" not in report
    assert "Do not emit this restore plan body." not in report


def test_restore_plan_blocks_writable_restore_check_result() -> None:
    result = RestoreCheckResult(
        database_path="/private/tmp/candidate.sqlite3",
        opened_read_only=False,
        integrity_check="ok",
        foreign_key_violations=0,
        journal_mode="wal",
        sqlite_user_version=1,
        current_schema_version=1,
        latest_migration_version=1,
        community_count=1,
        core_counts=(),
        readback_checks=(RestoreCheckReadback("communities", "ok", "1 community row read back"),),
        failures=(),
    )

    plan = restore_plan_from_check(result)
    report = format_restore_plan_report(plan)
    read_only_blockers = [
        step for step in plan.blockers if step.source == "restore_check.opened_read_only"
    ]

    assert plan.status == "blocked"
    assert len(read_only_blockers) == 1
    assert read_only_blockers[0].title == "Open candidate database read-only"
    assert read_only_blockers[0].human_confirmation_required is True
    assert "restore-plan blocked" in report
    assert "destructive restore command" not in report


def test_restore_plan_from_check_maps_blockers_to_sensitive_domains() -> None:
    result = RestoreCheckResult(
        database_path="/private/tmp/candidate.sqlite3",
        opened_read_only=True,
        integrity_check="ok",
        foreign_key_violations=0,
        journal_mode="wal",
        sqlite_user_version=1,
        current_schema_version=2,
        latest_migration_version=1,
        community_count=0,
        core_counts=(
            RestoreCheckCount("notifications", "notifications", 2),
            RestoreCheckCount("sessions", "user_sessions", 1),
        ),
        readback_checks=(
            RestoreCheckReadback("memberships", "failed", "membership ownership missing"),
            RestoreCheckReadback("characters", "failed", "character ownership drift detected"),
        ),
        failures=(
            "no communities found",
            "orphaned notification target found",
            "continuity source gap detected",
            "export manifest unavailable",
            "auth session posture needs review",
        ),
    )

    plan = restore_plan_from_check(result)
    blockers_by_domain = {step.domain for step in plan.blockers}

    assert plan.status == "blocked"
    assert blockers_by_domain >= {
        "auth posture",
        "character",
        "community",
        "continuity",
        "export",
        "membership",
        "notification",
        "schema",
    }
    assert all(step.human_confirmation_required for step in plan.blockers)
    assert "restore-plan blocked" in format_restore_plan_report(plan)


def test_restore_check_database_reports_wrong_database_failure(tmp_path: Path) -> None:
    db_path = tmp_path / "wrong.sqlite3"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("CREATE TABLE users (email TEXT)")
        connection.execute("INSERT INTO users (email) VALUES ('wrong@example.com')")
        connection.commit()
    finally:
        connection.close()

    result = restore_check_database(db_path)
    report = format_restore_check_report(result)

    assert result.ok is False
    assert "restore-check failed" in report
    assert "missing table: communities" in result.failures
    assert "migration ledger unavailable" in "\n".join(result.failures)
    assert "no communities found" in result.failures
    assert "wrong@example.com" not in report


def test_restore_check_database_reports_foreign_key_violation(tmp_path: Path) -> None:
    db_path = tmp_path / "foreign-key-drift.sqlite3"
    services = create_services(path=db_path)
    services.close()
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            """
            INSERT INTO roles (
                community_id,
                slug,
                name,
                is_admin,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                999_999,
                "orphan-role-secret",
                "Should Not Leak",
                0,
                "2026-06-15T00:00:00Z",
                "2026-06-15T00:00:00Z",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    result = restore_check_database(db_path)
    report = format_restore_check_report(result)
    plan_report = format_restore_plan_report(restore_plan_from_check(result))
    combined_report = f"{report}\n{plan_report}"

    assert result.ok is False
    assert result.foreign_key_violations > 0
    assert "foreign_key_check reported" in "\n".join(result.failures)
    assert "restore-check failed" in report
    assert "restore-plan blocked" in plan_report
    assert "orphan-role-secret" not in combined_report
    assert "Should Not Leak" not in combined_report


def test_restore_check_database_requires_filesystem_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="filesystem database path"):
        restore_check_database(Path(":memory:"))

    with pytest.raises(FileNotFoundError):
        restore_check_database(tmp_path / "missing.sqlite3")


def test_composer_pages_point_empty_roster_to_character_setup() -> None:
    async def run() -> None:
        connection = connect(check_same_thread=False)
        create_schema(connection)
        repo = ForumRepository(connection)
        community = repo.seed_default_community("Empty Roster")
        role = repo.create_role(community.id, "member", "Member")
        user = repo.create_user("empty@example.com", "hash")
        membership = repo.create_membership(
            community.id,
            user.id,
            role.id,
            "empty",
            "Empty",
        )
        author_user = repo.create_user("author@example.com", "hash")
        author_membership = repo.create_membership(
            community.id,
            author_user.id,
            role.id,
            "author",
            "Author",
        )
        author = repo.create_character(
            community.id,
            author_membership.id,
            "author-face",
            "Author Face",
        )
        board = repo.create_board(community.id, "ic", "In Character")
        thread = repo.create_thread(
            community.id,
            board.id,
            author.id,
            "open-scene",
            "Open Scene",
        )
        repo.create_post(community.id, thread.id, author.id, "A scene exists.")
        services = AppServices(
            repo,
            DemoSeed(
                community=community,
                user=user,
                membership=membership,
                default_character=None,
            ),
        )

        app = create_app(debug=False, services=services)
        async with TestClient(app) as client:
            index = await client.get("/c/x-men-apocalypse")
            assert index.status == 200
            assert "Create your first character" in index.text

            new_thread = await client.get(f"/boards/{board.slug}/threads/new")
            assert new_thread.status == 200
            assert "Create a character first" in new_thread.text
            assert "Open roster" in new_thread.text
            assert "elbysodicComposer" not in new_thread.text

            reply = await client.get(f"/boards/{board.slug}/threads/{thread.slug}")
            assert reply.status == 200
            assert "Create a character first" in reply.text
            assert "A scene exists." in reply.text

    asyncio.run(run())


def test_app_contract_check_passes() -> None:
    _app().check()


def test_chirp_ui_alpine_runtime_is_loaded_for_interactive_layouts() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.get("/characters/storm")
            assert response.status == 200
            check = check_alpine_runtime(response.text)
            assert check.ok
            assert check.script_loaded

    asyncio.run(run())


def _moderation_app(
    *,
    is_admin: bool,
) -> tuple[App, ForumRepository, Community, Thread]:
    connection = connect(check_same_thread=False)
    create_schema(connection)
    repo = ForumRepository(connection)
    community = repo.seed_default_community("Moderation Test")
    role = repo.create_role(
        community.id,
        "staff" if is_admin else "member",
        "Staff" if is_admin else "Member",
        is_admin=is_admin,
    )
    user = repo.create_user("moderator@example.com", "hash")
    membership = repo.create_membership(
        community.id,
        user.id,
        role.id,
        "modlane" if is_admin else "memberlane",
        "Mod Lane" if is_admin else "Member Lane",
    )
    character = repo.create_character(
        community.id,
        membership.id,
        "moderator-face" if is_admin else "member-face",
        "Moderator Face" if is_admin else "Member Face",
        make_default=True,
    )
    board = repo.create_board(community.id, "ic", "In Character")
    repo.create_board(community.id, "archive", "Archive", sort_order=20)
    thread = repo.create_thread(
        community.id,
        board.id,
        character.id,
        "moderation-queue",
        "Moderation Queue",
    )
    repo.create_post(community.id, thread.id, character.id, "A thread ready for staff tools.")
    services = AppServices(
        repo,
        DemoSeed(
            community=community,
            user=user,
            membership=repo.get_membership(community.id, membership.id),
            default_character=character,
        ),
    )
    return create_app(debug=False, services=services), repo, community, thread
