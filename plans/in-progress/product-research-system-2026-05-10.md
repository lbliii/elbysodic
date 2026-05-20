# Product Research And UXR System

Status: active methodology plan
Owner: Product, research, UX, planning, and test stewardship
Created: 2026-05-10
Last updated: 2026-05-10
Review by: 2026-06-07
Closure criteria: The research folder has reusable templates for source notes,
competitive audits, synthetic panel runs, real interview notes, UAT sessions,
and synthesis promotion; at least three product flows have been evaluated
through the system; accepted findings are reflected in product docs, plans, or
test proof without confusing simulated signal for real evidence.

## Purpose

Elbysodic needs a repeatable product research and user research system that can
do four jobs well:

- gather broad roleplay-market signal without flattening cultures into one
  generic user
- simulate user-panel critique quickly while product artifacts are still cheap
  to change
- run real UXR and UAT when prototypes, alpha flows, or candidate users are
  available
- promote only the right findings into product doctrine, roadmap, tests, and
  agent/steward operating rules

The system should let us move quickly without lying to ourselves about
evidence quality. Synthetic panel output is useful pressure-testing, not field
truth.

## Operating Model

```text
public source or product artifact
  -> source note / audit
  -> research synthesis
  -> synthetic panel critique
  -> product hypothesis
  -> prototype or implemented flow
  -> simulated UAT
  -> real interview, usability test, or alpha observation
  -> accepted doctrine, roadmap item, test, or not-now decision
```

Not every question needs every step. Use the lightest path that can answer the
decision safely.

## Evidence Ladder

Use these labels consistently:

- `source signal`: public sources, product audits, market observations, real
  community artifacts, or direct quotes.
- `research inference`: what Elbysodic thinks the source signal means.
- `synthetic panel`: simulated user critique seeded from research and product
  constraints.
- `simulated UAT`: task-based critique by synthetic users against a concrete
  artifact, route, screenshot, or prototype.
- `real UXR`: interviews, moderated usability tests, unmoderated tasks,
  support conversations, alpha observation, or analytics.
- `product doctrine`: accepted Elbysodic stance after filtering signal through
  mission, tenant/identity constraints, privacy standards, and product taste.

Confidence rules:

- `high`: repeated source signal plus real UXR or live alpha behavior.
- `medium`: repeated source signal plus synthetic panel convergence, or a
  strong real-user finding that still needs broader validation.
- `low`: plausible single-source or synthetic-only signal.
- `conflict`: credible cultures, users, or product constraints disagree.

Promotion rule:

- Synthetic-only findings can shape hypotheses, prompts, PR review questions,
  and not-now lists.
- Synthetic-only findings should not become irreversible product doctrine
  without either human product acceptance or real UXR.

## Research Repository Shape

Keep the current `research/` structure and add only what earns its keep.

Near-term structure:

```text
research/
  sources/
    roleplay-ecosystem/
    platform-audits/
    blogs-and-thinkers/
  synthesis/
  interviews/
    protocols/
    notes/
    synthesis/
  outreach/
  uat/
    protocols/
    simulated/
    observed/
```

Rules:

- `sources/` holds source notes and competitive audits.
- `synthesis/` holds cross-source judgment and confidence.
- `interviews/` holds consent-safe real-user research.
- `outreach/` holds candidate leads, templates, and contact status.
- `uat/` holds task-based product evaluations, both simulated and observed.

Do not add raw scrape dumps, private contact details, Discord handles, DMs,
recordings, or sensitive interview material without explicit permission.

## Template Library

### Source Note

Purpose: capture one public article, blog, community artifact, product page, or
thread as traceable signal.

Required fields:

- title/name
- URL or source path
- accessed date
- source type
- relevant segment
- source signal
- researcher inference
- product implication: accepted/proposed/deferred/rejected
- confidence
- follow-up questions

### Competitive Audit

Purpose: inspect products such as RPHub, RPR, RPoL, Jcink forums, Discord RP
servers, Tumblr RP patterns, or Reddit partner-search flows.

Required fields:

- product/community
- accessed date
- target user
- core flows audited
- what works
- where it fails PBP-native needs
- what Elbysodic should learn
- what Elbysodic should reject
- screenshots or links when safe
- confidence

### Synthetic Panel Run

Purpose: preserve simulated user critique without pretending it is real UXR.

Required fields:

- artifact evaluated
- panelists used
- seed docs
- task prompt
- findings by panelist
- convergence
- tensions/minority reports
- accepted/deferred/rejected/not-now findings
- proof needed
- confidence

### Simulated UAT Session

Purpose: run synthetic task testing against a concrete flow.

Required fields:

- flow/task
- artifact inspected: route, screenshot, copy, prototype, plan, or code
- synthetic user
- success criteria
- task path
- failure points
- trust breaks
- vocabulary breaks
- privacy/identity risks
- recommended changes
- required proof
- confidence

### Real Interview Note

Purpose: capture consent-safe learning from a real participant.

Required fields:

- participant label, not private handle
- consent level: private, unattributed, attributed, or publishable
- segment/lens
- date
- protocol used
- high-signal quotes or paraphrases
- observed behavior
- jobs to be done
- pain points
- product reactions
- contradictions
- follow-up permission
- promotion candidates

### Real UAT Observation

Purpose: record a real user's task attempt against Elbysodic.

Required fields:

- participant label and consent level
- task
- start state
- expected success path
- actual path
- confusion points
- hesitation or abandonment points
- privacy/trust concerns
- time to first meaningful action
- user language
- severity
- recommended product change
- required proof

## Synthetic Panel System

Keep the current panel in `docs/product/user-personas-panel.md` as the canonical
persona guide. Use `research/synthesis/2026-05-10-simulated-user-panel.md` as
the first synthesis run.

Core panel:

- Active Scene Writer
- Invited/New Face Applicant
- Hook Hunter and Reddit 1x1 Seeker
- Community Director
- Staff Moderator and Safety-Boundary Writer
- Discord Migrant and Rapid-Touch Writer
- Dedicated Platform Regular and Modern Design Skeptic

Add adversarial lenses when needed:

- Discord Loyalist: wants RP to stay in servers and sees forums as dead weight.
- Old-School Skinner: values high-control forum aesthetics and may distrust
  product-owned constraints.
- Low-Commitment 1x1 Drifter: wants fast matching, low ceremony, and clean
  exits.
- Private Friend-Group Operator: wants no marketplace or public discovery.
- Accessibility-First Writer: rejects visual novelty that harms readability,
  focus, or screen-reader semantics.
- Alpha Breaker: looks for ways onboarding, privacy, empty states, and mobile
  can fail.

Panel rule:

- Broad roadmap or whole-flow review: use all core panelists plus one or two
  adversarial lenses.
- Focused UX review: use two to four panelists directly affected by the flow.
- Privacy, face, staff, or application flows: always include Staff/Safety.
- Rapid-touch, Discord, AI, import, or chatbox flows: always include
  Discord/Rapid-Touch and Staff/Safety.
- Public discovery and appearance flows: always include Applicant and Modern
  Design Skeptic.

## UXR And UAT Cadence

Weekly research loop:

- 1 public-source note or competitive audit.
- 1 synthetic panel or simulated UAT run against an active flow.
- 1 synthesis update or product-doc promotion decision.

Per product slice:

- Before implementation: run synthetic panel against the planned flow.
- During implementation: use panel findings as UX acceptance questions.
- Before merge or alpha demo: run simulated UAT against screenshots/routes.
- After alpha exposure: replace or qualify synthetic assumptions with real UXR.

Monthly review:

- Identify repeated synthetic findings that real users have validated.
- Promote stable findings to `docs/product/`, `plans/`, tests, or `AGENTS.md`.
- Prune noisy panel prompts.
- Mark unvalidated assumptions that still carry product risk.

## Product Flow Coverage

Use the system first on these high-risk flows:

1. Public realm preview and request/invite posture.
2. First-face onboarding: account, membership, face, application, claim, and
   reserve.
3. Writer Desk to scene reply loop.
4. Wanted hook to prospective interest to plotting room to scene.
5. Application review with staff-only and applicant-visible notes.
6. Studio launch checklist and operations home.
7. Public catalog/network cards and signed-out privacy.
8. Appearance defaults and mobile public trust.
9. Export/backup posture.
10. Future rapid-touch object model.

## Decision And Promotion Rules

Every synthesis should produce one of these outcomes:

- `accepted`: product direction changes now; update docs/plans/tests as needed.
- `proposed`: promising but needs more evidence or implementation scoping.
- `deferred`: likely valid, but sequence later.
- `rejected`: conflicts with Elbysodic standards or weak evidence.
- `not-now`: strategically plausible but outside the current backbone.

Promotion targets:

- `docs/product/`: accepted product language, UX doctrine, or product standard.
- `docs/architecture/`: accepted tenant, identity, security, or privacy rule.
- `plans/`: sequenced implementation work or roadmap dependency.
- `tests/`: regression proof for accepted trust, privacy, identity, or journey
  findings.
- `AGENTS.md`: durable agent/steward behavior that should affect future work.

## Guardrails

- Do not present simulated panel responses as real people, outreach, or
  community evidence.
- Do not quote private users, private servers, or private interview material
  without consent.
- Do not copy competitor taxonomy, moderation posture, or community rules as
  doctrine.
- Do not let research become a feature grab bag. Convert signal into user jobs,
  risks, and product bets.
- Do not overfit to founder nostalgia; explicitly mark where post-2014
  behavior changed the expected product.
- Do not add heavy process until the artifact has been used at least twice.

## Immediate Work Plan

### Phase 0: Plain-Language Skill

Status: implemented locally 2026-05-10.

Deliverables:

- Added `.agents/skills/elbysodic-product-research/SKILL.md` as a thin
  orchestration skill for source notes, competitive audits, synthetic panels,
  simulated UAT, real UXR, observed UAT, synthesis, and promotion.
- Added `agents/openai.yaml` metadata for the skill.
- Kept the skill as a router to repo docs/templates/protocols instead of
  duplicating the research system.

Proof:

- Markdown hygiene check.
- Skill references existing repo paths.

### Phase 1: Templates And Indexes

Status: implemented locally 2026-05-10.

Deliverables:

- Added templates for source notes, competitive audits, synthetic panel runs,
  simulated UAT sessions, interview notes, and real UAT observations.
- Added `research/uat/` README and subdirectory guides for protocols,
  simulated sessions, and observed sessions.
- Added reusable UAT protocols for public realm preview, first-face onboarding,
  and wanted-hook-to-plotting handoff.
- Updated `research/README.md` and `research/AGENTS.md` with the evidence
  ladder, UAT scope, and synthetic-vs-real guardrails.

Proof:

- Markdown hygiene check.
- Directory map matches committed files.

### Phase 2: First Three Simulated UAT Runs

Status: seeded locally 2026-05-10 against product docs and roadmap; rerun each
against rendered routes or screenshots before treating findings as route-level
evidence.

Run simulated UAT against:

- `research/uat/simulated/2026-05-10-public-realm-preview-simulated-uat.md`
- `research/uat/simulated/2026-05-10-first-face-onboarding-simulated-uat.md`
- `research/uat/simulated/2026-05-10-wanted-to-plotting-simulated-uat.md`

Each run should name task, artifact, synthetic users, failure points,
accepted/deferred findings, and proof needed.

Proof:

- Three notes under `research/uat/simulated/`.
- Accepted findings linked into active plans or product docs.

2026-05-19 follow-up:

- Added
  `research/uat/simulated/2026-05-19-community-landing-first-face-simulated-uat.md`
  against the current rendered-route contracts for community landing,
  account-visitor posture, scoped search, and accepted first-face handoff.
- Accepted findings promoted into the active implementation queue: signed-in
  non-members must render as account visitors rather than logged-out users,
  scoped search may use realm initials only when the full realm name remains
  available to assistive tech, members keep public story orientation on the
  realm home, and accepted applications need a service-owned next writing move.
- 2026-05-20 implementation follow-up closed the remaining local notification
  count privacy gap for inactive/faceless identity modes and added public
  Network card request-access actions. Live production smoke and real PBP
  writer UAT remain deferred.
- Deferred findings remain synthetic until browser QA and real PBP writer UAT
  run against a reachable production or staging URL.

### Phase 3: Real UXR Readiness

Deliverables:

- Tighten recruiting criteria by segment.
- Prepare consent-safe interview note template.
- Prepare moderated task scripts for the same three flows.
- Decide what is safe to show: concept brief, screenshots, local demo, or repo.

Proof:

- Updated `research/interviews/` and `research/outreach/` docs.
- No private contact details committed.

### Phase 4: Product Doctrine Review

After at least three synthetic runs and one real-user signal batch, review:

- which panel findings held up
- which were overfit or noisy
- which product docs need doctrine updates
- which plans need reprioritization
- which tests should encode trust failures

Proof:

- Synthesis note in `research/synthesis/`.
- Product docs/plans updated or explicitly unchanged.

## Not Now

- Building a full custom agentic skill before the panel has been reused across
  several concrete artifacts.
- Broad analytics instrumentation before alpha flows exist.
- Public surveys as the primary research method; this product needs task and
  culture nuance more than preference polling.
- Real outreach without a consent-safe protocol and clear artifact to show.
