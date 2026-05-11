# Synthetic Panel Run: Layered Shell Navigation

Status: synthetic panel
Date: 2026-05-11
Researcher: Codex
Artifact evaluated: layered shell navigation model, sidebar icon vocabulary,
and proposed route mapping
Seed docs:

- `AGENTS.md`
- `design/AGENTS.md`
- `src/elbysodic/web/AGENTS.md`
- `docs/product/user-personas-panel.md`
- `docs/product/navigation-menus.md`
- `docs/product/control-topology.md`
- `docs/product/information-hierarchy.md`
- `design/sidebar-icon-vocabulary.md`

Panelists used:

- Product Design Steward
- Web Shell/Navigation Implementation Steward
- Product Strategy/Docs Steward
- Active Scene Writer
- Returning Regular
- Invited/New Face Applicant
- Hook Hunter
- Community Director
- Staff Moderator
- Safety-Boundary Writer

Confidence: high

This is simulated research. It is useful for critique and hypothesis
generation, but it is not real interview evidence.

## Task Prompt

```text
Evaluate the proposed layered shell model:

- outermost chrome is icon-first
- inner shell navigation is text or icon-plus-text
- page action bars only act on displayed content

Evaluate the proposed product split:

- World Home = realm landing and orientation
- Locations = in-character place surface
- Wanted = hooks, casting, claims, reserves, and handoffs
- Desk = writer work and personal attention
- Studio = director/staff production

Return steward findings or user-panel findings with mapping preferences,
confusion risks, component needs, proof, and collateral.
```

## Panel Findings

### Active Scene Writer And Returning Regular

- Flow: Daily writing loop across outer rail, Desk, and thread pages
- Severity: P2
- User Job: Find `needs reply`, unread, watched, and waiting work without
  losing writing flow.
- Evidence: Active writers need `needs reply`, `waiting`, `caught up`,
  watched, mentioned, and unread scenes to stay visible and explainable.
- User Impact: If the rail is only place navigation, writers must enter Desk
  repeatedly to discover whether anything needs them.
- Expected Experience: Desk acts as the personal attention cockpit, with
  count/state hints on the rail or notification affordance and detailed lanes
  inside Desk.
- Recommended Change: Accept `Desk` in the outer rail and allow authorized
  attention badges for Desk/notifications. Keep detailed counts inside Desk.
- Required Proof: Desktop and mobile rendered checks for badges/tooltips and
  Desk inner shell lanes.
- Collateral: Product docs and rendered tests when implemented.
- Confidence: High

- Flow: Return after absence -> Desk -> first unread -> next obligation
- Severity: P2
- User Job: Regain continuity without rereading everything.
- Evidence: Thread continuation controls such as `Previous unreplied` and
  `Next unread` belong after reading, even if they jump across boards.
- User Impact: A strict "page actions only target this route" rule could remove
  the fastest return path.
- Expected Experience: Thread pages keep controls local to the reading moment
  but may point to the queue's next obligation.
- Recommended Change: Treat attention-continuation controls as page-local
  because they are triggered by finishing the current content.
- Required Proof: Thread QA for first unread, mark caught up, previous
  unreplied, and next unread placement.
- Collateral: Control-topology clarification.
- Confidence: High

- Flow: Scene/thread reading and replying from any room
- Severity: P1
- User Job: Reply as the right face.
- Evidence: Wrong-face posting is a core writer anxiety.
- User Impact: If active face visibility depends on the current shell, writers
  lose authorship confidence.
- Expected Experience: Active face remains in the identity cluster and appears
  again at commitment points such as `Reply as <face>` or `Join as <face>`.
- Recommended Change: Keep active face outside the rail/shell hierarchy.
- Required Proof: Rendered checks for thread reply, wanted interest, and mobile
  drawer identity state.
- Collateral: Privacy/authorship tests when implemented.
- Confidence: High

### Invited/New Face Applicant And Hook Hunter

- Flow: New realm understanding -> first face path
- Severity: P1
- User Job: Decide whether the realm is safe, active, and worth joining.
- Evidence: Applicants need premise, guidebook/application guidance, wanted
  board, claims/reserves, and start application entry points.
- User Impact: If World Home is only a generic landing page, no-face applicants
  may not find the first-face path.
- Expected Experience: World Home exposes `Start Here`, guidebook, application
  guidance, community table, current pulse, and public/request-access posture.
- Recommended Change: Keep World Home in the outer rail and make its inner shell
  applicant-aware.
- Required Proof: First-face walkthrough or rendered navigation check.
- Collateral: Navigation docs and implementation checklist.
- Confidence: High

- Flow: Wanted board -> hook detail -> interest -> plotting
- Severity: P1
- User Job: Find a playable hook and move toward a scene.
- Evidence: Hook hunters need status, compatibility, private interest,
  plotting, and ready-for-scene handoff.
- User Impact: If Wanted means only "wanted ads," claims/reserves/casting and
  handoff state become hard to understand.
- Expected Experience: Wanted inner shell includes wanted board, casting,
  claims, reserves, related wants, and handoff/status lanes where appropriate.
- Recommended Change: Treat Wanted as the discovery-to-commitment room; keep
  hook actions content-local near hook state and audience/privacy copy.
- Required Proof: Rendered wanted flow for open, reserved, plotting, filled,
  and prospective-interest states.
- Collateral: Wanted shell checklist if not covered in implementation docs.
- Confidence: High

- Flow: Application draft/status tracking
- Severity: P2
- User Job: Track application state, revision requests, claims, and reserves.
- Evidence: `/applications` is currently Desk by default, while staff later need
  Studio Intake.
- User Impact: A no-face applicant may not understand that Desk is where "my
  application" lives before they have a roster or reply queue.
- Expected Experience: Desk adapts for no-face/applicant state with visible
  application, claims/reserves, and next-step lanes.
- Recommended Change: Desk inner shell should support applicant states such as
  `Application draft`, `Staff review`, `Revision requested`, `Claims`, and
  `Reserves`.
- Required Proof: Rendered no-face/applicant Desk state check.
- Collateral: Product docs if Desk contract tightens.
- Confidence: Medium-high

### Director, Staff Moderator, And Safety-Boundary Writer

- Flow: Studio production routing
- Severity: P2
- User Job: Run the board without turning the realm into generic admin.
- Evidence: Studio should be production-native: launch, operations, intake,
  navigation, boards, appearance, and continuity.
- User Impact: Studio home becomes noisy if it is a grid of all tools rather
  than "what needs a director now."
- Expected Experience: Studio opens on director obligations and production
  health, then hands off to focused rooms.
- Recommended Change: Use production-native labels: `Operations`, `Launch`,
  `Intake`, `Boards`, `Navigation`, `Appearance`, `Continuity`.
- Required Proof: Browser QA and rendered active-state tests.
- Collateral: Product docs if route labels change.
- Confidence: High

- Flow: Intake, claims, reserves, and moderation work
- Severity: P1
- User Job: Review private work without leaking staff state.
- Evidence: Wanted is the public bridge for casting/claims/reserves, but staff
  need private review queues and notes.
- User Impact: If all claims/reserves live visually under Wanted, staff work may
  leak or become hard to find.
- Expected Experience: Public Wanted shows safe availability and movement
  state; Studio Intake owns private review queues, conflicts, notes, and
  decisions.
- Recommended Change: Make inner shells audience-aware. Public/writer Wanted
  can show `Wanted board`, `Casting`, `Claims`, `Reserves`; Staff/Studio should
  expose `Intake` or `Casting operations`.
- Required Proof: Permission/rendered privacy tests for anonymous, member,
  owner, staff, director, and same-user-different-community states.
- Collateral: Security/privacy docs if route visibility changes.
- Confidence: High

- Flow: Public realm browsing and community switching
- Severity: P0
- User Job: Browse safely without private work state or identity leakage.
- Evidence: Counts, sidebars, mobile drawers, notifications, and recovery pages
  are privacy side channels.
- User Impact: Public pages feel surveilled or unsafe if they show Desk, Studio,
  private counts, active-face context, or staff/intake hints to unauthorized
  viewers.
- Expected Experience: Public pages show public-safe realm navigation only.
  Private identity and work state appear after community-local membership and
  permission checks.
- Recommended Change: Gate outer rail items, badges, tooltips, active states,
  and inner shell rows by audience, community, and capability.
- Required Proof: Cross-community rendered tests, same-global-account
  different-role tests, mobile drawer privacy assertions, and denied-route
  recovery checks.
- Collateral: Security/privacy docs and route privacy matrix if visibility
  semantics change.
- Confidence: High

## Steward Findings

- Product Design accepted the layered shell model and five-room split:
  `World Home`, `Locations`, `Wanted`, `Desk`, `Studio`. It recommended shared
  shell components instead of page-local variants.
- Web Shell/Navigation recommended a server-side nav view model before broad
  edits: `PrimaryNavItem`, `SidebarSection`, and expanded
  `ShellRouteState`.
- Product Strategy accepted World Home as a landing/orientation surface,
  Locations as the in-character place surface, Wanted as hook/casting movement,
  and Desk/Studio as obligation-focused hubs.

## Convergence

- Accept the five-room outer rail: `World Home`, `Locations`, `Wanted`, `Desk`,
  `Studio`.
- Treat `Network` as future/not default until it has a real cross-realm route.
- Keep outermost chrome icon-first; inner shell text or icon-plus-text; page
  action bars content-local.
- Do not repeat the outer rail as a desktop inner sidebar directory.
- Do not use `Play`, `Dashboard`, `Admin`, `Backstage`, or IC/OOC as primary
  modes.
- Keep active face out of navigation. It belongs to the identity cluster and
  commitment actions.
- Make shell rendering audience-aware and community-scoped.

## Tensions And Minority Reports

- Desk versus Wanted for `/plotting` and `/discover`: default to Desk because
  they are writer work lanes; allow Wanted pages to link to them when a hook
  handoff makes the intent visible.
- Applications belong to Desk for writers/applicants, but staff review should
  move toward Studio Intake.
- World Home must remain orientation and pulse, not a shortcut dashboard, but
  applicants need enough first-face entry points there.

## Decisions

- Accepted:
  - Layered shell model.
  - Five-room outer rail.
  - Locations as in-character navigation.
  - World Home as realm home/orientation.
  - Wanted as discovery-to-commitment room.
  - Desk as personal attention and applicant-owned state.
  - Studio as director/staff production.
  - Audience-aware rail items, badges, tooltips, and inner shell rows.
  - Attention-continuation controls as allowed page-local actions.

- Proposed:
  - Server-side nav view model.
  - Shared shell components: `primary_icon_rail`, `inner_sidebar_shell`,
    `rail_icon_link`, `sidebar_context_collection`, `mobile_shell_drawer`.
  - Studio route split: `/studio/operations`, `/studio/launch`,
    `/studio/navigation`, `/studio/boards`, `/studio/appearance`,
    `/studio/intake`, `/studio/continuity`.

- Deferred:
  - Exact public route moves.
  - Final staff/private Intake routing.
  - Network rail item.

- Rejected:
  - `Play` as primary label.
  - Fully hidden sidebar as normal collapsed state.
  - Page shortcut strips that duplicate the shell route map.
  - Iconifying generated boards, faces, scenes, or guidebook entries.

- Not-now:
  - Global `Backstage`.
  - IC/OOC mode switch.
  - Fully configurable navigation grammar.

## Proof Needed

- Rendered test:
  - Outer rail labels, icons, accessible names, active state, and badges.
  - Inner shell per room.
  - Route active-state mapping, including board placement.
  - Applicant/no-face Desk state.
  - Wanted open/reserved/plotting/filled states.
  - Studio visibility and active state.

- Service test:
  - None until shell counts or route services change.

- Browser QA:
  - Desktop expanded.
  - Compact icon rail.
  - Hidden/focus mode.
  - Mobile drawer.
  - Keyboard focus and tooltips.

- Copy check:
  - `World Home`, `Locations`, `Wanted`, `Desk`, `Studio`.
  - No `Play`, generic `Dashboard`, or generic `Admin`.

- Accessibility check:
  - Icon-only accessible names.
  - `aria-current`.
  - Badge announcement or readable labels.
  - Keyboard reachable rail/sidebar toggle.

- Privacy check:
  - Anonymous, outsider, member, applicant/no-face, owner, staff, director, and
    same-user-different-community render states.
  - Public pages do not leak active face, private counts, staff/intake links,
    private object names, or application status.

- Real interview:
  - Needed before broad roadmap claims, not required before implementation of
    this navigation cleanup.

- Real UAT:
  - Run on first-face, wanted handoff, and daily writing loops after the shell
    is implemented.

## Promotion Target

- `docs/product/navigation-menus.md`
- `docs/product/control-topology.md`
- `design/sidebar-icon-vocabulary.md`
- Future implementation plan/tests once routes/components are changed.
