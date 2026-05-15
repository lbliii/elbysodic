# Scene Context Reader Saga

Status: active implementation plan; static prototype accepted, codebase
analysis complete, Epics 1-5, Epic 6 Phase A, and mock-convergence pass
implemented locally
Owner: Product design, web, service, privacy, and test stewardship
Created: 2026-05-15
Last updated: 2026-05-15
Review by: 2026-06-05
Closure criteria: the static scene-context reader prototype is either
implemented through merged PR-sized slices or superseded by a narrower reader
plan; the live thread reader has a service-owned scene context contract,
desktop split-pane and mobile drawer behavior, privacy-tested location/context
rows, browser QA, and preserved post customization semantics.

## Strategy Anchor

This saga strengthens:

- Writer Network: a writer can read a scene, know the active face, understand
  what they owe next, and continue through location or Desk context without
  losing the prose.
- Realm Studio: directors get richer location/event/media staging without
  turning the scene reader into chat or generic SaaS chrome.
- Continuity Graph foundation: grounding context creates a future place for
  source-linked canon and event provenance, while explicitly deferring
  automatic canon summaries.

The work is deliberately not a Discord/Slack replacement. It borrows layered
context and drawers while preserving PBP scene, face, roster, location,
wanted, watching, waiting, caught-up, and needs-reply language.

## Source Artifacts

- Static prototype:
  `design/static-scene-context-mock.html`
- Prototype notes:
  `design/static-scene-context-mock-notes.md`
- Relevant product/design guidance:
  `docs/product/information-hierarchy.md`,
  `docs/product/control-topology.md`,
  `docs/product/navigation-menus.md`,
  `design/image-dimensions.md`
- Current implementation surfaces:
  `src/elbysodic/web/pages/boards/{board_slug}/threads/{thread_slug}/page.py`,
  `src/elbysodic/web/pages/boards/{board_slug}/threads/{thread_slug}/page.html`,
  `src/elbysodic/web/pages/_components/posts.html`,
  `src/elbysodic/services/threads.py`,
  `src/elbysodic/services/read_models.py`,
  `src/elbysodic/web/static/elbysodic-theme/42-threads-queues.css`,
  `src/elbysodic/web/static/elbysodic-theme/45-posts-scenes.css`

## Current Baseline

The live code already supports more of the desired direction than the static
mock initially implied:

- cinematic thread stage with runtime, cast, credits, latest beat, and actions
- board/location images and media treatments
- character `poster_url`, `avatar_url`, accent color, summary, and tagline
- post profile variants: `bio`, `poster`, `dock`, and `crest`
- post accent, border, title, and density customization
- alternating post profile rails on desktop
- current event bridge
- adjacent scene navigation
- previous unreplied and next unread navigation
- active-face composer with safe markup preview/draft behavior
- watch/read/caught-up semantics

The biggest live gap is not character art. The live gap is the
scene-in-context shell:

- location scene lane beside or drawer-accessible from the reader
- grounding inspector for place, present faces, event, visibility, and future
  source-linked context
- service-owned read model that assembles these pieces without template-side
  privacy decisions
- mobile/tablet behavior that keeps the reader first and moves auxiliary
  context into drawers

## Accepted Product Shape

Desktop:

```text
community shell -> location scene lane -> scene reader -> optional grounding inspector
```

Tablet/mobile:

```text
community shell -> scene reader
                 -> Scenes here drawer
                 -> Scene context drawer
```

Reader hierarchy:

1. Scene identity and optional inherited media.
2. Active face and turn state.
3. Long-form prose with face-forward post rails.
4. Context as optional support, not persistent noise.
5. Continuation into `Next unread`, `Scenes here`, or Desk obligations.

## Saga Epics

### Epic 1: Scene Context Surface Contract

Goal: create the route-facing service/read-model contract that templates can
render without deciding privacy, ranking, or lifecycle state.

Tasks:

- [x] Add read models in `src/elbysodic/services/read_models.py`:
  `SceneContextView`, `SceneLocationLane`, `SceneLocationLaneItem`,
  `SceneGroundingPanel`, and small supporting value objects as needed.
- [x] Add `read_scene_context(repo, viewer, board, thread)` in
  `src/elbysodic/services/threads.py`, wrapping the existing `ThreadView`.
- [x] Add `AppServices.read_scene_context(board_slug, thread_slug)` in
  `src/elbysodic/services/forum.py`.
- [x] Update the thread route to call `read_scene_context` once and pass the
  wrapper to the template.
- [x] Keep existing `services.read_thread()` available until callers are
  migrated or intentionally preserved.
- [x] Move `parent_board` and `current_event_for_thread` assembly into the
  contract or make their continued route-level use explicit.
- [x] Add focused service tests for the new read model shape.

Required proof:

- Service test proves the contract includes thread, board, parent/location,
  participants, lane rows, grounding data, and current event when available.
- Existing thread route tests continue to pass.
- No route handler or template performs visibility filtering for lane/context
  rows.

Local proof recorded 2026-05-15:

- `uv run pytest tests/test_forum_slice.py -q --tb=short -k 'scene_context_contract or seeded_boards_and_thread or tenant_prefixed_thread_routes_scope_composer_redirects'`
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`
- `uv run ruff check src/elbysodic/services/read_models.py src/elbysodic/services/threads.py src/elbysodic/services/forum.py src/elbysodic/services/__init__.py 'src/elbysodic/web/pages/boards/{board_slug}/threads/{thread_slug}/page.py' tests/test_forum_slice.py`
- `uv run ruff format src/elbysodic/services/read_models.py src/elbysodic/services/threads.py src/elbysodic/services/forum.py src/elbysodic/services/__init__.py 'src/elbysodic/web/pages/boards/{board_slug}/threads/{thread_slug}/page.py' tests/test_forum_slice.py --check`
- `uv run ty check src/elbysodic/services/read_models.py src/elbysodic/services/threads.py src/elbysodic/services/forum.py 'src/elbysodic/web/pages/boards/{board_slug}/threads/{thread_slug}/page.py' tests/test_forum_slice.py`
- `uv run ruff check .`
- `uv run ruff format . --check`
- `uv run ty check src/elbysodic/ tests/`
- `uv run pytest tests/test_forum_slice.py -q --tb=short`

Collateral:

- Update this plan with actual read model names if implementation diverges.
- Update `docs/architecture/surface-contract-architecture.md` only if the
  pattern changes beyond existing doctrine.

### Epic 2: Location Scene Lane

Goal: make nearby location context available while reading a scene, without
requiring a back-navigation loop to the board page.

Tasks:

- [x] Build lane rows from the current board's direct visible threads.
- [x] Include current scene marker, title, summary/snippet, updated label,
  reply count, participants, and state badges.
- [x] Include writer-specific badges where available: `needs reply`, `waiting`,
  `new replies`, `mine`, and `watching`.
- [x] Keep child/sibling location rows out of the first slice unless the
  service contract can prove they remain privacy-safe and not noisy.
- [x] Reuse or adapt `ThreadSummary` and thread card helper logic where
  practical instead of creating a second one-off scene row model.
- [x] Add batching for any watched-state or read-state lookups. Do not add
  per-row queries.
- [x] Render the lane as a persistent desktop pane and as a `Scenes here`
  drawer below the desktop breakpoint.

Required proof:

- Rendered test: lane shows only visible same-board scenes.
- Rendered test: lane marks current scene.
- Rendered test: private board/thread names do not leak to unauthorized
  viewers.
- Query-budget test if lane assembly touches watched/read state across many
  rows.
- Browser QA: desktop split, tablet drawer, mobile drawer.

Local proof recorded 2026-05-15:

- `uv run pytest tests/test_forum_slice.py -q --tb=short -k 'scene_context_contract or thread_page_renders_location_scene_lane or scene_lane_keeps_private_board_threads_out_of_visible_scene_context or scene_lane_watch_state_uses_batched_lookup or thread_watch_toggle_controls_thread_notifications'`
- Browser smoke against a seeded local app route
  `/c/x-men-apocalypse/boards/danger-room/threads/sentinel-drill`: desktop
  lane visible at 1440px, tablet/mobile drawer active at 820px and 390px, no
  horizontal overflow.

Notes:

- This slice intentionally keeps the lane to same-board direct scenes. It does
  not pull child or sibling location rows into the reader yet.
- The lane switches to drawer treatment below `64rem`; the existing thread
  stage and post-card mobile compaction still use their narrower breakpoint.
- The rendered privacy proof covers private board context. Thread status
  `private` remains the existing scene status label, not a newly changed
  visibility boundary.

Collateral:

- Add shared component notes if lane markup graduates into
  `src/elbysodic/web/pages/_components/`.

### Epic 3: Grounding Inspector

Goal: provide optional scene grounding without making the prose reader feel
like an admin cockpit.

First-slice context:

- board/location identity
- parent location if present
- board image or inherited visual identity
- present faces
- scene status, posting mode, runtime, reply count
- active/current event bridge
- visibility label: public/member/private/staff-manageable as appropriate
- watch state and active-face obligation state

Tasks:

- [x] Add grounding read model fields owned by `read_scene_context`.
- [x] Render the inspector as a right pane on wide desktop.
- [x] Render the inspector as a `Scene context` drawer on tablet/mobile.
- [x] Keep staff controls in the existing management disclosure unless the
  inspector is explicitly in staff mode.
- [x] Add "visibility" copy from service-owned state, not template role checks.
- [x] Add affordance hooks for future wanted/plotter/canon links, but do not
  render fake relationships.

Required proof:

- Rendered tests for ordinary member, scene owner, staff, and unauthorized
  states.
- Test that staff-only controls/notes do not appear for ordinary members.
- Browser QA proving the drawer does not cover initial reader content or
  composer controls.

Local proof recorded 2026-05-15:

- `uv run pytest tests/test_forum_slice.py -q --tb=short -k 'scene_context_contract or thread_page_renders_location_scene_lane or scene_lane_keeps_private_board_threads_out_of_visible_scene_context or scene_lane_watch_state_uses_batched_lookup or thread_page_renders_scene_grounding_for_owner or scene_grounding_for_ordinary_member_hides_staff_management_copy or scene_grounding_for_staff_uses_service_owned_visibility_copy or thread_watch_toggle_controls_thread_notifications'`
- Browser smoke against seeded local app route
  `/c/x-men-apocalypse/boards/danger-room/threads/sentinel-drill`: desktop
  lane plus inspector visible at 1440px, tablet/mobile drawers active at 820px
  and 390px, no horizontal overflow.

Notes:

- The inspector renders future linked story-object affordance copy only; it
  does not invent wanted, plotter, or canon relationships.
- Staff controls remain in the existing management disclosure. The inspector
  only reports service-owned visibility copy.

Collateral:

- Update rendered-route privacy matrix if the inspector introduces new visible
  fields not already covered by thread pages.

### Epic 4: Reader Layout And Responsive Shell

Goal: move the live thread page from centered page sections to a scene-context
reader shell while preserving server-rendered Chirp behavior.

Tasks:

- [x] Create shared template components for:
  `scene_context_shell`, `location_scene_lane`, `scene_grounding_inspector`,
  and drawer toggles if repeated enough.
- [x] Keep route breadcrumbs and primary scene actions clear in the reader.
- [x] Preserve current management disclosures, composer behavior, CSRF, HTMX
  behavior, and idempotency.
- [x] Preserve previous/next scene and previous-unreplied/next-unread
  continuation semantics.
- [x] Add minimal progressive enhancement for drawer open/close state.
- [x] Ensure drawer controls are keyboard reachable and named.
- [x] Ensure mobile starts with the scene reader, not the lane or composer.
- [x] Avoid turning the whole page into an SPA.

Required proof:

- `create_app(...).check()` passes.
- Rendered tests assert semantic landmarks and controls:
  `Scenes here`, `Scene context`, `Reply as <face>`, `Next unread`.
- Browser QA at desktop, tablet, and mobile viewports.

Local proof recorded 2026-05-15:

- `uv run pytest tests/test_forum_slice.py -q --tb=short -k 'scene_context_shell or thread_page_renders_location_scene_lane or thread_page_renders_scene_grounding_for_owner or scene_grounding_for_ordinary_member_hides_staff_management_copy or scene_grounding_for_staff_uses_service_owned_visibility_copy or thread_view_hides_unspecified_scene_metadata'`
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check(warnings_as_errors=True)"`
- `uv run ruff check .`
- `uv run ruff format . --check`
- `uv run ty check src/elbysodic/ tests/`
- `uv run pytest tests/test_forum_slice.py -q --tb=short`
- `uv run pytest -q --tb=short`
- Browser smoke against seeded local app route
  `/c/x-men-apocalypse/boards/danger-room/threads/sentinel-drill`: desktop
  lane plus inspector visible at 1440px, tablet/mobile drawer triggers active
  at 820px and 390px, drawer contents verified, no horizontal overflow.

Notes:

- Scene context markup now lives in
  `src/elbysodic/web/pages/_components/scene_context.html`.
- The thread page remains server-rendered and keeps existing command forms and
  continuation controls inside the reader slot.
- Browser screenshots from the local smoke are in
  `/private/tmp/elbysodic-scene-context-smoke/`.

Collateral:

- Changelog fragment for user-visible reader layout change.
- Design QA note if substantial responsive behavior is introduced.

### Epic 5: Editorial Post Reading Polish

Goal: bring the strongest parts of the static mock into the live post system
without breaking existing post customization.

Tasks:

- [x] Audit existing `poster`, `dock`, `crest`, accent, border, title, and
  density CSS against the static mock.
- [x] Decide whether "poster-wrap" is a new `post_profile_variant`, a
  `post_density="dramatic"` behavior, or a realm-level reader mode.
- [x] Prototype poster-wrap in live CSS behind an explicit class, not as a
  default replacement for all posts.
- [x] Preserve existing alternating rails and mobile fallback.
- [x] Confirm existing quiet post permalinks remain sufficient after the
  layout change.
- [x] Consider drop caps and beat notes as theme/post-style aware polish only;
  do not hardcode them across every post.
- [x] Keep writer-entered formatting authoritative. Do not auto-bold dialogue.

Required proof:

- Rendered thread still includes post anchors, edit links where allowed,
  poster rail variants, and writer/member links.
- Browser QA for long posts, short posts, poster images, no poster image, and
  mobile widths.
- Markup tests continue to prove safe rendered post output.

Local proof recorded 2026-05-15:

- `uv run pytest tests/test_forum_slice.py -q --tb=short -k 'editorial_poster_wrap or post_shell_inherits_identity_accent_from_facet_group or scene_context_shell_preserves_reader_landmarks_and_controls'`
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check(warnings_as_errors=True)"`
- `uv run ruff check .`
- `uv run ruff format . --check`
- `uv run ty check src/elbysodic/ tests/`
- `uv run pytest tests/test_forum_slice.py -q --tb=short`
- `uv run pytest -q --tb=short`
- Browser smoke against seeded local app route
  `/c/x-men-apocalypse/boards/danger-room/threads/moonlight-skirmish`:
  desktop poster rails floated and alternated around prose at 1440px, poster
  media used a 2:3 ratio, tablet/mobile rails did not float at 820px and
  390px, and all checked widths avoided horizontal overflow.

Notes:

- `poster-wrap` is implemented as the explicit reader mode
  `data-elbysodic-post-reader-mode="poster-wrap"` plus
  `elbysodic-post-list--editorial-wrap`, not as a new schema-backed
  `post_profile_variant`.
- Existing post profile variants, density, accent, border, title, post anchors,
  writer/member links, and edit links remain rendered.
- Automatic dialogue bolding remains a not-now item; writer-authored markup
  stays authoritative.
- Browser screenshots from the local smoke are in
  `/private/tmp/elbysodic-editorial-post-smoke/`.

Collateral:

- Update `design/component-inventory.md` or post-style docs if a new
  `poster-wrap` variant is accepted.

### Epic 6: Optional Scene Media Contract

Goal: support Netflix/Apple TV-like scene media without forcing schema work
into the first reader slice.

Phase A, no schema:

- [x] Let the reader use existing board/location image as inherited scene
  media.
- [x] Let current event material provide context only if already available and
  public/member-safe.
- [x] Use existing `design/image-dimensions.md` ratios:
  `16:9` for thread-stage media and `21:9` only for broad stage contexts.

Phase B, schema decision gate:

- [ ] Stop and ask before adding thread-level media fields.
- [ ] If accepted, add thread media fields such as `image_url`, `image_alt`,
  `image_focal_point`, `image_overlay`, and maybe `image_source_kind`.
- [ ] Add repository, migration, Studio/editor forms, seed data, blueprint
  import/export rules if thread media becomes a public contract.
- [ ] Add privacy and theme-safety tests for any new media inputs.

Required proof:

- Phase A: rendered tests prove inherited media does not expose private boards.
- Phase B: migration/repository/service/web tests plus app check and docs.

Local proof recorded 2026-05-15:

- `uv run pytest tests/test_forum_slice.py -q --tb=short -k 'scene_media_band or scene_context_contract or thread_page_renders_inherited_scene_media_band or text_first_location_media'`
- `uv run ruff check .`
- `uv run ruff format . --check`
- `uv run ty check src/elbysodic/ tests/`
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check(warnings_as_errors=True)"`
- `uv run pytest tests/test_forum_slice.py -q --tb=short`
- `uv run pytest -q --tb=short`
- Browser smoke against seeded local app route
  `/c/x-men-apocalypse/boards/danger-room/threads/sentinel-drill`: desktop,
  tablet, and mobile render the inherited Xavier Institute location image for
  the Danger Room scene, preserve alt text, and avoid horizontal overflow.

Notes:

- Phase A uses a service-owned `SceneMediaBand` selected from the current
  board image or a visible parent board image. Text-first board media
  treatments are intentionally suppressed.
- Current event material appears as contextual chip text only when already
  present in the scene context. No event image or thread override is invented.
- Phase B remains gated. Adding thread-specific media fields would require a
  schema/repository/editor/Blueprint decision and human approval.
- Browser screenshots from the local smoke are in
  `/private/tmp/elbysodic-scene-media-smoke/`.

Collateral:

- Update `docs/product/appearance-studio.md` only if directors gain new media
  controls.
- Changelog if thread media becomes user-facing.

### Epic 7: Writer Activity Drawer

Goal: bring the static mock's `What needs you` drawer into the reader after the
core scene context shell is stable.

Tasks:

- [ ] Reuse `MyThreadsDashboard` / `ThreadObligationItem` rather than creating
  a notification-like duplicate.
- [ ] Render only a small set of current obligations:
  `Needs reply`, `Waiting`, `Watching`, `Caught up`, `Reserve expiring`, and
  `Claim reviewed` only when backed by real services.
- [ ] Keep the drawer member-only and active-membership scoped.
- [ ] Keep notifications in Desk as the canonical full history.
- [ ] Add no drawer state to signed-out/public thread previews.

Required proof:

- Rendered privacy tests for signed-out, inactive, ordinary member, and
  same-user-different-community states.
- Query-budget proof if obligation rows are assembled on every thread page.

Collateral:

- Coordinate with existing Desk and notification docs before introducing new
  permanent navigation.

### Epic 8: Continuity/Wanted/Plotter Grounding

Goal: later enrich the inspector with real story-object relationships after
the core reader is trusted.

Tasks:

- [ ] Add linked wanted hook and plotting room context only from explicit
  relationships already enforced by services.
- [ ] Add current event links when public/member visibility is proven.
- [ ] Add canon/source context only after Continuity Graph manual provenance
  and review workflows exist.
- [ ] Keep provenance labels visible: proposed, reviewed, staff-only, public,
  member-visible.
- [ ] Avoid generated summaries until consent, provenance, privacy, and review
  gates are implemented.

Required proof:

- Service tests for each relationship source.
- Rendered privacy tests for public, member, involved writer, staff, and
  cross-tenant attempts.

Collateral:

- Likely updates to Continuity Graph docs, wanted/backstage docs, and privacy
  matrix when this moves out of not-now.

## Dependency Order

1. Epic 1: scene context contract.
2. Epic 2: location lane.
3. Epic 3: grounding inspector.
4. Epic 4: responsive shell integration.
5. Epic 5: editorial post polish.
6. Epic 6 Phase A: inherited scene media.
7. Epic 7: writer activity drawer.
8. Epic 6 Phase B and Epic 8 only after explicit decision gates.

The first PR should include Epics 1-4 at a minimal level and no schema change.
Epic 5 can be a second PR because it touches post customization and browser QA
more heavily. Epic 6 Phase B is a schema/data-model change and requires human
check-in before implementation.

## Risks

- Privacy leakage through lane rows, counts, drawer labels, private board names,
  staff controls, or active-face state.
- Query growth if thread/read/watch state is assembled per row.
- Mobile regressions where drawers, sticky composer, or poster rails cover the
  reader.
- Post customization drift if the editorial mock replaces live variants rather
  than extending them.
- Product drift toward Slack/Discord chat urgency instead of PBP prose rhythm.
- Scene media scope creep into unsafe raw CSS, external URLs, or unreviewed
  community customization.

## Not Now

- Automatic dialogue bolding or automatic post source transformations.
- Thread-specific media schema before the no-schema scene context slice lands.
- Generated beat notes, generated canon, or AI-assisted continuity summaries.
- Full Discord-style presence or real-time pressure indicators.
- Nested Slack-style story replies.
- Canon/wanted/plotter inspector links without explicit service-owned
  relationships.

## Proof Matrix

| Contract | Service | Web | Privacy | Browser QA | Docs/Plans |
|---|---|---|---|---|---|
| Scene context contract | read-model tests | route render test | member/staff/private assertions | not required until layout | this plan |
| Location lane | batched lane tests | lane rows render | no private/cross-tenant rows | desktop/tablet/mobile | component notes if promoted |
| Grounding inspector | grounding read model tests | drawer/pane render | no staff/private leaks | drawer coverage | privacy matrix if new fields |
| Reader shell | existing command tests pass | landmarks/actions render | active-face scoping | required | changelog |
| Editorial posts | post-style tests if variant changes | post anchors/rendering | edit links by capability | long/short/mobile/poster fallback | design docs if accepted |
| Scene media | inherited media tests | media fallback render | no private board media leak | media crop coverage | appearance docs only if controls |

## Closure Notes

When this saga closes, preserve:

- the final accepted reader contract
- browser QA artifact paths
- any deferred schema/media decisions
- any minority design findings about poster-wrap readability or mobile drawers
- links to merged PRs or replacement plans
