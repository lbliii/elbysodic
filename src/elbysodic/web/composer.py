"""View helpers for Alpine-backed posting composers."""

from __future__ import annotations

from elbysodic.domain import Character


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
