from __future__ import annotations

import pytest

from elbysodic.blueprints import (
    BlueprintAppearance,
    BlueprintBoard,
    BlueprintCharacter,
    BlueprintMaterial,
    BlueprintMaterialVariant,
    BlueprintPostStyle,
    BlueprintTheme,
    BlueprintThemeMode,
    BlueprintTypography,
    BlueprintValidationError,
    BlueprintWanted,
    ProgramBlueprint,
    ensure_valid_program_blueprint,
    preview_program_blueprint_yaml,
    validate_program_blueprint,
)
from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.db import seed as seed_module
from elbysodic.db.seed import DemoSeed, seed_demo_forum
from elbysodic.services import AppServices


def _blueprint(
    *,
    boards: tuple[BlueprintBoard, ...] | None = None,
    materials: tuple[BlueprintMaterial, ...] | None = None,
    wanted: tuple[BlueprintWanted, ...] = (),
    theme: BlueprintTheme | None = None,
    appearance: BlueprintAppearance | None = None,
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
        appearance=appearance,
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


def test_program_blueprint_accepts_safe_appearance_payload() -> None:
    appearance = BlueprintAppearance(
        post_style=BlueprintPostStyle(
            profile_variant="poster",
            accent_style="line",
            border_style="hairline",
            title_style="serif",
            density="dramatic",
        ),
        material_variants=(
            BlueprintMaterialVariant("event", "noticeboard"),
            BlueprintMaterialVariant("premise", "chapter"),
        ),
    )
    preview = preview_program_blueprint_yaml(
        """
elbysodic_blueprint: 1
program:
  slug: demo-program
  name: Demo Program
  role:
    slug: director
    name: Director
    is_admin: true
characters:
  - slug: june-calloway
    name: June Calloway
    summary: Florist and town council note-taker.
boards:
  - slug: main-street
    name: Main Street
    kind: location
    tagline: One stoplight, twelve opinions.
    description: The town's public spine.
materials:
  - slug: premise
    title: Premise
    type: premise
    summary: A small-town ensemble.
    body: Founder's Week should be a cozy pressure cooker.
appearance:
  post_style:
    profile_variant: poster
    accent_style: line
    border_style: hairline
    title_style: serif
    density: dramatic
  material_variants:
    event: noticeboard
    premise: chapter
"""
    )

    assert validate_program_blueprint(_blueprint(appearance=appearance)) == ()
    assert preview.is_valid
    assert preview.appearance_count == 1
    assert (
        preview.appearance_summary == "postbit: poster rail, hairline frame; 2 guidebook variants"
    )


def test_program_blueprint_rejects_unsafe_appearance_payload() -> None:
    preview = preview_program_blueprint_yaml(
        """
elbysodic_blueprint: 1
program:
  slug: demo-program
  name: Demo Program
  role:
    slug: director
    name: Director
    is_admin: true
characters:
  - slug: june-calloway
    name: June Calloway
    summary: Florist and town council note-taker.
boards:
  - slug: main-street
    name: Main Street
    kind: location
    tagline: One stoplight, twelve opinions.
    description: The town's public spine.
materials:
  - slug: premise
    title: Premise
    type: premise
    summary: A small-town ensemble.
    body: Founder's Week should be a cozy pressure cooker.
appearance:
  raw_css: ".postbit { display: none; }"
  post_style:
    profile_variant: marquee
  material_variants:
    event: freeform-css
"""
    )

    assert not preview.is_valid
    assert "appearance.raw_css is not supported in Program Blueprints" in preview.errors
    assert any(".profile_variant must be one of:" in error for error in preview.errors)
    assert any(".variant must be one of:" in error for error in preview.errors)


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


def test_program_blueprint_reports_unknown_material_and_wanted_types() -> None:
    blueprint = _blueprint(
        materials=(
            BlueprintMaterial(
                "mood-board",
                "Mood Board",
                "cms_page",
                "A generic page that should not hydrate.",
                "This is not a director material type.",
            ),
        ),
        wanted=(
            BlueprintWanted(
                "anyone",
                "Anyone",
                "generic_listing",
                "A generic listing that should not hydrate.",
                "Wanted hooks should use the shared PBP vocabulary.",
            ),
        ),
    )

    errors = validate_program_blueprint(blueprint)

    assert any(".materials.mood-board.material_type must be one of:" in error for error in errors)
    assert any(".wanted.anyone.wanted_type must be one of:" in error for error in errors)


def test_program_blueprint_accepts_safe_board_media_payload() -> None:
    preview = preview_program_blueprint_yaml(
        """
elbysodic_blueprint: 1
program:
  slug: rl-small-town
  name: RL Small Town
  role:
    slug: director
    name: Director
    is_admin: true
characters:
  - slug: june-calloway
    name: June Calloway
    summary: Florist and town council note-taker.
boards:
  - slug: main-street
    name: Main Street
    kind: location
    tagline: One stoplight, twelve opinions.
    description: The town's public spine.
    media:
      url: /elbysodic-static/seed-media/locations/smalltown-main-street.svg
      alt: Main street storefronts under Founder's Week lights
      treatment: background
      focal_point: top
      overlay: heavy
materials:
  - slug: premise
    title: Premise
    type: premise
    summary: A small-town ensemble.
    body: Founder's Week should be a cozy pressure cooker.
"""
    )

    assert preview.is_valid
    assert preview.blueprint is not None
    board = preview.blueprint.boards[0]
    assert board.image_url == "/elbysodic-static/seed-media/locations/smalltown-main-street.svg"
    assert board.image_alt == "Main street storefronts under Founder's Week lights"
    assert board.image_treatment == "background"
    assert board.image_focal_point == "top"
    assert board.image_overlay == "heavy"
    assert preview.board_media_count == 1
    assert preview.board_media_summary == "1 board media slot."


def test_program_blueprint_rejects_unsafe_board_media_payload() -> None:
    preview = preview_program_blueprint_yaml(
        """
elbysodic_blueprint: 1
program:
  slug: broken-media
  name: Broken Media
  role:
    slug: director
    name: Director
    is_admin: true
characters:
  - slug: june-calloway
    name: June Calloway
    summary: Florist and town council note-taker.
boards:
  - slug: main-street
    name: Main Street
    kind: location
    tagline: One stoplight, twelve opinions.
    description: The town's public spine.
    image_url: javascript:alert(1)
    image_treatment: raw-css
    image_focal_point: middle
    image_overlay: opaque
  - slug: town-hall
    name: Town Hall
    kind: location
    tagline: Everybody has a permit problem.
    description: Civic scenes and public pressure.
    media:
      alt: Town hall without a URL
materials:
  - slug: premise
    title: Premise
    type: premise
    summary: A small-town ensemble.
    body: Founder's Week should be a cozy pressure cooker.
"""
    )

    assert not preview.is_valid
    assert (
        "program broken-media.boards.main-street.image_alt is required when image_url is set"
        in preview.errors
    )
    assert (
        "program broken-media.boards.main-street.image_url must be a safe image URL or local path"
        in preview.errors
    )
    assert any(".image_treatment must be one of:" in error for error in preview.errors)
    assert any(".image_focal_point must be one of:" in error for error in preview.errors)
    assert any(".image_overlay must be one of:" in error for error in preview.errors)
    assert (
        "program broken-media.boards.town-hall.image_url is required when image_alt is set"
        in preview.errors
    )


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


def test_program_blueprint_yaml_preview_maps_director_friendly_keys() -> None:
    preview = preview_program_blueprint_yaml(
        """
elbysodic_blueprint: 1
program:
  slug: rl-small-town
  name: RL Small Town
  role:
    slug: director
    name: Director
    is_admin: true
characters:
  - slug: june-calloway
    name: June Calloway
    summary: Florist and town council note-taker.
boards:
  - slug: main-street
    name: Main Street
    kind: location
    tagline: One stoplight, twelve opinions.
    description: The town's public spine.
materials:
  - slug: premise
    title: Premise
    type: premise
    summary: A small-town ensemble.
    body: Founder's Week should be a cozy pressure cooker.
wanted:
  - slug: returning-sibling
    title: Returning sibling
    type: relationship
    related_material: premise
    summary: A homecoming character with history.
    body: Someone left, came back, and knows where the deed is hidden.
"""
    )

    assert preview.is_valid
    assert preview.blueprint is not None
    assert preview.blueprint.slug == "rl-small-town"
    assert preview.blueprint.boards[0].board_kind == "location"
    assert preview.blueprint.materials[0].material_type == "premise"
    assert preview.blueprint.wanted[0].wanted_type == "relationship"
    assert preview.blueprint.wanted[0].related_material_slug == "premise"
    assert preview.character_count == 1
    assert preview.board_count == 1
    assert preview.material_count == 1
    assert preview.wanted_count == 1


@pytest.mark.parametrize(
    ("role_yaml", "expected_is_admin"),
    [
        ("is_admin: true", True),
        ("is_admin: false", False),
        ("", False),
    ],
)
def test_program_blueprint_yaml_preview_parses_admin_flag_strictly(
    role_yaml: str,
    expected_is_admin: bool,
) -> None:
    preview = preview_program_blueprint_yaml(
        f"""
elbysodic_blueprint: 1
program:
  slug: rl-small-town
  name: RL Small Town
  role:
    slug: director
    name: Director
    {role_yaml}
characters:
  - slug: june-calloway
    name: June Calloway
    summary: Florist and town council note-taker.
boards:
  - slug: main-street
    name: Main Street
    kind: location
    tagline: One stoplight, twelve opinions.
    description: The town's public spine.
materials:
  - slug: premise
    title: Premise
    type: premise
    summary: A small-town ensemble.
    body: Founder's Week should be a cozy pressure cooker.
"""
    )

    assert preview.is_valid
    assert preview.blueprint is not None
    assert preview.blueprint.is_admin is expected_is_admin


@pytest.mark.parametrize("role_yaml", ["is_admin: 'false'", "is_admin: 'true'", "is_admin: 1"])
def test_program_blueprint_yaml_preview_rejects_non_boolean_admin_flag(role_yaml: str) -> None:
    preview = preview_program_blueprint_yaml(
        f"""
elbysodic_blueprint: 1
program:
  slug: rl-small-town
  name: RL Small Town
  role:
    slug: director
    name: Director
    {role_yaml}
characters:
  - slug: june-calloway
    name: June Calloway
    summary: Florist and town council note-taker.
boards:
  - slug: main-street
    name: Main Street
    kind: location
    tagline: One stoplight, twelve opinions.
    description: The town's public spine.
materials:
  - slug: premise
    title: Premise
    type: premise
    summary: A small-town ensemble.
    body: Founder's Week should be a cozy pressure cooker.
"""
    )

    assert not preview.is_valid
    assert "program.role.is_admin must be true or false" in preview.errors
    assert preview.blueprint is not None
    assert preview.blueprint.is_admin is False


def test_program_blueprint_yaml_preview_reports_parse_and_validation_errors() -> None:
    parse_preview = preview_program_blueprint_yaml("program: [")
    validation_preview = preview_program_blueprint_yaml(
        """
elbysodic_blueprint: 2
program:
  slug: broken
  name: Broken
  role:
    slug: director
    name: Director
characters: []
boards: []
materials: []
"""
    )

    assert not parse_preview.is_valid
    assert "Blueprint YAML could not be parsed:" in parse_preview.errors[0]
    assert not validation_preview.is_valid
    assert "elbysodic_blueprint must be 1" in validation_preview.errors
    assert (
        "program broken.characters must include at least one starter face"
        in validation_preview.errors
    )


def test_seed_hydrates_program_blueprints_into_network_programs() -> None:
    connection = connect()
    create_schema(connection)
    repo = ForumRepository(connection)

    seed_demo_forum(repo)

    communities = connection.execute(
        "SELECT slug FROM communities ORDER BY id",
    ).fetchall()
    wanted_count = connection.execute("SELECT COUNT(*) FROM wanted_ads").fetchone()[0]
    discovery_profile_count = connection.execute(
        "SELECT COUNT(*) FROM community_discovery_profiles",
    ).fetchone()[0]
    discovery_tag_count = connection.execute(
        "SELECT COUNT(*) FROM community_discovery_tags",
    ).fetchone()[0]
    themes = connection.execute(
        """
        SELECT communities.slug AS community_slug, themes.slug AS theme_slug
        FROM communities
        JOIN themes ON themes.id = communities.default_theme_id
        ORDER BY communities.id
        """,
    ).fetchall()

    assert [row["slug"] for row in communities] == [
        "x-men-apocalypse",
        "hp-universe",
        "jurassic-park-universe",
        "rl-nyc",
        "rl-small-town",
        "harbor-society",
        "signal-creek",
        "nocturne-row",
        "crownfall",
        "afterlight-accord",
        "brightline",
        "emberhouse",
        "gaslight-ward",
        "wayfarer-station",
    ]
    assert wanted_count == 57
    assert discovery_profile_count == 14
    assert discovery_tag_count == 42
    assert [(row["community_slug"], row["theme_slug"]) for row in themes] == [
        ("hp-universe", "glass-staircase"),
        ("jurassic-park-universe", "isla-nublar-operations"),
        ("rl-nyc", "rent-week"),
        ("rl-small-town", "founders-week"),
    ]


def test_original_premise_seed_contract_covers_landed_archetypes() -> None:
    connection = connect()
    create_schema(connection)
    repo = ForumRepository(connection)

    seed_demo_forum(repo)

    rows = connection.execute(
        """
        SELECT
            communities.slug,
            community_discovery_profiles.premise_archetype,
            COUNT(DISTINCT boards.id) AS board_count,
            COUNT(DISTINCT materials.id) AS material_count,
            COUNT(DISTINCT characters.id) AS character_count,
            COUNT(DISTINCT wanted_ads.id) AS wanted_count,
            COUNT(DISTINCT claim_types.id) AS claim_type_count
        FROM communities
        JOIN community_discovery_profiles
            ON community_discovery_profiles.community_id = communities.id
        LEFT JOIN boards ON boards.community_id = communities.id
        LEFT JOIN materials ON materials.community_id = communities.id
        LEFT JOIN characters ON characters.community_id = communities.id
        LEFT JOIN wanted_ads ON wanted_ads.community_id = communities.id
        LEFT JOIN claim_types ON claim_types.community_id = communities.id
        WHERE communities.slug IN (
            'harbor-society',
            'signal-creek',
            'nocturne-row',
            'crownfall',
            'afterlight-accord',
            'brightline',
            'emberhouse',
            'gaslight-ward',
            'wayfarer-station'
        )
        GROUP BY communities.id
        ORDER BY communities.slug
        """,
    ).fetchall()
    contract = {row["slug"]: dict(row) for row in rows}

    assert set(contract) == set(seed_module.ORIGINAL_PREMISE_SEED_SLUGS)
    assert {
        slug: contract[slug]["premise_archetype"]
        for slug in seed_module.ORIGINAL_PREMISE_SEED_SLUGS
    } == seed_module.ORIGINAL_PREMISE_SEED_ARCHETYPES
    for slug in seed_module.ORIGINAL_PREMISE_SEED_SLUGS:
        assert contract[slug]["board_count"] >= 6
        assert contract[slug]["material_count"] >= 5
        assert contract[slug]["character_count"] >= 8
        assert contract[slug]["wanted_count"] >= 5
        assert contract[slug]["claim_type_count"] >= 4


def test_program_blueprint_preview_fingerprint_changes_with_source() -> None:
    connection = connect()
    create_schema(connection)
    repo = ForumRepository(connection)
    seed = seed_demo_forum(repo)
    moira = repo.get_membership_by_username(seed.community.id, "moira")
    admin_services = AppServices(
        repo,
        DemoSeed(
            seed.community,
            repo.get_user(moira.user_id),
            moira,
            repo.get_character_by_slug(seed.community.id, "moira-mactaggert"),
        ),
    )
    source = """
elbysodic_blueprint: 1
program:
  slug: rl-small-town-preview
  name: RL Small Town Preview
  role:
    slug: director
    name: Director
    is_admin: true
characters:
  - slug: june-calloway
    name: June Calloway
    summary: Florist and town council note-taker.
boards:
  - slug: main-street
    name: Main Street
    kind: location
    tagline: One stoplight, twelve opinions.
    description: The town's public spine.
materials:
  - slug: premise
    title: Premise
    type: premise
    summary: A small-town ensemble.
    body: Founder's Week should be a cozy pressure cooker.
"""

    preview = admin_services.preview_program_blueprint(source)
    changed = admin_services.preview_program_blueprint(
        source.replace("RL Small Town Preview", "RL Small Town Preview 2")
    )

    assert preview.is_valid
    assert preview.preview_fingerprint
    assert len(preview.preview_fingerprint) == 16
    assert changed.preview_fingerprint != preview.preview_fingerprint


def test_seed_hydrates_blueprint_board_media_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    program = _blueprint(
        boards=(
            BlueprintBoard(
                "main-street",
                "Main Street",
                "location",
                "One stoplight, twelve opinions.",
                "The town's public spine.",
                image_url="/elbysodic-static/seed-media/locations/smalltown-main-street.svg",
                image_alt="Main Street under string lights",
                image_treatment="background",
                image_focal_point="top",
                image_overlay="heavy",
            ),
        )
    )
    connection = connect()
    create_schema(connection)
    repo = ForumRepository(connection)
    monkeypatch.setattr(seed_module, "STUDIO_NETWORK_PROGRAMS", (program,))
    monkeypatch.setattr(seed_module, "STUDIO_PROGRAM_MEDIA", {})
    monkeypatch.setattr(seed_module, "STUDIO_PROGRAM_BOARD_MEDIA", {})

    seed_demo_forum(repo)

    community = repo.get_community_by_slug("demo-program")
    board = repo.get_board_by_slug(community.id, "main-street")
    assert board.image_url == "/elbysodic-static/seed-media/locations/smalltown-main-street.svg"
    assert board.image_alt == "Main Street under string lights"
    assert board.image_treatment == "background"
    assert board.image_focal_point == "top"
    assert board.image_overlay == "heavy"
