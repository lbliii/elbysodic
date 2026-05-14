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
- **page-compositions**: broad page layouts and temporary composition surfaces
  that are not yet stable product components.
- **pbp-components**: roleplay-native product components: faces, threads,
  scenes, wanted hooks, claims, reserves, boards, rosters, staff queues,
  writer obligations, and director material cards.
- **utilities**: small reusable helpers that do not encode a product concept.
- **legacy-ledger**: selectors that still need markup work, component
  extraction, or Chirp adoption. The ledger should shrink over time.

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
