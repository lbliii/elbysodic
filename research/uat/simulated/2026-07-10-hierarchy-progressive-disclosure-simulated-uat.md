# Simulated UAT Session: Hierarchy And Progressive Disclosure

Status: simulated UAT
Date: 2026-07-10
Researcher: Codex
Artifact inspected: current staging routes and fresh desktop/mobile screenshots
Artifact path or URL: `https://elbysodic-staging.up.railway.app`
Synthetic users: Active Scene Writer, Invited/New Face Applicant, Community
Director, Staff Moderator, Safety-Boundary Writer, Modern Design Skeptic
Seed docs: `docs/product/user-personas-panel.md`,
`docs/product/surface-quality-bar.md`, `docs/product/information-hierarchy.md`,
`docs/product/experience-direction.md`
Confidence: medium

This is simulated task testing against fresh rendered screenshots. It can
expose likely friction, but it does not replace observed user behavior.
Screenshots were captured from public staging on desktop and mobile during this
run and intentionally were not committed as durable research evidence.

## Tasks

1. Decide what Harbor Society is and choose the next meaningful entry action.
2. Return as Maris Vale and find the scene that needs a reply.
3. Identify the next director obligation from Studio.
4. Find the current-event and guidebook work inside Studio Content.
5. Enter Shoreline Club, understand what is playable, and start or continue a
   scene without director controls taking over the story path.

## Success Criteria

- The user understands the surface purpose and next action within five seconds.
- Community, membership, active face, story object, and audience state remain
  legible.
- One primary action leads each viewport region.
- Supporting depth remains reachable without rendering a route inventory.
- Staff/director controls stay available but outside ordinary story and writing
  flow.
- Desktop and mobile preserve the same action hierarchy without collisions,
  clipped copy, or excessive scroll before the primary task.

## Starting States

- Public visitor: signed out on `/c/harbor-society`.
- Active writer/director: signed in as the seeded Harbor Society director,
  wearing Maris Vale.
- Viewports: 1440x1100 desktop and 390x844 mobile.
- Privacy posture: public screenshots contain public-safe data; signed-in
  screenshots use the seeded public staging demo account and contain no private
  participant research data.

## Step Findings

### 1. Public Community Home

General health: needs structural revision.

- Strength: the realm premise, atmosphere, fit, current event, places, scenes,
  guidebook, wanted hooks, entry paths, cast, and social lanes are individually
  readable and visually coherent.
- Failure: nine content bands share enough visual weight that the page reads as
  a complete inventory rather than a directed front door.
- Mobile impact: the same inventory becomes a very long single column; the
  entry decision and supporting trust signals are separated by substantial
  scrolling.
- Applicant impact: useful information is present, but the page asks the user
  to evaluate every object class before it resolves the best first action.

### 2. Signed-In Community Home

General health: overloaded by additive audience state.

- Failure: `Director controls` and `Continue writing` are inserted above the
  full public inventory instead of replacing or demoting irrelevant visitor
  sections.
- Failure: three director actions interrupt the emotional transition from
  realm promise to current story pressure.
- Writer impact: the correct continuation is visible, but not dominant enough
  to turn community entry into a reliable next-writing loop.
- Director impact: object-local editing is useful, but a single `Edit realm
  home` command would preserve access without rendering an admin panel in the
  story path.

### 3. Writer Desk

General health: mobile hierarchy is promising; desktop composition is broken.

- Strength: mobile correctly leads with `What needs you`, Maris Vale, and one
  `needs reply` scene.
- P1 failure: the desktop command area visibly collides: heading, explanatory
  copy, action surface, and count occupy overlapping or disconnected regions,
  followed by a large dead zone.
- Failure: `What needs you`, `Face lanes`, `Work lanes`, and `Needs reply`
  repeat the same obligation through four hierarchy levels for a one-item
  queue.
- Accessibility risk: overlapping visible text is a perceivability failure;
  keyboard order, focus indication, and assistive-technology announcements
  still require direct verification.

### 4. Studio Home

General health: clear labels, wrong product shape.

- Strength: the seven Studio rooms use PBP/director language and remain easy to
  recognize.
- Failure: the page says it is a director-attention surface but renders a
  permanent destination directory. Zero-state and active rooms receive nearly
  identical elevation, size, color, and action treatment.
- Failure: `Public discovery profile` appears once under Director attention and
  again under Studio rooms with overlapping content.
- Director impact: the page requires scanning the product topology before
  finding actual work.

### 5. Studio Content And Operations

General health: implementation and diagnostic structure dominates the user
job.

- Studio Content failure: guidebook, world map, current pressure, applications,
  and claims appear first as destination cards and then again as director-queue
  or coverage cards.
- Studio Operations contradiction: the page says no director operations need
  attention, then devotes most of the page to queue parity contracts and
  runtime/persistence diagnostics.
- Staff impact: contract and diagnostic proof is valuable, but belongs in a
  dedicated health/diagnostics surface rather than the daily work path.
- Accessibility risk: dense repeated card headings and link labels increase
  navigation cost; heading semantics and tab-stop count need browser/AT proof.

### 6. Shoreline Club Location

General health: strong story identity, interrupted play path.

- Strength: the hero, place logline, `Start scene here`, local play pressure,
  nearby places, filters, and scene card make the location understandable.
- Failure: an elevated director-controls block sits directly between the place
  hero and `What is playable here`; on mobile it occupies a large portion of
  the first interaction path.
- Failure: top-level `Manage place` plus the full director block duplicate the
  editing entry point.
- Writer impact: staff power is visually foregrounded even when the immediate
  job is reading, joining, or continuing a scene.

## Synthetic Panel Signals

- Panelist: Active Scene Writer
  - Flow: community entry and Writer Desk
  - Severity: P1
  - User Job: find the next owed reply as the correct face
  - Evidence: signed-in community home appends continuation to the full public
    inventory; desktop Desk command composition overlaps
  - User Impact: continuation exists but does not provide a calm, reliable
    return-to-writing loop
  - Expected Experience: active face and next scene dominate; exploration is
    secondary
  - Recommended Change: make continuation replace visitor entry content and
    collapse the Desk to one command plus only active lanes
  - Required Proof: rendered tests, desktop/mobile screenshots, keyboard and
    focus review
  - Collateral: Writer Desk and information-hierarchy docs
  - Confidence: medium

- Panelist: Invited/New Face Applicant
  - Flow: public community orientation
  - Severity: P2
  - User Job: judge fit and find a first-face path
  - Evidence: useful fit and entry information is distributed across a
    nine-band home
  - User Impact: high reading burden before commitment; likely abandonment or
    off-platform questions
  - Expected Experience: premise, current pressure, trust/fit, and one adaptive
    entry action within the first viewport
  - Recommended Change: keep one realm promise, one current pressure, and one
    curated ways-in group; move complete collections to scoped pages
  - Required Proof: first-five-second test and real applicant UAT
  - Collateral: community-home component and public-preview tests
  - Confidence: medium

- Panelist: Community Director
  - Flow: Studio home, Content, Operations, object-local controls
  - Severity: P2
  - User Job: find the next director decision without losing deep control
  - Evidence: equal-weight room cards, duplicated content taxonomy, and
    diagnostics after an operations-clear state
  - User Impact: deep control feels like permanent cognitive load
  - Expected Experience: active work first; permanent rooms in navigation and
    search; object-local editing through one command
  - Recommended Change: make Studio action-only, deduplicate Content, move
    diagnostics, and reduce object controls to one disclosure entry
  - Required Proof: queue-state tests, empty-state screenshots, navigation and
    capability proof
  - Collateral: Studio docs, rendered privacy matrix, changelog
  - Confidence: medium

- Panelist: Staff Moderator And Safety-Boundary Writer
  - Flow: director and staff controls on story surfaces
  - Severity: P2
  - User Job: reach capability-gated tools without making ordinary writers feel
    watched or exposing private state
  - Evidence: role-only controls visibly dominate member home and location
    composition
  - User Impact: blurred emotional boundary between play and moderation/admin
  - Expected Experience: one capability-gated edit disclosure outside the main
    story reading order
  - Recommended Change: preserve permission checks and move controls behind one
    clearly labeled action or disclosure
  - Required Proof: public/member/director rendered variants and DOM privacy
    assertions
  - Collateral: rendered-route privacy matrix if visible state changes
  - Confidence: medium

## Recommended Changes

- P1: repair the Writer Desk desktop command composition and remove repeated
  one-item hierarchy.
- P2: enforce audience replacement on community home instead of additive
  visitor/member/director sections.
- P2: make Studio home an active-work surface; keep the room directory in
  persistent navigation and future Studio search.
- P2: remove the duplicate first-pass inventory from Studio Content and keep
  one director queue/current-production sequence.
- P2: move parity/runtime diagnostics out of ordinary Operations.
- P2: collapse public-page director controls to one capability-gated edit
  disclosure.
- P3: tighten label repetition, borders, and elevated surfaces after the
  structural changes land.

## Required Proof

- Rendered tests: audience-specific community-home sections, Studio empty and
  active states, director-control visibility, Desk command ordering.
- Service tests: ranking and section membership remain service-owned and
  tenant-aware.
- Browser QA: all five surfaces at desktop and mobile, including dense and
  empty states.
- Copy check: no route-directory, parity-contract, implementation, or setup
  language in ordinary story and daily-work paths.
- Accessibility check: heading order, keyboard path, focus visibility, target
  size, zoom/reflow, and screen-reader naming for disclosure controls.
- Real UAT: applicant five-second comprehension, writer next-reply task, and
  director next-obligation task.

## Decisions

- Accepted: hierarchy and progressive disclosure are the next product-design
  priority; page-by-page polish alone will not resolve the current experience.
- Accepted: community home, Desk, Studio home, Studio Content, and location
  controls form one cross-surface contract and should move together.
- Accepted: keep the existing Elbysodic design language and vary structure,
  interaction, hierarchy, and emphasis before changing brand style.
- Proposed: a community home with one story promise, one continuation/current
  pressure, one curated mixed ways-in group, and quiet links to full rooms.
- Proposed: a Studio home that renders only active attention and true empty
  state, with rooms remaining in sidebar navigation.
- Deferred: Studio-wide control search until the action-only home and scoped
  room contracts are stable.
- Rejected: adding new schema, homepage modules, metrics, or theme controls as
  a response to overwhelm.
- Not-now: broad redesign of every Elbysodic route before the five named
  representative surfaces prove the system.
