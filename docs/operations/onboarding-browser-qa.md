# Onboarding Browser QA

Use this checklist when a PR touches auth entry, public preview, request
access, invite acceptance, first-face work, applicant state, director launch, or
first writing move handoffs. Rendered tests prove behavior; this pass catches
viewport, focus, overflow, copy, and state-language regressions.

## Required Viewports

- Desktop: 1440 x 1200.
- Tablet: 900 x 1100.
- Mobile: 390 x 844.

## Required States

- Signed-out visitor on `/network` and `/c/afterlight-accord`.
- Signed-in account visitor on `/c/afterlight-accord`.
- Request-access form and confirmation posture.
- Valid invitation acceptance into a faceless member state.
- Faceless member on Desk and first-face application start.
- Applicant with draft or accepted application room.
- Member with accepted active face on Desk, wanted, plotting, and first-scene
  paths.
- Director on Studio Launch, access requests, invitation management, and Studio
  Operations.
- Inactive or cross-community recovery state when the changed surface can
  expose membership-local data.

## Community Landing Profile

Start an isolated seeded development server:

```bash
ELBYSODIC_ENV=development uv run elbysodic \
  --db-path /private/tmp/elbysodic-onboarding-qa.sqlite3 \
  --port 8007 \
  --seed-demo \
  serve
```

Run the existing public-preview and first-face surface profile:

```bash
ELBYSODIC_ENV=development uv run python scripts/browser_qa.py \
  --base-url http://127.0.0.1:8007 \
  --profile community-landing \
  --artifact-dir /private/tmp/elbysodic-onboarding-community-landing-qa
```

## Writer Activation Script

Run the invite-to-first-face smoke path against the same seeded server:

```bash
ELBYSODIC_ENV=development uv run python scripts/writer_activation_qa.py \
  --base-url http://127.0.0.1:8007
```

The script creates a copy-only invitation, accepts it as a new writer, verifies
faceless continuation, creates a first-face draft, and checks wanted/plotting
entry for an accepted writer.

## Manual Inspection

For each screenshot set or browser pass, record:

- base URL, database path, command, date, and artifact directory
- route and seed persona or login state
- first viewport identity signal and primary action
- whether public/account visitors see only public-safe realm, wanted,
  guidebook, request-access, and application posture
- whether faceless members and applicants can find first-face work without
  seeing other writers' applications, staff notes, private queues, active-face
  controls, or staff controls
- whether director-only launch blockers, access-request notes, invite links,
  and review state remain private
- keyboard focus order through login, request access, application, invite,
  and Studio queue controls where present
- text overlap, clipped buttons, horizontal scroll, console errors, missing
  media, or awkward mobile truncation

## Pass Criteria

- Public and account visitor states do not render Desk, active face, unread
  counts, staff controls, private notes, invite links, application review state,
  plotting rooms, or reserves.
- Applicants and faceless members see a next action toward first-face work.
- Directors can find launch blockers and request/invite work without exposing
  that state to ordinary members or visitors.
- Auth and recovery copy distinguishes account, membership, face, application,
  claims, reserves, wanted, plotting, scene, and thread state.
- Screenshots or artifact paths are recorded in the PR, release note, or
  operations note.

## Current Status

Passed locally on June 3, 2026 against an isolated seeded development server on
`http://127.0.0.1:8007` with database
`/private/tmp/elbysodic-onboarding-qa.sqlite3`.

- Community landing profile passed. Screenshot artifacts:
  `/private/tmp/elbysodic-onboarding-community-landing-qa-2026-06-03`.
- Writer activation QA passed after refreshing the script to wait for the
  current first-face action label, `Create draft face`.

Passed locally on June 13, 2026 for the no-face and accepted-face next-move
regression pack against an isolated seeded development server on
`http://127.0.0.1:8007` with database
`/private/tmp/elbysodic-issue-152-qa.sqlite3`.

- `scripts/writer_activation_qa.py` passed. The path created a new invitation,
  accepted it into faceless membership, verified Desk first-face continuation,
  created a first-face draft, and checked accepted-writer wanted and plotting
  entry points.
- Focused rendered regression proof lives in
  `tests/test_onboarding_journey_contracts.py` for no-face, draft,
  submitted, revision-requested, accepted-without-scene, and
  accepted-with-recommended-opening states.
