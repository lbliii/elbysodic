# Static Shell Mock Notes

Status: design artifact
Date: 2026-05-11
Artifact: `design/static-shell-mock.html`

## Purpose

This mock explores the accepted layered shell model before the live Chirp
templates are refactored:

- outermost chrome is icon-first
- inner shell is text or icon-plus-text
- page action bars are scoped to displayed content
- full sidebar hiding is focus mode, not the ordinary collapsed state

It uses the Elbysodic theme CSS, Chirp/Elbysodic class vocabulary, and the
first-party SVG sprite in `src/elbysodic/web/static/icons/sidebar.svg`.

## What To Review

- Whether the five outer rail rooms feel distinct enough by icon:
  `World Home`, `Locations`, `Wanted`, `Desk`, `Studio`.
- Whether the inner shell explains the current room without repeating the rail
  as another route directory.
- Whether page actions remain local to the displayed object.
- Whether compact mode still leaves navigation available.
- Whether focus mode feels deliberate rather than broken.
- Whether mobile uses the same hierarchy.
- Whether public, applicant, writer, and staff variants avoid private-state
  leakage.

## Accepted Mapping In The Mock

| Outer Rail | Inner Shell |
|---|---|
| World Home | Start Here, Guidebook, Community, current event/material, applicant entry points |
| Locations | Location tree, active scenes here, related wants, current place context |
| Wanted | Wanted board, Casting, Claims, Reserves, hook handoffs |
| Desk | Queue, Inbox, Roster, Plotting, Applications, Discovery, applicant-owned state |
| Studio | Operations, Launch, Intake, Boards, Navigation, Appearance, Continuity |

## Implementation Lessons To Carry Forward

- The rail needs a shared `rail_icon_link` component with accessible labels,
  tooltip text, active state, and optional privacy-safe badge.
- The inner shell should come from one server-side nav model, not hand-authored
  desktop/mobile templates.
- `Desk` badges are useful only when authorized and scoped to the current
  community.
- `Studio` must be hidden from public/member views unless the viewer has staff
  capability.
- Active face remains in the identity cluster and commitment buttons, not in
  rail/sidebar navigation.
- Page actions can include queue continuation after reading a thread, but they
  should not contain primary route directories.

## Not Covered

- Real route generation.
- Permission-backed counts.
- HTMX swapping.
- Reduced-motion behavior beyond simple CSS transitions.
- Browser screenshot QA.
- Final spacing and token names for production CSS.
