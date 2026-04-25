"""View helpers for Alpine-backed posting composers."""

from __future__ import annotations

from elbysodic.domain import Character
from elbysodic.services import Mentionable


def composer_config(
    *,
    config_id: str,
    draft_key: str,
    roster: list[Character],
    selected_character_id: int,
    initial_body: str = "",
    initial_title: str = "",
) -> dict[str, object]:
    return {
        "configId": config_id,
        "draftKey": draft_key,
        "characters": [
            {
                "id": character.id,
                "name": character.name,
                "summary": character.summary,
                "avatar_url": character.avatar_url,
                "initial": character.name[:1],
            }
            for character in roster
        ],
        "selectedCharacterId": selected_character_id,
        "initialBody": initial_body,
        "initialTitle": initial_title,
    }


def mention_picker_config(
    *,
    endpoint: str,
    hidden_name: str,
    scope: str,
    selected: list[Mentionable],
    placeholder: str = "@character",
) -> dict[str, object]:
    return {
        "endpoint": endpoint,
        "hiddenName": hidden_name,
        "placeholder": placeholder,
        "scope": scope,
        "selected": [item.to_dict() for item in selected],
    }
