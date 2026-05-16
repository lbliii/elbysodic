# Community Landing Design-System Translation

Status: draft implementation plan after static V2 prototype
Owner: Product design, Chirp/web, service, privacy, tests, and docs stewardship
Created: 2026-05-15
Last updated: 2026-05-15
Review by: 2026-05-29
Closure criteria: the community landing V2 prototype is translated into
service-owned public/member/applicant read models, Chirp-composed Elbysodic
components, theme-layer CSS, privacy-tested rendered routes, desktop/mobile
browser QA, and docs/checklist updates; or the prototype is explicitly
superseded by a narrower gateway plan.

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

## Implementation Phases

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
