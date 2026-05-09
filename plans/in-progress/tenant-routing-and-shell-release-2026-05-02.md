# Tenant Routing And Shell Release Plan

Created: 2026-05-02
Last updated: 2026-05-09
Review by: 2026-05-16
Owner: Web, service, storage, domain, and Chirp integration stewardship
Status: implemented locally; production smoke and global entry polish remain

## 2026-05-09 Verification Update

Tenant-prefix middleware, scoped link generation, boosted shell regression
coverage, identity switching, and cross-realm recovery tests exist locally.
This plan should now track only production shared-host proof and global entry
polish: hard refresh, boosted navigation, login redirect recovery, membership
switching, seed media, and canonical `/c/{community_slug}` links on Railway.

## Problem

The Railway deployment currently has two related launch blockers:

1. Boosted shell navigation can swap an empty inner shell. The app shell has
   `hx-select="#page-content"`, but boosted fragment responses can return a
   fragment rooted at `#page-root` without `#page-content`. HTMX selects
   nothing and clears `<main>`.
2. Shareable links are not fully self-describing on the shared Railway host.
   Routes such as `/world/b-24-winter`, `/boards/paddock-twelve`, and
   `/wanted/brotherhood-rival-for-rogue` resolve slugs inside whichever
   community the request identity resolver chooses. On a single shared host,
   that can come from the host, session-selected community, development
   identity, or default community.

The current Railway root at `https://elbysodic-production.up.railway.app/`
resolves to X-Men Apocalypse. That makes `/world/b-24-winter` work there, but
Jurassic links such as `/boards/paddock-twelve` depend on the request resolving
to Jurassic first. A user should be able to send a forum, board, thread,
material, wanted hook, or character link that opens the same program regardless
of another user's current session state.

## Product Decision

Support two canonical URL modes:

- Community-specific hosts keep clean local paths:
  - `https://xmen.example.com/world/b-24-winter`
  - `https://jurassic.example.com/boards/paddock-twelve`
- Shared studio/demo hosts use a community path prefix:
  - `/c/x-men-apocalypse/world/b-24-winter`
  - `/c/jurassic-park-universe/boards/paddock-twelve`

Session state may choose a writer membership and active face, but canonical
content URLs must carry enough tenant information to resolve the community
before local slug lookup. The root path on a shared Railway host can remain a
default/demo landing route, but generated cross-program links should use the
prefixed form unless the current host is already canonical for that community.

## Steward Consultation Rollup

Consulted stewards:

| Steward | Priority | Evidence | Risk / Ordering |
| --- | --- | --- | --- |
| Root product constitution | Preserve one-community-per-install MVP while keeping tenant-aware architecture real. | Root guide says architecture is tenant-aware from day one and communities are scoped production spaces. | Do not flatten community into session state or global slugs. |
| Web / rendering | Keep server-rendered Chirp and small progressive enhancement; fix shell navigation through layout/outlet semantics. | `src/elbysodic/web/AGENTS.md`; shell layout currently uses HTMX and Chirp-UI app shell. | The blank shell should be fixed in Chirp/renderer behavior, not by turning Elbysodic into an SPA. |
| Service layer | Resolve community, membership, role, and active face deliberately. | `RequestIdentityResolver` already centralizes community resolution and service methods consume `viewer.community`. | Path tenant resolution must happen before local slug lookup and cannot trust client-side state. |
| Domain model | Keep community, membership, character, board, thread, material, wanted, and plotting primitives explicitly scoped. | `src/elbysodic/domain/AGENTS.md`; schema already uses `community_id` and `communities.slug`. | Avoid global characters or user-level staff power while adding canonical URLs. |
| Storage / migrations | Reuse existing tenant fields before adding schema. | `communities.slug` and `communities.host` already exist with uniqueness. | Schema change is not needed for the first path-prefix implementation unless host aliases or custom domains need multiple rows. |
| Navigation docs | Navigation should answer the current room and contextual map without duplicating hierarchy. | `docs/product/navigation-menus.md` keeps topbar as realms and sidebar as contextual route map. | URL prefix must not appear as a new visible topbar realm; it is routing context, not product navigation. |

## Current State

- `communities.host` exists and `RequestIdentityResolver` tries host matching
  before session/default resolution.
- `communities.slug` exists and is unique.
- Most repository and service reads are already community-scoped.
- Filesystem page routes are still authored as local-path routes such as
  `/world/{material_slug}` and `/boards/{board_slug}`.
- `TenantPrefixMiddleware` resolves `/c/{community_slug}` before page routing,
  strips the prefix for the page tree, and scopes rendered links back into the
  prefixed URL space.
- Boosted shell navigation has Chirp 0.6 outlet regression coverage for both
  local and tenant-prefixed routes.
- Route timing headers are available for measuring local route work before a
  Railway timing readout.
- Remaining verification is live shared-host QA, plus tightening the global
  Elbysodic/LBSodic home and any cross-program entry controls that still emit
  unprefixed community routes.

## Priority Reset: 2026-05-03

Recommendation: treat the shared-host studio network as the next production
spine. Community forums are now solid enough that the highest leverage work is
making the platform layer explicit: `/` as the Elbysodic/LBSodic home,
`/c/{community_slug}` as the canonical community home on shared hosts, and
community switching that always carries the target program in the URL.

Why now:

- Railway exposes multiple seeded programs on one host, so unprefixed routes
  are no longer only a developer convenience.
- The identity dropdown is a high-frequency cross-program control; if it posts
  an unprefixed `next`, it trains the app back toward session-hydrated global
  paths.
- The product narrative is shifting from "one forum install" to "a hub of
  playable communities," and the routing contract needs to be visible in daily
  navigation before adding more studio/global pages.

Immediate order:

1. Finish identity and entry controls so every cross-program move targets
   `/c/{target_community_slug}` or a scoped child path.
2. Audit root/global pages and decide the small outside-community set for the
   first production cut: `/`, `/network`, `/login`, `/logout`, `/health`,
   static assets, and future account/browse pages.
3. Promote the network page from a QA directory into the Elbysodic/LBSodic home
   pattern: clear platform brand, reachable programs, current membership/face,
   and no community sidebar.
4. Run Railway shared-host browser QA against hard refresh, fresh session, and
   boosted navigation across at least X-Men and Jurassic.
5. Add timing readout only after the route contract is stable enough that the
   measured paths are the paths users will actually share.

## Phase 0: Production Triage

Goal: keep Railway usable while the platform-correct fixes are prepared.

Work:

- Merge the static package-data fix so nested seed media ships in the wheel.
- Set Railway production env explicitly:
  - `ELBYSODIC_ENV=production`
  - `ELBYSODIC_SECRET_KEY=<stable generated secret>`
  - `ELBYSODIC_DEMO_MODE=1` only for intentional seeded demo credentials
- Decide whether to add a temporary Elbysodic workaround for blank shell
  navigation while waiting on Chirp:
  - disable boosted shell navigation on production, or
  - add an `HX-Reselect` bridge for boosted `#main` responses
- Treat any workaround as temporary and remove it after the Chirp release is
  consumed.

Acceptance checks:

- Fresh Chrome/Safari no longer auto-resolve a development identity.
- Seed media URLs under `/elbysodic-static/seed-media/...` return `200`.
- Clicking through production does not leave an empty `<main>`, even if the
  temporary answer is hard navigation.

## Phase 1: Chirp Shell Outlet Release

Goal: make boosted shell navigation render the correct selectable content from
the framework layer.

Work:

- Patch/release `bengal-chirp` with outlet-aware shell rendering behavior.
- Confirm app-shell layouts can declare:

```jinja
{# target: body #}
{# outlet: main #}
```

- Update Elbysodic's `_layout.html` to include `{# outlet: main #}` only after
  the released renderer supports it.
- Add a regression test that requests a boosted main navigation response:
  - `HX-Request: true`
  - `HX-Boosted: true`
  - `HX-Target: main`
  - path such as `/wanted/brotherhood-rival-for-rogue`
- Assert the response is non-empty and includes the selectable page content
  expected by the shell.
- Remove any temporary `HX-Reselect` or boosted-navigation workaround.

Acceptance checks:

- Boosted navigation into `/world/...`, `/wanted/...`, `/boards/...`, and thread
  composer routes swaps real content into `<main>`.
- Hard refresh and boosted navigation render equivalent page content.
- No route relies on client-side hydration to populate the primary page body.

## Phase 2: Canonical Tenant URL Contract

Goal: define exactly how a request chooses the community before resolving local
slugs.

Resolution order:

1. Community path prefix, when present: `/c/{community_slug}/...`
2. Canonical community host, when present and not a shared host.
3. Session-selected community for unprefixed routes on shared hosts.
4. Deployment default community for unprefixed routes on shared hosts.

Rules:

- A path prefix is explicit tenant intent and should override session state.
- On a community-specific host, an incompatible `/c/{other_community}/...`
  should redirect to the other community's canonical host if available, or
  return a clear recovery/404 if not.
- On the shared Railway host, generated links to non-current communities should
  include `/c/{community_slug}`.
- On a community-specific host, generated links for that same community should
  stay clean and unprefixed.
- The prefix is infrastructure context, not user-facing navigation. Topbar and
  sidebar labels remain `World`, `Guidebook`, `Wanted`, `Writer Desk`, and
  `Studio`.

Acceptance checks:

- `/c/x-men-apocalypse/world/b-24-winter` always resolves to X-Men.
- `/c/jurassic-park-universe/boards/paddock-twelve` always resolves to
  Jurassic.
- `/world/b-24-winter` can still work on the X-Men host or shared default, but
  it is no longer the only shareable form on a shared host.

## Phase 3: Tenant Prefix Middleware

Goal: make prefixed routes work without duplicating the filesystem page tree.

Work:

- Add a request middleware before page routing that detects `/c/{community_slug}`.
- Resolve the slug with `repo.get_community_by_slug`.
- Store the explicit tenant slug/community id on request scope/state for
  `RequestIdentityResolver`.
- Strip the prefix before filesystem page routing so existing page handlers
  continue to receive local paths such as `/world/b-24-winter`.
- Preserve the original canonical request URL for generated links,
  redirects, recovery actions, forms, and `next` values.
- Reject or recover unknown community slugs with a clear page, not a silent
  fallback to the default community.

Implementation notes:

- Prefer middleware/request-state over route duplication.
- Keep path rewriting server-side and invisible to templates except through a
  link-generation helper.
- Make `recover_next_url` understand prefixed paths.
- Ensure static assets, `/health`, `/login`, and `/logout` are not interpreted
  as tenant-prefixed routes.

Acceptance checks:

- Existing unprefixed route tests keep passing.
- New prefixed route tests pass for materials, boards, threads, wanted hooks,
  characters, applications, and plotting recovery where applicable.
- Unknown `/c/not-a-program/...` does not resolve to another community by
  accident.

## Phase 4: Community-Aware Link Generation

Goal: stop hardcoding local paths in templates when the href points to
community-scoped content.

Work:

- Add a small server-side helper, tentatively `community_href(viewer, path,
  community=None)`.
- Helper behavior:
  - if current host is canonical for the target community, return `path`
  - if target community has a canonical host, return absolute or host-relative
    canonical URL as appropriate
  - if current host is shared, return `/c/{community.slug}{path}`
  - preserve hash fragments and query strings
- Register the helper as a template global.
- Update shared navigation and content templates first:
  - `_layout.html`
  - board cards and board/thread links
  - world material links
  - wanted links
  - character/application links
  - identity switcher `next` values
  - recovery links
- Keep app-global routes unprefixed unless they are community-scoped.
  Examples: `/login`, `/logout`, static assets, and perhaps a future studio
  network landing page.

Acceptance checks:

- The Railway home page can link to Jurassic pages with `/c/jurassic-park-universe/...`.
- A Jurassic page can link to X-Men material with `/c/x-men-apocalypse/...` on
  the shared host.
- Generated links do not show double prefixes.
- Hash anchors still work for guidebook sections.

## Phase 5: Session, Identity, And Recovery Semantics

Goal: make tenant routing cooperate with login, active face, and cross-program
switching.

Work:

- When a prefixed URL names a community where the logged-in user has a
  membership, choose that membership for the viewer unless a valid session
  selection for the same community exists.
- If the user is logged in but lacks membership in the prefixed community,
  render an intentional public/limited viewer or membership-required recovery
  state, depending on the production auth posture.
- Update `/identity` switching so `next` preserves tenant context.
- Update route recovery:
  - unprefixed wrong-community links can suggest the canonical prefixed URL
  - prefixed wrong slugs should search within that explicit community first and
    only offer cross-community alternatives as recovery
- Keep active/default face scoped to membership.

Acceptance checks:

- Switching from X-Men to Jurassic keeps `next=/c/jurassic-park-universe/...`
  when that was the user's destination.
- A user cannot forge a prefixed URL plus membership id to gain another
  community's role.
- Recovery pages explain program mismatch without leaking staff/private data.

## Phase 6: Tests And QA Matrix

Goal: prove URL correctness through rendered pages, not only helper functions.

Test groups:

- Resolver tests:
  - host-only community resolution
  - path-prefix community resolution
  - path-prefix overriding session selection
  - unknown prefix behavior
- Rendered page tests:
  - home links on shared host
  - world material detail under prefix
  - board detail under prefix
  - thread detail/new-thread under prefix
  - wanted detail under prefix
  - character/application links under prefix
- Auth/session tests:
  - production ignores development identity
  - session-selected community does not override explicit prefix
  - identity switch preserves canonical `next`
- Browser QA:
  - start at Railway root
  - open X-Men material
  - open Jurassic board via generated link
  - hard refresh Jurassic route
  - open a fresh browser on the same Jurassic route
  - verify no empty inner shell after boosted navigation

Checks:

```bash
uv run ruff check .
uv run ruff format . --check
uv run pytest -q --tb=short
uv run ty check src/elbysodic/ tests/
uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"
```

## Phase 7: Routing Performance Instrumentation

Goal: separate Railway/runtime overhead from Elbysodic route work.

Work:

- Add lightweight request timing in development/staging logs:
  - total request time
  - identity resolution
  - shell/viewer context
  - route data loading
  - template rendering
- Avoid logging private user content or post bodies.
- Compare timings for:
  - `/`
  - `/world/b-24-winter`
  - `/c/jurassic-park-universe/boards/paddock-twelve`
  - `/c/jurassic-park-universe/boards/paddock-twelve/threads/new`
  - boosted vs hard navigation
- Use the data to decide whether to optimize shell context queries, add request
  caching inside services, or tune Railway resources.

Acceptance checks:

- We can say whether page latency is mostly platform baseline, DB/query work,
  service read-model assembly, or template render time.
- No sensitive content appears in logs.
- Performance work is split into focused follow-up PRs.

## Suggested PR Sequence

1. **Chirp release PR**: patch/release outlet-aware shell rendering in
   `bengal-chirp`.
2. **Elbysodic shell PR**: bump Chirp dependency, add `{# outlet: main #}`, add
   boosted navigation regression tests, remove temporary workaround.
3. **Tenant prefix resolver PR**: middleware/request-state resolution,
   prefixed route tests, recovery handling for unknown community slugs.
4. **Community-aware href PR**: template helper plus high-traffic links in
   shell, world, boards, wanted, and identity switcher.
5. **Full route coverage PR**: remaining page links, `next` handling, cross-
   program recovery, browser QA.
6. **Performance instrumentation PR**: request timing logs and initial Railway
   timing report.

## Progress Log

- 2026-05-02: Started the tenant prefix resolver PR on
  `codex/tenant-prefix-resolver`. Explicit `/c/{community_slug}` routes now
  have regression coverage against production session selection, development
  headers, cross-realm recovery actions, app-global route exclusions, Studio
  Network entry targets, thread composer JSON endpoints, plotting-room SSE
  streams, and production login redirects back to prefixed destinations.

## Not Now

- Full multi-tenant hosted billing or account provisioning.
- Public anonymous browsing semantics beyond the current production auth
  posture.
- Multiple custom domains per community. `communities.host` is enough for the
  first canonical host pass.
- Client-side router or SPA conversion.
- Global slugs for boards, materials, characters, threads, or wanted hooks.
- Moving community identity into user-level state.

## Closure Criteria

- Chirp shell navigation no longer blanks `<main>` on boosted navigation.
- Shared Railway/demo links use `/c/{community_slug}/...` for community-scoped
  content.
- Community-specific hosts keep clean local paths.
- Session state cannot change what community a canonical prefixed URL resolves.
- Rendered tests and browser QA cover hard refresh, fresh browser, and boosted
  navigation across at least X-Men and Jurassic seeded programs.
- A timing report identifies the dominant source of real page routing latency.
