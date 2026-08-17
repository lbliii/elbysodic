# Technicolor Futurism

Technicolor futurism is Elbysodic's default product art direction. It should
feel luminescent, clean, striking, and editorially prestigious while remaining
quiet enough for long-form writing and staff work.

The intent is not retrofuturism, arcade neon, cyberpunk grime, or generic
glassmorphism. The product should feel like a modern studio layer for
pseudonymous roleplay: sharp surfaces, confident color, legible prose, strong
identity moments, and enough restraint that writers can stay with a scene for
hours.

Use `design/technicolor-futurism-research.md` as the source-backed companion to
this doctrine. It explains why Technicolor means controlled chroma,
registration, dye layering, and color direction rather than indiscriminate
saturation.

## Pillars

1. Reading Is The Prestige Surface

   Threads, guidebook pages, applications, wanted hooks, and staff notes must
   read beautifully before they look dramatic. Typography, measure, line
   height, paragraph rhythm, and contrast carry more prestige than decoration.

2. Color Behaves Like Light

   Accent color should feel luminous and intentional: signal, focus, identity,
   active face, current scene, or atmospheric pressure. Avoid spraying glow
   across every border, card, and badge.

3. Editorial Hierarchy Beats Dashboard Density

   Elbysodic can be operational without feeling like enterprise software.
   Production rooms, queues, rosters, and claims need clean scan paths, stable
   controls, and clear state. The hierarchy should feel edited, not merely
   arranged.

4. Character Identity Stays Human

   Face, roster, wanted, claim, reserve, and postbit surfaces should make
   public authorship and story context obvious. Visual polish must never make
   it easier to post as the wrong face or lose track of scene context.

5. Atmosphere Is Product-Owned

   Directors can shape community mood through approved tokens, media slots,
   density, texture, and presentation variants. They should not need raw CSS,
   arbitrary templates, scripts, or unsafe font loading to make a board feel
   alive.

6. Glass Is A Hierarchy Material

   Glass treatment belongs where it clarifies layers: topbar, transient menus,
   selected overlays, preview scrims, media captions, and focused control
   surfaces. It should not become nested frosted cards or a full-page blur
   blanket. Long-lived reading and writing surfaces need stable opacity.

7. Every Community Gets A Color Score

   Borrowing from Natalie Kalmus's sequence-by-sequence color planning,
   community art direction should be expressible as a structured score:
   key neutral, identity dye, atmosphere dye, state dyes, surface intensity,
   material use, and restraint rules. This can help a director generate a
   coherent board without raw CSS or skin work.

## Relationship To Chirp

Keep Chirp + Kida + HTMX + Alpine. Chirp-UI is leftover, not the foundation
(ADR 0002). Elbysodic owns primitives and PBP components in
`src/elbysodic/web/pages/_components/` and
`src/elbysodic/web/static/elbysodic-theme.css`. The design system layer
adds:

- product-specific token aliases and defaults
- PBP component vocabulary
- editorial composition rules
- mood and media guidance
- state language for writing workflows
- Appearance Studio constraints and warnings

When a visual decision cannot be expressed through existing Elbysodic
tokens, prefer adding a small Elbysodic token with product meaning in
`src/elbysodic/web/static/elbysodic-theme.css`. Do not create page-local
color systems that bypass the theme. Do not add new `chirpui-*` classes
or `--chirpui-*` aliases.

## Token Direction

Use token names that describe product function rather than raw appearance.

Good token purposes:

- canvas, surface, elevated surface
- prose text, muted metadata, on-media text
- identity accent, secondary accent, warning, error, success
- focus ring, active face, private/staff state
- editorial rule, media overlay, atmospheric texture

Avoid token purposes that encode one decorative treatment too early:

- neon-card-border
- cyber-glow
- purple-gradient
- glass-panel
- cool-shadow

The current theme can evolve away from warm paper and rose/moss defaults toward
a more luminous product palette, but the bar is readability first. Any palette
shift should be checked across thread prose, board cards, Studio rooms, wanted
hooks, applications, and staff/private notices.

## Palette Architecture

Technicolor futurism should be built like a registered print, not a rainbow.

1. Black key

   A deep neutral structure gives type, rules, outlines, shadows, and surface
   edges their crispness. In UI terms, this is the contrast system: canvas,
   text, border, focus containment, and on-media legibility.

2. Dye records

   Cyan, magenta, yellow, and their near-neighbor harmonies become controlled
   accent families. They should be strong enough to feel luminous, but each
   usage needs a job: identity, action, state, event pressure, or editorial
   emphasis.

3. Registration

   Technicolor's precision becomes product composition: clean alignment,
   consistent spacing, stable component dimensions, sharp focus states, and
   no accidental edge seams.

4. Harmonized restraint

   High chroma appears in small, meaningful quantities. Prose backgrounds,
   Studio forms, staff notes, and application review rooms stay quieter than
   gateway, board, wanted, event, and character identity surfaces.

Suggested starting families for exploration, not implementation doctrine:

| Role | Direction | Use |
| --- | --- | --- |
| Key dark | blue-black, ink-black, near-neutral graphite | canvas, type contrast, shell |
| Key light | cool porcelain, soft white, luminous mist | light theme canvas, content layer |
| Cyan record | electric cyan, peacock, aqueous blue-green | focus, links, active systems |
| Magenta record | spectral magenta, fuchsia, rose-violet | identity, face accents, selected state |
| Yellow record | clean amber, chartreuse-yellow, sodium gold | warnings, event pressure, highlights |
| Green bridge | emerald, mint signal, oxidized teal | success, fresh activity, safe state |
| Red pressure | vermilion, signal coral | errors, destructive state, urgent notices |

## Color Score Model

Use `design/art-direction-program.md` for the working structured model. The
short version:

- `key`: the neutral contrast system that protects prose and editorial polish.
- `identity_dye`: the primary expressive accent for community, face, or world
  identity.
- `atmosphere_dye`: the mood color used most often on ritual surfaces.
- `state_dyes`: reserved colors for success, warning, error, private, staff,
  watching, caught up, waiting, and needs reply.
- `surface_intensity`: a per-surface budget for how much chroma, media,
  texture, motion, and glass a screen may carry.
- `restraint_rule`: the reason a board does not use all of its colors at once.

## Composition Rules

- Put prose and story context in the calmest part of the page.
- Use strong media at ritual surfaces: world gateway, board/location, character
  hub, wanted hooks, guidebook materials, and event notices.
- Keep command surfaces dense but edited: fewer decorative panels, clearer
  grouping, stable controls, and direct next actions.
- Make active face and authorship visible near posting and reply workflows.
- Use color for signal and identity before decoration.
- Prefer sharp editorial rhythm over oversized marketing sections.
- Let the next section peek into view on atmospheric first viewports so the
  page feels like a working product, not a landing poster.
- Use glass or translucency to reveal relationship between layers, not to make
  every surface look expensive.
- Avoid edge-to-edge translucent panes that create seams, striping, or noisy
  overlap on dense production screens.

## Interaction Rules

- Focus states must be visible against both dark and light theme values.
- Hover states should reinforce clickability without causing layout shift.
- Motion should be brief, purposeful, and optional under reduced motion.
- Icon-only controls need accessible names and recognizable forms.
- Dense controls should stay reachable by keyboard and touch.
- Destructive, private, staff-only, locked, and archived states must be clear
  without relying on color alone.
- Transient glass surfaces need solid fallbacks for reduced transparency, high
  contrast, low-power, and unsupported environments.

## Component Translation

- App shell: mostly opaque, with controlled luminous edges and a possible
  Mica-like base treatment. Navigation should feel calm and persistent.
- Topbar/sidebar: restrained translucency is acceptable when it keeps page
  context visible and text contrast remains strong.
- Menus/popovers: best fit for glass. They are transient, context-linked, and
  should dismiss cleanly.
- Cards: use solid or lightly tinted surfaces first. Add glass only when a card
  overlays media or needs a specific foreground/background relationship.
- Postbit/thread prose: avoid glass behind body copy. Use the black-key layer
  for clarity and small dye-record accents for face, scene, and state.
- Wanted/event/board heroes: use the most expressive media, color, and light,
  but keep actions and metadata registered to a stable grid.
- Studio/application/staff rooms: editorial, crisp, and low-noise. Use color
  for state and routing, not ambience.

## Review Questions

Ask these before accepting a UI or theme change:

- Does this feel purpose-built for PBP, or could it be any SaaS dashboard?
- Can a writer read a long thread here without fighting the styling?
- Is the active face, scene, queue state, or staff/privacy boundary clearer?
- Are Elbysodic tokens and `_components/` doing the structural work?
- Is any new visual language repeated enough to become a component?
- Does the page still work on mobile as a designed surface?
- Are color, glow, blur, media, or motion serving hierarchy rather than noise?
- Would a director feel the default board has taste before customization?

## Not Yet Decided

These choices need future exploration and proof before becoming implementation
doctrine:

- the exact default dark and light palette for technicolor futurism
- whether Elbysodic needs a named display type stack beyond system fonts
- which ritual surfaces should get the first presentation variants
- how much luminosity belongs in staff-heavy operational rooms
- whether product screenshots or browser QA should be archived under `design/`
