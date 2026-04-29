# Notices, Admonitions, And Toasts

Elbysodic uses notices to make the world feel alive without turning every page
into an alert dashboard. A notice is a contextual signal attached to the
surface the writer is already reading.

Use this guide before adding current-event bridges, staff notices, warnings,
success messages, empty-state nudges, or toast-style feedback.

## Notice Roles

### Context Notice

Use when a page is shaped by something adjacent: a current event affecting a
scene, a material related to a board, or a continuity pressure that explains why
this page matters right now.

Examples:

- Current event shaping a scene.
- Current event shaping a location.
- Related guidebook material on a wanted hook.

Contract:

- Sits near the affected content, not in global chrome.
- Has a small mark, label, title, summary, and optional action.
- Should feel like world pressure, not an error.

### Admonition

Use for durable guidance that changes how the user should act: staff-only
preview, locked thread, archived content, private board, or application revision
request.

Contract:

- Clear state first, explanation second.
- Usually page-local and persistent until the state changes.
- Can include one action if there is an obvious next step.

Use `.elbysodic-notice--staff` for read-only staff tooling previews and locked
production surfaces. Use `.elbysodic-notice--warning` or
`.elbysodic-notice--attention` only when the state needs director attention.

### Toast

Use for temporary confirmation after an action: draft saved, application
submitted, interest sent, reserve created.

Contract:

- Short, dismissible or self-clearing.
- Never contain the only path to the next action.
- Should not replace inline validation for forms.

### Inline Status

Use inside a form, composer, row, or card when the feedback belongs to that
component: draft status, validation, preview empty, or search empty.

Contract:

- Stays adjacent to the control or region it describes.
- Uses compact live-region text when needed.
- Avoid long explanations in `aria-live`.

Inline status is not a full notice. Keep draft saved, preview empty, no matches,
and field validation close to the relevant control unless the message changes
what the whole page is doing.

## Event Notice Shape

Events are special because they make the board feel seasonal and alive. They
should be visible where they shape play, but not so heavy that they interrupt
reading.

The current event bridge should use the notice pattern:

- mark: small icon or ASCII signal
- label: "Current event shaping this scene" or local equivalent
- title: linked event/material title
- summary: one-sentence event pressure
- action: "View event" when space allows

Events may eventually deserve a dedicated `/world/events` index, but individual
event notices should still link to the event material page until the event model
needs a richer route.

## Styling Rules

- Use a left accent rail or compact mark for notices; avoid large cards unless
  the notice is the main content.
- Do not use warning colors for event context unless something is actually
  broken or blocked.
- Do not use empty-state styling for permission or workflow constraints. Those
  are admonitions, not absences.
- Keep notices responsive: on tablet and mobile, title and action must wrap
  beneath the label instead of squeezing adjacent content.
- Prefer one action. If there are multiple actions, the notice is probably a
  workflow panel, not a notice.
- Notices can be atmospheric, but they must remain readable with ordinary text
  contrast.

## Implementation Notes

- Shared notice classes live in `elbysodic-theme.css` under `.elbysodic-notice`.
- Event bridge notices compose `.elbysodic-notice` with
  `.elbysodic-notice--event` and `.elbysodic-event-bridge`.
- Staff previews and locked surfaces use `.elbysodic-notice--staff`.
- Navigation health and other production warnings use `.elbysodic-notice--note`,
  `.elbysodic-notice--warning`, or `.elbysodic-notice--attention`.
- Success and neutral status variants should extend the same base class instead
  of inventing one-off panels.
