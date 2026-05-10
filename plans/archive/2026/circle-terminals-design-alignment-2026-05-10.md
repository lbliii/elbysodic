# Circle Terminals Design Alignment Plan

Status: completed and archived
Owner: design + web stewardship
Created: 2026-05-10
Updated: 2026-05-10
Review by: 2026-05-17

## Goal

Align the app's default visual system with the selected Circle Terminals brand
direction and the existing technicolor futurism doctrine, without weakening
long-form reading, community identity, or staff/private clarity.

The logo gives the palette and grammar:

```text
o --   opening post
o -    reply beat
o ---  continuing scene
```

Translated to UI:

- black key = structure, shell, focus containment, product precision
- cyan = opening/thread signal, world/atmosphere, exploration
- magenta = face/reply identity, selected state, active membership energy
- amber = continuity, needs reply, warning/event pressure
- cool white = prose, thread bars, text-bearing surfaces

## Non-Goals

- No schema, migration, repository, service, Blueprint, CLI, or import/export
  changes.
- No public Appearance Studio contract changes.
- No raw CSS, arbitrary HTML, external font URLs, or layout controls.
- No SPA redesign.
- No replacement of community marks. Circle Terminals is the platform mark;
  `community_mark_url` remains realm identity.
- No broad page redesign in the palette pass.

## Steward Boundaries

Consulted docs/stewards:

- root `AGENTS.md`
- `design/AGENTS.md`
- `src/elbysodic/web/AGENTS.md`
- `design/technicolor-futurism.md`
- `design/technicolor-futurism-roadmap.md`
- `design/component-inventory.md`
- `docs/product/appearance-studio.md`
- `docs/product/information-hierarchy.md`
- `design/motion-design.md`

Affected steward areas:

- Design: palette, surface budgets, brand coherence.
- Web: shell, templates, static CSS, rendered route QA.
- Tests: rendered assertions and browser QA artifacts.
- Docs: design notes, not public product contracts unless behavior changes.

## Phase 1: Token Audit And Target Map

Objective: define the exact token changes before editing CSS.

Work:

- Audit current `src/elbysodic/web/static/elbysodic-theme.css` color tokens:
  key dark/light, surfaces, borders, text, muted text, accent, secondary
  accent, state colors, glass, on-media text, focus ring.
- Create a target map from Circle Terminals roles to existing tokens:
  `--elbysodic-key-dark`, `--elbysodic-key-light`,
  `--elbysodic-identity-dye`, `--elbysodic-atmosphere-dye`,
  `--elbysodic-state-needs-reply`, `--elbysodic-state-waiting`,
  `--elbysodic-state-caught-up`, `--elbysodic-state-watching`,
  `--elbysodic-state-private`, `--elbysodic-state-staff`,
  `--elbysodic-state-error`, `--elbysodic-editorial-rule`,
  `--elbysodic-glass-bg`, `--elbysodic-glass-border`,
  `--elbysodic-on-media-*`.
- Decide which current tokens are already aligned and which need adjustment.
- Keep the light mode as a first-class luminous porcelain/ink treatment.

Deliverable:

- A short design note or section in `design/` describing before/after token
  intent and accepted color roles.

Proof:

- `rg`/file audit grounded in actual token names.
- No app behavior changes in this phase if kept doc-only.

## Phase 2: Default Theme Token Pass

Objective: shift the default app tone toward Circle Terminals/technicolor
futurism with a small, reversible CSS change.

Work:

- Edit only `src/elbysodic/web/static/elbysodic-theme.css`.
- Adjust default dark and light token values, not page-local selectors.
- Preserve existing Chirp-UI token mappings.
- Make high chroma purposeful:
  - cyan: atmosphere/focus/explore
  - magenta: identity/selection/face
  - amber: needs reply/warning/continuity
  - green: caught up/safe state only
  - coral/red: error/destructive only
- Keep thread body, composer, application review, staff/private, and recovery
  surfaces calmer than ritual surfaces.

Surfaces to check:

- `/`
- `/network`
- `/c/x-men-apocalypse`
- `/c/x-men-apocalypse/world`
- `/c/x-men-apocalypse/locations`
- one board/location page
- one thread page
- new-thread composer
- `/c/x-men-apocalypse/wanted`
- `/c/x-men-apocalypse/casting`
- `/c/x-men-apocalypse/applications`
- `/c/x-men-apocalypse/claims`
- `/c/x-men-apocalypse/studio`
- `/login`
- `/request-access`

Deliverable:

- CSS token patch.
- Changelog fragment if default appearance changes are user-visible.

Proof:

- `uv run ruff check .`
- `uv run ruff format . --check`
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`
- focused rendered tests if markup/classes change; otherwise explain no
  rendered test impact.
- Browser QA smoke, and deep profile if broad palette regressions are likely.

## Phase 3: Surface Intensity Corrections

Objective: fix obvious mismatches after the token pass without broad redesign.

Candidate corrections:

- Shell/topbar/sidebar active states: reinforce the Circle Terminals dye
  grammar without making navigation noisy.
- Network/global surfaces: make product identity feel more deliberate now that
  the product mark is installed.
- Wanted/casting: first ritual family to get stronger editorial/casting
  energy after palette stabilization.
- Applications/claims/Studio: keep lower intensity and state-forward.

Rules:

- Do not put glass behind prose, composer body, staff notes, or application
  review text.
- Do not make every datum a badge/card/pill.
- Do not hide active face, next action, staff/private state, or validation.
- Prefer shared `_components/` macros if repeated shapes appear.

Deliverable:

- Small selector-level CSS patch or a follow-up implementation plan if the
  surface needs component promotion.

Proof:

- Rendered tests for any semantic markup/component change.
- Browser QA screenshots for desktop and mobile.

## Phase 4: Wanted/Casting Identity Upgrade

Objective: make the first product family really inherit the logo's language:
faces attached to threads, desire/casting energy, and continuity handoff.

Candidate work:

- Audit `_components/wanted.html`, casting page templates, and plotting
  handoff cards.
- Strengthen wanted cards with a clearer face/thread/interest rhythm.
- Align reserve, interest, ready-for-scene, and plotting states with the
  state dye map.
- Preserve privacy: private interest notes and staff/backstage state must not
  leak.

Deliverable:

- Component-level plan or implementation patch.
- Docs update to `docs/product/information-hierarchy.md` if a repeated visual
  concept is renamed or promoted.

Proof:

- rendered tests for wanted/casting privacy and state visibility.
- browser QA for wanted index/detail and casting desk.

## Phase 5: Brand Cleanup

Objective: keep the repo usable after exploration.

Work:

- Decide whether to keep all `design/logo-options/` exploration files, move
  non-selected options into an archive subfolder, or remove them.
- Move the selected Circle Terminals brand kit into `design/brand/` and keep
  non-selected options archived under `design/logo-options/archive/`.
- Update `design/README.md` if brand assets become a durable design area.
- Add a changelog fragment for installed product brand if this ships.

Proof:

- File organization diff only.
- No app behavior changes unless paths move.

## Risks And Mitigations

- Risk: palette becomes futuristic but less readable.
  Mitigation: reading surfaces are the hard gate; check thread body,
  composer, guidebook, applications, claims, and recovery first.

- Risk: cyan/magenta/amber become rainbow decoration.
  Mitigation: every high-chroma use must map to atmosphere, identity, or
  continuity/state.

- Risk: product mark competes with community marks.
  Mitigation: platform mark stays global/platform; community marks remain
  primary in tenant shell.

- Risk: token pass silently breaks light mode.
  Mitigation: test light, dark, and system mode before acceptance.

- Risk: CSS-only design drift creates untested visual regressions.
  Mitigation: use browser QA screenshots and keep selector changes small.

## Acceptance Criteria

- Default theme visibly aligns with Circle Terminals and technicolor futurism.
- Thread prose, composer, applications, claims, staff/private, and recovery
  surfaces remain calm and readable.
- Community marks still own realm identity.
- Product mark appears only in platform/global/account/attribution contexts.
- Light and dark modes both look intentional.
- Browser QA passes desktop and mobile smoke.
- Required local gates pass or skipped gates are explicitly justified.

## Recommended Next Implementation Slice

Start with Phase 1 and Phase 2 together in one small PR:

1. document the token target map
2. adjust the default token values in `elbysodic-theme.css`
3. run app check and browser QA
4. update changelog if the appearance change is accepted

Do not touch wanted/casting composition until the base palette is stable.

## Final Note

Archived on 2026-05-10 after completing the token map, default theme pass,
surface intensity corrections, wanted/casting identity upgrade, brand source
organization, release collateral, focused rendered proof, and app check.
