# UAT Protocol: Onboarding Regression Pack

Status: reusable UAT protocol
Flow: auth entry, request access, invite acceptance, first face, applicant
state, director launch, and public preview handoff
Primary users: Active Scene Writer, Invited/New Face Applicant, Hook Hunter,
Community Director, Staff Moderator, Safety-Boundary Writer, Returning Regular
Last updated: 2026-06-03

## Evidence Mode

Use this protocol for simulated UAT, browser QA, or observed UAT against
implemented routes, screenshots, or a deployed preview. Simulated findings must
stay labeled as synthetic until real PBP writers or directors perform the task.

## Research Question

Can a writer or director move through the entry and onboarding states without
confusing account, membership, face, application, staff review, request-access,
or public-preview boundaries?

## Artifact Options

- `/login`, `/logout`, stale-session recovery, and account-visitor posture
- `/network` and public catalog cards
- `/c/{community}` public realm previews and request-access entry
- `/invite/{token}` acceptance states
- `/applications/new` and `/applications/{character}` first-face work
- `/claims`, `/wanted`, `/plotting`, and first-scene handoff surfaces
- `/studio/launch`, `/studio/access-requests`, and invitation management
- screenshots, browser QA artifacts, local preview URLs, or PR diffs

## Starting States

Run the smallest set that matches the surface under test:

- Signed-out public visitor.
- Signed-in account visitor with no local membership.
- Pending access requester.
- Invited writer with valid, accepted, revoked, expired, malformed, or
  cross-community token.
- Faceless member with no public posting identity.
- Applicant with draft, submitted, revision-requested, accepted, or declined
  application.
- Member with accepted active face.
- Staff or director with current-community capability.
- Inactive membership.
- Same global account or route target in another community.

## Tasks

1. Auth entry and recovery: sign in, sign out, recover from stale or inactive
   selected membership, and confirm the page explains account versus realm
   membership without granting member shell state.
2. Public preview handoff: inspect a realm preview or catalog card, identify
   whether access is invite-only, request-access, closed, or application-ready,
   and choose the next safe action.
3. Request access: submit or revisit a request-access posture and confirm the
   user understands it is interest, not membership or permission.
4. Invite acceptance: accept or inspect valid, accepted, revoked, expired,
   malformed, and cross-community invite states without exposing raw tokens,
   launch-room details, or private staff context.
5. First-face onboarding: start or continue first-face work, then distinguish
   account, membership, public face, application, claims, reserves, wanted, and
   scene handoff.
6. Applicant state: inspect draft, submitted, revision-requested, accepted, and
   declined application states and explain what staff can see versus what other
   writers can see.
7. Director launch: open Studio Launch, access requests, and invitation
   management, then identify private blockers without showing them to ordinary
   members or public visitors.
8. First writing move: from an accepted face, find one concrete next move:
   claim/reserve cleanup, wanted hook, plotting room, location, open scene, or
   thread.

## Success Criteria

- The participant can name their state: public visitor, account visitor,
  pending requester, invited writer, faceless member, applicant, member with
  face, staff, director, inactive member, or cross-community visitor.
- Every state has a concrete next action or a clear no-action recovery state.
- Public and account-visitor surfaces never render Desk, active face, unread
  counts, staff controls, private notes, invite links, application review state,
  plotting rooms, or reserves unless authorized.
- Applicant and faceless-member flows point to first-face work without showing
  another writer's applications, staff notes, or private queues.
- Director launch and request-access review surfaces use current-community
  state and do not imply public self-serve registration.
- Copy uses realm, writer, face, roster, application, claims, reserves, wanted,
  plotting, scene, thread, needs reply, waiting, caught up, and watching.
- Desktop and mobile first view preserve current identity, privacy state, and
  primary action without overlap, truncation, or horizontal scroll.

## Browser QA Checklist

Use `docs/operations/onboarding-browser-qa.md` for local commands. Record:

- base URL and database path
- browser QA profile or script name
- desktop/tablet/mobile screenshots or artifact directory
- seed persona or login state for each pass
- pass/fail notes for first viewport, primary action, copy clarity, privacy
  state, focus order, text overflow, horizontal overflow, and console errors

## Synthetic Panelists

Use these lenses for simulated panel passes:

- Active Scene Writer: wrong-face prevention, obligations, and first writing
  move.
- Invited/New Face Applicant: public trust, application state, and staff
  visibility.
- Hook Hunter: wanted-to-application and wanted-to-request-access handoff.
- Community Director: launch blockers, invitations, access requests, and
  staff workload.
- Staff Moderator and Safety-Boundary Writer: private notes, review state, and
  applicant confidence.
- Returning Regular: stale session recovery, membership switching, and account
  posture.

## Required Proof Candidates

- Rendered tests: public visitor, account visitor, pending requester, invited
  writer, faceless member, applicant, member, staff/director, inactive, and
  cross-community states.
- Negative assertions: Desk, active face, unread counts, staff controls,
  private notes, invite links, application review state, plotting rooms, and
  reserves where unauthorized.
- Browser QA: community landing profile plus writer activation QA across
  desktop/tablet/mobile where the script supports it.
- Copy check: account, membership, face, application, claims, reserves, wanted,
  plotting, scene, and thread vocabulary.
- Accessibility check: labels, focus order, keyboard reachability, alert roles,
  and mobile tap targets.
- Real UAT: repeat the highest-risk tasks with 2 to 3 PBP writers or directors
  after the route is reachable in a shared preview.

## Decision Ledger

Record findings as:

- Accepted: update tests, docs, product docs, component changes, or existing
  issue links in the same PR.
- Proposed: useful but needs more evidence or route implementation.
- Deferred: likely correct but blocked by another issue or release gate.
- Rejected: conflicts with Elbysodic standards or evidence is too weak.
- Not-now: valid later work outside the onboarding backbone.

Never promote synthetic-only findings as real UXR.
