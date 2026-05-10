# Circle Terminals App Touchpoints

Date: 2026-05-10

This maps where the selected Circle Terminals logo should enter the app. The
logo is the Elbysodic product/platform mark, not a community mark. Community
marks remain director-controlled media attached to `Community`.

## Product Identity Rules

- Use Circle Terminals for global Elbysodic identity, platform attribution,
  browser/app metadata, and non-community auth/recovery surfaces.
- Keep `community_mark_url` for the current realm/program identity. Do not
  replace community marks in the topbar, Studio media settings, or Network
  cards.
- In community shell chrome, product identity should be secondary: visible in
  "Built on Elbysodic" and possibly as a small mark in the footer, not fighting
  the realm name.
- In global/no-community pages, Circle Terminals can be primary because the
  user is interacting with the Studio Network or account surface.

## Immediate App Touchpoints

1. Static asset home

   Copy production-ready SVGs from this kit into `src/elbysodic/web/static/`,
   likely under `src/elbysodic/web/static/brand/`.

   Suggested files:

   - `brand/elbysodic-mark.svg`
   - `brand/elbysodic-mark-small.svg`
   - `brand/elbysodic-favicon.svg`
   - `brand/elbysodic-mark-one-color-dark.svg`
   - `brand/elbysodic-lockup-horizontal.svg`
   - `brand/elbysodic-lockup-compact.svg`

2. Browser metadata

   Add favicon and touch icon links in `src/elbysodic/web/pages/_layout.html`
   head. The app currently loads theme CSS and scripts there, but no product
   favicon/touch metadata is present.

   Recommended:

   - `<link rel="icon" href="/elbysodic-static/brand/elbysodic-favicon.svg" type="image/svg+xml">`
   - Optional later PNG/apple-touch-icon export if needed.

3. Global brand link fallback

   `src/elbysodic/web/pages/_layout.html` already renders the topbar brand.
   When there is a community, it uses `viewer.community.community_mark_url`.
   When there is no community, it only renders the text `Elbysodic`.

   Add the product mark only for the no-community/global case:

   - `/`
   - `/network`
   - `/login`
   - `/request-access`
   - recovery pages when no community is resolved

   Do not replace community marks for tenant pages.

4. Sidebar platform attribution

   `src/elbysodic/web/pages/_components/sidebar.html` has
   `sidebar_footer()` rendering:

   ```html
   Built on <strong>Elbysodic</strong>
   ```

   This is the best community-shell touchpoint for Circle Terminals. Add a
   small product mark before "Built on", with `alt=""` because the footer text
   already supplies the accessible name.

5. Auth and access surfaces

   `src/elbysodic/web/pages/login/page.html` and
   `src/elbysodic/web/pages/request-access/page.html` currently rely on text
   headings. These should use either the compact lockup or the mark plus
   `Elbysodic` as a calm product identity block.

   Keep the pages utilitarian: no marketing hero, no decorative explanation.

6. Recovery/error surfaces

   `src/elbysodic/web/pages/recovery/_page.html` is an account/identity
   recovery surface. A small product mark can anchor trust without implying a
   community context.

7. Network home

   `src/elbysodic/web/pages/network/page.html` uses community marks inside
   program cards/billboards. Leave those alone. Add Circle Terminals only as
   page-level global product identity if needed, such as a small lockup in the
   network masthead.

8. CSS and tokens

   Add product-mark styling to `src/elbysodic/web/static/elbysodic-theme.css`.

   Candidate classes:

   - `.elbysodic-product-mark`
   - `.elbysodic-product-mark--sm`
   - `.elbysodic-product-lockup`
   - `.elbysodic-platform-mark__logo`

   Keep dimensions fixed and responsive-safe:

   - topbar/global brand mark: `2rem`
   - sidebar footer mark: `1.25rem`
   - auth lockup mark: `3rem`
   - no layout shifts on hover/focus

9. Tests

   Update rendered-page tests in `tests/test_forum_slice.py`.

   Add/adjust assertions for:

   - root/global shell includes `/elbysodic-static/brand/elbysodic-mark.svg`
     while community shell still uses the community mark.
   - community pages still show `viewer.community.community_mark_url`.
   - sidebar footer includes product mark and "Built on Elbysodic".
   - login/request-access pages include product identity without requiring a
     community.

10. Browser QA

   Because this changes shell/header/sidebar visuals, run browser QA on:

   - global root `/`
   - `/network`
   - `/login`
   - `/request-access`
   - one tenant home, e.g. `/c/x-men-apocalypse`
   - one deep thread page
   - mobile width around 375px

## Not Touchpoints

- Do not change `community_mark_url`, `community_mark_alt`, schema,
  repositories, services, or Studio community media behavior for this product
  logo work.
- Do not replace seed community marks. They are realm identity assets.
- Do not expose Circle Terminals through Appearance Studio as a community
  customization control.
- Do not add raw SVG markup into templates unless there is a strong reason;
  prefer static SVG files with stable CSS sizing.

## Suggested Implementation Order

1. Copy final brand SVGs into `src/elbysodic/web/static/brand/`.
2. Add a shared template helper/macro for product mark rendering if repeated
   more than twice.
3. Add favicon metadata in `_layout.html`.
4. Add no-community brand mark in `_layout.html`.
5. Add sidebar footer product mark in `_components/sidebar.html`.
6. Add auth/access/recovery identity blocks.
7. Add CSS in `elbysodic-theme.css`.
8. Update rendered tests.
9. Run app check and focused rendered tests.
10. Run browser QA screenshots for shell/header/sidebar.
