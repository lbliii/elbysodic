from __future__ import annotations

from elbysodic.services.markup import post_snippet, render_post_body


def test_post_markup_renders_small_safe_dialect() -> None:
    rendered = str(
        render_post_body(
            "**Rogue** drops in.\n"
            "> Keep moving.\n"
            "> *Now.*\n\n"
            "[Briefing](/boards/plotting) and [bad](javascript:alert(1))"
        )
    )

    assert "<strong>Rogue</strong>" in rendered
    assert "<blockquote><p>Keep moving.<br><em>Now.</em></p></blockquote>" in rendered
    assert 'href="/boards/plotting"' in rendered
    assert '<a class="chirpui-link" href="javascript:alert(1)"' not in rendered
    assert "[bad](javascript:alert(1))" in rendered


def test_post_markup_escapes_raw_html() -> None:
    rendered = str(render_post_body('Hello <script>alert("x")</script>'))

    assert "<script>" not in rendered
    assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in rendered


def test_post_snippet_collapses_whitespace_and_truncates() -> None:
    assert post_snippet("Rogue\n\nanswers   late.") == "Rogue answers late."
    assert post_snippet("x" * 132, limit=10) == "xxxxxxxxx..."
