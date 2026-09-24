# Continuity Graph Readiness Contract

Continuity Graph remains gated at the rendered-surface and notification-fanout
boundaries. Elbysodic now has the first manual backend slice with source-link
privacy, review authority, notification-target planning, and export proof. This
contract does not authorize automatic canon, public/member routes, or fanout.

## Current Posture

- Schema version 27 stores tenant-scoped proposals, citations, affected-object
  links, review events, and approved public canon entries.
- No public continuity or canon route family exists yet.
- Domain vocabulary and persisted row models exist in
  `src/elbysodic/domain/continuity.py` for manual proposals, source
  citations, affected objects, review events, lifecycle state, visibility, and
  approved canon entry drafts.
- Existing world materials, wanted-hook types, and scene-context labels may use
  "canon" vocabulary, but they are not reviewed Continuity Graph records.
- Program, plotting, claims, applications, and notifications already carry
  source links in specific workflows. They are examples to inspect, not a
  generic continuity primitive.
- `src/elbysodic/services/continuity.py` owns source visibility, proposal
  lifecycle, review, redacted read models, review queues, and a target plan for
  future notification fanout. It resolves board,
  location, scene/thread, post, character, material, wanted-hook, claim, and
  reserve references through tenant-aware repository methods and returns
  redacted visible/hidden results before any future route renders.
- `src/elbysodic/services/exports.py` includes one-community continuity counts,
  ownership, and citation provenance without serializing review notes or post
  excerpts. No archive/download route or new export file format was added.

## Implemented Backend Slice

The first real backend slice is manual and reviewed:

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

## Manual Source Visibility Matrix

The first slice may cite only explicit same-community scene sources and
explicit same-community affected objects. Source citations are limited to:

- `thread` / `scene`: a same-community thread the viewer can already read.
- `post`: a same-community post with an explicit `source_thread_id`; malformed
  post/thread pairs stay hidden.

Affected-object links are explicit reviewer-visible relationships, not inferred
from prose. The first slice may link same-community characters, published or
staff-visible materials, boards/locations, wanted hooks, claims, reserves, and
future typed continuity targets only after the same visibility gate can prove
the viewer may see that object name.

Visibility decisions are service-owned before rendering. Templates must receive
already-redacted read models; they must not decide whether to hide a cited
scene title, post excerpt, affected object name, review state, or notification
target.

| Viewer mode | Proposal title | Cited scene title | Post excerpt | Affected object names | Review state | Notifications |
| --- | --- | --- | --- | --- | --- | --- |
| Source participant | Own draft/submitted proposal titles and approved visible titles. | Visible when the participant can already read the source scene. | Visible only for the cited post the participant can already read; excerpt length is service-capped. | Visible only for affected objects the participant can already read or owns. | Own proposal lifecycle and applicant-visible revision notes only. | May receive proposal movement notifications for visible sources and affected objects. |
| Unrelated active member | Approved member/public titles only; no draft/submitted proposal titles unless they own an affected object and the service grants a visible handoff. | Public/member-readable scene titles only. | Public/member-readable cited post excerpt only; private scenes and posts are redacted. | Public/member-readable affected names only. | Approved/public state only; no staff notes, reviewer checklist, or private revision context. | Only if they own or are responsible for a visible affected object; notification copy must omit hidden source titles. |
| Staff/director | Draft, submitted, revision, approved, rejected, and archived titles inside the current community. | Visible for current-community sources staff can already review. | Visible for current-community sources staff can already review; service-capped excerpt. | Visible for current-community objects staff can already review. | Full review state, reviewer notes, checklist, and audit events. | May receive review queue notifications with visible source and affected-object labels only. |
| Inactive member | Hidden. | Hidden. | Hidden. | Hidden. | Hidden; route recovery must not confirm private proposal existence. | None. |
| Public visitor | Approved public canon title only after a future public canon route is explicitly approved. | Public scene title only after public continuity routes are approved. | No excerpt in the first backend slice. | Public affected object names only after public continuity routes are approved. | Public approved state only; no draft, review, or revision state. | None. |
| Signed-in account visitor without local membership | Same as public visitor; account identity does not grant community continuity access. | Same as public visitor. | No excerpt in the first backend slice. | Same as public visitor. | Same as public visitor. | None. |
| Cross-community viewer | Hidden. | Hidden. | Hidden. | Hidden. | Hidden; no title or object-name confirmation. | None. |

Notification targeting must be computed from visible source and affected-object
read models. A target is eligible only when all of these are true:

- the target is an active membership in the proposal community
- the target can already see the cited source label and affected object label
- the target is the proposal author, a source participant, an affected-object
  owner/responsible staff member, or a staff/director reviewer

Export behavior for the first slice must include only one community's
continuity rows, source citations, affected-object links, review events, and
approved canon entries. Exports may include hidden source identifiers for
provenance inside that community archive, but public preview exports must not
include private post excerpts, staff notes, reviewer checklist content, access
request details, or cross-community identifiers.

## Implementation Test Matrix

The backend now covers the first five named proofs below. The rendered-route
placeholder remains mandatory before any continuity route is introduced:

- `test_continuity_proposal_sources_reject_cross_community_threads_posts_and_objects`
- `test_continuity_proposal_source_visibility_matrix_redacts_private_titles_and_excerpts`
- `test_continuity_review_authority_requires_active_staff_or_director_membership`
- `test_continuity_notifications_filter_targets_by_source_and_affected_object_visibility`
- `test_continuity_export_stays_single_community_and_redacts_private_review_material`
- `test_continuity_routes_render_redacted_read_models_without_template_owned_filtering`

## Must Not Ship First

- AI-generated canon
- automatic scene summarization
- public canon marketplace or discovery
- approved-canon retraction or supersession before that lifecycle is designed
- public route rendering for unreviewed proposals
- citations to private scene, plotting, application, staff, or access-request
  notes unless the viewer can already read that source
- inferred affected objects from prose without explicit reviewer confirmation
- global continuity records detached from `community_id`

## Backend Gates

The v27 backend includes proof for:

- tenant ownership for every source and affected object join
- active membership and named staff capability checks for proposal review
- lifecycle transition rules and rollback behavior
- same-community review actor membership and optional character context
- service read-model visibility for participant, unrelated member,
  staff/director, inactive, public, and cross-community viewer shapes; rendered
  proof remains deferred with the routes
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

- changing the v27 continuity schema, lifecycle, repository API, or public
  visibility contract
- adding public or member-facing continuity routes
- changing thread, post, material, wanted, claim, reserve, plotting, or
  notification visibility to support continuity
- adding review/audit event storage
- adding notification fan-out, notification copy, or unread-count behavior for
  continuity proposals
- adding export/import rows, public preview exports, archive files, or
  provenance redaction behavior for continuity proposals
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
