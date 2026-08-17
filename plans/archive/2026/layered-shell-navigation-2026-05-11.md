# Layered Shell Navigation Implementation Plan


## Archival Note

Lifecycle: Superseded

Archived 2026-08-17. Phases 1-4 and later shell slices merged. Remaining navigation work belongs on GitHub under the live index, not this plan. See docs/plan/issue-lifecycle.md.

Status: active implementation plan; phases 1-4 plus writer-hub, handoff,
Studio hub, writing-flow cleanup, and public-preview shell slices are merged;
broader page conversion remains
Owner: Product, design, web, privacy, and test stewardship
Created: 2026-05-11
Last updated: 2026-05-12
Review by: 2026-05-25
Closure criteria: the accepted layered shell model is implemented or split into
merged PRs; the stale `World`/`Play` shell labels are replaced; compact sidebar
means icon rail rather than hidden sidebar; rail, inner shell, and mobile drawer
share one server-side navigation model; privacy-gated badges/rows have rendered
tests; desktop, compact, focus, and mobile browser QA are recorded.

## Strategy Anchor

This plan strengthens:

- Writer Network: faster access to Desk obligations, active face confidence,
  wanted discovery, and return-after-absence continuity.
- Realm Studio: clearer Studio production rooms, intake separation, and
  director/staff work without public-page clutter.
- Realm Studio foundation: a safer shell contract for tenant-aware navigation,
  public previews, mobile drawers, and future community customization.

## Basis

Accepted input:

- Product docs: `docs/product/navigation-menus.md`,
  `docs/product/control-topology.md`,
  `docs/product/information-hierarchy.md`.
- Design docs and artifacts: `design/sidebar-icon-vocabulary.md`,
  `design/static-shell-mock.html`, `design/static-shell-mock-v2.html`,
  `design/static-shell-mock-v2-notes.md`.
- Research synthesis:
  `research/synthesis/2026-05-11-layered-shell-navigation-panel.md`.
- Web implementation steward findings from 2026-05-11.
- Synthetic user-panel findings from 2026-05-11.

## Accepted Model

Use a three-layer shell:

1. Outermost chrome is icon-first: stable community rooms and global utilities.
2. Inner shell is explanatory: text or icon-plus-text rows for the active room.
3. Page chrome is task-local: actions only affect displayed content or a
   continuation action naturally triggered by finishing that content.

Accepted outer rail:

| Room | Icon | Visibility | Inner Shell |
|---|---|---|---|
| World Home | `home` | Public-safe | Start Here, Guidebook, Community, current event/material, applicant entry points |
| Locations | `locations` | Public-safe when locations are public | Location tree, active scenes here, related wants, current place context |
| Wanted | `wanted` | Public/member-safe with capability-gated actions | Wanted board, Casting, Claims, Reserves, hook handoffs |
| Desk | `desk` | Signed-in community members only | Queue, Inbox, Roster, Plotting, Applications, Discovery, applicant-state rows |
| Studio | `studio` | Staff/director only | Operations, Launch, Intake, Boards, Navigation, Appearance, Continuity, Materials |

`Network` stays out of the default community rail until cross-realm network
behavior is a real daily workflow.

## 2026-05-12 Baseline Update

After pulling `main` to `f08eae8`, the shell foundation and first page
conversion waves are no longer local-only. PR #37 merged the layered shell,
inner-sidebar privacy gates, Desk/Wanted/Studio/writing-flow cleanup, and
browser QA artifacts. PR #38 extended the same public-safe shell contract to
signed-out realm previews for `/c/{community_slug}`, guidebook, and wanted
surfaces.

Open before closure:

- Keep this plan active until the remaining identity, member, character, and
  public guidebook surfaces are either converted or split into narrower plans.
- Add another browser QA pass after public preview, identity, and member pages
  stop relying on older page-local movement patterns.
- Preserve rendered privacy proof for anonymous/public preview, ordinary
  writer, staff/director, and same-user-different-community paths as page
  conversion continues.

## 2026-05-11 Implementation Readout

Reviewed current `main` at `4f4afd2`, the V2 mock, live shell templates,
rendered tests, and an independent designer-agent pass.

What is now real:

- The five-room route model exists in `src/elbysodic/web/navigation.py`.
  `primary_nav_items()` returns `World Home`, `Locations`, `Wanted`, `Desk`,
  and `Studio`, and `tests/test_shell_navigation.py` covers the active-state
  mapping.
- The primary icon rail is implemented in
  `src/elbysodic/web/pages/_components/sidebar.html` and mounted from
  `src/elbysodic/web/pages/_layout.html`.
- Compact navigation now preserves the icon rail instead of fully hiding the
  shell by default.
- Desk and several flow pages have started the page-surface conversion: Desk
  leads with attention state, accepted applications are moving out of work
  lanes, duplicate shortcut grids are being reduced, and wanted/plotting
  handoffs have begun to lose generic route CTAs.

Remaining gaps:

- The inner shell is still hardcoded through separate `_layout.html` sidebar
  functions instead of rendered from one `ShellNavigation.sidebar_sections`
  model.
- `PrimaryNavItem` does not yet carry audience/capability visibility. The rail
  always returns `Desk` and `Studio`, so privacy-safe public/member/staff rail
  behavior is not represented in the server model yet.
- The rail uses the SVG sprite vocabulary, but inner sidebar rows still use
  mixed Chirp icon names such as `grid`, `star`, `pencil`, and `diamond`.
- Mobile drawer and desktop sidebar share template output, but not yet a
  shared typed navigation model with privacy-gated rows, badges, and tooltips.
- Browser QA is still the proof gap for expanded desktop, compact rail, focus
  mode, mobile drawer, and keyboard traversal.

Priority reset:

1. Finish Phase 3 and Phase 4 as one shell-foundation slice before broad page
   polish. Build the server-side `ShellNavigation` model, render inner
   sections from it, and add audience/capability visibility at the model layer.
2. Convert inner-shell stable route icons to the sidebar SVG vocabulary while
   keeping generated boards, locations, scenes, faces, and guidebook entries
   text-first.
3. Add rendered privacy tests for anonymous/public preview, applicant/no-face,
   writer, staff/director, same-user-different-community, mobile drawer, and
   compact rail states.
4. Run browser QA across the V2 shell states before removing more page-local
   route affordances.

Designer-agent synthesis:

- Accept the current five-room model and compact rail direction.
- Treat the hardcoded inner sidebar as the main architectural/design gap.
- Treat rail/sidebar audience gating as a privacy blocker, not a polish task.
- Start page conversion with Desk only after shell reachability is proven
  enough that pages can safely remove duplicate route CTAs.

## 2026-05-11 Implementation Update

The inner shell and privacy-gate slice landed locally after the readout above.

Implemented:

- Added `ShellNavItem`, `ShellNavSection`, and `ShellNavigation` in
  `src/elbysodic/web/navigation.py`.
- Moved rail, inner-sidebar, mobile-drawer, location tree, wanted context,
  Desk, and Studio section construction into the server-side navigation model.
- Removed the old hardcoded world/desk/studio/wanted sidebar branch builders
  from `src/elbysodic/web/pages/_layout.html`.
- Updated `_components/sidebar.html` with shared `shell_nav_item`,
  `shell_nav_section`, and `inner_sidebar_shell` renderers.
- Gated `Desk` to active signed-in memberships and `Studio` to staff/director
  capabilities in the nav model while keeping existing route behavior intact.
- Converted stable inner-shell rows to the SVG sprite icon vocabulary while
  leaving generated boards, location branches, wanted hooks, and materials
  text-first.

Proof:

- `uv run pytest -q tests/test_shell_navigation.py`
- `uv run pytest -q tests/test_forum_slice.py`
- `uv run pytest -q tests/test_web_security.py`
- `uv run ruff check src/elbysodic/web/navigation.py src/elbysodic/web/app.py src/elbysodic/web/routes.py tests/test_shell_navigation.py tests/test_forum_slice.py`
- `uv run ruff format src/elbysodic/web/navigation.py src/elbysodic/web/app.py src/elbysodic/web/routes.py tests/test_shell_navigation.py tests/test_forum_slice.py --check`
- `uv run ty check src/elbysodic/ tests/`
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`
- `uv run python scripts/browser_qa.py --base-url http://127.0.0.1:8004 --artifact-dir tests/browser/artifacts/shell-navigation-2026-05-11`

Browser QA artifact path:

- `tests/browser/artifacts/shell-navigation-2026-05-11`

Remaining before closure:

- Full release gate if this is shipped as a PR.
- Page-surface cleanup in Phase 5 beyond the first Desk/writer hub,
  Wanted/Casting/Claims/Plotting, Studio hub, and writing-flow cleanup slices.
- Optional deeper browser QA after the Desk/Wanted/Studio page conversion
  slices remove more duplicate route affordances.

## 2026-05-11 Phase 5 First Slice Update

The first Page Surface Conversion slice landed locally for writer hubs:

- Desk handles faceless members as first-face/application work instead of
  saying the roster is caught up.
- My Threads keeps queue metrics but suppresses empty section noise.
- Applications keeps active intake work separate from accepted roster/profile
  faces and avoids assuming a hardcoded guide material route.
- Roster copy now uses visible face language for the metric, form, submit
  action, and no-roster state.

This does not close Phase 5. Wanted/Casting/Claims/Plotting and Studio cleanup
remain the next conversion slices.

## 2026-05-11 Phase 5 Second Slice Update

The Wanted/Casting/Claims/Plotting handoff slice landed locally:

- Wanted remains browsing-first on the index and commitment-first on detail.
- Wanted and plot-hook details use raised-hand language for lifecycle lanes.
- Casting collapses empty handoff lanes into one clear state and hides optional
  empty lanes when other handoff work exists.
- Claims remains a low-chroma directory/editor with claim-specific language.
- Plotting hides empty room/inbox sections and prioritizes ready scene
  handoffs before lower-action groups.

This still does not close Phase 5. Studio hub cleanup is the next major
conversion slice.

## 2026-05-11 Phase 5 Third Slice Update

The Studio hub cleanup slice landed locally:

- Studio home no longer repeats the shell with local room rail/card navigation.
- The hub now renders production attention lanes only when director movement is
  needed, otherwise one `Production calm` empty state.
- Studio Operations hides zero-count cards and empty triage panels, otherwise
  rendering one `Operations clear` state.
- Launch and board editor shed duplicate return-to-Studio buttons while
  preserving contextual actions.

This still does not close Phase 5. Remaining page conversion should move next
to Locations/Boards/Thread reading flow.

## 2026-05-11 Phase 5 Fourth Slice Update

The Locations/Boards/Thread reading flow slice landed locally:

- Locations now reads as a place-first scan and no longer repeats passive
  active-face copy.
- Board actions and empty states are scene-native: `Start scene here`, `Next
  unread here`, direct-scene empty action, and caught-up filter copy.
- Thread readers split adjacent scene movement near the top from
  previous-unreplied/next-unread continuation after the transcript.
- The reply commitment remains face-specific at the composer while top-level
  movement says `Jump to reply`.

This still does not close Phase 5. Remaining page conversion should move next
to character/member identity pages or public World/Guidebook surfaces.

## Next Implementation Slice: Inner Shell And Privacy Gates

Status: implemented locally on 2026-05-11.

Goal: make the V2 shell trustworthy enough that page conversion can remove
duplicate navigation without harming reachability or leaking private state.

This is the next coding slice. It should land before more broad Desk/Wanted/
Studio page cleanup.

### Scope

Implement one server-side shell navigation model for:

- primary icon rail rows
- inner sidebar sections
- mobile drawer rendering
- compact rail and focus mode state
- privacy-safe counts, badges, labels, tooltips, and active states

Do not add or remove public routes in this slice. Do not move application,
claim, reserve, or Studio review behavior between route families yet. This
slice changes how existing navigation is modeled and rendered, not which
product workflows exist.

### Proposed Objects

Extend `src/elbysodic/web/navigation.py` with typed model objects:

```python
ShellAudience = Literal["public", "applicant", "member", "staff"]

@dataclass(frozen=True, slots=True)
class ShellNavItem:
    key: str
    label: str
    href: str
    icon_id: str | None
    active: bool
    count: int | None = None
    description: str | None = None
    aria_label: str | None = None

@dataclass(frozen=True, slots=True)
class ShellNavSection:
    key: str
    label: str | None
    items: tuple[ShellNavItem, ...]
    source: str

@dataclass(frozen=True, slots=True)
class ShellNavigation:
    active_room: str
    active_inner: str
    primary_items: tuple[ShellNavItem, ...]
    sidebar_sections: tuple[ShellNavSection, ...]
```

Keep visibility decisions out of templates. Hidden rows should not be created
in the returned model. Avoid a `visible: bool` flag that relies on templates or
CSS to suppress private data after it has already entered the DOM.

### Audience Contract

Use explicit viewer state when building navigation:

| Audience | Rail | Inner Shell |
|---|---|---|
| Anonymous/public preview | `World Home`, `Locations` if public, `Wanted` if public-safe | Public orientation, guidebook, community-safe rows, public wanted/location context |
| Applicant/no-face member | Public rail plus `Desk` only when signed in | Application status, claims/reserves next steps, no-face guidance, public wanted/location context |
| Writer/member | Public rail plus `Desk` | Queue, Inbox, Roster, Plotting, Applications, Discovery, privacy-safe counts |
| Staff/director | Writer/member rail plus `Studio` | Operations, Launch, Intake, Boards, Navigation, Appearance, Continuity, staff-only counts |

Private labels, staff rows, application status, active-face context, counts, and
tooltips must not be present in public DOM for unauthorized viewers. Same
global user with different community memberships must only see rows for the
resolved community.

### Implementation Steps

1. Add `ShellNavItem`, `ShellNavSection`, and `ShellNavigation` to
   `src/elbysodic/web/navigation.py`.
2. Replace `primary_nav_items(current_path, board_section)` with a wrapper
   around `shell_navigation(viewer, current_path, board_section)`, preserving
   the current helper temporarily for compatibility.
3. Move current hardcoded sidebar section construction from
   `src/elbysodic/web/pages/_layout.html` into navigation helpers:
   - world home / guidebook / community context
   - locations tree and generated board rows
   - wanted / casting / claims / related wants
   - Desk rows and desk navigation boards
   - Studio rows and studio navigation boards
4. Add template renderers in
   `src/elbysodic/web/pages/_components/sidebar.html`:
   - `shell_nav_item`
   - `shell_nav_section`
   - `inner_sidebar_shell`
   - `mobile_shell_drawer` only if the current drawer markup cannot reuse the
     same `inner_sidebar_shell` safely
5. Switch `_layout.html` to render the model instead of calling separate
   world/desk/studio/wanted sidebar functions.
6. Convert stable inner-shell icons from mixed Chirp icon names to the sidebar
   SVG sprite IDs. Generated boards, generated locations, individual scenes,
   individual faces, and guidebook entries stay text-first.
7. Keep legacy compatibility helpers until rendered shell tests pass, then
   remove unused template branches in the same slice if the diff stays small.

### Test Plan

Focused unit tests:

- `tests/test_shell_navigation.py` covers:
  - active room and inner route mapping
  - public/applicant/member/staff item inclusion
  - no `Desk`/`Studio` rows for anonymous public preview
  - no staff rows for ordinary members
  - board section overrides for `locations`, `community`, `desk`, and `studio`
  - sprite icon IDs for stable route rows

Rendered tests:

- Add or extend `tests/test_forum_slice.py` coverage for:
  - expanded desktop sidebar uses the shared model
  - compact rail still exposes icon-only accessible names
  - mobile drawer renders the same allowed rows as desktop inner shell
  - anonymous public pages do not render `Desk`, `Studio`, private counts,
    active-face labels, application state, or staff/intake labels
  - applicant/no-face state sees application guidance but not staff review
    rows
  - writer state sees `Desk`, `Queue`, `Inbox`, `Roster`, `Plotting`,
    `Applications`, and `Discovery`
  - staff/director state sees `Studio` and production rows
  - same-user-different-community routes do not leak other-community counts

Security/privacy tests:

- Extend `tests/test_web_security.py` if rendered public/privacy assertions
  better fit there, especially for anonymous public preview, denied-route
  recovery, and same-user-different-community rail/drawer output.

Browser QA:

- Desktop expanded shell.
- Desktop compact icon rail.
- Desktop focus mode.
- Mobile drawer.
- Keyboard traversal of topbar, rail, inner shell, identity menu, and page
  actions.
- At least one route per room:
  `/`, `/locations`, `/wanted`, `/desk`, `/studio`, `/my/threads`,
  `/applications`, `/plotting`, `/world/...`, and a board/thread route.

### Acceptance Criteria

- Rail, inner sidebar, and mobile drawer are all rendered from
  `ShellNavigation`.
- Unauthorized rows/counts/tooltips are absent from server-rendered HTML, not
  merely hidden by CSS.
- Stable route icons use `src/elbysodic/web/static/icons/sidebar.svg`.
- Existing route labels stay aligned with the accepted five-room model.
- Focused shell tests and rendered privacy tests pass.
- Browser QA notes are recorded before declaring the shell slice complete.

### Follow-On Slice

After this lands, resume page-surface conversion:

1. Desk/writer work hubs: remove remaining duplicate page CTAs, prove empty
   lanes, and cover no-face/applicant states.
2. Wanted/Casting/Claims/Plotting: tighten handoff ownership and action
   placement.
3. Studio hub cleanup: let the inner shell carry room links so the hub can
   become production pulse instead of a tool directory.

## Non-Negotiables

- Do not use `Play` as a primary room label. Use `Wanted`.
- Do not use `World` as a broad route drawer. `World Home` is the realm landing
  and orientation surface; `Locations` is in-character place navigation.
- Do not make fully hidden sidebar the ordinary collapsed state. Compact means
  visible icon rail.
- Do not put active face in navigation. Active face stays in the identity
  cluster and in commitment actions such as `Reply as <face>`.
- Do not expose private work state in public rail, mobile drawer, tooltips,
  badges, recovery pages, or disabled-looking rows.
- Do not iconify generated boards, faces, scenes, guidebook entries, or
  location branches in the outer rail.

## Stop-And-Ask Gates

Check with a human before:

- Adding public routes such as `/studio/intake`, `/studio/operations`, or
  `/community`.
- Removing or redirecting existing public routes.
- Changing role visibility, permission checks, security wrappers, or privacy
  behavior.
- Adding new count sources to rail badges, mobile drawers, or public previews.
- Changing schema or board/sidebar placement contracts.

The first implementation pass should avoid route additions where possible. Use
current routes and labels while preparing the nav model. Add new Studio routes
only in a separate approved slice.

## Proposed Server Model

Introduce a small server-side navigation model before broad template work.

Candidate module:

- `src/elbysodic/web/navigation.py`

Candidate objects:

```python
PrimaryNavItem(
    key: str,
    label: str,
    href: str,
    icon_id: str,
    active: bool,
    count: int | None,
    visibility: ShellVisibility,
)

SidebarItem(
    key: str,
    label: str,
    href: str,
    icon_id: str | None,
    active: bool,
    count: int | None,
    description: str | None,
    visibility: ShellVisibility,
)

SidebarSection(
    label: str | None,
    items: tuple[SidebarItem, ...],
    source: str,
)

ShellNavigation(
    primary_items: tuple[PrimaryNavItem, ...],
    sidebar_sections: tuple[SidebarSection, ...],
    active_room: str,
    active_inner: str | None,
)
```

`visibility` must be computed from the current viewer, community membership,
role/capabilities, tenant context, and public preview posture. Avoid embedding
private labels or counts in objects that are later hidden client-side.

## Route Active-State Contract

Initial mapping:

- `/`, `/c/{slug}`: outer `World Home`; inner world home/community context.
- `/locations` and location/sublocation boards: outer `Locations`; inner
  `Locations`.
- `/world`, `/world/*`: outer `World Home`; inner `Guidebook`.
- `/members` and community boards: outer `World Home`; inner `Community`.
- `/wanted`, `/wanted/*`, `/casting`, `/claims`: outer `Wanted`; inner
  `Wanted`.
- `/desk`, `/my/threads`, `/notifications`, `/characters`, `/applications`,
  `/interactions`, `/plotting`, `/discover`: outer `Desk` by default.
- `/studio`, `/studio/*`: outer `Studio`; inner Studio route.
- `/network`: future global `Network`, outside the default community rail.

If `/plotting` or `/discover` is reached from a wanted hook, the page may show
hook-context links or continuation actions, but the route remains writer work
unless a future scoped handoff route changes that contract.

## Component Plan

Implement shared shell components instead of page-local variants.

Candidate template/components:

- `rail_icon_link`: icon, accessible label, tooltip, active state, optional
  privacy-safe badge.
- `primary_icon_rail`: outer rail using `PrimaryNavItem`.
- `inner_sidebar_shell`: room header and `SidebarSection` rendering.
- `sidebar_context_collection`: generated/contextual row collection for
  locations, boards, wanted hooks, or materials.
- `mobile_shell_drawer`: same `ShellNavigation` rendered in drawer form.

Candidate CSS:

- Keep foundation in `src/elbysodic/web/static/elbysodic-theme.css`.
- Use `design/static-shell-mock-v2.html` as implementation reference, not a
  file to copy wholesale.
- Promote reusable tokens/classes only after verifying they do not fight
  Chirp-UI shell primitives.

Candidate icon helper:

- Render inline SVG use nodes from
  `src/elbysodic/web/static/icons/sidebar.svg`.
- Icons are decorative when labels are visible.
- Icon-only rail links need `aria-label`, `aria-current`, visible focus, and
  hover/focus tooltip.

## Implementation Phases

### Phase 1: Nav Contract And Tests

Status: landed in `fdce7df`.

Scope:

- Add the server-side navigation model.
- Expand or replace `ShellRouteState` so it returns `active_room` and
  `active_inner`, not old `world/play/desk/studio` booleans.
- Keep existing templates mostly unchanged except where tests need a stable
  helper.

Proof:

- Unit tests for route mapping, query stripping, tenant-prefixed links, and
  board sidebar section override.
- Rendered tests asserting `Locations`, `Wanted`, `Desk`, `Studio`, and brand
  home are the shell labels.
- Rendered tests asserting `Play` is absent from primary shell navigation.

### Phase 2: Icon Rail Components

Status: landed in `9278311`.

Scope:

- Add `rail_icon_link` and `primary_icon_rail`.
- Replace the ordinary collapsed hidden state with compact rail.
- Keep full hidden sidebar as deliberate focus mode.
- Wire icons from the SVG sprite.

Proof:

- Rendered tests for icon-only accessible names, `aria-current`, and badge
  visibility.
- Browser QA for expanded desktop, compact rail, focus mode, and keyboard
  focus.

### Phase 3: Inner Shell Refactor

Status: landed locally on 2026-05-11.

Scope:

- Render current sidebar from `ShellNavigation.sidebar_sections`.
- Move hardcoded primary room duplication out of desktop sidebar.
- Keep contextual location trees and generated lists in the inner shell.
- Preserve mobile drawer hierarchy with the same model.

Proof:

- Rendered route tests for World Home, Locations, Wanted, Desk, Studio.
- Mobile drawer assertions that the same labels and visibility rules apply.
- Browser QA at mobile widths.

### Phase 4: Audience And Privacy Gates

Status: landed locally on 2026-05-11.

Scope:

- Gate rail items, counts, tooltips, active states, and inner shell rows by
  viewer/membership/capability.
- Hide or neutralize `Desk`, `Studio`, private counts, active-face context, and
  application state for anonymous and public preview viewers.
- Ensure staff/private rows never render into public DOM.

Proof:

- `tests/test_web_security.py` coverage for anonymous, member, applicant,
  staff/director, and same-user-different-community states.
- Rendered privacy assertions for public preview, mobile drawer, compact rail,
  denied-route recovery, and tenant-prefixed routes.

### Phase 5: Hub Cleanup

Status: partially landed locally through Desk, writer hubs,
Wanted/Casting/Claims/Plotting, Studio hub, and writing-flow cleanup.

Scope:

- Remove persistent shortcut grids/duplicate route CTAs from Desk and Studio.
- Keep hub CTAs only when active work exists or an empty state teaches a useful
  next step.
- Preserve page-local continuation controls such as `Next unread`, `Previous
  unreplied`, `Mark caught up`, `Watch`, and `Unwatch`.

Proof:

- Desk rendered tests for active lanes, empty lanes, and accepted applications
  becoming roster/face pages.
- Studio rendered tests for production-focused home and scoped room links.
- Browser QA against current `/c/hp-universe/desk` and `/c/hp-universe/studio`.

### Phase 6: Studio Route Split

Scope:

- Only after explicit approval, add scoped Studio routes such as
  `/studio/operations`, `/studio/launch`, `/studio/intake`,
  `/studio/appearance`, and `/studio/continuity`.
- Move staff application/casting review out of public writer-facing routes when
  implementation catches up.

Proof:

- Route tests, rendered privacy tests, docs/changelog, and browser QA.

## Test Matrix

| Contract | Tests |
|---|---|
| Route active state | Focused route-state unit tests and rendered shell assertions |
| Tenant scoping | Tenant-prefixed link tests and same-user-different-community cases |
| Public privacy | Anonymous/public preview rendered tests for rail, drawer, badges, and recovery |
| Member privacy | Desk counts and application state visible only to authorized members |
| Staff privacy | Studio and Intake visible only to staff/director capabilities |
| Accessibility | `aria-label`, `aria-current`, focus state, tooltip/fallback text |
| Responsive behavior | Browser screenshots for desktop expanded, compact, focus, and mobile drawer |
| Hub discipline | Desk/Studio tests that page CTAs do not duplicate routine shell routes |

## Browser QA Checklist

- Desktop expanded shell.
- Desktop compact icon rail.
- Desktop focus mode.
- Mobile drawer.
- Keyboard traversal of topbar, rail, inner shell, identity menu, and page
  actions.
- Public, applicant/no-face, writer, staff/director, and same-user different
  community states.
- `/c/hp-universe/`, `/locations`, `/wanted`, `/desk`, `/studio`,
  `/my/threads`, `/applications`, `/plotting`, `/discover`, `/members`,
  `/world/...`, and representative board routes.

## Collateral

Required as implementation lands:

- Product docs only when route labels/ownership change beyond the accepted
  mapping already documented.
- Changelog fragment for user-visible shell/navigation behavior.
- Route privacy matrix updates if audience visibility semantics change.
- Plan updates after each phase lands or is split into PR-sized work.

## Not Now

- Global `Backstage`.
- IC/OOC mode switch.
- Fully configurable navigation grammar.
- Raw CSS/template customization for navigation.
- Default `Network` rail item before cross-realm network is a real route.
- Replacing server-rendered Chirp pages with SPA navigation.
