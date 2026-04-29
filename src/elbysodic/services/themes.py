"""Safe community theme token rendering."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, cast

from elbysodic.domain.models import CommunityTheme

FONT_STACKS: dict[str, str] = {
    "system": "Inter, ui-sans-serif, system-ui, sans-serif",
    "serif": "Georgia, serif",
    "condensed": "Impact, Arial, sans-serif",
    "mono": "ui-monospace, monospace",
}
RADIUS_TOKENS: dict[str, tuple[str, str]] = {
    "square": ("0", "0"),
    "sm": ("0.5rem", "0.25rem"),
    "md": ("0.75rem", "0.375rem"),
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


@dataclass(frozen=True, slots=True)
class ProgramThemeView:
    name: str
    base_variables: tuple[tuple[str, str], ...]
    light_variables: tuple[tuple[str, str], ...]
    dark_variables: tuple[tuple[str, str], ...]


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


def _is_safe_css_value(value: str) -> bool:
    allowed = set(
        "#0123456789abcdefABCDEF(),.% -abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )
    return bool(value) and all(character in allowed for character in value)
