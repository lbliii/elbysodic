# Simulated UAT Session: First-Face Onboarding

Status: simulated UAT
Date: 2026-05-10
Researcher: Codex
Artifact inspected: product docs and roadmap; rerun required against rendered
route or screenshot
Artifact path or URL: `docs/product/user-personas-panel.md`,
`plans/in-progress/non-ai-pbp-studio-roadmap-2026-05-10.md`,
`research/uat/protocols/first-face-onboarding.md`
Synthetic user: Invited/New Face Applicant plus Staff/Safety lens
Seed docs: `research/synthesis/2026-05-10-simulated-user-panel.md`
Confidence: medium

This is simulated task testing. It can expose likely friction, but it does not
replace observed user behavior.

## Task

Create or apply with a first face, understand what is public or private, and
find the next writing move after acceptance.

## Success Criteria

- User can distinguish account, membership, face, application, claim, and
  reserve.
- User can tell what staff sees, what other members see, and what remains
  private.
- User can identify required fields and optional character material.
- User can understand application state after submit.
- Accepted user reaches a character hub, wanted hook, plotting room, or first
  scene path.

## Starting State

- User role: invited writer.
- Community/membership state: accepted invite, membership exists.
- Face/application state: no face yet.
- Device or viewport: mobile should support draft and submit.
- Privacy/audience state: applicant-visible plus staff review.

## Expected Path

1. Accept invite or enter realm as no-face member.
2. See first-face path and explain identity layers.
3. Start application or face draft.
4. Resolve claim/reserve requirements.
5. Submit application and see persistent status.
6. Receive revision/acceptance state.
7. Land on next writing move after acceptance.

## Simulated Task Path

1. User tries to understand whether they are creating an account profile,
   membership identity, or playable face.
2. User looks for claim/reserve availability before investing in application
   prose.
3. User submits or imagines submitting and checks what state persists.
4. User asks who can see draft material, staff notes, and revision requests.
5. User expects acceptance to lead to a default face, character hub, wanted
   handoff, plotting room, or first scene.

## Failure Points

- If account, membership, and face are collapsed in copy, the user cannot trust
  pseudonymity or community-local identity.
- If application state exists only as a toast, the applicant has no durable
  status.
- If claims/reserves availability is unclear before writing, effort feels
  risky.
- If staff-only notes and applicant-visible requests are not distinct, privacy
  trust breaks.
- If acceptance does not hand off to writing, the flow solves administration
  but not play.

## Trust Breaks

- Wrong-face risk: medium at acceptance and default-face setup.
- Privacy/audience risk: high around application drafts, staff notes, revision
  requests, claim conflicts, and decline/withdraw states.
- Source-of-truth risk: medium if staff review or plotting moves to Discord.
- Data-loss/draft risk: high for long application prose.
- Design credibility risk: medium; onboarding must feel PBP-native, not generic
  account setup.

## Vocabulary Breaks

- Avoid `profile setup`, `workspace membership`, `content submission`, and
  `admin review`.
- Prefer `face`, `membership`, `application`, `claims`, `reserves`, `staff
  review`, `revision request`, `accepted face`, and `first scene`.

## Recommended Changes

- P0: Application privacy split must distinguish staff-only notes,
  applicant-visible revision requests, applicant-authored draft, and public
  status.
- P0: Ownership and permission must stay membership-scoped; public authorship
  must stay face-scoped.
- P1: First-face path should explain account, membership, face, application,
  claim, and reserve in product language.
- P1: Application status should persist: draft, submitted, needs revision,
  accepted, declined, withdrawn.
- P1: Acceptance should immediately set or confirm default face and offer a
  first writing move.
- P2: Claim/reserve conflict and expiry should be visible before commitment.

## Required Proof

- Rendered test: applicant, no-face member, accepted face owner, ordinary
  member, staff, director, outsider, and same-user-different-community states.
- Service test: membership ownership, character authorship, application state,
  staff-only/applicant-visible note separation.
- Browser QA: mobile drafting, status persistence, acceptance handoff.
- Copy check: identity-layer vocabulary.
- Accessibility check: form labels, errors, focus, long-form text entry.
- Real UAT: new applicant task against prototype or route.
- No collateral:

## Decisions

- Accepted: first-face onboarding is one of the highest-risk alpha flows.
- Accepted: privacy and identity comprehension must be designed into the UI,
  not only enforced by service code.
- Proposed: add a dedicated UAT gate before invitation lifecycle is considered
  alpha-ready.
- Deferred: real task testing until a rendered first-face artifact exists.
- Rejected: treating first-face setup as generic profile creation.
