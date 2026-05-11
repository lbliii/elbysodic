# Layered Shell Navigation Implementation Plan

Status: active implementation plan; phases 1 and 2 landed in code
Owner: Product, design, web, privacy, and test stewardship
Created: 2026-05-11
Last updated: 2026-05-11
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
