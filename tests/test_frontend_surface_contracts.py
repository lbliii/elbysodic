from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PAGES = REPO_ROOT / "src/elbysodic/web/pages"
PACK_DOC = REPO_ROOT / "docs/product/front-end-surface-conversion-pack.md"


SURFACE_COMPONENT_EXPECTATIONS = {
    "login/page.html": [
        'from "_components/access.html" import product_identity',
        "product_identity()",
        "Choose the account first",
    ],
    "request-access/page.html": [
        'from "_components/access.html" import access_account_notice, product_identity',
        "access_account_notice(",
        "Request access",
    ],
    "desk/page.html": [
        'from "_components/ui.html" import empty_policy_block, page_section',
        'from "_components/vocabulary.html" import command_action, lane_preview, metric_item, page_pulse',
        "needs_first_face",
    ],
    "applications/page.html": [
        'from "_components/facets.html" import facet_pills',
        'from "_components/ui.html" import empty_policy_block, page_section',
        'from "_components/vocabulary.html" import command_panel, metric_item',
    ],
    "claims/page.html": [
        'from "_components/ui.html" import empty_policy_block',
        "Claims",
        "reserved",
    ],
    "wanted/page.html": [
        'from "_components/ui.html" import empty_policy_block',
        'from "_components/wanted.html" import wanted_card',
        "wanted hooks",
    ],
    "wanted/{wanted_slug}/page.html": [
        'from "_components/facets.html" import facet_pills',
        'from "_components/wanted.html" import thread_signal, wanted_card',
        "plotting",
    ],
    "notifications/page.html": [
        'from "_components/ui.html" import empty_policy_block',
        'from "_components/vocabulary.html" import metric_item, page_pulse',
        "Mark all read",
    ],
    "network/page.html": [
        'from "_components/network_catalog.html" import program_card, program_summary',
        'from "_components/vocabulary.html" import metric_item',
        "network_access_posture",
    ],
    "page.html": [
        'from "_components/realm_gateway.html" import realm_gateway_home',
        'from "_components/director_controls.html" import director_context_panel',
        "realm_gateway_home(",
    ],
    "studio/page.html": [
        'from "_components/facets.html" import facet_pills',
        'from "_components/ui.html" import empty_policy_block',
        'from "_components/vocabulary.html" import room_header',
    ],
    "boards/{board_slug}/threads/new/page.html": [
        'from "_components/composer.html" import composer_toolbar, composer_view_toggle',
        "idempotency_key",
        "Start scene",
    ],
    "boards/{board_slug}/threads/{thread_slug}/page.html": [
        'from "_components/composer.html" import composer_toolbar, composer_view_toggle',
        'from "_components/posts.html" import post_frame',
        "reply-character",
    ],
}


@pytest.mark.parametrize(
    ("template_path", "required_snippets"),
    SURFACE_COMPONENT_EXPECTATIONS.items(),
)
def test_high_risk_templates_use_shared_frontend_surface_patterns(
    template_path: str,
    required_snippets: list[str],
) -> None:
    text = (PAGES / template_path).read_text(encoding="utf-8")

    for snippet in required_snippets:
        assert snippet in text, f"{template_path} is missing {snippet!r}"


def test_frontend_surface_conversion_pack_names_required_audit_profiles() -> None:
    text = PACK_DOC.read_text(encoding="utf-8")

    for required in [
        "Shared Pattern Inventory",
        "CSS And Token Audit",
        "Label And Typography Audit",
        "Accessibility Audit",
        "Browser QA Profiles",
        "Auth/access",
        "Public preview",
        "Account visitor",
        "Writer onboarding",
        "Studio",
        "Public catalog",
    ]:
        assert required in text


def test_access_and_search_surfaces_keep_labelled_controls() -> None:
    expectations = {
        "login/page.html": [
            "<span>Email</span>",
            "<span>Password</span>",
            'autocomplete="username"',
            'autocomplete="current-password"',
        ],
        "request-access/page.html": [
            "<span>Writer email</span>",
            "<span>Writer name</span>",
            "<span>Face concept</span>",
            "<span>Wanted hook or way in</span>",
            "<span>Notes for directors</span>",
            'role="status"',
            'role="alert"',
        ],
        "network/page.html": [
            'role="search"',
            'label for="network-search"',
            'type="search"',
        ],
        "_layout.html": [
            'role="search"',
            'for="elbysodic-topbar-search-input"',
            'aria-label="Search {{ scope_label }}"',
        ],
    }

    for template_path, required_snippets in expectations.items():
        text = (PAGES / template_path).read_text(encoding="utf-8")
        for snippet in required_snippets:
            assert snippet in text, f"{template_path} is missing {snippet!r}"
