# Location And Board Media Epic

Status: implemented; archive candidate after final verification note
Owner: Product/UI stewardship  
Created: 2026-05-02  
Last updated: 2026-05-09
Review by: 2026-05-16
Closure criteria: split into PRs for accessible board media rendering, seeded
location art throughlines, Studio QA controls, and any later Blueprint alignment.

## 2026-05-09 Verification Update

PRs 1-5 are marked implemented in this plan. The remaining useful work is not a
new media epic; it is final verification and archival hygiene. Keep only
explicit follow-ups that still matter for production readiness: browser QA for
board media on dense/mobile pages, Blueprint/export alignment if needed, and
seed media availability in Railway smoke.

## Purpose

Move from one community-level hero image to a layered visual language for
locations, sublocations, and forum boards.

The product goal is not "images everywhere." It is to make a board's playable
world easier to scan: a writer should feel the difference between the academy,
the city, a paddock, a night market, or a town hall before reading a paragraph,
while still getting stable navigation, readable metadata, and accessible media.

## Current State

- `boards.image_url` and `boards.image_alt` already exist.
- The Studio board editor already lets staff set a board image URL and alt text.
- Board cards, board pages, and Studio previews currently render board media as
  CSS `background-image` values.
- Community hero media now renders through safe treatment enums: split,
  background, poster, and text-first.
- Seed communities have distinct community marks and world heroes, but seeded
  boards do not yet have a deliberate media throughline.

The main gap is not persistence. The main gap is product quality: meaningful
board images need accessible rendering, alt validation, seed art direction, and
consistent presentation rules.

## Principles

1. Board media should clarify playable place and pressure, not decorate every
   repeated item.
2. Meaningful images should have an accessible text equivalent. Do not rely on
   CSS backgrounds for world-significant media.
3. Location images should inherit the community art direction while giving each
   board its own motif.
4. Keep controls as safe fields and enums. No raw CSS, custom templates,
   external scripts, or per-board layout builders.
5. Prefer existing `Board` fields before adding schema. Add new board media
   fields only when a real repeated need appears.
6. Keep operational surfaces calm: composer controls, thread actions, queue
   affordances, staff controls, and notification flows must not be visually
   buried by board art.

## PR Sequence

### PR 1: Accessible Board Media Rendering

Implemented in commit `db44c3c`.

Goal: make existing board images render through product components instead of
inline background-image shortcuts.

Tasks:

- Add a shared board media frame/component under
  `src/elbysodic/web/pages/_components/`.
- Replace background-image rendering in:
  - `src/elbysodic/web/pages/_components/boards.html`
  - `src/elbysodic/web/pages/boards/{board_slug}/page.html`
  - `src/elbysodic/web/pages/studio/boards/{board_slug}/page.html`
- Preserve overlays, slug classes, active-face relevance signals, and mobile
  layout.
- Add service validation so a board image URL requires alt text.
- Add rendered tests that prove board image alt text is present somewhere
  accessible on board cards and board pages.

Acceptance checks:

- Existing board image workflows still work from Studio.
- Meaningful board media is no longer only a CSS background.
- Missing alt text is rejected when staff save a board image URL.
- `uv run pytest tests/test_forum_slice.py tests/test_tenant_repository.py -q --tb=short`
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`

### PR 2: Seed Location Art Throughlines

Implemented in commit `cc731a7`.

Goal: give seeded boards distinct images that belong to each community's visual
language.

Tasks:

- Add local seed board media assets under
  `src/elbysodic/web/static/seed-media/locations/`.
- Define a small art bible per seed community:
  - X-Men: cold academy light, B-24 signal geometry, institutional winter.
  - HP: glass, staircases, paper, candlelight, magical institutional memory.
  - Jurassic: operations monitors, fences, rain, warning color, island greenery.
  - RL NYC: late transit, windows, rain, neon work-life pressure.
  - RL Small Town: storefronts, civic boards, string lights, lake-road dusk.
- Seed images for primary location boards first, then important sublocations
  where they carry different scene pressure.
- Keep community boards more restrained unless they represent a place-like
  ritual surface.
- Add seed tests for expected board image URLs and alt text.

Acceptance checks:

- Each seeded community has at least three location images.
- X-Men primary locations and HP/Jurassic/NYC/small-town programs feel visually
  related but not interchangeable.
- Seed hydration is idempotent and does not overwrite locally customized board
  images.
- Browser QA covers home location cards, a board page, and Studio board preview.

### PR 3: Board Media Presentation Controls

Implemented in this branch after seeded art QA showed boards need safe focal,
treatment, and overlay controls across cards, stages, and Studio previews.

Goal: decide whether board media needs a small safe control set like community
hero treatment, after the seeded assets expose the real layout pressures.

Candidate controls:

- Image focal point: center, top, bottom, left, right.
- Board media treatment: card poster, stage background, compact thumbnail,
  text-first.
- Overlay strength: light, medium, heavy.

Decision rule:

- Add schema only if seed/browser QA shows one image cannot work across cards,
  board stages, and Studio previews with existing CSS.
- Prefer one shared field set over page-local exceptions.

Acceptance checks:

- Controls are staff-gated through navigation/world management policies.
- Unsupported enum values are rejected.
- Rendered pages preserve readable text at desktop and mobile widths.

### PR 4: Location Page Throughline Pass

Implemented in this branch with a location throughline band, visible active-face
relevance on location stages, and focused dense/quiet location coverage.
The throughline side panel is framed as plot pressure so future event boosts,
location pins, or per-post reward modifiers can occupy that slot without
turning nearby/scene links into redundant jump controls.

Goal: make board pages feel like playable locations, not just thread lists with
art.

Tasks:

- Review board stage hierarchy against `docs/product/information-hierarchy.md`
  and `docs/product/paragraph-rhythm.md`.
- Tune how sublocations, sibling locations, current events, and latest threads
  sit below the board media.
- Ensure active-face relevance remains visible without competing with the
  location image.
- Add browser QA screenshots for one dense location with sublocations and one
  quieter location with few threads.

Acceptance checks:

- Board pages remain fast to scan for "start thread", "next unread", current
  event, sublocations, and latest activity.
- Images do not push the useful thread list too far down on mobile.
- Text never collapses to one-word columns.

### PR 5: Blueprint And Export Alignment

Implemented in this branch for Program Blueprint parsing, preview summaries,
validation, docs, and seed hydration of safe board media fields. Export remains
future work because there is not yet a board export surface.

Goal: only after Studio and seed behavior settle, decide how board media belongs
in starter packets.

Tasks:

- Update Program Blueprint docs if board media URLs become part of the safe
  starter packet contract.
- Validate alt text in blueprint previews.
- Keep raw CSS and arbitrary layout out of blueprint input.
- Defer hydration unless the broader Program Blueprint apply flow is active.

Acceptance checks:

- Blueprint validation rejects media without alt text.
- Appearance payloads are readable in director language.
- No import path can smuggle scripts, raw CSS, or external font controls.

## Not Now

- User upload/storage pipeline.
- AI image generation inside the app.
- Raw CSS or Jcink skin import.
- Per-board HTML templates.
- Images for every tiny board before the primary locations prove the system.
- Marketplace or downloadable theme packs.

## Risks

- Accessibility regression if images remain CSS-only or alt text is treated as
  optional.
- Visual noise if every card becomes a large artwork.
- Seed assets becoming too generic and failing to show the difference between
  communities.
- Variant sprawl if each board asks for a bespoke treatment.
- Mobile layouts pushing thread actions and latest activity too far down.

## Consulted Stewards

- Root constitution: PBP-native world surface, character/scene context, and
  community aesthetic control.
- `src/elbysodic/web/AGENTS.md`: server-rendered pages, shared components,
  stable controls, readable long-session UI.
- `src/elbysodic/db/AGENTS.md`: existing board media storage and idempotent
  seed data.
- `src/elbysodic/services/AGENTS.md`: staff-gated service methods and no
  template-owned tenant checks.
- `src/elbysodic/domain/AGENTS.md`: board/location primitives stay typed and
  community-scoped.
- `tests/AGENTS.md`: rendered-page and tenant-boundary coverage.

## Next Checks

1. Confirm seed media URLs return `200` on Railway.
2. Include one dense and one quiet board in the production browser QA pass.
3. Archive this plan after those checks or move any remaining export work into
   the Program Blueprint roadmap.
