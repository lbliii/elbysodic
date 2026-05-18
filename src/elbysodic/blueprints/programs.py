"""Typed Program Blueprint contracts for studio-network seed hydration."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any, Literal

import yaml

from elbysodic.domain.boards import (
    BOARD_IMAGE_FOCAL_POINTS,
    BOARD_IMAGE_OVERLAYS,
    BOARD_IMAGE_TREATMENTS,
    BOARD_KINDS,
)
from elbysodic.domain.vocabulary import MATERIAL_TYPES, WANTED_TYPES

THEME_FONT_KEYS: frozenset[str] = frozenset({"system", "serif", "condensed", "mono"})
THEME_RADIUS_KEYS: frozenset[str] = frozenset({"square", "sm", "md"})
THEME_DENSITY_KEYS: frozenset[str] = frozenset({"calm", "compact", "dramatic"})
THEME_TEXTURE_KEYS: frozenset[str] = frozenset({"none", "grid", "paper", "scanline"})
APPEARANCE_POST_PROFILE_VARIANTS: frozenset[str] = frozenset({"bio", "poster", "dock", "crest"})
APPEARANCE_POST_ACCENT_STYLES: frozenset[str] = frozenset({"soft", "line", "glow", "block"})
APPEARANCE_POST_BORDER_STYLES: frozenset[str] = frozenset({"none", "hairline", "bracket", "double"})
APPEARANCE_POST_TITLE_STYLES: frozenset[str] = frozenset({"standard", "serif", "condensed", "mono"})
APPEARANCE_POST_DENSITIES: frozenset[str] = frozenset({"calm", "compact", "dramatic"})
APPEARANCE_MATERIAL_TYPES: frozenset[str] = MATERIAL_TYPES
APPEARANCE_MATERIAL_VARIANTS: frozenset[str] = frozenset(
    {"chapter", "dossier", "noticeboard", "archive"}
)
APPEARANCE_DISALLOWED_KEYS: frozenset[str] = frozenset(
    {"css", "raw_css", "script", "javascript", "html", "template", "external_font_url"}
)


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
    image_url: str = ""
    image_alt: str = ""
    image_treatment: str = "poster"
    image_focal_point: str = "center"
    image_overlay: str = "medium"


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
class BlueprintPostStyle:
    profile_variant: str = "bio"
    accent_style: str = "soft"
    border_style: str = "hairline"
    title_style: str = "standard"
    density: str = "calm"


@dataclass(frozen=True, slots=True)
class BlueprintMaterialVariant:
    material_type: str
    variant: str


@dataclass(frozen=True, slots=True)
class BlueprintAppearance:
    post_style: BlueprintPostStyle | None = None
    material_variants: tuple[BlueprintMaterialVariant, ...] = ()


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
    appearance: BlueprintAppearance | None = None


class BlueprintValidationError(ValueError):
    """Raised when a Program Blueprint cannot be hydrated safely."""

    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("\n".join(self.errors))


BlueprintDiffAction = Literal["create", "update", "skip", "blocked", "warning"]


@dataclass(frozen=True, slots=True)
class BlueprintDiffRow:
    section: str
    slug: str
    label: str
    action: BlueprintDiffAction
    detail: str


@dataclass(frozen=True, slots=True)
class ProgramBlueprintPreview:
    blueprint: ProgramBlueprint | None
    errors: tuple[str, ...]
    diff_rows: tuple[BlueprintDiffRow, ...] = ()
    preview_fingerprint: str = ""

    @property
    def is_valid(self) -> bool:
        return self.blueprint is not None and not self.errors

    @property
    def program_count(self) -> int:
        return 1 if self.blueprint is not None else 0

    @property
    def character_count(self) -> int:
        return len(self.blueprint.characters) if self.blueprint is not None else 0

    @property
    def board_count(self) -> int:
        return len(self.blueprint.boards) if self.blueprint is not None else 0

    @property
    def material_count(self) -> int:
        return len(self.blueprint.materials) if self.blueprint is not None else 0

    @property
    def wanted_count(self) -> int:
        return len(self.blueprint.wanted) if self.blueprint is not None else 0

    @property
    def theme_count(self) -> int:
        return 1 if self.blueprint is not None and self.blueprint.theme is not None else 0

    @property
    def appearance_count(self) -> int:
        return 1 if self.blueprint is not None and self.blueprint.appearance is not None else 0

    @property
    def board_media_count(self) -> int:
        if self.blueprint is None:
            return 0
        return sum(1 for board in self.blueprint.boards if board.image_url)

    @property
    def appearance_summary(self) -> str:
        if self.blueprint is None or self.blueprint.appearance is None:
            return "No appearance payload."
        appearance = self.blueprint.appearance
        parts: list[str] = []
        if appearance.post_style is not None:
            parts.append(
                "postbit: "
                f"{appearance.post_style.profile_variant} rail, "
                f"{appearance.post_style.border_style} frame"
            )
        if appearance.material_variants:
            material_count = len(appearance.material_variants)
            parts.append(f"{material_count} guidebook variants")
        return "; ".join(parts) if parts else "Appearance payload is empty."

    @property
    def board_media_summary(self) -> str:
        count = self.board_media_count
        if count == 0:
            return "No board media payload."
        return f"{count} board media {'slot' if count == 1 else 'slots'}."

    @property
    def diff_action_summary(self) -> str:
        if not self.diff_rows:
            return "Hydration preflight not available."
        action_order: tuple[BlueprintDiffAction, ...] = (
            "create",
            "update",
            "skip",
            "blocked",
            "warning",
        )
        counts = {
            action: sum(1 for row in self.diff_rows if row.action == action)
            for action in action_order
        }
        parts = [
            f"{count} {action} {'action' if count == 1 else 'actions'}"
            for action, count in counts.items()
            if count
        ]
        return f"Preflight: {', '.join(parts)}."


def preview_program_blueprint_yaml(source: str) -> ProgramBlueprintPreview:
    """Parse and validate director-authored YAML without hydrating anything."""

    if not source.strip():
        return ProgramBlueprintPreview(None, ("Blueprint YAML is required.",))
    try:
        loaded = yaml.safe_load(source)
    except yaml.YAMLError as exc:
        return ProgramBlueprintPreview(
            None,
            (f"Blueprint YAML could not be parsed: {exc}",),
        )
    errors: list[str] = []
    root = _mapping(loaded, "blueprint", errors)
    if root is None:
        return ProgramBlueprintPreview(None, tuple(errors))
    if root.get("elbysodic_blueprint") != 1:
        errors.append("elbysodic_blueprint must be 1")
    program_data = _mapping(root.get("program"), "program", errors) or {}
    role_data = _mapping(program_data.get("role"), "program.role", errors) or {}
    blueprint = ProgramBlueprint(
        slug=_text(program_data.get("slug")),
        name=_text(program_data.get("name")),
        role_slug=_field(role_data, "slug"),
        role_name=_field(role_data, "name"),
        is_admin=_optional_bool_field(role_data, "is_admin", "program.role.is_admin", errors),
        characters=_characters_from_yaml(root.get("characters"), errors),
        boards=_boards_from_yaml(root.get("boards"), errors),
        materials=_materials_from_yaml(root.get("materials"), errors),
        wanted=_wanted_from_yaml(root.get("wanted", ()), errors),
        theme=_theme_from_yaml(root.get("theme"), errors),
        appearance=_appearance_from_yaml(root.get("appearance"), errors),
    )
    errors.extend(validate_program_blueprint(blueprint))
    return ProgramBlueprintPreview(blueprint, tuple(errors))


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
    if blueprint.appearance is not None:
        _validate_appearance_blueprint(errors, path, blueprint.appearance)
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
        _validate_board_media_blueprint(errors, board_path, board)


def _validate_board_media_blueprint(
    errors: list[str],
    board_path: str,
    board: BlueprintBoard,
) -> None:
    if board.image_url and not board.image_alt.strip():
        errors.append(f"{board_path}.image_alt is required when image_url is set")
    if board.image_alt.strip() and not board.image_url:
        errors.append(f"{board_path}.image_url is required when image_alt is set")
    if board.image_url and not _is_safe_media_url(board.image_url):
        errors.append(f"{board_path}.image_url must be a safe image URL or local path")
    _validate_choice(
        errors,
        f"{board_path}.image_treatment",
        board.image_treatment,
        BOARD_IMAGE_TREATMENTS,
    )
    _validate_choice(
        errors,
        f"{board_path}.image_focal_point",
        board.image_focal_point,
        BOARD_IMAGE_FOCAL_POINTS,
    )
    _validate_choice(
        errors,
        f"{board_path}.image_overlay",
        board.image_overlay,
        BOARD_IMAGE_OVERLAYS,
    )


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
        _validate_choice(
            errors,
            f"{material_path}.material_type",
            material.material_type,
            MATERIAL_TYPES,
        )
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
        _validate_choice(
            errors,
            f"{hook_path}.wanted_type",
            hook.wanted_type,
            WANTED_TYPES,
        )
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


def _validate_appearance_blueprint(
    errors: list[str],
    path: str,
    appearance: BlueprintAppearance,
) -> None:
    appearance_path = f"{path}.appearance"
    if appearance.post_style is not None:
        post_path = f"{appearance_path}.post_style"
        _validate_choice(
            errors,
            f"{post_path}.profile_variant",
            appearance.post_style.profile_variant,
            APPEARANCE_POST_PROFILE_VARIANTS,
        )
        _validate_choice(
            errors,
            f"{post_path}.accent_style",
            appearance.post_style.accent_style,
            APPEARANCE_POST_ACCENT_STYLES,
        )
        _validate_choice(
            errors,
            f"{post_path}.border_style",
            appearance.post_style.border_style,
            APPEARANCE_POST_BORDER_STYLES,
        )
        _validate_choice(
            errors,
            f"{post_path}.title_style",
            appearance.post_style.title_style,
            APPEARANCE_POST_TITLE_STYLES,
        )
        _validate_choice(
            errors,
            f"{post_path}.density",
            appearance.post_style.density,
            APPEARANCE_POST_DENSITIES,
        )
    for material_variant in appearance.material_variants:
        variant_path = f"{appearance_path}.material_variants.{material_variant.material_type}"
        _validate_choice(
            errors,
            f"{variant_path}.material_type",
            material_variant.material_type,
            APPEARANCE_MATERIAL_TYPES,
        )
        _validate_choice(
            errors,
            f"{variant_path}.variant",
            material_variant.variant,
            APPEARANCE_MATERIAL_VARIANTS,
        )


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


def _is_safe_media_url(value: str) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return False
    return not (
        normalized.startswith(("javascript:", "data:")) or "<" in normalized or ">" in normalized
    )


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


def _mapping(value: object, path: str, errors: list[str]) -> dict[str, Any] | None:
    if isinstance(value, Mapping):
        mapped = {str(key): item for key, item in value.items()}
        errors.extend(
            f"{path}.{key} is not supported in Program Blueprints"
            for key in mapped
            if key in APPEARANCE_DISALLOWED_KEYS
        )
        return mapped
    errors.append(f"{path} must be a mapping")
    return None


def _optional_mapping(value: object, path: str, errors: list[str]) -> dict[str, Any]:
    if value is None:
        return {}
    return _mapping(value, path, errors) or {}


def _mapping_items(value: object, path: str, errors: list[str]) -> tuple[dict[str, Any], ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, str):
        errors.append(f"{path} must be a list")
        return ()
    items: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        mapping = _mapping(item, f"{path}[{index}]", errors)
        if mapping is not None:
            items.append(mapping)
    return tuple(items)


def _text(value: object) -> str:
    return value if isinstance(value, str) else ""


def _field(mapping: dict[str, Any], key: str) -> str:
    return _text(mapping.get(key))


def _optional_bool_field(
    mapping: dict[str, Any],
    key: str,
    path: str,
    errors: list[str],
) -> bool:
    value = mapping.get(key)
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    errors.append(f"{path} must be true or false")
    return False


def _characters_from_yaml(value: object, errors: list[str]) -> tuple[BlueprintCharacter, ...]:
    return tuple(
        BlueprintCharacter(
            slug=_field(item, "slug"),
            name=_field(item, "name"),
            summary=_field(item, "summary"),
            tagline=_field(item, "tagline"),
        )
        for item in _mapping_items(value, "characters", errors)
    )


def _boards_from_yaml(value: object, errors: list[str]) -> tuple[BlueprintBoard, ...]:
    boards: list[BlueprintBoard] = []
    for index, item in enumerate(_mapping_items(value, "boards", errors)):
        media = _optional_mapping(item.get("media"), f"boards[{index}].media", errors)
        boards.append(
            BlueprintBoard(
                slug=_field(item, "slug"),
                name=_field(item, "name"),
                board_kind=_field(item, "kind") or _field(item, "board_kind"),
                tagline=_field(item, "tagline"),
                description=_field(item, "description"),
                image_url=_field(item, "image_url")
                or _field(media, "image_url")
                or _field(media, "url"),
                image_alt=_field(item, "image_alt")
                or _field(media, "image_alt")
                or _field(media, "alt"),
                image_treatment=_field(item, "image_treatment")
                or _field(media, "image_treatment")
                or _field(media, "treatment")
                or "poster",
                image_focal_point=_field(item, "image_focal_point")
                or _field(media, "image_focal_point")
                or _field(media, "focal_point")
                or "center",
                image_overlay=_field(item, "image_overlay")
                or _field(media, "image_overlay")
                or _field(media, "overlay")
                or "medium",
            )
        )
    return tuple(boards)


def _materials_from_yaml(value: object, errors: list[str]) -> tuple[BlueprintMaterial, ...]:
    return tuple(
        BlueprintMaterial(
            slug=_field(item, "slug"),
            title=_field(item, "title"),
            material_type=_field(item, "type") or _field(item, "material_type"),
            summary=_field(item, "summary"),
            body=_field(item, "body"),
        )
        for item in _mapping_items(value, "materials", errors)
    )


def _wanted_from_yaml(value: object, errors: list[str]) -> tuple[BlueprintWanted, ...]:
    return tuple(
        BlueprintWanted(
            slug=_field(item, "slug"),
            title=_field(item, "title"),
            wanted_type=_field(item, "type") or _field(item, "wanted_type"),
            summary=_field(item, "summary"),
            body=_field(item, "body"),
            related_material_slug=_field(item, "related_material")
            or _field(item, "related_material_slug"),
        )
        for item in _mapping_items(value, "wanted", errors)
    )


def _theme_from_yaml(value: object, errors: list[str]) -> BlueprintTheme | None:
    if value is None:
        return None
    theme = _mapping(value, "theme", errors)
    if theme is None:
        return None
    typography = _mapping(theme.get("typography"), "theme.typography", errors) or {}
    light = _theme_mode_from_yaml(theme.get("light"), "theme.light", errors)
    dark = _theme_mode_from_yaml(theme.get("dark"), "theme.dark", errors)
    return BlueprintTheme(
        slug=_field(theme, "slug"),
        name=_field(theme, "name"),
        typography=BlueprintTypography(
            display=_field(typography, "display") or "system",
            body=_field(typography, "body") or "system",
            mono=_field(typography, "mono") or "mono",
        ),
        light=light,
        dark=dark,
        radius=_field(theme, "radius") or "sm",
        density=_field(theme, "density") or "calm",
        texture=_field(theme, "texture") or "none",
    )


def _appearance_from_yaml(value: object, errors: list[str]) -> BlueprintAppearance | None:
    if value is None:
        return None
    appearance = _mapping(value, "appearance", errors)
    if appearance is None:
        return None
    post_style = _post_style_from_yaml(appearance.get("post_style"), errors)
    return BlueprintAppearance(
        post_style=post_style,
        material_variants=_material_variants_from_yaml(
            appearance.get("material_variants"),
            errors,
        ),
    )


def _post_style_from_yaml(value: object, errors: list[str]) -> BlueprintPostStyle | None:
    if value is None:
        return None
    post_style = _mapping(value, "appearance.post_style", errors)
    if post_style is None:
        return None
    return BlueprintPostStyle(
        profile_variant=_field(post_style, "profile_variant") or "bio",
        accent_style=_field(post_style, "accent_style") or "soft",
        border_style=_field(post_style, "border_style") or "hairline",
        title_style=_field(post_style, "title_style") or "standard",
        density=_field(post_style, "density") or "calm",
    )


def _material_variants_from_yaml(
    value: object,
    errors: list[str],
) -> tuple[BlueprintMaterialVariant, ...]:
    if value is None:
        return ()
    variants = _mapping(value, "appearance.material_variants", errors)
    if variants is None:
        return ()
    return tuple(
        BlueprintMaterialVariant(
            material_type=str(material_type),
            variant=_text(variant),
        )
        for material_type, variant in variants.items()
    )


def _theme_mode_from_yaml(
    value: object,
    path: str,
    errors: list[str],
) -> BlueprintThemeMode:
    mode = _mapping(value, path, errors) or {}
    return BlueprintThemeMode(
        bg=_field(mode, "bg"),
        bg_subtle=_field(mode, "bg_subtle"),
        surface=_field(mode, "surface"),
        surface_elevated=_field(mode, "surface_elevated"),
        border=_field(mode, "border"),
        text=_field(mode, "text"),
        text_muted=_field(mode, "text_muted"),
        accent=_field(mode, "accent"),
        accent_hover=_field(mode, "accent_hover"),
        accent_dim=_field(mode, "accent_dim"),
        accent_secondary=_field(mode, "accent_secondary"),
        success=_field(mode, "success"),
        warning=_field(mode, "warning"),
        error=_field(mode, "error"),
    )
