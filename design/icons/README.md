# Faces & Threads

Elbysodic's app-owned icon family connects the Circle Terminals identity to
roleplay work: circular faces, lines of writing, open story frames, and paths
between collaborators. The set contains **52 original symbols**: the existing
33 product concepts, redrawn under their stable IDs, plus 19 utilities.

- [Interactive specimen](index.html): search, light/dark surfaces, actual-size
  controls, interface example, and a previous/new comparison for the 33 core
  symbols. Serve the repository over HTTP so external SVG references load.
- [Production sprite](../../src/elbysodic/web/static/icons/sidebar.svg).
- [Download the SVG kit](elbysodic-faces-and-threads.zip): 52 standalone SVGs,
  the sprite, and usage notes. This is a v1 export snapshot; regenerate it from
  the canonical production sprite when artwork changes.
- [Previous sprite](sidebar-before.svg): an inventory snapshot for comparison,
  not a second production family.
- [Sidebar vocabulary](../sidebar-icon-vocabulary.md): destination semantics
  and navigation rules.

## Inventory before replacement

The repository contained **157 SVG files**, excluding installed dependencies:

The [complete inventory](inventory.json) lists every path, asset role, and the
original sprite's symbol IDs.

| Role | Files | Location |
|---|---:|---|
| Served platform brand | 6 | `web/static/brand/` |
| UI sprite | 1, with 33 symbols | `web/static/icons/sidebar.svg` |
| Seed realm artwork | 50: 14 marks, 14 heroes, 22 locations | `web/static/seed-media/` |
| Canonical brand masters | 10 | `design/brand/circle-terminals/` |
| Archived logo exploration | 90 | `design/logo-options/archive/2026-05-circle-terminals-exploration/` |

The `web/` paths above are under `src/elbysodic/`. Counts describe the baseline,
before adding this specimen's comparison snapshot. Separate untracked realm
artwork was not part of the icon replacement.

Only 15 of the 33 symbols were referenced by `web/navigation.py`. Meanwhile,
14 `| icon` call sites across six templates used ChirpUI Unicode glyphs for
board types, active-face overlays, network card actions, scene controls, and
reply counts. One was an unused legacy sidebar macro. This mixed SVG outlines
with font-dependent marks: `user` became ⊙, `chat` and `watch` both became ◉,
and `logs` became ⟳. Counts also used T/P/R, and the composer used B/I/>/[].
No dedicated third-party SVG icon library was present.

## Drawing language

Every symbol uses a `0 0 24 24` viewBox, a 1.75-unit stroke, rounded caps and
joins, and `currentColor`. The default fill is `none`; selected small circular
terminals explicitly use `fill="currentColor"` and `stroke="none"`. Icons
contain no text, gradients, scripts, embedded images, or external artwork.
There is no new runtime dependency.

Openings and circular terminals connect the set to the brand without turning
every icon into a logo. Recognizable utilities remain simple. Related product
concepts have distinct structures:

| Concepts | Visual distinction |
|---|---|
| Home / locations / world | Realm gate / folded map with a point / open globe |
| Wanted / casting | Open story hook / face inside an open casting frame |
| Face / roster / members / community | Posting identity / stacked face cards / writer register / faces at a shared table |
| Network / plotting / continuity | Writers in orbit / story branches converging / linked beats in sequence |
| Desk / studio / operations | Writing desk and pen / director controls in a diamond / running order |
| Claims / reserves / applications | Checked claim tag / bookmark and clock / face in draft |
| Scene / boards / guidebook / materials | Alternating lines in a story frame / open scene shelves / open reference / collected pages |
| Launch / intake / artifacts | Opening a door / page entering review / preserved fragment |
| Appearance / events / notifications | Three adjustable color records / marked date / new signal on a bell |
| Discovery / queue / inbox / settings | Open compass / next reply / correspondence / adjustment gear |

## Template use and sizing

Use the shared macros in `web/pages/_components/icons.html` rather than inline
paths or the ChirpUI glyph filter:

```jinja
{% from "_components/icons.html" import icon, icon_counter %}

<button type="button">{{ icon("watch") }} Watch thread</button>
{{ icon_counter("reply", reply_count, "replies") }}
```

`icon(name, size="md", cls="")` loads `elbysodic-icon-{name}` from the
versioned production sprite. Sizes are `sm` = 1rem, `md` = 1.25rem, and `lg` =
1.5rem: 16, 20, and 24 pixels at the default root size. The sidebar retains its
1.35rem footprint through `elbysodic-sidebar-svg-icon`. Styling lives in
`elbysodic-theme/15-app-utilities.css`; the sidebar override is in
`20-shell.css`. Color is inherited from the owning surface or control.

The macro's SVG is always decorative (`aria-hidden="true"`,
`focusable="false"`). Its owner must supply the meaning through visible text
or an accessible name. Icon-only controls also need a hover/focus tooltip;
PBP-specific actions retain labels. `icon_counter` renders the value with a
visually hidden count label. Never use an icon alone to communicate a privacy,
permission, or workflow state.

The 19 utility IDs are `add`, `arrow-down`, `arrow-right`, `close`, `watch`,
`reply`, `write`, `archive`, `search`, `check`, `more`, `menu`, `panel`, `sun`,
`moon`, `system`, `log-out`, `link`, and `lock`. A utility being available does
not imply every corresponding control has been migrated.

## Integration scope

The family covers shell navigation, community board marks and face overlays,
board and scene counts, network card actions, and scene join/watch/latest,
context, and locked-state controls. Labels, actions, navigation visibility,
and role boundaries remain owned by their existing components and read models.

Platform brand assets, community logos, seeded hero/location illustrations,
and archived logo studies remain separate artwork. Dependency-owned theme
toggle and drawer glyphs, composer formatting marks, back-link arrows, notice
marks, and other text/CSS signals are not all migrated. Do not claim that every
visible symbol in the application comes from this sprite.

For future additions, check distinctness against neighboring concepts at 16,
20, and 24 pixels on light and dark surfaces, then inspect the actual control
and mobile layout. The specimen supports that review; it is not proof of
application browser QA.

Keep the production sprite as the artwork source of truth. After changing it,
advance the version in the shared icon macro and regenerate the standalone
ZIP export. Preserve existing symbol IDs so older templates keep working.

## Visual review — 2026-09-24

Reviewed the specimen at 16, 20, and 24 pixels on light and dark surfaces.
Widened the scene frame, separated portrait heads from shoulder strokes, and
gave Operations a production-slate silhouette distinct from Queue. Verified
the live Studio rail, community marks and counters, and mobile navigation
drawer against an isolated local demo database. The specimen was also checked
at a 390-pixel viewport with no horizontal overflow.

Migrated board-hero counter color rules to the owned component and verified
light-theme counters over artwork: numbers use `--elbysodic-on-media-text`,
and SVGs use `--elbysodic-on-media-muted`.

Structural validation confirms 52 unique symbols, all 33 original IDs retained,
and matching literal template/navigation references. Kida, the Chirp app check,
Ruff, type checking, and the 18 frontend surface contract tests pass.
The 268-test forum run passed 266 tests; its two stale assertions (the previous
stylesheet version and old counter markup) were updated and both passed on
rerun. No other forum failures remained.

Existing repository-wide checks still need separate cleanup: the CSS validator
does not recognize versioned import URLs, the cluster check rejects an existing
`elbysodic-cluster--sm` use in Casting, and Ruff's full format check reports
pre-existing formatting in `test_forum_slice.py` and
`test_onboarding_journey_contracts.py`. These are outside the icon changes.
