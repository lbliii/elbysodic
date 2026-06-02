from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, cast

import pytest

from elbysodic.db import ForumRepository, connect
from elbysodic.services import create_services
from elbysodic.web.state import close_request_services, configure_services, get_services

REPO_ROOT = Path(__file__).parents[1]
WEB_DIR = REPO_ROOT / "src" / "elbysodic" / "web"
WEB_PAGES_DIR = WEB_DIR / "pages"
SERVICES_DIR = REPO_ROOT / "src" / "elbysodic" / "services"


class RequestStub:
    def __init__(self) -> None:
        self._cache: dict[str, object] = {}


class HeaderRequestStub(RequestStub):
    def __init__(self, headers: dict[str, str]) -> None:
        super().__init__()
        self.headers = headers
        self.cookies: dict[str, str] = {}


class TrackingRepositoryContext:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.connection: sqlite3.Connection | None = None
        self.exited = False

    def __enter__(self) -> ForumRepository:
        self.connection = connect(self.database_path, check_same_thread=False)
        return ForumRepository(self.connection)

    def __exit__(self, *_exc_info: object) -> None:
        self.exited = True
        assert self.connection is not None
        self.connection.close()


class TrackingDatabase:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.context: TrackingRepositoryContext | None = None

    def repository(self) -> TrackingRepositoryContext:
        self.context = TrackingRepositoryContext(self.database_path)
        return self.context


def test_file_backed_request_services_are_cached_and_closed(tmp_path: Path) -> None:
    root_services = create_services(path=tmp_path / "elbysodic.sqlite3")
    configure_services(root_services)
    request = RequestStub()

    try:
        first = get_services(request)
        second = get_services(request)

        assert first is second
        assert first is not root_services
        assert first.repo.connection.execute("SELECT COUNT(*) FROM communities").fetchone()[0] > 0

        close_request_services(request)

        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            first.repo.connection.execute("SELECT 1")
        assert request._cache == {}
        assert (
            root_services.repo.connection.execute("SELECT COUNT(*) FROM communities").fetchone()[0]
            > 0
        )
    finally:
        close_request_services(request)
        root_services.close()


def test_file_backed_request_services_close_when_identity_resolution_fails(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "elbysodic.sqlite3"
    root_services = create_services(path=database_path)
    tracking_database = TrackingDatabase(database_path)
    cast(Any, root_services)._database = tracking_database
    request = HeaderRequestStub({"x-elbysodic-membership-id": "999999"})

    try:
        with pytest.raises(LookupError, match="membership not found"):
            root_services.for_request(request)

        assert tracking_database.context is not None
        assert tracking_database.context.exited is True
        assert tracking_database.context.connection is not None
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            tracking_database.context.connection.execute("SELECT 1")
    finally:
        root_services.close()


def test_request_service_cleanup_rolls_back_open_transactions(tmp_path: Path) -> None:
    root_services = create_services(path=tmp_path / "elbysodic.sqlite3")
    configure_services(root_services)
    request = RequestStub()

    try:
        request_services = get_services(request)
        request_services.repo.connection.execute(
            """
            INSERT INTO communities (slug, name, created_at, updated_at)
            VALUES ('cleanup-rollback', 'Cleanup Rollback', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00')
            """
        )
        assert request_services.repo.connection.in_transaction

        close_request_services(request)

        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            request_services.repo.connection.execute("SELECT 1")
        with pytest.raises(LookupError, match="community not found"):
            root_services.repo.get_community_by_slug("cleanup-rollback")
    finally:
        close_request_services(request)
        root_services.close()


def test_repository_transaction_rolls_back_and_recovers_when_commit_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    services = create_services(path=":memory:")
    repo = services.repo

    def fail_commit() -> None:
        raise RuntimeError("simulated commit failure")

    monkeypatch.setattr(repo, "_commit", fail_commit)
    with pytest.raises(RuntimeError, match="simulated commit failure"), repo.transaction():
        repo.connection.execute(
            """
            INSERT INTO communities (slug, name, created_at, updated_at)
            VALUES ('commit-failure', 'Commit Failure', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00')
            """
        )

    assert repo._transaction_depth == 0
    assert not repo.connection.in_transaction
    with pytest.raises(LookupError, match="community not found"):
        repo.get_community_by_slug("commit-failure")

    monkeypatch.undo()
    recovered = repo.create_community("commit-recovered", "Commit Recovered")
    assert repo.get_community_by_slug("commit-recovered") == recovered
    services.close()


def test_web_entrypoints_do_not_manually_scope_services() -> None:
    offenders: list[str] = []
    for path in sorted(WEB_DIR.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        if "get_services().for_request(" in source:
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == []


def test_web_handlers_do_not_run_sql_directly() -> None:
    database_call_patterns = (
        re.compile(r"\.connection\b"),
        re.compile(r"\.execute\("),
        re.compile(r"\bexecutemany\("),
        re.compile(r"\bsqlite3\b"),
        re.compile(r"\bconnect\("),
    )
    offenders: list[str] = []

    for path in sorted(WEB_DIR.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        if any(pattern.search(source) for pattern in database_call_patterns):
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == []


def test_web_page_handlers_do_not_make_policy_decisions_directly() -> None:
    offenders: list[str] = []
    for path in sorted(WEB_PAGES_DIR.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        if "policies." in source or "from elbysodic.services import policies" in source:
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == []


def test_critical_rendered_pages_use_named_service_surface_contracts() -> None:
    expected_calls = {
        "src/elbysodic/web/pages/page.py": "services.realm_home()",
        "src/elbysodic/web/pages/claims/page.py": "services.claims_page(",
        "src/elbysodic/web/pages/characters/page.py": "services.character_roster_page(",
        "src/elbysodic/web/pages/notifications/page.py": "services.notification_center()",
        "src/elbysodic/web/pages/wanted/page.py": "services.wanted_ads()",
        "src/elbysodic/web/pages/boards/{board_slug}/page.py": "services.board_page(",
        "src/elbysodic/web/pages/studio/page.py": "services.director_studio()",
    }

    missing: list[str] = []
    for relative_path, service_call in expected_calls.items():
        source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        if service_call not in source:
            missing.append(f"{relative_path}: {service_call}")

    assert missing == []


def test_service_raw_sql_stays_limited_to_lifecycle_and_operations_diagnostics() -> None:
    exact_allowed = {
        (
            "src/elbysodic/services/forum.py",
            'connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")',
        ),
        (
            "src/elbysodic/services/forum.py",
            'connection.execute("PRAGMA database_list").fetchall()',
        ),
        (
            "src/elbysodic/services/forum.py",
            'return any(row["file"] for row in connection.execute("PRAGMA database_list").fetchall())',
        ),
        (
            "src/elbysodic/services/operations.py",
            'database_row = connection.execute("PRAGMA database_list").fetchone()',
        ),
        (
            "src/elbysodic/services/operations.py",
            'user_version = connection.execute("PRAGMA user_version").fetchone()[0]',
        ),
        (
            "src/elbysodic/services/operations.py",
            'community_count = connection.execute("SELECT COUNT(*) AS count FROM communities").fetchone()',
        ),
    }
    prefix_allowed = {
        ("src/elbysodic/services/operations.py", "migration_row = connection.execute("),
    }
    offenders: list[str] = []

    for path in sorted(SERVICES_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(source.splitlines(), start=1):
            if ".execute(" not in line and "executemany(" not in line:
                continue
            relative = str(path.relative_to(REPO_ROOT))
            stripped = line.strip()
            if (relative, stripped) in exact_allowed:
                continue
            if (relative, stripped) in prefix_allowed:
                continue
            if any(
                relative == allowed_path and stripped.startswith(allowed_prefix)
                for allowed_path, allowed_prefix in prefix_allowed
            ):
                continue
            else:
                offenders.append(f"{relative}:{line_number}: {stripped}")

    assert offenders == []
