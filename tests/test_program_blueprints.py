from __future__ import annotations

import pytest

from elbysodic.blueprints import (
    BlueprintBoard,
    BlueprintCharacter,
    BlueprintMaterial,
    BlueprintTheme,
    BlueprintThemeMode,
    BlueprintTypography,
    BlueprintValidationError,
    BlueprintWanted,
    ProgramBlueprint,
    ensure_valid_program_blueprint,
    validate_program_blueprint,
)
from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.db.seed import seed_demo_forum


def _blueprint(
    *,
    boards: tuple[BlueprintBoard, ...] | None = None,
    materials: tuple[BlueprintMaterial, ...] | None = None,
    wanted: tuple[BlueprintWanted, ...] = (),
    theme: BlueprintTheme | None = None,
) -> ProgramBlueprint:
    return ProgramBlueprint(
        slug="demo-program",
        name="Demo Program",
        role_slug="director",
        role_name="Director",
        is_admin=True,
        characters=(
            BlueprintCharacter(
                "june-calloway",
                "June Calloway",
                "Florist, town council note-taker, and keeper of other people's secrets.",
            ),
        ),
        boards=boards
        if boards is not None
        else (
            BlueprintBoard(
                "main-street",
                "Main Street",
                "location",
                "One stoplight, twelve opinions.",
                "The town's public spine.",
            ),
        ),
        materials=materials
        if materials is not None
        else (
            BlueprintMaterial(
                "premise",
                "Premise",
                "premise",
                "A small-town ensemble where celebration keeps digging up history.",
                "Founder's Week should be a cozy pressure cooker.",
            ),
        ),
        wanted=wanted,
        theme=theme,
    )


def _theme(*, accent: str = "#8d3f4a", display: str = "serif") -> BlueprintTheme:
    light = BlueprintThemeMode(
        bg="#fbf5e8",
        bg_subtle="#eee3cf",
        surface="#fffaf0",
        surface_elevated="#f4ead7",
        border="#c8b89a",
        text="#2b2318",
        text_muted="#75684f",
        accent=accent,
        accent_hover="#6e2f38",
        accent_dim="#c9878f",
        accent_secondary="#4f7c5b",
        success="#4f7c5b",
        warning="#a06d2a",
        error="#a64242",
    )
    dark = BlueprintThemeMode(
        bg="#16130f",
        bg_subtle="#211c16",
        surface="#282219",
        surface_elevated="#332b1f",
        border="#675942",
        text="#f6eddf",
        text_muted="#c9b99e",
        accent="#e38991",
        accent_hover="#f0a7ad",
        accent_dim="#7d4248",
        accent_secondary="#91c49a",
        success="#91c49a",
        warning="#dbb168",
        error="#ee8d8d",
    )
    return BlueprintTheme(
        slug="founders-week",
        name="Founder's Week",
        typography=BlueprintTypography(display=display, body="serif", mono="mono"),
        light=light,
        dark=dark,
        radius="md",
        density="calm",
        texture="paper",
    )


def test_valid_program_blueprint_has_no_validation_errors() -> None:
    blueprint = _blueprint(
        wanted=(
            BlueprintWanted(
                "returning-sibling",
                "Returning sibling",
                "relationship",
                "A homecoming character with history.",
                "Someone left, came back, and knows where the deed is hidden.",
                related_material_slug="premise",
            ),
        )
    )

    assert validate_program_blueprint(blueprint) == ()


def test_program_blueprint_accepts_complete_theme_tokens() -> None:
    assert validate_program_blueprint(_blueprint(theme=_theme())) == ()


def test_program_blueprint_reports_invalid_theme_color() -> None:
    errors = validate_program_blueprint(_blueprint(theme=_theme(accent="rose")))

    assert "program demo-program.theme.light.accent must be a 6-digit hex color" in errors


def test_program_blueprint_reports_invalid_theme_font_key() -> None:
    errors = validate_program_blueprint(_blueprint(theme=_theme(display="papyrus")))

    assert "program demo-program.theme.typography.display must be one of: " in "\n".join(errors)


def test_program_blueprint_reports_duplicate_slugs() -> None:
    blueprint = _blueprint(
        boards=(
            BlueprintBoard("main-street", "Main Street", "location", "Public spine.", "A"),
            BlueprintBoard("main-street", "Main Street Annex", "location", "Same slug.", "B"),
        )
    )

    with pytest.raises(BlueprintValidationError) as exc_info:
        ensure_valid_program_blueprint(blueprint)

    assert "program demo-program.boards contains duplicate slug: main-street" in str(exc_info.value)


def test_program_blueprint_reports_unknown_board_kind() -> None:
    blueprint = _blueprint(
        boards=(
            BlueprintBoard(
                "main-street",
                "Main Street",
                "vibes",
                "One stoplight, twelve opinions.",
                "The town's public spine.",
            ),
        )
    )

    errors = validate_program_blueprint(blueprint)

    assert any(".board_kind must be one of:" in error for error in errors)


def test_program_blueprint_reports_missing_wanted_material_reference() -> None:
    blueprint = _blueprint(
        wanted=(
            BlueprintWanted(
                "missing-deed",
                "Missing deed",
                "event_role",
                "A civic character with one dangerous document.",
                "The town needs someone who can make the event personal.",
                related_material_slug="current-event",
            ),
        )
    )

    errors = validate_program_blueprint(blueprint)

    assert (
        "program demo-program.wanted.missing-deed.related_material_slug "
        "references unknown material: current-event"
    ) in errors


def test_seed_hydrates_program_blueprints_into_network_programs() -> None:
    connection = connect()
    create_schema(connection)
    repo = ForumRepository(connection)

    seed_demo_forum(repo)

    communities = connection.execute(
        "SELECT slug FROM communities ORDER BY id",
    ).fetchall()
    wanted_count = connection.execute("SELECT COUNT(*) FROM wanted_ads").fetchone()[0]
    themes = connection.execute(
        """
        SELECT communities.slug AS community_slug, themes.slug AS theme_slug
        FROM communities
        JOIN themes ON themes.id = communities.default_theme_id
        ORDER BY communities.id
        """,
    ).fetchall()

    assert [row["slug"] for row in communities] == [
        "default",
        "hp-universe",
        "jurassic-park-universe",
        "rl-nyc",
        "rl-small-town",
    ]
    assert wanted_count == 12
    assert [(row["community_slug"], row["theme_slug"]) for row in themes] == [
        ("hp-universe", "glass-staircase"),
        ("jurassic-park-universe", "isla-nublar-operations"),
        ("rl-nyc", "rent-week"),
        ("rl-small-town", "founders-week"),
    ]
