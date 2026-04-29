"""Typed Program Blueprint contracts for studio-network seed hydration."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from elbysodic.domain.boards import BOARD_KINDS

THEME_FONT_KEYS: frozenset[str] = frozenset({"system", "serif", "condensed", "mono"})
THEME_RADIUS_KEYS: frozenset[str] = frozenset({"square", "sm", "md"})
THEME_DENSITY_KEYS: frozenset[str] = frozenset({"calm", "compact", "dramatic"})
THEME_TEXTURE_KEYS: frozenset[str] = frozenset({"none", "grid", "paper", "scanline"})


@dataclass(frozen=True, slots=True)
class BlueprintCharacter:
    slug: str
    name: str
    summary: str
    tagline: str = ""


@dataclass(frozen=True, slots=True)
class BlueprintBoard:
    slug: str
    name: str
    board_kind: str
    tagline: str
    description: str


@dataclass(frozen=True, slots=True)
class BlueprintMaterial:
    slug: str
    title: str
    material_type: str
    summary: str
    body: str


@dataclass(frozen=True, slots=True)
class BlueprintWanted:
    slug: str
    title: str
    wanted_type: str
    summary: str
    body: str
    related_material_slug: str = ""


@dataclass(frozen=True, slots=True)
class BlueprintThemeMode:
    bg: str
    bg_subtle: str
    surface: str
    surface_elevated: str
    border: str
    text: str
    text_muted: str
    accent: str
    accent_hover: str
    accent_dim: str
    accent_secondary: str
    success: str
    warning: str
    error: str


@dataclass(frozen=True, slots=True)
class BlueprintTypography:
    display: str = "system"
    body: str = "system"
    mono: str = "mono"


@dataclass(frozen=True, slots=True)
class BlueprintTheme:
    slug: str
    name: str
    typography: BlueprintTypography
    light: BlueprintThemeMode
    dark: BlueprintThemeMode
    radius: str = "sm"
    density: str = "calm"
    texture: str = "none"


@dataclass(frozen=True, slots=True)
class ProgramBlueprint:
    slug: str
    name: str
    role_slug: str
    role_name: str
    is_admin: bool
    characters: tuple[BlueprintCharacter, ...]
    boards: tuple[BlueprintBoard, ...]
    materials: tuple[BlueprintMaterial, ...]
    wanted: tuple[BlueprintWanted, ...] = ()
    theme: BlueprintTheme | None = None


class BlueprintValidationError(ValueError):
    """Raised when a Program Blueprint cannot be hydrated safely."""

    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("\n".join(self.errors))


def validate_program_blueprint(blueprint: ProgramBlueprint) -> tuple[str, ...]:
    """Return human-readable validation errors for one Program Blueprint."""

    errors: list[str] = []
    path = f"program {blueprint.slug or '<missing slug>'}"
    _require_text(errors, f"{path}.slug", blueprint.slug)
    _require_text(errors, f"{path}.name", blueprint.name)
    _require_text(errors, f"{path}.role_slug", blueprint.role_slug)
    _require_text(errors, f"{path}.role_name", blueprint.role_name)

    _validate_character_blueprints(errors, path, blueprint.characters)
    _validate_board_blueprints(errors, path, blueprint.boards)
    material_slugs = _validate_material_blueprints(errors, path, blueprint.materials)
    _validate_wanted_blueprints(errors, path, blueprint.wanted, material_slugs)
    if blueprint.theme is not None:
        _validate_theme_blueprint(errors, path, blueprint.theme)
    return tuple(errors)


def validate_program_blueprints(blueprints: Iterable[ProgramBlueprint]) -> tuple[str, ...]:
    """Return validation errors for a studio-network blueprint collection."""

    blueprint_list = tuple(blueprints)
    errors: list[str] = []
    errors.extend(
        _duplicate_slug_errors("program", (blueprint.slug for blueprint in blueprint_list))
    )
    for blueprint in blueprint_list:
        errors.extend(validate_program_blueprint(blueprint))
    return tuple(errors)


def ensure_valid_program_blueprint(blueprint: ProgramBlueprint) -> None:
    errors = validate_program_blueprint(blueprint)
    if errors:
        raise BlueprintValidationError(errors)


def ensure_valid_program_blueprints(blueprints: Iterable[ProgramBlueprint]) -> None:
    errors = validate_program_blueprints(blueprints)
    if errors:
        raise BlueprintValidationError(errors)


def blueprint_theme_tokens(theme: BlueprintTheme) -> dict[str, Any]:
    """Return the safe token payload persisted for a hydrated theme."""

    return asdict(theme)


def _validate_character_blueprints(
    errors: list[str],
    path: str,
    characters: tuple[BlueprintCharacter, ...],
) -> None:
    if not characters:
        errors.append(f"{path}.characters must include at least one starter face")
    errors.extend(
        _duplicate_slug_errors(f"{path}.characters", (character.slug for character in characters))
    )
    for character in characters:
        character_path = f"{path}.characters.{character.slug or '<missing slug>'}"
        _require_text(errors, f"{character_path}.slug", character.slug)
        _require_text(errors, f"{character_path}.name", character.name)
        _require_text(errors, f"{character_path}.summary", character.summary)


def _validate_board_blueprints(
    errors: list[str],
    path: str,
    boards: tuple[BlueprintBoard, ...],
) -> None:
    if not boards:
        errors.append(f"{path}.boards must include at least one playable hub")
    errors.extend(_duplicate_slug_errors(f"{path}.boards", (board.slug for board in boards)))
    for board in boards:
        board_path = f"{path}.boards.{board.slug or '<missing slug>'}"
        _require_text(errors, f"{board_path}.slug", board.slug)
        _require_text(errors, f"{board_path}.name", board.name)
        _require_text(errors, f"{board_path}.description", board.description)
        if board.board_kind not in BOARD_KINDS:
            allowed = ", ".join(sorted(BOARD_KINDS))
            errors.append(f"{board_path}.board_kind must be one of: {allowed}")


def _validate_material_blueprints(
    errors: list[str],
    path: str,
    materials: tuple[BlueprintMaterial, ...],
) -> set[str]:
    if not materials:
        errors.append(f"{path}.materials must include at least one director material")
    errors.extend(
        _duplicate_slug_errors(f"{path}.materials", (material.slug for material in materials))
    )
    material_slugs: set[str] = set()
    for material in materials:
        material_path = f"{path}.materials.{material.slug or '<missing slug>'}"
        _require_text(errors, f"{material_path}.slug", material.slug)
        _require_text(errors, f"{material_path}.title", material.title)
        _require_text(errors, f"{material_path}.material_type", material.material_type)
        _require_text(errors, f"{material_path}.summary", material.summary)
        material_slugs.add(material.slug)
    return material_slugs


def _validate_wanted_blueprints(
    errors: list[str],
    path: str,
    wanted: tuple[BlueprintWanted, ...],
    material_slugs: set[str],
) -> None:
    errors.extend(_duplicate_slug_errors(f"{path}.wanted", (hook.slug for hook in wanted)))
    for hook in wanted:
        hook_path = f"{path}.wanted.{hook.slug or '<missing slug>'}"
        _require_text(errors, f"{hook_path}.slug", hook.slug)
        _require_text(errors, f"{hook_path}.title", hook.title)
        _require_text(errors, f"{hook_path}.wanted_type", hook.wanted_type)
        _require_text(errors, f"{hook_path}.summary", hook.summary)
        if hook.related_material_slug and hook.related_material_slug not in material_slugs:
            errors.append(
                f"{hook_path}.related_material_slug references unknown material: "
                f"{hook.related_material_slug}"
            )


def _validate_theme_blueprint(
    errors: list[str],
    path: str,
    theme: BlueprintTheme,
) -> None:
    theme_path = f"{path}.theme"
    _require_text(errors, f"{theme_path}.slug", theme.slug)
    _require_text(errors, f"{theme_path}.name", theme.name)
    _validate_choice(
        errors, f"{theme_path}.typography.display", theme.typography.display, THEME_FONT_KEYS
    )
    _validate_choice(
        errors, f"{theme_path}.typography.body", theme.typography.body, THEME_FONT_KEYS
    )
    _validate_choice(
        errors, f"{theme_path}.typography.mono", theme.typography.mono, THEME_FONT_KEYS
    )
    _validate_choice(errors, f"{theme_path}.radius", theme.radius, THEME_RADIUS_KEYS)
    _validate_choice(errors, f"{theme_path}.density", theme.density, THEME_DENSITY_KEYS)
    _validate_choice(errors, f"{theme_path}.texture", theme.texture, THEME_TEXTURE_KEYS)
    _validate_theme_mode(errors, f"{theme_path}.light", theme.light)
    _validate_theme_mode(errors, f"{theme_path}.dark", theme.dark)


def _validate_theme_mode(errors: list[str], path: str, mode: BlueprintThemeMode) -> None:
    for name, value in asdict(mode).items():
        if not _is_hex_color(value):
            errors.append(f"{path}.{name} must be a 6-digit hex color")


def _validate_choice(
    errors: list[str],
    path: str,
    value: str,
    allowed_values: frozenset[str],
) -> None:
    if value not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        errors.append(f"{path} must be one of: {allowed}")


def _require_text(errors: list[str], path: str, value: str) -> None:
    if not value.strip():
        errors.append(f"{path} is required")


def _is_hex_color(value: object) -> bool:
    if not isinstance(value, str):
        return False
    if len(value) != 7 or not value.startswith("#"):
        return False
    return all(character in "0123456789abcdefABCDEF" for character in value[1:])


def _duplicate_slug_errors(label: str, slugs: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for slug in slugs:
        if not slug:
            continue
        if slug in seen:
            duplicates.add(slug)
        seen.add(slug)
    return [f"{label} contains duplicate slug: {slug}" for slug in sorted(duplicates)]
