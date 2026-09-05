# Community Landing Archetype Stress Pass

Status: design stress pass
Date: 2026-05-16
Primary artifact: `design/static-community-landing-v2-mock.html`
Related plan (archived): `plans/archive/2026/community-landing-design-system-translation-2026-05-15.md`

## Purpose

The V2 community landing mock is directionally right: `/c/{community_slug}`
should be a public realm gateway with atmosphere, playable doors, public-safe
scene motion, wanted hooks, guidebook entry, and audience-aware continuation.

The 2026-05-15 premise research adds one correction before implementation:
the gateway should be organized around the realm's **premise engine** first.
Current events are one strong atmosphere source, but they cannot be the default
mental model for every PBP community.

The landing page should answer:

- What kind of play does this realm make easy?
- What is the public story pressure right now?
- Where can my first face enter?
- Which scene hubs, wanted hooks, claims, reserves, or guidebook objects prove
  that the premise is playable?
- What is public, applicant-only, member-only, or staff-only?

## Evidence Mode

Evidence mode: source signal plus research inference already promoted to
product doctrine in `docs/product/community-shapes.md`.

Inputs:

- `docs/product/community-shapes.md`
- `research/synthesis/2026-05-15-current-pbp-premise-archetypes.md`
- `research/synthesis/2026-05-15-pbp-premise-census-followup.md`
- `research/synthesis/2026-05-15-premise-archetype-reference-skeletons.md`
- `design/static-community-landing-v2-notes.md`

Confidence: medium-high for premise-engine discovery; medium for exact visual
weighting until browser QA and user-panel review inspect rendered variants.

## Design Decision

Rename the implementation concept from only "realm gateway with programmable
atmosphere" to:

**Premise gateway with playable entry paths.**

This does not reject the V2 mock. It reframes it:

- Hero: lead with the public realm offer and premise engine.
- Atmosphere: show current event, season, standing tension, mystery, status
  pressure, institution rule, scarcity, or location pulse.
- Pulse: describe public-safe play readiness, not generic metrics.
- Entry path: show the first-face route through wanted, claims, reserves,
  application guide, public scenes, or a guidebook object.
- Scene hubs: prove how the premise becomes threads.
- Wanted hooks: behave as entry paths inside the premise, not the top-level
  category system.

## Landing Slots

| Gateway Slot | Must Communicate | Avoid |
| --- | --- | --- |
| Hero identity | Realm name, premise engine, access posture, first public action. | A poster-only hero that hides the playable offer. |
| Atmosphere source | Current event, standing tension, season, institution pressure, mystery, scarcity, or featured material. | Treating every realm as event/crisis-driven. |
| Public pulse | Safe signals such as open hooks, public scene hubs, current chapter, roster posture, and guidebook readiness. | Staff workload, private queues, active-face state, unread state, or review counts. |
| First-face path | The next useful visitor step: read premise, browse wanted, check claims, request access, continue application. | A generic marketing CTA disconnected from PBP work. |
| Scene hubs/locations | Places, boards, institutions, factions, or social containers where scenes start. | Slack channel metaphors or equal-weight card grids. |
| Wanted/plotter lane | Character, relationship, faction, role, or scenario hooks that make entry less lonely. | Making wanted the whole community archetype. |
| Guidebook lane | Premise, rules, application guide, factions, current event, or safety notes. | Burying lore burden behind a beautiful hero. |
| Audience continuation | Applicant/member/staff continuation only after service-owned privacy checks. | Public leakage of Desk, staff, applications, notifications, private rooms, or obligations. |

## Archetype Matrix

| Premise Archetype | Gateway Hero Emphasis | Atmosphere Source | Public Pulse | First Entry Path | Stress Check |
| --- | --- | --- | --- | --- | --- |
| Small-town social web | Named town, social density, family/work/ritual ties. | Seasonal event, local gossip, business/family pressure. | Open connections, businesses, families, public events, wanted ties. | Browse wanted, check claims, enter a public scene hub. | Works without a central metaplot or crisis hero. |
| Weird-town mystery | Ordinary place plus unresolved phenomenon. | Rumors, encounter prompt, current chapter, public/private lore split. | Public rumors, open locations, prompt cadence, safety notes. | Read premise, choose local/researcher/skeptic angle, request access. | Mystery is legible without exposing private answers. |
| Urban supernatural pressure cooker | City factions, species, law, danger, nightlife. | Treaty crisis, faction pressure, law change, hunter activity. | Species/faction claims, content boundaries, public scenes, wanted roles. | Read power rules, check claims, browse faction hooks. | Power/lore burden is visible but not overwhelming. |
| Court-and-faction fantasy | Court, house, magic, succession, war, legitimacy. | Succession crisis, council session, border incident, relic pressure. | House/faction openings, rank claims, guidebook complexity, current chapter. | Pick faction/house, read rules, apply or reserve. | Strong lore identity still offers a clean first-face path. |
| Original canon-adjacent AU | Familiar role grammar through an original branch point. | Branch-point consequence, legacy conflict, institution pressure. | Role archetypes, roster/canon posture, reserves, public guide. | Browse role openings, read branch point, reserve/apply. | Uses original labels and avoids protected-name dependency. |
| Fame and industry drama | Public/private identity, career ladder, scandal, ambition. | Awards season, contract leak, gossip cycle, production deadline. | Career roles, reputation stakes, wanted ties, public events. | Choose career lane, browse wanted, check claims. | Feels playable without supernatural/event-combat framing. |
| Survival, trials, and institution pressure | Candidates, teams, houses, scarcity, visible tests. | Trial round, authority pressure, resource shortage, ranking moment. | House/team claims, trial rules, safety posture, current selection. | Read trial rules, pick team/role, apply. | Pressure is consent-safe and does not become generic battle royale. |
| Occult historical pressure | Period institutions, class/status, etiquette, crime, occult bargains. | Newspaper scandal, society season, reform conflict, occult debt. | Institution map, class/status claims, safety notes, public respectability pressure. | Read etiquette/safety, choose institution, browse wanted. | Period/lore context supports first scenes instead of blocking them. |
| Strange frontier | Settlement, station, ship, island, fragile law, scarcity. | Signal, storm, supply crisis, frontier incident. | Location hubs, role claims, scarcity ledger, public incident, operational loops. | Pick role/location, read station law, enter open scene. | Scarcity and operations feel like story engines, not admin dashboards. |

## Required Mock Stress Variants

Do not make nine full mocks before implementation. Make three annotated states
or lightweight variants that test the slots against different premise engines.

### Variant A: No-Event Social Realm

Representative archetype: small-town social web.

Purpose: prove the page has identity when there is no crisis, current event, or
heavy lore.

Expected changes from the X-Men V2 mock:

- Hero copy foregrounds town social density and low-friction first scenes.
- Atmosphere source comes from seasonal ritual, local gossip, or public event.
- Pulse favors open connections, businesses, claims, wanted ties, and scene
  hubs ready for casual entry.
- Location cards may be businesses, neighborhoods, homes, or civic spaces.
- Entry path starts with wanted/claims/public scene rather than guidebook depth.

### Variant B: Gated-Lore Mystery Realm

Representative archetype: weird-town mystery.

Purpose: prove the gateway can sell intrigue while protecting staff/private
truth.

Expected changes from the X-Men V2 mock:

- Hero copy names the public phenomenon, not the answer.
- Atmosphere source is a rumor, prompt, public incident, or current chapter.
- Guidebook lane distinguishes public premise, safety notes, and unknowns.
- Public scene rows show mystery pressure without naming private plots.
- First-face path offers several entry angles: local, newcomer, researcher,
  skeptic, witness, believer.

### Variant C: Institution/Status Pressure Realm

Representative archetypes: fame and industry drama, survival/trials, occult
historical pressure, or strange frontier.

Purpose: prove the gateway handles non-combat pressure where status,
institution, scarcity, or reputation generates scenes.

Expected changes from the X-Men V2 mock:

- Hero copy foregrounds the institution or operating pressure.
- Pulse uses public-safe role/claim/readiness signals instead of crisis counts.
- Scene hubs may be studios, courts, houses, teams, newspapers, stations, or
  settlements rather than literal locations only.
- Wanted hooks emphasize role openings, reputation ties, staffable scenarios,
  and first-thread pressure.
- The layout resists becoming a generic operations dashboard.

## V2 Mock Adjustments Before Production Translation

- Keep event states, but rename the data contract around `atmosphere_source`,
  not `event_state`.
- Keep location bento, but generalize copy to scene hubs, places, institutions,
  or operational locations depending on archetype.
- Add `premise_archetype`, `play_engine`, `lore_aperture`, `roster_posture`,
  `catalog_pitch`, and `onboarding_pitch` to the gateway planning vocabulary
  where the service read model needs public-safe copy.
- Let current event intensify the hero when present; let standing premise,
  social pressure, mystery, institution, scarcity, or public material carry it
  when not.
- Do not add schema for gateway layout controls. Use existing discovery
  profile fields and derive public-safe counts from existing objects.
- Use original-premise seed communities as the production proof, not only
  `/c/x-men-apocalypse`.

## Product Copy Rules

- Use public-facing archetype language sparingly. Writers should understand the
  promise; they do not need to see the internal taxonomy label everywhere.
- Prefer playable nouns: face, scene, thread, wanted, claims, reserves, roster,
  premise, guidebook, current chapter, scene hub.
- Put genre after premise. "Supernatural city" is weaker than "a city where
  species law, nightlife, hunters, and faction debts collide."
- Avoid reference-skeleton labels in UI. Film/TV skeletons are craft support,
  not user-facing claims.
- Avoid generic metrics. Replace "12 active users" style dashboard language
  with public-safe play readiness.

## Proof Before Implementation

- Browser QA should include at least three representative original-premise
  realm gateways, not only the X-Men seed route.
- Rendered tests should cover no-event, one-event/current-chapter, and
  multiple-atmosphere states where the read model supports them.
- Privacy tests must prove that archetype-rich public previews still hide
  staff notes, private boards, application review state, active-face state,
  member Desk obligations, notifications, unread state, and private plotting.
- A user-panel or simulated UAT pass should ask whether the visitor can name
  the premise engine and first-face path after scanning the gateway.

## Accepted

- Treat the V2 mock as a strong composition direction.
- Reframe production work around premise gateway plus playable entry paths.
- Use event/crisis treatment as one variant, not the base assumption.
- Stress the pattern against three archetype families before implementation.

## Deferred

- Full mocks for all nine archetypes.
- New schema for gateway layout control.
- Program Blueprint import/export for discovery profile fields.
- Public ranking, marketplace scoring, or automatic premise classification.

## Rejected

- Rebuilding the community home as a generic forum index.
- Treating wanted hooks as standalone community archetypes.
- Treating sanctuary sandboxes as first-pass public discovery archetypes.
- Using protected IP shorthand as the public center of original-premise seeds.
