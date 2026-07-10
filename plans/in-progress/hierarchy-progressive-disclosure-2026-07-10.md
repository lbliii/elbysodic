# Hierarchy And Progressive Disclosure

Status: active; revised story-poster direction selected and implemented across
the representative surfaces; browser/design QA and full gates pending
Owner: Product design, research, Writer Network, Realm Studio, surface
contract, web, privacy, tests, and docs stewardship
Created: 2026-07-10
Last updated: 2026-07-10
Review by: 2026-07-24
Closure criteria: current staging is audited with fresh desktop/mobile
screenshots; one of three grounded hierarchy directions is selected; community
home, Writer Desk, Studio home, Studio Content, and a representative location
implement the selected structural direction; privacy, identity, responsive,
accessibility-risk, rendered, service, browser, docs, and changelog proof pass;
and real-user validation is either recorded or explicitly remains a post-alpha
validation gap.

## Purpose

Elbysodic's core functionality is close to broad product coverage, but several
high-value pages still render depth as simultaneous inventory. This plan turns
the accepted simplification doctrine into a cross-surface implementation:

- community home answers why this realm matters now and what the viewer should
  do next
- Writer Desk answers what the writer owes next and as which face
- Studio home answers what needs a director now
- Studio Content owns current publishing/casting work without duplicating its
  own room directory
- location pages keep the story/place and scene path foregrounded while deep
  director control remains available through one capability-gated entry

This strengthens Writer Network and Realm Studio. It does not change tenant,
membership, character, staff, privacy, route, schema, or Blueprint contracts.

## Evidence

- Fresh staging screenshots captured 2026-07-10 at 1440x1100 and 390x844.
- Approved visual target:
  `design/references/editorial-hierarchy-2026-07-10.png`.
- Simulated task and persona synthesis:
  `research/uat/simulated/2026-07-10-hierarchy-progressive-disclosure-simulated-uat.md`.
- Product doctrine: `docs/product/surface-quality-bar.md`,
  `docs/product/information-hierarchy.md`,
  `docs/product/experience-direction.md`, and
  `docs/product/user-personas-panel.md`.
- Current implementation: community gateway, Writer Desk, Studio home,
  Operations, Studio Content, board/location, shared navigation, read models,
  and rendered tests.

Evidence modes remain distinct: staging screenshots are observed product
artifacts; persona findings are synthetic; comparator lessons are research
inference; existing product docs are doctrine. Confidence is medium until real
applicant, writer, and director UAT runs.

## Current-State Findings

- Community home has individually coherent sections but nine comparable bands;
  signed-in state appends continuation and director controls instead of
  replacing irrelevant visitor content.
- Writer Desk's mobile hierarchy is promising, but its desktop command area
  visibly overlaps and repeats one obligation through four hierarchy levels.
- Studio home renders permanent rooms with equal card weight and duplicates
  Discovery between attention and navigation.
- Studio Content renders the same content topology first as destination cards
  and again as queue/coverage cards.
- Operations says it is clear, then devotes most of the page to parity
  contracts and runtime/persistence diagnostics.
- Location story context is interrupted by duplicate director edit entries,
  especially on mobile.

## Visual Direction Gate

Three image-based directions were generated from the fresh staging screenshots
inside the existing Elbysodic visual language:

1. story-poster composition with continuation attached to the realm promise
2. writer-first command composition with realm context as support
3. editorial story column with a compact persistent continuation rail

The user selected the story-poster direction and then approved its less-blocky
revision. The approved target uses an open editorial canvas, large story type,
asymmetric media, light rules, natural language, and one contained continuation
surface. Fluid UI is translated as context preservation and immediate response,
not additional spectacle.

## Surface Contracts

### Community Home

- First five seconds: realm promise, current pressure, and viewer-specific next
  action.
- Public visitor: one adaptive entry action, not a complete route inventory.
- Member: active-face continuation replaces visitor entry scaffolding; it does
  not append another full section to the same inventory.
- Director: one capability-gated `Edit realm home` disclosure outside the main
  story reading order.
- Full guidebook, cast, places, scenes, wanted hooks, and claims remain in
  scoped rooms; the home may curate only the few objects that explain the
  current premise or next move.

### Writer Desk

- One command area names active face, highest-priority obligation, latest
  useful context, and next action.
- Active lanes render only when work exists.
- One-item queues do not repeat summary, face lane, work lane, and detailed
  queue as four peer sections.
- Desktop, mobile, zoom, and long-title variants cannot overlap or create large
  detached whitespace.

### Studio Home

- Active attention leads; zero-state rooms do not become equal-weight cards.
- A true clear state remains calm and short.
- Permanent Studio rooms use an open index and remain available in scoped
  navigation; they do not become equal-weight elevated cards.
- Counts appear only when they change urgency, confidence, or the next action.
- Discovery or another room cannot appear as both current attention and a
  duplicate directory card.

### Studio Content

- An open content index owns guidebook, places, events, applications, and
  claims; a separate work area renders only drafts, open wants, and reserved
  claims that currently need judgment.
- Destination routing remains available in Studio navigation and contextual
  actions; it does not require a second five-card inventory.
- Empty sections collapse or disappear according to service-owned display
  policy.

### Representative Location

- Place identity, playable pressure, and scene continuation remain the primary
  reading path.
- Director capability is available through one `Manage place` disclosure.
- Full edit and structure-audit actions appear only after disclosure or on the
  scoped edit surface.
- The ordinary member DOM must not receive unsafe staff/private state.

## Implementation Progress

- Completed: community home editorial field, viewer-specific continuation,
  naturalized labels, and one director disclosure.
- Completed: Writer Desk continuation surface, repaired desktop grid, open face
  and work lanes, and updated empty states.
- Completed: Studio open room index, action-only attention lanes, and removal
  of unconditional duplicate Discovery attention.
- Completed: Studio Content open index and active-only publishing/intake work.
- Completed: Operations technical diagnostics moved behind one disclosure.
- Completed: representative location story field and removal of the duplicate
  director panel.
- Completed: focused rendered, privacy, and route checks.
- Completed: browser screenshots, source comparison, keyboard/fine-pointer/
  touch-emulated/reduced-motion QA, and final evidence rollup in
  `design-qa.md` and `design/qa/editorial-hierarchy-2026-07-10/`.
- Pending: repository-wide regression gates tracked by #264 and observed
  real-user validation.

## Implementation Slices

### Slice 1: Selected Community-Home Composition

- Translate the selected visual target into existing gateway components and
  theme tokens.
- Update service/read-model section membership only where templates currently
  receive additive audience state.
- Keep public/member/director privacy assertions and no-media fallbacks.
- Add desktop/mobile rendered proof before moving to the next surface.

### Slice 2: Writer Desk Command Repair

- Replace the colliding desktop command layout with the selected hierarchy
  grammar.
- Collapse repeated one-item sections and render only active lanes.
- Preserve face-named actions, latest-beat context, queue route, and empty
  states.

### Slice 3: Studio Attention Home

- Replace the permanent room-card directory with an open room index.
- Keep Studio rooms in existing navigation as the persistent route layer.
- Render ranked actionable work or one concise clear state.
- Remove duplicate Discovery and zero-count emphasis.

### Slice 4: Content And Operations Simplification

- Replace Studio Content's duplicate destination cards with an open index and
  an active-only work area with contextual edit actions.
- Put parity/runtime material behind one closed technical-checks disclosure on
  Operations so the daily decision path remains foregrounded.
- Do not change diagnostics, deployment, or persistence behavior.

### Slice 5: Object-Local Control Disclosure

- Replace the duplicate location director block with one capability-gated
  disclosure entry.
- Reuse the pattern on realm home only after location proof is stable.
- Verify public, ordinary-member, staff, and director states.

### Slice 6: Cross-Surface Quality And Collateral

- Run focused and full local gates.
- Capture selected-target versus implementation screenshots at matching
  viewports.
- Verify keyboard path, focus visibility, target size, heading order, zoom and
  reflow, and accessible naming for disclosure controls.
- Verify that disclosure and continuity transitions accept the latest input,
  adapt across keyboard, touch, and fine pointers, and retain a complete
  reduced-motion state.
- Prefer CSS and bounded native browser capabilities; do not add a motion
  runtime dependency for this mission.
- Update product docs where implementation reveals a reusable hierarchy rule.
- Add a user-visible changelog fragment.
- Record real UAT as a remaining validation gap unless it runs before closure.

## Required Proof

| Contract | Required Evidence |
| --- | --- |
| Community hierarchy | public/member/director rendered tests plus desktop/mobile screenshots |
| Active face and next action | service/rendered tests naming the face and target scene |
| Studio active/clear states | service and rendered tests for empty, one-item, and multi-item queues |
| No duplicated Content inventory | semantic rendered assertions and screenshot review |
| Director control disclosure | public/member/director DOM assertions and keyboard/focus check |
| Tenant/privacy | existing tenant, security, and rendered-route privacy suites |
| Responsive composition | desktop/mobile browser QA plus long-copy/zoom spot checks |
| Accessibility risks | heading, keyboard, focus, target-size, zoom/reflow, and screen-reader naming notes |
| Fluid interaction | rapid reversal/latest-intent check, keyboard/touch/fine-pointer parity, and reduced-motion state |
| Product collateral | updated doctrine only where changed, plan status, changelog fragment |
| Full regression | Ruff, Ruff format check, Pytest, Ty, and Chirp app check from root done criteria |

## Steward Synthesis

- Product/research: accepted subtractive hierarchy before further feature or
  visual-system expansion; real UAT remains required for validation.
- Surface contract: accepted audience replacement and service-owned section
  membership; templates must not improvise privacy or ranking.
- Rendering/UI: accepted one dominant object/action, fewer elevated surfaces,
  and screenshot QA at desktop/mobile.
- Writer Network: accepted active-face continuation as the member-home and Desk
  priority.
- Realm Studio: accepted action-first Studio, permanent depth in navigation,
  and object-local editing through disclosure.
- Privacy/safety: accepted that staff/director state remains capability-gated
  and visually outside the emotional path of play.
- Minority report: directors still need fast access to every deep control. The
  solution is persistent Studio navigation, scoped pages, and later searchable
  controls—not removal of capability.

## Dependencies And Risks

- The revised story-poster direction is the selected visual implementation
  target.
- Existing public/member/staff/director read models may need additive fields or
  display policy, but no schema change is planned.
- The fluid-UI source is translated as continuity and interruptibility, not a
  requirement for springs, dragging, elastic behavior, or route-wide motion.
- Simplification can hide needed work if empty/active display rules remain
  template-owned; service proof is required.
- Responsive improvements can regress keyboard order or accessible naming when
  controls move into disclosure; direct verification is required.
- Real-user behavior is not yet observed. Do not promote synthetic preference
  findings as broad user demand.

## Not Now

- New schema, migrations, runtime dependencies, routes, Blueprint fields, or
  raw layout controls.
- Redesigning the global Network home or every scoped workflow before these
  five representative surfaces prove the system.
- Building Studio-wide control search before the action-only home and room
  boundaries stabilize.
- Replacing Elbysodic's existing brand, navigation shell, or PBP vocabulary.
