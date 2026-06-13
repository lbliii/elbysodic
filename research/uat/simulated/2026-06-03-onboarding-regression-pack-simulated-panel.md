# Synthetic Panel Run: Onboarding Regression Pack

Status: synthetic panel
Date: 2026-06-03
Researcher: Codex
Artifact evaluated: issue #118 scope, existing UAT protocols, browser QA
scripts, community landing browser QA, rendered privacy matrix, and current
onboarding route contracts
Seed docs: `docs/product/user-personas-panel.md`,
`docs/architecture/rendered-route-privacy-matrix.md`,
`docs/architecture/seed-personas.md`,
`research/uat/protocols/public-realm-preview.md`,
`research/uat/protocols/first-face-onboarding.md`,
`research/uat/protocols/wanted-to-plotting-handoff.md`
Panelists used: Active Scene Writer, Invited/New Face Applicant, Hook Hunter,
Community Director, Staff Moderator and Safety-Boundary Writer, Returning
Regular
Confidence: medium for synthetic convergence, low for observed usability

This is simulated research. It is useful for critique and hypothesis
generation, but it is not real interview evidence.

## Task Prompt

```text
Evaluate the repeatable onboarding QA pack for auth entry, request access,
invite acceptance, first face, applicant flow, director launch, and public
preview handoffs. Focus on whether the tasks prove public privacy, account
visitor posture, first-face clarity, staff/director privacy, mobile composition,
and PBP-native vocabulary without turning synthetic findings into doctrine.
```

## Panel Findings

### Active Scene Writer

- Flow: accepted face and first writing move
- Severity: P1
- User Job: know who I am wearing and what I owe next before posting
- Evidence: persona guide prioritizes active face, obligations, and wrong-face
  prevention; existing browser QA covers Desk, wanted, and plotting entry
- User Impact: accepted writers can still stall if "accepted" is a status
  rather than a path into wanted, plotting, locations, or scenes
- Expected Experience: accepted application and Desk state should keep face,
  claims/reserves, wanted, plotting, and first-scene paths close together
- Recommended Change: keep first writing move as a required UAT task and proof
  candidate
- Required Proof: rendered tests for accepted applicant handoff plus browser QA
  first viewport on Desk/application
- Collateral: `research/uat/protocols/onboarding-regression-pack.md`
- Confidence: medium

### Invited Or New Face Applicant

- Flow: public preview, request access, and first-face work
- Severity: P1
- User Job: decide whether the realm is safe and worth bringing a face into
- Evidence: public preview and first-face protocols both flag public/private
  audience confusion and staff-note anxiety
- User Impact: a polished public preview can still lose trust if request access
  reads as membership or if application visibility is ambiguous
- Expected Experience: every entry state names what happens next and who can
  see notes, applications, claims, and reserves
- Recommended Change: require public/account/applicant negative assertions and
  copy checks in the onboarding protocol
- Required Proof: public visitor, account visitor, pending requester, faceless
  member, applicant, member, staff/director, inactive, and cross-community
  rendered states
- Collateral: `docs/operations/onboarding-browser-qa.md`
- Confidence: medium

### Hook Hunter

- Flow: wanted hook to application or request access
- Severity: P2
- User Job: follow a playable opening without exposing private pitch notes
- Evidence: wanted handoff protocol identifies open/raised-hand/private-note
  leakage risks; issue #119 covers public wanted handoff work
- User Impact: hook hunters can misread a public wanted hook as an application
  grant or expose a concept before they understand staff visibility
- Expected Experience: public wanted actions should say request access or
  start application without implying membership
- Recommended Change: keep wanted-to-request-access and wanted-to-application
  as explicit UAT tasks, but defer UI changes to #119 and #116
- Required Proof: rendered wanted public/privacy assertions and browser QA on
  wanted detail mobile/desktop
- Collateral: existing issues #119 and #116
- Confidence: medium

### Community Director

- Flow: Studio Launch, access requests, and invitations
- Severity: P1
- User Job: open a realm and manage invitations without leaking launch blockers
- Evidence: community landing browser QA already includes Studio Launch and
  Operations; issue #115 tracks director realm-opening front-end
- User Impact: directors need repeatable proof that launch blockers and invite
  links are private while public preview remains safe
- Expected Experience: QA should inspect director state and public/account
  visitor state in the same pass
- Recommended Change: add director launch and invitation management states to
  the onboarding browser QA checklist
- Required Proof: browser QA artifacts and rendered tests for director,
  ordinary member, account visitor, public visitor, inactive, and
  cross-community states
- Collateral: `docs/operations/onboarding-browser-qa.md`
- Confidence: medium

### Staff Moderator And Safety-Boundary Writer

- Flow: application review, request access, and private notes
- Severity: P1
- User Job: protect applicant and staff context from leaking through public or
  member surfaces
- Evidence: research steward requires synthetic notes to label evidence; privacy
  matrix lists request notes, staff notes, invite links, review state, and
  private queues as sensitive
- User Impact: one leaked applicant note can break trust in a pseudonymous
  writing space
- Expected Experience: public, member, applicant, and staff surfaces have
  visibly different audience states and negative privacy proof
- Recommended Change: make negative assertions and evidence labeling required
  in every onboarding UAT note
- Required Proof: negative rendered assertions plus browser QA copy/privacy
  checklist
- Collateral: protocol decision ledger and operations checklist
- Confidence: medium

### Returning Regular

- Flow: auth entry, logout, stale session recovery, and membership switching
- Severity: P2
- User Job: return to the correct realm and face without stale session surprises
- Evidence: issue #114 tracks auth UX; production auth issue #54 tracks backend
  trust; QA currently needs a protocol that routes findings into those issues
- User Impact: returning users may mistake account visitor posture or stale
  membership recovery for lost access
- Expected Experience: login, logout, account visitor, inactive, and
  cross-community recovery copy should be tested as trust surfaces
- Recommended Change: add auth entry/session recovery tasks without changing
  auth behavior in this PR
- Required Proof: rendered auth/session states and browser QA where UI changes
  land
- Collateral: existing issue #114
- Confidence: medium-low until auth UX surfaces are implemented

## Convergence

- Public visitor, account visitor, faceless member, applicant, accepted member,
  staff/director, inactive, and cross-community states need to be tested as
  distinct states.
- Browser QA must check identity signal, primary action, mobile composition,
  privacy state, focus order, overflow, and console errors.
- Synthetic panel and simulated UAT outputs must stay labeled as synthetic
  until real PBP writers or directors perform the tasks.
- Accepted findings should route to existing implementation issues rather than
  expanding this QA-pack PR into route, auth, schema, or privacy changes.

## Tensions And Minority Reports

- The Hook Hunter wants richer wanted-to-application paths now; the safety lens
  prefers deferring UI changes until public-preview privacy and request-access
  posture are proven.
- The Returning Regular lens wants stale-session recovery covered, but auth UX
  implementation belongs to #114 and backend trust gates belong to #54.
- The Director lens wants launch-room QA in the pack, while the applicant lens
  warns that public preview should not expose director blockers as proof that
  the realm is alive.

## Decisions

- Accepted: create one reusable onboarding regression protocol that stitches
  public preview, auth entry, request access, invite acceptance, first face,
  applicant state, director launch, and first writing move tasks together.
- Accepted: add an operations browser QA checklist that reuses the existing
  community landing browser profile and writer activation script.
- Accepted: record this panel run as synthetic-only evidence with confidence
  labels and promotion boundaries.
- Proposed: when #114, #116, #119, or #115 change surfaces, use this pack to
  produce fresh screenshots and rendered privacy proof.
- Deferred: real UAT until a shared preview is stable and participant consent
  is planned.
- Rejected: treating synthetic panel convergence as validated user research.
- Not-now: broad analytics, new public registration, or a new browser QA CLI
  profile before the existing scripts are exhausted.

## Proof Needed

- Rendered test: implementation issues should add state-specific privacy tests
  when surfaces change.
- Service test: only when accepted findings change service read models.
- Browser QA: run `scripts/browser_qa.py --profile community-landing` and
  `scripts/writer_activation_qa.py` for onboarding-affecting PRs.
- Copy check: use PBP-native account, membership, face, application, claims,
  reserves, wanted, plotting, scene, and thread language.
- Accessibility check: labels, focus order, tap targets, and mobile overflow
  for login, request access, application, invite, and Studio controls.
- Real interview: after live preview and consent planning.
- Real UAT: after live preview and consent planning.
- No collateral: this PR changes QA/research artifacts only; no route, schema,
  auth, permission, or privacy behavior changes.

## Promotion Target

- `research/uat/protocols/onboarding-regression-pack.md`
- `docs/operations/onboarding-browser-qa.md`
