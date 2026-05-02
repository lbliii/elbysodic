# Plans

Plans are working snapshots for product and architecture direction. They are
not scratchpads, permanent specs, or a second issue tracker.

Use a plan when a decision needs continuity across agent sessions: steward
rollups, multi-step implementation plans, migration strategies, or roadmap
sequencing. Keep ordinary notes in the PR, issue, or final response instead.

## Lifecycle

Active plans live in `plans/in-progress/` and must appear in the Active Plans
table below. Every active plan needs a status, owner, created date, last updated
date, review-by date, and closure criteria.

When a plan is no longer active:

- move completed, superseded, or abandoned plans to `plans/archive/YYYY/`
- remove them from the Active Plans table
- leave a short final note in the plan explaining why it moved

Do not leave stale plans in `plans/in-progress/`. If a plan has not been
updated by its review-by date, the next agent should either refresh it, split
it into concrete work, or archive it as superseded/abandoned.

## Naming

Use lowercase kebab-case:

```text
plans/in-progress/<topic>-<yyyy-mm-dd>.md
```

Prefer stable topic names over vague labels. Good names:

- `steward-backlog-rollup-2026-05-01.md`
- `studio-production-workflows-2026-05-15.md`
- `program-blueprint-intake-2026-06-02.md`

## Active Plans

| Plan | Status | Owner | Review By | Closure Criteria |
| --- | --- | --- | --- | --- |
| [Appearance Studio roadmap 2026-05-01](in-progress/appearance-studio-roadmap-2026-05-01.md) | in-progress | Product/UI stewardship | 2026-05-22 | Split into implementation issues or PR-sized plans covering the theme editor, ritual-surface variants, validation, and import/export support. |
| [Auth and seed QA roadmap 2026-05-01](in-progress/auth-seed-qa-roadmap-2026-05-01.md) | in-progress | Auth, seed, and browser QA stewardship | 2026-05-22 | Split into PR-sized tasks for seed personas, local login sessions, persona matrix docs, and capability granularity. |
| [Location and board media epic 2026-05-02](in-progress/location-board-media-epic-2026-05-02.md) | in-progress | Product/UI stewardship | 2026-05-23 | Split into PRs for accessible board media rendering, seeded location art throughlines, Studio QA controls, and Blueprint alignment. |
| [Living canon layer 2026-05-02](in-progress/living-canon-layer-2026-05-02.md) | drafted | Product, domain, storage, service, and web stewardship | 2026-05-30 | Split into PR-sized work for scene outcomes, source-linked canon entries, proposal review, rendered privacy coverage, and later automation/digest integration. |
| [Program Blueprint hydration 2026-05-02](in-progress/program-blueprint-hydration-2026-05-02.md) | drafted | Blueprint, service, storage, and test stewardship | 2026-05-23 | Split into PRs for dry-run diffs, service-layer hydration, rollback tests, tenant coverage, and Studio apply controls. |
| [Railway auth hardening 2026-05-02](in-progress/railway-auth-hardening-2026-05-02.md) | local verification green; awaiting Railway smoke | Auth, service, web, and deployment stewardship | 2026-05-09 | Production mode no longer trusts dev identity, write routes require session and CSRF, secure cookies are configured, demo credentials are intentional, and Railway smoke passes. |
| [Steward backlog rollup 2026-05-01](in-progress/steward-backlog-rollup-2026-05-01.md) | in-progress | Steward workflow | 2026-05-15 | Split into concrete backlog items or archive as superseded. |
| [Studio production workflows 2026-05-02](in-progress/studio-production-workflows-2026-05-02.md) | drafted | Product, web, service, storage, and test stewardship | 2026-05-23 | Split into focused implementation PRs for board/world editing, application and claim review, wanted outcomes, and director operations shortcuts. |
| [Tenant routing and shell release 2026-05-02](in-progress/tenant-routing-and-shell-release-2026-05-02.md) | implemented; awaiting shared-host smoke and timing readout | Web, service, storage, domain, and Chirp integration stewardship | 2026-05-16 | Chirp shell navigation no longer blanks inner content, shared-host links carry community context, clean community-host URLs remain supported, and routing latency has a measured owner. |
