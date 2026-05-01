# Rendering And UI Steward

## Steward

Rendering and UI steward for `src/elbysodic/web/`: Chirp app setup,
filesystem pages, templates, static assets, navigation, composer behavior, and
Chirp-UI integration.

## Protects

- Server-rendered Chirp pages stay the default, with small progressive
  enhancement islands for focused interactions.
- Repeated PBP UI concepts move into `web/pages/_components/` before becoming
  page-local patterns.
- Elbysodic-specific design tokens and styles stay in
  `web/static/elbysodic-theme.css`.
- Composer, previews, drafts, active face, and long-form post readability stay
  ergonomic for real writing sessions.

## Must Not Become

- A single-page app or client-state rewrite.
- A generic dashboard skin that visually outshouts the community's world.
- A tangle of page-local CSS for shared PBP concepts.

## Documentation Ownership

Owns product docs for information hierarchy, control topology, navigation,
paragraph rhythm, and notices whenever templates or static assets change those
contracts.

## Local Checks

- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`
- `uv run pytest tests/test_forum_slice.py -q --tb=short`
- `uv run pytest tests/test_markup.py -q --tb=short` for composer/prose changes.
- Browser QA on port 8001 for substantial layout, navigation, or interaction
  changes.

## Public Contracts And Safety

- Keep controls visible, labeled, keyboard reachable, and attached to the
  object or workflow they affect.
- Do not render unsafe post markup; preserve preview and final render parity.
- Keep route/navigation changes aligned with `docs/product/navigation-menus.md`.
- Avoid leaking private/staff data into pages, sidebars, shell counts, or
  client-side state.
