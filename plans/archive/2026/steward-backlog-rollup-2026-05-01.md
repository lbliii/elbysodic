# Steward Backlog Rollup Snapshot

Status: archived 2026-05-18; superseded by production-readiness roadmap
Owner: Steward workflow  
Created: 2026-05-01  
Last updated: 2026-05-09
Review by: 2026-05-16
Source: `ask stewards` consultation on `main` after `git fetch --prune`  
Closure criteria: split this into concrete backlog items, implementation
plans, or issues; then move this file to `plans/archive/2026/` as completed or
superseded.

## Archival Note

Archived because the actionable production, identity, privacy, and surface
risks are now tracked in the production-readiness roadmap and focused active
plans. Keep this file as historical steward synthesis.

## 2026-05-09 Verification Update

This snapshot has been superseded as the active sequencing document by
`plans/in-progress/production-readiness-roadmap-2026-05-09.md`. Preserve its
minority reports and progress log as history, but do not use it as the current
backlog order unless a later agent archives or extracts the remaining items.

## Purpose

Capture the first scoped steward prioritization report so future agents can
build a backlog without rerunning the conversation from scratch. This is a
snapshot, not a permanent roadmap.

## Consulted Stewards

- Root constitution: `AGENTS.md`
- Product and architecture: `docs/AGENTS.md`
- Package and tooling: `src/elbysodic/AGENTS.md`
- Domain model: `src/elbysodic/domain/AGENTS.md`
- Service layer: `src/elbysodic/services/AGENTS.md`
- Storage and migrations: `src/elbysodic/db/AGENTS.md`
- Rendering and UI: `src/elbysodic/web/AGENTS.md`
- Blueprint contract: `src/elbysodic/blueprints/AGENTS.md`
- Tests: `tests/AGENTS.md`

## Recommended Priority List

1. Harden Studio production workflows around board, world, wanted, and
   application operations.
   Confidence: high.
   Why now: strong convergence from root, docs, services, web/UI, DB, and
   tests. The root guide says board-running materials belong in the studio
   layer; existing routes already include Studio, applications, claims,
   casting, wanted, and world surfaces.

2. Finish the character hub and active-face discovery loop.
   Confidence: high.
   Why now: the root guide says character profiles are becoming hubs and the
   active/default face should reduce cognitive load across discovery, queues,
   joins, and filters.

3. Create a privacy and tenant test matrix for rendered routes.
   Confidence: high.
   Why now: security docs require rendered page privacy tests for routes that
   expose scoped data. Route count has grown, and tests are the strongest
   risk-reduction lever before broadening workflows.

4. Ship Program Blueprint YAML intake as a dry-run-first Studio flow.
   Confidence: medium-high.
   Why now: the typed contract and validation already exist, and
   `docs/product/program-blueprints.md` defines the intended upload, parse,
   validate, preview, and apply flow. Apply should wait for a safe preview and
   service-layer hydration boundary.

5. Establish the first post-baseline migration pattern when the next schema
   feature lands.
   Confidence: medium.
   Why now: current baseline is version `1`; the next schema-affecting feature
   should demonstrate the fresh-schema plus ordered-migration plus migration
   test pattern.

6. Do a paragraph, control, and component consolidation pass on the
   highest-traffic writing surfaces.
   Confidence: medium.
   Why now: paragraph rhythm and UI vocabulary docs identify post bodies,
   composer preview, thread page, board page, character hub, and Studio as dense
   text surfaces. Start with thread reader/composer and character hub.

7. Thin the service facade only where feature work creates pain.
   Confidence: medium-low.
   Why now: `services/forum.py` is broad, but a pure refactor is less valuable
   than extracting narrower seams while building Studio, blueprint intake, or
   active-face workflows.

## Minority Reports

- Test steward would put the rendered-route privacy matrix first before any new
  feature work. The rollup places it third because it can move alongside Studio
  hardening, but the risk is real.
- Blueprint steward would move YAML intake earlier because the contract is
  already mature. The rollup keeps it behind Studio production hardening so
  imports hydrate into stable director workflows.
- Package steward recommends landing the steward docs before large backlog
  implementation so future PRs can cite the workflow cleanly.

## Not Now

- Hosted forum creation.
- Billing.
- Custom domains.
- Cross-community dashboards.
- Broad single-page app rewrites.
- Raw theme CSS imports.
- Generic admin-dashboard expansion.

These are either explicitly deferred or would blur the current PBP-native
product spine.

## Remaining Work

The original seven priorities have each received at least one implementation
slice. Keep this snapshot active only while turning the remaining gaps into
focused plans, issues, or follow-up PRs.

- Stabilize and curate the current cross-cutting change set before adding more
  surface area. Confirm the diff is reviewable, Steward Notes are ready, and
  full CI remains green.
- Split Studio production workflow follow-ups into smaller work. The active
  split now lives in
  `plans/in-progress/studio-production-workflows-2026-05-02.md` and covers
  board/world editor ergonomics, application/claims reviewer operations, wanted
  lifecycle outcomes, director operations shortcuts, and docs/QA alignment.
- Expand the rendered-route privacy matrix beyond the first draft-material and
  inactive-identity cases. Prioritize staff desks, notification surfaces,
  application review rooms, plotting rooms, and cross-community recovery pages.
  Plotting-room notification leakage now has a rendered regression; continue
  with staff desks, application review rooms, and cross-community recovery pages.
- Decide the next Program Blueprint step: keep dry-run preview as-is, or design
  a separate hydration plan with repository/service boundaries, duplicate
  handling, rollback behavior, and tenant tests.
- Continue character hub and active-face discovery only where it reduces a real
  writer workflow: filtered queues, discovery defaults, join/reply defaults,
  and plot/wanted handoffs.
- Continue component consolidation opportunistically on writing surfaces and
  Studio controls. Avoid broad template rewrites while the current batch is
  still unmerged.
- Thin `AppServices` only at natural seams created by feature work. Recent
  examples are blueprint preview and material production state.

## Progress Log

- 2026-05-01: Started the Studio production workflow priority with wanted-hook
  lifecycle controls. The first scoped slice lets permitted hook managers move
  wanted hooks through open, reserved, filled, and archived states from the
  wanted detail page while preserving archived-hook privacy for ordinary
  viewers.
- 2026-05-01: Started the rendered-route privacy matrix priority with
  `docs/architecture/rendered-route-privacy-matrix.md` and a first regression
  proving draft world materials stay staff-only on `/world`, direct material
  routes, and Studio/material editor surfaces.
- 2026-05-01: Hardened the application/claims review flow by routing revision
  requests from the applications index into the review room instead of sending
  blank revision requests, and added coverage that private staff notes and
  review checklists stay hidden from applicants.
- 2026-05-01: Started the character hub active-face loop with owner-only next
  actions on character profiles. Current faces now expose reply, discovery,
  casting, and plot-hook actions from the hub, while non-current owned faces
  nudge writers to make the face current before using active-face defaults.
- 2026-05-01: Extended rendered-route privacy coverage for inactive identities.
  Member directory/profile routes and direct character routes now treat inactive
  memberships as absent, and cross-realm character recovery ignores inactive
  faces instead of offering a realm switch to retired cast.
- 2026-05-01: Started Program Blueprint YAML intake as a dry-run-only Studio
  flow. Directors can paste YAML in Studio intake, map director-friendly keys
  into the typed blueprint contract, see validation notes and launch counts, and
  confirm that no hydration or database changes occur yet.
- 2026-05-01: Tightened the schema migration pattern by documenting the actual
  current version, making the next-schema-change checklist require contiguous
  post-baseline migrations, and adding ledger tests that prove historical
  baseline databases advance through ordered migrations to the current version.
- 2026-05-01: Started the paragraph/control/component consolidation pass on
  writing surfaces by extracting shared composer view-toggle and formatting
  toolbar macros, then reusing them across new-thread, reply, and edit-post
  composers without changing the existing Alpine behavior or controls.
- 2026-05-01: Started the service-facade thinning pass where recent feature work
  created a natural boundary: Program Blueprint preview permission and parsing
  orchestration now lives in `services/blueprints.py`, while `AppServices`
  remains a small delegating route-facing facade.
- 2026-05-01: Continued Studio production workflow hardening with director-only
  world material state controls. Studio draft-material cards can now publish a
  material, or publish a draft event as the current event while demoting the
  previous current event; ordinary members cannot mutate draft material state.
- 2026-05-01: Followed the steward stabilization recommendation by turning the
  plan's backlog split into an explicit remaining-work list and moving material
  production-state orchestration into `services/materials.py`, leaving
  `AppServices` as a route-facing delegator.
- 2026-05-14: Continued progressive surface extraction after the performance
  hardening pass. Writer activation, Studio operations, network catalog,
  board/thread read models, and material detail orchestration now live in
  domain-named service modules with narrower repository protocols where the
  module owns the read model. `AppServices` remains the route-facing facade,
  and `surface-contract-architecture.md` now records the extraction pattern for
  future steward review.
- 2026-05-01: Continued the next priority batch on
  `codex/steward-next-priorities`: plotting room notifications now filter
  private room targets from non-participant inboxes, visible unread counts honor
  target visibility, notifications expose current-face discovery and plotter
  handoffs, Studio operations links to dry-run blueprint intake, and the Program
  Blueprint docs/UI name the hydration gate before apply work.
