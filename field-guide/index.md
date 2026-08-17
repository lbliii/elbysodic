<!--
field-guide inject point — keep the body ≤ 80 lines (excluding this comment).
Budget: 80 lines. Current body should stay scannable in one screen.
-->

# Elbysodic field guide (index)

Line budget: **80** (body below). Prefer links over essays.

## Build / run

- Local: `uv sync --group dev` then `uv run elbysodic serve` (see root README).
- Gates: `uv run ruff check .`, `uv run ruff format . --check`,
  `uv run pytest -q --tb=short`, `uv run ty check src/elbysodic/ tests/`,
  and `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`.
- Browser QA for substantial UI: port 8001 against the Surface Quality Bar.

## Issue lifecycle (swarm-ready)

- Invokes: [`AGENTS.md`](../AGENTS.md) — default **`swarm`** / **`drive`**
  (orchestrator delegates); escape hatches `claim #N`, `board`, …
- Standard: [`docs/plan/issue-lifecycle.md`](../docs/plan/issue-lifecycle.md)
- ADR: [`docs/adr/0001-issue-lifecycle.md`](../docs/adr/0001-issue-lifecycle.md)
- Workers claim only issues labeled `type:leaf` **and** `ready`.
- Leaves must list **owned paths** + **machine acceptance**; do not re-decide ADRs.
- Templates: `.github/ISSUE_TEMPLATE/` (saga / epic / design / leaf / bug).
- Label queries use `type:leaf`, not bare `leaf`.
- Board (ready queue):
  `gh issue list --label type:leaf --label ready`
- Board (blocked leaves):
  `gh issue list --label type:leaf --label blocked`

## Architecture pointers

- Strategy spine: [`docs/product/strategy-spine.md`](../docs/product/strategy-spine.md)
- Surface contracts: [`docs/architecture/surface-contract-architecture.md`](../docs/architecture/surface-contract-architecture.md)
- Privacy matrix: [`docs/architecture/rendered-route-privacy-matrix.md`](../docs/architecture/rendered-route-privacy-matrix.md)
- Plans are an index, not specs: [`plans/README.md`](../plans/README.md)

## Megafile caution

Prefer leaves that touch one page/service slice + matching tests/docs.
Treat these as contention hotspots unless the leaf explicitly owns a carve-out:

- `src/elbysodic/web/app.py`
- `src/elbysodic/web/pages/_layout.html`
- `src/elbysodic/web/static/elbysodic-theme.css` and `elbysodic-theme/`
- `src/elbysodic/web/surface_contracts.py`
- shared seed modules under `src/elbysodic/db/`

## Surprises
