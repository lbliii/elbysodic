# Continuity Graph Readiness Contract

Continuity Graph is deferred until Elbysodic can prove source-link privacy,
review authority, notification visibility, and export boundaries for manual
canon work. This contract is the backend gate for the first implementation PR;
it is not a schema design and it does not authorize automatic canon.

## Current Posture

- No Continuity Graph schema tables exist yet.
- No public continuity or canon route family exists yet.
- Schema-neutral domain vocabulary exists in
  `src/elbysodic/domain/continuity.py` for manual proposals, source
  citations, affected objects, review events, lifecycle state, visibility, and
  approved canon entry drafts.
- Existing world materials, wanted-hook types, and scene-context labels may use
  "canon" vocabulary, but they are not reviewed Continuity Graph records.
- Program, plotting, claims, applications, and notifications already carry
  source links in specific workflows. They are examples to inspect, not a
  generic continuity primitive.
- `src/elbysodic/services/continuity.py` owns a schema-neutral source
  visibility gate for future continuity read models. It resolves board,
  location, scene/thread, post, character, material, wanted-hook, claim, and
  reserve references through tenant-aware repository methods and returns
  redacted visible/hidden results before any route or stored proposal exists.

## First Implementable Slice

The first real backend slice should be manual and reviewed:

- scene outcome proposals authored by an active same-community membership
- explicit source citations to same-community threads and posts
- explicit affected-object links to same-community characters, materials,
  boards/locations, wanted hooks, claims/reserves, events, or future typed
  continuity targets
- lifecycle states for draft, submitted, revision requested, approved,
  rejected, and archived
- review events that record staff membership actor separately from any optional
  public character context
- visibility decisions owned by services before any read model renders public
  canon
- notifications only to participants, owners, or staff who can already see the
  cited source and affected target
- export rows scoped to one community and preserving source provenance

## Must Not Ship First

- AI-generated canon
- automatic scene summarization
- public canon marketplace or discovery
- public route rendering for unreviewed proposals
- citations to private scene, plotting, application, staff, or access-request
  notes unless the viewer can already read that source
- inferred affected objects from prose without explicit reviewer confirmation
- global continuity records detached from `community_id`

## Required Backend Gates

Before adding continuity schema, services, routes, or notifications, the PR
must include proof for:

- tenant ownership for every source and affected object join
- active membership and named staff capability checks for proposal review
- lifecycle transition rules and rollback behavior
- same-community review actor membership and optional character context
- source-link visibility for participant, unrelated member, staff/director,
  inactive, public, and cross-community viewers when rendered surfaces exist
- notification target filtering that hides private source titles, notes, and
  links from unauthorized memberships
- export behavior that includes only one community's continuity rows and
  citations

The source visibility gate is intentionally conservative. Public and member
viewers may see only sources they can already read: public locations, visible
scenes/posts, accepted faces, published materials, open wanted hooks, and
public claimed claims. Private scene participants can see their own private
scene/post references inside otherwise visible locations. Staff/director
capabilities can reveal review-only source labels for current-community
workflow records, but inactive viewers, cross-community viewers, malformed
post/thread pairs, private boards, draft materials, private claims, reserves,
and other writers' private records return redacted hidden statuses unless the
viewer already owns or can review that source.

## Stop-And-Ask Points

Stop for human review before:

- adding continuity schema tables, migrations, repository APIs, or domain row
  models
- adding public or member-facing continuity routes
- changing thread, post, material, wanted, claim, reserve, plotting, or
  notification visibility to support continuity
- adding review/audit event storage
- adding AI or automatic summary generation

## Steward Notes

- Domain: source links and affected objects must be explicit typed
  relationships.
- Service: review, visibility, and notification decisions belong in services.
- Storage: every source and affected join row must carry or validate
  `community_id`.
- Web: rendered canon surfaces stay absent until privacy proof covers every
  viewer mode in the rendered route privacy matrix.
- User panel: safety-boundary writers need confidence that tentative plotting,
  private scenes, staff notes, and unreviewed summaries cannot silently become
  public canon.
