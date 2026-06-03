from __future__ import annotations

import sqlite3
from pathlib import Path

from elbysodic.db import connect, create_schema

REPO_ROOT = Path(__file__).parents[1]
READINESS_DOC = REPO_ROOT / "docs" / "architecture" / "continuity-graph-readiness.md"
WEB_PAGES_DIR = REPO_ROOT / "src" / "elbysodic" / "web" / "pages"


def test_continuity_readiness_contract_names_backend_gates() -> None:
    text = READINESS_DOC.read_text(encoding="utf-8")

    required_phrases = {
        "manual and reviewed",
        "explicit source citations",
        "explicit affected-object links",
        "review events that record staff membership actor separately",
        "visibility decisions owned by services",
        "notifications only to participants, owners, or staff",
        "tenant ownership for every source and affected object join",
        "No public continuity or canon route family exists yet.",
        "AI-generated canon",
        "automatic scene summarization",
    }

    missing = sorted(phrase for phrase in required_phrases if phrase not in text)

    assert missing == []


def test_no_continuity_schema_tables_exist_before_approved_backend_slice() -> None:
    connection = connect()
    try:
        create_schema(connection)
        table_names = _table_names(connection)
    finally:
        connection.close()

    deferred_tables = {
        "continuity_proposals",
        "continuity_sources",
        "continuity_affected_objects",
        "continuity_review_events",
        "canon_entries",
        "canon_sources",
        "scene_outcomes",
    }

    assert table_names.isdisjoint(deferred_tables)


def test_no_public_continuity_route_family_exists_before_privacy_proof() -> None:
    deferred_route_dirs = {
        WEB_PAGES_DIR / "canon",
        WEB_PAGES_DIR / "continuity",
        WEB_PAGES_DIR / "studio" / "canon",
        WEB_PAGES_DIR / "studio" / "continuity",
    }
    existing = sorted(
        str(path.relative_to(REPO_ROOT)) for path in deferred_route_dirs if path.exists()
    )

    assert existing == []


def _table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()
    return {str(row["name"]) for row in rows}
