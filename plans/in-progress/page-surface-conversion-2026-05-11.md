# Page Surface Conversion Plan

Status: active planning artifact
Owner: Product design, web, Writer Network, Realm Studio, privacy, and rendered-route tests
Created: 2026-05-11
Review by: 2026-05-25
Closure criteria: the major pages have been converted to the layered shell
model; duplicate shell links and passive active-face repetition are removed;
empty sections follow an explicit display policy; repeated page patterns are
promoted to shared Elbysodic components; rendered tests and browser QA cover
the converted flows.

## Evidence Mode

This is promotion/planning synthesis. It promotes accepted design guidance from:

- `docs/product/navigation-menus.md`
- `docs/product/control-topology.md`
- `docs/product/information-hierarchy.md`
- `design/component-inventory.md`
- `design/static-shell-mock-v2.html`
- `plans/in-progress/layered-shell-navigation-2026-05-11.md`
- `research/synthesis/2026-05-11-layered-shell-navigation-panel.md`

No new real-user research is claimed here. Confidence is medium-high because
the plan follows accepted product doctrine and rendered implementation findings,
but individual page conversions still need browser QA.

## Decision

Use a hybrid conversion strategy:

1. Build the smallest shared page grammar first.
2. Convert one room/flow at a time.
3. Promote patterns only after the first real page proves them.

Do not do a large component-system rewrite before touching pages. That would
freeze uncertain abstractions. Do not convert pages entirely one-by-one with
page-local CSS either. That would preserve the current drift.

The unit of work should be a page slice with a narrow shared-component
promotion when the page proves the pattern.

## Page Conversion Questions

Every page conversion starts with this brief:

| Question | Required Answer |
|---|---|
| Page job | What single user job does this page own? |
| Room | `World Home`, `Locations`, `Wanted`, `Desk`, `Studio`, `Network`, or public/access |
| Audience | anonymous, applicant, member, staff/director, same-user-different-community |
| Primary object | realm, location, scene, face, wanted hook, application, claim, plotting room, material, staff setting |
| Shell-owned links | Which CTAs disappear because rail/sidebar already owns them? |
| Page-owned actions | Which controls are true commands for this displayed content? |
| Empty policy | Which empty sections teach/reassure, and which should disappear? |
| Active-face policy | Is the face named because the user is committing, or should copy say `active-face`/nothing? |
| Surface budget | high ritual, medium reading/object, low production/form |
| Proof | rendered assertions, service/read-model tests, privacy tests, browser QA |

## Shared Grammar First

Create or refine these shared components before broad page conversion:

| Pattern | Candidate Home | Purpose | First Proof Page |
|---|---|---|---|
| `page_pulse` / hub attention band | `_components/vocabulary.html` | one row of current work without turning into shortcut grid | Desk |
| `empty_policy_block` | `_components/ui.html` | render useful empty states and hide optional empty groups consistently | Desk, Applications |
| `object_action_bar` | `_components/ui.html` | compact local actions scoped to the displayed object | Thread, Wanted detail |
| `meta_line` | `_components/ui.html` | quiet metadata rows without badge/card inflation | Wanted, Members, Characters |
| `page_section` wrapper | `_components/ui.html` or Chirp layout macros | open section rhythm without wrapping every group in a card | Desk, Locations |
| `work_lane` / `attention_lane` | `_components/vocabulary.html` | queue-like rows with counts and continuation action | Desk, Studio operations |
| `editor_panel` | `_components/vocabulary.html` | low-chroma production forms with clear save actions | Studio, Applications |
| `ritual_header` variants | existing page-local first | expressive page identity without repeated CTA bands | Location, Character, Wanted hook |

Rules:

- A pattern needs two likely uses before promotion, except when it protects
  privacy or empty-state behavior.
- Keep component names product-native, not generic SaaS names.
- Prefer Chirp-UI primitives under the hood.
- CSS goes in `src/elbysodic/web/static/elbysodic-theme.css`; repeated markup
  goes in `src/elbysodic/web/pages/_components/`.
- Do not introduce raw client state for decisions the server can render.

## Empty Policy

Render empty states when they reduce anxiety or teach the next useful action:

- no scenes need reply
- no notifications are waiting
- no submitted applications need review
- no direct scenes exist in a location where the user expects a list
- an application draft is incomplete
- a staff queue is clear

Hide empty structures when they only prove absence:

- accepted applications on writer-facing application lanes
- optional Desk/Studio shortcut panels
- zero-count work lanes on hub pages
- empty related-wanted strips
- empty claims/reserves groups on character pages unless the user is managing
  claims/reserves
- repeated route CTAs whose destination is already in rail/sidebar

Accepted applications are resolved intake. Writer-facing surfaces should show
the character page, roster entry, or posting identity instead of continuing to
show accepted items as application work.

## Active-Face Text Policy

The identity cluster owns the current active face. Pages should not repeat
`Writing as <face>`, `Browsing as <face>`, `Current face`, or equivalent
passive identity statements.

Use generic state language for passive surfaces:

- `active-face matches`
- `active-face reserves`
- `Relevant to the active face`
- `Prioritizing active-face matches`

Name the face only at commitment points:

- `Reply as <face>`
- `Join as <face>`
- `Raise interest as <face>`
- `Reserve for <face>`
- `Set current face`

## Conversion Order

### Slice 1: Desk And Writer Work Hubs

Pages:

- `/desk`
- `/my/threads`
- `/notifications`
- `/applications`
- `/characters`

Why first: these pages most visibly suffer from duplicate routing, zero-count
structure, active-face repetition, and hub-as-drawer behavior.

Primary changes:

- Desk becomes an attention dashboard, not a directory.
- Show current work first: needs reply, unread, waiting, inbox.
- Hide zero-count lanes unless the empty state reassures.
- Remove persistent shortcut grids duplicated by rail/sidebar.
- Applications shows active drafts/submissions/revisions; accepted faces move
  to roster/profile.
- Notifications keeps continuation actions only when they resolve the current
  inbox state.
- Roster keeps `Add face`, profile links, and application-specific actions;
  it should not duplicate Desk or Applications.

Proof:

- rendered tests for empty Desk, active Desk, accepted applications hidden from
  work lanes, notifications with/without inbox items
- browser QA on `/c/hp-universe/desk`, `/my/threads`, `/notifications`,
  `/applications`, `/characters`

### Slice 2: Wanted, Casting, Claims, And Plotting Handoffs

Pages:

- `/wanted`
- `/wanted/{wanted_slug}`
- `/casting`
- `/claims`
- `/plotting`
- `/plotting/{room_id}`
- `/characters/{character_slug}/hooks/{hook_slug}`

Why second: this room has the most overlap between browsing, raising interest,
reserving, claiming, plotting, and staff review.

Primary changes:

- Wanted board is browsing and entry into hooks.
- Wanted detail owns interest/reserve lifecycle and related hook context.
- Casting becomes a work lane for active-face and staff handoffs, not another
  global directory.
- Claims should be a focused directory/editor, with filters and staff controls
  kept visually low.
- Plotting should show current rooms and actionable handoffs; hide empty
  handoff sections unless they teach next steps.
- Remove generic `Browse wanted`/`Discover hooks` CTAs when the shell already
  provides the route and no current handoff exists.

Proof:

- rendered tests for wanted empty state, hook action placement, raised-interest
  state, claims filter behavior, plotting empty/active handoff states
- privacy tests for staff notes, private interest state, same-community scope

### Slice 3: Locations, Boards, Scenes, And Reading Flow

Pages:

- `/locations`
- `/boards/{board_slug}`
- `/boards/{board_slug}/threads/{thread_slug}`
- `/boards/{board_slug}/threads/new`
- post edit and revision pages

Why third: these are core writing surfaces. They need careful action placement
without breaking long-form reading.

Primary changes:

- Locations page is an in-character map and place scan, not a dashboard.
- Board pages keep place identity, local scene list, and `Start scene` when
  authorized.
- Thread pages should push continuation controls to the point of use: previous
  and next can stay near the top; attention continuation belongs after reading.
- Staff/director controls on scene pages should collapse behind a low-chroma
  management panel.
- Thread composer keeps active face clarity at the reply commitment point.
- Empty board filters should explain the filtered absence, not render a large
  structural lane for every zero state.

Proof:

- rendered tests for location active rail, board empty filters, start-scene
  authorization, reply-as-face, staff controls, mobile reading layout
- browser QA on long thread, no-post board, location with sublocations

### Slice 4: Character, Roster, Member, And Identity Pages

Pages:

- `/characters`
- `/characters/{character_slug}`
- `/members`
- `/members/{username}`
- `/identity`
- `/dev/personas`

Why fourth: these pages carry identity and relationship context, but they
should not become route directories.

Primary changes:

- Character pages are profile/work surfaces for one face: profile, writing
  lane, plotter, reserves, tracker, settings.
- Hide empty related collections unless they teach the owner what to do next.
- Keep face names visible because the page object is the face, but do not
  repeat active-face state passively.
- Member pages should show public writer record, not operational controls.
- Dev persona page can remain dense and utility-oriented, but should still use
  the active-face text policy.

Proof:

- rendered tests for owner vs non-owner profile controls, empty plotter,
  empty reserves, collaborator/member privacy, active-face set action

### Slice 5: World Home, Guidebook, Materials, Community

Pages:

- `/`
- `/world`
- `/world/{material_slug}`
- `/community`
- public request/access pages

Why fifth: these are orientation and lore surfaces. They need openness and
negative space, not app dashboards.

Primary changes:

- World Home is realm pulse plus orientation, with the next section visible.
- Guidebook is structured reading, not a link farm.
- Material detail pages keep canon/event/wanted/location relationships near
  the content, but hide empty relationship blocks.
- Community page is OOC table/record, not another world map.
- Public/access pages must not leak private rail/sidebar state.

Proof:

- rendered tests for public-safe content, hidden private sections, material
  related sections when empty/non-empty, community-board routing

### Slice 6: Studio And Production Rooms

Pages:

- `/studio`
- `/studio/operations`
- `/studio/launch`
- `/studio/intake`
- `/studio/boards/{board_slug}`

Why sixth: Studio needs the biggest conceptual split, but it is also most
likely to require approved route and privacy changes.

Primary changes:

- Studio home answers "what needs a director now?"
- Operations owns current production queues.
- Launch owns readiness and public posture.
- Intake owns application, claims, reserves, and blueprint controls.
- Board editor owns one board's settings and preview, with fewer nested cards.
- Appearance-heavy controls should stay low-chroma and form-forward.

Stop and ask before:

- adding new Studio routes beyond the already-present scoped routes
- changing staff visibility
- moving application review out of existing route contracts
- adding counts or badges that reveal private staff state

Proof:

- rendered privacy tests for staff/director-only content
- form validation tests for edited surfaces
- browser QA for long forms and mobile overflow

### Slice 7: Network, Recovery, Login, Request Access

Pages:

- `/network`
- `/login`
- `/request-access`
- recovery/error pages

Why last: these are outside the ordinary community rail and need public-safe
polish after the core community model stabilizes.

Primary changes:

- Network can stay card-oriented, but reduce repeated "enter/wanted/premise"
  CTA stacks and favor one primary journey per program card.
- Login is an access utility; keep it calm and clear.
- Request Access should explain entry without duplicating Network/World Home.
- Recovery pages should remain lowest-chroma and privacy-safe.

Proof:

- public rendered tests, denied-route recovery tests, no community-private rail
  leakage, mobile browser QA

## Page Triage Matrix

| Priority | Route Group | Main Risk | Component Proof |
|---|---|---|---|
| P1 | Desk, Applications, Notifications | duplicate routing, empty noise, active-face repetition | `page_pulse`, `empty_policy_block`, `work_lane` |
| P1 | Wanted detail, Casting, Plotting | unclear handoff ownership, too many CTAs | `object_action_bar`, `meta_line`, lifecycle rows |
| P2 | Locations, Board, Thread | action placement and reading flow | `ritual_header`, local action bar, continuation controls |
| P2 | Character, Roster, Member | identity clutter and empty related sections | profile sections, `meta_line`, owner action bar |
| P2 | Studio home/operations/intake | dashboard/card overload and staff privacy | `editor_panel`, production lane |
| P3 | World/material/community | orientation vs directory drift | open sections, related-content policy |
| P3 | Network/login/request/recovery | public polish and privacy | public-safe card/action policy |

## Implementation Rules

- Each conversion PR should include one route group or one shared component
  plus its first proof page.
- Do not rename/remove public routes without explicit approval.
- Do not change schema, auth, permissions, or privacy rules without explicit
  approval.
- Keep old routes working while page shape changes.
- Prefer rendered tests over snapshot-size assertions. Assert presence/absence
  of route duplication, active-face repetition, empty sections, and actions.
- Browser QA is required for any route with a hero, rail/sidebar interaction,
  dense form, long thread, or mobile-sensitive layout.
- Add changelog fragments for user-visible navigation/page behavior.

## Accepted Findings

- Component-first only is too abstract for this product. Use components as
  proof-backed grammar, not a speculative design system.
- Page-by-page only is too likely to keep duplicating cards and CTAs. Convert
  pages by room/flow and promote repeated patterns immediately.
- Empty-state policy is a product requirement, not copy polish.
- Active-face repetition should be treated as navigation/identity clutter.
- Shell reachability unlocks page simplification. The compact icon rail must
  remain reliable before removing duplicate page links.

## Deferred

- Fully configurable navigation grammar.
- New public route names or route removals.
- Dedicated Backstage global room.
- Appearance Studio fields for page density or layout variants.
- Replacing server-rendered pages with SPA shell behavior.

## Not Now

- Blanket card removal. Some cards are correct for repeated objects.
- Blanket hero removal. Ritual pages still need expressive identity.
- Icon-only PBP actions. Shell icons are acceptable; domain verbs still need
  words.
- Global command palette as a substitute for page clarity.
