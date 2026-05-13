# Studio Network Homepage Plan

Status: partially implemented; public catalog and public realm previews landed;
catalog fields, browser QA, and later personalization remain
Owner: Product/UI and network homepage stewardship
Created: 2026-05-03
Last updated: 2026-05-12
Review by: 2026-05-30
Closure criteria: split into PR-sized work for the editorial platform home,
network read models, privacy-safe public browsing, responsive browser QA, and
later personalization/search lanes.

## 2026-05-12 Baseline Update

Pulled `main` to `f08eae8` after PR #38. The public discovery baseline is now
stronger than this plan's 2026-05-09 snapshot:

- `AppServices.public_studio_network()` provides a signed-out public catalog
  path with membership, role, active-face, unread, plotting-room, and staff
  counts removed.
- `/` and `/network` choose signed-in continuation data only when a viewer is
  authenticated; otherwise they use the public catalog.
- Tenant-prefixed public previews now render `/c/{community_slug}`,
  `/world`, `/world/{material_slug}`, `/wanted`, and
  `/wanted/{wanted_slug}` for public-ready realms.
- Rendered security tests prove empty/backstage realms stay out of the public
  catalog and direct public preview, and public network cards do not expose
  membership or staff signals.

Still open:

- Formal catalog fields for genre, mood, availability, editorial collection,
  and invite/request posture.
- A cleaner `NetworkHome`/Explore read model if homepage rows need more shape
  than the current `StudioNetworkDirectory` can carry.
- Desktop/mobile browser QA for `/`, `/network`, public realm preview,
  public guidebook, and public wanted detail.

## 2026-05-13 Music-App Pattern Update

Apple Music and Spotify are the stronger reference class for the platform home
than forum indexes. The home surface should behave like editorial discovery:
featured media, trending rails, genre/mood shelves, and a light return path for
signed-in writers. It should not become the Writer Desk or a profile dashboard;
most returning writers will bookmark their realm or enter through the identity
menu.

Route posture:

- `/`: glossy discovery and visitor hook. Use large featured realm media,
  portrait trending tiles, landscape genre shelves, and low-copy CTAs.
- `/network`: explicit search/browse. This is where tag relationships, query
  refinement, genre/mood browsing, and deeper catalog filtering belong if the
  route survives as a distinct surface.
- Naming recommendation: label this surface `Explore` in navigation and page
  copy. Keep `/network` until a public-route migration is approved, then add
  `/explore` as an alias or redirect before considering removal of `/network`.
- `/desk`: personal obligations, needs reply, waiting, watching, applications,
  plotting, and active-face work.

Slice management should not be inferred only from free-text descriptions. The
durable model should combine:

- director-owned catalog tags: genre, mood, fandom/original, pace, writing
  length, invite posture, application posture, claims/reserves posture
- app-owned activity signals: recent public scene activity, open wanted count,
  roster size, newly opened status, public-preview eligibility
- optional editorial curation: featured weight and collection membership for
  launch week, seasonal spotlights, or staff-picked realms
- viewer personalization only after privacy gates: membership, active face,
  watched scenes, accepted interests, and writer-safe return paths

Early implementation can use seeded/search keywords to populate prototype
slices, but the product contract should move toward structured tags and
service-owned `NetworkHome` rows so public discovery stays explainable and
privacy-safe.

## 2026-05-09 Verification Update

`/` and `/network` now render a platform/network surface and `/network?q=...`
has a search form. The search implementation is still page-local filtering over
`studio_network()`, which is a logged-in membership directory. Production
readiness requires a service-layer `NetworkHome` or catalog read model that
separates safe public program cards from signed-in continuation lanes, plus
signed-out and signed-in privacy tests.

## Purpose

Make `/` feel like the front door to Elbysodic as a hub of playable PBP
communities, not a utility list of installed forums. The product direction is
PBP Jcink if it had a Hollywood studio layer: worlds are programs, characters
are faces, wanted hooks are casting calls, scenes are live productions, and the
home page should make a writer feel there is a rich menu of worlds and roles
waiting for them.

This plan primarily strengthens the Writer Network pillar from
`docs/product/strategy-spine.md`: public discovery, signed-in continuation,
active-face lanes, wanted pressure, and privacy-safe cross-realm entry. It must
not outrun the production trust gates that keep public catalog cards from
leaking membership, staff, application, or private scene data.

The current `/` behavior already routes shared-host visitors to
`network/page.html` when no tenant prefix is present. This plan promotes that
surface from "Studio Network directory" into the platform homepage.

## Research Basis

Research checked on 2026-05-03:

- Netflix's 2025 TV redesign moved core shortcuts to an always-visible top
  navigation, made recommendations more responsive to browsing behavior, added
  a personal hub, and surfaced richer title details to reduce decision fatigue.
  Source: <https://www.netflix.com/tudum/articles/netflix-new-tv-layout>
- Netflix documents layered personalization at the row level: which rows show,
  which titles sit in each row, and the order of titles inside the row. Source:
  <https://help.netflix.com/en/node/100639>
- Apple TV positions Home as the place to pick up where you left off, browse
  recommendations, explore collections, or start watching. Source:
  <https://support.apple.com/guide/tvapp/start-watching-on-the-home-screen-atvb05f2070b/1.0/web/1.0>
- Apple TV's product promise combines originals, sports, store inventory,
  channels, connected apps, recommendations, Continue Watching, Watchlist, and
  cross-device continuity. Source:
  <https://apps.apple.com/us/app/apple-tv/id1174078549>
- Baymard's homepage research says the homepage should make the site scope
  clear and support category navigation, search, and curated paths. Source:
  <https://baymard.com/homepage-and-category-usability/benchmark/page-types/homepage/>

Fresh inspiration checked on 2026-05-03:

- Dribbble searches for discussion UI, discussion threads, forum UI, and
  community threads still show active visual exploration around split
  feed/thread layouts, sidebars, dark social surfaces, mobile thread views,
  and polished card stacks. These are useful for visual shape and contemporary
  density, but weak evidence for shipped behavior. Sources:
  <https://dribbble.com/search/discussion-ui>,
  <https://dribbble.com/search/discussion-thread>,
  <https://dribbble.com/search/forum-ui-design>
- Behance has high volume for discussion/forum projects and is more useful
  than Dribbble when a project includes multiple screens or case-study
  rationale. Relevance varies, and many projects are still aspirational.
  Source:
  <https://www.behance.net/search/projects/discussion%20forum%20design?locale=en_US>
- Mobbin and Page Flows are stronger behavior references because they collect
  real app screenshots, user journeys, and flow recordings. Use them for
  onboarding, search, identity switching, save/follow behavior, profile flows,
  and review/moderation state decisions. Sources:
  <https://mobbin.com/>, <https://pageflows.com/>
- Godly, Landbook, Awwwards, and SiteInspire are better taste sources than
  forum behavior sources. They are useful for 2026 web/editorial signals:
  large type, strong grids, visible borders, premium negative space, live-site
  interaction craft, and better section composition. Sources:
  <https://godly.design/>, <https://land-book.com/>,
  <https://www.awwwards.com/>, <https://www.siteinspire.com/>
- Cosmos and Savee are moodboard/taste-graph sources. They are useful for
  visual vocabulary, color/image relationships, attribution habits,
  collaborative reference collection, and avoiding stale forum aesthetics.
  They are not component-behavior evidence. Sources:
  <https://www.cosmos.so/>, <https://inspire.savee.com/>

Translation for Elbysodic:

- Do not clone streaming UI literally. PBP is not passive viewing.
- Keep the streaming grammar that helps discovery: editorial feature,
  continue lane, curated rails, genre/mood shelves, rich cards, and quick
  decision context.
- Replace "watch" with PBP-native actions: enter a realm, continue writing,
  answer queue, start application, express interest, reserve a wanted, open a
  plotting room, or browse scenes.
- Treat inspiration sources by evidence level:
  - shipped products and flow libraries can inform behavior;
  - Dribbble/Behance can inform visual experiments;
  - moodboards and web galleries can inform art direction.
- Use fresh visual inspiration to lift the platform home away from old forum
  chrome, but keep Elbysodic's PBP-native control grammar intact.

## Product Decision

The Elbysodic/LBSodic home is the editorial studio-network front door.
`/network` is the distinct Explore surface for search, catalog browsing, and
discovery.

It answers:

> What world do I want to write in, and what can I do there right now?

It should feel high-end, editorial, and modern, but still dense enough for
roleplayers who are deciding where to spend a writing session. The visual
reference is closer to Apple TV and Netflix than a generic forum directory:
large media, cinematic world identity, curated rows, tight metadata, strong
continuation paths, and personal state when the writer is logged in.

It must remain server-rendered Chirp with small progressive-enhancement
islands. No SPA rewrite, no autoplaying sound, no hidden essential controls,
and no private/staff leakage into global catalog cards.

Route distinction:

- `/`: cinematic platform home, featured world, continuation lane, a small
  taste of featured worlds, casting pressure, and mood browsing.
- `/network`: Explore, with search first, browse/discovery lenses, filtered
  catalog results, casting index, and membership/active-face lanes.
- The global topbar may link to `Explore`, but it should not mark Explore as
  active on `/`. The brand is the Home affordance.

## Audience Modes

### New Or Signed-Out Visitor

Needs to understand the promise quickly:

- Elbysodic hosts roleplay communities.
- Communities are playable worlds with genre, tone, open roles, and current
  events.
- The visitor can browse, search, inspect a community, and start joining.

Default experience:

- Editorial featured world.
- Browse by genre/mood.
- Casting now / wanted hooks.
- Recently active or newly opened worlds.
- Sign in or apply actions where appropriate.

### Returning Writer

Needs to resume writing without losing the fun of browsing:

- Continue writing where a face has obligations.
- See current programs and active faces.
- Jump to queue, plotting rooms, applications, unread scenes, and open wants.
- Discover new worlds without the current community swallowing the platform
  home.

Default experience:

- "Continue writing" rail above general browsing.
- Current/active program can be featured, but not at the expense of discovery.
- Rows can be personalized by membership, active face, recent visits, and
  attention signals.

### Director Or Staff

Needs production visibility without turning the homepage into Studio:

- See owned/current programs.
- Notice application/review pressure where permission allows.
- Enter Studio for production work.

Default experience:

- Staff signals stay compact and permission-filtered.
- Director work is a lower-priority lane or card, not the hero.

## Page Structure

### 1. Platform Shell

Use the global shell, not the community shell:

- Brand: `Elbysodic` or future final platform wordmark.
- Primary global controls: Explore, Search, Sign in / identity.
- No community sidebar.
- No `World / Play / Desk / Studio` topbar unless a community is active.

The page should tolerate `/` and `/network` pointing to the same product
surface during the transition.

### 2. Editorial Billboard

The first viewport should sell one world with actual program identity:

- Large world hero image or generated media from the community media slot.
- Community mark and program name.
- Logline from current event, premise, or director-defined network pitch.
- Genre/mood facets such as `superhero crisis`, `magic school`, `survival
  sci-fi`, `small town`, `urban real life`.
- Decision metadata: open roles, active scenes, faces, current event, activity
  freshness.
- Primary CTA:
  - signed in and member: `Enter realm`
  - signed in but not member: `Start application` or future `Request invite`
  - signed out: `Preview world` plus `Sign in`
- Secondary CTA: current event, wanted board, or premise.

The billboard should not be a marketing split layout. It is a media-first
editorial hero with text over or integrated into the image treatment, leaving a
hint of the next rail visible on desktop and mobile.

### 3. Continue Writing

Equivalent to Continue Watching, but for writing obligations.

Show only when signed in:

- Needs reply.
- Waiting rooms with new plotting messages.
- Draft application or application needing revision.
- Watched scenes with unread posts.
- Accepted interest that can become a plotting room.
- Current face switch context when the action will write as a face.

This lane should rank by "what can I productively do next", not raw newest
activity. It should use existing queue language: `needs reply`, `waiting`,
`caught up`, `watching`, `application`, `plotting`.

### 4. Featured Worlds Rails

Curated rows make the network feel broad:

- `Featured worlds`
- `New this week`
- `Fantasy and magic`
- `Sci-fi and survival`
- `Superhero crisis`
- `Real life and small towns`
- `Fandom universes`
- `Original settings`
- `Short-form friendly`
- `Long-form slow burn`

Early MVP can derive these from seeded programs and director facets. Later,
programs need explicit catalog metadata rather than inferring from board
facets alone.

### 5. Casting And Wanted Rails

Make PBP-specific opportunities first-class:

- `Casting now`
- `Open wanted hooks`
- `Event roles`
- `Faction seats`
- `Family ties`
- `Rivals and foils`
- `Prospective concepts welcome`

Cards should make the community, role, creator face, and commitment level
clear. A wanted hook should never look like a generic ad tile.

### 6. Scene And Activity Rails

Show that worlds are alive:

- `Open scenes`
- `Recently active`
- `Event pressure`
- `Fresh plotters`
- `Rooms forming now`

Do not expose private/staff boards or membership-only details. Public cards can
show safe counts and public titles only. Signed-in members can see their
permission-filtered activity.

### 7. Browse By Mood

Add a compact browse band that feels like streaming genres but uses roleplay
language:

- `Found family`
- `Political pressure`
- `School year`
- `Survival`
- `Romance-forward`
- `Mystery`
- `Slice of life`
- `Canon divergence`
- `Original characters welcome`
- `Beginner friendly`

These should become catalog facets, not hard-coded copy, once more communities
exist.

### 8. Director Entry

Near the bottom, not in the emotional hero path:

- `Build a world on Elbysodic`
- `Open Studio`
- `Preview blueprint intake`

This is for directors and admins. It should not make the writer-facing
homepage feel like SaaS onboarding.

## Component Vocabulary

Promote repeated shapes instead of growing page-local CSS:

- `network_billboard`: editorial feature for one program/world.
- `program_poster_card`: vertical or landscape world card using community
  mark, hero media, logline, genre/mood facets, and safe counts.
- `network_rail`: titled horizontal or responsive row with an optional reason
  line and stable card sizing.
- `continue_writing_card`: personal action card for queue, plotting,
  application, unread scene, or current event continuation.
- `casting_card`: wanted-hook card that preserves creator face, wanted type,
  status, and prospective/new-character behavior.
- `catalog_chip`: genre/mood browse link, visually distinct from world facets
  inside communities.

Candidate location:

- Shared macros in `src/elbysodic/web/pages/_components/vocabulary.html` when
  they represent PBP-native concepts.
- Network-specific macros can start in `network/page.html`, then promote once
  reused by discover/casting/global search.

## Data Model And Service Needs

Current `studio_network()` is enough for a signed-in membership directory:

- community
- membership and role
- current character
- premise/current event
- roster count
- open wanted count
- application count
- plotting room count
- unread notification count
- theme preview

The editorial homepage needs a broader read model:

- public program catalog entries independent of membership
- program availability: open, invite-only, coming soon, archived, private
- network pitch/logline distinct from the in-community premise
- catalog genres/moods/tags
- featured priority and editorial collection membership
- safe public counts: active scenes, open wanted, roster size, last public
  activity
- hero media and mark from existing community media slots
- viewer-specific continuation items merged in only after auth and permission
  checks

Do this through service-layer methods, not ad hoc SQL in the page handler:

- `services.network_home()` or similar read model.
- Public catalog queries must not require a membership.
- Personal lanes must resolve through current viewer memberships and existing
  repository/service permission boundaries.

## Visual Direction

The page should feel cinematic without becoming a dark Netflix clone.

Principles:

- Media first, but readable. Use actual community hero images where possible.
- Editorial typography, controlled density, and strong section rhythm.
- Dark mode can be dramatic, but light/system themes must remain coherent.
- Avoid a one-note dark blue/slate or purple gradient palette.
- Avoid decorative orbs, bokeh blobs, and generic gradient backgrounds.
- Cards stay stable in size. Hover/focus can reveal detail, but should not
  shift layout.
- No auto-rotating carousels. Horizontal rails need visible controls,
  keyboard access, and useful fallback wrapping.
- Motion is optional and reduced-motion safe. No autoplaying sound.
- Mobile should feel like a browseable editorial feed, not a compressed
  desktop grid.

Fresh-source translation:

- From Dribbble/Behance: explore split browsing/detail compositions, quiet
  side metadata, mobile-first thread cards, modern social-feed spacing, and
  dark editorial surfaces. Reject unsupported glassmorphism, fake AI
  dashboard chrome, and unlabeled icon-heavy product verbs.
- From Mobbin/Page Flows-style shipped references: use for onboarding,
  identity switching, saved/followed collections, search, profile, and
  moderation/review flow decisions.
- From Godly/Landbook/Awwwards/SiteInspire: borrow large-type editorial
  rhythm, distinctive section composition, visible grids/borders, high-quality
  media treatment, and premium restraint. Do not import marketing-page
  hero/split layouts into the actual app shell.
- From Savee/Cosmos/Are.na-style moodboards: build art-direction boards for
  each homepage rail or seed world before heavy CSS work. Track atmosphere,
  typography, imagery, and color relationships separately from interaction
  decisions.

Concrete first-pass composition:

```text
Global topbar

[large editorial billboard]
  featured world image
  program mark + name
  logline
  genre/mood marks
  Enter realm / Preview world / Start application

Continue writing
  queue card | plotting card | application card | unread scene card

Featured worlds
  program poster cards

Casting now
  wanted/casting cards

Browse by mood
  compact catalog chips

Recently active
  safe activity cards

Director entry
  build/open Studio affordance
```

## Implementation Order

### Phase 1: Editorial MVP On Existing Data

Goal: make `/` and `/network` feel like a premium studio network for the
currently reachable programs.

Work:

- Rename page copy away from utility directory language.
- Use existing community hero media instead of only color swatches.
- Add an editorial billboard sourced from current program, current event, or
  the strongest seeded program.
- Add a signed-in `Continue writing` lane from existing counts and current
  program links.
- Convert the current program list into a `Featured worlds` rail or responsive
  poster grid.
- Keep all links tenant-prefixed through existing `entry_href` helpers.

Acceptance checks:

- `/` and `/network` render without the community shell.
- Current X-Men, HP, Jurassic, NYC, and small-town seed programs visibly feel
  like different worlds.
- Desktop and mobile screenshots show no text overlap, no blank hero media,
  and no card layout shift.

### Phase 2: Network Read Model

Goal: separate public catalog data from signed-in membership continuation.

Work:

- Add a `NetworkHome` read model with `featured_program`,
  `continue_items`, `editorial_collections`, `casting_items`, and
  `browse_facets`.
- Keep tenant boundaries explicit on every query.
- Add tests for signed-out and signed-in views.
- Make private/staff-only data impossible to include in public catalog cards.

Acceptance checks:

- Signed-out visitors see public programs and safe counts.
- Signed-in writers see only continuation items they are allowed to access.
- Director/staff counts appear only when policy allows.

### Phase 3: Catalog And Search Hooks

Goal: make the homepage a real discovery system, not only a visual refresh.

Work:

- Add program catalog fields or a structured primitive for network genres,
  moods, availability, and editorial collections.
- Add a global search/browse entry that can handle natural PBP phrases later:
  "magic school with open students", "sci-fi survival wanted hooks",
  "small town slow burn".
- Keep catalog facets separate from in-community director facets unless a
  deliberate mapping exists.

Acceptance checks:

- Browse chips lead to meaningful filtered results.
- Search is visible from the platform topbar.
- Catalog filtering does not leak private community objects.

### Phase 4: Personalization

Goal: make rows adapt without becoming opaque or creepy.

Inputs:

- current memberships
- active/default faces
- recent program visits
- queue state
- watched scenes
- applications
- plotting rooms
- expressed interest
- saved/followed programs

Rules:

- Always keep at least one broad discovery row for serendipity.
- Label reason lines in PBP language: `because Rogue has wanted hooks here`,
  `new scenes in a watched realm`, `casting roles near your factions`.
- Do not personalize from demographic assumptions.
- Provide visible search and browse escape hatches.

## Dependencies

- Tenant-prefixed URL contract remains stable.
- Community media slots and seed media remain available.
- Appearance Studio owns community art direction, but platform card grammar is
  product-owned.
- Navigation docs continue to treat `/` as platform home and
  `/c/{community_slug}` as community home on shared hosts.

## Risks

- A cinematic homepage can hide useful writing actions if the hero becomes too
  dominant.
- Public catalog cards can leak private/staff activity if the read model
  reuses member-only summaries.
- Too many rails can recreate streaming choice paralysis.
- Over-copying Netflix can make Elbysodic feel passive, while PBP needs
  writable opportunities.
- Dark, media-heavy UI can hurt accessibility if contrast, reduced motion, and
  mobile wrapping are not tested.

## Not Now

- Autoplay video or audio previews.
- Algorithmic ranking beyond simple editorial and viewer-state rules.
- AI search before catalog metadata and permission-safe result models exist.
- Public monetization, subscriptions, or app-store style purchase flows.
- Director-customizable platform homepage layout.
- A full redesign of individual community home pages.

## Steward Notes

Consulted:

- Root `AGENTS.md`: PBP-native mission, community as creative production,
  active face as product lens, and tenant-aware architecture.
- `docs/AGENTS.md`: product docs should remain practical and avoid generic
  SaaS language.
- `src/elbysodic/web/AGENTS.md`: keep server-rendered Chirp pages, shared PBP
  components, and theme CSS in `elbysodic-theme.css`.
- `docs/product/navigation-menus.md`: `/` is the platform home on shared
  hosts; community home lives at `/c/{community_slug}`.
- `docs/product/information-hierarchy.md`: promote repeated PBP concepts and
  preserve stable vocabulary for counters, latest lines, facets, faces, and
  activity signals.
- `docs/product/control-topology.md`: keep controls visible, labeled, and
  attached to the moment of intent.
- `docs/product/appearance-studio.md`: platform grammar stays product-owned
  while community media and theme tokens provide atmosphere.

Boundary decisions:

- The platform home is not an individual community world gateway.
- The platform home is not Studio/admin onboarding.
- Public catalog data and signed-in continuation data need separate service
  boundaries.
- Streaming inspiration is translated into writable PBP opportunities, not
  copied as passive viewing UI.

Suggested next checks:

- Browser screenshot audit of current `/network` at desktop and mobile before
  the first visual PR.
- Read model privacy tests before exposing public catalog cards.
- Seed data review to ensure each demo program has a strong enough hero,
  logline, genre/mood, and open opportunity for the homepage.
