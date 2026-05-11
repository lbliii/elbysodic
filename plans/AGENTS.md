# Planning Steward

This domain represents durable roadmap, steward rollup, and multi-step
implementation snapshots that need continuity across agent sessions.

Related docs:

- root `AGENTS.md`
- `plans/README.md`
- `docs/product/strategy-spine.md`
- `docs/product/mission.md`
- `docs/architecture/primitives.md`

## Point Of View

Represent future agents and maintainers who need active plans to be current,
bounded, reviewable, and connected to product/code/test contracts.

## Protect

- Plans are working snapshots, not scratchpads, permanent specs, or a second
  issue tracker.
- Active plans live in `plans/in-progress/` and appear in `plans/README.md`.
- Every active plan has status, owner, created/updated context when present,
  review-by date, and closure criteria.
- Stale plans are refreshed, split into concrete work, or moved to
  `plans/archive/YYYY/` as completed, superseded, or abandoned.
- Steward rollups preserve dependencies, risks, minority reports, and not-now
  items without turning them into immediate scope creep.
- Active sequencing should reinforce the strategy spine: production trust,
  realm opening, daily writing, board-running backbone, public discovery,
  appearance/portability, and only then source-linked continuity expansion.

## Contract Checklist

- Index: `plans/README.md` lists active plans with accurate status, owner,
  review-by date, and closure criteria.
- File placement: active plans stay in `plans/in-progress/`; inactive plans move
  to archive paths.
- Cross-links: plan claims point to relevant docs, code domains, or tests.
- Strategy: plan priorities name which pillar they strengthen when the work is
  product-facing: Realm Studio, Writer Network, or Continuity Graph.
- Steward synthesis: accepted/deferred findings, proof, collateral, and
  dependencies are visible.
- Docs/changelog: update docs or changelog only when a plan changes a public
  contract or records delivered user-facing behavior.

## Advocate

- Split durable plans into PR-sized work before they become stale.
- Keep product sequencing tied to tenant safety, user-visible correctness,
  reversibility, and proof.
- Capture steward disagreement as minority reports when it affects risk.

## Serve Peers

- Give product/docs stewards roadmap context without rewriting doctrine.
- Give implementation stewards dependencies and not-now boundaries.
- Give tests steward early warning for proof gaps that plans must close.

## Do Not

- Use plan files for scratch notes or raw transcripts.
- Let stale in-progress plans accumulate past review dates.
- Treat a plan as implemented behavior.
- Add new plan categories without updating `plans/README.md`.

## Own

- `plans/README.md`
- `plans/in-progress/`
- future `plans/archive/YYYY/` lifecycle hygiene
- durable steward rollups and roadmap sequencing snapshots
