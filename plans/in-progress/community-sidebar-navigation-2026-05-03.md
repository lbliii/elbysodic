# Community Sidebar Navigation Plan

Status: active UX polish; browser QA remains
Owner: Product/UI stewardship
Created: 2026-05-03
Last updated: 2026-05-09
Review by: 2026-05-30
Closure criteria: topbar/sidebar ownership is documented, the Elbysodic
sidebar primitives are implemented without duplicate route control, mobile and
desktop sidebar behavior pass browser QA, and any upstream Chirp UI candidates
are identified.

## 2026-05-09 Verification Update

Navigation docs and route tests have advanced, but production polish still
needs browser QA across desktop and mobile, including login, network search,
tenant-prefixed community entry, board/thread/composer, wanted, application
review, plotting, notifications, and Studio. Search is currently discoverable
on `/network`, not as a topbar/global affordance; either add that affordance or
explicitly defer it in docs and UI copy.

## Purpose

Make Elbysodic navigation feel like a polished creative community product
instead of a generic forum/admin shell. The immediate concern is the left
sidebar feeling chunky, visually random, and duplicated with the global top
navigation. The deeper product need is a durable navigation contract that can
scale from one community per install to a future LBSodic home where writers can
explore, browse, and return to many communities.

The plan keeps both topbar and sidebar, but gives each one a single job:

- Topbar: platform/global shell utilities.
- Sidebar: the canonical community and local navigation map.

No route family should be controlled with equal weight in both places.

## Research Basis

The direction is informed by current sidebar/navigation guidance from Apple,
Apple TV, Fluent, Carbon, Baymard, WAI APG, and web.dev:

- Apple and Apple TV treat the sidebar as a simplified source/navigation rail
  that keeps media/content browsing in front, supports profiles, and gives
  quick access to primary sources without making each source a competing global
  tab.
- Fluent and Carbon both emphasize brief, scannable navigation, shallow nesting,
  clear active state, and a left panel when users frequently switch among more
  than a few secondary destinations.
- Baymard's filtering research supports keeping many filters/facets visible
  near the result set instead of hiding them in horizontal top controls. For
  Elbysodic, facets belong near discovery and list surfaces, not in the global
  shell.
- WAI APG and web.dev support semantic navigation, drawer behavior, focus
  handling, Escape-to-close behavior, and reduced-motion-safe mobile sidebars.

## Steward Notes

Consulted:

- Root `AGENTS.md`: preserve PBP-native product language, active face as a
  product lens, and community as a creative production space.
- `src/elbysodic/web/AGENTS.md`: keep server-rendered Chirp pages, small
  progressive enhancement, shared PBP UI vocabulary components, and theme CSS
  in `elbysodic-theme.css`.
- `docs/AGENTS.md`: keep product docs practical and avoid generic SaaS
  vocabulary.
- `docs/product/navigation-menus.md`: one navigation surface should answer one
  question; sidebar is contextual route map; labels are dividers, not routes.
- `docs/product/information-hierarchy.md`: app sidebar should not repeat the
  topbar product label; LocationTree is a world map/orientation primitive.
- `docs/product/control-topology.md`: icon-only controls are for familiar
  utility actions; PBP-specific terms need words.

Boundary decisions:

- This is not a SPA rewrite.
- This is not a full Chirp app-shell fork.
- Elbysodic can own sidebar vocabulary/components inside the existing Chirp
  shell slot first, then upstream useful primitives to Chirp UI later.
- Active face is a lens/identity state, not a navigation mode switch.
- In-world/out-of-world is language and grouping, not a binary sidebar mode.

Risks:

- Changing topbar/sidebar ownership affects almost every route's mental model.
- Existing tests may assert current topbar realm links or sidebar content.
- Removing topbar realms before the sidebar has a strong community map could
  temporarily make navigation feel hidden.
- Mobile behavior must not regress into a horizontal strip or duplicated menu.
- Counts in the sidebar can leak private/staff state if route visibility is not
  checked through existing service/viewer boundaries.

## Product Decision

Keep the topbar and sidebar, but let the topbar own the stable community modes
and let the sidebar own the current mode's contents.

On shared hosts, `/` is the Elbysodic/LBSodic home for exploring reachable
communities. A community home lives at `/c/{community_slug}`. The seeded X-Men
community uses `/c/x-men-apocalypse`, not `/c/default`, so the URL names the
actual community.

### Topbar Job

The topbar answers:

> Which major part of this community am I in?

Topbar owns:

- Current community identity and future community switcher.
- The community brand/title as the community home affordance.
- Primary community modes after home: `World`, `Play`, `Desk`, and `Studio`.
- Future global/community search entry.
- Future explore/browse communities entry from the LBSodic home.
- Notifications indicator.
- Writer/account/active-face identity menu.
- Theme, accessibility, and account utilities.
- Mobile sidebar/drawer trigger.
- At most one cross-cutting create/action control when it is truly global.

Topbar does not own:

- Boards, locations, threads, materials, applications, claims, roster, plotting,
  or discovery route families.

### Sidebar Job

The sidebar answers:

> What is inside this place?

Sidebar owns:

- Current mode children.
- Current board/location branch.
- Current material/event/related object collections.
- Counts that help a writer move: unread, needs reply, inbox, open wants.
- Director-configured community language and ordering within allowed sections.

The sidebar is not the primary community mode map on desktop. It should hydrate
with the current mode's local map. Mobile may include the topbar's community
mode map in the drawer because the horizontal topbar nav is hidden there.

## Canonical Sidebar Shape

Use one stable topbar mode map plus one current-mode sidebar map. Avoid two
separate desktop sidebars, duplicate root links, or a mode switch.

Topbar community modes:

```text
Community brand/title
World
Play
Desk
Studio
```

Sidebar context examples:

```text
In World
  Locations
    Xavier Institute
      Med Bay
      Cerebro
  Guidebook
  Community Table
    Members
    Announcements
```

```text
On Your Desk
  Desk home (only away from /desk)
  Queue
  Inbox
  Roster
  Plotting
  Applications
  Discovery
```

```text
In Play
  Wanted board (only away from /wanted)
  Casting desk
  Claims
  Active Face
    Cass Mercer
  Related Wants
```

The topbar is stable enough to orient writers. The sidebar is where the current
location, material, desk lane, or wanted hook gets local context. At a mode
root, do not repeat an active `Overview` row immediately under the active mode.
When someone is deeper inside a mode, use a plain home escape link only if it
clarifies the route.

## Toggle Decision

The sidebar should have a visibility toggle, not a mode toggle.

Allowed states:

- Expanded: normal community navigation.
- Hidden/focus: page gets more room for reading or writing.
- Mobile: same sidebar content in a drawer.

Deferred/optional state:

- Icon rail: only if later browser QA proves it helps, and only for stable
  universal destinations. It must not become the main experience because
  Elbysodic terms such as Wanted, Roster, Queue, Plotting, Claims, Reserves,
  and Studio need visible words.

The toggle means "show or hide navigation." It never means "switch to IC,"
"switch to OOC," "switch to in-world," or "switch to out-of-world."

Use the sidebar edge itself as the desktop visibility affordance. Do not render
a separate visible arrow pill such as `<` or `>`; the pointer/focus edge is the
control.

## In-World / Out-Of-World Decision

Do not implement an IC/OOC or in-world/out-of-world sidebar toggle.

Reason:

- World is story-facing but contains board structure.
- Guidebook is about canon/world materials but is director-authored.
- Wanted is story-facing but operational/casting-oriented.
- Writer Desk is out-of-character work tied to active character obligations.
- Studio is production/admin.

A binary toggle would hide useful routes or misclassify them. Use grouping and
language instead:

- World-facing: World, Guidebook, Wanted.
- Writer work: Queue, Roster, Plotting, Applications, Discovery.
- Director work: Studio, Navigation, Board taxonomy, Production.

Active face remains a lens and identity state. It may appear as a compact
sidebar context module where relevant, but it must not hide or replace the
canonical community map.

## Design Principles

1. One route family, one primary home.
2. The sidebar should feel calm, glossy, native, and community-hydrated.
3. The topbar should get quieter, not disappear.
4. A writer should always know whether they are moving globally, inside a
   community, or inside one object.
5. Labels are dividers. Route rows are clickable, active, and count-bearing.
6. Location trees reveal the current branch, not the whole world at once.
7. Counts should mean movement or obligation, not decorative metrics.
8. Facets and filters belong near results, not in the shell.
9. Mobile reuses the same sidebar model in a drawer.
10. Use Chirp shell contracts until a genuine upstream component need appears.

## Implementation Plan

### Phase 0: Sync And Baseline

Goal: begin implementation from a current branch and preserve existing work.

Tasks:

- Rebase or merge current `origin/main` before code changes. This plan was
  drafted while local `main` was 17 commits behind `origin/main`.
- Record current desktop and mobile screenshots of the shell/sidebar for:
  - World home.
  - A board/location page.
  - Guidebook.
  - Wanted hook detail.
  - Writer Desk or My Threads.
  - Studio navigation composer.
- Run the current app check before edits:

```bash
uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"
```

Acceptance checks:

- Implementation branch is based on current remote state.
- Baseline screenshots exist for before/after comparison.
- No unrelated local changes are overwritten.

### Phase 1: Product Contract Docs

Goal: make the topbar/sidebar ownership decision durable before changing UI.

Tasks:

- Update `docs/product/navigation-menus.md`:
  - Topbar is platform/global shell utilities.
  - Sidebar is canonical community/local route map.
  - Remove the old assumption that topbar owns community realms.
  - Define the community map and current-room hydration pattern.
  - Define sidebar visibility toggle behavior.
  - Explicitly reject IC/OOC mode switching.
- Update `docs/product/information-hierarchy.md`:
  - Add the community sidebar primitives.
  - Clarify LocationTree remains a world orientation primitive.
  - Clarify active face lens placement.
- Update `docs/product/control-topology.md` if needed:
  - Hide/show navigation is a utility control.
  - PBP-specific navigation rows should keep text labels.

Acceptance checks:

- Docs no longer contradict the implementation target.
- Future agents can answer "topbar or sidebar?" from docs alone.
- Steward Notes in the PR name the docs and web stewards consulted.

### Phase 2: Sidebar Data Model / Template Vocabulary

Goal: stop hand-assembling generic Chirp sidebar links everywhere.

Tasks:

- Add `src/elbysodic/web/pages/_components/sidebar.html`.
- Create Elbysodic-owned macros, tentatively:
  - `community_sidebar_shell`.
  - `sidebar_room_link`.
  - `sidebar_destination`.
  - `sidebar_attention_link`.
  - `sidebar_context_collection`.
  - `sidebar_location_tree`.
  - `sidebar_active_face`.
  - `sidebar_count`.
- Keep compatibility classes or HTMX route attributes required by Chirp shell
  navigation.
- Move repeated sidebar row markup out of `_layout.html`.
- Keep server-owned active/open branch state.

Acceptance checks:

- `_layout.html` describes sidebar composition, not row-level markup.
- Existing route links still boost/swap correctly.
- Location parent rows remain clickable.
- Counts render only from `viewer`/service read models, not ad hoc SQL.

### Phase 3: Topbar Simplification

Goal: make the topbar platform/global rather than duplicate community rooms.

Tasks:

- Remove visible `World`, `Guidebook`, `Wanted`, `Writer Desk`, and `Studio`
  topbar links.
- Keep the community brand/current community identity at the leading edge.
- Keep the identity/active-face menu and notification count.
- Add or reserve global utility slots for:
  - Search.
  - Community switch/explore.
  - Account/theme/accessibility.
  - Mobile navigation trigger.
- Ensure mobile trigger opens the same canonical sidebar, not a separate topbar
  realm list.

Acceptance checks:

- There is no duplicate primary route family in topbar and sidebar.
- All previous topbar destinations are reachable from the sidebar.
- The topbar still communicates current community/global identity.
- Keyboard tab order remains sensible: brand/global utilities, then sidebar,
  then page content.

### Phase 4: Community Sidebar Composition

Goal: implement the stable community map plus current-room hydration.

Tasks:

- Add a stable community map band:
  - World.
  - Guidebook.
  - Wanted.
  - Writer Desk.
  - Studio when the viewer can access it.
- Decide exact grouping labels through docs and browser QA:
  - likely `Community`, `Writer`, `Director`; or fewer labels if visual rhythm
    proves calmer.
- Hydrate the lower/current-room section based on current path and object:
  - World: overview, locations, current branch, community boards.
  - Guidebook: overview, start here, guides, events, applications, current
    material, related materials.
  - Wanted: wanted board, casting desk, claims, applications, active face,
    open/related wants.
  - Writer Desk: queue, inbox, roster, plotting, applications, discovery, desk
    boards.
  - Studio: overview, navigation composer, board taxonomy, production,
    current event, staff boards.
- Keep director-configured sidebar section labels/order for board-derived
  groups where already supported.

Acceptance checks:

- On every major route, the active primary room is visible once.
- Hydrated context changes only where it helps orientation.
- Empty contextual collections disappear.
- Staff-only links are hidden from non-staff viewers.

### Phase 5: Sidebar Visual System

Goal: replace the chunky generic sidebar feel with an Elbysodic product surface.

Tasks:

- Tune CSS in `src/elbysodic/web/static/elbysodic-theme.css`.
- Target desktop width around `17rem-19rem`, with stable responsive clamps.
- Use a quiet glossy/translucent surface where supported, with accessible
  fallbacks.
- Reduce row chunkiness:
  - primary rows roughly `38-42px`.
  - child/location rows roughly `32-36px`.
  - tighter section gaps.
- Active state:
  - slim accent rail or soft luminous wash.
  - avoid large full-row pills everywhere.
- Counts:
  - compact, aligned, lower visual priority than labels.
  - attention counts stronger only for queue/inbox needs.
- Footer:
  - remove or heavily demote `Built on Elbysodic` if it competes with the
    community surface.
- Avoid icon-only primary navigation in expanded mode.

Acceptance checks:

- Sidebar reads as one designed surface, not a stack of unrelated rows.
- Active route is obvious without shouting.
- Text does not clip awkwardly at expected community/board label lengths.
- Light, dark, and system themes remain readable.

### Phase 6: Sidebar Toggle And Mobile Drawer

Goal: support focus/reading without creating a second navigation model.

Tasks:

- Replace current resize/collapse affordance with a clear hide/show navigation
  utility.
- Persist hidden/expanded preference per device.
- Ensure thread/composer-heavy pages can benefit from hidden sidebar state.
- Mobile:
  - topbar trigger opens the same canonical sidebar content.
  - drawer has close button, Escape handling, focus return, and reduced-motion
    behavior.
  - no horizontal sidebar strip on mobile.
- Defer icon rail unless validated later.

Acceptance checks:

- Toggle never changes which routes exist.
- Hidden sidebar can be restored without hunting.
- Mobile drawer does not duplicate a separate realm list.
- Keyboard and screen reader users can open, use, and close navigation.

### Phase 7: Tests And Browser QA

Goal: prove the new navigation contract across rendered pages and viewports.

Tasks:

- Add/update rendered tests for:
  - topbar no longer includes community room links.
  - sidebar includes community rooms.
  - active room appears once.
  - non-staff does not see Studio if policy requires hiding it.
  - board/location current branch opens server-side.
  - contextual collections render/disappear correctly.
- Browser QA on port 8001:
  - desktop 1440x900 and 1024x768.
  - mobile 390x844 and/or 320x640.
  - light, dark, and system where practical.
- Capture screenshots for before/after review.
- Run project checks before handoff:

```bash
uv run ruff check .
uv run ruff format . --check
uv run pytest -q --tb=short
uv run ty check src/elbysodic/ tests/
uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"
```

Acceptance checks:

- Full checks pass or any failure is explained with ownership.
- Browser screenshots show no overlap, blank shell, unreadable glass, or
  duplicate navigation.
- Navigation remains usable with sidebar hidden and restored.

### Phase 8: Upstream Chirp UI Assessment

Goal: decide what should be upstreamed after Elbysodic proves the pattern.

Candidate upstream primitives:

- App shell topbar/side panel responsibility guidance.
- Sidebar hide/show utility distinct from icon-only collapse.
- Sidebar section density tokens.
- Source rail / contextual sidebar macro.
- Mobile drawer reuse of sidebar content.
- Better active rail/count styling hooks.

Not likely upstream:

- Elbysodic route vocabulary.
- Active face lens.
- LocationTree semantics.
- Wanted/plotter/studio grouping.

Acceptance checks:

- Upstream candidates are listed with screenshots and code references.
- Elbysodic-specific primitives remain local.

## Not Now

- Full multi-community browse/home implementation.
- Global search implementation.
- Icon-only sidebar rail as primary behavior.
- IC/OOC or in-world/out-of-world mode toggle.
- Facet filtering in the app shell.
- Route or tenant URL rewrites unrelated to sidebar ownership.
- Chirp app-shell fork unless the existing slot/contract cannot support the
  design after implementation.

## Suggested First PR

First PR should be docs plus topbar/sidebar template scaffolding only:

1. Update navigation docs with the ownership contract.
2. Add sidebar component macros.
3. Move existing sidebar rows into those macros with minimal visual change.
4. Keep topbar realm links temporarily if needed behind a clear TODO, or remove
   them only when the sidebar community map is already present in the same PR.

This reduces risk: the project gets a source of truth and reusable sidebar
vocabulary before visual polish and behavior changes land.
