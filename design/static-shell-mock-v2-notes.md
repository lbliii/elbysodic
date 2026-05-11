# Static Shell Mock V2 Notes

Status: design artifact
Date: 2026-05-11
Artifact: `design/static-shell-mock-v2.html`

## Purpose

V2 translates the first visual mock toward the implementation shape:

- Uses live-ish class names such as `chirpui-app-shell`,
  `chirpui-app-shell__sidebar`, `chirpui-sidebar__link`,
  `chirpui-surface`, `chirpui-btn`, and `chirpui-badge`.
- Adds candidate Elbysodic component classes such as
  `elbysodic-primary-rail`, `elbysodic-inner-shell`, and
  `elbysodic-nav-icon`.
- Keeps mock-only mode and audience controls outside the app shell.
- Embeds inline SVG symbols so icons render when the HTML is opened directly
  from disk.

## Component Candidates

- `primary_icon_rail`: persistent icon-first outer rail.
- `rail_icon_link`: icon, accessible label, tooltip, active state, optional
  privacy-safe badge.
- `inner_sidebar_shell`: current-room text or icon-plus-text shell.
- `sidebar_context_collection`: generated or contextual room rows.
- `mobile_shell_drawer`: same nav model rendered for small screens.

## Difference From V1

V1 is a freer visual exploration. V2 is closer to a Chirp/Elbysodic
implementation target and should be used when evaluating how to refactor the
live `_layout.html` and `_components/sidebar.html`.

## Icon Note

V2 embeds placeholder SVG symbols inline. The production source of truth remains
`src/elbysodic/web/static/icons/sidebar.svg`; the inline symbols are included
only so local file previews show icons reliably.
