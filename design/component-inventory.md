# Component Inventory And Surface Budgets

This inventory grounds technicolor futurism in the current rendered product. It
is design-system execution guidance, not a new public route, Blueprint, schema,
or Appearance Studio contract.

Use it before changing `src/elbysodic/web/static/elbysodic-theme.css` or
promoting page-local UI into `src/elbysodic/web/pages/_components/`.

## Current Product Layer

Elbysodic already has a real product-design layer. Chirp-UI leftovers remain
in templates and token aliases; they are an exit target (ADR 0002), not the
foundation:

- Elbysodic primitives and `_components/` own structure going forward.
  Leftover Chirp-UI names (`surface`, `badge`, `avatar`, `avatar_stack`,
  `timeline`, `description_list`, buttons, chips, fields, clusters, stacks,
  breadcrumbs, and tooltips) still appear in markup as a migration layer
  to drain.
- Elbysodic theme tokens map product colors, prose, focus, shell, media,
  card, radius, and shadow behavior in
  `src/elbysodic/web/static/elbysodic-theme.css`. Leftover `--chirpui-*`
  names are aliases to drain, not new foundation tokens.
- Shared PBP concepts are partially promoted into
  `src/elbysodic/web/pages/_components/`.
- Ritual surfaces already exist for world, board/location, thread, character,
  wanted, event, and network contexts.

The current weakness is not lack of UI. It is that the design vocabulary is
unevenly codified: some surfaces are named macros, some are large CSS regions,
and some are repeated card patterns that need clearer product roles.

## Shared Component Map

| Component File | Current Role | Design Category | Notes |
| --- | --- | --- | --- |
| `_components/boards.html` | board posters, latest lines, board stats, subboards, community rows | Ritual surface, discovery, navigation | Strong media identity; needs surface-intensity alignment and tokenized on-media treatment. |
| `_components/posts.html` | post profile rail, post frame, author media, post body | Reading surface, face identity | Good separation between public author identity and prose; protect opacity behind body copy. |
| `_components/composer.html` | composer controls, active face, preview behavior | Reading/writing surface | Motion and feedback should be low and precise; active face clarity is a hard gate. |
| `_components/wanted.html` | wanted hook cards and related faces | Ritual surface, casting | Needs more editorial desire/casting energy without exposing private interest state. |
| `_components/plot_hooks.html` | plotter and hook summaries | Ritual/plotting surface | Should share wanted/backstage state language. |
| `_components/thread_summary.html` | scene preview and thread summaries | Reading movement, queue/discovery | Good place for needs-reply/watching/caught-up state styling. |
| `_components/sidebar.html` | realm navigation, local community movement | Shell/navigation | Candidate for restrained glass and active-state dye, with reduced-transparency fallback. |
| `_components/facets.html` | director-defined lenses | Metadata/filter surface | Facets should stay quieter than actions unless actively filtering. |
| `_components/ui.html` | counters, local rails, latest lines, meta hints, event bridge, state badges | Vocabulary support | Should remain the semantic home for compact repeated PBP signals. |
| `_components/post_style_preview.html` | Appearance Studio post preview | Appearance preview | Useful proof surface for color score and postbit variants. |
| `_components/vocabulary.html` | promoted command panels, lanes, metrics, rooms | Production surface | Good base for Studio/desk hierarchy; avoid generic dashboard drift. |

## Surface Intensity Budget

| Surface | Budget | Chroma | Motion | Glass | Required Protection |
| --- | --- | --- | --- | --- | --- |
| World gateway | High | identity + atmosphere dyes | medium | media captions/topbar only | next section visible, readable hero copy |
| Network billboard/cards | High | network accent + atmosphere | medium | icon actions/captions only | not seed-specific as product doctrine |
| Board/location | High | atmosphere + relevant-face signal | medium | captions only | board hierarchy, private-board state |
| Thread stage | Medium | scene state + cast accents | low | avoid | scene metadata and next action |
| Thread body | Low | author accent only | none-low | never | prose measure, contrast, no layout shift |
| Composer | Low | active face + validation | low | never | active face, draft/preview parity |
| Character hub | Medium-high | face identity dye | medium | poster overlay only | ownership actions, profile privacy |
| Wanted hooks | High | desire/casting + state | medium | media overlay only | reserve/interest workflow clarity |
| Plotting/backstage | Medium | plotting state + participants | low-medium | avoid except transient controls | private notes and handoff state |
| Guidebook/material | Medium-high | canon/event accent | low-medium | cover/media captions only | long prose readability |
| Event notice | High | warning/event pressure | low-medium | avoid on text | warning semantics and action placement |
| Studio rooms | Low | routing/state only | low | transient controls only | labels, validation, staff access |
| Applications/claims | Low | review/state only | low | never | staff review privacy and trust |
| Staff/private/recovery | Lowest | boundary/state only | lowest | never | safety, clarity, no drama |

## Token Roles To Add Or Audit

Current CSS still maps leftover Chirp-UI core tokens. The next token pass
should audit or introduce Elbysodic aliases for product meaning and stop
adding `--chirpui-*` aliases:

- `--elbysodic-key-dark`
- `--elbysodic-key-light`
- `--elbysodic-identity-dye`
- `--elbysodic-atmosphere-dye`
- `--elbysodic-active-face`
- `--elbysodic-state-needs-reply`
- `--elbysodic-state-waiting`
- `--elbysodic-state-caught-up`
- `--elbysodic-state-watching`
- `--elbysodic-state-private`
- `--elbysodic-state-staff`
- `--elbysodic-editorial-rule`
- `--elbysodic-glass-bg`
- `--elbysodic-glass-border`
- `--elbysodic-motion-*`

These aliases should feed Elbysodic component CSS. They should not become
director-editable contract fields until Appearance Studio and Blueprint
contracts are explicitly reviewed. Do not add new `--chirpui-*` aliases.

## First Canonical Proof Patterns

Use small proofs before broad redesign:

1. Palette proof: default theme token map in `elbysodic-theme.css`.
2. Motion proof: menu/popover glass resolve and composer preview toggle.
3. Reading proof: thread body and composer remain calm in all modes.
4. Ritual proof: board poster and wanted hook carry stronger identity.
5. Production proof: applications/claims/Studio stay crisp and low-noise.

## QA Matrix

Every visual implementation based on this inventory should check:

- Desktop and mobile.
- Light, dark, and system modes.
- With media and without media.
- Long titles, long names, many facets, many badges.
- Thread body, composer, active face, post profile rail.
- Wanted hook, board/location, character hub.
- Studio room, applications/claims, staff/private notice.
- Keyboard focus and touch behavior.
- `prefers-reduced-motion: reduce`.
- Reduced transparency or unsupported backdrop-filter fallback.

## Not-Now

- No design-system playground route yet.
- No Blueprint, schema, import/export, CLI, or public Appearance Studio fields.
- No raw CSS or template controls.
- No route transition system.
- No animation library.
