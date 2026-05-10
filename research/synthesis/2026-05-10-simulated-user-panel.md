# Simulated User Panel Synthesis

Status: synthetic panel synthesis
Last updated: 2026-05-10
Sources: simulated Codex subagents seeded from `docs/product/user-personas-panel.md`, `research/synthesis/2026-wave-2-modern-pbp-delta.md`, `research/interviews/protocols/elbysodic-concept-brief.md`, and founder direction in this thread
Confidence: medium

This is not real interview evidence. It is a seeded/emulated panel intended to
stress-test Elbysodic's product direction, expose tensions between roleplayer
segments, and produce reusable user lenses for roadmap and UX review.

## Panel Composition

- Active Scene Writer: daily long-form writer managing replies, drafts, faces,
  unread state, and continuity.
- Invited/New Face Applicant: newcomer judging whether the realm is worth
  joining and trying to apply without exposing private work.
- Hook Hunter and Reddit 1x1 Seeker: partner-search user who needs compatible
  wanted hooks and low-friction interest before committing to a face.
- Community Director: founder/admin/operator responsible for launch, intake,
  claims, reserves, guidebooks, events, wanted hooks, and board health.
- Staff Moderator and Safety-Boundary Writer: staff/user blend focused on
  privacy, audience boundaries, staff scope, reports, and side channels.
- Discord Migrant and Rapid-Touch Writer: modern RP user accustomed to pings,
  proxying, fast OOC coordination, and chat-like affordances.
- Dedicated Platform Regular and Modern Design Skeptic: user shaped by RPR,
  RPoL, RPHub-style expectations around persistent profiles, private spaces,
  public polish, archives, events, and portability.

## Convergent Signals

### Active Face Safety Is P0

Every writing or coordination lens treated wrong-face prevention as a trust
breaker. The product should show the active face at every authoring and commit
boundary: `Reply as <face>`, `Join as <face>`, `Raise hand as <face>`, and
future quick-touch equivalents.

Product implication:

- Accepted: authoring actions must use character for public authorship and
  membership for ownership/permission.
- Accepted: composer, scene reply, wanted interest, plotting, and future rapid
  touchpoints need visible face confirmation.
- Required proof: service tests for membership/character separation and
  rendered/browser checks for active-face affordances on desktop and mobile.

### Privacy Must Hold Across Summary Surfaces

The safety panel, applicant, director, and platform-regular lenses all warned
that privacy failures often appear outside the detail page: counts,
notifications, sidebars, mobile drawers, denial pages, search, recovery links,
queue names, and public movement states.

Product implication:

- Accepted: application notes need separate `staff-only`,
  `applicant-visible`, and `public status` surfaces.
- Accepted: private plotting/backstage links and staff context must not leak
  through metadata.
- Proposed: maintain a rendered privacy matrix for public, member, participant,
  applicant, face owner, staff, director, outsider, and same-user-different-
  community viewers.

### The Daily Writer Loop Is The Backbone

The writer and Discord-migrant panels converged on the same loop: active face,
Writer Desk, scene reader, composer/preview, post, next obligation. If this
loop is not excellent, stronger director tooling will not compensate.

Product implication:

- Accepted: `needs reply`, `waiting`, `caught up`, `watching`, unread, latest
  beat, active cast, and linked context are core writing infrastructure.
- Accepted: Studio surfaces should not dominate ordinary writer surfaces.
- Proposed: scene pages should foreground cast, state, latest beat, unread,
  current face, and reply affordance before administrative metadata.

### Public Trust And Design Quality Are Product Requirements

The new applicant and platform-regular lenses treated public polish as a trust
screen, not decoration. A realm must look active, modern, PBP-native, and safe
before people invest in a face or application.

Product implication:

- Accepted: public preview should show premise, tone, current activity, roster
  shape, app/recruitment state, content posture, and safe recent movement.
- Accepted: defaults must be good enough to launch without custom skins.
- Proposed: launch readiness should include appearance health, mobile
  readability, and public preview quality checks.

### Wanted Hooks Need A Complete Handoff

The hook hunter, applicant, writer, director, and safety lenses all converged on
wanted hooks as a major bridge from discovery to play. The failure mode is an
ad that never becomes a scene, or a private negotiation that moves to Discord
and leaves Elbysodic behind.

Product implication:

- Accepted: wanted hooks should be structured story-intent objects, not only
  ads or forum posts.
- Proposed: support lifecycle states such as `open`, `raised hand`, `checking
  fit`, `in plotting`, `reserved`, `ready for scene`, `scene started`,
  `filled`, `paused`, `passed`, and `archived`.
- Proposed: include compatibility fields where useful: cadence, post style,
  boundaries, OOC preference, time zone/free windows, commitment level, and
  sample/recent post.

### Studio Should Be A Production Room

The director panel was clear that an admin console is not enough. Directors
need the product to surface board-running jobs by urgency and story consequence.

Product implication:

- Accepted: launch readiness, applications, claims, reserves, wanted hooks,
  plotting handoffs, events/current activity, guidebooks, roster health,
  appearance, privacy, and export posture are director production work.
- Proposed: Studio home should group work by production lane: review apps,
  resolve casting, handle expiring reserves, unblock wanted handoffs, check
  stale scenes, update public activity, and maintain realm materials.

### Rapid Touchpoints Should Wait, But The Model Should Not

The Discord-migrant lens wanted pings, fast proxying, OOC coordination, and
quick IC exchanges acknowledged. The safety and director lenses warned against
shipping generic chat before the canonical model is proven.

Product implication:

- Accepted: Elbysodic should not chase Discord parity in the MVP.
- Deferred: live chat, broad presence, Discord import, autoproxy-like quick
  chat, AI summaries, and external notification bridges.
- Proposed now: define future rapid-touch object semantics: audience, canon
  status, participants, face identity, archive behavior, provenance, and source
  of truth.

### Portability Is A Trust Feature

Directors and dedicated-platform users both treated archive/export posture as a
precondition for moving real communities. The first version can be modest, but
the promise should be visible early.

Product implication:

- Proposed: add export posture to launch readiness and director trust copy.
- Proposed: define export inventory for scenes, roster, faces, guidebooks,
  claims/reserves, wanted hooks, and privacy handling for staff/private data.

## Tensions And Minority Reports

- Discord migrants need the product to acknowledge pings, quick beats, and OOC
  coordination. The stronger consensus is to model those later around the
  canonical record instead of making chat the MVP center.
- Hook hunters want compatibility metadata. The risk is turning wanted hooks
  into sterile partner-search forms. Elbysodic should collect only fields that
  reduce mismatch and handoff friction.
- Dedicated-platform users expect events and public activity objects. Current
  non-AI roadmap can satisfy this partially through current activity and wanted
  handoffs, but first-class events may deserve an earlier design spike.
- Directors want export/backup trust before large data migration. The early
  version can be a visible export contract and inventory before full fidelity
  tooling exists.
- Appearance matters culturally, but raw customization remains misaligned.
  Elbysodic should offer strong art-direction knobs inside product-owned
  layout, typography, privacy, and accessibility constraints.

## Ranked Backlog Signal

### P0

- Active face confirmation on every authoring commit.
- Membership-scoped permissions and community-visible staff anchoring on staff
  surfaces.
- Application privacy split: staff-only notes, applicant-visible requests, and
  public status.
- Notification, count, search, sidebar, mobile drawer, denial, and recovery
  side-channel privacy tests.

### P1

- Writer Desk obligation queue: `needs reply`, `waiting`, `caught up`,
  `watching`, unread, mentions, and latest beat.
- Public realm preview as trust screen, with modern visual quality and
  PBP-native vocabulary.
- First-face onboarding that distinguishes account, membership, face,
  application, claim, and reserve.
- Wanted lifecycle from public hook to prospective interest to plotting to
  scene start.
- Studio launch checklist and operations home organized by production jobs.
- Archive/export posture visible to directors.
- Face hubs as durable public posting-identity surfaces.

### P2

- Compatibility fields and graceful pass/pause/closed states for wanted hooks.
- Events/current activity as continuity and discovery objects.
- Appearance variants, media slots, and health warnings across public preview,
  postbit, face hub, wanted hook, and mobile.
- Object-bound plotting/backstage before broad chat.
- Moderation provenance fields for canonical object, external reference,
  audience, staff-only rationale, and writer-facing aftermath.
- Future rapid-touch state model.

## Reusable Panel Prompts

Use these as reusable seeds when evaluating a feature, page, or roadmap slice.

```text
You are the Active Scene Writer for Elbysodic. Evaluate this flow only through
daily writing needs: active face clarity, reply obligation, unread state,
continuity, drafts, preview, scene context, and whether the product keeps you in
the story instead of an admin surface. Return P0/P1/P2 findings.
```

```text
You are the Invited/New Face Applicant for Elbysodic. Evaluate whether a new
writer can understand the realm, trust the public surface, apply privately,
distinguish account/membership/face/application/claim/reserve, and reach a
first writing move. Return P0/P1/P2 findings.
```

```text
You are the Hook Hunter and Reddit 1x1 Seeker for Elbysodic. Evaluate wanted
hooks, compatibility, interest, plotting handoff, ghosting/mismatch handling,
and whether Elbysodic becomes the source of truth instead of Discord/DMs.
Return P0/P1/P2 findings.
```

```text
You are the Community Director for Elbysodic. Evaluate board-running work:
launch readiness, applications, claims, reserves, rosters, wanted lifecycle,
guidebooks, events, appearance, privacy, export, and what needs director action.
Return P0/P1/P2 findings.
```

```text
You are the Staff Moderator and Safety-Boundary Writer for Elbysodic. Evaluate
community-scoped staff power, audience labels, privacy side channels, staff-only
notes, reports, moderation provenance, and wrong-face risks. Return P0/P1/P2
findings.
```

```text
You are the Discord Migrant and Rapid-Touch Writer for Elbysodic. Evaluate
whether the product respects modern proxying, pings, OOC coordination, and quick
IC touchpoints while keeping the durable forum backbone as source of truth.
Return P0/P1/P2 findings.
```

```text
You are the Dedicated Platform Regular and Modern Design Skeptic for Elbysodic.
Evaluate whether the product looks active, modern, private, portable, and
roleplay-native compared with dedicated RP platforms. Return P0/P1/P2 findings.
```

## Product Implications

- Accepted: use this panel as a recurring simulated review panel for UX,
  roadmap, and implementation critique.
- Proposed: create an agentic skill or scoped panel file later if the panel
  format proves useful across several reviews.
- Deferred: treat these synthetic findings as validated user evidence only
  after real interviews, usability tests, or live alpha observation.
- Rejected: do not present simulated responses as outreach, interviews, or
  direct community evidence.

## Promotion Target

- `docs/product/user-personas-panel.md`: keep the durable panel lineup, JTBD,
  journeys, and evaluation prompts there once stable.
- `plans/in-progress/non-ai-pbp-studio-roadmap-2026-05-10.md`: use accepted
  signals to tune phase ordering and proof requirements.
- `research/interviews/`: use the tensions above as prompts for real discovery
  interviews and alpha usability tasks.
