# Design

This folder is the home for Elbysodic's product design steward: the agent that
cares about the design system, visual direction, product polish, interaction
quality, and how Chirp (Kida + HTMX + Alpine) plus Elbysodic primitives
become a PBP experience instead of a generic component library.

Chirp gives Elbysodic the bones: filesystem pages, Kida templates, HTMX
boosting, and Alpine islands. This folder defines the product layer:
art direction, composition, hierarchy, editorial rhythm, PBP-specific visual
vocabulary, and the standards for when a pattern should become shared product
design. Chirp-UI is an exit target (ADR 0002), not the foundation.

Current direction:

- Name: technicolor futurism.
- Mood: luminescent, clean, striking, and tasteful.
- Priority: reading first, then character identity, then operational clarity,
  then atmosphere.
- Prestige cue: editorial hierarchy, sharp restraint, high-quality defaults,
  and confident color rather than decorative clutter.

## What Belongs Here

- Product design principles and visual direction.
- Design-system rules for Elbysodic tokens and primitives (ADR 0002).
- Component vocabulary guidance before patterns move into
  `src/elbysodic/web/pages/_components/`.
- Review checklists for UI, theme, responsive, media, accessibility, and
  editorial polish.
- Notes that help future agents preserve the product's taste and PBP-native
  identity.

## What Does Not Belong Here

- Raw CSS that should live in `src/elbysodic/web/static/elbysodic-theme.css`.
- Product behavior docs that belong in `docs/product/`.
- Architecture, schema, service, repository, or privacy contracts that belong
  in their scoped steward areas.
- Scratch inspiration dumps that have not been distilled into decisions.

## How To Use This Folder

For UI or product-design work, read `design/AGENTS.md` and the nearest scoped
`AGENTS.md` for the implementation area. For major UX, onboarding,
navigation, writing-flow, Studio, Appearance Studio, wanted/backstage,
application, claim, reserve, or public discovery changes, also consult
`docs/product/user-personas-panel.md`.

For design-system changes, update the relevant design note here, then implement
the token or component change in the web layer. Design guidance should not
pretend a behavior exists until code, tests, or product docs support it.

## Current Notes

- `art-direction-program.md`: a programmatic model for translating a
  community's premise into a safe art-direction score.
- `brand/`: durable selected brand assets and usage notes after logo
  exploration settles into a production direction.
- `component-inventory.md`: current shared component map, surface-intensity
  budgets, token roles, and QA matrix for visual implementation.
- `composition-bible.md`: living composition doctrine for page rhythm, surface
  ladder, layered chrome, media use, mobile layout, and bad patterns.
- `circle-terminals-token-map.md`: accepted token roles for translating the
  Circle Terminals mark into default theme color and state language.
- `community-landing-archetype-stress-pass.md`: V2.1 stress pass that applies
  premise-archetype research to the public community landing mock before
  production translation.
- `image-dimensions.md`: aspect-ratio map for Midjourney-style image
  generation and product media surfaces.
- `motion-design.md`: animation and transition guidance for technicolor
  futurism, PBP reading flow, and reduced-motion-safe interaction design.
- `rendered-qa-pass.md`: latest rendered QA notes, accepted fixes, and
  deferred visual risks.
- `sidebar-icon-vocabulary.md`: canonical SVG icon set and route mapping for
  sidebar destinations, compact rail behavior, and Studio/Desk route cleanup.
- `../docs/product/experience-direction.md`: concise product-experience
  synthesis for the current Jcink/PBP, Slack-like layered context,
  Netflix/Apple TV editorial discovery, RPHub polish, and technicolor futurism
  direction.
- `static-community-landing-v2-mock.html`: static V2 prototype for a public
  realm gateway at `/c/x-men-apocalypse`.
- `static-community-landing-v2-notes.md`: research, design rationale, accepted
  moves, read-model implications, and proof needed for the community landing
  V2 prototype.
- `static-community-landing-v2-archetype-mock.html`: static V2.1 archetype
  stress mock with switchable no-event social, gated mystery, and institution
  pressure gateway states.
- `static-scene-context-mock.html`: static prototype for a scene-in-location
  reader with a minified location lane, grounding inspector, PBP hovercard, and
  writer activity drawer.
- `static-scene-context-mock-notes.md`: product-design notes for the scene
  context prototype and its Slack/Discord pattern boundaries.
- `static-shell-mock.html`: static layered shell mock for the accepted icon rail
  plus inner-shell model.
- `static-shell-mock-notes.md`: review notes for the static shell mock and
  implementation lessons to carry forward.
- `static-shell-mock-v2.html`: implementation-oriented shell mock using
  Chirp/Elbysodic class vocabulary and inline SVG placeholders.
- `static-shell-mock-v2-notes.md`: component candidates and review notes for
  the V2 shell mock.
- `terminology-map.md`: UX writing conventions for PBP terms such as scene,
  thread, face, roster, guidebook, canon, wanted, claims, and reserves.
- `technicolor-futurism.md`: the working design doctrine.
- `technicolor-futurism-roadmap.md`: a phased roadmap for moving the current
  theme, components, QA, and Appearance Studio direction toward the doctrine.
- `technicolor-futurism-research.md`: source-backed notes on Technicolor,
  color theory, futurism, glass materials, and component translation.
