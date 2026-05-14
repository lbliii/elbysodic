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

- **tokens**: Elbysodic brand, state, motion, density, media, and Chirp-UI token
  mappings. This layer may define CSS custom properties and base document
  defaults, but should not define product components.
- **chirp-primitives**: narrow Elbysodic theming overrides for Chirp-UI
  primitives. Prefer Chirp's native tone and appearance classes before adding a
  custom override.
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
  `48-wanted-plotting.css`, and `49-composer.css`.
- **composer**: writer input surfaces, formatting controls, body mention
  pickers, scene setup fields, draft status, and post style previews. Rendered
  post shells and scene cast displays stay in `45-posts-scenes.css`.
- **studio**: Director Studio, launch, operations, intake, appearance editor,
  navigation composer, board taxonomy, and director workflow rooms.
- **legacy-ledger**: selectors that still need markup work, component
  extraction, or Chirp adoption. The ledger should shrink over time.

Responsive overrides live in the same layer as the selector they adapt. Do not
add a catch-all responsive file unless it is a short-lived migration staging
step that is immediately drained back to owner layers.

## Chirp Adoption Rule

Before adding an Elbysodic selector that styles a primitive UI shape, check
whether Chirp-UI already owns the shape:

- buttons: use Chirp button size, tone, and appearance classes.
- badges/chips: use Chirp badge or facet-chip classes unless the text carries a
  PBP lifecycle meaning that needs an Elbysodic wrapper.
- cards/surfaces: use Chirp card/surface tone and appearance classes for generic
  panels. Keep Elbysodic wrappers for PBP concepts.
- fields: use Chirp field tone and appearance classes for form state.
- overlays: use Chirp z-index tokens before introducing local numeric layers.

When the component is product-semantic, compose Chirp primitives underneath an
Elbysodic name. A wanted hook card, face card, thread state lane, claim row, or
director queue is Elbysodic-owned even if its border, badge, or button comes
from Chirp.

## Decomposition Rule

Moving CSS is not enough. Every touched selector should be classified as one of:

- **Chirp primitive**: replace or reduce local CSS with Chirp classes/tokens.
- **Elbysodic PBP component**: keep and move into the named product layer.
- **Page composition**: keep temporarily with a clear route/surface owner.
- **Legacy**: list in the ledger with the intended replacement path.

This keeps the CSS split aligned with the product architecture instead of only
making the file tree look cleaner.

## Shared Pattern Ownership

Use this table before adding a new card, row, poster, metric, or editor shell:

| Pattern | Owner | Rule |
|---|---|---|
| Generic panel/card chrome | Chirp `surface` or `card` | Use Chirp appearance and tone classes; keep an Elbysodic class only for product semantics. |
| Product card body/layout | Product-family CSS | Boards, threads, faces, wanted hooks, claims, world materials, Network, and plotting own their internal grids and PBP labels. |
| Media poster/fallback/overlay | Product-family CSS until shared behavior repeats across three families | Board, thread, character, post, and Network posters currently have different content and interaction contracts. |
| Metric/signal rows | `_components/vocabulary.html` plus product-family wrappers | Use `metric()` and Chirp badges/stats where possible; keep wrappers for needs reply, waiting, caught up, staff, and director signal language. |
| Page command, pulse, preview, empty policy | `30-page-patterns.css` | These are route-level page vocabulary, not product-family cards. |
| Form primitive | Chirp field classes | Product CSS may arrange fields, but labels/inputs/tone/appearance should come from Chirp. |
| Responsive override | Owning CSS file | Put the media query after the base selector in the same family file. |

If a selector only sets background, border, radius, padding, hover elevation, or
form/control chrome, try Chirp first. If a selector encodes PBP state,
identity, authorship, continuity, or staff visibility, keep an Elbysodic
wrapper and compose Chirp underneath it.
