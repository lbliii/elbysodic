# Community Landing Design-System Translation

Status: implementation pass landed on `codex/community-gateway-plan`; final
merge/review pending
Owner: Product design, Chirp/web, service, privacy, tests, and docs stewardship
Created: 2026-05-15
Last updated: 2026-05-18
Review by: 2026-05-29
Closure criteria: the community landing V2 prototype is translated into
service-owned public/member/applicant read models, Chirp-composed Elbysodic
components, theme-layer CSS, privacy-tested rendered routes, desktop/mobile
browser QA, and docs/checklist updates; or the prototype is explicitly
superseded by a narrower gateway plan.

## 2026-05-16 Implementation Pass

Branch: `codex/community-gateway-plan`

Completed in task commits:

- Hardened `RealmGatewayView` with hero, action, signal, scene-hub emphasis,
  wanted preview, and continuation contracts.
- Replaced the early card-grid community home with
  `_components/realm_gateway.html`; signed-in homes now keep the gateway and
  continuation lane rather than also rendering the old board/activity index.
- Added tokenized theme CSS across page, media, board/place, and wanted layers
  without copying prototype CSS.
- Rendered open wanted hooks as public first-face previews from existing
  public wanted data.
- Added member/faceless continuation lanes from service-owned identity state.
- Updated rendered QA notes, privacy matrix coverage, and changelog.

Second wave:

- Routed applicant continuation through writer activation, including existing
  draft first-face applications.
- Added public-safe open scene previews from existing public boards and
  threads.
- Ranked scene hubs by gateway emphasis and public thread activity before the
  four-card limit.
- Added rendered fallback proof for no-media/no-wanted public gateways.
- Reran the premise browser profile with wave-two screenshots.

Content cleanup:

- Removed generic explanatory section summaries and placeholder signal copy
  from the rendered gateway.
- Derived signal and entry-path copy from current event, premise, guidebook,
  wanted, and scene-hub names.
- Added rendered regression coverage so original-premise gateways do not
  reintroduce the known boilerplate phrases.
- Hid legacy signed-in home activity/index rows when a gateway exists; those
  workflows live in Desk, Locations, and board routes.

Curated gateway follow-up:

- Added tenant-scoped `community_gateway_slots` storage for curated scene hubs,
  wanted hooks, and guidebook materials.
- Rendered curated gateway slots ahead of derived fallback content, while
  omitting stale private boards, closed wanted hooks, and draft materials.
- Added Studio gateway curation so directors can select, order, remove, and
  preview public home-page slots without raw layout controls or generated copy.
- Replaced the remaining original-premise demo "Wanted thread start" scaffold
  with board/face-specific first-scene language.
- Removed the rendered public "Play readiness" signal band after visitor
  feedback showed the counts and status copy were not useful for deciding what
  to read or click next.
- Simplified scene-hub cards so the section context carries the type; cards now
  show the place and its useful hook instead of repeating hub labels and thread
  counts.

Proof captured so far:

- `uv run ruff check src/elbysodic/services/read_models.py src/elbysodic/services/forum.py src/elbysodic/web/pages/page.py tests/test_forum_slice.py`
- `uv run pytest tests/test_forum_slice.py tests/test_web_security.py -q --tb=short -k 'original_premise_gateways or forum_pages_render_seeded_boards_and_thread or anonymous or public_realm_gateway_contract'`
- `uv run pytest tests/test_forum_slice.py::test_writer_desk_keeps_first_face_application_active tests/test_forum_slice.py::test_public_realm_gateway_scene_previews_hide_private_threads tests/test_forum_slice.py::test_public_realm_gateway_ranks_active_scene_hubs_before_limit tests/test_forum_slice.py::test_public_realm_gateway_contract_uses_fallbacks_and_denies_backstage -q --tb=short`
- `uv run pytest tests/test_forum_slice.py::test_original_premise_gateways_surface_premise_entry_and_scene_hubs tests/test_forum_slice.py::test_forum_pages_render_seeded_boards_and_thread tests/test_forum_slice.py::test_rendered_route_query_budgets_are_tracked -q --tb=short`
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`
- `uv run python scripts/browser_qa.py --base-url http://127.0.0.1:8003 --profile premise --artifact-dir /private/tmp/elbysodic-gateway-premise-qa`
- `uv run python /private/tmp/run_elbysodic_gateway_qa.py`
- `uv run ruff check .`
- `uv run ruff format . --check`
- `uv run ty check src/elbysodic/ tests/`
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check(warnings_as_errors=True)"`
- `make changelog-check`
- `uv run pytest -q --tb=short`
- `uv run pytest tests/test_tenant_repository.py -q --tb=short`
- `uv run pytest tests/test_forum_slice.py -q --tb=short -k "gateway_curation or realm_gateway or gateway"`

Remaining before merge:

- Review branch diff and open PR.

## Purpose

Translate `design/static-community-landing-v2-mock.html` into the real
Elbysodic design system and Chirp-UI layer without copying prototype CSS into
production, after applying the premise-archetype stress pass in
`design/community-landing-archetype-stress-pass.md`.

The target route is `/c/{community_slug}`, with `/c/x-men-apocalypse` as the
seed proof. The design goal is a public premise gateway with playable entry
paths and programmable atmosphere:

- one active event
- no active event
- multiple active events
- media and no-media fallback
- visitor, applicant, and member states
- location bento emphasis for important or popular scene hubs
- archetype-flexible variants for no-event social play, gated-lore mystery,
  and institution/status/scarcity pressure

This strengthens:

- Realm Studio: directors can express realm atmosphere, featured pressure, and
  launch/access posture safely.
- Writer Network: visitors, applicants, and members see playable openings,
  wanted hooks, active face continuation, and first writing paths.
- Continuity Graph foundation: the gateway creates a future slot for
  source-linked event/material context without publishing unsourced canon.

## Source Artifacts

- Prototype:
  `design/static-community-landing-v2-mock.html`
- Archetype stress mock:
  `design/static-community-landing-v2-archetype-mock.html`
- Prototype notes:
  `design/static-community-landing-v2-notes.md`
- Composition doctrine:
  `design/composition-bible.md`
- Experience synthesis:
  `docs/product/experience-direction.md`
- Current route:
  `src/elbysodic/web/pages/page.py`
- Current template:
  `src/elbysodic/web/pages/page.html`
- Current CSS owners:
  `src/elbysodic/web/static/elbysodic-theme/30-page-patterns.css`,
  `35-media-patterns.css`,
  `41-boards-places.css`,
  `47-network-catalog.css`
- Current public services:
  `AppServices.public_studio_program()`,
  `AppServices.public_world_hub()`,
  `AppServices.public_wanted_ads()`
- Archetype stress pass:
  `design/community-landing-archetype-stress-pass.md`
- Accepted premise-shape doctrine:
  `docs/product/community-shapes.md`

## Product Decision

`/c/{community_slug}` should become a premise gateway, not a forum index and
not a duplicate of `/world`.

The gateway owns:

- realm identity, premise engine, and access posture
- current atmosphere source: active event, featured premise/material, season,
  director pulse, social pressure, public mystery, institution pressure,
  scarcity, or standing realm tension
- first writing path for visitors/applicants
- public-safe playable scene/location/wanted previews
- member continuation lane when signed in

`/world` remains the guidebook/material room. `Locations`, `Wanted`, `Desk`,
and `Studio` remain scoped rooms in the shell.

## Curated Gateway Slot Contract

Gateway content should be director-curatable after the privacy-safe derived
gateway is stable. Curation is a small ordering contract, not a layout builder.

Slot types:

- `scene_hub`: targets a public board that can function as a scene hub.
- `wanted_hook`: targets an open wanted hook.
- `guidebook_material`: targets a published material.
- `public_scene`: deferred until the product has an explicit public-scene
  curation contract; do not infer it from private/staff/thread state.

Storage contract:

- Every slot stores `community_id`, `slot_type`, `target_id`, `position`, an
  optional director-facing `label`, and timestamps.
- `community_id` is part of every repository lookup, write, and uniqueness
  rule.
- A community can curate several slot types without affecting the order of
  unrelated gateway sections.
- Curation never stores permission decisions; services re-check target safety
  before rendering.

Rendering contract:

- Curated safe targets render first, in slot order.
- Derived content fills any remaining gateway capacity.
- Unsafe curated targets are silently omitted and do not block fallback:
  private boards, archived wanted hooks, draft/unpublished materials, missing
  rows, and cross-community targets never render.
- Public visitors still see only published/public-safe gateway material.
- Signed-in members may see only the same curated public gateway plus their
  viewer-scoped continuation lane.

Studio contract:

- Director controls may select, reorder, and remove gateway slots.
- The Studio surface lists only eligible public boards, open wanted hooks, and
  published materials for the current community.
- The first implementation should stay operational and compact: no masonry,
  raw CSS, custom layout controls, or AI-generated public copy.

Proof contract:

- Fresh schema and upgraded schema include the same slot table and indexes.
- Repository tests prove tenant-scoped create/list/delete behavior and
  cross-community target rejection.
- Service tests prove curated order, derived fallback, and unsafe target
  omission for each slot type.
- Rendered tests prove public gateway output does not leak private boards,
  archived wanted hooks, draft materials, Desk state, or active-face state.

## Non-Negotiables

- Do not copy prototype CSS wholesale.
- Use Chirp primitives for generic buttons, badges, surfaces, rows, fields,
  stacks, clusters, and responsive structure where possible.
- Keep Elbysodic wrappers only where the shape has PBP meaning.
- Public visitors must never see membership, active-face, Desk, staff,
  application-review, private board, private scene, or private wanted state.
- B-24 is example seed content. The production design must support no event,
  one event, or multiple events without changing templates.
- Event/crisis pressure is one valid atmosphere variant, not the base
  organizing principle for every community shape.
- Wanted hooks are entry paths inside premise communities, not top-level
  community archetypes.
- No route migration away from `/c/{community_slug}` in this plan.
- No new runtime dependency.
- No raw CSS, script, external font, or layout-builder controls for directors.

## Proposed Read Models

Add route-facing models in `src/elbysodic/services/read_models.py`:

- `RealmGatewayView`
- `RealmGatewayPremise`
- `RealmGatewayAtmosphere`
- `RealmGatewayPulseItem`
- `RealmGatewayGuideItem`
- `RealmGatewayScenePreview`
- `RealmGatewayWantedPreview`
- `RealmGatewayLocationCard`
- `RealmGatewayEntryStep`
- `RealmGatewayContinuation`

Suggested fields:

- audience mode: `public`, `applicant`, `member`, `staff`
- premise archetype, play engine, lore aperture, roster posture, catalog pitch,
  and onboarding pitch from public discovery profile fields where available
- access posture: public preview, request access, invite only, applications open
- atmosphere mode: `none`, `single`, `multiple`
- atmosphere source type: event, premise, material, season, director pulse,
  social pressure, mystery, institution, scarcity, location, or fallback
- public-safe status labels and copy
- location emphasis: normal, featured, hot now, event-linked, high activity,
  director-pinned
- public-safe counts only after service privacy checks
- optional member continuation with active face and Desk-safe rows
- optional applicant continuation with application-safe rows

The route handler should call one service method and render the template. The
template should not choose what is public-safe.

## Component Translation

Promote these as Elbysodic components composed from Chirp primitives:

| Prototype Shape | Production Candidate | Likely Home | Chirp Foundation |
| --- | --- | --- | --- |
| realm gateway hero | `realm_gateway_hero` | `_components/realm_gateway.html` | surface, button, badge, cluster |
| status strip | `realm_signal_strip` | `_components/realm_gateway.html` or `_components/ui.html` | badge/chip |
| realm pulse | `realm_pulse` | `_components/realm_gateway.html` | stat or metric vocabulary |
| premise summary | `realm_premise_gateway` | `_components/realm_gateway.html` | surface, badge, description/list |
| atmosphere feed | `realm_atmosphere_panel` | `_components/realm_gateway.html` | surface + description/list |
| guide rows/cards | `realm_guide_preview` | `_components/realm_gateway.html` | surface/card + preview row |
| playable scene row | `public_scene_preview_row` | `_components/thread_summary.html` or gateway component | preview row |
| wanted casting card | `public_wanted_gateway_card` | `_components/wanted.html` | card + badge |
| location bento | `location_bento_grid` | `_components/boards.html` | card/surface + media pattern |
| entry path | `realm_entry_path` | `_components/realm_gateway.html` | ordered rows/steps |
| member continuation | `realm_continuation_lane` | `_components/realm_gateway.html` or vocabulary | lane preview |

Avoid a large generic "bento" abstraction. The product concept is a scene-hub
or location emphasis field, not arbitrary designer-controlled masonry. Some
archetypes will express scene hubs as businesses, institutions, houses,
factions, stations, studios, or courts rather than literal geographic places.

## CSS Translation

Use existing CSS ownership:

- `30-page-patterns.css`: realm gateway section rhythm, pulse, entry path.
- `35-media-patterns.css`: reusable media frame/fallback/overlay mechanics if
  they repeat across gateway, Network, boards, and materials.
- `41-boards-places.css`: location bento cards and board/location-specific
  emphasis states.
- `40-pbp-components.css` or `_components/ui.html`: shared PBP signal rows if
  the status strip/pulse becomes cross-surface.
- Keep `47-network-catalog.css` separate unless a card is explicitly shared by
  Network and realm gateway through one component.

Token needs:

- atmosphere source accent
- event pressure accent
- hot-location accent
- on-media caption surface
- realm pulse border/surface
- no-media fallback texture

These should be internal theme tokens first, not Appearance Studio public
fields.

## Real Build Plan: V2.1 Gateway Translation

This is the concrete implementation plan for translating
`design/static-community-landing-v2-archetype-mock.html` into the real
server-rendered community home.

Current code state:

- `src/elbysodic/web/pages/page.py` already routes tenant-prefixed community
  homes through `public_realm_gateway()` for signed-out viewers and tries to
  attach `realm_gateway` for signed-in viewers.
- `src/elbysodic/services/read_models.py` already has
  `RealmGatewayView`, `RealmGatewayPremise`, `RealmGatewayAtmosphere`,
  `RealmGatewaySceneHub`, and `RealmGatewayEntryPath`.
- `src/elbysodic/services/forum.py` already builds a public gateway from
  discovery profiles, public guidebook material, boards, and entry paths.
- `src/elbysodic/web/pages/page.html` renders an early card-based gateway, but
  it still reads closer to an operational card grid than the V2.1 editorial
  threshold.
- `tests/test_forum_slice.py` already proves three original-premise gateways
  expose premise, entry, and scene hub signals without staff leakage.

Implementation stance:

- No schema changes in the first build. Use existing discovery profiles,
  public materials, wanted counts, boards, and threads.
- Do not copy static mock CSS. Translate the composition into named read-model
  fields, shared template components, and tokenized theme CSS.
- Build public/signed-out first, then member/applicant continuation. Public
  privacy and tenant-prefixed links are the first gate.
- Keep `/c/{community_slug}` as the route. `/world`, `/wanted`, `/locations`,
  `/claims`, `/request-access`, and application links must resolve through
  tenant-safe scoped paths.

### PR 1: Gateway Contract Hardening

Goal: make the service read model carry the V2.1 editorial decisions so the
template does not infer hierarchy, safety, or CTA priority.

Files:

- `src/elbysodic/services/read_models.py`
- `src/elbysodic/services/forum.py`
- `tests/test_forum_slice.py`
- `tests/test_web_security.py` if rendered privacy assertions are clearer
  there

Read-model additions:

- `RealmGatewayHero` or equivalent fields on `RealmGatewayView`:
  - `kicker`
  - `title`
  - `lead`
  - `now_playing_label`
  - `now_playing_copy`
  - `first_face_path`
  - `primary_action`
  - `secondary_action`
- `RealmGatewayAction`:
  - `label`
  - `href`
  - `is_external_boost_safe` or a template-safe flag for `hx-boost`
- `RealmGatewaySignalItem`:
  - `title`
  - `summary`
  - optional public-safe `value`, but do not lead the UI with numeric metrics
- Extend `RealmGatewaySceneHub`:
  - `emphasis`: `normal`, `featured`, `hot`, `atmosphere`, or `high_activity`
  - `eyebrow`
  - `summary`
  - optional `image_url`, `image_alt`, `image_treatment`
- Optional `RealmGatewayWantedPreview` only if existing wanted summaries can be
  reused safely without widening scope.

Service behavior:

- Build hero copy from `CommunityDiscoveryProfile` first:
  `premise_archetype`, `play_engine`, `lore_aperture`, `catalog_pitch`,
  `onboarding_pitch`, `roster_posture`, and `featured_event_material_id`.
- Use `RealmGatewayAtmosphere` as the `Now playing` source:
  current event first, then featured/premise/standing tension fallback.
- Select one primary action per audience:
  - public with wanted hooks: first wanted/entry action
  - public with no wanted: request access or read premise
  - applicant/member later: continuation action
- Keep the secondary action quiet, usually `Read premise` or `Open guidebook`.
- Build signal items as editorial play-readiness labels:
  open connection hooks, scene hubs ready, claims worth checking, public
  rumors, entry angles, safety notes, career openings, reputation hooks, public
  venues, etc.
- Keep all filtering service-owned: no private boards, private threads, staff
  materials, application-review state, active-face state, unread state, or
  notification state in public gateway data.

Proof:

- Service tests for at least:
  - `harbor-society`: no-event social path, wanted/claims/social signals
  - `signal-creek`: mystery path, public rumor/private-answer boundary
  - `glasslight-circuit` or the closest industry/status seed: institution
    pressure path
  - fallback realm with no current event and minimal material
  - non-public/backstage realm denial
- Rendered privacy test proving public `/c/{slug}` omits staff/private,
  active-face, Desk, application-review, unread, and notification terms.
- Tenant-link test proving gateway links are tenant-scoped on `/c/{slug}`.

### PR 2: Component And Template Translation

Goal: replace the early card grid on `page.html` with a production
`realm_gateway` component that follows the V2.1 hierarchy.

Files:

- `src/elbysodic/web/pages/page.html`
- `src/elbysodic/web/pages/_components/realm_gateway.html` new
- `src/elbysodic/web/pages/_components/boards.html` only if scene-hub media
  helpers are shared
- `src/elbysodic/web/pages/_components/wanted.html` only if wanted previews are
  promoted

Template behavior:

- Public first viewport order:
  1. realm-owned hero lockup
  2. premise engine/kicker
  3. realm title
  4. lead/catalog pitch
  5. `Now playing`
  6. first-face path
  7. one primary CTA and one quiet secondary CTA
  8. media/caption if available
- Replace `elbysodic-world-hero__stats` public metrics with a signal band.
- Render scene hubs as playable doors, not a generic equal card grid.
- Render entry path lower on the page as reinforcement, not as the first place
  the visitor learns how to enter.
- Keep member-only location/attention/activity sections behind the signed-in
  branch until member continuation is explicitly designed.

Proof:

- Rendered tests assert semantic text for hero `Now playing`, first-face path,
  primary CTA, signal band, and scene hubs.
- Rendered tests assert absence of old public stat labels where they would
  create dashboard feel.
- App check.

### PR 3: Theme CSS And Responsive Behavior

Goal: translate the static mock's composition into tokenized production CSS
without creating a second design system.

Files:

- `src/elbysodic/web/static/elbysodic-theme/30-page-patterns.css`
- `src/elbysodic/web/static/elbysodic-theme/35-media-patterns.css` only if
  reusable media/caption behavior is needed
- `src/elbysodic/web/static/elbysodic-theme/41-boards-places.css` only if
  scene-hub cards share board/location media behavior
- `design/component-inventory.md` only if component roles change materially

CSS behavior:

- Use existing Chirp/Elbysodic tokens first.
- Keep high surface intensity on the gateway, but avoid nested glass cards.
- Replace big metric cards with compact editorial signal-band styling.
- Mobile must show realm name, premise lead, `Now playing`, first-face path,
  and primary CTA before route-directory weight.
- Collapse local chrome/inner shell on mobile so navigation does not precede
  the realm promise.
- Preserve no-media fallback and long-title resilience.

Proof:

- Browser QA desktop and mobile for:
  - public social/no-event gateway
  - public mystery gateway
  - public institution/status or frontier gateway
  - no-media fallback
  - long realm name and long wanted title fixture if available
- `scripts/browser_qa.py --profile premise` should either cover this or be
  extended to include these gateway checks.

### PR 4: Public Wanted And Entry Previews

Goal: make first-face entry feel story-native without leaking backstage or
private interest state.

Files:

- `src/elbysodic/services/read_models.py`
- `src/elbysodic/services/forum.py`
- `src/elbysodic/web/pages/_components/realm_gateway.html`
- `src/elbysodic/web/pages/_components/wanted.html` if shared card rendering is
  appropriate
- focused tests in `tests/test_forum_slice.py` and `tests/test_web_security.py`

Behavior:

- Add up to three public wanted/entry previews if existing public wanted data
  supports it cleanly.
- Prefer story invitations over counts:
  "tenant organizer who knows everyone", "researcher who heard the first
  signal", "publicist holding the contract leak".
- Do not expose wanted interest notes, plotting rooms, private creator state,
  applicant state, or staff handling state.
- If wanted previews are thin for a realm, fall back to claims/application
  guide/premise entry rows.

Proof:

- Public wanted preview tests for visible open hooks.
- Negative tests for private/backstage wanted interest and plotting room data.
- Rendered tests for realms with and without wanted hooks.

### PR 5: Member And Applicant Continuation

Goal: add audience-aware continuation after the public gateway works.

Files:

- `src/elbysodic/services/read_models.py`
- `src/elbysodic/services/forum.py`
- `src/elbysodic/web/pages/page.py`
- `src/elbysodic/web/pages/_components/realm_gateway.html`
- tests in `tests/test_forum_slice.py` and `tests/test_web_security.py`

Behavior:

- Member hero may show active-face continuation only after public gateway
  privacy is stable.
- Applicant state may show continue-application only to the owning applicant.
- Staff/director continuation should remain Studio-oriented and not leak to
  public mode.
- Keep public premise/atmosphere visible even for signed-in users; continuation
  should augment, not replace, realm orientation.

Proof:

- Member with active face sees safe continuation.
- Faceless member sees first-face path, not active-face affordances.
- Applicant sees only their own application continuation.
- Cross-community user does not see another realm's member/applicant state.
- Signed-out public remains unchanged.

### PR 6: Final QA, Docs, And Cutover

Goal: make the route production-ready and remove stale plan/mock drift.

Files:

- `design/rendered-qa-pass.md`
- `docs/architecture/rendered-route-privacy-matrix.md` if new privacy rows are
  needed
- `docs/product/information-hierarchy.md` if the gateway hierarchy becomes
  product doctrine
- `plans/in-progress/community-landing-design-system-translation-2026-05-15.md`
- `changelog.d/`

Proof:

- `uv run ruff check .`
- `uv run ruff format . --check`
- focused rendered/security tests from PRs 1-5
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check(warnings_as_errors=True)"`
- browser QA profile covering desktop/mobile gateway variants
- broader `uv run pytest -q --tb=short` before merging the cutover

Cutover criteria:

- Public `/c/{slug}` is visually gateway-first and not a forum index.
- A visitor can name the premise engine, why now matters, and where a first
  face enters after the first viewport.
- Public previews do not leak private/staff/member/applicant state.
- Mobile does not force route chrome before the realm promise.
- Original-premise seed communities, not only X-Men, prove the design.

## Supporting Phase Sketch

The original phase sketch below remains as supporting context. The PR plan
above is the concrete build order.

### Phase 0: Baseline Privacy And Route Audit

Goal: prove the current public preview route boundaries before making the page
richer.

Work:

- Add or refresh tests for `/c/x-men-apocalypse` signed-out, applicant, member,
  and staff states.
- Assert public visitors do not see active face, Desk, Studio, staff room,
  private board names, application-review state, private scene names, or
  member continuation details.
- Record current rendered behavior and known template limitations.

Proof:

- Focused rendered tests in `tests/test_forum_slice.py` and/or
  `tests/test_web_security.py`.
- App check.

### Phase 1: Service-Owned Gateway Contract

Goal: create `RealmGatewayView` and one service method for the route.

Work:

- Add `AppServices.realm_gateway()` for signed-in viewers.
- Add `AppServices.public_realm_gateway(community_slug)`.
- Use existing materials, wanted hooks, boards, public scene summaries, and
  public preview community checks.
- Pull public discovery profile fields into the gateway contract where they
  answer premise engine, play engine, lore aperture, roster posture, catalog
  pitch, and onboarding pitch.
- Return audience-specific copy and CTA posture from services.
- Keep current template behavior available until the new template is ready.

Proof:

- Service tests for no event, one event, and multiple events.
- Service tests for at least three archetype variants: no-event social realm,
  gated-lore mystery, and institution/status/scarcity pressure.
- Service tests for visitor, applicant, member, staff boundaries.
- Multi-community privacy tests.

### Phase 2: Shared Components And Chirp Composition

Goal: build production components without importing prototype CSS.

Work:

- Add `_components/realm_gateway.html`.
- Reuse existing button/badge/surface/stack/cluster primitives.
- Reuse existing board media helpers where possible.
- Promote only repeated gateway shapes; keep one-off composition inside the
  route template.
- Add no-media fallback behavior using existing media tokens.

Proof:

- Rendered tests assert major semantic sections and CTAs by audience.
- Snapshot-like assertions stay semantic, not pixel brittle.

### Phase 3: Premise Engine, Scene Hubs, And Atmosphere

Goal: make premise engine and atmosphere visible while keeping them
programmatic and safe.

Work:

- Add location emphasis values from service read model:
  - normal
  - featured
  - hot now
  - event-linked
  - high activity
  - director-pinned
- Compute initial emphasis without schema changes:
  - active/open public scenes in location
  - related current event material
  - seeded media availability
  - director-pinned deferred unless already modeled
- Render a responsive bento field for desktop.
- Collapse to one-column cards on mobile.
- Ensure copy and layout work when the emphasized hub is a social place,
  mystery location, faction/institution, industry venue, trial house, or
  frontier station instead of an event battlefield.

Proof:

- Tests for emphasized location selection and private-board exclusion.
- Rendered proof that current event is not required for the gateway to feel
  playable.
- Browser QA for desktop, tablet, mobile, media/no-media.

### Phase 4: Template Cutover

Goal: replace the current public/member community home template with the
gateway composition.

Work:

- Update `src/elbysodic/web/pages/page.py` to call the gateway service.
- Update `src/elbysodic/web/pages/page.html` to render the new components.
- Preserve tenant-prefixed links.
- Keep `/world`, `/wanted`, `/locations`, `/request-access`, `/desk`, and
  application links in the correct audience states.

Proof:

- Rendered route tests for `/c/x-men-apocalypse` plus another seed realm.
- Public route privacy tests.
- App check.

### Phase 5: Browser QA And Polish

Goal: prove the page feels designed, not merely assembled.

Work:

- Browser QA for:
  - signed-out visitor
  - applicant
  - member with active face
  - no-event social realm
  - gated-lore mystery realm
  - institution/status/scarcity pressure realm
  - no-media fallback
  - no active event
  - one active event
  - multiple active events
  - mobile and desktop
- Check long realm names, long wanted titles, missing media, empty wanted,
  empty public scenes, and reduced motion.

Proof:

- Browser screenshots or QA notes in the established QA artifact location.
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`
- Focused tests, then broader local gate if implementation touches shared
  services or components.

## Contract Matrix

| Contract | API/CLI | Programmatic | Protocol/Routes | Schema/Types | Docs | Examples/Seeds | Tests | Changelog |
|---|---|---|---|---|---|---|---|---|
| Realm gateway read model | N/A | `RealmGatewayView` | `/c/{community_slug}` | typed service models first | design + product docs | X-Men + one other realm | service + rendered | yes when shipped |
| Premise engine | N/A | `RealmGatewayPremise` or equivalent fields | `/c/{community_slug}` | reuse discovery profile first | community shapes + design stress pass | original-premise realms | archetype variants | yes if shipped |
| Atmosphere state | N/A | `RealmGatewayAtmosphere` | page copy/sections | no schema first | Appearance/experience docs if promoted | no/one/multi event fixtures | service + rendered | yes if user-visible |
| Location bento | N/A | `RealmGatewayLocationCard.emphasis` | community home | no schema first | composition/design notes | X-Men emphasized locations | privacy + browser | yes if shipped |
| Public wanted/scene previews | N/A | public-safe preview rows | community home | existing wanted/thread models first | privacy docs if changed | open/private fixtures | negative leakage tests | yes |
| Curated gateway slots | N/A | `GatewaySlot` repository + gateway service ordering | `/c/{community_slug}` + Studio curation | `community_gateway_slots` tenant-scoped table | plan + privacy matrix | Harbor curated slots | migration + repository + service + rendered | yes |
| Member/applicant continuation | N/A | audience-specific continuation | community home | existing membership/application first | info hierarchy if behavior changes | seed personas | rendered privacy | yes |

## Risks

- Prototype CSS overfit: copying static CSS would create layout debt and bypass
  Chirp.
- Event overfit: B-24 must stay seed content, not a permanent product shape.
- Archetype overfit: public UI should communicate the play promise without
  turning the internal taxonomy into loud labels everywhere.
- Public leakage: richer previews increase risk of private/staff/application
  side channels.
- Bento overreach: arbitrary masonry controls could become a layout builder.
- Homepage/Network overlap: `/c/{slug}` should remain one realm gateway, while
  `/` and `/network` handle cross-realm discovery.

## Deferred

- Persisted event scheduling or multi-event schema.
- Director-authored layout builders.
- Public-scene curation until public scene eligibility is explicit.
- Public route migration.
- Cross-realm personalization.
- Appearance Studio controls for bento layout.
- AI-generated atmosphere copy.

## Immediate Next Slice

Recommended first PR:

1. Add `RealmGatewayView` read models.
2. Add public/member service methods using existing data.
3. Include premise-engine fields from the existing public discovery profile.
4. Add service and rendered privacy tests for `/c/x-men-apocalypse` plus at
   least one original-premise realm.
5. Do not change the visual template yet.

That creates the contract needed to translate the mock safely.
