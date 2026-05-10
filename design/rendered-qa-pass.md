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
