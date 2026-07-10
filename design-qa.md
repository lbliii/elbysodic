# Design QA: Editorial Hierarchy And Progressive Disclosure

- Source visual truth: `design/references/editorial-hierarchy-2026-07-10.png`
- Evidence archive: `design/qa/editorial-hierarchy-2026-07-10/`
- Machine-readable audit: `design/qa/editorial-hierarchy-2026-07-10/audit-results.json`
- Routes: Harbor Society community home, Writer Desk, Studio home, Studio
  Content, Studio Operations, and Shoreline Club
- Viewports: 1440 × 1200 desktop and 390 × 844 mobile
- Audiences: public visitor plus signed-in Maris Vale writer/director
- Captured: 2026-07-10 from the no-debug staging-security local preview on
  port 8001

## Full-View Comparison Evidence

The source and implementation were inspected together at the desktop target,
then every implementation surface was inspected at desktop and mobile sizes.
The implementation preserves the source's open editorial field, asymmetric
realm hero, strong story title, lightweight rules, contained continuation,
and few high-value story shelves without reproducing the reference as a
pixel-perfect skin.

The final public home removes the appended join/cast/social route directory;
the hero's premise and open-call actions now lead a curated current-story,
places, guidebook, and wanted sequence. The member home replaces visitor entry
scaffolding with the Maris Vale continuation. Writer Desk, Studio, Content,
Operations, and Shoreline Club retain the same hierarchy at mobile width
without collisions or horizontal scrolling.

| Surface | Desktop | Mobile |
| --- | --- | --- |
| Public home | `01-public-home-desktop.png` | `02-public-home-mobile.png` |
| Member home | `03-member-home-desktop.png` | `04-member-home-mobile.png` |
| Writer Desk | `05-writer-desk-desktop.png` | `06-writer-desk-mobile.png` |
| Studio home | `07-studio-home-desktop.png` | `08-studio-home-mobile.png` |
| Studio Content | `09-studio-content-desktop.png` | `10-studio-content-mobile.png` |
| Operations | `11-operations-desktop.png` | `12-operations-mobile.png` |
| Shoreline Club | `13-shoreline-club-desktop.png` | `14-shoreline-club-mobile.png` |

## Focused Interaction Evidence

- Realm and location disclosures open from keyboard input, retain focus, show
  the browser focus indicator, and measure 44px high:
  `15-realm-disclosure-keyboard.png` and
  `16-location-disclosure-keyboard.png`.
- Reduced motion preserves the complete open state with computed transition
  and animation durations of `1e-05s`:
  `17-realm-disclosure-reduced-motion.png`.
- Fine-pointer hover changes the summary background and border while the
  essential action stays visible:
  `18-realm-disclosure-fine-pointer-hover.png`.
- Playwright touchscreen taps exercised open-close-open latest intent on the
  location disclosure; the final state is open and the target is 44px high:
  `19-location-disclosure-touch.png`. The headless browser exposed
  `ontouchstart` but did not report the coarse-pointer media query, so this is
  touch-emulation evidence rather than physical-device evidence.

## Final Findings

- Resolved [P2]: the anonymous realm home appended a complete join, cast, and
  social-map directory after already providing a clear entry path. Scoped
  collections remain reachable from navigation and contextual actions.
- Resolved [P2]: Harbor Society's one-item Writer Desk repeated the same owed
  reply through a single-face lane and the active work lane. The face index now
  renders only when multiple actionable faces create a real choice.
- Resolved [P2]: shared realm/location director summaries measured 39px high
  and had no fine-pointer hover response. The shared control now measures 44px
  and has a fine-pointer-only hover state.
- Passed: all 14 route captures have exactly one visible `h1`, no horizontal
  overflow, no console errors, and no page errors.
- Passed: no unresolved P0, P1, or P2 visual, responsive, interaction, or
  accessibility-risk findings remain in the captured scope.

## Research And Validation Limits

The panel interpretation is synthetic and medium-confidence: active writer,
new-face applicant, community director, and safety-boundary perspectives were
applied to the rendered evidence. This is simulated UAT, not observed user
research. Physical-device coarse-pointer testing and real applicant/writer
validation remain post-alpha evidence gaps; they do not block this bounded
browser design-QA pass.

## Verification

- `uv run pytest -q --tb=short tests/test_director_realm_opening_contracts.py tests/test_forum_slice.py -k 'realm_gateway or writer_desk_hub_keeps_meta_tools_reachable or director_controls'`: 6 passed.
- Ruff check and format check pass for the changed Python files.
- Chirp application check: no errors; the pre-existing Studio heading warning is
  tracked by #264.
- Repository-wide Ruff, format, Ty, and Pytest are not clean on this branch for
  the baseline failures recorded in #264. The full Pytest run reached 48% with
  those failures before the 10-minute verification timeout; no #263-specific
  failure appeared in the focused suite.

## Comparison History

- Pass 0: source inspected; implementation capture blocked.
- Pass 1: 19 browser states captured; public route inventory, single-face Desk
  repetition, and 39px director targets recorded as P2.
- Pass 2: all P2 findings fixed; all 19 states recaptured and inspected against
  the source and across desktop/mobile, keyboard, fine-pointer, touch-emulated,
  and reduced-motion conditions.

final result: passed
