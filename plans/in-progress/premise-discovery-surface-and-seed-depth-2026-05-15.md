# Premise Discovery Surface And Seed Depth

Status: implemented in PR-sized slices; pending review and follow-up planning
Owner: Product research, Writer Network, Realm Studio, storage, service, web,
tests, docs, and planning stewardship
Created: 2026-05-15
Last updated: 2026-05-15
Review by: 2026-06-12
Closure criteria: public discovery surfaces, Director Studio discovery-profile
editing, original-premise seed depth, demo posture, persona/browser QA, and
related model extensions are either implemented in PR-sized slices with proof
or split into narrower accepted plans.

## Purpose

The first premise seed plan proved the foundation:

- tenant-scoped discovery profile and discovery tag storage
- service-owned public catalog read models
- public home and Network Explore wiring
- nine original premise-based seed communities
- research and product doctrine for premise-first community shapes

This plan owns the next phase: turn the premise system from seeded proof into a
usable product surface for visitors, writers, directors, and staff.

It strengthens:

- Writer Network: public visitors and returning writers can browse by story
  engine, entry path, current activity, and fit.
- Realm Studio: directors can intentionally author the public discovery posture
  for a realm without editing seed code.
- Continuity Graph foundation: current chapter, roster, scene, wanted, claim,
  and material connections become clear enough to later support source-linked
  memory without automatic canon extraction.

## Source Artifacts

- `docs/product/community-shapes.md`
- `plans/in-progress/premise-seed-data-expansion-2026-05-15.md`
- `plans/in-progress/network-catalog-metadata-slices-2026-05-13.md`
- `research/synthesis/2026-05-15-current-pbp-premise-archetypes.md`
- `research/synthesis/2026-05-15-pbp-premise-census-followup.md`
- `research/synthesis/2026-05-15-premise-archetype-reference-skeletons.md`
- `src/elbysodic/db/seed.py`
- `src/elbysodic/services/network.py`
- `src/elbysodic/web/pages/network/`
- `tests/test_forum_slice.py`
- `tests/test_tenant_repository.py`
- `tests/test_web_security.py`
- `tests/test_program_blueprints.py`

Evidence mode:

- Source signal: public PBP/Jcink ad and directory patterns from the 2026-05-15
  research pass.
- Research inference: writers compare premise engine, entry readiness, roster
  fit, pace, tone, and current story pressure more reliably than broad genre.
- Product doctrine: public discovery starts with premise archetype, while
  wanted hooks, claims, reserves, canons, plotters, applications, and scenes are
  entry paths inside a premise.

## Product Decisions

Accepted:

- Keep premise archetype as the primary public discovery lens.
- Keep discovery profiles and tags explicit, tenant-scoped public catalog data.
- Keep the existing discovery profile/tag schema for this phase; no additional
  migration is needed until the expanded seed catalog and real UAT expose a
  stable missing fact.
- Keep public cards separate from member continuation, active-face obligations,
  staff state, private rooms, draft material, and backstage plotting data.
- Keep reference skeletons internal to research and seed craft; do not render
  film or television comparisons as public catalog labels.
- Shift public demo emphasis toward original premise communities once route,
  docs, persona, and browser proof are ready.

Deferred:

- Program Blueprint import/export for discovery profiles.
- Marketplace ranking, personalization, social graph recommendations, and
  Continuity Graph-derived recommendations.
- Automatic canon extraction or AI-generated premise classification.

Not-now:

- Sanctuary sandbox communities as homepage archetypes.
- Wanted-hook-first communities as public discovery categories.
- Literal-IP seed communities as the public demo center of gravity.

## Implementation Slices

### Slice 1: Public Discovery Lanes And Filters

Goal: make home and Explore visibly premise-native without relying on slug,
name, or template heuristics.

Work:

- Add service-owned lane definitions for archetype, current chapter, entry
  path, pace, roster posture, and activity readiness.
- Extend `NetworkHomeView` and `NetworkExploreView` only where the template
  needs named public-safe data.
- Add Browse or Explore filters for premise archetype, play engine, lore
  aperture, access model, application model, pace, roster posture, and content
  posture.
- Keep wanted hooks visible as entry paths, not as the top-level category
  system.

Proof:

- Rendered tests for signed-out home and `/network` prove all public-preview
  original premise communities can appear without private leakage.
- Search/filter tests assert archetype and profile fields match explicit
  discovery data.
- Privacy tests assert no active face, Desk, staff, private board, notification,
  application-review, or backstage plotting state appears in public catalog
  cards.

### Slice 2: Director Studio Discovery Editing

Goal: let directors and staff author a realm's public discovery posture through
Realm Studio instead of seed code.

Work:

- Add Studio route and service methods for viewing and updating discovery
  profiles and discovery tags.
- Use allowlisted values for archetype, play engine, lore aperture, access
  model, application model, pace, rating, forum adjunct, and roster posture.
- Validate catalog pitch and onboarding pitch lengths.
- Preview the public card using the same read model as Network surfaces.
- Audit role checks so only authorized community staff can edit discovery
  metadata.

Proof:

- Service and route tests for director/staff edit success.
- Rendered and security tests for ordinary member, applicant, signed-out, and
  cross-community denial.
- Repository tests for update idempotence and `community_id` scoping.
- Docs update for the discovery-profile contract.

### Slice 3: Original Seed Depth Pass

Goal: make each original premise community feel active enough to test writer
and director workflows, not just public cards.

Work:

- Add richer threads, posts, watches, read state, and reply obligations for the
  nine original communities.
- Add character claims and reserves that prove faction, species, rank, career,
  house, role, and location mechanics across archetypes.
- Add selected applications in flight for representative communities.
- Add character plot hooks and material links where they demonstrate first
  entry without making the realm wanted-first.
- Keep seeded content concise, original, and public/private scoped.

Proof:

- Seed contract tests assert minimum scenes/posts/claims/reserves for each
  original premise community.
- Writer Desk and thread reader tests cover at least one social, mystery,
  supernatural, fantasy, industry, institution, historical, and frontier scene.
- Tenant tests assert claims, reserves, applications, watches, and read state do
  not cross communities.

### Slice 4: Demo Posture And Persona Matrix

Goal: move public QA and demo language from literal-IP compatibility seeds to
original premise communities.

Work:

- Update `docs/architecture/seed-personas.md` around purpose-based personas:
  public visitor, applicant, hook hunter, ordinary writer, active-face writer,
  director, staff moderator, inactive member, and cross-community returner.
- Preserve same-global-user, different-community role proof.
- Decide whether `harbor-society`, `signal-creek`, or a neutral original realm
  becomes the default public demo target.
- Keep legacy literal-IP seeds only where tests still need compatibility
  fixtures, and label that posture clearly in docs.

Proof:

- Persona docs match seed code exactly.
- Route smoke tests use purpose-based persona keys rather than obsolete
  IP-specific assumptions.
- Public demo entry route tests still pass when the original-premise slate is
  emphasized.

### Slice 5: Browser And Simulated Persona QA

Goal: prove the discovery experience reads clearly across archetypes and
devices before turning it into doctrine-heavy UI.

Work:

- Run browser QA for desktop and mobile public home, Network Explore, and at
  least three representative realm gateways.
- Run a synthetic user-panel review using `docs/product/user-personas-panel.md`
  after the rendered surfaces exist.
- Record findings as simulated signal, not real UXR.
- Promote only accepted findings into docs, tests, or follow-up plans.

Proof:

- QA notes include viewport, route, persona/task, screenshots or observations,
  accepted fixes, deferred findings, and residual risk.
- Public discovery tests cover any accepted clarity or privacy issues found by
  the QA pass.

### Slice 6: Model Extension Review

Goal: decide which discovery-adjacent fields deserve durable schema support
after the seed and surface work applies real pressure.

Candidates:

- featured current event material pointer
- roster posture and open role summary
- onboarding pitch and first-face route
- canon posture
- activity expectation and reply-labor signal
- application posture and review cadence
- public scene/activity count labels

Decision rule:

- Add schema only when the field is stable, public-safe, reusable across
  surfaces, and not already represented by a stronger Elbysodic object.
- Keep transient editorial copy in materials or service read models when it is
  not a durable catalog fact.
- Keep director-defined in-world facets separate from platform discovery tags.

Proof:

- Accepted schema changes move with migration, repository, service, rendered
  tests, docs, and changelog.
- Rejected/deferred fields get a short rationale in this plan or a follow-up
  plan.

## Dependencies

- The discovery profile/tag tables and repository methods must remain stable.
- Public catalog cards must continue to use service-owned read models.
- Director Studio edit work depends on an accepted form contract and role
  checks.
- Seed depth work depends on stable seed helper ownership and idempotence.
- Browser QA depends on a local runnable app and representative seeded data.

## Slice Outcomes

Completed in this branch:

- Slice 1 added public discovery filters and service-owned counts for Network
  discovery profile groups.
- Slice 2 added the director-only Studio discovery profile editor for profile
  fields and public discovery tags.
- Slice 3 deepened each original premise seed with starter scenes, posts,
  watches, read state, and character claims.
- Slice 4 added original-premise seed personas and shifted demo QA guidance
  toward premise-based communities.
- Slice 5 added a premise browser QA profile, route proof, and simulated UAT
  notes for public catalog and Studio discovery maintenance.
- Slice 6 completed the model extension review without adding schema.

Model extension decision:

- Keep `featured_event_material_id` as the durable current-chapter pointer,
  limited to a published event material for the same `community_id`.
- Keep `roster_posture`, `catalog_pitch`, `onboarding_pitch`,
  `activity_expectation`, and the profile choice fields in
  `community_discovery_profiles`.
- Keep public browse/search labels in discovery tags, not in director-defined
  in-world facets.
- Derive public scene/activity count labels from existing threads, posts,
  wanted hooks, claims, and materials through service read models.
- Do not add cinematic reference, TV Tropes, public ranking, or automatic
  premise-classification fields.

Deferred model candidates:

- Program Blueprint import/export for discovery profiles.
- Review cadence, first-face route, and onboarding funnel fields after
  application/intake work creates a stronger contract.
- Public activity freshness labels once there is enough seeded and live
  activity to distinguish alive, quiet, waiting, and paused realms without
  leaking private member behavior.

Next-phase follow-up completed:

- Studio discovery now reuses the public Network card component as its preview
  instead of rendering an approximate local card.
- Original-premise QA now proves first-face application, wanted board, and
  wanted detail entry paths across Harbor Society, Signal Creek, and Wayfarer
  Station.

## Steward Notes

Storage and migration:

- Discovery profile edits must be tenant-scoped by `community_id`.
- Any model extension requires fresh-schema and migrated-schema parity.
- Seed helpers must stay idempotent.

Service and Surface Contract:

- Services own filtering, sorting, privacy, and lane membership.
- Templates render named read models; they do not infer archetype or privacy
  state.
- Public catalog cards and member continuation lanes remain separate shapes.

Web and UX:

- Discovery should feel PBP-native: face, roster, thread, scene, wanted, claims,
  reserves, needs reply, waiting, caught up, and watching.
- Filters should answer writer-fit questions before generic taxonomy questions.
- Avoid turning Explore into a marketing page or a marketplace ranking surface.

Product Research:

- Use the 2026-05-15 research as medium-high confidence source signal plus
  product inference.
- Use simulated panels and browser QA to test clarity, not to invent market
  claims.
- Revisit TV Tropes-style vocabulary later for wanted-hook and plotting tools,
  not as the current community archetype registry.

Blueprint:

- Keep discovery profile import/export out of `ProgramBlueprint` until the
  Studio editing contract and public rendering contract have settled.
- If Blueprint support becomes necessary, create a dedicated contract plan with
  validation, docs, examples, dry-run output, and hydration tests.

Privacy and Security:

- Public discovery may expose public catalog metadata only.
- It must not expose staff notes, private rooms, draft materials, application
  review state, private plotting rooms, member obligations, active-face state,
  unread state, notifications, or cross-community identity data.

## Open Questions

- Which original-premise realm should become the default public demo target
  after product review?
- Which Explore filters should stay visible once the catalog grows beyond the
  nine archetype proofs?
- How much public activity freshness can be exposed without leaking private
  writer obligations?
- Which Studio preview affordance gives directors enough confidence before
  saving discovery profile changes?

## Implementation Order

Implemented order:

1. Public discovery lanes and filters.
2. Director Studio discovery editing.
3. Original seed depth pass.
4. Demo posture and persona matrix.
5. Browser and simulated persona QA.
6. Model extension review.

Rationale:

- Discovery lanes made the existing nine-community slate visible.
- Studio editing landed early because directors needed a real maintenance
  surface before QA could inspect the profile contract.
- Seed depth and persona docs then gave the QA pass realistic original-premise
  routes.
- Model extensions were reviewed after surfaces and seed depth created real
  pressure.

## Validation

Light proof for plan-only changes:

- `git diff --check`

Expected implementation gates for future slices:

- `uv run ruff check .`
- `uv run ruff format . --check`
- `uv run pytest -q --tb=short`
- `uv run ty check src/elbysodic/ tests/`
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`

## Closure

Close or archive this plan when:

- discovery lanes/filters, Director Studio editing, seed depth, demo posture,
  and QA are implemented or intentionally split into narrower active plans
- rejected model extensions are recorded with rationale
- the old broad premise seed plan is archived or converted into historical
  foundation context
