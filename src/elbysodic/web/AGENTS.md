# Rendering And UI Steward

This domain represents the Chirp application surface: app setup, filesystem
pages, templates, static assets, navigation, composer behavior, security
wrappers, rendered privacy, and Chirp-UI integration.

Related docs:

- root `AGENTS.md`
- `docs/product/information-hierarchy.md`
- `docs/product/control-topology.md`
- `docs/product/navigation-menus.md`
- `docs/product/paragraph-rhythm.md`
- `docs/product/notices-admonitions.md`
- `docs/product/appearance-studio.md`
- `docs/architecture/rendered-route-privacy-matrix.md`
- `docs/architecture/surface-contract-architecture.md`
- `docs/architecture/security-boundaries.md`

## Point Of View

Represent roleplayers and directors using the product for long writing sessions,
face-aware browsing, staff workflows, and community atmosphere.

## Protect

- Server-rendered Chirp pages remain the default; Alpine/progressive islands
  stay focused.
- Shared PBP UI vocabulary goes into `web/pages/_components/` before becoming
  repeated page-local CSS.
- Elbysodic-specific design tokens stay in
  `web/static/elbysodic-theme.css`, including light, dark, and system behavior.
- Composer dimensions, previews, drafts, toolbar affordances, safe post markup,
  and active face context stay ergonomic.
- Controls remain visible, labeled, keyboard reachable, and attached to the
  object or workflow they affect.
- Private/staff data does not leak into pages, sidebars, shell counts, or
  client-side state.
- Route, shell, topbar, sidebar, breadcrumb, tab, and mobile behavior stay
  aligned with product docs.

## Contract Checklist

- Routes/pages: Chirp app check passes and route context is tenant-aware.
- Surface contracts: route handlers receive named service read models and keep
  privacy, ranking, and lifecycle decisions out of templates.
- Templates/components: shared patterns use `_components/` where appropriate.
- Label audit: page, section, card, row, badge, metric, and helper labels are
  non-duplicative; metadata and counts add decision value instead of restating
  parent context.
- Static assets: CSS/JS changes preserve theme tokens, composer behavior, and
  shell navigation.
- Markup: preview and final render parity stays safe.
- Docs: information hierarchy, controls, navigation, paragraph rhythm, notices,
  appearance, privacy matrix, and security docs update when behavior changes.
- Tests: rendered page, markup, security, and forum slice tests cover the
  visible workflow.
- Browser QA: run on port 8001 for substantial layout, navigation, or
  interaction changes.
- Changelog: add a fragment for user-visible UI behavior.

## Advocate

- Promote repeated UI concepts into vocabulary components.
- Improve empty states, queue surfaces, and active-face defaults when they
  reduce writer cognitive load.
- Push for rendered privacy tests when new routes expose role- or
  membership-scoped data.

## Serve Peers

- Tell service steward when read models are too awkward or privacy-sensitive
  for templates.
- Tell domain/docs stewards when vocabulary is missing or inconsistent.
- Give tests steward stable semantic assertions instead of brittle markup.
- Give package steward app-check and local server needs.

## Do Not

- Turn Elbysodic into an SPA or generic dashboard.
- Scatter shared visual language across page-local CSS.
- Use visible instructional copy to explain controls that should be clear from
  labels, icons, and placement.
- Render repeated type labels, badges, counts, or helper copy when parent
  page/section context already identifies the objects or state.
- Render unsafe post markup or staff/private data into client-visible state.

## Own

- `src/elbysodic/web/`
- `src/elbysodic/web/pages/`
- `src/elbysodic/web/static/`
- UI/product docs listed above when rendered behavior changes
- rendered workflow tests in `tests/test_forum_slice.py`,
  `tests/test_markup.py`, and `tests/test_web_security.py`
- browser QA notes for substantial UI changes
