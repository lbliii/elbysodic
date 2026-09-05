from __future__ import annotations

import asyncio
import re
import sqlite3
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Barrier
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest
from chirp.testing import TestClient

from elbysodic.db import ForumRepository, connect
from elbysodic.services import AppServices, create_services
from elbysodic.services.commands import PendingCommandError
from elbysodic.web import create_app
from elbysodic.web.commands import draft_ack_path

_FORM = {"Content-Type": "application/x-www-form-urlencoded"}


def test_post_edit_rolls_back_revision_when_body_write_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    services = create_services(path=":memory:")
    viewer = services.viewer()
    assert viewer.current_character is not None
    created = services.start_thread_with_post(
        board_slug="danger-room",
        character_id=viewer.current_character.id,
        title="Revision rollback proof",
        body="The original post survives.",
    )
    before_revisions = services.repo.list_post_revisions(viewer.community.id, created.post.id)

    def fail_body_write(*_args: object, **_kwargs: object) -> object:
        raise sqlite3.OperationalError("injected body write failure")

    monkeypatch.setattr(services.repo, "update_post_body", fail_body_write)
    with pytest.raises(sqlite3.OperationalError, match="injected body write failure"):
        services.update_post(
            "danger-room",
            created.thread.slug,
            created.post.post_number,
            "A changed post that must roll back.",
        )

    persisted = services.repo.get_post(viewer.community.id, created.post.id)
    after_revisions = services.repo.list_post_revisions(viewer.community.id, created.post.id)
    assert persisted.body == "The original post survives."
    assert after_revisions == before_revisions


def test_scene_edit_rolls_back_metadata_when_participant_write_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    services = create_services(path=":memory:")
    viewer = services.viewer()
    assert viewer.current_character is not None
    created = services.start_thread_with_post(
        board_slug="danger-room",
        character_id=viewer.current_character.id,
        title="Scene rollback proof",
        body="The scene begins unchanged.",
    )
    before = services.repo.get_thread(viewer.community.id, created.thread.id)

    def fail_participants(*_args: object, **_kwargs: object) -> object:
        raise sqlite3.OperationalError("injected participant write failure")

    monkeypatch.setattr(services.repo, "set_thread_participants", fail_participants)
    with pytest.raises(sqlite3.OperationalError, match="injected participant write failure"):
        services.update_thread_scene(
            "danger-room",
            created.thread.slug,
            status="archived",
            location="Changed location",
            timeline="Changed timeline",
            summary="Changed summary",
        )

    after = services.repo.get_thread(viewer.community.id, created.thread.id)
    assert (
        after.status,
        after.location,
        after.timeline,
        after.summary,
    ) == (
        before.status,
        before.location,
        before.timeline,
        before.summary,
    )


def test_command_completion_failure_rolls_back_post_and_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    services = create_services(path=":memory:")
    viewer = services.viewer()
    assert viewer.current_character is not None
    character_id = viewer.current_character.id
    board = services.repo.get_board_by_slug(viewer.community.id, "danger-room")
    thread = services.repo.get_thread_by_slug(viewer.community.id, board.id, "sentinel-drill")
    before_posts = services.repo.list_posts(viewer.community.id, thread.id)
    command_key = "reply:danger-room:sentinel-drill"
    submission_id = "atomic-command-token"
    result_path = draft_ack_path(
        f"/boards/danger-room/threads/sentinel-drill#post-{len(before_posts) + 1}",
        submission_id,
    )

    def operation() -> str:
        services.reply_to_thread(
            "danger-room",
            "sentinel-drill",
            character_id,
            "The command result commits with this reply.",
        )
        return result_path

    original_complete = services.repo.complete_command_submission

    def fail_completion(*_args: object, **_kwargs: object) -> None:
        raise sqlite3.OperationalError("injected command completion failure")

    monkeypatch.setattr(services.repo, "complete_command_submission", fail_completion)
    with pytest.raises(sqlite3.OperationalError, match="injected command completion failure"):
        services.execute_command(command_key, submission_id, operation)

    assert services.repo.list_posts(viewer.community.id, thread.id) == before_posts
    assert services.command_result(command_key, submission_id) is None

    monkeypatch.setattr(
        services.repo,
        "complete_command_submission",
        original_complete,
    )
    first = services.execute_command(command_key, submission_id, operation)
    replay = services.execute_command(
        command_key,
        submission_id,
        lambda: pytest.fail("a completed command must not execute again"),
    )

    assert first.replayed is False
    assert replay.replayed is True
    assert replay.result_path == first.result_path == result_path
    assert len(services.repo.list_posts(viewer.community.id, thread.id)) == len(before_posts) + 1


def test_legacy_pending_command_fails_closed_without_reposting() -> None:
    services = create_services(path=":memory:")
    viewer = services.viewer()
    assert viewer.current_character is not None
    board = services.repo.get_board_by_slug(viewer.community.id, "danger-room")
    thread = services.repo.get_thread_by_slug(viewer.community.id, board.id, "sentinel-drill")
    command_key = "reply:danger-room:sentinel-drill"
    submission_id = "legacy-ambiguous-command"

    assert services.reserve_command(command_key, submission_id)
    committed_post = services.reply_to_thread(
        "danger-room",
        "sentinel-drill",
        viewer.current_character.id,
        "This post committed before the old command result write failed.",
    )

    invoked = False

    def duplicate_operation() -> str:
        nonlocal invoked
        invoked = True
        return "/must-not-run"

    with pytest.raises(PendingCommandError, match="may already have completed"):
        services.execute_command(command_key, submission_id, duplicate_operation)

    assert invoked is False
    assert services.command_result(command_key, submission_id) is None
    posts = services.repo.list_posts(viewer.community.id, thread.id)
    assert [post.id for post in posts].count(committed_post.id) == 1
    assert posts[-1].body == ("This post committed before the old command result write failed.")


def test_reply_command_revalidates_membership_inside_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root_services = create_services(path=":memory:")
    services = root_services.for_request(object())
    viewer = services.viewer()
    assert viewer.current_character is not None
    character_id = viewer.current_character.id
    repo = services.repo
    board = repo.get_board_by_slug(viewer.community.id, "danger-room")
    thread = repo.get_thread_by_slug(viewer.community.id, board.id, "sentinel-drill")
    before_posts = repo.list_posts(viewer.community.id, thread.id)
    submission_id = "revoked-reply"
    original_transaction = repo.transaction
    revoked = False

    @contextmanager
    def transaction_after_revocation() -> Iterator[None]:
        nonlocal revoked
        if not revoked:
            repo.connection.execute(
                "UPDATE community_memberships SET is_active = 0 WHERE id = ?",
                (viewer.membership.id,),
            )
            repo.connection.commit()
            revoked = True
        with original_transaction():
            yield

    monkeypatch.setattr(repo, "transaction", transaction_after_revocation)

    def reply() -> str:
        post = services.reply_to_thread(
            "danger-room",
            "sentinel-drill",
            character_id,
            "A revoked writer must not add this reply.",
        )
        return f"/boards/danger-room/threads/sentinel-drill#post-{post.post_number}"

    with pytest.raises(PermissionError, match=r"membership .* is not active"):
        services.execute_command("reply:danger-room:sentinel-drill", submission_id, reply)

    assert repo.list_posts(viewer.community.id, thread.id) == before_posts
    assert (
        repo.get_command_submission(
            viewer.community.id,
            viewer.membership.id,
            command_key="reply:danger-room:sentinel-drill",
            token=submission_id,
        )
        is None
    )


def test_start_command_revalidates_membership_inside_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root_services = create_services(path=":memory:")
    services = root_services.for_request(object())
    viewer = services.viewer()
    assert viewer.current_character is not None
    character_id = viewer.current_character.id
    repo = services.repo
    board = repo.get_board_by_slug(viewer.community.id, "danger-room")
    before_thread_ids = {thread.id for thread in repo.list_threads(viewer.community.id, board.id)}
    submission_id = "revoked-start"
    original_transaction = repo.transaction
    revoked = False

    @contextmanager
    def transaction_after_revocation() -> Iterator[None]:
        nonlocal revoked
        if not revoked:
            repo.connection.execute(
                "UPDATE community_memberships SET is_active = 0 WHERE id = ?",
                (viewer.membership.id,),
            )
            repo.connection.commit()
            revoked = True
        with original_transaction():
            yield

    monkeypatch.setattr(repo, "transaction", transaction_after_revocation)

    def start() -> str:
        thread = services.start_thread(
            board_slug="danger-room",
            character_id=character_id,
            title="Revoked transaction scene",
            body="A revoked writer must not open this scene.",
        )
        return f"/boards/danger-room/threads/{thread.slug}"

    with pytest.raises(PermissionError, match=r"membership .* is not active"):
        services.execute_command("start-thread:danger-room", submission_id, start)

    assert {
        thread.id for thread in repo.list_threads(viewer.community.id, board.id)
    } == before_thread_ids
    assert (
        repo.get_command_submission(
            viewer.community.id,
            viewer.membership.id,
            command_key="start-thread:danger-room",
            token=submission_id,
        )
        is None
    )


def test_concurrent_same_title_threads_receive_distinct_slugs(tmp_path) -> None:
    database_path = tmp_path / "atomic-slugs.sqlite3"
    seeded = create_services(path=database_path)
    viewer = seeded.viewer()
    assert viewer.current_character is not None
    seed = seeded.seed
    character_id = viewer.current_character.id
    seeded.close()

    services = [
        AppServices(
            ForumRepository(connect(database_path, check_same_thread=False)),
            seed,
        )
        for _ in range(2)
    ]
    barrier = Barrier(2)

    def create_scene(service: AppServices, body: str) -> str:
        barrier.wait()
        return service.start_thread(
            board_slug="danger-room",
            character_id=character_id,
            title="Simultaneous Arrival",
            body=body,
        ).slug

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(create_scene, service, f"Opening from writer {index}.")
                for index, service in enumerate(services, start=1)
            ]
            slugs = {future.result(timeout=10) for future in futures}
    finally:
        for service in services:
            service.close()

    assert slugs == {"simultaneous-arrival", "simultaneous-arrival-2"}


def test_success_redirects_carry_the_submitted_draft_receipt() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        viewer = services.viewer()
        assert viewer.current_character is not None
        character_id = viewer.current_character.id
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            new_form = await client.get("/boards/danger-room/threads/new")
            command_token = _input_value(new_form.text, "idempotency_key")
            created = await client.post(
                "/boards/danger-room/threads/new",
                body=urlencode(
                    {
                        "character_id": character_id,
                        "title": "Draft receipt proof",
                        "body": "An opening tied to its submitted draft.",
                        "idempotency_key": command_token,
                    }
                ).encode(),
                headers=_FORM,
            )
            created_location = _header(created, "location")
            created_parts = urlsplit(created_location)
            assert created_parts.path.endswith("/threads/draft-receipt-proof")
            assert created_parts.fragment == "post-1"
            assert parse_qs(created_parts.query) == {"draft_ack": [command_token]}

            duplicate = await client.post(
                "/boards/danger-room/threads/new",
                body=urlencode(
                    {
                        "character_id": "not-an-integer",
                        "idempotency_key": command_token,
                    }
                ).encode(),
                headers=_FORM,
            )
            assert _header(duplicate, "location") == created_location

            reply_form = await client.get(created_parts.path)
            reply_token = _input_value(reply_form.text, "idempotency_key")
            replied = await client.post(
                created_parts.path,
                body=urlencode(
                    {
                        "character_id": character_id,
                        "body": "A reply with a replayable result.",
                        "idempotency_key": reply_token,
                    }
                ).encode(),
                headers=_FORM,
            )
            malformed_reply = await client.post(
                created_parts.path,
                body=urlencode(
                    {
                        "character_id": "not-an-integer",
                        "idempotency_key": reply_token,
                    }
                ).encode(),
                headers=_FORM,
            )
            assert _header(malformed_reply, "location") == _header(replied, "location")
            created_thread = services.repo.get_thread_by_slug(
                viewer.community.id,
                services.repo.get_board_by_slug(viewer.community.id, "danger-room").id,
                "draft-receipt-proof",
            )
            assert len(services.repo.list_posts(viewer.community.id, created_thread.id)) == 2

            edit_path = "/boards/danger-room/threads/draft-receipt-proof/posts/1/edit"
            first_edit_form = await client.get(edit_path)
            second_edit_form = await client.get(edit_path)
            draft_receipt = _input_value(first_edit_form.text, "draft_token")
            assert draft_receipt
            assert _input_value(second_edit_form.text, "draft_token") != draft_receipt

            invalid_edit = await client.post(
                edit_path,
                body=urlencode({"body": "", "draft_token": draft_receipt}).encode(),
                headers=_FORM,
            )
            assert invalid_edit.status == 200
            assert _input_value(invalid_edit.text, "draft_token") == draft_receipt

            edited = await client.post(
                edit_path,
                body=urlencode(
                    {
                        "body": "The opening is edited atomically.",
                        "draft_token": draft_receipt,
                    }
                ).encode(),
                headers=_FORM,
            )
            edited_parts = urlsplit(_header(edited, "location"))
            assert edited_parts.path.endswith("/threads/draft-receipt-proof")
            assert edited_parts.fragment == "post-1"
            assert parse_qs(edited_parts.query) == {"draft_ack": [draft_receipt]}

    asyncio.run(run())


def _input_value(html: str, name: str) -> str:
    match = re.search(
        rf'<input[^>]+name="{re.escape(name)}"[^>]+value="(?P<value>[^"]*)"',
        html,
    )
    assert match is not None
    return match.group("value")


def _header(response: Any, name: str) -> str:
    headers = response.headers
    if isinstance(headers, dict):
        return str(headers[name])
    for key, value in headers:
        if str(key).lower() == name.lower():
            return str(value)
    raise AssertionError(f"response header not found: {name}")
