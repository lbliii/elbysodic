# Motion Design

This note defines Elbysodic's animation and transition direction. It supports
technicolor futurism without turning a writing product into a spectacle layer.

This is design guidance, not an implementation contract. Do not add new
JavaScript animation libraries, route transitions, public settings, Appearance
Studio controls, or Blueprint fields from this note without an explicit human
check-in and the relevant stewards.

## Point Of View

Motion should make a writer feel oriented, not interrupted. Elbysodic is a
long-form PBP studio: scenes, faces, claims, reserves, wanted hooks, queues,
and staff review all depend on clarity. Animation can make the product feel
alive, but it must never disturb reading, hide controls, imply state changes
that did not happen, or make private/staff boundaries ambiguous.

## Motion Personality

Technicolor futurism gives Elbysodic three motion cues:

- Registered: movement lands exactly where the layout says it should. No
  wandering, wobble, bounce, or ornamental delay.
- Luminous: color and focus may brighten briefly when attention changes.
  Light behaves like signal, not decoration.
- Editorial: transitions feel like cut, reveal, emphasis, and pacing. They
  should support reading rhythm and hierarchy.

Avoid arcade motion, sci-fi HUD clutter, parallax spectacle, animated
background loops, excessive glow pulses, and page-wide route choreography.

## Motion Jobs

Use animation only when it does one of these jobs:

- Micro-feedback: a button, chip, icon control, field, toggle, or menu item
  acknowledges hover, focus, press, selection, save, or disabled state.
- Orientation: a drawer, rail, menu, disclosure, or composer panel opens from
  the place that triggered it.
- Continuity: a thread, scene, queue, or plotting room updates without making
  the user lose their place.
- State change: active face, watching, caught up, needs reply, waiting,
  private, locked, saved, error, or warning state becomes clear.
- Loading: a surface communicates that work is pending without looking broken
  or implying story activity.
- Attention routing: a new obligation, validation problem, or selected action
  gets a brief, respectful cue.
- Material behavior: a glass/translucent surface resolves into or out of the
  layer it belongs to.

If motion does not serve one of these jobs, it should not ship.

## Surface Budgets

| Surface | Motion Budget | Allowed Motion |
| --- | --- | --- |
| Thread body | None to lowest | anchor focus, no ambient motion |
| Composer | Low | toolbar state, preview toggle, save/error cue |
| Post profile rail | Low | disclosure reveal, no hover-dependent identity |
| World gateway | Medium | hero media settle, next-section reveal, subtle state cues |
| Board/location | Medium | media hover, relevant-face cue, filter change |
| Character hub | Medium | identity accent, poster hover, queue state |
| Wanted hooks | Medium | reserve/interest state, casting emphasis |
| Event notices | Medium | urgency cue, not looping alarm |
| Menus/popovers | Medium | open/close from trigger, glass resolve |
| Sidebar/topbar | Low-medium | drawer, collapse, active state |
| Studio rooms | Low | validation, progress, selected room |
| Applications/claims | Low | review state and validation only |
| Staff/private/recovery | Lowest | focus and validation only |

## Micro-Feedback Rules

Micro-feedback is the default motion layer. It should make controls feel
responsive without drawing attention away from writing.

Buttons:

- Hover/focus may shift border, background, text color, and shadow.
- Pressed state may move at most 1px or use a darker/lighter fill.
- Primary actions should feel crisp, not bouncy.
- Disabled state should not animate; it should be plainly unavailable.

Icon controls:

- Use a small color, background, or outline change.
- Do not spin, bounce, or wiggle icons for routine hover.
- Tooltips may fade/translate briefly, but the accessible name must not depend
  on the animation.

Chips, facets, and filters:

- Selection may use a quick dye-record fill or inset rule.
- Removing a filter may fade/contract only if the list does not jump in a
  confusing way.
- Facets that are metadata should stay quieter than filters or actions.

Fields:

- Focus should be immediate and visible.
- Validation errors may use one brief outline or message reveal.
- Do not shake fields; it reads punitive and can be hostile in application or
  staff contexts.

Toggles:

- Thumb movement is allowed when the control is a real binary setting.
- The label and final state must remain clear without motion.
- Theme changes should avoid dramatic crossfades that make text flash.

Cards and rows:

- Hover may lift or tint interactive cards only when the whole object is a
  link/action.
- Non-interactive cards should not pretend to be clickable through hover
  animation.
- Rows in dense production surfaces should prefer underline, border, or tint
  changes over lift.

## Loading And Pending States

Loading states should communicate product work without creating fake story
movement.

Use these patterns:

- Skeletons for content blocks that will preserve layout: board cards, wanted
  cards, roster rows, application lists, and Studio lanes.
- Inline pending labels for form actions: saving, posting, reserving,
  watching, joining, sending, or updating.
- Button-local busy state for commands that affect one object.
- Page or lane empty/loading states for first load, never a full-screen loader
  when the shell and navigation can remain useful.
- Optimistic UI only when rollback is clear and does not risk posting as the
  wrong face or leaking staff/private state.

Avoid:

- shimmer behind long-form prose
- infinite spinners as the only signal on object-level actions
- loading animation that looks like unread, needs reply, or live scene
  activity
- skeleton geometry that shifts when real content arrives
- fake progress bars for unknown duration work

Pending state language should use PBP verbs where possible:

```text
Posting...
Saving draft...
Watching scene...
Reserving face...
Sending interest...
Updating claim...
```

## State Transition Rules

State changes should be visible, semantic, and reversible where the workflow
allows it.

- `needs reply`: one amber or attention-color cue, then settle into a stable
  badge/count state.
- `waiting`: quieter than needs reply; no urgent pulse.
- `caught up`: brief success cue, then stable calm state.
- `watching`: selected state should feel persistent, not celebratory.
- `private` and `staff`: no dramatic animation; clarity and boundary dominate.
- `locked` and `archived`: state should settle into reduced emphasis.
- `saved` and `posted`: one confirmation cue; do not keep glowing.
- `error` and `warning`: reveal the message and focus target without shaking
  or flashing.
- active face switch: immediate identity confirmation near composer and shell;
  avoid any transition that creates ambiguity about authorship.

## Timing Direction

These are target ranges for later tokens, not committed CSS names.

- Instant state: 80-120ms. Use for button hover, selected chip, active nav,
  focus-adjacent color changes.
- Interface reveal: 140-200ms. Use for menus, disclosures, drawers, and
  compact panels.
- Surface transition: 180-260ms. Use for composer preview, rail collapse,
  media caption, and command-panel entrance.
- Attention cue: 300-600ms total, one cycle only. Use for save, error,
  needs-reply, or new state arrival.

Do not use long easing for core writing flow. Anything over 300ms needs a
specific reason and reduced-motion behavior.

## Easing Direction

Motion should feel precise and calm:

- Use ease-out for entrances and reveals.
- Use ease-in for dismissals.
- Use standard ease or linear only for tiny color/shadow transitions.
- Avoid spring, elastic, bounce, shake, and overshoot unless a future game-like
  surface explicitly justifies it.

## Allowed Properties

Prefer:

- `opacity`
- `transform`
- `background-color`
- `border-color`
- `box-shadow`
- `filter` only for tiny media/focus treatment

Avoid:

- animating layout dimensions in ways that shift prose or controls
- animating `top`, `left`, `width`, or `height` for routine UI
- blur changes behind text-bearing surfaces
- looping gradients or animated background fields
- motion that depends on hover with no keyboard/touch equivalent

## Component Patterns

### Glass Resolve

For menus, popovers, media captions, and selected overlays:

- fade and translate 2-6px from the trigger direction
- bring the border/focus ring into clarity as the surface settles
- keep text readable throughout the transition
- fall back to solid surfaces under reduced transparency or unsupported blur

### Luminous State

For selected face, active nav, watching, caught up, needs reply, saved, or
error:

- use one brief color/outline/shadow change
- do not pulse indefinitely
- never rely on color alone
- do not imply a state changed until the server/client state actually changed

### Loading Skeleton

For lists, cards, and lanes:

- reserve the final component's approximate size
- use low-chroma neutral motion or static blocks
- avoid shimmer if reduced motion is requested
- never use skeletons for body prose once real text is available
- replace with final content without layout jump

### Editorial Reveal

For disclosures, local rails, queue lanes, and command panels:

- reveal content from its source context
- keep headings and primary actions stable
- avoid moving existing prose under the user's eyes
- preserve focus order and keyboard position

### Media Settle

For board posters, character posters, world hero media, and network cards:

- allow subtle image scale or light shift on hover/focus
- keep overlays, captions, and actions stable
- do not animate media behind long-form prose
- provide no-motion behavior that still exposes the same affordances

## Reduced Motion Contract

Every animation must have a reduced-motion path:

- Remove non-essential transforms.
- Keep opacity changes brief or instant.
- Preserve final visual state and focus visibility.
- Do not hide information behind motion-only affordances.
- Disable ambient, looping, parallax, shimmer, and attention pulses.

Future implementation should centralize this in CSS with
`@media (prefers-reduced-motion: reduce)` and avoid duplicating exceptions
across page-local selectors.

## PBP-Specific Rules

- Never animate thread body text while a writer is reading.
- Never animate composer text, preview content, or active face identity in a
  way that creates doubt about who is posting.
- New replies, needs-reply, waiting, caught up, and watching states may receive
  a single respectful cue.
- Staff/private/warning surfaces may use motion for clarity, not drama.
- Plotting and wanted movement should feel like story momentum, not inbox
  noise.
- Application and claim review should feel calm and trustworthy.

## QA Checklist

For any motion implementation:

- Test keyboard focus before, during, and after the transition.
- Test touch behavior where hover is unavailable.
- Test `prefers-reduced-motion: reduce`.
- Verify no layout shift around prose, composer, primary actions, or controls.
- Verify motion does not obscure private/staff/warning/error state.
- Verify long labels, many badges, and mobile wrapping do not collide with the
  animated element.
- Verify the final state is visible without animation.

## Open Decisions

- Exact CSS token names for duration and easing.
- Whether Elbysodic should expose any motion density preset to directors.
- The first canonical motion proof pattern. Recommended: menu/popover glass
  resolve or composer preview toggle, because both are useful and bounded.
- Whether browser QA should archive short videos or only still screenshots
  plus reduced-motion checks.
