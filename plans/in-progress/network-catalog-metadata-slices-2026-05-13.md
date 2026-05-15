# Network Catalog Metadata And Slices

Status: implementation partially landed; profile/tag storage, public read models,
route wiring, seed profiles, and product-doc promotion are in place
Owner: Product, services, web, storage, tests, docs, and planning stewardship
Created: 2026-05-13
Last updated: 2026-05-15
Review by: 2026-05-27
Closure criteria: `/` and `/network` are backed by service-owned public catalog
read models; public cards and search use explicit `community_id`-scoped
discovery profiles/tags instead of template or slug heuristics; privacy tests
prove no backstage, private, member, active-face, staff, draft, notification, or
plotting-room leakage; premise archetype discovery supports the seed slate; docs,
migrations, tests, and changelog are updated.

## Purpose

The 2026-05-15 PBP premise research changed this plan from a reversible
service-metadata slice into a real public discovery primitive.

Current problems:

- `/` and `/network` are visually close to the desired Explore direction, but
  they still pass `StudioNetworkDirectory` and route-local search data into the
  template instead of rendering the named `NetworkHomeView` and
  `NetworkExploreView` service contracts.
- Public search currently infers discovery categories from slugs and names such
  as `hp`, `jurassic`, `x-men`, `small-town`, and `nyc`.
- Browse chips and shelves are hard-coded around old genre buckets and wanted
  pressure, while the research shows writers compare premise engine, entry
  readiness, lore aperture, access posture, activity pace, rating, current
  chapter, roster/canon shape, and touchpoint posture.
- Published premise materials carry rich prose, but prose alone is too brittle
  for homepage slices, Explore filters, seed census proof, and director-owned
  public positioning.

This plan adds a tenant-scoped community discovery profile and public discovery
signals, then routes homepage, Explore, and public cards through service-owned
read models.

Canonical product lens: `docs/product/community-shapes.md`.

## Research Inputs

- `research/synthesis/2026-05-15-current-pbp-premise-archetypes.md`
- `research/synthesis/2026-05-15-pbp-premise-census-followup.md`
- `research/synthesis/2026-05-15-premise-archetype-reference-skeletons.md`
- `plans/in-progress/premise-seed-data-expansion-2026-05-15.md`

Evidence mode:

- Source signal: current public PBP/Jcink ads and directories.
- Research inference: premise engines are more useful than broad genre labels.
- Accepted product implication: Explore/search and seed data should classify
  communities by PBP premise fit, writer jobs, and public entry readiness.
- Deferred/open: exact director editing UI and future Blueprint import shape.

## Steward Synthesis

Consulted stewards:

- Storage and Migration
- Service and Surface Contract
- Web/Explore UX
- Blueprint Contract
- Product Docs and Research
- Tests and Privacy

Accepted findings:

- Add separate discovery tables rather than widening `communities` with many
  optional public-catalog fields.
- Keep every discovery row tenant-scoped by `community_id`.
- Use explicit repository methods for discovery profile/tag reads and writes.
- Route `/` through `services.network_home()` and `/network` through
  `services.network_explore(query)`; templates should not own taxonomy,
  ranking, or slice membership.
- Keep `PublicCatalogCard` or a named public profile read model as the only
  card shape for homepage, Explore, public search, and public cards.
- Put signed-in continuation state in `NetworkReturnPath` or a separate member
  lane, not in public catalog cards.
- Remove slug/name archetype inference except ordinary text matching on public
  visible names and summaries.
- Keep current event/chapter as published `event` materials. Discovery profiles
  may point to a featured event material, but they should not duplicate event
  body or become a parallel event source of truth.
- Keep discovery metadata out of `ProgramBlueprint` for the first implementation.
  A future `BlueprintDiscovery` extension needs typed fields, allowlists,
  preview rows, hydration, docs, and tests.
- Keep reference skeletons in research and seed-authoring notes, not rendered
  public catalog metadata.
- Balance first-entry lanes around premise/world, current chapter, roster/face
  energy, mood/tone, play pace, open scenes, application posture, and wanted
  hooks. Wanted hooks remain visible but should not lead every path.

Deferred:

- Director-editable Studio form for discovery profiles.
- Persisted editorial collections beyond profile/tag-driven slices.
- `/explore` public route migration.
- Blueprint discovery import.
- Demographic personalization, social graph, marketplace ranking, and
  Continuity Graph-derived recommendations.

Minority reports:

- No steward objected to the separate profile/tag tables. The main caution is
  sequencing: storage and tests want schema/migration proof in the same PR as
  repository methods, while Blueprint wants import fields deferred until after
  storage and rendered discovery stabilize.

## Product Contract

Community shapes:

- A community is discovered by premise engine first, then genre/tone/access
  metadata.
- Sanctuary sandboxes and wanted-hook-first groups are not homepage/Explore
  archetypes.
- Wanted hooks, claims, reserves, rosters, canons, applications, scenes, and
  current chapters are entry paths and proof points inside a premise community.

Public discovery should answer:

- What kind of story engine does this realm make easy?
- Can I start with an OC, canon, wanted hook, starter scene, current chapter, or
  application?
- How much lore do I need before my first face?
- What is the age/rating and activity pace?
- Is the realm forum-first, Discord-light, or using Discord for plotting or
  onboarding?
- What is moving right now?
- Are claims, reserves, rosters, wanted hooks, and application paths open?

Touchpoint rule:

- Explore may expose adjunct posture such as `forum-first`,
  `Discord-light`, or `Discord for plotting`.
- Canonical objects remain Elbysodic-owned: premise materials, current event
  materials, boards, threads/scenes, faces, wanted hooks, claims, reserves,
  applications, and plotters.

## Proposed Schema

Use a one-row-per-community profile plus repeatable public discovery signals.

```text
community_discovery_profiles
- community_id INTEGER PRIMARY KEY REFERENCES communities(id) ON DELETE CASCADE
- premise_archetype TEXT NOT NULL DEFAULT ''
- play_engine TEXT NOT NULL DEFAULT ''
- lore_aperture TEXT NOT NULL DEFAULT ''
- access_model TEXT NOT NULL DEFAULT ''
- application_model TEXT NOT NULL DEFAULT ''
- age_rating TEXT NOT NULL DEFAULT ''
- content_rating TEXT NOT NULL DEFAULT ''
- activity_pace TEXT NOT NULL DEFAULT ''
- activity_expectation TEXT NOT NULL DEFAULT ''
- forum_adjunct TEXT NOT NULL DEFAULT ''
- roster_posture TEXT NOT NULL DEFAULT ''
- catalog_pitch TEXT NOT NULL DEFAULT ''
- onboarding_pitch TEXT NOT NULL DEFAULT ''
- staff_pick_label TEXT NOT NULL DEFAULT ''
- featured_event_material_id INTEGER REFERENCES materials(id) ON DELETE SET NULL
- created_at TEXT NOT NULL
- updated_at TEXT NOT NULL
```

```text
community_discovery_tags
- id INTEGER PRIMARY KEY
- community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE
- tag_type TEXT NOT NULL
- tag_key TEXT NOT NULL
- label TEXT NOT NULL
- search_text TEXT NOT NULL DEFAULT ''
- sort_order INTEGER NOT NULL DEFAULT 0
- created_at TEXT NOT NULL
- updated_at TEXT NOT NULL
- UNIQUE (community_id, tag_type, tag_key)
```

Indexes:

- `idx_community_discovery_tags_community`
  on `(community_id, tag_type, sort_order, id)`
- optional search helper index on `(community_id, tag_key)` if tests show it is
  useful

Allowed profile values should live as service/domain constants first:

- Premise archetype: small-town social web, weird-town mystery, urban
  supernatural pressure cooker, court-and-faction fantasy, original
  canon-adjacent AU, fame and industry drama, survival/trials, occult
  historical pressure, strange frontier.
- Play engine: character-driven, event-driven, mystery-driven, faction-driven,
  institution-driven, canon-adjacent, survival-driven.
- Lore aperture: low-lore real life, open lore, original lore, semi-open lore,
  canon-divergent, closed canon.
- Access/application: public preview, invite/referral, interest form, short
  app, profile app, canon app, member app.
- Touchpoint posture: forum-first, Discord-light, Discord for plotting,
  Discord for onboarding, Discord for lore drops.

Discovery tags are not generic director-defined facets. They are public catalog
signals with allowlisted `tag_type` values such as:

- `genre`
- `tone`
- `premise`
- `pressure`
- `entry_path`
- `pace`
- `format`
- `content`
- `roster`
- `access`

## Surface Contract

Homepage `/`:

- Uses `NetworkHomeView`.
- Shows a featured public realm, premise archetype shelves, recent/current
  chapter shelves, entry-readiness shelves, and a small signed-in return path.
- Does not render member names, active faces, unread counts, staff state,
  private queues, applications, or plotting rooms in public cards.

Explore `/network`:

- Uses `NetworkExploreView`.
- Filters by story fit and entry readiness, not generic marketplace tags.
- Searches public discovery profile fields, public discovery tags, published
  premise/current-event summaries, public board labels where accepted, and safe
  counts.
- Does not search drafts, private/staff facets, private boards, staff notes,
  applications, notifications, member names, active faces, or backstage realms.

Public community preview:

- Can show premise archetype, catalog pitch, rating, pace, access, application
  posture, touchpoint posture, current chapter link, roster/canon posture, open
  wanted count, and claims/reserves posture.
- Should link to canonical objects: premise, current event, wanted hooks,
  roster/faces, boards/scenes, applications, claims, and reserves.

Signed-in continuation:

- Belongs in a separate return lane: desk link, current community, active face,
  unread count, or membership switch.
- Must not be baked into public catalog cards.

## Implementation Plan

### Phase 0: Baseline Alignment

Status: landed in the community discovery profile implementation.

Goal: remove drift before adding durable discovery storage.

Work:

- Update the migration docs version drift: code is at schema version 16 while
  docs currently say 14.
- Confirm current `/` and `/network` privacy tests before changing card shapes.
- Confirm `NetworkHomeView` and `NetworkExploreView` are the route-level
  contracts to preserve.

Proof:

- Existing public network/security tests pass before the migration PR starts.

Collateral:

- `docs/architecture/migrations.md`

### Phase 1: Discovery Schema And Repositories

Status: landed for seed/admin-owned profiles and tags; director editing remains
deferred.

Goal: add the tenant-scoped storage primitive.

Work:

- Add `community_discovery_profiles` and `community_discovery_tags` to fresh
  `SCHEMA`.
- Add ordered migration version 17 in `src/elbysodic/db/migrations.py`.
- Increment `CURRENT_SCHEMA_VERSION` and keep migrations contiguous.
- Add domain row models if needed.
- Add repository methods:
  - `get_discovery_profile(community_id)`
  - `upsert_discovery_profile(...)`
  - `list_discovery_profiles_for_communities(community_ids)`
  - `list_discovery_tags_for_communities(community_ids)`
  - `replace_discovery_tags(community_id, tags)` or idempotent upsert helpers
- Ensure normal community reads work without a discovery profile.

Proof:

- Fresh schema and upgraded version-16 schema parity.
- One profile per community.
- Duplicate `tag_key` values allowed across different communities.
- `UNIQUE (community_id, tag_type, tag_key)` enforced inside one community.
- Cascade delete removes profile/tags with community.
- Repository batch reads return only requested communities.

Collateral:

- `docs/architecture/migrations.md`
- `docs/architecture/multi-tenancy.md`
- changelog fragment

### Phase 2: Service-Owned Public Read Models

Status: landed for public catalog cards, discovery profile/tag reads, and public
search text. Richer ranking and editorial collections remain deferred.

Goal: make public discovery service-owned before web templates consume it.

Work:

- Extend `NetworkCatalogRepository` with discovery profile/tag batch methods.
- Add public discovery read models for profile and tags.
- Add discovery profile to `PublicCatalogCard` or a nested public profile view.
- Keep member-only state out of `PublicCatalogCard`.
- Make `network_home()` and `network_explore()` build slices, facets, search
  results, and ranking from public card data.
- Keep public readiness gates:
  - `launch_status == public-preview`
  - published premise material
  - public scene hub
  - published current event if a featured event pointer is shown
- Remove slug/name archetype heuristics. Ordinary text matching on public name
  and public summaries can remain.

Proof:

- Service tests where a non-semantic slug is found by explicit archetype.
- Slug rename does not change archetype search results.
- A community without a profile does not match that archetype.
- Homepage slices contain only matching profile/tag cards.
- Ranking is deterministic.
- Backstage/invite-only communities with discovery rows do not appear in public
  home, Explore, public search, or public preview.

Collateral:

- `docs/architecture/surface-contract-architecture.md` if contract names move
- `docs/architecture/rendered-route-privacy-matrix.md`

### Phase 3: Web Surface Conversion

Status: landed for `/` and `/network` route ownership and public card rendering.
Further first-entry action statefulness remains follow-up work.

Goal: make homepage and Explore render the service contract cleanly.

Work:

- Update `/` route to call `services.network_home()`.
- Update `/network` route to call `services.network_explore(query)`.
- Render homepage slices from `NetworkHomeView`, not template-local lists.
- Render Explore filters and relationship lanes from `NetworkExploreView`.
- Split public preview cards from signed-in continuation cards.
- Rebalance browse lanes:
  - start with premise/world
  - start with current chapter
  - start with roster/face energy
  - start with mood/tone or pace
  - start with open scenes
  - start with application posture
  - start with wanted hooks
- Make first-entry actions stateful and explicit:
  - `Preview realm`
  - `Start application`
  - `Enter as <membership/face>`
  - `Switch to <realm>`
  - `Reserve wanted`
  - `Open plotting room`

Proof:

- Rendered tests for signed-out `/`, `/network`, and `/network?q=<public-tag>`.
- Rendered tests for signed-in multi-membership state proving public cards are
  unchanged and continuation state is separated.
- Negative assertions for member names, role labels, active-face text, unread
  counts, plotting rooms, staff notes, applications, draft terms, private room
  labels, and backstage realm names.
- Browser QA on desktop and mobile.

Collateral:

- `docs/product/navigation-menus.md` if labels/active state change
- `docs/product/control-topology.md` or information hierarchy docs for entry
  action labels
- changelog fragment

### Phase 4: Seed Integration

Status: first slice landed for the five existing public seed realms; the
nine-community original premise slate remains planned.

Goal: prove the premise taxonomy with deterministic seed data.

Work:

- Add discovery profiles/tags for current public seed communities first.
- Add idempotent seed helpers for profiles/tags.
- Seed exact premise-archetype coverage for the nine-community slate in
  `plans/in-progress/premise-seed-data-expansion-2026-05-15.md`.
- Keep reference skeleton titles out of public seed copy.
- Preserve same-global-user, different-community role proof in personas.

Proof:

- Running seed twice produces exact profile/tag counts.
- Seed census asserts each intended public-preview community has a profile,
  premise, current event/chapter material, public scene hub, roster/canon roles,
  wanted hooks, and discovery tags.
- Public `/network` shows intended public seed realms and omits private/staff
  strings.
- Public search finds archetypes from profile/tags, not slugs.

Collateral:

- `docs/architecture/seed-personas.md` if persona keys or purposes change
- seed/profile matrix in product or architecture docs
- premise seed plan status update

### Phase 5: Product Docs Promotion

Status: landed in `docs/product/community-shapes.md`.

Goal: promote research into a stable product contract without overclaiming.

Work:

- Add a concise `docs/product/community-shapes.md` or equivalent discovery
  guide.
- Label evidence modes: source signal, research inference, accepted product
  implication, deferred/open questions.
- Tie each discovery field to a user job.
- Update the network metadata plan and seed plan to point at the product guide.
- Keep exact market prevalence out of doctrine.

Proof:

- Docs name accepted fields and the user question each answers.
- Docs distinguish research references from public product metadata.
- Text check or seed/rendered assertions ensure public seed/catalog content does
  not include protected reference titles, character names, places, or plots.

Collateral:

- `docs/product/user-personas-panel.md` if premise discovery jobs are promoted
- `docs/product/strategy-spine.md` only if adding a bounded summary

### Phase 6: Blueprint Discovery Extension

Goal: decide later whether directors can import discovery profiles through
Program Blueprints.

Work:

- Defer until schema, services, public cards, and seed profiles stabilize.
- If accepted, add a typed `BlueprintDiscovery` extension with allowlisted
  fields, validation, preview rows, hydration, docs, YAML examples, and tests.
- Do not accept raw/freeform tags.

Proof:

- Parser/validation tests.
- Invalid-value and duplicate-value tests.
- Dry-run preview rows.
- Tenant-scoped hydration tests.
- Rendered discovery/search tests.

Collateral:

- `docs/product/program-blueprints.md`
- `tests/test_program_blueprints.py`
- changelog fragment

## Contract Matrix

| Contract | API/CLI | Programmatic | Protocol/Routes | Schema/Types | Docs | Examples/Seeds | Tests | Changelog |
|---|---|---|---|---|---|---|---|---|
| Discovery profile | N/A | repository methods and public read model | `/`, `/network`, public preview | `community_discovery_profiles` | product discovery, migrations, multi-tenancy | seeded profiles | schema, repository, service, rendered privacy | yes |
| Discovery tags | N/A | batch tag reads, search index text | `/network?q=...`, browse filters | `community_discovery_tags` | product discovery, privacy matrix | seeded tags | tenant collision, public/private leakage, search | yes |
| Public catalog card | N/A | `PublicCatalogCard` public-only model | `/`, `/network`, `/network?q=...` | profile/tag view fields | privacy matrix | public seed cards | signed-out/signed-in privacy | yes |
| Home slices | N/A | `NetworkHomeView` slice builder | `/` | service-owned ranking | product discovery | archetype seed slices | filtered slices, deterministic order | yes |
| Explore search/filter | N/A | `NetworkExploreView` search/filter | `/network?q=...` | profile/tag metadata | navigation/discovery docs | premise archetypes | positive/negative search | yes |
| Signed-in continuation | N/A | `NetworkReturnPath` or member lane | `/`, `/network` | no public-card fields | privacy matrix | multi-membership personas | no public card leakage | yes if changed |
| Blueprint import | N/A | future `BlueprintDiscovery` | future import/apply | future typed dataclass | Program Blueprint docs | future YAML examples | parser/hydration tests | yes if added |

## Required Proof

Minimum local gate for implementation PRs:

```bash
uv run ruff check .
uv run ruff format . --check
uv run pytest tests/test_tenant_repository.py tests/test_web_security.py tests/test_forum_slice.py tests/test_program_blueprints.py -q --tb=short
uv run ty check src/elbysodic/ tests/
uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"
```

Browser QA:

- `/`
- `/network`
- `/network?q=<public-archetype-or-tag>`
- signed-out public session
- signed-in multi-membership session
- empty/backstage-only network state
- desktop and mobile viewport notes or screenshots

## Not Now

- Do not make `/explore` canonical in this slice.
- Do not add a public social graph, writer recommendations, demographic
  personalization, or marketplace ranking.
- Do not expose private scene activity, staff activity, notifications, watches,
  read state, plotting-room activity, applications, private room labels, staff
  facets, or draft material as public discovery signals.
- Do not persist editorial collections until there is an explicit owner model
  and visibility contract.
- Do not add denormalized counters without performance evidence.
- Do not put discovery metadata in Program Blueprints until the future
  Blueprint extension is accepted and tested.
- Do not derive recommendations from Continuity Graph data before provenance,
  privacy, and canon-review gates exist.

## Open Questions

- Should discovery profiles be seed/admin-only for alpha, or should Director
  Studio get an editor in the same milestone?
- Should public roster count include only accepted faces, all public faces, or
  only active/posted faces?
- What is the first public activity signal: latest public post, active public
  thread count, open wanted count, newly opened status, or editorial weight?
- Which catalog fields are director-owned versus platform-owned?
- Does `request access` become a first-class public posture before the route is
  ready?
- When `/explore` is eventually approved, should it redirect to `/network` or
  become canonical with `/network` redirecting to it?
