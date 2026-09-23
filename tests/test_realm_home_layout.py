from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
COMPOSITIONS_CSS = REPO_ROOT / "src/elbysodic/web/static/elbysodic-theme/50-page-compositions.css"
GATEWAY_COMPONENT = REPO_ROOT / "src/elbysodic/web/pages/_components/realm_gateway.html"


def _declarations(css: str, selector: str) -> list[str]:
    pattern = re.compile(rf"(?m)^\s*{re.escape(selector)}\s*\{{([^{{}}]*)\}}")
    return [match.group(1) for match in pattern.finditer(css)]


def _media_declarations(css: str, max_width: str, selector: str) -> str:
    pattern = re.compile(
        rf"@media\s*\(\s*max-width:\s*{re.escape(max_width)}\s*\)\s*\{{"
        rf"(?P<rules>.*?)(?=^\}})",
        re.DOTALL | re.MULTILINE,
    )
    media = pattern.search(css)
    assert media is not None, f"missing {max_width} responsive rules"
    blocks = _declarations(media.group("rules"), selector)
    assert blocks, f"missing {selector} rules at {max_width}"
    return blocks[-1]


def test_realm_home_hero_title_and_actions_stay_clear_of_media() -> None:
    css = COMPOSITIONS_CSS.read_text(encoding="utf-8")
    component = GATEWAY_COMPONENT.read_text(encoding="utf-8")

    title_rules = _declarations(css, ".elbysodic-realm-gateway-hero h1")
    assert title_rules
    assert "max-inline-size: 100%;" in title_rules[0]
    assert "overflow-wrap: anywhere;" in title_rules[0]

    stacked_hero = _media_declarations(
        css,
        "72rem",
        ".elbysodic-realm-gateway-hero",
    )
    assert "grid-template-columns: minmax(0, 1fr);" in stacked_hero
    assert "min-block-size: 0;" in stacked_hero

    stacked_media = _media_declarations(
        css,
        "72rem",
        ".elbysodic-realm-gateway-hero__media",
    )
    assert "grid-template-rows: minmax(clamp(12rem, 32vw, 18rem), 1fr) auto;" in (stacked_media)
    assert "transform: none;" in stacked_media

    mobile_title = _media_declarations(
        css,
        "48rem",
        ".elbysodic-realm-gateway-hero h1",
    )
    assert "max-inline-size: 100%;" in mobile_title

    title = component.index('<h1 id="realm-gateway-title">')
    actions = component.index('class="chirpui-cluster elbysodic-realm-gateway-hero__actions"')
    media = component.index('class="elbysodic-realm-gateway-hero__media"')
    assert title < actions < media
