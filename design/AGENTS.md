# Product Design Steward

This domain represents Elbysodic's product design direction, design system
standards, visual identity, interaction quality, and translation of Chirp-UI
primitives into a distinctive PBP-native product experience.

Related docs:

- root `AGENTS.md`
- `design/README.md`
- `design/art-direction-program.md`
- `design/composition-bible.md`
- `design/motion-design.md`
- `design/technicolor-futurism.md`
- `design/technicolor-futurism-research.md`
- `docs/product/experience-direction.md`
- `docs/product/appearance-studio.md`
- `docs/product/information-hierarchy.md`
- `docs/product/control-topology.md`
- `docs/product/navigation-menus.md`
- `docs/product/paragraph-rhythm.md`
- `docs/product/notices-admonitions.md`
- `docs/product/user-personas-panel.md`
- `src/elbysodic/web/AGENTS.md`
- `src/elbysodic/web/static/elbysodic-theme.css`
- `src/elbysodic/web/pages/_components/`

## Point Of View

Represent the product's visual and interaction integrity: Elbysodic should feel
purpose-built for roleplay communities, editorially credible, emotionally safe,
and visually memorable without compromising prose readability or operational
clarity.

## Protect

- Technicolor futurism is the default product art direction: luminescent,
  clean, striking, and editorial, with story prose and character identity
  always foregrounded.
- Chirp-UI remains the component and token foundation. Elbysodic builds product
  personality through named tokens, repeated PBP components, composition,
  rhythm, media treatment, and state language.
- Long-form reading, posting, reviewing applications, managing queues, and
  browsing faces stay calm and legible even when surfaces carry atmosphere.
- Visual identity supports PBP language: face, roster, thread, scene, plotter,
  wanted, claims, reserves, needs reply, waiting, caught up, and watching.
- Shared product concepts graduate into
  `src/elbysodic/web/pages/_components/` before page-local styling becomes a
  parallel design system.
- Theme work uses `src/elbysodic/web/static/elbysodic-theme.css` and approved
  Chirp-UI token names before inventing new CSS surfaces.
- Design decisions preserve tenant, membership, character, staff, privacy, and
  rendered-route boundaries.
- Accessibility, contrast, keyboard reachability, focus states, mobile rhythm,
  and reduced-motion behavior are part of the design bar, not cleanup work.

## Contract Checklist

- Vibe: the surface advances technicolor futurism without becoming generic
  SaaS, nostalgic forum skinning, dark cyberpunk, or decorative neon clutter.
- Reading: prose measure, paragraph rhythm, metadata weight, and muted text
  contrast keep threads, guidebook pages, and application materials readable.
- Hierarchy: identity, action, metadata, state, and atmosphere each have a
  distinct visual role.
- Tokens: colors, type, spacing, radius, density, shadows, and texture use
  Chirp-UI or Elbysodic theme tokens; new tokens are named by product meaning.
- Components: repeated PBP UI shapes are promoted or aligned with
  `_components/`; page-local CSS is justified by local-only behavior.
- States: empty, loading, active, focus, hover, disabled, private, staff-only,
  error, warning, and success states remain clear and accessible.
- Media: art direction supports community, board, face, wanted, material, and
  event identity without hiding required controls or story context.
- Mobile: first viewport, navigation, composer, cards, tables, and dense
  production rooms remain intentionally composed, not merely collapsed.
- Docs: update `design/`, product docs, or web steward notes when visual
  meaning, token contracts, component vocabulary, or Appearance Studio controls
  change.
- Tests and QA: use rendered-page tests for semantic behavior and browser QA
  for substantial layout, motion, media, or responsive changes.
- Changelog: add a user-visible fragment when product UI behavior or default
  appearance changes.

## Advocate

- Turn repeated visual decisions into named design-system guidance instead of
  letting them drift across templates.
- Push for richer default themes and media treatments that let a director
  launch a tasteful board without custom skin labor.
- Improve surfaces where writer attention, active face, reply obligations,
  staff privacy, or next action are visually ambiguous.
- Replace generic dashboard or forum vocabulary with PBP-native composition and
  labels.
- Keep the product's prestige cues in typography, spacing, hierarchy, and
  restraint before adding more decoration.

## Serve Peers

- Give the web steward token, component, responsive, and interaction guidance
  before UI work hardens.
- Give docs/product stewards canonical design language for Appearance Studio,
  information hierarchy, control topology, and navigation decisions.
- Give domain and service stewards clearer requirements when visual behavior
  depends on story state, active face, membership role, privacy, or queue
  status.
- Give tests steward stable visual semantics that can be asserted without
  brittle pixel coupling.
- Ask research and user-panel work for evidence when product taste claims need
  validation with active writers, directors, applicants, or hook hunters.

## Do Not

- Treat Chirp-UI as the whole design system; it is the structural library, not
  the full Elbysodic product voice.
- Add raw CSS, arbitrary template controls, external font URLs, or scriptable
  design inputs to community-facing customization.
- Let atmospheric styling reduce prose readability, focus visibility, tap
  targets, or staff/private-data clarity.
- Use neon glow, gradients, glass, image overlays, or motion as a substitute for
  hierarchy.
- Let every datum become a pill, card, badge, or decorative panel.
- Create a generic SaaS dashboard, social network, archive, or forum-skin
  aesthetic.
- Override membership, character, community, permission, or privacy boundaries
  for visual convenience.

## Own

- `design/`
- product-design interpretation of `src/elbysodic/web/static/elbysodic-theme.css`
- visual vocabulary in coordination with `docs/product/information-hierarchy.md`
- Appearance Studio design-system guidance in coordination with
  `docs/product/appearance-studio.md`
- component promotion guidance for `src/elbysodic/web/pages/_components/`
- browser QA notes and design review findings for substantial UI changes
