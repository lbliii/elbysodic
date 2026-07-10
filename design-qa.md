# Design QA: Editorial Hierarchy And Progressive Disclosure

- Source visual truth: `design/references/editorial-hierarchy-2026-07-10.png`
- Implementation routes: community home, Writer Desk, Studio home, Studio
  Content, Studio Operations, and a representative location
- Intended comparison viewport: 1440 × 1200 desktop and 390 × 844 mobile
- Intended state: Harbor Society public home plus signed-in writer and director
  states
- Implementation screenshot: not captured

## Full-View Comparison Evidence

The source visual was opened and inspected. The implementation has not yet
been captured in a browser, so composition, crop, vertical rhythm, and
above-the-fold fidelity cannot be judged from rendered evidence.

## Focused Region Comparison Evidence

Blocked with the full-view comparison. Focused comparison is still required
for the realm hero, continuation surface, Studio open index, Writer Desk action
surface, and location director disclosure.

## Findings

- [P1] Browser-rendered implementation evidence is missing.
  - Location: all target routes.
  - Evidence: the source mock is available, but no same-viewport implementation
    screenshot has been captured.
  - Impact: spacing, typography, media crop, responsive behavior, and overall
    fidelity cannot pass design QA from source code and rendered tests alone.
  - Fix: run the local preview in the user's chosen browser, capture matching
    desktop/mobile states, inspect primary interactions and console errors, and
    compare source and implementation together.

## Implementation Checklist

- Capture Harbor Society public and member home at desktop and mobile sizes.
- Capture Writer Desk, Studio home, Studio Content, Operations, and a location.
- Test the realm-home and location director disclosures with keyboard input.
- Test fine-pointer, touch-sized viewport, and reduced-motion states.
- Compare the source and implementation at the same viewport.
- Fix all P0/P1/P2 differences and repeat the comparison.

## Comparison History

- Pass 0: source inspected; implementation capture blocked because the in-app
  browser is not exposed in this task and Playwright CLI use requires the
  user's browser approval under the Product Design workflow.

final result: blocked
