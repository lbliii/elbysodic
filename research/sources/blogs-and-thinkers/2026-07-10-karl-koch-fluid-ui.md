# Source Note: 10 Principles For Fluid UI

## Source

- Title: 10 Principles for Fluid UI
- Author: Karl Koch
- Published: 2026-02-16
- URL: https://karlkoch.me/writing/10-principles-for-fluid-ui
- Accessed: 2026-07-10
- Researcher: Codex
- Confidence: Medium. The article is a useful interaction-design point of
  view, not user research or evidence that every principle fits Elbysodic.

## Why This Source Matters

The hierarchy and progressive-disclosure work is reducing visual competition
and repeated containers. That leaves a second question: how should a calmer
interface respond when a writer or director opens, closes, changes, or follows
something? This source offers a vocabulary for continuity and responsiveness
without requiring Elbysodic to become a gesture-heavy or animation-led product.

## Source Signal

Koch describes fluid interfaces through ten related practices: physics-based
motion, interruptible animation, direct manipulation, preserved velocity,
shared-element transitions, input-method adaptation, animated layout changes,
progressive resistance, choreographed sequencing, and reduced-motion support.
The article points to native browser capabilities such as the View Transitions
API, pointer and hover media queries, FLIP-style layout animation, bounded
staggering, and `prefers-reduced-motion`.

The strongest signal for Elbysodic is not that the product needs more motion.
It is that state changes should preserve context, accept a newer intention
without making the user wait, and remain legible across mouse, keyboard, and
touch input.

## Relevant User Panel Segments

- Active writers switching between obligations, scenes, and faces
- Returning regulars rebuilding context after time away
- Directors moving from overview to a specific editorial or operational task
- Staff moderators processing queues without losing place
- Safety-boundary writers who need reduced motion and predictable disclosure

## Interpretation For Elbysodic

### Adopt

- Latest intent wins. A disclosure or transition must be interruptible and land
  in the state the user most recently requested.
- Preserve the object of attention. When a scene, location, application, or
  queue item opens into detail, retain enough visual and semantic continuity
  that the user understands where it came from.
- Adapt to input. Hover may enrich a mouse path, but essential context and
  action cannot depend on hover, drag, or a gesture.
- Animate bounded layout changes only when the movement explains what changed.
- Use sequencing sparingly to direct attention to one consequential update,
  not to make a page full of items perform on arrival.
- Treat reduced motion as an alternate complete presentation, not simply a
  slower version of the same choreography.

### Do Not Adopt As Defaults

- Spring, bounce, elastic resistance, or overshoot as the product's general
  motion character
- Draggable cards, velocity-preserving gestures, or elastic overscroll for
  ordinary navigation and board-running work
- Page-wide cascades, parallax, or route choreography that delays reading
- A new client runtime or animation dependency when CSS, native browser APIs,
  and existing Chirp or Alpine behavior can express the interaction

Elbysodic should feel fluid through continuity, not kinetics. Its registered,
luminous, editorial tone calls for calm state changes that protect reading and
writing concentration.

## Product Implications

- The selected community-home direction should use an open editorial canvas
  with only a small number of contained action surfaces. Motion should connect
  a selected object or disclosure to its result, not compensate for weak
  hierarchy.
- Progressive disclosure controls need explicit open and closed states,
  immediate reversal, focus preservation, and a useful no-motion state.
- Writer Desk and Studio transitions should preserve task context and return
  position where the server-rendered navigation model allows it.
- Shared-element or native View Transition work is a later bounded proof, not a
  prerequisite for the hierarchy refactor.

## Promotion Targets

- `design/motion-design.md`: define fluidity as continuity rather than kinetic
  spectacle and add interaction QA expectations.
- `plans/in-progress/hierarchy-progressive-disclosure-2026-07-10.md`: include
  interruptibility, input adaptation, and reduced-motion proof in the selected
  direction's implementation slices.

## Follow-Up Questions

- Can a native View Transition preserve a scene or location's context across
  Chirp navigation without weakening focus, history, scroll, or privacy
  behavior?
- Which disclosure transition best explains hierarchy while remaining useful
  when motion is removed?
- Should reduced motion remain a system preference only, or eventually become
  a writer preference inside accessibility settings?
- What automated or manual QA best proves that rapid repeated input resolves
  to the latest intended state?
