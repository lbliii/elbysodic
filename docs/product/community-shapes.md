# Community Shapes

Status: accepted product lens from 2026-05-15 PBP premise research
Evidence mode: source signal plus research inference promoted to product
doctrine where noted
Primary source notes:
- `research/synthesis/2026-05-15-current-pbp-premise-archetypes.md`
- `research/synthesis/2026-05-15-pbp-premise-census-followup.md`
- `research/synthesis/2026-05-15-premise-archetype-reference-skeletons.md`

## Product Decision

Writer Network discovery should classify public realms by premise engine first,
then layer genre, tone, access, pace, rating, roster, wanted, claims, reserves,
and current chapter signals on top.

Accepted product implication:

- Premise archetype is the primary public discovery lens.
- Genre is useful metadata, not the top-level community shape.
- Wanted hooks are entry paths inside premise communities, not standalone seed
  community archetypes.
- Sanctuary sandboxes are excluded from the first curated seed slate.
- Reference skeletons from film and television are internal craft scaffolding,
  not public-facing labels, market evidence, or seed copy.

Do not use this document as a market-share report. The research sample is
medium-high confidence for current public PBP/Jcink advertising patterns, but
it is not a precise census of all roleplay spaces.

## Community Archetypes

Use one primary archetype per public realm. Secondary discovery tags can cover
tone, genre, pressure, access, pace, and roster shape.

| Archetype | Writer Promise | Seed/Explore Pressure |
| --- | --- | --- |
| Small-town social web | A face enters a dense town of family, work, gossip, ritual, romance, and local status. | Needs businesses, families, public events, claims, wanted ties, and low-friction first scenes. |
| Weird-town mystery | Ordinary life has an unresolved phenomenon, rumor economy, secrets, and staff prompts. | Needs public rumors, encounter rules, current chapter, source-linked events, and public/private lore boundaries. |
| Urban supernatural pressure cooker | Species, factions, law, secrecy, nightlife, hunters, media, and danger collide in a city. | Needs species/faction claims, power boundaries, content posture, and staff review surfaces. |
| Court-and-faction fantasy | Houses, courts, magic, succession, war, faith, trade, and legitimacy create high-stakes scenes. | Needs constrained lore, faction openings, rank/house claims, and a clear first-face path. |
| Original canon-adjacent AU | Familiar story roles or genre shorthand are remixed through an original branch point. | Needs role archetypes without protected names, canon roster support, and strong IP hygiene. |
| Fame and industry drama | Public image, career pressure, patrons, gossip, contracts, scandal, and ambition create play. | Needs career ladders, media/gossip hooks, public events, and reputational stakes. |
| Survival, trials, and institution pressure | Candidates, houses, clans, or teams face visible tests under scarcity and rank pressure. | Needs consent-safe trial rules, house/rank claims, current selection, and authority pressure. |
| Occult historical pressure | Period institutions, class, crime, etiquette, reform, newspapers, and occult bargains collide. | Needs institution maps, class/status claims, safety notes, and public/private respectability pressure. |
| Strange frontier | A station, settlement, ship, island, or edge-world runs on scarcity, fragile law, and a signal from beyond. | Needs location hubs, scarcity/current incident, role claims, and operational scene loops. |

## Discovery Fields

These are public catalog fields. They should be owned by service read models
and repository methods, not by templates or slug/name heuristics.
Request-access hrefs are also read-model posture, not template string building:
templates may suppress the action for the current member, but they should not
infer public access paths from private membership state.
Public catalog helpers accept only `PublicCatalogCard` read models and reject
membership-bearing Studio Network rows, which keeps staff role, active face,
unread count, application, and plotting-room state out of browse/search cards.
The allowed search signals, excluded private signals, viewer modes, and batching
requirements are pinned in
`docs/architecture/public-catalog-privacy-contract.md`.

| Field | User Question It Answers | Product State |
| --- | --- | --- |
| `premise_archetype` | What kind of story engine does this realm make easy? | Accepted |
| `play_engine` | Is play character-driven, event-driven, mystery-driven, faction-driven, institution-driven, or survival-driven? | Accepted |
| `lore_aperture` | How much lore or canon do I need before my first face? | Accepted |
| `access_model` | Can I preview, apply, request access, or enter by invitation? | Accepted |
| `application_model` | Is entry a profile app, short app, canon app, member app, or interest form? | Accepted |
| `age_rating` and `content_rating` | Is this realm compatible with my age and content boundaries? | Accepted |
| `activity_pace` and `activity_expectation` | Can I keep up with the cadence and reply labor? | Accepted |
| `forum_adjunct` | Is the source of truth forum-first, Discord-light, or Discord-supported? | Accepted |
| `roster_posture` | Are canons, OCs, families, factions, species, careers, or role claims open? | Accepted |
| `catalog_pitch` | Can I understand the public story offer without reading a full guidebook? | Accepted |
| `onboarding_pitch` | Where should a new face start? | Accepted |
| discovery tags | Which story-fit lenses should browse/search expose? | Accepted as public catalog signals, not generic tags |
| featured event material | What current chapter is moving right now? | Accepted as a pointer to a published event material |
| Director Studio editor | Can directors intentionally position this realm for Writer Network discovery? | Accepted for discovery profiles and public discovery tags |

Deferred:

- Program Blueprint import for discovery metadata.
- Persisted editorial collections beyond profile/tag-backed slices.
- Continuity Graph-derived recommendations.

## Model Extension Review

Date: 2026-05-15

Decision: do not add more schema in this pass. The implemented public catalog,
Director Studio editor, original-premise seed depth, and browser QA profile put
enough pressure on the model to confirm that the current
`community_discovery_profiles` and `community_discovery_tags` tables cover the
first product surface.

Accepted durable fields:

- `premise_archetype`, `play_engine`, `lore_aperture`, `access_model`,
  `application_model`, `age_rating`, `content_rating`, `activity_pace`, and
  `forum_adjunct` stay allowlisted discovery profile choices.
- `roster_posture`, `catalog_pitch`, `onboarding_pitch`, and
  `activity_expectation` stay short director-authored public catalog copy.
- `featured_event_material_id` stays the current-chapter pointer and should
  point only to a published event material in the same community.
- Discovery tags stay public browse/search signals, separate from
  director-defined in-world facets.

Derived instead of stored:

- Public scene/activity counts should come from existing threads, posts,
  wanted hooks, claims, materials, and publication state through service read
  models.
- Public freshness labels should wait until the service can distinguish alive,
  quiet, waiting, and paused without exposing private writer obligations.
- First-face routes and review cadence should come from application/intake
  contracts once those flows settle, not from free-form discovery fields.

Deferred:

- Program Blueprint import/export for discovery profiles.
- More precise onboarding route fields after first-face onboarding and intake
  surfaces are stable.
- Real UAT before treating any additional field as a broad market need.

Accepted follow-up:

- Studio discovery should render the same public catalog card component used by
  Network Explore so directors are not editing against an approximate preview.
- Original-premise QA should include first-face application, wanted board, and
  wanted detail entry paths, not only public catalog cards.

Not-now:

- Cinematic reference skeleton fields.
- TV Tropes taxonomy fields.
- Automatic premise classification or marketplace ranking fields.
- Public categories for sanctuary sandboxes or wanted-hook-first communities.

## Public Touchpoint Rule

Public cards may expose adjunct posture such as `forum-first`,
`Discord-light`, or `Discord for plotting`, but Elbysodic-owned objects remain
the source of truth:

- premise materials
- current event/chapter materials
- boards and threads/scenes
- faces and rosters
- wanted hooks and plotters
- claims and reserves
- application paths

Do not treat Discord, chat, or offsite ads as canonical continuity storage.

## Seed Slate Implication

The first large seed rewrite should prove one original premise community per
archetype. Each seed packet needs enough structured surface area to support
real PBP workflows:

- public premise
- current event or chapter
- 6-8 playable boards plus one staff/private board
- 8-12 accepted characters or canon roster roles
- 5-8 wanted hooks
- claim/reserve posture
- starter scenes or threads
- discovery profile and tags
- at least one privacy/staff example where the archetype needs it

The existing literal-IP coded demo realms can remain temporarily as
compatibility fixtures, but public demo emphasis should move to original
premise communities as soon as seed/test/docs coverage permits it.
