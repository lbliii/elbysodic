# Network Catalog Metadata And Slices

Status: planned implementation slice after home/Explore visual prototype
Owner: Product, services, web, storage, tests, docs, and planning stewardship
Created: 2026-05-13
Last updated: 2026-05-13
Review by: 2026-05-27
Closure criteria: `/` and `/network` are backed by service-owned public catalog
read models, public slices/search use explicit public metadata instead of
template or slug heuristics, privacy tests prove no backstage/private/staff
leakage, docs and changelog are updated, and `/network` remains canonical while
the product label is `Explore`.

## Purpose

The visual direction for the shared-host home and Explore surfaces is now clear:

- `/` is a high-gloss visitor hook with featured realm media, trending shelves,
  genre/mood slices, and a small signed-in return path.
- `/network` is the Explore surface for search, tag relationships, wanted
  hooks, roster signals, current events, claims, reserves, and public catalog
  browsing.
- `/desk` and `/studio` own personal obligations, staff/director queues, active
  face work, and daily board-running tasks.

The current implementation still relies on `StudioNetworkDirectory`,
`StudioNetworkProgramView`, hard-coded slug/name search keywords, and
template-local slice labels. This plan makes the catalog contract real before
adding schema or heavier personalization.

## Steward Synthesis

Accepted:

- Build service-owned `NetworkHomeView` and `NetworkExploreView` before adding
  durable catalog schema.
- Split public catalog cards from signed-in continuation rows at the type
  level; public cards must not contain membership, role, active face, unread,
  plotting-room, application-review, staff, or private state.
- Keep `/network` canonical for this slice and label the surface `Explore`.
  Defer `/explore` alias or redirect until an explicit public-route migration is
  approved.
- Use existing public data first: public-preview realms, published premise/event
  summaries, open wanted hooks, public scene hubs, safe roster counts, hero
  media, community marks, and public launch/access posture.
- Add repository/service aggregate APIs before richer slices become N+1 loops.
- Add multi-community privacy tests for every new slice and search/filter path.
- Run browser QA after the service/read-model contract lands because the home
  and Explore surfaces are responsive, media-heavy pages.

Deferred:

- New catalog schema for genre/mood/pace/editorial collection labels.
- Persisted editorial collections.
- Denormalized activity or trending counters.
- Demographic personalization, cross-community writer recommendations,
  marketplace ranking, and Continuity Graph-derived recommendations.
- `/explore` public route migration.

Minority or caution reports:

- Storage sees migration-doc drift: `docs/architecture/migrations.md` still
  references schema version 14 while code is at 16. Update it before or
  alongside any future catalog migration.
- Web sees template-local macro growth. Promote shared realm-card/slice/search
  components only after the real read-model fields stabilize.
- Tests identified an immediate privacy risk: public catalog summaries must
  select only published premise/current-event materials, never draft material.

## User Panel Synthesis

Evidence mode: synthetic panel from `docs/product/user-personas-panel.md`.

- New face applicants need public catalog cards to show fit signals before
  commitment: premise, tone, current event, application posture, wanted hooks,
  claims/reserves posture, and invite/request access.
- Hook hunters need relationship and wanted-hook entry points that lead to
  playable scenes, not decorative genre tags.
- Directors need public discovery to represent realm atmosphere and openings
  without exposing staff workload or private setup gaps.
- Safety-boundary writers need public cards and Explore filters to avoid all
  membership, staff, private room, application, notification, and active-face
  side channels.
- Returning writers can use a small return path from `/`, but daily obligations
  belong in Desk and Studio, not on the visitor homepage.

## Contract Matrix

| Contract | API/CLI | Programmatic | Protocol/Routes | Schema/Types | Docs | Examples/Seeds | Tests | Changelog |
|---|---|---|---|---|---|---|---|---|
| Public catalog card | N/A | `PublicCatalogCard` service model | `/`, `/network`, `/network?q=...` | no new schema first | primitives, privacy matrix | seeded public realms | service + rendered privacy | yes |
| Home slices | N/A | `NetworkHomeView` rows | `/` home mode | typed read model | homepage plan | seeded slice fixtures | signed-out/signed-in rendered | yes |
| Explore search/filter | N/A | `NetworkExploreView` + filter service | `/network?q=...` | typed public metadata fields; schema deferred | navigation, primitives | genre/mood seed metadata | positive/negative search tests | yes |
| Safe activity/trending | N/A | derived public aggregate | `/` trending shelf | derived only first | privacy matrix | public/private activity fixtures | private activity exclusion | yes if surfaced |
| Invite/access posture | N/A | policy-filtered public field | card CTA/copy only | existing launch/access state first | invite docs if changed | seed postures | public/member/staff states | yes if behavior changes |
| Route naming | N/A | N/A | keep `/network`; label `Explore` | N/A | navigation docs if changed | smoke docs if changed | route tests | yes if route changes |

## Implementation Plan

### Phase 0: Privacy Bug And Baseline Proof

Goal: close the known public material-selection risk before new slices amplify
it.

Work:

- Ensure public catalog summaries use only published public premise/current
  event materials.
- Add a focused test with draft and published premise/event rows in the same
  public-preview realm.
- Add rendered negative assertions for draft title/body on `/` and
  `/network?q=...`.

Proof:

- `uv run pytest tests/test_forum_slice.py tests/test_web_security.py -q --tb=short -k "network or public_catalog or home"`
- App check.

Collateral:

- No collateral if behavior now matches existing security docs.

### Phase 1: Service-Owned Catalog Models

Goal: stop templates and route handlers from composing public discovery state.

Work:

- Add read models:
  - `PublicCatalogCard`
  - `NetworkHomeView`
  - `NetworkExploreView`
  - `NetworkSlice`
  - `NetworkBrowseFacet`
  - signed-in continuation rows, separated from public rows
- Add service methods:
  - `services.network_home()`
  - `services.network_explore(query: str = "")`
- Keep page handlers thin: resolve viewer, call service, render template.
- Keep signed-in continuation optional and viewer-scoped.

Proof:

- Service/read-model tests for signed-out and signed-in home and Explore.
- Rendered tests proving public rows do not include membership, role, active
  face, unread, plotting room, staff, or application-review fields.

Collateral:

- Update `plans/in-progress/studio-network-homepage-2026-05-03.md` status note.

### Phase 2: Public-Safe Repository Aggregates

Goal: avoid N+1 public catalog composition and centralize privacy predicates.

Work:

- Add a narrow repository aggregate such as `list_public_network_catalog_rows()`
  or equivalent repository helpers.
- Predicates must be explicit:
  - `launch_status = public-preview`
  - at least one public scene hub where required
  - published public premise/current event only
  - open wanted hooks only
  - public/accepted roster count only if intended
  - exclude private boards, private threads, staff rooms, notifications,
    watches, read state, plotting rooms, draft materials, applications, and
    inactive/backstage realms
- Keep activity/trending derived from public activity only; no persisted
  counters in this phase.

Proof:

- Multi-community tests with public, backstage, invite-only, private-heavy, and
  unrelated staffed realms.
- Tests where private activity outranks public activity in raw data but does
  not affect public trending output.

Collateral:

- Repository/service steward notes in the implementation PR.

### Phase 3: Prototype Catalog Metadata Without Schema

Goal: replace hard-coded slug/name search heuristics with explicit public
metadata while keeping the migration surface reversible.

Work:

- Define service-level catalog metadata for seeded realms:
  - genre
  - mood
  - pace
  - fandom/original
  - writing length
  - invite/request posture
  - application posture
  - claims/reserves posture
- Derive where possible from published materials and existing public facts.
- Keep labels tenant-aware in shape, even if generated in service code.
- Update search/filter to match public metadata and published summaries, not
  membership names, roles, active faces, staff labels, private rooms, or draft
  text.

Proof:

- Positive search tests for `magic school`, `wanted hooks`, `slow burn`,
  `superhero crisis`, and `survival sci-fi`.
- Negative search tests for staff names, member names, active face names,
  private room labels, and draft-only terms.
- Seed idempotency tests if seed metadata moves into seed helpers.

Collateral:

- Product docs for supported public catalog metadata if labels become visible
  product contract.

### Phase 4: Wire Home And Explore To Read Models

Goal: make the visual prototype consume the real service contract.

Work:

- Update `/` to render `NetworkHomeView`:
  - featured realm
  - trending realms
  - genre/mood shelves
  - wanted/casting shelf
  - small signed-in return path
- Update `/network` to render `NetworkExploreView`:
  - query state
  - browse facets
  - relationship lanes
  - catalog results
  - empty result state
- Promote shared card/tile/slice/search components from page-local macros only
  after field names stabilize.

Proof:

- Rendered tests for `/`, `/network`, `/network?q=wanted`, signed-out, signed-in
  multi-membership, and empty/backstage network.
- Browser QA at desktop and mobile viewports.

Collateral:

- `docs/architecture/rendered-route-privacy-matrix.md`
- `docs/architecture/primitives.md`
- `docs/product/navigation-menus.md` only if labels/active state change
- changelog fragment

### Phase 5: Decide Persistence

Goal: add schema only after labels, owner model, and public visibility rules are
stable.

Decision criteria:

- Directors need to edit catalog labels in Studio, or
- Seed/service constants are too brittle for alpha QA, or
- Query/filter behavior needs durable labels across deploys.

If accepted, model catalog labels as tenant-aware rows, not overloaded global
facets. Candidate shape:

```text
community_catalog_labels(
  community_id,
  label_type,
  slug,
  name,
  sort_order,
  visibility,
  created_at,
  updated_at
)
```

Migration requirements:

- Fresh schema and upgraded schema parity.
- `community_id` explicit in every row and index.
- Multi-community duplicate slug tests.
- Seed idempotency.
- Update `docs/architecture/migrations.md` version drift before adding the
  migration.

## Required Proof

Minimum local gate for implementation PRs:

```bash
uv run ruff check .
uv run ruff format . --check
uv run pytest tests/test_forum_slice.py tests/test_web_security.py tests/test_tenant_repository.py -q --tb=short
uv run ty check src/elbysodic/ tests/
uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"
```

Browser QA:

- `/`
- `/network`
- `/network?q=wanted`
- signed-out public session
- signed-in multi-membership session
- empty/backstage-only network state
- desktop and mobile viewport notes or screenshots

## Not Now

- Do not make `/explore` canonical in this slice.
- Do not add a public social graph, writer recommendations, demographic
  personalization, or marketplace ranking.
- Do not expose private scene activity, staff activity, notifications, watches,
  read state, plotting-room activity, applications, or private room labels as
  public discovery signals.
- Do not persist editorial collections until there is an explicit
  platform-editor owner model and visibility contract.
- Do not add denormalized counters without performance evidence.
- Do not derive recommendations from Continuity Graph data before provenance,
  privacy, and canon-review gates exist.

## Open Questions

- Should `public roster count` include only accepted faces, all public faces, or
  only active/posted faces?
- What is the first public activity signal: latest public post, active public
  thread count, open wanted count, newly opened status, or editorial weight?
- Which catalog labels are director-owned versus platform-owned?
- Does `request access` become a first-class public posture before the route is
  ready?
- When `/explore` is eventually approved, should it redirect to `/network` or
  become canonical with `/network` redirecting to it?

