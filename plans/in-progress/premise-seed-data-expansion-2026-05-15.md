# Premise Seed Data Expansion

Status: active implementation plan; discovery profile foundation and nine
original premise communities landed
Owner: Product research, storage/seed, Blueprint, service, web, tests, and docs stewardship
Created: 2026-05-15
Last updated: 2026-05-15
Review by: 2026-06-05

## Strategy Anchor

This plan strengthens Realm Studio and Writer Network first. The seed data
should prove that Elbysodic can open, present, browse, join, and operate
premise-based PBP communities without collapsing them into generic forums,
single-fandom skins, or wanted-ad directories.

Continuity Graph implications are deferred to proof surfaces only: seeded
threads, events, materials, rumors, prompts, claims, and plot hooks should make
future source-linked memory obvious, but this plan does not add automatic canon
extraction.

## Research Inputs

- `research/synthesis/2026-05-15-current-pbp-premise-archetypes.md`
- `research/synthesis/2026-05-15-pbp-premise-census-followup.md`
- `research/synthesis/2026-05-15-premise-archetype-reference-skeletons.md`
- `plans/in-progress/network-catalog-metadata-slices-2026-05-13.md`
- `docs/product/community-shapes.md`

Evidence mode:

- Source signal: current public Jcink/PBP ads, directories, and ad mirrors.
- Research inference: premise engines matter more than broad genre labels.
- Product promotion: build seed communities around premise archetypes, then
  use genre, access, pace, age/rating, and connection scaffolds as metadata.

## Decision

Accepted:

- Seed one curated, original, premise-based community for each researched
  archetype.
- Use cinematic and television history as reinforcing story skeletons, not IP
  sources.
- Treat TV Tropes-style patterns as a later plotting and wanted-hook vocabulary
  layer, not as market validation.
- Exclude sanctuary sandboxes and wanted-hook-first communities from the seed
  slate.
- Let the seed exercise reveal missing product primitives, schema fields,
  repository APIs, read models, and public discovery metadata. The point is not
  to avoid database work; it is to make any new database work deliberate,
  tenant-scoped, migratable, and proven.

Rejected:

- Multi-genre sanctuary sandbox as an initial curated community archetype.
- Wanted-hook-first communities as homepage or Explore archetypes.
- Literal copyrighted fandom communities as the new public seed baseline.

Deferred:

- Blueprint contract expansion for threads, plot hooks, claims, applications,
  and richer event objects.
- Generated visual assets for all nine communities.

Not-now:

- AI-first canon automation.
- Marketplace ranking.
- Private Discord import.
- Multi-community production provisioning.

## Current Seed Contract Inventory

The current seed layer is concentrated in `src/elbysodic/db/seed.py`.

Existing Blueprint-backed seed capabilities:

- community creation and public-preview launch status
- director/member role and membership creation
- starter faces
- playable boards
- materials
- wanted hooks
- safe theme tokens
- appearance settings
- board and community media defaults
- realm interactions
- claim types and application template fields

Existing seed-only helper capabilities:

- additional users and memberships
- richer character identities
- character claims
- facets and facet assignments
- wanted-ad facets
- character plot hooks
- threads and posts
- watches, read state, notifications, applications, and route-facing QA data

Current model pressure revealed by this research:

- Public Explore search currently relies on service-owned but hard-coded
  keyword buckets such as superhero, magic, survival, town, urban, wanted,
  event, plotting, claims, and reserves.
- The `communities` table has launch status, media, theme, and appearance
  fields, but no first-class public discovery profile for premise archetype,
  play engine, lore aperture, access posture, pace, rating, adjunct Discord
  posture, current event label, or onboarding shape.
- Published `premise` materials can carry rich prose, but they are not enough
  for reliable faceted browsing, homepage lanes, Explore filters, or seed
  census proof.

Current public seed posture to replace or supersede:

- `X-Men Apocalypse` is the default demo community and is strongly literal-IP
  coded.
- `HP Universe` and `Jurassic Park Universe` are multi-community director QA
  seeds but also literal-IP coded.
- `RL NYC` and `RL Small Town` are closer to original premise seeds, but they
  are too small to carry the new Explore/homepage archetype system.
- `docs/architecture/seed-personas.md` is currently aligned to those persona
  keys and must move with any seed replacement.

Implementation implication:

- The first implementation should prefer data-definition expansion plus
  tenant-scoped seed helpers over a schema change.
- Blueprint import is a director-facing contract. Do not expand
  `ProgramBlueprint` until the team explicitly accepts that public-contract
  change.
- Keep `community_id` explicit in every repository call, test assertion, and
  generated fixture.

## Likely Model Extensions To Evaluate

The seed expansion should actively test whether these belong as durable
database primitives. This is not pre-approval for a specific migration; it is
the implementation brief for the migration design pass.

### Community Discovery Profile

Likely shape:

- one row per community, keyed by `community_id`
- public only when the community is otherwise public-ready
- service-owned reads for homepage and Explore cards

Candidate fields:

- `community_id`
- `premise_archetype`
- `secondary_archetypes`
- `genre_tags`
- `play_engine`
- `lore_aperture`
- `access_model`
- `age_rating`
- `content_rating`
- `pace_label`
- `activity_expectation`
- `forum_adjunct`
- `application_model`
- `current_event_label`
- `current_event_summary`
- `open_hook_count_label`
- `catalog_pitch`
- `staff_pick_label`

Rationale:

- These are platform discovery facts, not director-defined in-world facets.
- They should be stable enough for search, browse chips, homepage lanes, and
  public cards.
- Keeping them out of free-form materials prevents public Explore from parsing
  prose or relying on seed slugs.

Accepted design direction:

- Use a new `community_discovery_profiles` table for public catalog metadata
  and `community_discovery_tags` for repeatable public discovery signals.
- Keep these separate from `communities` because they are optional public
  discovery/editorial metadata, not core tenant identity or media fields.

### Archetype Registry

Likely shape:

- static domain constants first
- database table only if directors will manage or localize archetypes later

Candidate values:

- `small-town-social-web`
- `weird-town-mystery`
- `urban-supernatural-pressure-cooker`
- `court-and-faction-fantasy`
- `original-canon-adjacent-au`
- `fame-and-industry-drama`
- `survival-trials`
- `occult-historical-pressure`
- `strange-frontier`

Rationale:

- The homepage and Explore pages need consistent language.
- Seed tests need a stable census target.
- Director-defined facets should remain community-local; archetypes are
  platform discovery categories.

### Public Current Event Or Discovery Highlight

Likely shape:

- continue using published `event` materials for long-form content
- add one public catalog field or relationship for the headline highlight

Rationale:

- Current events are one of the strongest browse signals.
- Explore cards need a short, reliable label without scraping material bodies.

### Reference Skeleton Metadata

Preferred shape:

- keep this in research and seed authoring notes, not public DB fields

Rationale:

- Reference skeletons are craft scaffolding. Publicly exposing them risks IP
  confusion and makes original communities feel derivative.
- If needed for internal tooling, keep them in seed definitions or docs, not
  rendered public catalog output.

## Target Seed Slate

Each community below is original. Reference skeletons are craft inputs only:
they shape story mechanics, not names, plots, characters, or settings.

### 1. Coastal Status Town

Archetype: small-town social web
Working slug: `harbor-society`
Reference skeletons: Palm Royale, Gilmore Girls, Friday Night Lights
Anti-reference: pure cozy town with no consequences

Premise engine:

A newcomer, returnee, or fallen local tries to find footing in a coastal town
where a club, civic calendar, school institution, and old families make every
favor public and every secret useful.

Seed surfaces:

- Boards: club, main street diner, marina hotel, town hall, school or stadium,
  local paper, staff office.
- Materials: premise, social ladder, town calendar, application guide, current
  event.
- Canon roster: outsider social climber, old-money gatekeeper, fallen heiress,
  club manager, local reporter, golden-child coach, town fixer, returnee,
  deputy mayor.
- Opening event: Founders Gala membership vote plus a charity-accounting
  scandal.
- Wanted hooks: sibling returnee, rival committee chair, secret donor, reporter
  source, ex-spouse with town leverage.

### 2. Open-Lore Weird Town

Archetype: weird-town mystery
Working slug: `signal-creek`
Reference skeletons: Twin Peaks, Stranger Things, Gravity Falls
Anti-reference: solved puzzle box where staff has already answered everything

Premise engine:

A beautiful mountain town keeps recording impossible signals after a long-ago
disappearance. Locals, researchers, skeptics, teens, believers, and officials
all hold partial truths.

Seed surfaces:

- Boards: observatory, diner, woods and lake, sheriff station, archive, clinic,
  abandoned relay site.
- Materials: premise, public rumors, open-lore species or phenomena, encounter
  rules, current chapter.
- Canon roster: observatory researcher, skeptical sheriff, local historian,
  teen witness, occult shopkeeper, returning sibling, town doctor, hidden
  insider.
- Opening event: midnight signal during a meteor shower and one missing hiker.
- Wanted hooks: field technician, cult survivor, government observer, local
  rival, person who remembers the vanished year differently.

### 3. Supernatural City

Archetype: urban supernatural pressure cooker
Working slug: `nocturne-row`
Reference skeletons: True Blood, The Vampire Diaries, Shadowhunters
Anti-reference: species encyclopedia with no playable conflict

Premise engine:

Supernatural groups are partly visible in a city where law, nightlife, media,
hunters, medicine, and old covenants are all failing at once.

Seed surfaces:

- Boards: nightlife district, supernatural council, hunter safehouse, hospital
  or blood bank, press room, old quarter, court house.
- Materials: premise, species limits, city law, factions, current treaty crisis.
- Canon roster: vampire negotiator, witch barrister, werewolf organizer,
  hunter defector, human journalist, coroner, nightclub owner, council heir.
- Opening event: treaty breach after a public attack and a missing elder.
- Wanted hooks: hostile witness, coven rival, hunter handler, forbidden romance,
  legal advocate, blood-bank whistleblower.

### 4. Court-And-Faction Fantasy

Archetype: original court-and-faction fantasy
Working slug: `crownfall`
Reference skeletons: Game of Thrones, House of the Dragon, Shadow and Bone
Anti-reference: lore atlas with no immediate succession pressure

Premise engine:

A realm loses its monarch while magic, border war, priesthood, merchant houses,
and noble claimants all contest who gets to define legitimacy.

Seed surfaces:

- Boards: palace court, rebel border, mage archive, market docks, temple,
  war room, noble quarter.
- Materials: premise, houses and factions, magic limits, succession crisis,
  application guide.
- Canon roster: disputed heir, spymaster, rebel envoy, mage scholar, border
  commander, merchant diplomat, priest, hostage noble, royal bastard.
- Opening event: coronation interrupted by a magical omen and border raid.
- Wanted hooks: secret claimant, oath-bound guard, foreign ambassador, court
  physician, black-market mage, lost sibling.

### 5. Original Canon-Adjacent AU

Archetype: original canon-adjacent AU
Working slug: `afterlight-accord`
Reference skeletons: Once Upon a Time, Riverdale, Battlestar Galactica
Anti-reference: renamed fandom with protected names filed off

Premise engine:

Legendary roles survived a catastrophe, but the old story broke. Heirs,
exiles, monsters, archivists, rebels, and reformers inherit archetypal duties
inside an original branch-point world.

Seed surfaces:

- Boards: treaty town, old academy, archive, rebel safehouse, transit gate,
  ruined district, council chamber.
- Materials: premise, branch point, role archetypes, factions, current accord.
- Canon roster: heir of the vanished order, exile captain, reluctant prophet,
  archivist, converted monster, reformer, traitor, border runner.
- Opening event: the Accord seal fails during a public remembrance.
- Wanted hooks: missing mentor, oath sibling, reformed antagonist, archive
  thief, forbidden envoy, person who knows the old ending.

### 6. Spotlight City

Archetype: fame and industry drama
Working slug: `brightline`
Reference skeletons: Palm Royale, Mad Men, The Marvelous Mrs. Maisel
Anti-reference: celebrity claim list with no industry pressure

Premise engine:

Public image is currency in a city where studios, clubs, magazines, patrons,
lawyers, stylists, and gossip writers turn ambition into leverage.

Seed surfaces:

- Boards: studio lot, live club, magazine newsroom, charity circuit, hotel,
  courthouse, backstage hall.
- Materials: premise, career ladder, image rules, scandal board, current awards
  season.
- Canon roster: rising star, PR fixer, old-money patron, gossip columnist,
  producer, venue owner, fallen idol, contract lawyer, assistant with receipts.
- Opening event: awards-night sabotage and a leaked contract.
- Wanted hooks: rival performer, crisis photographer, patron with conditions,
  ex-manager, secret spouse, columnist source.

### 7. Trial Clans Or Academy

Archetype: survival, trials, and institution pressure
Working slug: `emberhouse`
Reference skeletons: The 100, Yellowjackets, The Hunger Games
Anti-reference: PvP arena that normalizes consent failures

Premise engine:

An academy or clan system forces candidates into visible trials while scarcity,
rank, loyalty, and adult agendas decide who gets protected and who becomes
useful.

Seed surfaces:

- Boards: academy hall, training grounds, council chamber, infirmary, forbidden
  zone, supply depot, dormitory.
- Materials: premise, house or clan guide, trial rules, safety and consent
  guide, current selection.
- Canon roster: reluctant champion, ambitious rival, instructor, medic, house
  heir, outsider scholarship student, quartermaster, rule-breaker, council
  observer.
- Opening event: trial selection tampered with before the first challenge.
- Wanted hooks: secret sponsor, sibling competitor, rule enforcer, injured
  favorite, black-market supplier, witness to sabotage.

### 8. Occult Historical City

Archetype: occult historical pressure
Working slug: `gaslight-ward`
Reference skeletons: Peaky Blinders, Bridgerton, Carnival Row
Anti-reference: costume drama with no institutional stakes

Premise engine:

Class, crime, reform, etiquette, police power, newspapers, and occult societies
collide in a period city where public respectability hides old bargains.

Seed surfaces:

- Boards: newspaper office, police court, season rooms, docks and factory,
  occult society, theater, hospital.
- Materials: premise, city institutions, etiquette and class, occult rules,
  murder inquiry.
- Canon roster: investigator, socialite, crime-family heir, reformer, medium,
  union organizer, stage performer, surgeon, newspaper editor.
- Opening event: a society-season debut is interrupted by an impossible murder.
- Wanted hooks: masked patron, police informant, rival medium, factory witness,
  disgraced fiance, occult debtor.

### 9. Strange Frontier

Archetype: sci-fi or weird frontier
Working slug: `wayfarer-station`
Reference skeletons: Firefly, The Expanse, Silo, Westworld
Anti-reference: empty sandbox map with no scarcity or authority pressure

Premise engine:

An isolated station, ship, or settlement survives at the edge of known space
where law is fragile, memory is contested, supplies are limited, and one signal
could change every bargain.

Seed surfaces:

- Boards: docking ring, med bay, market deck, admin control, frontier wilds,
  archive level, repair bay.
- Materials: premise, station law, factions, scarcity ledger, current signal.
- Canon roster: marshal, smuggler, engineer, medic, corporate envoy, archivist,
  scientist, performer, quartermaster, station-born guide.
- Opening event: missing convoy and an encrypted signal from outside the chart.
- Wanted hooks: debt-holder, corporate auditor, missing pilot, forbidden-level
  witness, alien-signal translator, old war comrade.

## Scale Targets

Minimum target for the first complete seed pass:

| Surface | Per community target | Nine-community target |
| --- | ---: | ---: |
| Communities | 1 | 9 |
| Public boards | 6-8 | 54-72 |
| Private/staff boards | 1 | 9 |
| Materials | 5-7 | 45-63 |
| Accepted characters | 8-12 | 72-108 |
| Wanted hooks | 5-8 | 45-72 |
| Character plot hooks | 4-6 | 36-54 |
| Current threads | 4-8 | 36-72 |
| Posts | 2-4 per current thread | 72-288 |
| Claim types or facet groups | 3-5 | 27-45 |
| Applications in flight | 0-2 selected communities | 4-8 total |
| QA personas | stable matrix, not one per face | 12-18 total |

This is roughly a 10x expansion in public premise coverage, not a requirement
to make every community equally large in the first PR.

## Implementation Sequence

### Phase 0: Approval And Contract Lock

Status: next

- Confirm the nine-community slate and working slugs.
- Decide whether literal-IP coded seeds are removed immediately, preserved
  behind legacy compatibility, or phased out after tests and docs move.
- Confirm that Phase 1 may change seed data, seed personas, route-facing QA
  fixtures, public demo content, and database-backed discovery metadata.
- Decide whether the first implementation PR should include a discovery-profile
  migration or first prove the seed shape with existing tables.

Stop-and-ask gate:

- Seed data, persona matrix, and public demo content changes require explicit
  user approval before implementation.
- Schema, migration, repository API, and public read-model changes require the
  normal storage, service, docs, and test collateral.

### Phase 1: Discovery Model Design

Status: foundation landed in
`plans/in-progress/network-catalog-metadata-slices-2026-05-13.md`; Director
Studio editing remains planned.

- Audit the current public catalog and Explore service behavior.
- Implement the accepted `community_discovery_profiles` and
  `community_discovery_tags` direction from the network catalog metadata plan.
- Define allowed values for archetype, play engine, lore aperture, access,
  pace, rating, adjunct posture, and application model.
- Add a migration plan because existing materials/facets are not sufficient for
  stable public homepage slices, Explore filters, seed census proof, and
  director-owned public positioning.
- Keep reference skeletons out of rendered public metadata.

Proof:

- Fresh schema and migrated schema produce the same shape if a migration is
  added.
- Repository APIs expose public discovery metadata without page-level SQL.
- Public catalog tests prove backstage/private realms and staff data do not
  leak through new metadata.

Accepted direction after 2026-05-15 steward synthesis:

- Use `community_discovery_profiles` and `community_discovery_tags`, both
  tenant-scoped by `community_id`.
- Keep discovery profile/tag fields out of `ProgramBlueprint` until a future
  typed Blueprint extension is accepted.
- Route homepage and Explore through service-owned public read models before
  rendering new metadata.

Implementation note:

- The discovery profile/tag storage, seed helper, current five-realm profile
  seed, public read-model wiring, and rendered public search proof have landed.
  The nine original premise communities are also seeded: `harbor-society`,
  `signal-creek`, `nocturne-row`, `crownfall`, `afterlight-accord`, and
  `brightline`, `emberhouse`, `gaslight-ward`, and `wayfarer-station`.

### Phase 2: Seed Definition Shape

Status: landed for the current five compatibility realms and all nine original
premise realms.

- Introduce a premise seed definition structure inside the seed module or a
  seed-adjacent module.
- Reuse existing `ProgramBlueprint` fields for community, starter faces,
  boards, materials, wanted, theme, and appearance where possible.
- Keep richer seed-only data separate for facets, claims, plot hooks, threads,
  posts, and applications unless the Blueprint contract is explicitly expanded.
- Add seed census helpers for tests so coverage does not depend on brittle
  string hunts.
- Include discovery-profile fields in seed definitions if Phase 1 adds that
  primitive.

Proof:

- Unit test that all premise seed definitions validate.
- Unit test that all seed slugs are unique.
- Unit test that no target community is sanctuary sandbox or wanted-first.
- Unit test that each public seed community has complete discovery metadata
  when the discovery profile primitive exists.

### Phase 3: Community Packets

Status: landed for all nine original premise realms.

- Add the nine original community packets with materials, boards, starter
  characters, wanted hooks, and visual/theme placeholders.
- Keep public homepage and Explore readiness in mind: each community needs a
  crisp premise, archetype, access/rating/pace posture, and current event.
- Avoid literal references to source skeleton IP in public seed content.

Proof:

- Seeded database contains all nine public-preview communities.
- Each has minimum counts for boards, materials, characters, and wanted hooks.
- Public catalog can render the slate without private or staff-only leakage.

### Phase 4: Connections, Claims, And Plotting

Status: planned for richer connections, claims, and plotting beyond the seed
minimums.

- Add facet groups or claim types that make each archetype browseable and
  staff-operable.
- Add character claims and reserves where they demonstrate face, faction,
  species, rank, career, house, or role mechanics.
- Add character plot hooks to show wanted-hook support without making the
  community wanted-first.

Proof:

- Tenant repository tests assert claim and facet rows remain community-scoped.
- Wanted and plotter pages render related faces, materials, and facets for at
  least three archetype variants.

### Phase 5: Scenes And Activity

Status: partially landed for profile-backed public cards and search; planned for
expanded original seed coverage and richer first-entry states.

- Seed current threads and posts that prove each premise can generate immediate
  scenes.
- Include needs-reply, waiting, caught-up, watching, and staff/private examples
  through existing writer-facing surfaces.
- Keep scene content concise and original.

Proof:

- Writer desk and thread reader route tests cover at least one new social,
  mystery, supernatural, fantasy, and frontier thread.
- Rendered pages prove active face, reply state, and tenant-local links survive
  the larger seed catalog.

### Phase 6: Persona Matrix And Docs

Status: planned

- Update `SEED_PERSONAS` and `docs/architecture/seed-personas.md`.
- Preserve same-global-user, different-community role proof.
- Preserve inactive membership proof.
- Add QA personas that exercise director, staff, ordinary writer, applicant,
  outsider, and cross-community membership behavior across original premises.

Proof:

- Existing dev persona tests pass after updated keys.
- Seed persona docs match code exactly.
- Route smoke tests use purpose-based persona keys, not obsolete IP names.

### Phase 7: Public Home And Explore Readiness

Status: planned

- Update homepage and Explore seed assumptions after the seed catalog exists.
- Make archetype labels, current event, pace, access, wanted count, and recent
  activity available through service-owned read models and explicit discovery
  metadata where accepted.
- Use the premise taxonomy for discovery, not broad genre alone.
- Remove hard-coded legacy browse buckets once the discovery profile can power
  homepage slices and Explore filters.

Proof:

- Public home and `/network` or Explore routes render all public-preview seed
  communities without staff/private content.
- Browser QA records desktop and mobile screenshots for the expanded slate.

## Compatibility Strategy

Preferred path:

- Add original premise communities first.
- Keep existing literal-IP coded seeds only as temporary compatibility fixtures
  until tests, docs, and QA personas move.
- Move public demo emphasis to original premise communities immediately after
  route and docs proof pass.
- Remove or archive literal-IP coded seed names in a follow-up once no test,
  persona, or doc contract depends on them.

Reason:

- Immediate removal would touch many tests and docs at the same time as the
  seed expansion.
- Keeping them forever would undermine the premise-based public product
  posture.

## Testing And Proof Plan

Light planning proof for this artifact:

- `git diff --check`

Implementation gates after seed changes:

- `uv run ruff check .`
- `uv run ruff format . --check`
- `uv run pytest -q --tb=short`
- `uv run ty check src/elbysodic/ tests/`
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`

Focused tests to add or update:

- seed census test for nine premise communities and minimum surface counts
- seed persona matrix test for original communities and cross-community roles
- migration/schema parity tests if discovery-profile storage is added
- repository tests for creating, updating, and reading community discovery
  profiles through `community_id`
- tenant repository coverage for claims, facets, wanted hooks, plot hooks,
  threads, and applications
- rendered public catalog tests proving no staff/private leakage
- route smoke tests for representative community home, board, thread, wanted,
  material, application, and character surfaces

## Steward Notes

Storage and migration:

- Schema change is allowed if the seed exercise proves public discovery needs a
  first-class primitive.
- The preferred hypothesis is a `community_discovery_profiles` table keyed by
  `community_id`, not slug-derived heuristics or prose parsing.
- Seed helpers must remain idempotent.
- Every insert and lookup must stay tenant-scoped through `community_id`.
- Any migration or schema addition must update fresh schema, migration path,
  repositories, read models, docs, and tests together.

Blueprint:

- Reuse Blueprint-compatible structures for packet content.
- Do not expand the director-authored Blueprint contract until the import,
  validation, docs, and tests move together.
- If richer seed-only structures prove stable, promote them to Blueprint later
  through a dedicated contract plan.

Surface contract:

- Public home and Explore should consume service-owned read models.
- Templates must not infer archetype from slug or private seed details.
- Templates should not carry hard-coded archetype lanes once discovery metadata
  exists.
- Staff/private boards, applications, claims, and production materials need
  rendered privacy proof before they are used in public discovery.

Research:

- The nine archetypes are a medium-high confidence synthesis from current
  public ad signal.
- Reference skeletons are product craft guidance, not evidence that writers
  explicitly requested those shows.
- TV Tropes should be revisited when building hook templates, plot prompts,
  and wanted-ad authoring support.

## Open Questions

- Should the first code PR add all nine communities with minimum content, or
  land three communities first as a pattern proof?
- Should the default demo community become `harbor-society`,
  `signal-creek`, or a neutral original flagship built from the same taxonomy?
- Should Director Studio editing for `community_discovery_profiles` land during
  the nine-community seed pass, or stay seed/admin-only until after the public
  catalog contract settles?
- Which existing literal-IP seed persona keys should be preserved as aliases
  during transition, if any?
- How much visual media is required before the expanded seed slate feels like a
  real curated network rather than a text fixture?

## Closure Criteria

Close or archive this plan when one of these is true:

- The nine premise-based demo communities are implemented through PR-sized seed
  slices with tenant-scoped proof, updated persona/docs/test coverage, and
  public Explore readiness.
- The nine-community slate is explicitly superseded by a narrower seed slate
  plan with accepted rationale.
- Seed work is deferred and the research remains only as product input, with a
  final note linking the replacement plan.
