from __future__ import annotations

from pathlib import Path

from elbysodic.domain import Character
from elbysodic.web.composer import composer_config

_ROOT = Path(__file__).parents[1]
_PAGES = _ROOT / "src/elbysodic/web/pages"


def _character(character_id: int, name: str) -> Character:
    return Character(
        id=character_id,
        community_id=7,
        membership_id=3,
        name=name,
        slug=name.lower(),
        avatar_url=None,
        poster_url=None,
        poster_alt="",
        tagline="",
        accent_color="",
        summary=f"{name}'s face summary",
        post_profile_variant="default",
        post_accent_style="default",
        post_border_style="default",
        post_title_style="default",
        post_density="default",
        application_status="accepted",
        created_at="2026-09-05T00:00:00Z",
        updated_at="2026-09-05T00:00:00Z",
    )


def test_composer_config_names_a_tenant_object_key_and_versioned_storage_base() -> None:
    config = composer_config(
        config_id="reply-composer-config",
        draft_key="reply:7:11",
        roster=[_character(1, "Rogue"), _character(2, "Logan")],
        selected_character_id=1,
        initial_body="",
        initial_title="",
    )

    assert config["draftKey"] == "reply:7:11"
    assert config["draftStorageKey"] == "elbysodic:draft:reply:7:11"
    assert config["draftStorageVersion"] == 2
    assert config["selectedCharacterId"] == 1
    characters = config["characters"]
    assert isinstance(characters, list)
    assert len(characters) == 2
    assert characters[0] == {
        "id": 1,
        "name": "Rogue",
        "summary": "Rogue's face summary",
        "avatar_url": None,
        "initial": "R",
    }
    assert characters[1] == {
        "id": 2,
        "name": "Logan",
        "summary": "Logan's face summary",
        "avatar_url": None,
        "initial": "L",
    }
    assert config["initialBody"] == ""
    assert config["initialTitle"] == ""


def test_posting_templates_submit_the_token_used_for_draft_acknowledgement() -> None:
    new_thread = (_PAGES / "boards/{board_slug}/threads/new/page.html").read_text(encoding="utf-8")
    reply = (_PAGES / "boards/{board_slug}/threads/{thread_slug}/page.html").read_text(
        encoding="utf-8"
    )
    edit = (
        _PAGES / "boards/{board_slug}/threads/{thread_slug}/posts/{post_id}/edit/page.html"
    ).read_text(encoding="utf-8")

    for template in (new_thread, reply, edit):
        assert '@submit="submitDraft()"' in template
    assert 'name="idempotency_key" value="{{ idempotency_key }}"' in new_thread
    assert 'name="idempotency_key" value="{{ idempotency_key }}"' in reply
    assert 'name="draft_token" value="{{ draft_receipt }}"' in edit
