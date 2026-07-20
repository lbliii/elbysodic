from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from elbysodic.db.repository import ForumRepository
from elbysodic.db.schema import connect
from elbysodic.services.auth import create_login_session
from elbysodic.services.forum import initialize_database

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "password_rehash_smoke.py"


def _load_smoke_module():
    spec = importlib.util.spec_from_file_location("password_rehash_smoke", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["password_rehash_smoke"] = module
    spec.loader.exec_module(module)
    return module


def test_staging_fixture_prepares_login_upgrade_and_reports_labels_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_path = initialize_database(tmp_path / "staging.sqlite3", seed_demo=True)
    monkeypatch.setenv("ELBYSODIC_ENV", "staging")
    monkeypatch.setenv("ELBYSODIC_DEMO_MODE", "1")
    smoke = _load_smoke_module()

    assert smoke.main(["prepare", "--db-path", str(database_path), "--confirm-staging-write"]) == 0
    assert smoke.main(["status", "--db-path", str(database_path)]) == 0

    connection = connect(database_path, check_same_thread=False)
    try:
        repo = ForumRepository(connection)
        before_login = repo.get_user_by_email("writer@example.com")
        assert before_login.password_hash.startswith("$scrypt$")
        login_phrase = "".join(("pass", "word"))
        create_login_session(repo, "writer@example.com", login_phrase)
        assert repo.get_user(before_login.id).password_hash.startswith("$argon2id$")
    finally:
        connection.close()

    assert smoke.main(["verify", "--db-path", str(database_path)]) == 0
    output = capsys.readouterr().out
    assert "before=demo-seed after=scrypt" in output
    assert "format=scrypt" in output
    assert "format=argon2id" in output
    assert "writer@example.com" not in output
    assert "$scrypt$" not in output
    assert "$argon2" not in output
    assert login_phrase not in output


def test_staging_fixture_refuses_non_staging_or_unconfirmed_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = initialize_database(tmp_path / "staging.sqlite3", seed_demo=True)
    smoke = _load_smoke_module()

    monkeypatch.setenv("ELBYSODIC_ENV", "production")
    monkeypatch.setenv("ELBYSODIC_DEMO_MODE", "1")
    with pytest.raises(RuntimeError, match="requires staging demo mode"):
        smoke.main(["status", "--db-path", str(database_path)])

    monkeypatch.setenv("ELBYSODIC_ENV", "staging")
    with pytest.raises(RuntimeError, match="requires --confirm-staging-write"):
        smoke.main(["prepare", "--db-path", str(database_path)])
