# Studio Production Workflows Plan

Status: active after production gates
Owner: Product, web, service, storage, and test stewardship  
Created: 2026-05-02  
Last updated: 2026-05-09
Review by: 2026-05-30
Closure criteria: split into focused implementation PRs for board/world
editing, application and claim review, wanted outcomes, and director operations
shortcuts; archive when those PRs land or supersede the plan.

## 2026-05-09 Verification Update

The production-readiness roadmap moves broad Studio workflow expansion behind
auth/Railway smoke, storage/seed persistence, rendered privacy, and transaction
boundaries. Keep this plan active for application/claims review, wanted
outcomes, and daily Studio operations, but every new sensitive surface needs
service-policy proof and rendered privacy coverage in the same PR.

## Purpose

The Studio layer should help directors run a board without turning Elbysodic
into a generic admin dashboard. The current Studio already gathers boards,
world materials, applications, claims, wanted hooks, reserves, navigation,
appearance, and dry-run Blueprint intake. The next work should harden the
highest-value production workflows in small, testable slices.

## Product Shape

Studio work should stay close to the fiction:

- boards are playable locations and ritual lanes
- world materials are guidebook, canon, event, and application context
- applications and claims are casting and roster operations
- wanted hooks are structured plot and casting invitations
- operations should surface what needs a director without exposing private data
  to ordinary members

The public world remains the emotional surface. Studio controls should be calm,
capability-gated, and attached to the objects they change.

## PR Slices

### PR 1: Board And World Editor Ergonomics

Goal: make current board and material editing safer to use before adding new
controls.

Scope:

- tighten board media validation messages
- keep board image, alt, treatment, focal, and overlay preview close together
- add draft/published/current-event state clarity on material cards
- preserve mobile readability for board stages and material detail pages

Checks:

- rendered tests for board media alt text and material state controls
- browser QA for one dense location and one quiet location

### PR 2: Application And Claims Reviewer Operations

Goal: make review movement and claim conflict resolution easier without
leaking private applicant or staff notes.

Scope:

- keep application review queue, claim conflicts, and revision requests in one
  director path
- add clearer links from claim conflict cards to the affected application and
  claim desk
- preserve applicant-only visibility for applicant notes and staff-only
  visibility for staff notes/checklists

Checks:

- rendered privacy tests for review room, operations console, and claims desk
- policy tests for non-staff POST failure

### PR 3: Wanted Lifecycle Outcomes

Goal: turn interest into play with explicit next actions.

Scope:

- clarify open, reserved, filled, and archived wanted states
- surface accepted interest, prospective concepts, and plotting room handoff
  from wanted detail and casting desk
- keep archived/private hooks hidden from ordinary viewers unless they own or
  can manage the hook

Checks:

- rendered tests for owner, ordinary member, and staff views
- service tests for lifecycle transitions and plotting room creation

### PR 4: Director Operations Shortcuts

Goal: make `/studio/operations` a useful daily console without becoming a
second dashboard.

Scope:

- group action cards by attention needed, not table ownership
- add direct links to the first actionable review queue, claim conflict,
  active reserve, and hook with movement
- keep read-only ordinary-member rendering private and low-detail
- include route timing or health notes only when they have an owner

Checks:

- rendered tests for staff vs ordinary-member operations output
- no private application body, staff note, room note, or hidden hook title
  appears for ordinary members

### PR 5: Production Workflow Docs And QA

Goal: keep steward docs aligned with actual route behavior.

Scope:

- update `docs/product/control-topology.md` when controls move or collapse
- update `docs/product/information-hierarchy.md` when counters or latest lines
  gain new meanings
- update `docs/architecture/rendered-route-privacy-matrix.md` for any new
  route family or private data surface

Checks:

- `uv run pytest tests/test_forum_slice.py tests/test_policies.py -q --tb=short`
- browser QA on port 8001 for substantial Studio layout changes

## Dependencies

- Railway/shared-host smoke should stay ahead of broad Studio changes.
- Rendered privacy regressions should land with every new sensitive surface.
- Program Blueprint apply should wait for its hydration plan and transaction
  tests; Studio can keep linking to dry-run intake meanwhile.

## Not Now

- Hosted community creation.
- Billing or custom-domain setup.
- Role/capability editing UI.
- Raw CSS skin tooling.
- A generic analytics dashboard.
- Broad Studio template rewrites that are not tied to a director workflow.

## Steward Notes

Consulted root, docs, services, storage, web/UI, and tests steward boundaries.
The main boundary decision is to split Studio by director workflow rather than
by table. Risks are privacy leakage from staff desks, visual overload on
public world surfaces, and duplicate controls that bypass service policies.
