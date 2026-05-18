# Post-PR31 Priority Roadmap

Status: active sequencing snapshot; first priorities mostly merged or superseded
Owner: Product, operations, web, service, storage, and test stewardship
Created: 2026-05-10
Last updated: 2026-05-18
Review by: 2026-06-01
Closure criteria: The first five priorities are merged or superseded by more
specific implementation plans, and remaining items are linked into the
production-readiness roadmap, Studio roadmap, or archived as not-now.

## Context

PR #31 closed the first-time entrypoint gap: anonymous login/request-access
actions, platform-shell auth pages, intentional empty network launch state,
production CSP compatibility, Railway staging seed startup, production admin
bootstrap, and SQLite inspection docs.

This plan captures the next work queue after that merge. It is not a feature
spec. It exists so future agents have a current, ranked sequence for turning
Elbysodic from a production-like demo into a real, supportable PBP studio.

## 2026-05-18 Status Refresh

The original top priorities have mostly moved into narrower plans or landed:
first realm setup is archived as implemented, wanted backstage is archived as
implemented, public discovery and realm previews have advanced, and signed-in
non-member previews now have an explicit account-visitor boundary. Keep this
roadmap active only as a short sequencing bridge until the remaining items are
absorbed by production-readiness, community creator onboarding, Studio
Operations, and public catalog plans.

## 2026-05-12 Project State

Pulled `main` to `f08eae8`.

Recent merged progress:

- PR #37 merged the layered shell, shared inner-sidebar model, privacy-gated
  rail rows, and first page-surface cleanup waves.
- First realm setup is implemented as a CLI/service bootstrap path with
  transaction rollback proof; the launch room can now create the minimum
  opening packet for an empty configured realm.
- Studio Launch and Studio Operations exist as product-native rooms, but the
  production inspection surface for DB/env/session posture is still not the
  read-only ops scope described below.
- PR #38 added service-owned signed-out public catalog paths and public realm
  previews for premise/guidebook/wanted surfaces without exposing identity,
  staff, queue, interest, or write-action state.
- Railway staging smoke, restart persistence, and a SQLite backup/restore drill
  were recorded on 2026-05-12.
- Director-created writer invitations now create one-realm memberships and can
  hand accepted writers into first-face setup.

Current priority reset:

1. Execute production bootstrap only after the go/no-go checklist is approved.
2. Keep notification count privacy green as shell/sidebar surfaces change.
3. Extend first-face onboarding beyond current handoff copy into claims,
   reserves, and first-scene guidance.
4. Replace copy-only invitation delivery with an explicit email or resend
   contract when credentials and sender policy exist.
5. Broaden catalog posture beyond launch/application/claims into activity
   freshness and request posture.

## Sequencing Principles

- Stabilize deployment, identity, data persistence, and recovery before adding
  broader public onboarding.
- Keep production and staging separated by volume, secret, and environment
  posture.
- Prefer Elbysodic Studio and explicit CLI commands over manual database writes.
- Preserve PBP-native language: realm, director, writer, membership, face,
  roster, wanted hooks, scenes, claims, reserves, queues, and watching.
- Every accepted item needs proof: smoke record, rendered tests, repository
  tests, docs, or an explicit no-collateral note.

## Top 10 Priorities

### 1. Complete Staging Smoke

Goal: prove the staging Railway environment is usable before touching real
production data.

Status: completed on 2026-05-12 for staging. The record lives in
`docs/operations/railway-smoke.md`.

Required work:

- attach a staging-only volume at `/app/var`
- set `ELBYSODIC_ENV=staging`, staging secret, and `ELBYSODIC_DEMO_MODE=1`
- deploy from `main`
- confirm the staging override runs `seed-demo`
- log in as `writer@example.com` with `password`
- smoke `/`, `/network`, `/login`, tenant-prefixed realm pages, logout, and
  restart persistence

Proof:

- recorded Railway smoke note in the PR or relevant plan update
- live staging URL and deployment identifier

Collateral:

- update `docs/operations/railway-smoke.md` if the run discovers missing steps

### 2. Bootstrap Production Admin

Goal: create the first real director account without demo seed data.

Required work:

- attach a production-only volume at `/app/var`
- set `ELBYSODIC_ENV=production` and a production-only secret
- run `elbysodic bootstrap-admin` over Railway SSH
- confirm login and admin membership resolution
- turn off `ELBYSODIC_DEMO_MODE` unless production is intentionally a seeded
  demo

Proof:

- successful production login as the bootstrapped admin
- `sqlite3` read-only check showing one user, one community, one admin role,
  and the admin membership

Collateral:

- update the smoke record with the bootstrapped account email but not password

### 3. Define First Realm Setup

Goal: make the first non-demo production community intentional.

Status: CLI/service bootstrap is implemented and covered locally. The first
realm can be created without global director power, partial setup rows roll
back on failure, and empty configured realms remain backstage until they have
public-ready material. The next planning question is guided Studio builder
writes and launch status, not whether first realm setup exists at all.

Required work:

- decide whether the first realm is created by `bootstrap-admin`, a new CLI, a
  Studio setup wizard, or Program Blueprint apply
- define minimum board/world/material defaults for an empty real community
- distinguish “empty but configured” from “no realm exists yet”
- decide whether production `/` should route to a primary realm or the network
  launch state before public opening

Proof:

- plan or implementation PR with rendered tests for empty configured realm and
  no-realm launch state

Collateral:

- `docs/architecture/multi-tenancy.md`
- `docs/product/information-hierarchy.md`
- `README.md` deployment section if command behavior changes

### 4. Build Read-Only Ops Surface

Goal: give directors/operators a product-native way to inspect the whole app
before manual SQL becomes habit.

Initial scope:

- `/ops` or Studio Operations room
- users, communities, memberships, roles, sessions
- DB path, env posture, demo mode, volume mount presence, schema version
- read-only tables and links into relevant Studio surfaces

Proof:

- rendered tests for admin-only access
- non-admin and signed-out denial
- no password hashes or session token hashes rendered

Collateral:

- security boundaries doc
- rendered route privacy matrix

### 5. Account Invitation Model

Goal: replace placeholder request-access with a real invite flow without
opening unsafe public registration.

Status: first slices implemented. Directors can create invite links from the
launch room, list pending/accepted/revoked invitation state, and revoke pending
invites. Accepting an invite creates or reuses the global user, creates a
membership in the invited realm, optionally creates a first face, starts a
session, rejects replayed tokens, and routes no-face writers to first-face
application setup. Email delivery and copy/resend-after-creation posture remain
follow-up work.

Open decisions:

- director-created accounts vs invite links vs request-access queue
- who can invite writers
- whether invites create `User`, `CommunityMembership`, or both
- expiration, revocation, replay protection, and email delivery posture
- first face/application handoff after account creation

Proof:

- service/repository tests for invite lifecycle
- rendered tests for request-access/invite acceptance privacy
- rate-limit or abuse notes if anything is public

Collateral:

- security docs
- product onboarding docs
- changelog when user-facing

### 6. First Face Onboarding

Goal: after login, a new writer should know how to choose or create their first
posting face.

Required work:

- empty roster state with clear “create/apply with a face” next step
- default face selection after creation or application acceptance
- queue and composer behavior when no face exists
- route from invite acceptance to roster/application flow

Proof:

- rendered tests for no-face writer state
- service tests for default face ownership

Collateral:

- information hierarchy and control topology docs if navigation changes

### 7. Backup, Snapshot, And Restore Drill

Goal: make SQLite safe enough for real writer data while it remains the
production-like store.

Status: staging drill completed on 2026-05-12. The record lives in
`docs/operations/sqlite-production.md`.

Required work:

- document exact backup command
- document restore procedure
- test a copied SQLite file locally
- define migration safety checklist
- decide when service must be stopped or quiescent

Proof:

- recorded backup/restore drill against staging

Collateral:

- `docs/operations/sqlite-production.md`

### 8. Program Blueprint Apply Or Guided Realm Builder

Goal: give directors a controlled way to create real realm structure beyond
manual seed data.

Status: guided builder minimum write slice is implemented for scene hub,
premise material, application guide, and default appearance tokens. Program
Blueprint Apply remains gated behind diff, collision, transaction, and rollback
proof.

Required work:

- decide between Blueprint apply as the first production setup path or a
  smaller guided Studio builder
- keep Blueprint apply diff-first, permission-checked, tenant-aware,
  transaction-backed, and rollback-tested

Proof:

- dry-run diff tests
- apply idempotency tests
- rollback tests
- ordinary-member denial tests

Collateral:

- Program Blueprint docs
- Studio intake copy

### 9. Public Discovery Polish

Goal: make `/` and `/network` feel like the front door once real or seeded
realms exist.

Status: base public discovery landed in PR #38. Signed-out visitors now use a
service-owned public catalog and can preview public-ready realm guidebook and
wanted surfaces. Desktop/mobile browser QA smoke and deep profiles passed on
2026-05-12; remaining work is richer catalog shape and invite/request posture,
not the first privacy-safe read model.

Required work:

- service-owned public catalog read model
- privacy-safe realm cards
- wanted hooks, premise/current event, public media, and request-access lane
- browser QA for desktop/mobile

Proof:

- signed-out rendered privacy tests
- browser screenshots for public catalog and empty launch state

Collateral:

- Studio Network homepage plan
- rendered privacy matrix

### 10. Transaction Boundaries For Multi-Step Workflows

Goal: prevent partial state in scene, posting, plotting, application, claims,
and future Blueprint apply workflows.

Required work:

- repository transaction helper
- identify first high-risk workflows
- add forced-failure tests
- apply transaction helper to one workflow at a time

Proof:

- rollback tests that leave no partial rows

Collateral:

- architecture note if transaction semantics become a service contract

## Not Now

- Public self-serve registration before invitation and first-face onboarding
  are designed.
- Direct production manual SQL writes except for backed-up, recorded emergency
  repair.
- Blueprint Apply button without diff, transaction, rollback, and tenant proof.
- Global super-admin powers detached from `CommunityMembership`.

## Immediate Next PR Candidates

1. Remaining privacy matrix closure tests for inactive/faceless notification
   count identity modes.
2. Read-only production inspection surface if Railway smoke shows manual SQL
   or env/session introspection remains unavoidable.
3. Invite delivery and copy/resend posture after the first link display.
4. First-face onboarding polish for accepted invitees who skip face creation.
5. Public catalog-field follow-up.
