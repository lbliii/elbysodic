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
| [Current epic priority rollup 2026-06-15](in-progress/current-epic-priority-rollup-2026-06-15.md) | active sequencing snapshot after issue burn-down | Cross-steward planning, production trust, storage, service, web, docs, tests, Blueprint, and Continuity stewardship | 2026-06-29 | Remaining open sagas/epics are split into approved PR-sized slices, approval-bound decisions are recorded on the relevant issues or docs, and the next implementation wave has local proof or a live-ops owner where required. |
| [Community hub editorial iteration 2026-05-18](in-progress/community-hub-editorial-iteration-2026-05-18.md) | implementation wave landed; follow-up saga planned | Product design, Writer Network, Realm Studio, service, web, storage/seed, tests, and surface-contract stewardship | 2026-06-01 | `/c/{community_slug}` reads as an elegant story-facing realm hub with service-owned story, premise-stage, lore, cast, places, wanted, and activity sections; redundant labels and CRM/dashboard patterns are removed; representative original-premise seed proof, rendered tests, and browser QA pass the Surface Quality Bar; or the plan is split into narrower implementation plans. |
| [Community landing design-system translation 2026-05-15](in-progress/community-landing-design-system-translation-2026-05-15.md) | draft implementation plan after static V2 prototype plus premise-archetype stress pass | Product design, Chirp/web, service, privacy, tests, and docs stewardship | 2026-05-29 | The community landing V2 prototype is translated into service-owned public/member/applicant read models, Chirp-composed Elbysodic components, theme-layer CSS, privacy-tested rendered routes, desktop/mobile browser QA, and docs/checklist updates; or the prototype is explicitly superseded by a narrower gateway plan. |
| [Thread scene media contract 2026-05-15](in-progress/thread-scene-media-contract-2026-05-15.md) | gated follow-up; do not implement until schema, editor, and Blueprint surface are accepted | Product design, storage, service, web, Blueprint, privacy, and tests | 2026-06-12 | Thread-specific scene media is implemented with tenant-aware schema/repository/service/editor/Blueprint proof, or inherited media is accepted as sufficient and this plan is archived as not-now. |
| [Wanted to scene relationship contract 2026-05-15](in-progress/wanted-to-scene-relationship-contract-2026-05-15.md) | gated follow-up; relationship contract required before implementation | Product, service, storage, web, privacy, and tests | 2026-06-12 | Wanted hooks can be explicitly attached to scenes through a tenant-aware service-owned relationship with privacy/rendered proof, or this is archived as superseded by plotting-room source links. |
| [Continuity source grounding contract 2026-05-15](in-progress/continuity-source-grounding-contract-2026-05-15.md) | gated follow-up; blocked on Continuity Graph provenance and review | Continuity Graph, product, storage, service, web, privacy, and tests | 2026-06-19 | Source-linked continuity/canon grounding appears in scene context only after manual provenance, review state, visibility, and privacy contracts exist; otherwise this remains deferred. |
| [Layered shell navigation 2026-05-11](in-progress/layered-shell-navigation-2026-05-11.md) | active implementation plan; phases 1-4 plus writer-hub, handoff, Studio hub, writing-flow cleanup, and public-preview shell slices are merged | Product, design, web, privacy, and test stewardship | 2026-05-25 | The accepted layered shell model is implemented or split into merged PRs; stale `World`/`Play` labels are replaced; compact sidebar means icon rail; rail, inner shell, and mobile drawer share one server-side navigation model; privacy-gated badges/rows have rendered tests; desktop, compact, focus, and mobile browser QA are recorded. |
| [Page surface conversion 2026-05-11](in-progress/page-surface-conversion-2026-05-11.md) | active planning artifact; Desk/writer hub, Wanted/Casting/Claims/Plotting, Studio hub, writing-flow, and public-preview slices are merged | Product design, web, Writer Network, Realm Studio, privacy, and rendered-route tests | 2026-05-25 | Major pages have been converted to the layered shell model; duplicate shell links and passive active-face repetition are removed; empty sections follow an explicit display policy; repeated page patterns are promoted to shared Elbysodic components; rendered tests and browser QA cover converted flows. |
| [Premise discovery surface and seed depth 2026-05-15](in-progress/premise-discovery-surface-and-seed-depth-2026-05-15.md) | draft next-phase implementation plan after discovery profiles and nine original premise communities landed | Product research, Writer Network, Realm Studio, storage, service, web, tests, docs, and planning stewardship | 2026-06-12 | Public discovery surfaces, Director Studio discovery-profile editing, original-premise seed depth, demo posture, persona/browser QA, and related model extensions are either implemented in PR-sized slices with proof or split into narrower accepted plans. |
| [Premise seed data expansion 2026-05-15](in-progress/premise-seed-data-expansion-2026-05-15.md) | active implementation plan; discovery profile foundation and nine original premise communities landed | Product research, storage/seed, Blueprint, service, web, tests, and docs stewardship | 2026-06-05 | The nine premise-based demo communities are implemented through PR-sized seed slices with tenant-scoped proof, updated persona/docs/test coverage, and public Explore readiness; or the nine-community slate is explicitly superseded by a narrower seed-slate plan. |
| [Product research system 2026-05-10](in-progress/product-research-system-2026-05-10.md) | active methodology plan | Product, research, UX, planning, and test stewardship | 2026-06-07 | The research folder has reusable templates for source notes, competitive audits, synthetic panel runs, real interview notes, UAT sessions, and synthesis promotion; at least three product flows have been evaluated through the system; accepted findings are reflected in product docs, plans, or test proof without confusing simulated signal for real evidence. |
| [Non-AI PBP Studio roadmap 2026-05-10](in-progress/non-ai-pbp-studio-roadmap-2026-05-10.md) | active research-backed sequencing snapshot; staging proof, invite-first onboarding, guided opening packet, invite management, launch status, catalog posture, and browser QA are recorded | Product, research, web, service, storage, design, and test stewardship | 2026-05-31 | Split the top roadmap phases into PR-sized implementation plans or mark them superseded by existing active plans; archive when Elbysodic has a verified non-AI alpha path from first realm setup through daily writing, director operations, and invite-first onboarding. |
| [Post-PR31 priority roadmap 2026-05-10](in-progress/post-pr31-priority-roadmap-2026-05-10.md) | active sequencing bridge; first priorities mostly merged, archived, or superseded by narrower plans | Product, operations, web, service, storage, and test stewardship | 2026-06-01 | The first five priorities are merged or superseded by more specific implementation plans, and remaining items are linked into the production-readiness roadmap, Studio roadmap, or archived as not-now. |
| [Community creator onboarding 2026-05-10](in-progress/community-creator-onboarding-2026-05-10.md) | active product and implementation plan; minimum builder, invite management, launch status, and no-face invite continuation landed; delivery/polish work remains | Product, web, service, storage, auth, Blueprint, docs, and test stewardship | 2026-05-30 | Split into implementation PRs for first realm setup, guided realm builder, invitation handoff, launch checklist, and docs/test collateral; archive when those PRs land or this plan is superseded by a more specific hosted onboarding roadmap. |
| [Wattpad competitive research 2026-05-09](in-progress/wattpad-competitive-research-2026-05-09.md) | active research input; not an implementation plan | Product and planning stewardship | 2026-06-06 | Translate accepted lessons into focused roadmap slices for backstage collaboration, scene-safe social reading, writer progression, discovery, safety, and export guarantees; archive when those slices are either captured elsewhere or explicitly deferred. |
| [Production readiness roadmap 2026-05-09](in-progress/production-readiness-roadmap-2026-05-09.md) | active production gate; local auth, tenant, privacy, access-request, and community-landing browser gates have proof; live Railway smoke remains | Cross-steward production readiness | 2026-06-01 | Railway smoke is recorded, schema/seed persistence risks are resolved or explicitly deferred, S-tier core user flows have rendered and browser proof, and follow-up work is split into PR-sized implementation plans. |
| [Railway auth hardening 2026-05-02](in-progress/railway-auth-hardening-2026-05-02.md) | local contract implemented and locally verified; live Railway smoke still blocks closure | Auth, service, web, and deployment stewardship | 2026-06-01 | Production mode no longer trusts dev identity, write routes require session and CSRF, secure cookies are configured, demo credentials are intentional, Railway volume persistence is proven, and Railway smoke passes. |
| [Tenant routing and shell release 2026-05-02](in-progress/tenant-routing-and-shell-release-2026-05-02.md) | implemented locally and locally verified; production shared-host smoke remains | Web, service, storage, domain, and Chirp integration stewardship | 2026-06-01 | Chirp shell navigation no longer blanks inner content, shared-host links carry community context, clean community-host URLs remain supported, and Railway shared-host smoke passes. |
| [Auth and seed QA roadmap 2026-05-01](in-progress/auth-seed-qa-roadmap-2026-05-01.md) | mostly implemented; onboarding posture and capability granularity remain | Auth, seed, and browser QA stewardship | 2026-05-30 | Seed personas, local login sessions, persona matrix docs, production demo-account posture, startup seed persistence, and capability-granularity decisions are split or closed. |
| [Program Blueprint hydration 2026-05-02](in-progress/program-blueprint-hydration-2026-05-02.md) | active; dry-run exists and apply remains gated | Blueprint, service, storage, and test stewardship | 2026-05-30 | Split into PRs for dry-run diffs, unknown-key diagnostics, service-layer hydration, rollback tests, tenant coverage, and Studio apply controls. |
| [Network catalog metadata and slices 2026-05-13](in-progress/network-catalog-metadata-slices-2026-05-13.md) | implementation partially landed; profile/tag storage, public read models, route wiring, seed profiles, and product-doc promotion are in place | Product, services, web, storage, tests, docs, and planning stewardship | 2026-05-27 | `/` and `/network` are backed by service-owned public catalog read models; public cards and search use explicit `community_id`-scoped discovery profiles/tags instead of template or slug heuristics; privacy tests prove no backstage, private, member, active-face, staff, draft, notification, or plotting-room leakage; premise archetype discovery supports the seed slate; docs, migrations, tests, and changelog are updated. |
| [Studio Network homepage 2026-05-03](in-progress/studio-network-homepage-2026-05-03.md) | partially implemented; public catalog and public realm previews landed, catalog fields/browser QA/personalization remain | Product/UI and network homepage stewardship | 2026-05-30 | Split into PR-sized work for the editorial platform home, NetworkHome read model, privacy-safe public browsing/search, responsive browser QA, and later personalization/search lanes. |
| [Studio production workflows 2026-05-02](in-progress/studio-production-workflows-2026-05-02.md) | active after production gates | Product, web, service, storage, and test stewardship | 2026-05-30 | Split into focused implementation PRs for board/world editing, application and claim review, wanted outcomes, director operations shortcuts, and rendered privacy proof. |
| [Appearance Studio roadmap 2026-05-01](in-progress/appearance-studio-roadmap-2026-05-01.md) | partially superseded by production-readiness sequencing | Product/UI stewardship | 2026-06-06 | Remaining theme editor, health warning, ritual variant, and import/export work is split only after core auth/storage/privacy gates are stable. |
| [Living canon layer 2026-05-02](in-progress/living-canon-layer-2026-05-02.md) | deferred until production trust gates close | Product, domain, storage, service, and web stewardship | 2026-06-13 | Split into PR-sized work for manual scene outcomes, source-linked canon entries, proposal review, rendered privacy coverage, and later automation/digest integration. |
