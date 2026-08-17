# Living Canon Layer


## Archival Note

Lifecycle: Deferred

Archived 2026-08-17 as not-now. Continuity Graph stays behind production trust. Related closed saga #137; do not mint ready leaves until provenance/review gates exist.

Status: deferred until production trust gates close
Owner: Product, domain, storage, service, and web stewardship  
Created: 2026-05-02  
Last updated: 2026-05-09
Review by: 2026-06-13
Closure criteria: split into PR-sized work for scene outcomes, source-linked
canon entries, proposal review, rendered privacy coverage, and any later
automation/digest integration.

## 2026-05-09 Verification Update

Living Canon remains a strong future primitive, but stewards converged that it
should wait behind production trust gates: Railway smoke, schema/seed
persistence, transaction boundaries, rendered privacy matrix expansion, and
core flow browser QA. The first future slice should still be manual scene
outcomes, not automation or public canon indexing.

## Purpose

Elbysodic should eventually help a play-by-post community turn completed play
into maturing world memory: a guidebook, timeline, relationship record, and
fan-wiki-like canon surface that shows how characters have changed the setting.

This should not begin as a freeform wiki bolted onto the forum. The stronger
Elbysodic primitive is a living canon layer: source-linked continuity captured
from scenes, events, wanted hooks, applications, claims, reserves, and director
materials. Automation can assist later, but canon should become public only
through reviewable, attributable updates.

This plan is the deferred Continuity Graph pillar from
`docs/product/strategy-spine.md`. It should stay behind production trust,
rendered privacy, transaction boundaries, and manual provenance until the
ordinary writing and Studio workflows are stable enough to supply reliable
source objects.

## Product Decision

Use a staged model:

1. A scene reaches a complete state.
2. Elbysodic asks for a scene outcome summary and affected objects.
3. The app stores source-linked outcome records against the thread.
4. Staff, scene participants, or configured directors can draft canon update
   proposals from those outcomes.
5. Approved proposals become canon entries that appear on character hubs,
   world material pages, location pages, event pages, and later a wiki-style
   canon index.
6. Automated digestion can suggest drafts later, but it should not silently
   publish canon or rewrite director material.

The public product language can be tested as Chronicle, Canon Log, Story
Ledger, or Living Canon. Avoid exposing "AI wiki" as the core promise. The
trustworthy promise is source-linked continuity with review.

## Current State

The app already has several useful anchors:

- `threads` store status, location, timeline, summary, posting mode, facets,
  participants, and board scope. `complete` is already a supported thread
  status.
- `posts` and `post_revisions` preserve authored beats and edit history.
- `materials` are community-scoped world pages with status, material type,
  facets, and current event behavior.
- `wanted_ads`, `character_plot_hooks`, `plotting_rooms`, applications,
  claims, and reserves already model board-production material outside ordinary
  threads.
- Notifications, watches, and read state are membership-scoped.
- Character hubs already combine identity, hooks, tracker/queue context, and
  recent posts.

The missing layer is not "pages that can hold prose." The missing layer is a
tenant-safe, reviewed link between story events and the world objects they
change.

## Principles

1. Canon is community-scoped from the first schema.
2. Canon facts need citations to source objects: thread, post, material,
   wanted hook, plot hook, plotting room, application, claim, reserve, or a
   future event record.
3. Store both membership and character where authorship matters. Membership
   owns the proposal or approval; character records public story context.
4. Do not infer consent-heavy character facts without a review step.
5. Private boards, staff notes, private plotting rooms, unpublished
   applications, and draft materials must not leak into public canon.
6. Canon updates should be append-friendly. Prefer revisions and superseding
   records over rewriting history in place.
7. Automation should create proposals with evidence, confidence, and affected
   objects. Approval remains a product workflow.

## Proposed App Structure

Add the feature as a new domain area rather than hiding it inside threads or
materials:

- `src/elbysodic/domain/models.py`
  - Add typed records for scene outcomes, canon entries, canon sources, canon
    links, canon proposals, and proposal events.
- `src/elbysodic/db/repositories/canon.py`
  - Own persistence methods for canon objects and source/link tables.
  - Keep every read/write scoped by `community_id`.
- `src/elbysodic/services/canon.py`
  - Own workflow decisions: who can summarize a scene, who can propose canon,
    who can approve, what visibility applies, and how source privacy is checked.
- `src/elbysodic/services/threads.py`
  - Surface thread completion and scene-outcome read models without taking over
    canon proposal workflow.
- `src/elbysodic/services/materials.py`
  - Surface canon links on world materials and events once canon entries exist.
- `src/elbysodic/web/pages/canon/`
  - Later public index/detail routes for approved canon entries.
- `src/elbysodic/web/pages/studio/canon/`
  - Director review queue for proposals, conflicts, and approvals.
- `src/elbysodic/web/pages/_components/`
  - Promote repeated canon source/citation, timeline beat, and canon impact
    components once they appear on multiple pages.

Do not make this an SPA. Use server-rendered Chirp pages with small
progressive-enhancement islands only where review forms or affected-object
pickers need focused interactivity.

## Proposed Data Model

### First Groundwork Tables

`thread_outcomes`

- `id`
- `community_id`
- `thread_id`
- `summary`
- `outcome_type` such as `scene_complete`, `event_beat`, or `relationship_change`
- `visibility` such as `participants`, `staff`, or `public`
- `created_by_membership_id`
- nullable `created_by_character_id`
- `created_at`
- `updated_at`

`thread_outcome_links`

- `id`
- `community_id`
- `thread_outcome_id`
- nullable target columns for affected objects:
  - `character_id`
  - `board_id`
  - `material_id`
  - `wanted_ad_id`
  - `character_plot_hook_id`
  - `plotting_room_id`
  - `facet_id`
- `relationship_key` such as `featured`, `affected`, `resolved`, `introduced`,
  `changed`, `location`, or `event`
- `note`
- `created_at`

This first slice captures source-linked continuity without requiring a public
wiki yet.

### Canon Tables

`canon_entries`

- `id`
- `community_id`
- `slug`
- `title`
- `entry_type` such as `timeline_beat`, `character_arc`, `relationship`,
  `location_history`, `faction_history`, `event_record`, or `guide_note`
- `summary`
- `body`
- `status` such as `draft`, `proposed`, `published`, `archived`, `superseded`
- `visibility` such as `public`, `members`, `staff`
- `created_by_membership_id`
- `approved_by_membership_id`
- `published_at`
- `created_at`
- `updated_at`

`canon_entry_sources`

- `id`
- `community_id`
- `canon_entry_id`
- nullable source columns:
  - `thread_id`
  - `post_id`
  - `thread_outcome_id`
  - `material_id`
  - `wanted_ad_id`
  - `character_plot_hook_id`
  - `plotting_room_id`
  - `application_id`
  - `character_claim_id`
  - `character_reserve_id`
- `source_note`
- `created_at`

`canon_entry_links`

- `id`
- `community_id`
- `canon_entry_id`
- nullable target columns:
  - `character_id`
  - `membership_id`
  - `board_id`
  - `material_id`
  - `wanted_ad_id`
  - `character_plot_hook_id`
  - `plotting_room_id`
  - `claim_type_id`
  - `facet_id`
- `relationship_key`
- `display_order`
- `created_at`

`canon_proposals`

- `id`
- `community_id`
- `proposed_by_membership_id`
- nullable `proposed_by_character_id`
- nullable `target_entry_id`
- nullable `source_thread_outcome_id`
- `title`
- `summary`
- `body`
- `status` such as `draft`, `needs_review`, `approved`, `rejected`,
  `changes_requested`
- `automation_kind`
- `automation_confidence`
- `review_note`
- `created_at`
- `updated_at`

`canon_proposal_events`

- `id`
- `community_id`
- `canon_proposal_id`
- `actor_membership_id`
- `actor_character_id`
- `from_status`
- `to_status`
- `note`
- `created_at`

### Later Tables

Add these only after the first slices prove the workflow:

- `canon_entry_revisions` for published entry body/history diffs.
- `canon_conflicts` for two proposed facts touching the same relationship,
  claim, timeline beat, or event state.
- `canon_digest_jobs` for automated summary runs, model/provider metadata,
  source range, prompt version, and failure/retry state.
- `canon_subscription_rules` if writers or directors want notifications when
  canon changes touch their faces, factions, claims, or watched events.

## Workflow Sequence

### PR 1: Scene Outcome Capture

Goal: completed scenes can store structured outcome notes and affected objects.

Tasks:

- Decide how the existing `complete` thread status should trigger, request, or
  reveal outcome capture without breaking queue semantics.
- Add `thread_outcomes` and `thread_outcome_links`.
- Add repository methods to create, update, list, and read outcomes by thread.
- Add service methods that allow staff and scene participants to record outcome
  summaries.
- Render outcomes on the thread page beneath the transcript or in a compact
  "Scene outcome" band.
- Add tests for tenant scope, participant/staff permissions, and private-board
  visibility.

Acceptance checks:

- A completed scene can have one or more outcome records.
- Outcomes can cite affected characters, boards/locations, materials/events,
  facets, hooks, and plotting rooms.
- Ordinary members cannot create outcomes for scenes they cannot view.
- Outcome visibility does not leak private-board information into public pages.

### PR 2: Character And World Impact Surfaces

Goal: scene outcomes become visible where they help writers find inspiration.

Tasks:

- Add read models for character-related outcomes.
- Show recent public/member-visible outcomes on character hubs.
- Show material/event-related outcomes on world material pages.
- Show location-related outcomes on board/location pages.
- Add a shared citation/source component.

Acceptance checks:

- Character pages show how a face has affected recent play without replacing
  the tracker/queue.
- World/event pages can show recent changes sourced from scenes.
- Source links are clear and permission-aware.

### PR 3: Canon Entry And Proposal Foundation

Goal: establish the reviewed canon primitive before automation exists.

Tasks:

- Add `canon_entries`, `canon_entry_sources`, `canon_entry_links`,
  `canon_proposals`, and `canon_proposal_events`.
- Add `services/canon.py` with create proposal, request changes, approve,
  reject, publish, archive, and supersede workflows.
- Add a Studio review queue for proposals.
- Add public/member-visible canon entry detail pages for published entries.
- Notify affected proposal owners or linked face owners when review status
  changes, if notification semantics are clear.

Acceptance checks:

- Staff can approve a proposal into a published canon entry.
- Writers can see proposal status for items they submitted.
- Canon entries always carry at least one source.
- Public canon pages never reveal private source titles, staff notes, or
  inaccessible plotting-room context.

### PR 4: Timeline And Canon Index

Goal: turn entries into a useful guidebook surface.

Tasks:

- Add a canon index route with filters by entry type, character, location,
  material/event, facet, and status where permitted.
- Add a timeline view for dated or ordered entries.
- Add entry cards to world pages and Studio production rooms.
- Consider whether `materials` need a new `material_type` or whether canon
  entries should remain separate from director-authored guides.

Acceptance checks:

- Members can browse public canon by face, faction/facet, location, event, and
  recent changes.
- Staff can find drafts/proposals separately from public canon.
- Canon browsing does not compete with current writing actions.

### PR 5: Assisted Digest Proposals

Goal: automation suggests canon updates with source evidence, but does not
publish them.

Tasks:

- Add a digest job abstraction with source range, prompt version, output JSON,
  confidence, and reviewer-visible evidence.
- Generate proposal drafts from completed thread outcomes first, not raw live
  threads.
- Require every suggestion to cite source posts or an approved thread outcome.
- Add a staff review UI that makes accepting, editing, or rejecting suggestions
  faster than writing from scratch.

Acceptance checks:

- Digest output is stored as proposals, not published entries.
- Staff can see source evidence and confidence.
- Low-confidence or uncited claims cannot be approved without manual editing.
- Private content and staff-only sources are excluded unless the target canon
  visibility permits them and the reviewer has access.

## Permissions And Privacy

Use these default rules until product research proves something else:

- Thread participants can draft or edit outcome summaries for scenes they can
  view.
- Staff can manage all outcomes in their community, subject to board privacy.
- Writers can propose canon based on scenes or objects they can view.
- Only staff/director roles can publish public canon.
- A canon entry with a private source can still exist, but its public rendering
  must redact or omit inaccessible source details.
- Character-linked canon should notify or at least surface to the owning
  membership before public publication when it makes claims about a face's arc,
  relationship, status, or major event impact.

Rendered privacy matrix additions should cover:

- thread outcome visibility on public and private threads
- character hub outcome snippets
- material/event outcome snippets
- canon entry detail source redaction
- Studio canon proposal queue
- cross-tenant slug collisions for canon entries
- inactive membership and faceless behavior for proposal actions

## Navigation And UI Placement

Early UI should live near the story object:

- Thread page: "Scene outcome" near the completed transcript, not in the
  breadcrumb row or queue controls.
- Character hub: "Recent canon impact" below identity/plotter material and
  above or near tracker history if it helps continuity.
- Material/event page: "Recent story changes" near the material body or current
  event context.
- Location/board page: "Recent scene outcomes" below place identity and above
  long thread lists only when it clarifies the location's current pressure.
- Studio: "Canon review" as a director production room, not a generic admin
  table.

Use citation/source components instead of long explanatory prose. Writers
should be able to jump from a canon beat back to the scene that proved it.

## Open Questions

- How should the existing `complete` thread status interact with outcome
  capture, queue logic, read state, and later canon proposals?
- Who can mark a scene complete: starter, all participants, any participant,
  or staff only?
- Do outcomes require participant confirmation before public canon proposals
  can be generated?
- Should some canon entries be director-authored guides stored in `materials`,
  or should all story-derived canon live in `canon_entries` and link to
  materials?
- How should spoilers work for communities with private arcs, application
  reveals, or hidden event phases?
- Do relationship changes need a structured relationship primitive before
  canon links can model them well?

## Not Now

- Fully automatic public wiki updates.
- Cross-community canon graphs.
- Generic MediaWiki-style page editing as the first slice.
- Search indexing beyond ordinary database queries.
- Model/provider integration before manual scene outcomes and proposal review
  exist.
- Public canon generated from raw private plotting-room messages.
- Rewriting old posts or post revisions to match later canon.

## Risks

- Trust risk if automation appears to decide canon without consent.
- Privacy risk if source links expose private boards, staff notes, applications,
  or plotting rooms.
- Product sprawl if canon entries duplicate world materials without a clear
  source/review distinction.
- UI noise if every scene outcome appears everywhere.
- Schema rigidity if links are over-modeled before the app knows which canon
  surfaces matter most.
- Moderation risk if character-impact entries publish before affected writers
  can review sensitive claims.

## Suggested Next Checks

- Prototype the manual thread outcome form on a completed thread before adding
  canon entry pages.
- Audit current thread statuses and queue logic before introducing `complete`.
- Add a small seed example showing one completed scene affecting a character,
  a location, and a current event.
- Extend `docs/architecture/primitives.md` after the first implemented slice
  names the durable primitive.

## Consulted Stewards

- Root constitution: PBP-native studio layer, character identity, world
  materials, wanted hooks, plotting rooms, and tenant-aware primitives.
- `docs/AGENTS.md`: product and architecture docs should distinguish current,
  planned, and deferred behavior while preserving PBP vocabulary.
- `src/elbysodic/domain/AGENTS.md`: new records need explicit typed
  community, membership, and character ownership.
- `src/elbysodic/db/AGENTS.md`: new product tables require `community_id`,
  repository methods, migration discipline, and tenant tests.
- `src/elbysodic/services/AGENTS.md`: workflow and permissions belong in
  service methods, not page-local SQL.
- `src/elbysodic/web/AGENTS.md`: server-rendered pages, shared components,
  accessible controls, and privacy-safe rendering remain the default.
