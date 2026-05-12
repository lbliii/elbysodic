# Community Creator Onboarding Plan

Status: active product and implementation plan
Owner: Product, web, service, storage, auth, Blueprint, docs, and test stewardship
Created: 2026-05-10
Last updated: 2026-05-12
Review by: 2026-05-30
Closure criteria: split into implementation PRs for first realm setup, guided
realm builder, invitation handoff, launch checklist, and docs/test collateral;
archive when those PRs land or this plan is superseded by a more specific
hosted onboarding roadmap.

## 2026-05-10 Implementation Update

Completed locally:

- Added the first-realm boundary to multi-tenancy, information hierarchy, and
  README guidance.
- Added a read-only Studio launch room at `/studio/launch`.
- Added `RealmLaunchReadiness` and checklist items to the Director Studio read
  model.
- Connected Studio Operations and the Studio room grid to the launch checklist.
- Added rendered coverage for the seeded director Studio path and an empty
  configured realm that still has required lanes backstage.

Still open:

- The transition from no realm to empty configured realm is not implemented.
  It is now split into
  [First Realm Setup 2026-05-10](first-realm-setup-2026-05-10.md).
- Launch status now persists backstage, invite-only, and public-preview states
  while public readiness still depends on required realm content.
- Guided Realm Builder writes, invitation lifecycle, and first-face handoff are
  still future slices.
- Program Blueprint Apply remains gated.

## 2026-05-12 Baseline Update

First realm setup has merged as the CLI/service bootstrap slice. Public-ready
realm previews have also merged, and launch state now persists as
`backstage`, `invite-only`, or `public-preview` while still requiring published
premise plus public scene hub before public catalog exposure.

The first guided builder and invitation slices are now implemented: directors
can create the minimum opening packet from `/studio/launch`, create writer
invite links, manage pending/accepted/revoked invitation state, and accepted
writers can create a first face during invite acceptance or continue to the
first-face application form. Alpha delivery is copy-only, launch status is
persisted, and remaining work is richer delivery and first-face polish, not
proving that the first paths can write tenant-scoped data.

Current onboarding sequence:

1. Keep CLI bootstrap as the production-safe first realm creation path.
2. Extend guided Studio builder writes beyond the minimum opening packet into
   richer intake/claims defaults and wanted hooks.
3. Replace copy-only invitation delivery with email/resend when sender policy
   exists, and extend no-face onboarding into claims/reserves/first-scene work
   before any public self-serve registration.
4. Connect persisted launch status to hosted production runbooks and public
   catalog opening checks.

## Purpose

Elbysodic needs a creator onboarding path for a potential community director:
how they initiate opening a realm, how they shape it, how they invite staff and
writers, and how Studio proves the realm is safe to open.

This is not generic workspace setup. The creator is a director opening a
play-by-post realm with premise, scene hubs, roster policy, face claims,
director materials, wanted hooks, intake, and appearance.

This plan is the first Realm Studio opening path in the strategy spine at
`docs/product/strategy-spine.md`. It should create enough foundation for Writer
Network onboarding later, but it should not become public self-serve creator
signup or hosted billing scope.

## Current Boundary

- Public registration is intentionally deferred.
- `/request-access` currently tells visitors that access opens through a
  director invitation.
- The post-PR31 roadmap already prioritizes first realm setup, invitation
  model, first-face onboarding, and then Blueprint Apply or Guided Realm
  Builder.
- Program Blueprint intake can parse, validate, and preview YAML, but apply is
  gated until typed diff, collision handling, transaction, rollback, and tenant
  proof exist.
- The MVP is one community per install, but architecture remains tenant-aware.

## Product Principles

- Say "open a realm", "director", "writer", "face", "roster", "scene hub",
  "wanted hook", "claims", "reserves", and "backstage".
- Keep creator onboarding inside Studio, not a detached SaaS wizard.
- Let directors leave and return. Setup should be a saved launch room with
  sections, status, and next actions.
- Do not open public self-serve registration before invitation and first-face
  onboarding are implemented.
- Do not expose Blueprint Apply until the hydration gate is satisfied.
- Keep `community_id`, membership ownership, character authorship, and
  role-based permissions explicit in every implementation slice.

## Entry Model

### Self-Hosted MVP

The production operator runs the existing or planned bootstrap path to create
the first real director account. After login, Studio detects that no configured
realm exists and routes the director to an "Open first realm" launch room.

The no-realm public state remains `/network`: "The first realm is still
backstage." Signed-in directors get the setup path; signed-out visitors get
login/request-access.

### Future Hosted Flow

A potential creator starts from `/network` or `/request-access` with an "Open a
realm" action. The product records a creator request or invite, then creates a
global `User` and one director `CommunityMembership` inside a new community.

Hosted public self-serve creation remains not-now until abuse, email, billing,
custom domain, and support posture are designed.

## Creator Journey

### 1. Claim The Realm

Goal: create an empty but configured community, distinct from "no realm exists
yet."

Director inputs:

- realm name
- realm slug
- director display name for this community
- short premise
- launch status: backstage, invite-only, or public preview
- genre/tone tags from a safe allowlist or director-defined facets after
  facet setup exists

Implementation notes:

- Use service/repository methods, not ad hoc SQL in page handlers.
- Create the community, director role, director membership, and minimum default
  settings in one transaction once transaction helpers exist.
- Preserve the distinction between global `User` and community-local
  `CommunityMembership`.

Proof:

- repository/service tests for first realm creation with explicit
  `community_id`
- rendered tests for no-realm, empty configured realm, director, ordinary
  member, and signed-out states

### 2. Choose Starting Path

Goal: let directors choose how to shape the realm without making Blueprint
Apply the first production write path.

Paths:

- Guided Realm Builder: default path for first production onboarding.
- Program Blueprint Preview: paste YAML, validate, and preview hub counts.

The UI should explain Blueprint preview as a validation gate, not a launch
button, until hydration apply is transaction-backed and tested.

Proof:

- rendered tests that Blueprint preview has no apply action before the gate
- service tests that builder and preview paths stay tenant-scoped

### 3. Build Scene Hubs

Goal: create the first playable surfaces where scenes happen.

Required setup:

- at least one public scene hub
- optional plotting or wanted area
- optional private staff lane
- board description, tagline, visibility, and media metadata where supported

Language:

- "Where do scenes happen?"
- "What needs to be public when writers arrive?"
- "What is backstage for directors?"

Proof:

- board repository tests with `community_id`
- rendered tests for public/private board visibility
- browser QA for the first setup screen if layout changes are substantial

### 4. Write Director Materials

Goal: make the realm understandable before writers arrive.

Minimum launch packet:

- premise
- rules or safety guide
- application guide
- current event or opening prompt

Optional:

- factions
- canon primer
- face claim policy
- reserve policy

Materials should remain typed world materials, not threads.

Proof:

- service tests for material creation and visibility
- rendered privacy tests for draft, published, and staff-only material

### 5. Configure Intake, Claims, And Reserves

Goal: define how writers bring faces into the roster.

Director setup:

- application questions
- required claim types
- reserve duration and expiration posture
- canon/OC policy if relevant
- whether new faces start as draft, submitted, or accepted
- staff review notes/checklist visibility

This slice depends on the invitation model and first-face onboarding contracts.

Proof:

- service tests for claim and application configuration
- rendered tests for no-face writer state and first-face handoff
- privacy tests proving applicant notes and staff notes stay scoped

### 6. Set Realm Appearance

Goal: give directors atmosphere without unsafe skinning.

Allowed:

- approved theme tokens
- typography preset
- density preset
- post style defaults
- board media URL with alt text
- approved media treatment, focal point, and overlay

Disallowed:

- raw CSS
- scripts
- external font URLs
- HTML/template overrides
- layout-breaking controls

Proof:

- validation tests for token allowlists and unsafe values
- rendered tests for theme health warnings
- browser QA for a representative light and dark realm

### 7. Invite Staff And Writers

Goal: move from director-only setup into controlled community opening.

Director actions:

- invite co-directors or staff
- invite writers
- revoke or expire invitations
- preview the writer acceptance and first-face flow

Open decisions:

- director-created accounts vs invite links vs request-access queue
- whether invites create `User`, `CommunityMembership`, or both
- expiration, revocation, replay protection, and email delivery posture

Proof:

- invite lifecycle service/repository tests
- rendered tests for invite acceptance, replay denial, and privacy
- abuse/rate-limit notes for any public request surface

### 8. Launch Checklist

Goal: prevent directors from opening a realm with missing structure or privacy
risks.

Checklist gates:

- premise exists
- at least one public scene hub exists
- application guide exists
- claim/reserve policy is explicit, even if claims are disabled
- public preview does not render staff/private material
- director membership and role are community-scoped
- first-face onboarding route exists for invited writers
- backup/smoke posture is recorded for production installs

The launch action changes status from backstage to invite-only or public
preview. It should not publish hidden materials or broaden permissions
implicitly.

Proof:

- service tests for launch readiness and status transitions
- rendered route privacy matrix update if route visibility changes
- smoke note for production-like setup path

## Studio Surface Shape

The creator should land in a Studio launch room with persistent sections:

- Realm identity
- Scene hubs
- Director materials
- Intake, claims, and reserves
- Wanted hooks
- Appearance
- Invites
- Launch checklist

After launch, the same surface should become ordinary Studio with launch
progress collapsed into operations lanes:

- Realm pulse
- What needs a director?
- Intake and claims
- Scene hubs
- Director materials
- Wanted hooks
- Appearance
- Invites

## PR Slices

### PR 1: First Realm Setup Decision And Empty States

Status: split out to
[First Realm Setup 2026-05-10](first-realm-setup-2026-05-10.md) after steward
consultation. The accepted direction is CLI/bootstrap-owned first realm setup
before any web-global setup authority.

Scope:

- define "no realm exists" vs "empty configured realm"
- decide whether `bootstrap-admin`, a CLI, or Studio creates the first realm
- update route behavior for signed-in director in no-realm state
- add rendered tests for public, signed-in, and director states

Collateral:

- `docs/architecture/multi-tenancy.md`
- `docs/product/information-hierarchy.md`
- README deployment notes if command behavior changes

### PR 2: Studio Launch Room Skeleton

Status: implemented locally as `/studio/launch` and `RealmLaunchReadiness`.
Remaining follow-up is authorization hardening and launch-first routing for
empty configured realms, tracked by the first realm setup plan.

Scope:

- add director-only launch room route for an empty configured realm
- render setup sections with completion states
- keep controls read-only or hidden for non-directors
- reuse shared Studio/Director components where practical

Collateral:

- control topology and navigation docs if route ownership changes
- rendered route privacy matrix

### PR 3: Guided Realm Builder Minimum Writes

Scope:

- service-owned writes for realm identity, first scene hub, and required
  director materials
- transaction-backed creation if transaction helper has landed
- validation messages in director language

Collateral:

- service/storage tests
- rendered setup tests

### PR 4: Intake And First-Face Handoff

Scope:

- continue the invite flow for writers who skip first-face creation during
  acceptance
- define no-face writer states across roster, application, queues, and composer
- configure minimum application/claim policy during setup

Collateral:

- security docs for invitation boundary
- information hierarchy docs for first-face navigation

### PR 5: Appearance And Wanted Launch Polish

Scope:

- expose safe appearance setup within the launch room
- allow initial wanted hooks if the realm needs them before opening
- preserve Blueprint preview as a non-mutating alternative input path

Collateral:

- appearance Studio docs if controls change
- Program Blueprint docs only if preview/apply behavior changes

### PR 6: Launch Checklist And Status Transition

Scope:

- implement launch readiness read model
- block opening when required launch gates fail
- transition from backstage to invite-only or public preview
- prove no private/staff material leaks in public preview

Collateral:

- rendered privacy matrix
- changelog fragment for user-visible launch behavior

## Dependencies

- Production admin bootstrap and persistence smoke should land before real
  production usage.
- Invitation model must land before broad writer onboarding.
- First-face onboarding must land before public creator onboarding.
- Program Blueprint Apply must wait for typed diff, transaction, rollback, and
  tenant proof.
- Transaction helper should precede multi-row setup writes where practical.

## Not Now

- Public self-serve hosted community creation.
- Billing, plan limits, or custom domains.
- Raw CSS skins or external theme assets.
- General plugin system.
- Multi-community management UI beyond preserving tenant-aware architecture.
- Blueprint Apply button before the hydration gate.

## Steward Notes

Consulted root constitution plus planning, docs, web/UI, roadmap, and Blueprint
contracts. Accepted findings: creator onboarding must remain PBP-native,
director-led, tenant-aware, invitation-first, and Studio-owned. Deferred
findings: hosted public self-serve creation, billing, custom domains, and
Blueprint Apply belong after production trust gates and first-face onboarding.
