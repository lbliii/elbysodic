# Community Hub Editorial Iteration

Status: implementation wave landed; monitor preview feedback before archive
Owner: Product design, Writer Network, Realm Studio, service, web, storage/seed,
tests, and surface-contract stewardship
Created: 2026-05-18
Last updated: 2026-05-18
Review by: 2026-06-01
Closure criteria: `/c/{community_slug}` reads as an elegant story-facing realm
hub with service-owned story, premise-stage, lore, cast, places, wanted, and
activity sections; redundant labels and CRM/dashboard patterns are removed;
Harbor Society and at least two other original-premise communities have mature
seed proof; rendered tests and browser QA pass the Surface Quality Bar; or the
plan is split into narrower implementation plans.

## Evidence Mode

Promotion review from:

- live critique of `http://localhost:8002/c/harbor-society`
- `docs/product/surface-quality-bar.md`
- `docs/product/information-hierarchy.md`
- `docs/product/experience-direction.md`
- `design/composition-bible.md`
- `design/AGENTS.md`
- `src/elbysodic/web/AGENTS.md`
- `docs/product/user-personas-panel.md`
- existing gateway implementation in `src/elbysodic/services/forum.py`,
  `_components/realm_gateway.html`, and `tests/test_forum_slice.py`

This is accepted product doctrine plus simulated user-panel pressure, not real
UXR. Confidence is medium until browser QA and live user observation reinforce
the direction.

## Surface Intent Brief

- **Audience:** signed-out visitor, invited writer, first-face applicant, hook
  hunter, and signed-in member returning to a realm.
- **First five seconds:** "I know what this story is, why it is alive now, what
  kind of writing it expects, and whether I want to enter."
- **Primary object:** the realm as a living story world, not the board index or
  director readiness state.
- **Primary decision/action:** keep reading, browse hooks, read the premise,
  request access, continue an application, or continue writing.
- **Dominant reference job:** Apple TV/Netflix editorial clarity for public
  story presentation; Slack/Discord layered context for navigation and member
  continuation; Jcink/PBP depth for guidebook, faces, claims, wanted, places,
  and scenes.
- **Negative reference:** Salesforce CRM, launch checklist, route directory,
  equal-weight card grid, old forum index, and placeholder scaffolding.
- **Progressive disclosure:** first viewport sells premise and fit; next
  shelves reveal current stage, lore, cast, places, wanted hooks, public scenes,
  and quieter activity. Studio/Desk state stays out of visitor flow.

## What We Learned

- The current gateway still over-exposes implementation structure: readiness
  signals, counts, type labels, and repeated section nouns can make the page
  feel like a dashboard instead of a story offer.
- Public visitors need story confidence before operational confidence: genre,
  tone, writing cadence, rating/content posture, access posture, current
  premise stage, cast, lore, places, and open hooks matter more than how many
  rows exist.
- The page should sell a living premise. "Current chapter" is not enough as a
  label; the UI needs to show what changed, what pressure is active, and what a
  new face can do with it.
- Existing seed data is stronger than the current hub makes visible. Harbor
  Society already has characters, social claims, current chapter, premise,
  guidebook material, places, and wanted hooks; the read model/template are not
  yet using that depth.
- Schema should not lead this iteration. Existing `community_discovery_profiles`,
  `materials`, `boards`, `characters`, `wanted_ads`, `claims`, and curated
  gateway slots can support the next pass. A migration is only justified if
  director-authored premise evolution cannot be represented by published
  materials plus service-owned read models.

## Target Page Shape

1. **Editorial hero / story frame**
   - Realm name, story promise, rating/content posture, access posture, writing
     style/cadence, and one or two CTAs.
   - No metric band. No readiness language. No duplicated "current chapter"
     label stack.

2. **Premise stage**
   - Current chapter/event as a narrative state: what is happening, what
     changed, and what a first face can touch.
   - Optional recent/prior public event material if available, but only as
     story progression, not a timeline widget.

3. **Lore and world rules**
   - Public guidebook slices that answer what kind of world this is: premise,
     social rules, factions/powers/houses/species when present, application
     expectations, and content posture.
   - Section context carries the category; child cards lead with useful titles
     and hooks.

4. **Canon cast / roster signal**
   - A small public-safe cast shelf from accepted characters and roster posture:
     names, one-line identity, and story tie.
   - No membership ownership, private writer identity, staff notes, drafts, or
     inactive/private faces.

5. **Factions, claims, or social lanes**
   - Where the realm has factions, houses, species, families, businesses, ranks,
     powers, or club roles, surface them as playable story lanes.
   - Use existing claim types, claims, materials, and discovery tags before
     adding new schema.

6. **Places**
   - Atmosphere-rich place cards with playable hooks. Do not repeat "scene
     hub," "place," public thread counts, or readiness states inside the cards.

7. **Wanted hooks and public scenes**
   - Story invitations and public open scenes as ways into play.
   - Wanted child cards should explain relationship/role pressure, not repeat
     `Wanted hook`.

8. **Quiet activity / confidence footer**
   - Activity and pace appear late and lightly. It should answer "is this alive
     and compatible?" without becoming analytics.

Member continuation may appear above or near the story frame only when signed
in, but it must stay visually distinct from the public editorial promise.

## Implementation Slices

### Task 1: Hub Story Contract

Goal: add a service-owned story-frame contract so the hero/top card answers
genre, cadence, rating, access posture, story promise, and first action without
rendering raw discovery-profile fields.

Work:

- Add read models for story frame / public fit signals in
  `src/elbysodic/services/read_models.py`.
- Derive fields from `CommunityDiscoveryProfile`, current event/premise
  material, open wanted state, and access posture.
- Replace hero signal badges and readiness-style copy with edited story-fit
  language in `_components/realm_gateway.html`.
- Preserve public/member separation and existing continuation behavior.

Proof:

- Rendered tests for Harbor Society assert story-fit signals are present and
  no readiness/count dashboard copy appears.
- Privacy tests assert no active face, Desk, private room, staff, application
  review, or notification state leaks to visitors.

### Task 2: Premise Evolution Shelf

Goal: show where the premise currently stands and make the current chapter feel
like story progression instead of a label.

Work:

- Add a `premise_stage` read model from current event, premise, and public
  event materials.
- Render one focused section after the hero with the current chapter title,
  narrative pressure, playable implications, and a read-more link.
- Use prior/other event material only when it adds progression clarity.

Proof:

- Tests cover current-event, no-event, and multi-event communities without
  changing template conditionals.
- Harbor Society renders `Founders Gala` as an active story pressure, not a
  generic "Current chapter" badge stack.

### Task 3: Lore, Factions, And Rules Slice

Goal: make public world information visible enough to sell setting depth while
keeping the page breathable.

Work:

- Add grouped guidebook/lore previews from published materials.
- Derive faction/house/species/social-lane summaries from claim types,
  discovery tags, and published faction/lore materials where present.
- Avoid new schema unless the service cannot derive a reusable public-safe
  lane from existing objects.

Proof:

- Tests assert lore/material child cards do not repeat parent labels.
- Original-premise communities with factions, houses, species, or social claims
  render appropriate lane labels without generic taxonomy.

### Task 4: Public Cast Shelf

Goal: expose enough canon/accepted-character signal for visitors to understand
who is already playable or socially important.

Work:

- Add a public-safe cast preview from accepted characters.
- Show name, tagline/summary, and a useful story tie or claim when available.
- Keep writer membership, private notes, drafts, and inactive/private state out
  of the public read model.

Proof:

- Rendered tests cover public cast presence and absence.
- Cross-community/privacy tests prove no private membership or wrong-community
  character data leaks.

### Task 5: Editorial Recomposition

Goal: reorder the hub into the target story journey and remove remaining
dashboard/route-directory behavior.

Work:

- Recompose `_components/realm_gateway.html` around story frame, premise
  stage, lore, cast, places, wanted, public scenes, and quiet activity.
- Promote repeated shapes to `_components/` only when they represent stable PBP
  concepts.
- Keep CTAs contextual and sparse.

Proof:

- Rendered tests assert absent redundant labels: `Scene hub`, `Wanted hook`,
  `Guidebook path`, readiness bands, repeated "current chapter" stacks, and
  public thread-count labels inside homogeneous sections.
- Browser QA checks first viewport, desktop/mobile layout, density, label
  discipline, and no-media fallback.

### Task 6: Mature Seed Proof

Goal: use real-feeling original-premise seed content to validate the hub.

Work:

- Audit Harbor Society, Signal Creek, and one faction-heavy realm for enough
  premise, current stage, lore, cast, claims/factions, places, wanted hooks,
  and public scenes.
- Add concise seed content only where a section would otherwise be forced into
  placeholder copy.
- Keep seed changes idempotent and tenant-scoped.

Proof:

- Seed contract tests assert each representative realm has the minimum data for
  the new hub sections.
- Changelog/docs update only if public demo posture changes materially.

### Task 7: Surface Quality QA

Goal: prove the rendered hub meets the new quality bar before calling the
iteration done.

Work:

- Run focused tests and app check.
- Run browser QA for desktop and mobile on Harbor Society plus at least two
  archetype variants.
- Record screenshot notes against the Surface Quality Bar.
- Run a local synthetic user-panel review after screenshots exist, clearly
  labeled simulated.

Proof:

- QA notes include accepted fixes, deferred findings, and residual risk.
- Any accepted QA finding becomes a test, doc update, shared component, or
  follow-up plan.

## Schema And Seed Prerequisite Decision

No schema migration should land in the first slice.

Existing data can support the next hub:

- story fit: `community_discovery_profiles`
- genre/tone/search lenses: `community_discovery_tags`
- premise and current stage: published `materials`, especially `premise` and
  `event`
- lore/factions/rules: published `materials`, claim types, claims, and tags
- cast: accepted `characters`
- places: public `boards`
- wanted: open `wanted_ads`
- activity: public threads/posts
- director curation: `community_gateway_slots`

Initial Harbor Society seed audit on 2026-05-18:

- 8 accepted characters are available for a public cast shelf.
- 5 published materials cover premise, current chapter, social lore,
  application guidance, and town calendar.
- 4 claim types cover face, family, club role, and business lanes.
- 4 scene hubs render through the gateway.
- 3 wanted previews render through the gateway.
- Public active/open scenes now render after the gateway read model was
  broadened to public, unlocked scene threads without exposing private rooms.

Schema review is deferred until at least Task 2 or Task 3 proves a stable
missing concept. Candidate future fields:

- explicit premise-stage/stage-order contract
- director-authored public cast/faction curation
- public activity freshness labels that do not expose private obligations
- first-face route contract after application/intake work settles

Any accepted schema change must stop for human review, then ship with migration,
repository, service, rendered privacy proof, docs, and changelog.

## Steward Synthesis

Product Design:

- Accepted: require Surface Intent Brief and density budget before coding.
- Accepted: Apple TV/Netflix editorial clarity leads public hub composition.
- Accepted: Jcink depth should appear as curated shelves and PBP primitives,
  not visual density.
- Deferred: richer motion/media treatments until the content contract is clean.

Rendering And UI:

- Accepted: templates should render named read models and avoid deciding which
  data is safe or important.
- Accepted: browser screenshot QA is required for this iteration.
- Accepted: repeated labels and child type badges are regressions.

Service And Surface Contract:

- Accepted: privacy, ranking, filtering, and section membership belong in
  `AppServices.public_realm_gateway()` and helper read models.
- Accepted: member continuation remains viewer-scoped and separate from public
  story presentation.

Storage And Seed:

- Accepted: no migration for the first pass.
- Accepted: mature seed gaps should be filled through existing materials,
  characters, claims, boards, wanted hooks, and threads before adding schema.

User Panel Synthesis:

- New applicants need tone, safety, activity, and first-face confidence before
  committing.
- Hook hunters need visible playable openings without decoding internal labels.
- Directors need the public page to show authorship and polish without exposing
  operations.
- Safety-boundary writers need public/private state to stay clean even when the
  page becomes richer.

## Validation

Implementation proof from this wave:

- `uv run ruff check src/elbysodic/services/read_models.py src/elbysodic/services/forum.py tests/test_forum_slice.py scripts/browser_qa.py`
- `uv run ruff format . --check`
- `uv run pytest tests/test_forum_slice.py -q --tb=short -k "gateway or original_premise"`
- `uv run pytest tests/test_web_security.py tests/test_tenant_repository.py -q --tb=short`
- `uv run ty check src/elbysodic/ tests/`
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`
- `make changelog-check`
- `uv run python scripts/browser_qa.py --base-url http://127.0.0.1:8002 --profile community-hub --artifact-dir /private/tmp/elbysodic-community-hub-qa`
