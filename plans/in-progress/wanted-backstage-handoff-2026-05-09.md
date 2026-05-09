# Wanted Backstage Handoff Plan

Status: implemented locally; archive after full gate verification
Owner: Product, service, web, storage, and test stewardship
Created: 2026-05-09
Last updated: 2026-05-09
Review by: 2026-05-30
Closure criteria: archive after the full local gate passes or any remaining
same-user-different-community proof gap is moved into the production-readiness
roadmap.

## 2026-05-09 Implementation Update

The first wanted backstage slice landed locally:

- wanted-interest notes are private to the interested writer, hook creator, and
  casting-capable staff
- wanted detail shows derived backstage states and direct plotting-room or
  scene links for eligible viewers
- `/plotting` groups wanted handoffs by raised hands, in plotting, ready for
  scene, and scene started
- forged wanted-interest notifications are hidden from unrelated members
- Studio operations includes a Backstage `Ready for scene` card
- product and rendered privacy docs now capture the shipped contract

## Purpose

The Wattpad research identified **backstage** as the strongest Elbysodic-native
translation: not a global social feed, not public inline comments, and not a
generic DM surface, but object-bound coordination that helps writers and
directors move play forward.

The first implementation target should be wanted hooks because the repo already
has the core ingredients:

- wanted hooks and wanted interest
- prospective wanted interest for characters a writer would create
- hook creator/staff controls
- plotting rooms sourced from wanted interest
- plotting room participants, messages, plan state, and scene handoff
- notifications for wanted interest, plotting room creation, reserves, and
  scene start

The gap is product coherence and privacy. Interest currently raises a hand,
but the backstage lane is not explicit enough: the hook detail, plotting desk,
writer state, and director state should agree on what happens next and what is
private.

## Product Decision

Treat the first backstage slice as:

> A wanted hook can gather interest, expose safe public signals, and give the
> hook owner, interested writer, and staff a private coordination lane that can
> become a plotting room and then a scene.

Keep the existing `/plotting` route for now. Do not rename routes or introduce
`/backstage` until the primitive is proven, because public route/navigation
changes require explicit product review.

## Current State

Existing code surfaces:

- `src/elbysodic/db/repositories/wanted.py`
  - `wanted_ad_interests` supports membership-owned interest with optional
    character, prospective character name, note, and status.
  - Current interest statuses used in services/tests are `interested`,
    `plotting`, and `reserved`.
- `src/elbysodic/services/casting.py`
  - `read_wanted_ad()` builds wanted detail, interests, reserves, viewer
    interest, and manage permissions.
  - `express_wanted_interest()`,
    `express_prospective_wanted_interest()`,
    `reserve_wanted_interest()`, and
    `create_reserve_for_wanted_interest()` own the casting workflow.
- `src/elbysodic/services/plotting.py`
  - `plotting_desk()` lists rooms and manageable wanted interest.
  - `create_plotting_room_from_wanted_interest()` links wanted interest to a
    room and moves interest to `plotting`.
  - `create_thread_from_plotting_room()` turns room plans into scenes.
- `src/elbysodic/web/pages/wanted/{wanted_slug}/page.py`
  - POST intents already express interest, express prospective interest,
    reserve interest, start plotting room, create reserve, and update lifecycle.
- `src/elbysodic/web/pages/wanted/{wanted_slug}/page.html`
  - Wanted detail renders interest cards and management controls.
- `src/elbysodic/web/pages/plotting/page.html`
  - Plotting desk renders active rooms and an interest inbox.
- `tests/test_forum_slice.py`
  - Existing coverage proves wanted interest, prospective interest, reserve
    creation, plotting-room creation, plotting-room privacy, and scene handoff.

## Invariants

- Keep `community_id` explicit in repositories, services, routes, read models,
  notifications, and tests.
- Users remain global accounts. Wanted interest belongs to a
  `CommunityMembership`; public authorship or story context may reference a
  `Character`.
- Do not make backstage a generic DM replacement.
- Public wanted detail may show safe social proof, but private interest notes,
  staff-only context, and room state must not leak to unrelated members.
- Hook creator, interested writer, room participants, and staff should see the
  next action in the same PBP vocabulary.
- Ordinary members should understand whether a wanted hook is open, reserved,
  filled, or archived without seeing private coordination.
- Same-user-different-community requests must not recover or infer wanted
  interest, rooms, messages, or notifications across tenants.

## PR Slices

### PR 1: Privacy-Safe Wanted Interest Read Model

Goal: split public wanted signals from backstage coordination data.

Scope:

- Extend the wanted detail read model so each interest carries a visibility
  decision for the current viewer:
  - public signal: display name or safe count
  - participant signal: the viewer's own interest status and next action
  - manager signal: note, prospective pitch, reserve/start-room controls
  - staff signal: same as manager for casting-capable staff
- Hide interest notes and prospective pitch text from unrelated ordinary
  members unless the product intentionally marks them public.
- Keep the hook creator and casting staff able to inspect all interest notes.
- Let the interested writer see their own note/status and, once a room exists,
  a direct route into that room.
- Add a room summary or room href to wanted-interest read-model rows where a
  plotting room already exists, so detail pages can say `Open plotting room`
  instead of only `Plotting room started.`
- Avoid schema changes in this slice unless implementation proves the current
  `note` field needs an explicit visibility flag.

Expected files:

- `src/elbysodic/services/read_models.py`
- `src/elbysodic/services/casting.py`
- `src/elbysodic/services/plotting.py` if shared room-summary helpers need to
  move or become available to casting
- `src/elbysodic/web/pages/wanted/{wanted_slug}/page.html`
- `tests/test_forum_slice.py`

Proof:

- Hook creator sees interest note and start-room control.
- Casting staff sees interest note and start-room control.
- Interested writer sees their own status and note.
- Unrelated ordinary member does not see another writer's note or prospective
  pitch.
- Existing public wanted browsing still shows the hook and safe social proof.
- Same-user-different-community cannot see or open the interest/room.

### PR 2: Backstage Handoff Actions On Wanted Detail

Goal: make the wanted detail page the canonical place to move one raised hand
to the next step.

Scope:

- Present a clear backstage lane on manageable wanted hooks:
  - `Raised hand`
  - `Start plotting room`
  - `Open plotting room`
  - `Ready for scene` when the linked room is ready
  - `Open scene` when the linked room has a target thread
- Keep labels PBP-native: `raised hand`, `plotting room`, `ready for scene`,
  `reserve`, `filled`, `watching`, `waiting`.
- Keep existing POST intents where possible.
- Do not add new interest statuses until necessary. Derive stage from the
  existing interest status plus linked room state:
  - `interested` + no room = raised hand
  - `plotting` + room.status `brainstorming` or `paused` = plotting
  - `plotting` + room.status `ready` = ready for scene
  - `plotting` + room.status `threaded` = scene started
  - `reserved` = reserved
- If new status names such as `accepted` or `waiting` become necessary, stop
  and route through the schema/data-model review checklist before changing
  stored values.

Expected files:

- `src/elbysodic/services/read_models.py`
- `src/elbysodic/services/casting.py`
- `src/elbysodic/web/pages/wanted/{wanted_slug}/page.html`
- `src/elbysodic/web/pages/_components/wanted.html` only if repeated wanted
  backstage UI emerges
- `tests/test_forum_slice.py`

Proof:

- After interest is expressed, creator detail shows `Start plotting room`.
- After room creation, creator and interested writer see `Open plotting room`.
- After room is marked ready, wanted detail points at the room as ready for
  scene.
- After scene start, wanted detail points at the scene and does not offer a
  duplicate start-room action.
- Ordinary members do not get private room links.

### PR 3: Plotting Desk As Backstage Pulse

Goal: make `/plotting` read like the writer/director backstage pulse without
renaming the route.

Scope:

- Adjust copy and grouping on `src/elbysodic/web/pages/plotting/page.html` so
  the page explains the handoff through action labels, not instructional text.
- Group manageable wanted interest by stage:
  - raised hands
  - in plotting
  - ready for scene
  - threaded
- Keep active rooms grouped separately from the interest inbox.
- Preserve current ability to open the source wanted hook or enter the room.
- Use existing room status where possible.

Expected files:

- `src/elbysodic/services/read_models.py`
- `src/elbysodic/services/plotting.py`
- `src/elbysodic/web/pages/plotting/page.html`
- `src/elbysodic/web/static/elbysodic-theme.css` only if layout needs small
  component styling
- `tests/test_forum_slice.py`

Proof:

- Hook creator sees wanted interest in the correct backstage group.
- Interested writer sees active room but not creator-only interest-management
  controls.
- Staff sees manageable wanted interest across hooks.
- Ordinary unrelated member sees empty-state discovery paths, not private
  backstage objects.

### PR 4: Notifications And Operations Alignment

Goal: make the rest of the product point at the same backstage lane.

Scope:

- Ensure `wanted_interest`, `plotting_room_created`, and
  `plotting_room_threaded` notifications route to the right surface for the
  viewer:
  - hook creator/staff: wanted detail or plotting desk
  - interested writer/participant: plotting room once it exists
  - unrelated member: no visible notification
- Add or refine Studio operations cards only if directors lack a clear daily
  path to raised hands and rooms ready for scene.
- Avoid creating a generic analytics dashboard.

Expected files:

- `src/elbysodic/services/notifications.py`
- `src/elbysodic/services/plotting.py`
- `src/elbysodic/web/pages/notifications/page.html`
- `src/elbysodic/web/pages/studio/operations/page.py`
- `src/elbysodic/web/pages/studio/operations/page.html`
- `tests/test_forum_slice.py`

Proof:

- Notification inbox does not leak private room title or source hook to
  non-participants.
- Hook creator can reach raised hands from notifications or the plotting desk.
- Interested writer can reach the room after the room exists.
- Studio operations exposes only staff-safe counts/details.

### PR 5: Docs And Contract Capture

Goal: promote the accepted backstage language after behavior is real.

Scope:

- Update `docs/product/information-hierarchy.md` with wanted backstage as a
  proven object-bound coordination lane.
- Update `docs/product/navigation-menus.md` if `/plotting` copy or sidebar
  grouping changes mental rooms.
- Update `docs/architecture/rendered-route-privacy-matrix.md` for the rendered
  privacy contract around wanted interest and plotting rooms.
- Update `plans/in-progress/wattpad-competitive-research-2026-05-09.md` to mark
  wanted hooks as the selected first backstage object.
- Add a changelog fragment only when user-visible behavior lands, not for this
  plan alone.

Proof:

- Docs distinguish current shipped behavior from future backstage expansion.
- Privacy matrix names ordinary member, interested writer, hook creator,
  casting staff, outsider, and same-user-different-community cases.

## Parity Matrix

| Contract | API/CLI | Programmatic | Protocol | Schema/Types | Docs | Examples | Tests |
|---|---|---|---|---|---|---|---|
| Wanted interest visibility | N/A | `read_wanted_ad()` and read models hide private fields by viewer | Existing POST intents unchanged | Prefer no schema change; add typed visibility fields | Privacy matrix after implementation | Seed personas should still cover creator/interested/outsider | Rendered privacy tests |
| Start plotting from interest | N/A | `create_plotting_room_from_wanted_interest()` remains source of truth | `intent=start_plotting_room` unchanged | Existing room source ids reused | Product docs after implementation | Existing demo wanted hook should exercise it | Existing tests plus room-link assertions |
| Backstage stage labels | N/A | Derived from interest + room status | Existing routes unchanged | Avoid new stored statuses in first slice | Navigation/info hierarchy if labels ship | N/A | Rendered assertions for labels/actions |
| Room-to-scene handoff | N/A | `create_thread_from_plotting_room()` remains source of truth | Existing plotting POST intent unchanged | Existing target thread link reused | Privacy matrix if linked from wanted detail | N/A | Existing scene handoff tests plus wanted-detail backlink |
| Notifications | N/A | Notification read model filters inaccessible rooms | Existing notification open intent unchanged | Existing notification columns reused | Privacy matrix | N/A | Non-participant notification leakage regression |

## Sequencing Recommendation

1. Land PR 1 first. Privacy-safe read models are the foundation.
2. Land PR 2 next. It gives the wanted detail page the actual backstage
   handoff.
3. Land PR 3 after the detail page works, so `/plotting` reflects real stages
   rather than inventing another source of truth.
4. Land PR 4 only after the primary lane is clear.
5. Land PR 5 with whichever behavior PR first makes backstage a committed
   product concept.

## Not Now

- `/backstage` route or global navigation rename.
- Global social feed.
- Paragraph-level scene comments.
- General-purpose DMs.
- Public writer productivity scores.
- New stored interest statuses before the read-model derivation proves
  insufficient.
- New tables for generic backstage notes before wanted/plotting privacy is
  proven.

## Open Questions

- Should public wanted detail show exact interested-face names or only counts
  once privacy-safe backstage rows exist?
- Should prospective interest notes be private to hook creator/staff by default
  or explicitly marked public by the interested writer?
- Should hook owners be able to decline interest, or should non-action simply
  leave it waiting?
- Should `reserved` remain separate from plotting, or can a reserved wanted
  still have an active plotting room?
- Should scene start automatically mark a wanted hook `filled`, or should that
  stay a director-controlled lifecycle decision?

## Required Checks

For implementation PRs:

- `uv run ruff check .`
- `uv run ruff format . --check`
- `uv run pytest tests/test_forum_slice.py -q --tb=short`
- `uv run ty check src/elbysodic/ tests/`
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`

Run the full `uv run pytest -q --tb=short` gate when a PR touches shared
notifications, route registration, policies, schema, or transaction behavior.

## Steward Notes

- Product/docs: accepted. The plan preserves PBP-native language and keeps
  backstage object-bound instead of generic-social.
- Service/storage: accepted with caution. First slices should derive stages
  from existing wanted interest and plotting room state before adding schema.
- Web/UI: accepted. Keep `/plotting` route stable for now and improve labels,
  grouping, and direct links.
- Security/privacy: accepted as the first implementation dependency. Rendered
  privacy proof must land with any change that exposes interest notes, room
  links, notifications, or staff/creator controls.
- Tests: accepted. Existing wanted/plotting tests are a strong base, but need
  explicit unrelated-member and same-user-different-community assertions for
  wanted interest notes and room backlinks.
