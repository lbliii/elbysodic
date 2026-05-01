"""Safe community theme token rendering."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, cast

from elbysodic.domain.models import CommunityTheme

THEME_MODE_FIELDS: tuple[tuple[str, str], ...] = (
    ("bg", "Background"),
    ("bg_subtle", "Subtle background"),
    ("surface", "Surface"),
    ("surface_elevated", "Elevated surface"),
    ("border", "Border"),
    ("text", "Text"),
    ("text_muted", "Muted text"),
    ("accent", "Accent"),
    ("accent_hover", "Accent hover"),
    ("accent_dim", "Dim accent"),
    ("accent_secondary", "Secondary accent"),
    ("success", "Success"),
    ("warning", "Warning"),
    ("error", "Error"),
)
FONT_STACK_LABELS: dict[str, str] = {
    "system": "System",
    "serif": "Literary serif",
    "condensed": "Condensed",
    "mono": "Archive mono",
}
FONT_STACKS: dict[str, str] = {
    "system": "Inter, ui-sans-serif, system-ui, sans-serif",
    "serif": "Georgia, serif",
    "condensed": "Impact, Arial, sans-serif",
    "mono": "ui-monospace, monospace",
}
RADIUS_LABELS: dict[str, str] = {
    "square": "Square",
    "sm": "Soft",
    "md": "Round",
}
RADIUS_TOKENS: dict[str, tuple[str, str]] = {
    "square": ("0", "0"),
    "sm": ("0.5rem", "0.25rem"),
    "md": ("0.75rem", "0.375rem"),
}
DENSITY_LABELS: dict[str, str] = {
    "calm": "Calm",
    "compact": "Compact",
    "dramatic": "Dramatic",
}
TEXTURE_LABELS: dict[str, str] = {
    "none": "None",
    "grid": "Grid",
    "paper": "Paper",
    "scanline": "Scanline",
}
TEXTURE_TOKENS: dict[str, str] = {
    "none": "none",
    "grid": "linear-gradient(rgba(255,255,255,.045) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px)",
    "paper": "radial-gradient(circle at 20% 20%, rgba(255,255,255,.08), transparent 28%), radial-gradient(circle at 80% 10%, rgba(0,0,0,.05), transparent 22%)",
    "scanline": "repeating-linear-gradient(180deg, rgba(255,255,255,.04) 0 1px, transparent 1px 4px)",
}
MODE_VARIABLES: dict[str, str] = {
    "bg": "--chirpui-bg",
    "bg_subtle": "--chirpui-bg-subtle",
    "surface": "--chirpui-surface",
    "surface_elevated": "--chirpui-surface-elevated",
    "border": "--chirpui-border",
    "text": "--chirpui-text",
    "text_muted": "--chirpui-text-muted",
    "accent": "--chirpui-accent",
    "accent_hover": "--chirpui-accent-hover",
    "accent_dim": "--chirpui-accent-dim",
    "accent_secondary": "--chirpui-accent-secondary",
    "success": "--chirpui-success",
    "warning": "--chirpui-warning",
    "error": "--chirpui-error",
}
DEFAULT_THEME_TOKENS: dict[str, Any] = {
    "slug": "studio-default",
    "name": "Studio Default",
    "typography": {
        "display": "system",
        "body": "system",
        "mono": "mono",
    },
    "radius": "sm",
    "density": "calm",
    "texture": "none",
    "light": {
        "bg": "#f8f2ef",
        "bg_subtle": "#efe3df",
        "surface": "#fffaf8",
        "surface_elevated": "#f6ece8",
        "border": "#d8c1bb",
        "text": "#2a2020",
        "text_muted": "#756263",
        "accent": "#a3424d",
        "accent_hover": "#7f2f39",
        "accent_dim": "#c47a84",
        "accent_secondary": "#4f8465",
        "success": "#4f8465",
        "warning": "#9b6a1f",
        "error": "#a64242",
    },
    "dark": {
        "bg": "#160f12",
        "bg_subtle": "#21171a",
        "surface": "#281d20",
        "surface_elevated": "#332529",
        "border": "#5c4448",
        "text": "#f8ece9",
        "text_muted": "#c9b5b3",
        "accent": "#e38991",
        "accent_hover": "#f0a7ad",
        "accent_dim": "#7d4248",
        "accent_secondary": "#91c49a",
        "success": "#91c49a",
        "warning": "#dbb168",
        "error": "#ee8d8d",
    },
}


@dataclass(frozen=True, slots=True)
class ProgramThemeView:
    name: str
    base_variables: tuple[tuple[str, str], ...]
    light_variables: tuple[tuple[str, str], ...]
    dark_variables: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class ThemeModeEditor:
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

    def value_for(self, key: str) -> str:
        return str(getattr(self, key))


@dataclass(frozen=True, slots=True)
class ThemeEditorView:
    slug: str
    name: str
    typography_display: str
    typography_body: str
    typography_mono: str
    radius: str
    density: str
    texture: str
    light: ThemeModeEditor
    dark: ThemeModeEditor


@dataclass(frozen=True, slots=True)
class ThemeHealthWarning:
    severity: str
    title: str
    message: str
    mode: str


def community_theme_view(theme: CommunityTheme | None) -> ProgramThemeView | None:
    if theme is None:
        return None
    try:
        tokens = json.loads(theme.tokens_json)
    except json.JSONDecodeError:
        return None
    if not isinstance(tokens, dict):
        return None
    return ProgramThemeView(
        name=theme.name,
        base_variables=_base_variables(tokens),
        light_variables=_mode_variables(tokens.get("light")),
        dark_variables=_mode_variables(tokens.get("dark")),
    )


def community_theme_editor(theme: CommunityTheme | None) -> ThemeEditorView:
    tokens = _theme_tokens(theme)
    typography = _clean_mapping(tokens.get("typography"))
    return ThemeEditorView(
        slug=str(tokens.get("slug") or (theme.slug if theme else DEFAULT_THEME_TOKENS["slug"])),
        name=str(tokens.get("name") or (theme.name if theme else DEFAULT_THEME_TOKENS["name"])),
        typography_display=_choice(
            typography.get("display"),
            FONT_STACK_LABELS,
            str(DEFAULT_THEME_TOKENS["typography"]["display"]),
        ),
        typography_body=_choice(
            typography.get("body"),
            FONT_STACK_LABELS,
            str(DEFAULT_THEME_TOKENS["typography"]["body"]),
        ),
        typography_mono=_choice(
            typography.get("mono"),
            FONT_STACK_LABELS,
            str(DEFAULT_THEME_TOKENS["typography"]["mono"]),
        ),
        radius=_choice(tokens.get("radius"), RADIUS_LABELS, str(DEFAULT_THEME_TOKENS["radius"])),
        density=_choice(
            tokens.get("density"),
            DENSITY_LABELS,
            str(DEFAULT_THEME_TOKENS["density"]),
        ),
        texture=_choice(
            tokens.get("texture"),
            TEXTURE_LABELS,
            str(DEFAULT_THEME_TOKENS["texture"]),
        ),
        light=_mode_editor(tokens.get("light"), "light"),
        dark=_mode_editor(tokens.get("dark"), "dark"),
    )


def build_theme_tokens(
    *,
    slug: str,
    name: str,
    typography_display: str,
    typography_body: str,
    typography_mono: str,
    radius: str,
    density: str,
    texture: str,
    light: dict[str, str],
    dark: dict[str, str],
) -> dict[str, Any]:
    cleaned_slug = slug.strip()
    cleaned_name = name.strip()
    if not cleaned_slug:
        raise ValueError("theme slug is required")
    if not cleaned_name:
        raise ValueError("theme name is required")
    return {
        "slug": cleaned_slug,
        "name": cleaned_name,
        "typography": {
            "display": _required_choice(
                typography_display,
                FONT_STACK_LABELS,
                "display font",
            ),
            "body": _required_choice(typography_body, FONT_STACK_LABELS, "body font"),
            "mono": _required_choice(typography_mono, FONT_STACK_LABELS, "mono font"),
        },
        "radius": _required_choice(radius, RADIUS_LABELS, "radius"),
        "density": _required_choice(density, DENSITY_LABELS, "density"),
        "texture": _required_choice(texture, TEXTURE_LABELS, "texture"),
        "light": _validated_mode(light, "light"),
        "dark": _validated_mode(dark, "dark"),
    }


def theme_tokens_json(tokens: dict[str, Any]) -> str:
    return json.dumps(tokens, sort_keys=True)


def theme_health_warnings(editor: ThemeEditorView) -> tuple[ThemeHealthWarning, ...]:
    warnings: list[ThemeHealthWarning] = []
    for mode_name, mode in (("light", editor.light), ("dark", editor.dark)):
        _append_contrast_warning(
            warnings,
            mode_name,
            foreground=mode.text,
            background=mode.bg,
            minimum=4.5,
            title="Guidebook body text may be hard to read",
            message=(
                "Story prose and canon material need stronger contrast against the "
                f"{mode_name} background."
            ),
        )
        _append_contrast_warning(
            warnings,
            mode_name,
            foreground=mode.text_muted,
            background=mode.bg,
            minimum=3.0,
            title="Muted metadata may fade too far back",
            message=(
                "Writer names, latest lines, and helper copy may be difficult to scan "
                f"in {mode_name} mode."
            ),
        )
        _append_contrast_warning(
            warnings,
            mode_name,
            foreground=mode.accent,
            background=mode.surface,
            minimum=3.0,
            title="Accent actions may not stand out",
            message=(
                "Links, selected states, and character accents need enough contrast "
                f"against {mode_name} surfaces."
            ),
        )
        _append_contrast_warning(
            warnings,
            mode_name,
            foreground=mode.warning,
            background=mode.surface,
            minimum=3.0,
            title="Warnings may be too quiet",
            message=(
                "Director notes and revision requests should remain visible without "
                f"shouting in {mode_name} mode."
            ),
        )
        _append_contrast_warning(
            warnings,
            mode_name,
            foreground=mode.error,
            background=mode.surface,
            minimum=3.0,
            title="Error states may be too quiet",
            message=(
                f"Validation and blocked workflow states need clearer contrast in {mode_name} mode."
            ),
        )
    return tuple(warnings)


def _base_variables(tokens: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    typography = tokens.get("typography")
    if not isinstance(typography, dict):
        typography = {}
    body_stack = FONT_STACKS.get(str(typography.get("body") or "system"), FONT_STACKS["system"])
    display_stack = FONT_STACKS.get(
        str(typography.get("display") or "system"),
        FONT_STACKS["system"],
    )
    mono_stack = FONT_STACKS.get(str(typography.get("mono") or "mono"), FONT_STACKS["mono"])
    radius, radius_sm = RADIUS_TOKENS.get(str(tokens.get("radius") or "sm"), RADIUS_TOKENS["sm"])
    texture = TEXTURE_TOKENS.get(str(tokens.get("texture") or "none"), TEXTURE_TOKENS["none"])
    density = str(tokens.get("density") or "calm")
    return (
        ("--chirpui-ui-font-family", body_stack),
        ("--chirpui-prose-font-family", body_stack),
        ("--chirpui-font-family", body_stack),
        ("--chirpui-code-font-family", mono_stack),
        ("--chirpui-mono-font-family", mono_stack),
        ("--elbysodic-display-font-family", display_stack),
        ("--chirpui-radius", radius),
        ("--chirpui-radius-sm", radius_sm),
        ("--elbysodic-program-texture", texture),
        ("--elbysodic-program-density", density),
    )


def _mode_variables(raw_mode: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(raw_mode, dict):
        return ()
    mode = cast(dict[str, object], raw_mode)
    variables: list[tuple[str, str]] = []
    for key, variable_name in MODE_VARIABLES.items():
        value = mode.get(key)
        if isinstance(value, str) and _is_safe_css_value(value):
            variables.append((variable_name, value))
    surface = mode.get("surface")
    if isinstance(surface, str) and _is_safe_css_value(surface):
        variables.append(("--chirpui-surface-alt", surface))
    border = mode.get("border")
    if isinstance(border, str) and _is_safe_css_value(border):
        variables.append(
            ("--chirpui-border-subtle", f"color-mix(in srgb, {border} 72%, transparent)")
        )
    accent = mode.get("accent")
    text = mode.get("text")
    text_muted = mode.get("text_muted")
    if (
        isinstance(accent, str)
        and isinstance(text, str)
        and _is_safe_css_value(accent)
        and _is_safe_css_value(text)
    ):
        variables.append(("--chirpui-link", f"color-mix(in srgb, {accent} 72%, {text})"))
    if (
        isinstance(accent, str)
        and isinstance(text_muted, str)
        and _is_safe_css_value(accent)
        and _is_safe_css_value(text_muted)
    ):
        variables.append(
            ("--chirpui-link-visited", f"color-mix(in srgb, {accent} 52%, {text_muted})")
        )
    return tuple(variables)


def _theme_tokens(theme: CommunityTheme | None) -> dict[str, Any]:
    tokens = dict(DEFAULT_THEME_TOKENS)
    tokens["typography"] = dict(DEFAULT_THEME_TOKENS["typography"])
    tokens["light"] = dict(DEFAULT_THEME_TOKENS["light"])
    tokens["dark"] = dict(DEFAULT_THEME_TOKENS["dark"])
    if theme is None:
        return tokens
    try:
        raw = json.loads(theme.tokens_json)
    except json.JSONDecodeError:
        return tokens
    if not isinstance(raw, dict):
        return tokens
    tokens.update(
        {key: value for key, value in raw.items() if key not in {"typography", "light", "dark"}}
    )
    tokens["typography"].update(_clean_mapping(raw.get("typography")))
    tokens["light"].update(_clean_mapping(raw.get("light")))
    tokens["dark"].update(_clean_mapping(raw.get("dark")))
    return tokens


def _clean_mapping(value: object) -> dict[str, object]:
    return dict(cast(dict[str, object], value)) if isinstance(value, dict) else {}


def _choice(value: object, labels: dict[str, str], fallback: str) -> str:
    candidate = str(value or "")
    return candidate if candidate in labels else fallback


def _required_choice(value: str, labels: dict[str, str], label: str) -> str:
    candidate = value.strip()
    if candidate not in labels:
        allowed = ", ".join(labels)
        raise ValueError(f"{label} must be one of: {allowed}")
    return candidate


def _mode_editor(value: object, mode_name: str) -> ThemeModeEditor:
    raw = _clean_mapping(value)
    defaults = cast(dict[str, str], DEFAULT_THEME_TOKENS[mode_name])
    values = {key: str(raw.get(key) or defaults[key]) for key, _label in THEME_MODE_FIELDS}
    return ThemeModeEditor(**values)


def _validated_mode(values: dict[str, str], mode_name: str) -> dict[str, str]:
    mode: dict[str, str] = {}
    for key, label in THEME_MODE_FIELDS:
        value = values.get(key, "").strip()
        if not _is_hex_color(value):
            raise ValueError(f"{mode_name} {label.lower()} must be a 6-digit hex color")
        mode[key] = value
    return mode


def _append_contrast_warning(
    warnings: list[ThemeHealthWarning],
    mode: str,
    *,
    foreground: str,
    background: str,
    minimum: float,
    title: str,
    message: str,
) -> None:
    ratio = _contrast_ratio(foreground, background)
    if ratio < minimum:
        warnings.append(
            ThemeHealthWarning(
                severity="warning",
                title=title,
                message=f"{message} Current ratio: {ratio:.2f}:1.",
                mode=mode,
            )
        )


def _contrast_ratio(foreground: str, background: str) -> float:
    foreground_luminance = _relative_luminance(foreground)
    background_luminance = _relative_luminance(background)
    lighter = max(foreground_luminance, background_luminance)
    darker = min(foreground_luminance, background_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def _relative_luminance(hex_color: str) -> float:
    channels = tuple(int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5))
    linear_channels = tuple(_linear_channel(channel) for channel in channels)
    red, green, blue = linear_channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _linear_channel(channel: float) -> float:
    if channel <= 0.03928:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _is_hex_color(value: str) -> bool:
    return (
        len(value) == 7
        and value.startswith("#")
        and all(character in "0123456789abcdefABCDEF" for character in value[1:])
    )


def _is_safe_css_value(value: str) -> bool:
    allowed = set(
        "#0123456789abcdefABCDEF(),.% -abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )
    return bool(value) and all(character in allowed for character in value)
