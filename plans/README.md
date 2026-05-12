# Plans

Plans are working snapshots for product and architecture direction. They are
not scratchpads, permanent specs, or a second issue tracker.

Use a plan when a decision needs continuity across agent sessions: steward
rollups, multi-step implementation plans, migration strategies, or roadmap
sequencing. Keep ordinary notes in the PR, issue, or final response instead.

## Strategy Anchor

All product-facing plans should align with
[`docs/product/strategy-spine.md`](../docs/product/strategy-spine.md). That
spine names the three top-level pillars:

- Realm Studio: director and staff workflows for running PBP realms.
- Writer Network: writer identity, active face, obligations, discovery, and
  continuation.
- Continuity Graph: reviewed, source-linked story memory after trust,
  privacy, transaction, and provenance gates are solid.

Plans may focus on one pillar or a foundation that enables several pillars,
but they should not introduce generic forum, SaaS dashboard, marketplace, chat,
or AI-first directions that bypass the spine.

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
| [Layered shell navigation 2026-05-11](in-progress/layered-shell-navigation-2026-05-11.md) | active implementation plan; phases 1-4 plus writer-hub, handoff, Studio hub, writing-flow cleanup, and public-preview shell slices are merged | Product, design, web, privacy, and test stewardship | 2026-05-25 | The accepted layered shell model is implemented or split into merged PRs; stale `World`/`Play` labels are replaced; compact sidebar means icon rail; rail, inner shell, and mobile drawer share one server-side navigation model; privacy-gated badges/rows have rendered tests; desktop, compact, focus, and mobile browser QA are recorded. |
| [Page surface conversion 2026-05-11](in-progress/page-surface-conversion-2026-05-11.md) | active planning artifact; Desk/writer hub, Wanted/Casting/Claims/Plotting, Studio hub, writing-flow, and public-preview slices are merged | Product design, web, Writer Network, Realm Studio, privacy, and rendered-route tests | 2026-05-25 | Major pages have been converted to the layered shell model; duplicate shell links and passive active-face repetition are removed; empty sections follow an explicit display policy; repeated page patterns are promoted to shared Elbysodic components; rendered tests and browser QA cover converted flows. |
| [Product research system 2026-05-10](in-progress/product-research-system-2026-05-10.md) | active methodology plan | Product, research, UX, planning, and test stewardship | 2026-06-07 | The research folder has reusable templates for source notes, competitive audits, synthetic panel runs, real interview notes, UAT sessions, and synthesis promotion; at least three product flows have been evaluated through the system; accepted findings are reflected in product docs, plans, or test proof without confusing simulated signal for real evidence. |
| [Non-AI PBP Studio roadmap 2026-05-10](in-progress/non-ai-pbp-studio-roadmap-2026-05-10.md) | active research-backed sequencing snapshot; staging proof, invite-first onboarding, guided opening packet, invite management, and public browser QA are recorded; catalog fields and no-face polish remain | Product, research, web, service, storage, design, and test stewardship | 2026-05-31 | Split the top roadmap phases into PR-sized implementation plans or mark them superseded by existing active plans; archive when Elbysodic has a verified non-AI alpha path from first realm setup through daily writing, director operations, and invite-first onboarding. |
| [Post-PR31 priority roadmap 2026-05-10](in-progress/post-pr31-priority-roadmap-2026-05-10.md) | active sequencing snapshot; initial staging smoke, backup/restore, invites, guided builder, browser QA, and first privacy-gap closures are recorded; remaining work is notification count privacy, ops inspection, invite delivery, and catalog fields | Product, operations, web, service, storage, and test stewardship | 2026-05-24 | The first five priorities are merged or superseded by more specific implementation plans, and remaining items are linked into the production-readiness roadmap, Studio roadmap, or archived as not-now. |
| [First realm setup 2026-05-10](in-progress/first-realm-setup-2026-05-10.md) | implemented and merged; builder follow-up landed, launch status follow-up remains | Service/auth, storage, web, tests, docs, and planning stewardship | 2026-05-24 | Archive after final local gate verification or preserve as a foundation note once remaining onboarding work is confirmed in the community creator onboarding plan. |
| [Community creator onboarding 2026-05-10](in-progress/community-creator-onboarding-2026-05-10.md) | active product and implementation plan; minimum builder, invite management, and no-face invite continuation landed; delivery/polish/launch-status work remains | Product, web, service, storage, auth, Blueprint, docs, and test stewardship | 2026-05-30 | Split into implementation PRs for first realm setup, guided realm builder, invitation handoff, launch checklist, and docs/test collateral; archive when those PRs land or this plan is superseded by a more specific hosted onboarding roadmap. |
| [Wanted backstage handoff 2026-05-09](in-progress/wanted-backstage-handoff-2026-05-09.md) | implemented locally; archive after full gate verification | Product, service, web, storage, and test stewardship | 2026-05-30 | Archive after the full local gate passes or any remaining same-user-different-community proof gap is moved into the production-readiness roadmap. |
| [Wattpad competitive research 2026-05-09](in-progress/wattpad-competitive-research-2026-05-09.md) | active research input; not an implementation plan | Product and planning stewardship | 2026-06-06 | Translate accepted lessons into focused roadmap slices for backstage collaboration, scene-safe social reading, writer progression, discovery, safety, and export guarantees; archive when those slices are either captured elsewhere or explicitly deferred. |
| [Production readiness roadmap 2026-05-09](in-progress/production-readiness-roadmap-2026-05-09.md) | active production gate; staging Railway smoke, backup/restore, public browser QA, invites, builder proof, and first privacy-gap closures are recorded; production bootstrap and notification count privacy remain | Cross-steward production readiness | 2026-05-16 | Railway smoke is recorded, schema/seed persistence risks are resolved or explicitly deferred, S-tier core user flows have rendered and browser proof, and follow-up work is split into PR-sized implementation plans. |
| [Railway auth hardening 2026-05-02](in-progress/railway-auth-hardening-2026-05-02.md) | local contract implemented; live Railway smoke still blocks closure | Auth, service, web, and deployment stewardship | 2026-05-16 | Production mode no longer trusts dev identity, write routes require session and CSRF, secure cookies are configured, demo credentials are intentional, Railway volume persistence is proven, and Railway smoke passes. |
| [Tenant routing and shell release 2026-05-02](in-progress/tenant-routing-and-shell-release-2026-05-02.md) | implemented locally; production smoke and global entry polish remain | Web, service, storage, domain, and Chirp integration stewardship | 2026-05-16 | Chirp shell navigation no longer blanks inner content, shared-host links carry community context, clean community-host URLs remain supported, and Railway shared-host smoke passes. |
| [Auth and seed QA roadmap 2026-05-01](in-progress/auth-seed-qa-roadmap-2026-05-01.md) | mostly implemented; onboarding posture and capability granularity remain | Auth, seed, and browser QA stewardship | 2026-05-30 | Seed personas, local login sessions, persona matrix docs, production demo-account posture, startup seed persistence, and capability-granularity decisions are split or closed. |
| [Program Blueprint hydration 2026-05-02](in-progress/program-blueprint-hydration-2026-05-02.md) | active; dry-run exists and apply remains gated | Blueprint, service, storage, and test stewardship | 2026-05-30 | Split into PRs for dry-run diffs, unknown-key diagnostics, service-layer hydration, rollback tests, tenant coverage, and Studio apply controls. |
| [Studio Network homepage 2026-05-03](in-progress/studio-network-homepage-2026-05-03.md) | partially implemented; public catalog and public realm previews landed, catalog fields/browser QA/personalization remain | Product/UI and network homepage stewardship | 2026-05-30 | Split into PR-sized work for the editorial platform home, NetworkHome read model, privacy-safe public browsing/search, responsive browser QA, and later personalization/search lanes. |
| [Studio production workflows 2026-05-02](in-progress/studio-production-workflows-2026-05-02.md) | active after production gates | Product, web, service, storage, and test stewardship | 2026-05-30 | Split into focused implementation PRs for board/world editing, application and claim review, wanted outcomes, director operations shortcuts, and rendered privacy proof. |
| [Community sidebar navigation 2026-05-03](in-progress/community-sidebar-navigation-2026-05-03.md) | superseded by layered shell navigation; archive candidate | Product/UI stewardship | 2026-05-30 | Historical context only; archive on the next plan-hygiene pass now that useful notes have moved into the layered shell plan. |
| [Appearance Studio roadmap 2026-05-01](in-progress/appearance-studio-roadmap-2026-05-01.md) | partially superseded by production-readiness sequencing | Product/UI stewardship | 2026-06-06 | Remaining theme editor, health warning, ritual variant, and import/export work is split only after core auth/storage/privacy gates are stable. |
| [Living canon layer 2026-05-02](in-progress/living-canon-layer-2026-05-02.md) | deferred until production trust gates close | Product, domain, storage, service, and web stewardship | 2026-06-13 | Split into PR-sized work for manual scene outcomes, source-linked canon entries, proposal review, rendered privacy coverage, and later automation/digest integration. |
| [Location and board media epic 2026-05-02](in-progress/location-board-media-epic-2026-05-02.md) | implemented; archive candidate after final verification note | Product/UI stewardship | 2026-05-16 | Preserve final status and archive once Blueprint/export follow-up is either linked elsewhere or explicitly deferred. |
| [Steward backlog rollup 2026-05-01](in-progress/steward-backlog-rollup-2026-05-01.md) | superseded by production-readiness roadmap; archive candidate | Steward workflow | 2026-05-16 | Archive after preserving remaining useful minority reports and links into the production-readiness roadmap. |
