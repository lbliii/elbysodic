"""Safe post body rendering for forum content."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from kida.template import Markup

_LINK_RE = re.compile(r"\[([^\]\n]+)\]\(([^)\s]+)\)")
_MENTION_RE = re.compile(r"(?<![\w-])@([A-Za-z0-9][\w-]*)")
_STRONG_RE = re.compile(r"\*\*([^*\n]+)\*\*")
_EM_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_SAFE_SCHEMES = {"http", "https", "mailto"}


@dataclass(frozen=True, slots=True)
class MentionLink:
    handle: str
    href: str
    label: str
    kind: str


def render_post_body(value: str, *, mentions: list[MentionLink] | None = None) -> Markup:
    """Render a user-authored post body as sanitized HTML."""

    blocks = _blocks(value)
    if not blocks:
        return Markup("")
    mention_map = {mention.handle.lower(): mention for mention in mentions or []}
    return Markup("".join(_render_block(kind, lines, mention_map) for kind, lines in blocks))


def post_snippet(value: str, *, limit: int = 130) -> str:
    cleaned = " ".join(value.split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 1].rstrip()}..."


def _blocks(value: str) -> list[tuple[str, list[str]]]:
    lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[tuple[str, list[str]]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.lstrip().startswith(">"):
            quote_lines = []
            while index < len(lines) and lines[index].lstrip().startswith(">"):
                quote_lines.append(_strip_quote_marker(lines[index]))
                index += 1
            blocks.append(("quote", quote_lines))
            continue

        paragraph_lines = []
        while (
            index < len(lines)
            and lines[index].strip()
            and not lines[index].lstrip().startswith(">")
        ):
            paragraph_lines.append(lines[index].strip())
            index += 1
        blocks.append(("paragraph", paragraph_lines))
    return blocks


def _strip_quote_marker(value: str) -> str:
    stripped = value.lstrip()[1:]
    if stripped.startswith(" "):
        stripped = stripped[1:]
    return stripped


def _render_block(kind: str, lines: list[str], mentions: dict[str, MentionLink]) -> str:
    paragraphs = _paragraphs(lines, mentions)
    if kind == "quote":
        return f"<blockquote>{''.join(paragraphs)}</blockquote>"
    return "".join(paragraphs)


def _paragraphs(lines: list[str], mentions: dict[str, MentionLink]) -> list[str]:
    chunks: list[list[str]] = [[]]
    for line in lines:
        if line.strip():
            chunks[-1].append(line)
        elif chunks[-1]:
            chunks.append([])
    return [f"<p>{_render_inline_lines(chunk, mentions)}</p>" for chunk in chunks if chunk]


def _render_inline_lines(lines: list[str], mentions: dict[str, MentionLink]) -> str:
    return "<br>".join(_render_inline(line, mentions) for line in lines)


def _render_inline(value: str, mentions: dict[str, MentionLink]) -> str:
    rendered = []
    last_end = 0
    for match in _LINK_RE.finditer(value):
        rendered.append(_render_mentions(value[last_end : match.start()], mentions))
        href = _safe_href(match.group(2))
        if href is None:
            rendered.append(_render_mentions(match.group(0), mentions))
        else:
            label = _render_emphasis(html.escape(match.group(1), quote=True))
            rendered.append(
                f'<a class="chirpui-link" href="{html.escape(href, quote=True)}">{label}</a>'
            )
        last_end = match.end()
    rendered.append(_render_mentions(value[last_end:], mentions))
    return "".join(rendered)


def _render_mentions(value: str, mentions: dict[str, MentionLink]) -> str:
    rendered = []
    last_end = 0
    for match in _MENTION_RE.finditer(value):
        rendered.append(_render_emphasis(html.escape(value[last_end : match.start()], quote=True)))
        handle = match.group(1).lower()
        mention = mentions.get(handle)
        if mention is None:
            rendered.append(_render_emphasis(html.escape(match.group(0), quote=True)))
        else:
            rendered.append(
                '<a class="chirpui-mention elbysodic-mention-link" '
                f'data-mention-kind="{html.escape(mention.kind, quote=True)}" '
                f'href="{html.escape(mention.href, quote=True)}" '
                f'title="{html.escape(mention.label, quote=True)}">'
                f"@{html.escape(mention.handle, quote=True)}</a>"
            )
        last_end = match.end()
    rendered.append(_render_emphasis(html.escape(value[last_end:], quote=True)))
    return "".join(rendered)


def _render_emphasis(value: str) -> str:
    strong = _STRONG_RE.sub(r"<strong>\1</strong>", value)
    return _EM_RE.sub(r"<em>\1</em>", strong)


def _safe_href(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme:
        if parsed.scheme.lower() in _SAFE_SCHEMES:
            return value
        return None
    if value.startswith(("/", "#")):
        return value
    return None
