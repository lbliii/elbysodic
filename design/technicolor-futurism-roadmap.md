# Technicolor Futurism Roadmap

This roadmap translates Elbysodic's stated design vision into staged product
design work. It is design guidance, not an implementation contract. Do not use
this file to change public routes, Program Blueprint fields, schema, storage,
runtime dependencies, or Appearance Studio behavior without an explicit human
check-in and the relevant stewards.

Target vision: technicolor futurism that feels luminescent, clean, striking,
and editorially prestigious, with reading-first PBP flow. Chirp + Kida +
HTMX + Alpine stay the hypermedia stack. Elbysodic owns primitives and
tokens; Chirp-UI is leftover (ADR 0002), not the structural library.
Personality should be layered through tokens, surface rules, repeated PBP
components, media treatment, and safe art-direction programming.

## Current-State Assessment

### What Is Already Working

- `src/elbysodic/web/static/elbysodic-theme.css` already behaves like a
  product token layer. Named Elbysodic values exist for canvas, surface,
  accent, text, border, focus, link, radius, shadow, and mode. Leftover
  `--chirpui-*` aliases are a migration layer to drain (ADR 0002), not
  the design-system foundation.
- Shared PBP vocabulary has started moving into
  `src/elbysodic/web/pages/_components/`: boards, sidebar, facets, post
  frames, composer controls, wanted cards, plot hooks, thread summaries, and
  generic vocabulary components such as `local_rail`, `preview_row`,
  `metric_item`, `command_action`, `command_panel`, `lane_preview`,
  `production_room_card`, and `room_header`.
- Ritual surfaces already carry visual identity: world hero, network
  billboard, board stage, board posters, thread stage, character/profile
  posters, post profile rail variants, material heroes, event actions, and
  wanted/plotter cards.
- Reading-first work is not theoretical. The CSS has concrete prose rules:
  `elbysodic-prose-body`, post density variants, composer preview parity,
  max-widths around 66 to 72 characters, paragraph rhythm, and opaque post
  body surfaces.
- Appearance Studio already has safe primitives: light/dark theme token fields,
  allowlisted font/radius/density/texture keys, health warnings, media slots,
  world hero treatment, image focal point, overlay strength, hero height,
  identity accent source, and post style vocabulary. These match
  `docs/product/appearance-studio.md`.
- Product docs already define useful design doctrine:
  `design/technicolor-futurism.md`, `design/art-direction-program.md`,
  `docs/product/information-hierarchy.md`, and
  `docs/product/control-topology.md` agree that prose, active face,
  scene/thread state, privacy, and writer obligations outrank atmosphere.
- The design is tenant-aware in spirit where customization appears. Theme,
  media, navigation, identity accents, and post style policy are framed as
  community-local decisions, not global user or global character styling.

### What Conflicts With The Vision

- The default palette still reads warm editorial paper more than technicolor
  futurism. Current anchors are ink, paper, rose, moss, and gold. They are
  tasteful and readable, but not yet luminescent, clean, cool, or striking
  enough to establish the desired first impression.
- Templates still import leftover Chirp-UI primitives (`container`, `stack`,
  `cluster`, `surface`, `badge`, `breadcrumbs`, `section_header`, `tooltip`,
  `avatar_stack`, `timeline`, `stat`, buttons, chips, and form-field
  classes). ADR 0002 treats those as an exit target. New UI uses Elbysodic
  class names and `_components/`.
- Color roles are not yet a full color score. The theme still has leftover
  Chirp-UI token mappings, but Elbysodic-specific product roles are still
  incomplete: identity dye, atmosphere dye, active face, staff/private
  state, queue states, on-media overlays, material intensity, and surface
  intensity are not all named as stable token purposes.
- CSS is doing a lot of product-system work in one large file. That is allowed
  by the current architecture, but the meaning of major component families is
  easier to infer from selectors than to verify from a smaller token/component
  contract. Future changes could drift into page-local style logic.
- Some surfaces are already close to technicolor, but the expression is uneven:
  network and board/media surfaces carry cinematic treatment; discovery,
  wanted, claims, applications, and some dense Studio rooms are more neutral
  and card-like.
- Glow, gradients, scanline texture, and translucent panels appear in several
  places, but there is not yet a documented "surface intensity budget" wired to
  the actual template/component list. That makes it hard to tell whether a
  future accent belongs on a thread body, wanted card, or Studio queue.
- Glass is present in shell/topbar/sidebar and selected icon actions, but the
  product has not chosen its first canonical glass-eleganza pattern. Menus,
  popovers, media captions, topbar/sidebar, and network icon actions are all
  candidates; none is documented as the proof pattern.
- PBP component vocabulary is strong but incomplete. Wanted hooks, plotting
  backstage, applications, claims, roster/discovery cards, event notices,
  material cards, and post rails have product meaning, but only some are
  promoted into reusable macros with documented visual roles.
- The current world/board/thread visual language is shaped by X-Men seed data
  background classes. That is useful demo art direction, but it risks making
  technicolor futurism feel seed-specific instead of community-programmable.
- Appearance Studio exposes useful controls, but it still asks directors to
  edit individual theme tokens rather than helping them compose an art
  direction from premise, genre lanes, tone, safety posture, and surface
  intensity.

## Design Gap Analysis

### Palette And Token Gaps

- Need a cooler default key system: blue-black or graphite dark mode, cool
  porcelain light mode, crisp borders, high-legibility text, and less warm
  paper dominance.
- Need explicit dye roles layered over Elbysodic tokens:
  `identity_dye`, `atmosphere_dye`, `state_dyes`, `active_face`,
  `private_state`, `staff_state`, `on_media`, `focus`, and `editorial_rule`.
- Need state colors for PBP obligations beyond generic success/warning/error:
  `needs_reply`, `waiting`, `caught_up`, `watching`, `unread`, `private`,
  `staff`, `locked`, and `archived`.
- Need contrast guidance for color-mixed accents. A luminous accent should not
  make muted metadata, focus rings, warning notices, or on-media text fragile.

### Component Gaps

- Need an audited component inventory that maps each repeated visual shape to
  the docs vocabulary and current macros in `_components/`.
- Need a `RitualSurface` or equivalent design category in documentation before
  implementation: world gateway, board/location, thread stage, character hub,
  wanted hook, event notice, material detail, and network realm cards.
- Need a `ReadingSurface` category: thread body, composer, application review,
  staff/private notes, recovery pages, and long guidebook prose.
- Need a `ProductionSurface` category: Studio rooms, claims, reserves,
  applications, operations, launch, navigation composer, and health warnings.
- Need a canonical glass pattern with fallback expectations. Candidate:
  transient menu/popover/media-caption treatment, not post body or staff forms.
- Need wanted and plotting surfaces to feel more like casting/editorial desire
  rather than generic cards, while preserving interest, reserve, and backstage
  privacy boundaries.

### Layout And Editorial Gaps

- The strongest editorial pages are world, board, thread, character, and
  network. Discovery, claims, applications, and some Studio subrooms need the
  same edited hierarchy: identity first, next action second, metadata third.
- Dense cards frequently use similar tinted panels. That is coherent, but it
  can flatten hierarchy. More surfaces should use rules, compact rows, and
  typographic rhythm instead of another elevated card.
- Mobile has responsive rules for most major surfaces, but the design system
  lacks a durable mobile QA matrix for long titles, no media, many badges,
  many facets, and active-face controls.
- The first viewport of atmospheric surfaces should always show product work
  below the hero. Existing hero heights support this, but QA should verify it
  after palette/media changes.

### Appearance Studio And Art Direction Gaps

- Appearance Studio has safe controls, but not yet a guided art-direction
  workflow. Directors need help translating premise into key, dyes, media
  direction, material use, and restraint without raw CSS.
- The `design/art-direction-program.md` color-score model is promising but is
  not yet connected to a non-contract preview mode.
- Programmatic support should start with internal preview/read-model ideas,
  validation rules, and design fixtures, not new public Blueprint fields or
  database columns.
- Art direction health warnings should name PBP surfaces. The docs say this;
  future implementation should prove it across thread body, wanted hooks,
  application review, staff/private notices, and world gateway.

## Design Principles To Preserve

1. Reading is the prestige surface. Thread prose, guidebook material,
   applications, and composer preview stay calmer than heroes and network
   cards.
2. Elbysodic owns primitives and tokens (ADR 0002). Chirp supplies pages,
   Kida, HTMX, and Alpine. Extend through product tokens, `_components/`,
   composition, and vocabulary. Do not treat leftover Chirp-UI as the
   structural library.
3. Community art direction is safe and scoped. Directors get approved tokens,
   media slots, variants, density, texture, and warnings, not raw CSS,
   arbitrary HTML, scripts, external font URLs, or layout builders.
4. Color behaves like light and signal. High chroma should identify a face,
   current scene, surface state, event pressure, or action path.
5. Character identity stays operationally clear. Active face, author face,
   writer, membership, and staff state must not blur together.
6. Production rooms stay precise. Studio, claims, applications, staff/private
   surfaces, and recovery pages can inherit style, but atmosphere must not
   compete with trust, privacy, labels, or validation.
7. PBP vocabulary drives UI vocabulary. Use face, roster, thread, scene,
   plotter, wanted, claims, reserves, needs reply, waiting, caught up, and
   watching instead of generic dashboard language.
8. Mobile is a designed surface. Heroes, rosters, post rails, composer, queues,
   filters, and forms should intentionally recompose instead of merely stacking.

## Phased Roadmap

### Near: Stabilize The Design Contract

Goal: make the current product layer easier to evaluate before changing the
default look.

- Create a component inventory that maps actual selectors and macros to the
  vocabulary in `docs/product/information-hierarchy.md`.
  Surfaces: `src/elbysodic/web/pages/_components/`,
  `src/elbysodic/web/static/elbysodic-theme.css`, and representative page
  templates.
- Define a surface-intensity matrix in design docs for existing screens:
  world gateway, network, board/location, thread stage, thread body, composer,
  character hub, wanted, plotting, material, applications, claims, Studio,
  staff/private, and recovery.
- Audit `elbysodic-theme.css` for token purposes. Separate "Chirp token
  mappings we rely on" from "Elbysodic product aliases we need next" without
  changing CSS yet.
- Identify the first canonical glass proof. Recommended candidate:
  transient menus/popovers and media captions, because they match the
  `technicolor-futurism.md` glass rule and avoid prose risk.
- Define the first motion contract from `design/motion-design.md`: tokenized
  durations, allowed properties, reduced-motion fallbacks, and which surfaces
  may carry ambient or entrance motion.
- Define a screenshot/browser QA checklist for design changes:
  desktop and mobile, light/dark/system, hero with media and no media, long
  titles, many facets, thread prose, composer, application review, and staff
  notice.
- Add a "do not cross" list for visual changes:
  no glass behind prose, no raw director CSS, no user-level character styling,
  no hidden active-face context, no unlabeled icon-only PBP actions.

Deliverables:

- `design/` component inventory or appendix.
- Surface-intensity matrix.
- Token-purpose checklist for future CSS work.
- Motion-purpose checklist for future CSS/JS work.
- QA checklist tied to specific routes and components.

Proof:

- Doc-only proof can be Markdown review plus `rg` spot checks.
- Any later implementation based on this phase should run the web app check
  and rendered page/browser QA named in `src/elbysodic/web/AGENTS.md`.

### Near: Shift The Default Art Direction Deliberately

Goal: make the default product read as technicolor futurism without sacrificing
prose.

- Explore a cooler default palette using the existing Chirp token contract:
  key dark, key light, text, muted text, surface, elevated surface, border,
  accent, secondary accent, success, warning, error, focus, and on-media
  values.
- Keep the first implementation small when approved: token values in
  `src/elbysodic/web/static/elbysodic-theme.css`, not page-local rewrites.
- Test palette candidates on these surfaces before acceptance:
  world gateway, network billboard/card, board stage/poster, thread stage,
  post body, composer, character hub, wanted hook, material page, Studio,
  application review, claims, notices, and recovery page.
- Preserve warm editorial readability if the cool palette fails contrast or
  reading comfort. The visual target is luminescent and clean, not blue-black
  darkness everywhere.
- Ensure light mode is first-class. Technicolor futurism needs a luminous
  light mode, not just a dark theme with neon accents.

Deliverables:

- Candidate palette notes in `design/`.
- Accepted token map with explicit before/after rationale.
- Browser QA artifacts if implementation proceeds.

Proof:

- Contrast checks for text, muted text, links, focus, badges, warnings,
  staff/private notices, and on-media text.
- Screenshots for desktop and mobile across the required ritual, reading, and
  production surfaces.

### Mid: Turn Existing Visual Language Into Named Product Components

Goal: reduce drift by promoting repeated PBP shapes and documenting their
meaning.

- Promote or document repeated shapes that are currently mostly CSS-driven:
  `RitualHero`, `BoardStage`, `ThreadStage`, `PostProfileRail`,
  `CharacterPoster`, `WantedHookCard`, `EventNotice`, `ApplicationReviewCard`,
  `ClaimRecord`, and `PlottingBackstageCard`.
- Align wanted, plotter, casting, and backstage cards with the same editorial
  prestige as character and thread surfaces. They should feel like casting and
  desire, not generic task cards.
- Clarify when a card is appropriate. Repeated objects can be cards; page
  sections and dense production bands should prefer unframed layouts, rules,
  rows, or compact panels.
- Standardize post/face identity treatment. The post rail variants are a
  strong start; the roadmap should ensure roster cards, character hubs,
  thread cast, composer active face, and identity menu all speak the same
  identity language.
- Define state styling for PBP obligations: needs reply, waiting, caught up,
  watching, unread, in plotting, ready for scene, reserved, private, staff,
  locked, archived.

Deliverables:

- Updates to `docs/product/information-hierarchy.md` and/or `design/` naming
  the component categories.
- Follow-up implementation tickets or plans, not broad rewrites.
- Tests that assert semantic rendering, not fragile pixels, when components
  move into `_components/`.

Proof:

- Rendered-page tests for component presence and privacy-sensitive state.
- Browser QA for layout shifts, long labels, many badges, and mobile stacking.
- Reduced-motion QA for any promoted component with transitions or animation.

### Mid: Build Art-Direction Preview Without New Public Contracts

Goal: help community builders reason about art direction before adding durable
schema, Blueprint, route, or import fields.

- Keep the color-score model internal to design docs and possible local
  fixtures first: key, identity dye, atmosphere dye, state dyes, surface
  intensity, material use, texture, and restraint rule.
- Create non-public sample scores in `design/` or test fixtures only after
  human approval. They can describe boards in director language without
  becoming Program Blueprint keys.
- Define a preview shape that could be rendered from existing safe data:
  community name, premise/material summary, theme preview, media slots,
  existing theme tokens, existing hero treatment, existing post style policy,
  existing facet accent source.
- Draft validation expectations before implementation:
  unknown token key, raw CSS, scripts, unsafe font URLs, low contrast,
  glass behind prose, warning/identity hue collision, missing meaningful alt
  text, and excessive surface intensity.
- Use art-direction warnings as copy prototypes first. Example:
  "Thread body may be hard to read because glass was assigned behind prose."
  Do not change public form behavior until the contract is reviewed.

Deliverables:

- `design/` preview spec for an internal art-direction score.
- Example score fixtures that reference current Appearance Studio controls.
- No schema, route, CLI, Blueprint, or public import/export changes in this
  phase without separate approval.

Proof:

- Design review against `docs/product/appearance-studio.md`.
- Later implementation proof should include validation tests, contrast tests,
  and rendered preview tests with `community_id` explicit.

### Later: Expand Presentation Variants Carefully

Goal: let different boards feel authored while preserving the same product
grammar.

- Add variants only for repeated PBP rituals, not one-off skin ideas.
  Candidate order:
  1. Board/location hero: poster, map, directory, field-note.
  2. Wanted hook: casting-call, relationship, faction-seat, event-role.
  3. Guidebook material: chapter, dossier, noticeboard, archive.
  4. Character hub: profile-dossier, poster-profile, roster-sheet, journal.
  5. Event notice: seasonal-pressure, danger-bridge, festival-banner,
     staff-briefing.
- Each variant must preserve semantic headings, labels, keyboard/touch access,
  mobile wrapping, contrast, safe markup, permission visibility, and stable
  repeated geometry.
- Variants should be implemented as named keys and component classes inside
  approved surfaces, not arbitrary template controls.
- Appearance Studio can expose variants only after defaults, previews, health
  warnings, and docs are coherent.

Deliverables:

- Variant decision records in `design/` or `docs/product/appearance-studio.md`.
- Component-level implementation plans for one family at a time.
- Browser QA artifacts for each launched variant family.

Proof:

- Unit/rendered tests for variant keys and permissions.
- Mobile and desktop screenshots for each variant with long text and no media.
- Accessibility check for labels, focus, and reduced-motion behavior.

### Later: Mature The Design System Operations

Goal: make design quality repeatable for future agents and PRs.

- Add a design review checklist to PR/steward notes for UI work:
  consulted stewards, affected surfaces, token/component changes, proof,
  collateral, risks, and not-now items.
- Decide whether visual QA artifacts belong under `design/`, test artifacts,
  or both.
- Add a small catalog page or dev route only if approved by the web steward.
  It should render real components with seed/read-model data, not a disconnected
  design-system playground.
- Establish a palette regression checklist for light/dark/system and
  high-chroma changes.
- Periodically prune page-local CSS patterns that should be components.

Deliverables:

- Review checklist and QA artifact policy.
- Optional catalog/dev surface proposal.
- Maintenance notes for token/component drift.

Proof:

- Design steward review on UI PRs.
- CI/local gates appropriate to changed surfaces.

## Concrete Workstreams

### 1. Token Architecture

Surfaces:

- `src/elbysodic/web/static/elbysodic-theme.css`
- `docs/product/appearance-studio.md`
- `design/technicolor-futurism.md`
- future `design/` token inventory

Actions:

- Document current Chirp token mappings and Elbysodic product aliases.
- Define the desired color-score token roles without shipping them.
- Later, change default token values only after contrast and screenshot proof.
- Keep `community_id` explicit when token choices become stored or hydrated.

### 2. Reading And Prose Prestige

Surfaces:

- thread detail template
- `_components/posts.html`
- `_components/composer.html`
- material pages
- application review pages
- `docs/product/paragraph-rhythm.md`

Actions:

- Protect prose max-width, line-height, paragraph rhythm, and opaque surfaces.
- Keep composer preview visually close to final post output.
- Audit light/dark contrast for prose, metadata, links, quotes, mentions, and
  active face context.
- Refuse glass, noisy texture, or high-chroma panels behind long-form prose.

### 3. Ritual Surface Art Direction

Surfaces:

- home/world gateway
- network billboard/cards
- board/location pages
- thread stage
- character hubs
- wanted and plotter
- materials and event notices

Actions:

- Assign surface intensity budgets.
- Move repeated ritual visuals toward named component guidance.
- Ensure every first viewport has identity, next action, and a hint of working
  product below the hero.
- Use media and luminous accents where they help directors sell the board's
  promise.

### 4. Production And Safety Surfaces

Surfaces:

- Studio
- claims
- applications
- casting
- staff controls
- recovery pages
- notices/admonitions

Actions:

- Keep these surfaces crisp, low-noise, and label-forward.
- Use color for state, routing, validation, and privacy boundaries rather than
  atmosphere.
- Ensure staff/private/warning/error states never rely on hue alone.
- Keep hidden controls out of the main emotional path only when the primary
  action remains visible.

### 5. Appearance Studio And Community Builder Direction

Surfaces:

- `docs/product/appearance-studio.md`
- `design/art-direction-program.md`
- Studio identity/appearance templates
- future internal previews

Actions:

- Frame controls in director language: premise, tone, reading density, safety
  posture, media direction, and restraint.
- Build previews from approved tokens and existing safe media slots.
- Prototype warnings in PBP terms before public contract changes.
- Keep raw CSS, arbitrary HTML, scripts, external font URLs, and layout
  builders out of V1.

### 6. Component Promotion And Drift Control

Surfaces:

- `_components/`
- `docs/product/information-hierarchy.md`
- `src/elbysodic/web/static/elbysodic-theme.css`
- rendered page tests

Actions:

- Promote repeated PBP concepts into macros when reuse clarifies meaning.
- Avoid generic abstractions that hide product vocabulary.
- Keep CSS selectors aligned with documented component names.
- Add semantic tests for promoted components and privacy/state behavior.

### 7. Motion Design

Surfaces:

- `design/motion-design.md`
- `src/elbysodic/web/static/elbysodic-theme.css`
- `src/elbysodic/web/static/elbysodic-shell.js`
- `src/elbysodic/web/static/elbysodic-composer.js`
- interactive components and future browser QA artifacts

Actions:

- Treat motion as continuity, orientation, state change, and attention routing.
- Tokenize duration and easing before adding new animations.
- Prefer opacity, transform, border, background, and shadow transitions; avoid
  layout-shifting animation.
- Keep ambient motion out of thread prose, composer body, staff/private notes,
  application review, and recovery pages.
- Provide reduced-motion fallbacks for every animation.

## Proof And QA Expectations

For doc-only design work:

- Read root and scoped `AGENTS.md`.
- Check relevant docs and representative implementation surfaces.
- Use `rg` spot checks to ground claims in real files.
- Run no heavy code gates unless the doc change touches executable examples or
  generated docs.

For future visual implementation:

- Run the relevant local gates from root `AGENTS.md`.
- Run app check:
  `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`.
- Browser QA substantial layout/theme changes on desktop and mobile, including:
  world gateway, network, board, thread, composer, character hub, wanted,
  Studio, applications, claims, notices, and recovery.
- Verify light, dark, and system modes.
- Verify with and without media.
- Verify reduced-motion and reduced-transparency fallbacks when glass or motion
  changes.
- Verify no text overlap, no layout shift on hover/focus, and no hidden
  primary PBP action.
- Add rendered-page tests for semantic state, permission, and privacy behavior
  rather than brittle pixel assertions.
- Add changelog fragments only when user-visible UI behavior or default
  appearance changes.

## Risks

- A palette shift could make the app look more futuristic but less readable.
  Reading comfort is the hard gate.
- Technicolor can drift into rainbow noise. Every high-chroma color needs a
  job and a surface budget.
- Glass can quickly become nested translucent clutter. Keep it transient or
  context-linked unless a surface explicitly proves otherwise.
- Appearance controls can become a skin engine by accident. Keep customization
  to approved keys, media slots, variants, density, texture, and warnings.
- Seed-specific art direction can masquerade as product direction. X-Men demo
  classes should inform fixtures, not become the only visual grammar.
- Component promotion can become generic abstraction. Promote only when the
  PBP meaning becomes clearer.
- Design docs can outrun implementation. Mark proposed behavior as proposed
  until code, tests, and product docs support it.

## Non-Goals

- No implementation code changes in this roadmap.
- No new public API, route, CLI, Program Blueprint, schema, migration, or
  storage contract.
- No new runtime dependencies.
- No raw CSS, script, external font URL, or arbitrary template input for
  directors.
- No SPA redesign.
- No generic SaaS dashboard redesign.
- No replacement of Chirp, Kida, HTMX, or Alpine.
- No new Chirp-UI adoption; leftovers drain toward `_components/` and
  Elbysodic primitives (ADR 0002).
- No pixel-perfect design system detached from rendered PBP workflows.

## Programmatic Art Direction Without Contract Changes

The next useful move is to support art-direction thinking internally before
shipping any public contract.

Recommended approach:

1. Treat `design/art-direction-program.md` as the non-contract source for a
   color score.
2. Create internal design fixtures or examples that use existing concepts:
   community name, premise/material summary, current theme preview, existing
   safe token families, media slots, post style policy, identity accent source,
   and surface intensity notes.
3. Express generated direction in director language, not config:
   "graphite key, electric cyan atmosphere on board heroes, magenta face
   identity, amber needs-reply pressure, threads stay opaque."
4. Prototype validation and warnings in docs first:
   low contrast, hue collision, glass behind prose, too much intensity on
   staff/private surfaces, missing meaningful alt text, and state colors that
   collide with identity colors.
5. When implementation is approved, keep values enumerated and
   community-scoped. Hydrate through services/repositories with `community_id`
   explicit and tests covering unsafe input rejection.
6. Do not add Blueprint, schema, route, import/export, CLI, or stored contract
   fields until the human and relevant stewards approve the contract.

This lets Elbysodic move toward community-builder art direction now while
preserving the current public surface and safety model.
