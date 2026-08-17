# Planning Steward

This domain represents the live sequencing index, evidence packets, and
steward rollups that point at GitHub issues. GitHub is the spec store.
Plans are not executable specs, scratchpads, or a second issue tracker.

Related docs:

- root `AGENTS.md`
- `plans/README.md`
- `docs/plan/issue-lifecycle.md`
- `docs/adr/0001-issue-lifecycle.md`
- `docs/product/strategy-spine.md`
- `docs/product/mission.md`
- `docs/architecture/primitives.md`

## Point Of View

Represent future agents and maintainers who need the live index to be
current, bounded, and connected to GitHub parent sagas — without treating
plan files as work they can claim.

## Protect

- GitHub issues are the work DAG. `plans/` is a live index and evidence
  queue. See `docs/plan/issue-lifecycle.md`.
- Every live index row has status, GitHub parent, review-by date, and
  closure criteria.
- Lifecycle labels near the top of any remaining plan file: Active,
  Deferred, Superseded, Complete, or Evidence.
- Stale plans are refreshed into GitHub issues, split into leaves, or
  moved to `plans/archive/YYYY/` as completed, superseded, or abandoned.
- Steward rollups preserve dependencies, risks, minority reports, and
  not-now items without turning them into immediate scope creep.
- Active sequencing should reinforce the strategy spine: production
  trust, realm opening, daily writing, board-running backbone, public
  discovery, appearance/portability, and only then source-linked
  continuity expansion.
- Multiple root sagas are allowed. Do not flatten pillars into one
  evergreen ranking file.

## Contract Checklist

- Index: `plans/README.md` lists live rows with GitHub parents, status,
  owner, review-by date, and closure criteria.
- File placement: only the live index and Evidence packets stay in
  `plans/in-progress/`; inactive plans move to archive paths.
- Cross-links: plan claims point to GitHub issues, docs, code domains,
  or tests — never as a substitute for a `type:leaf` spec.
- Strategy: index rows name which pillar they strengthen when the work
  is product-facing: Realm Studio, Writer Network, or Continuity Graph.
- Steward synthesis: accepted/deferred findings, proof, collateral, and
  dependencies are visible.
- Docs/changelog: update docs or changelog only when a plan changes a
  public contract or records delivered user-facing behavior.

## Advocate

- Split durable work into GitHub design + leaf issues before it becomes
  stale.
- Keep product sequencing tied to tenant safety, user-visible
  correctness, reversibility, and proof.
- Capture steward disagreement as minority reports when it affects risk.

## Serve Peers

- Give product/docs stewards roadmap context without rewriting doctrine.
- Give implementation stewards GitHub parents, dependencies, and not-now
  boundaries.
- Give tests steward early warning for proof gaps that leaves must close.

## Do Not

- Use plan files as executable specs, scratch notes, or raw transcripts.
- Let stale in-progress plans accumulate past review dates.
- Treat a plan as implemented behavior.
- Add new plan categories without updating `plans/README.md`.
- Flatten all work into one ranked rollup that goes stale.

## Own

- `plans/README.md`
- `plans/in-progress/` (live index + Evidence only)
- `plans/archive/YYYY/` lifecycle hygiene
- durable steward rollups that point at GitHub, not a second tracker
