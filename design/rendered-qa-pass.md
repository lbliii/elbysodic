# Rendered QA Pass

Date: 2026-05-10

Scope: visual QA for the technicolor futurism rollout. This pass uses the
running local app on port 8003, rendered-template inspection, and browser
evidence from the current review. Playwright browser smoke QA is now available
through `uv run poe browser-qa` or
`uv run python scripts/browser_qa.py --base-url http://127.0.0.1:8003`.
The expanded route pass is available through `uv run poe browser-qa-deep`.

## Routes Reviewed

- `/`
- `/network`
- `/c/rl-nyc/world`
- `/c/jurassic-park-universe/boards/isla-nublar`
- thread detail surfaces via `boards/{board_slug}/threads/{thread_slug}`
- composer/new-thread surfaces
- `/c/rl-nyc/my/threads`
- wanted index/detail surfaces
- applications and claims surfaces
- Studio surfaces
- mobile CSS breakpoints for board, thread, composer, wanted, character, and
  network media surfaces
- Playwright desktop/mobile screenshots in `tests/browser/artifacts/`
- Expanded desktop/mobile crawl across seeded community hubs, board pages,
  thread pages, composers, wanted hooks, application pages, claims, Studio,
  character/member pages, plotting, discovery, and world material routes.

## Accepted Issues

- Thread card poster rail did not fill the full desktop card height on location
  pages, weakening the editorial image rhythm.
- Media ratios existed as scattered local decisions instead of an explicit
  design-system map from Midjourney-style ratios to product surfaces.
- Board hero and poster ratios needed named product tokens so future image work
  can choose between cinematic, editorial, square, portrait, poster, and tall
  crops.

## Fixed In This Wave

- Added ratio tokens in `elbysodic-theme.css`.
- Set board stages to `21:9` desktop and `16:9` mobile.
- Set board posters to a `7:4` editorial crop and compact posters to `4:3`.
- Made thread card poster rails span the full desktop card height and remain
  `16:7` on mobile.
- Added `design/image-dimensions.md` for future design-agent decisions.
- Added `scripts/browser_qa.py` to capture representative desktop/mobile
  screenshots and fail on page errors, horizontal overflow, broken media, and
  unusual shell height.
- Added a deep profile that crawls seeded route hubs and skips permission-only
  protected routes.

## Deferred

- Any public Appearance Studio image-ratio controls.
- Schema, Blueprint, import/export, or runtime dependency changes.

## Scene Context Reader QA

Date: 2026-05-15

Scope: browser smoke for the scene-context reader shell on the seeded route
`/c/x-men-apocalypse/boards/danger-room/threads/sentinel-drill`.

Verified:

- Desktop renders the location-aware scene lane in the shell's second rail,
  with no duplicate lane content in the reader body.
- Desktop keeps grounded scene context tucked behind a reader action until the
  inspector is opened beside the transcript.
- Tablet at 820px keeps the reader primary and moves scene/context rails into
  drawers.
- Mobile at 390px keeps the reader primary, exposes `Scenes here` and
  `Scene context` drawer triggers, and avoids horizontal overflow.
- Drawer contents were opened and verified for the current scene lane and
  grounding inspector.
- A 1920px screenshot verified the corrected shell rail and confirmed
  `#page-content` does not contain leaked primary rail or scene-lane markup.
- Boosted board-to-thread navigation swaps the shell second rail out of band,
  so the location nav updates to the thread's `Open scenes` lane without a
  hard refresh and without leaking lane markup below the reader.
- The threaded rail lists currently open scenes in the active location and
  excludes paused scenes from that lane.
- Scene management and staff controls render inside the right grounding tray
  instead of occupying reader-body space before the transcript.
- Reader utility actions are consolidated into the grounding tray, leaving the
  reader hero with a single scene-actions icon and no top reply shortcut.
- The desktop grounding tray slides in as a right-edge overlay instead of
  adding a layout column, so opening scene context no longer pushes posts
  inward.

Artifacts:

- `/private/tmp/elbysodic-scene-context-smoke/desktop.png`
- `/private/tmp/elbysodic-scene-context-smoke/tablet.png`
- `/private/tmp/elbysodic-scene-context-smoke/mobile.png`
- `/private/tmp/xmen-scene-reader-after-2.png`
- `/private/tmp/sidebar-oob-route-update.png`

Deferred:

- Broader screenshot artifact capture for every seeded thread style.
- Any schema-backed scene hero media controls.

## Editorial Post Reader QA

Date: 2026-05-15

Scope: browser smoke for the editorial post reader mode on the seeded route
`/c/x-men-apocalypse/boards/danger-room/threads/moonlight-skirmish`.

Verified:

- Desktop at 1440px renders post portrait rails as prose-wrapping editorial
  poster art with alternating sides.
- Character post media uses the shared `2:3` poster ratio token in the
  editorial reader mode.
- Tablet at 820px and mobile at 390px keep post rails non-floating and avoid
  horizontal overflow.
- Existing post customization variants remain present in the rendered thread:
  `bio`, `poster`, `dock`, calm/compact/dramatic density, post permalinks,
  writer links, and edit links where allowed.
- Editorial post shells suppress always-on character borders by default and
  reveal a soft post affordance on hover/focus, keeping customization from
  breaking the continuous reading flow.
- Editorial post lists use a tightened, centered reading measure under the
  wider scene hero so prose keeps a literary cadence while character posters
  remain prominent.
- Editorial post metadata leaves only the author visible by default; relative
  time, permalink, edit, and revision controls stay available on hover/focus
  instead of competing with the prose.
- The reply composer and after-scene continuation strip share that tightened
  measure, with a compact WYSIWYG toolbar and slimmer sticky editor modeled on
  the prototype's reply card.
- The after-scene continuation strip now sits after the reply composer and
  keeps a `Scenes here` return path beside any queue continuation links.
- The shell's scene lane fills the full secondary sidebar height and omits the
  current thread from its nearby-scene lists while preserving current-scene
  state for reader labels.
- Shell scene-lane rows use a compact sidebar density, and `Open scenes`
  excludes scenes where the current roster already has the last word.
- Editorial poster-style character cards keep their profile card as a
  hover/focus overlay instead of rendering the profile panel underneath by
  default.
- The reply composer folds face switching into the `Reply as` chip, removing
  the duplicate standalone character dropdown from the composer topline.
- The shell identity menu now uses a thinner active-face pill, a compact
  face/writer dropdown, and local click-away/Escape behavior.

Artifacts:

- `/private/tmp/elbysodic-editorial-post-smoke/desktop.png`
- `/private/tmp/elbysodic-editorial-post-smoke/tablet.png`
- `/private/tmp/elbysodic-editorial-post-smoke/mobile.png`

Deferred:

- Drop caps and beat notes remain theme/post-style polish, not global defaults.
- Automatic dialogue bolding remains deferred; writer-authored markup stays
  authoritative.

## Inherited Scene Hero Media QA

Date: 2026-05-15

Scope: browser smoke for the no-schema scene hero media on the seeded route
`/c/x-men-apocalypse/boards/danger-room/threads/sentinel-drill`.

Verified:

- The scene hero inherits the visible parent location image from Xavier
  Institute for the Danger Room scene.
- The inherited media keeps the stored image alt text.
- The hero renders the thread title, summary, state chips, facets, and
  scene-actions button over the image instead of introducing a second media
  block with boilerplate atmosphere copy.
- Desktop, tablet, and mobile widths avoid horizontal overflow.
- Text-first board media treatment suppresses inherited scene hero media in rendered
  tests.

Artifacts:

- `/private/tmp/elbysodic-scene-media-smoke/desktop.png`
- `/private/tmp/elbysodic-scene-media-smoke/tablet.png`
- `/private/tmp/elbysodic-scene-media-smoke/mobile.png`

Deferred:

- Thread-specific scene media fields remain a Phase B schema decision.
- Event-specific media remains deferred; current events only provide contextual
  chip text when already present.

## Scene Writer Activity Drawer QA

Date: 2026-05-15

Scope: browser smoke for the `What needs you` drawer on the seeded route
`/c/x-men-apocalypse/boards/danger-room/threads/sentinel-drill`.

Verified:

- Desktop and mobile expose a `What needs you` trigger for an active-face
  member.
- Opening the drawer shows the active face, current scene state, reply/waiting
  obligations, and the Desk queue link.
- Desktop and mobile widths avoid horizontal overflow while the drawer is
  open.

Artifacts:

- `/private/tmp/elbysodic-scene-activity-smoke/desktop.png`
- `/private/tmp/elbysodic-scene-activity-smoke/mobile.png`

Deferred:

- Reserve and claim rows remain deferred until they are backed by an explicit
  notification or deadline service contract.

## Scene Plotting Grounding QA

Date: 2026-05-15

Scope: browser smoke for a scene context panel with a real plotting-room story
link on `/c/x-men-apocalypse/boards/danger-room/threads/sentinel-drill`.

Verified:

- Desktop and mobile scene context expose the plotting-room link card when a
  room is explicitly attached to the current scene.
- The card shows the plotting-room title, source label, status, and planning
  faces.
- Desktop and mobile widths avoid horizontal overflow while the scene context
  panel/drawer is open.

Artifacts:

- `/private/tmp/elbysodic-scene-grounding-smoke/desktop.png`
- `/private/tmp/elbysodic-scene-grounding-smoke/mobile.png`

Deferred:

- Generic wanted hook links remain deferred until wanted-to-thread
  relationships are explicit outside plotting-room source data.
- Canon/source grounding remains deferred until Continuity Graph provenance and
  review workflows exist.

## Premise Discovery QA

Date: 2026-05-15

Scope: route and browser-profile proof for the public premise discovery catalog
and director-only Studio discovery editor.

Verified:

- `/network` renders public discovery filters with premise, play engine, lore
  aperture, ways in, and pace/touchpoint groups.
- `/network?q=weird-town mystery` finds Signal Creek without exposing active
  face, writer queue, private room, or staff state.
- Original-premise director personas for Harbor Society, Signal Creek, and
  Wayfarer Station can open `/studio/discovery` and see their own premise
  archetype labels.
- `scripts/browser_qa.py --profile premise` defines a desktop/mobile pass
  covering public catalog queries, original-premise realm hubs, and the Studio
  discovery editor after switching to `harbor_director` through dev personas.
- Studio discovery now renders the same public Network card component used by
  Explore, so directors can inspect the actual catalog card shape while
  maintaining the profile.
- Original-premise seeds now distribute each eight-face roster across
  `starlane`, `junipergray`, `milesnorth`, `cassmarlow`, and `lenawren`, so demo
  activity no longer reads as one writer owning every face.
- Route proof now covers all nine original-premise realm hubs, wanted boards,
  wanted detail pages, application hubs, and first-face application forms for
  faceless members.
- `scripts/browser_qa.py --profile premise` now visits all nine original realm
  hubs plus representative wanted details and first-face forms.

Artifacts:

- `research/uat/simulated/2026-05-15-premise-discovery-simulated-uat.md`
- `tests/test_forum_slice.py::test_original_premise_discovery_routes_support_persona_qa`
- `tests/test_forum_slice.py::test_original_premise_entry_paths_support_first_face_and_wanted_browsing`
- `uv run python scripts/browser_qa.py --profile premise --base-url http://127.0.0.1:8003`

Deferred:

- Real hook-hunter and new-face applicant UAT against the expanded seed catalog.
