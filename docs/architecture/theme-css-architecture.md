# Theme CSS Architecture

Elbysodic keeps one public app theme entrypoint:

```text
src/elbysodic/web/static/elbysodic-theme.css
```

That file is an import manifest. The owned CSS lives in
`src/elbysodic/web/static/elbysodic-theme/` and is split by responsibility,
not by whichever page first needed the selector.

## Ownership Layers

Use these layers when adding or moving CSS:

- **tokens**: Elbysodic brand, state, motion, density, media, and remaining
  Chirp-UI token aliases during the ADR 0002 drain. This layer may define CSS
  custom properties and base document defaults, but should not define product
  components.
- **chirp-primitives**: migration overrides for leftover `chirpui-*` markup.
  Drain toward Elbysodic primitive classes; do not add new Chirp-UI bridges.
- **shell**: app chrome, sidebar, top navigation, mobile drawer, route tabs,
  identity menu, notification shell affordances, and global navigation
  behavior.
- **page-patterns**: reusable route-level page vocabulary shared across public,
  member, board, and Studio surfaces: world heroes, local rails, command panels,
  page pulses, empty policy blocks, preview rows, copy styles, and listing
  grids.
- **media-patterns**: repeated frame and image mechanics for posters, board
  media slots, hero media, and catalog media. Product-family files still own
  overlays, fallback typography, aspect ratios, and hover behavior.
- **page-compositions**: broad page layouts and temporary composition surfaces
  that are not yet stable product components. This should stay small and act as
  a review queue, not a permanent home.
- **pbp-components**: shared roleplay-native product components that cross
  families, currently broad notices, notification surfaces, and recovery UI.
  Product-family components live in numbered sibling layers:
  `41-boards-places.css`, `42-threads-queues.css`,
  `43-faces-composer.css`, `44-claims-intake.css`,
  `45-posts-scenes.css`, `46-world-materials.css`, `47-network.css`,
  `47-network-catalog.css`, `48-wanted-plotting.css`, and `49-composer.css`.
- **network**: public Network home, billboards, home rails, genre slices, and
  signed-in return panels.
- **network-catalog**: Network search, browse lanes, realm cards, catalog
  editorial panels, and application entry/facet surfaces.
- **composer**: writer input surfaces, formatting controls, body mention
  pickers, scene setup fields, draft status, and post style previews. Rendered
  post shells and scene cast displays stay in `45-posts-scenes.css`.
- **studio**: Director Studio, launch, operations, intake, appearance editor,
  navigation composer, board map, and director workflow rooms.
- **legacy-ledger**: selectors that still need markup work, component
  extraction, or Chirp adoption. The ledger should shrink over time.

Responsive overrides live in the same layer as the selector they adapt. Do not
add a catch-all responsive file unless it is a short-lived migration staging
step that is immediately drained back to owner layers.

## Primitive Rule (ADR 0002)

Before adding an Elbysodic selector that styles a primitive UI shape, prefer an
existing Elbysodic primitive or `_components/` pattern:

- buttons, badges, cards, fields, and overlays are Elbysodic-owned. Do not add
  new `chirpui-*` classes or `--chirpui-*` custom properties.
- leftover `chirpui-*` markup is a drain queue, not a pattern to copy.
- PBP-semantic objects (wanted hook card, face card, thread state lane, claim
  row, director queue) stay Elbysodic-named even while a leaf still maps old
  Chirp-UI classes underneath.

## Decomposition Rule

Moving CSS is not enough. Every touched selector should be classified as one of:

- **Elbysodic primitive**: buttons, fields, cluster, stack, surface chrome
  owned by theme tokens / primitive CSS (ADR 0002).
- **Elbysodic PBP component**: keep and move into the named product layer.
- **Page composition**: keep temporarily with a clear route/surface owner.
- **Legacy**: leftover `chirpui-*` listed in the ledger with a drain path.

This keeps the CSS split aligned with the product architecture instead of only
making the file tree look cleaner.

## Shared Pattern Ownership

Use this table before adding a new card, row, poster, metric, or editor shell:

| Pattern | Owner | Rule |
|---|---|---|
| Generic panel/card chrome | Elbysodic primitive / surface | Use Elbysodic classes; do not add new `chirpui-*` chrome. |
| Product card body/layout | Product-family CSS | Boards, threads, faces, wanted hooks, claims, world materials, Network, and plotting own their internal grids and PBP labels. |
| Media poster/fallback/overlay | Product-family CSS until shared behavior repeats across three families | Board, thread, character, post, and Network posters currently have different content and interaction contracts. |
| Metric/signal rows | `_components/vocabulary.html` plus product-family wrappers | Use `metric()` and Elbysodic badges/counts; keep wrappers for needs reply, waiting, caught up, staff, and director signal language. |
| Page command, pulse, preview, empty policy | `30-page-patterns.css` | These are route-level page vocabulary, not product-family cards. |
| Form primitive | Elbysodic field classes | Product CSS may arrange fields; labels/inputs/tone come from Elbysodic primitives, not new Chirp-UI field classes. |
| Responsive override | Owning CSS file | Put the media query after the base selector in the same family file. |

If a selector only sets background, border, radius, padding, hover elevation, or
form/control chrome, add or reuse an Elbysodic primitive. If a selector encodes
PBP state, identity, authorship, continuity, or staff visibility, keep an
Elbysodic wrapper. Do not expand Chirp-UI usage.

## Browser QA Coverage

Use the app check and unit tests for ownership and route contracts, then run
browser QA when a cleanup changes layout, interaction, or responsive behavior.

```bash
uv run poe preview-prod-devtools
uv run poe latest-click-wins-qa
uv run poe browser-qa-deep --base-url http://127.0.0.1:8001
```

The deep browser pass should keep covering these CSS ownership slices:

| Layer | Routes/Flows To Exercise |
|---|---|
| `20-shell.css` | root, Network, community home, board, thread, boosted navigation, identity menu |
| `30-page-patterns.css` | root, community home, writer desk, world, dev personas, operations summary |
| `35-media-patterns.css` | board posters, character cards, rendered posts, Network cards, world hero media |
| `40-pbp-components.css` | notices, metrics, inline mention links, notifications/recovery |
| `41-48` product families | board index/detail, thread list/detail, members/roster, claims, wanted, world, Network catalog |
| `47-network-catalog.css` | `/network`, `/network?q=...`, realm entry actions, application starter |
| `49-composer.css` | new thread, reply composer, post edit, scene setup/cast mention picker, post style preview |
| `60-studio.css` | Studio overview, launch, operations, intake, appearance, board map |

When a browser failure appears after CSS movement, first check whether the
selector lives in the same layer as the markup flow above. Cross-layer selectors
should either move to their product family, become a shared pattern, or reduce
to a Chirp primitive.
