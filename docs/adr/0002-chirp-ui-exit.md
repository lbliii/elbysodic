# ADR 0002: Exit Chirp-UI; keep Chirp + Kida + HTMX + Alpine

- **Status:** Accepted
- **Date:** 2026-08-17
- **Design:** GitHub #293
- **Exit epic:** GitHub #300
- **Pattern gap:** GitHub #299
- **Supersedes:** ADR 0001 D4 Chirp-UI half (adopt-vs-exit is no longer
  parked). Platform-currency sagas #214–#216 and #218 remain separate.

## Context

Elbysodic already runs Chirp 0.10 with `htmx=True`, Kida templates, and
Alpine islands (`elbysodicComposer`, `elbysodicMentionPicker`, layout
`x-data`). Chirp-UI is an optional extra (`use_chirp_ui(app)`), not the
framework. July saga #217 aimed to adopt Chirp-UI 0.11 as the component
and token foundation. That would freeze the wrong design system: PBP
personality already lives in `_components/` and `elbysodic-theme.css`,
while templates still import `chirpui/*` macros and `chirpui-*` classes
(~59 templates, token aliases in `00-tokens.css`).

Chirp's own contracts treat Chirp-UI as optional (`ui` extra;
`use_chirp_ui` is provisional). Lucky Cat chirp-ui examples are not the
Elbysodic UI target. Local Chirp main now wants Kida ≥ 0.12; this repo
still pins `kida-templates>=0.11,<0.12` because of the Chirp-UI extra.

## Decision

1. **Keep Chirp** as the hypermedia framework (pages, contracts, HTMX
   boosting, optional Alpine injection, health/drain, auth extras).
2. **Keep Kida** as the template engine. Do not replace Kida with Jinja
   or an SPA.
3. **Keep HTMX + Alpine** as Chirp-native progressive enhancement.
   After Chirp-UI is gone, Alpine comes from Chirp `AppConfig(alpine=True)`
   (or equivalent injection), not `chirp_ui.alpine`.
4. **Exit Chirp-UI.** Stop adopting `chirpui-*` components, macros, and
   tokens as the design-system foundation. Elbysodic owns primitives and
   PBP components in `src/elbysodic/web/pages/_components/` and
   `src/elbysodic/web/static/elbysodic-theme.css`.
5. **Do not mint `ready` leaves under #231 / #232 / #233.** Those epics
   implement the rejected adopt path. Replace them with an exit epic.
6. **Chirp official patterns are a separate wave.** Page actions,
   FormContract, signals, Suspense, AuthSpec, and Kida 0.12 are not
   Chirp-UI work. See the gap design under saga #216 / epic #226.
7. **Kida 0.12 and dropping the `chirp-ui` dependency are Stop And Ask.**
   They need their own leaves after templates no longer import `chirpui/*`.

## Consequences

- Steward language in `AGENTS.md`, `design/AGENTS.md`, and
  `src/elbysodic/web/AGENTS.md` must say Chirp + Kida + HTMX + Alpine,
  not “Chirp-UI first.”
- Theme architecture’s Chirp adoption rule becomes an Elbysodic
  primitive rule. `10-chirp-primitives.css` is a migration layer to
  drain, not a forever Chirp-UI bridge.
- Workers may not copy Lucky Cat / chirp-ui component names into new
  markup. New UI uses Elbysodic class names and `_components/`.
- Exit leaves serialize on megafiles (`app.py`, `_layout.html`,
  `elbysodic-theme.css` / `elbysodic-theme/`). Prefer one page or one
  CSS layer per leaf.
- Removing `use_chirp_ui` is the last slice, not the first: templates
  and `kida_check` chirp-ui roots must already be gone.

## Non-goals

- Leaving the Chirp framework
- Replacing Kida or HTMX
- Building a CSS-in-JS or SPA design system
- Adopting Chirp-UI 0.11 `app_shell`, `css_subset`, or appearance/tone
  as the product chrome
- Shipping Kida 0.12 in the same leaf as the doctrine freeze
