# Production Readiness Roadmap

Status: active production gate; local auth, tenant, privacy, and full test gates pass
Owner: Cross-steward production readiness
Created: 2026-05-09
Last updated: 2026-05-18
Review by: 2026-06-01
Closure criteria: Railway smoke is recorded, schema/seed persistence risks are
resolved or explicitly deferred, S-tier core user flows have rendered and
browser proof, and follow-up work is split into PR-sized implementation plans.

## Purpose

Make Elbysodic ready to share as a real production-like PBP studio, not just a
locally impressive prototype. The target is a tenant-aware Railway deployment
where login, logout, community navigation, active face context, search, writing
flows, staff workflows, and core data boundaries feel mature enough that more
visual polish can sit on top of stable primitives.

This roadmap is the trust foundation for the product strategy spine in
`docs/product/strategy-spine.md`. Realm Studio, Writer Network, and Continuity
Graph all depend on boringly correct tenant routing, sessions, persistence,
rendered privacy, transaction boundaries, and recovery before their product
surfaces expand.

## 2026-05-19 Status Refresh

The production-trust surface is now materially clearer for alpha entry, but
live production proof is still blocked outside this workspace. Railway CLI is
not installed locally, so `docs/operations/railway-production-smoke-record.md`
contains an incomplete attempt record rather than a pass. The live host, volume,
cookie, seed media, and restart checks still need a Railway-connected operator.

Local work since the previous refresh closed several account/member/applicant
state gaps:

- Signed-in non-members render as account visitors on public realm surfaces,
  not as logged-out users.
- Tenant-scoped access requests are stored, moderated in Studio Launch, can be
  declined/reviewed, and can create linked writer invitations without granting
  membership directly.
- Access requests now reuse an existing pending/reviewed request for the same
  realm email, enforce valid pending/reviewed/invited/declined transitions, and
  have a director-only detail room for private notes and first-face context.
- Access request notes have rendered privacy proof across public pages and
  non-director member surfaces.
- Studio Operations links directly to access requests and includes request
  context in the activation lane.
- No-face members see first-face guidance from the realm home.
- Accepted applications surface a service-owned next writing move, and accepted
  face activation can recommend a specific opening when claims/reserves are
  clear.
- Program Blueprint apply remains gated, with apply-readiness checklist data
  owned by the service rather than the template.
- `scripts/browser_qa.py --profile community-landing` now covers public,
  account-visitor, member, accepted-application, and Studio routes for local
  screenshot QA. The profile passed locally on 2026-05-19 with artifacts in
  `/private/tmp/elbysodic-community-landing-qa-2026-05-19` after catching and
  closing a tablet scoped-search overflow.

Still required before this roadmap can call the production gate closed:

- Run and record live Railway production smoke.
- Decide email sender policy before replacing copy-only invitations with
  resend/email delivery.

## 2026-05-18 Status Refresh

Local proof is stronger than the stale review date implied. The full test suite
passes after the account-visitor public-preview slice; app contract check passes
with warnings as errors; `ruff check`, `ty`, and `git diff --check` pass. The
current remaining production blockers are operational rather than conceptual:
approve and execute production bootstrap, run the invite-only alpha runbook
against the live environment, record restart persistence, and decide the
invitation delivery/resend contract.

The next implementation work should stay focused on production trust and alpha
entry: account-visitor public route coverage, first-face onboarding polish,
public catalog access posture, Studio Operations attention lanes, transaction
proof for the next high-risk workflow, and Blueprint preflight without enabling
mutating apply.

The theme for this roadmap is production trust:

- writers never post as the wrong face
- staff power never follows a global user across communities
- shared-host URLs resolve the intended realm
- search and catalog surfaces never leak private or staff data
- seeded demo data does not overwrite director-edited production state
- schema and repository contracts are strong enough for future primitives
- user-facing flows are proven in rendered tests and browser QA, not only in
  isolated helpers

## Verification Snapshot

Baseline refreshed on 2026-05-12 after pulling `main` to `f08eae8`:

- PR #37 merged the layered shell/navigation contract, inner-sidebar privacy
  gates, and first page-surface cleanup waves.
- PR #38 merged public realm previews for public-ready tenant-prefixed realms:
  realm gateway, world/guidebook material, wanted board, and wanted detail.
- Signed-out `/` and `/network` now use a service-owned public catalog path,
  while signed-in viewers still receive membership continuation lanes.
- Railway staging smoke is recorded for deployment
  `13a712ad-da07-4d8f-8617-078a1ca4add6`: `/health`, public network/realm
  pages, seed media, demo login, tenant-prefixed authenticated routes, identity
  switch write, logout boundary, and service restart persistence passed.
- SQLite backup/restore drill is recorded against the staging volume-backed DB;
  the copied DB/WAL/SHM set passed `PRAGMA integrity_check` and service readback.
- Director-created writer invitations, accepted invite replay denial, and the
  first-face handoff are covered locally.
- Guided Realm Builder can create the minimum opening packet for an empty
  configured realm.
- Public discovery browser QA smoke and deep profiles passed on desktop/mobile
  widths against a local seeded app.
- `tests/test_web_security.py` now includes rendered proof that backstage
  realms stay out of the public network/direct preview, public catalog cards
  hide membership/staff signals, public wanted/material previews omit write and
  staff controls, and core production smoke covers login, tenant entry,
  membership switch, major route families, logout, and stale-session denial.

Still unverified:

- Production, as distinct from staging, still has not been bootstrapped or
  smoke-tested.
- Read-only ops inspection for DB/env/session posture is still future work.
- Invitation email delivery and resend/copy-later posture remain open; Studio
  can now list invitation state and revoke pending invitations.
- Rendered privacy matrix gaps remain for inactive/faceless notification counts;
  claims notes, direct outsider access to another writer's application room, and
  cross-tenant plotting-room id leakage now have rendered proof.
- Transaction coverage for broader multi-step workflows remains future work.

Verified locally on 2026-05-09:

- Production auth/session/CSRF scaffolding exists in `src/elbysodic/web/app.py`,
  `src/elbysodic/web/security.py`, `src/elbysodic/services/auth.py`, and
  `src/elbysodic/services/access.py`.
- `user_sessions` stores selected community and membership.
- `/login`, `/logout`, `/dev/personas`, tenant-prefixed routes, `/network`,
  mentionable search, claims search, Studio intake, applications, plotting,
  notifications, wanted hooks, boards, world materials, and Studio routes exist.
- Tests cover production auth, dev identity rejection, tenant-prefixed routing,
  session-bound membership switching, CSRF, login/logout, dev persona gating,
  network search, Program Blueprint preview, migrations, tenant repositories,
  markup, and policies.
- Public registration does not exist. Current production posture is
  login-only/demo/invite-style until an onboarding contract is designed.
- Network search exists and now operates over either the signed-in
  `studio_network()` directory or signed-out `public_studio_network()` catalog.
  It is still keyword/filter-light rather than a formal catalog-fields system.
- Program Blueprint Studio intake is dry-run preview only. Hydration/apply is
  intentionally gated.
- Live Railway smoke remains unrecorded in this repository.

## Consulted Stewards

Consulted through independent steward review plus local tests/plans review:

| Steward | Highest Priority | Confidence | Accepted |
| --- | --- | --- | --- |
| Domain | Close production auth/tenant URL readiness, then repair public primitive contracts. | High | Yes |
| DB/storage | Fix fresh-vs-upgraded schema parity and startup seed persistence before broader data work. | High | Yes |
| Services | Smoke Railway, add transaction boundaries, and finish rendered privacy proof. | High | Yes |
| Web | Decide onboarding posture, promote network/search to a safe service contract, and run browser QA. | High | Yes |
| Blueprint | No Apply button before typed diff, collision handling, transaction, rollback, and tenant proof. | High | Yes |
| Docs | Fix migration/multi-tenancy/README/Blueprint drift and triage stale plans. | High | Yes |
| Tests | Treat rendered privacy, browser QA, and S-tier smoke scripts as release proof. | High | Yes |
| Plans | Keep this roadmap as the sequencing spine; refresh or archive stale snapshots. | High | Yes |

## Raw Steward Signals

Merged signals by area:

- Steward: Cross-steward
- Area: Railway production gate
- Severity: P1
- Invariant: A production-like shared deployment must resolve identity from
  server-backed sessions, preserve tenant-prefixed URLs, keep dev helpers out of
  production, and persist state across redeploys.
- Evidence: Local production auth tests exist, but the Railway auth plan still
  names live smoke as open. DB and web stewards both identified attached
  volume, one replica, seed media, login, membership switch, and one write as
  unclosed proof.
- User Impact: A shared URL could fail at the exact trust moments that matter:
  login, staff/member separation, current realm, static media, or persistent
  writes.
- Required Fix: Record Railway smoke with exact env posture, `/health`, login,
  logout, member view, staff view, membership switch, tenant-prefixed route, one
  CSRF-protected write, seed media, volume restart, and one-replica SQLite.
- Required Proof: Smoke notes plus focused auth/security tests.
- Collateral: Railway auth plan, tenant routing plan, README/deployment notes
  if env or persistence assumptions change.
- Confidence: High

- Steward: DB/storage
- Area: Schema and migration parity
- Severity: P1
- Invariant: Fresh databases and upgraded databases must end in the same shape.
- Evidence: `CURRENT_SCHEMA_VERSION` is `12`; DB steward found migration 8 adds
  `idx_user_sessions_user`, while fresh schema does not create that index.
- User Impact: Railway fresh databases can differ from upgraded local
  databases, undermining performance and migration confidence.
- Required Fix: Add the missing fresh-schema index and a fresh-vs-upgraded
  schema/index parity test.
- Required Proof: Test that introspects tables and indexes for fresh and
  upgraded databases.
- Collateral: Migration docs.
- Confidence: High

- Steward: DB/storage
- Area: Startup seed persistence
- Severity: P1
- Invariant: Long-lived demo data should not be overwritten by automatic seed
  refresh on app startup.
- Evidence: `create_services()` seeds demo data; steward review found existing
  boards and materials can be rewritten on every seed pass.
- User Impact: Railway can preserve writer posts while silently resetting
  director-edited boards or materials after redeploy.
- Required Fix: Split bootstrap/create-missing seeding from intentional demo
  refresh/reset, or make startup seed create-missing-only for director-editable
  rows.
- Required Proof: File-backed restart test proving customized boards/materials
  survive service recreation.
- Collateral: README/Railway deployment notes.
- Confidence: High

- Steward: Web/services
- Area: Network search and public catalog
- Severity: P1
- Invariant: Public catalog/search and signed-in continuation data must use
  separate service read models with explicit privacy rules.
- Evidence: `/network` search currently filters `studio_network()` in the page
  handler; the homepage plan already calls for a `NetworkHome` read model.
- User Impact: Search is useful for a logged-in directory, but it is not yet a
  production public discovery contract.
- Required Fix: Add service-layer public catalog cards, separate continuation
  lanes, safe counts, and query semantics.
- Required Proof: Signed-out and signed-in rendered tests proving no private,
  staff, or membership-only data leaks.
- Collateral: Network homepage plan, navigation/search docs, rendered privacy
  matrix.
- Confidence: High

- Steward: Domain/services/web/tests
- Area: Rendered privacy and S-tier core flows
- Severity: P1
- Invariant: Route families that expose staff, private, applicant, plotting,
  notification, or recovery data need rendered proof across viewer modes.
- Evidence: Existing focused regressions cover important examples, but the
  backlog and privacy matrix still call out route-family gaps.
- User Impact: Passing repository tests is not enough if a shell count,
  recovery page, sidebar, or rendered card leaks private context.
- Required Fix: Mark each S-tier route family covered/partial/missing and fill
  the gaps for boards/threads/composer, wanted/casting/claims,
  applications/review, plotting, notifications, Studio, members/characters,
  network search, and cross-tenant recovery.
- Required Proof: Focused rendered tests and browser QA notes.
- Collateral: `docs/architecture/rendered-route-privacy-matrix.md`.
- Confidence: High

- Steward: Services/DB/Blueprint
- Area: Transaction boundaries
- Severity: P1
- Invariant: Multi-step workflows should not leave partial thread, post,
  watch, notification, room, claim, or Blueprint state when a later write fails.
- Evidence: Services steward identified thread creation and
  plotting-room-to-scene as multi-step workflows; Blueprint hydration requires
  transaction-backed apply.
- User Impact: Failed writes can strand scenes, plotting rooms, notifications,
  or import rows in inconsistent state.
- Required Fix: Add repository transaction support and apply it first to
  thread creation, plotting-room-to-scene, application acceptance/claim
  hydration, and Blueprint apply.
- Required Proof: Forced mid-workflow failure tests.
- Collateral: Architecture note if transaction semantics become a service
  contract.
- Confidence: Medium-high

- Steward: Domain/docs
- Area: Product primitive contract
- Severity: P1
- Invariant: First-class PBP primitives and tenant context should have stable,
  current public contracts.
- Evidence: Domain models now include applications, facets, materials, wanted,
  plotting, claims, interactions, watches, and notifications; `domain/__init__`
  and `domain/context.py` still expose an older contract, and docs drifted on
  multi-tenancy.
- User Impact: Future implementation can import unstable internals, reuse stale
  seeded-default helpers, or under-document current primitives.
- Required Fix: Decide stable domain exports, update/retire stale tenant
  helpers, and refresh primitives/multi-tenancy docs.
- Required Proof: Import/type tests plus docs checks.
- Collateral: `docs/architecture/primitives.md`,
  `docs/architecture/multi-tenancy.md`.
- Confidence: High

- Steward: Blueprint
- Area: Program Blueprint hydration
- Severity: P1
- Invariant: Program Blueprint apply must be diff-first, service-owned,
  transaction-backed, tenant-aware, and permission-checked.
- Evidence: Current Studio intake intentionally stops at dry-run preview; seed
  hydration exists as a privileged path.
- User Impact: A premature Apply button could create duplicate, partial, or
  cross-community board-running state.
- Required Fix: Implement typed diff rows, collision semantics, unknown-key
  diagnostics, stale-diff fingerprint, transactional apply, rollback, and
  idempotency.
- Required Proof: No-write preview, ordinary-member denial, collision preview,
  apply-same-packet-twice, rollback, and tenant tests.
- Collateral: Program Blueprint docs, Studio intake copy, changelog fragment
  when behavior changes.
- Confidence: High

## Ranked Roadmap

### Gate 0: Freeze The Production Contract

Goal: decide what the shared Railway URL is allowed to promise before adding
new primitives or visual polish.

Deliverables:

- Production posture: login-only demo/invite-style access unless a separate
  registration/request-access plan is accepted.
- Canonical S-tier smoke script:
  1. Visit `/health`.
  2. Log in.
  3. Enter one realm through `/c/{community_slug}`.
  4. Switch membership/community.
  5. Select or confirm active face.
  6. Navigate board, thread, wanted, application, plotting, notifications, and
     Studio surfaces as permitted.
  7. Complete one CSRF-protected write.
  8. Log out.
- Railway deployment checklist: env vars, allowed hosts, demo mode, volume,
  one replica, seed media, restart persistence, backup/export expectation.

Proof:

- Focused auth/security tests.
- Recorded Railway smoke notes.

### Gate 1: Storage And Persistence Hardening

Goal: make the database contract strong enough for production-like demos and
future schema work.

Deliverables:

- Fresh-vs-upgraded schema/index parity fix and test.
- Startup seed split so director-edited rows survive restart.
- Migration docs updated to schema version `12`.
- Decision on gapped migration ledger behavior.
- File-backed SQLite operational posture: one replica, busy timeout/WAL
  decision, backup/export notes.

Proof:

- `tests/test_tenant_repository.py` coverage for parity, migration ledger, and
  seed restart persistence.
- README/deployment notes if operational posture changes.

### Gate 2: Identity, Tenant, And Privacy Proof

Goal: prove the core identity model works through rendered pages, not only
repository methods.

Deliverables:

- Rendered privacy matrix marked `covered`, `partial`, or `missing` for each
  major route family.
- Tests for staff desks, application review, claims, notifications, plotting,
  cross-tenant recovery, sidebar counts, faceless state, and search/catalog.
- Domain contract cleanup for stable primitive exports and stale tenant context
  helpers.
- Active/default face contract documented before personalization expands.

Proof:

- Focused rendered tests across ordinary writer, staff, outsider, inactive, and
  same-user-different-community personas.
- Type/import test if domain exports change.

### Gate 3: S-Tier Core User Flows

Goal: make the flows people will actually click feel mature and dependable.

Core flows:

- Login, logout, session expiry/recovery, and intentionally absent
  registration/request-access messaging.
- Network home and search.
- Community entry via tenant-prefixed URLs.
- Board/location browsing, thread reading, composer reply/start/edit, active
  face context, mentions, drafts, and notifications.
- Wanted/casting/claims path from discovery to interest to plotting room.
- Application path from draft to submission to staff review to revision/accept.
- Studio daily operations for boards, world materials, applications, claims,
  wanted hooks, and navigation.

Deliverables:

- One release smoke script for these flows.
- Browser QA at desktop and mobile widths.
- Navigation/search affordance decision: add visible topbar/global search or
  explicitly defer it in docs and UI.
- Public catalog and signed-in continuation lanes split at the service
  boundary; keep maturing this into a fuller `NetworkHome`/Explore model only
  when catalog rows need fields beyond `StudioNetworkDirectory`.

Proof:

- Rendered tests plus browser screenshots/notes for `/login`, `/network?q=magic`,
  `/c/x-men-apocalypse`, `/c/jurassic-park-universe/boards/paddock-twelve`,
  a thread composer/reply, wanted detail, application review, plotting room,
  and Studio.

### Gate 4: Transactional Workflow Maturity

Goal: keep multi-object user actions consistent when something fails.

Deliverables:

- Repository transaction helper.
- Transaction-backed thread creation.
- Transaction-backed plotting-room-to-scene handoff.
- Transaction-backed application acceptance and claim hydration where
  appropriate.
- Transaction-backed Program Blueprint apply after diff planning lands.

Proof:

- Forced-failure rollback tests for every converted workflow.

### Gate 5: Program Blueprint Apply Readiness

Goal: make director-authored starter packets safe enough for production use.

Deliverables:

- Typed hydration diff rows: create, update, skip, blocked, warning.
- Collision and duplicate semantics for program, role, face, board, material,
  wanted, theme, appearance, and board media.
- Unknown-key diagnostics.
- Stale-preview fingerprint.
- Transaction-backed apply.
- Decision on whether seed hydration remains privileged or shares planning
  semantics with YAML import.

Proof:

- Preview writes no rows.
- Ordinary members cannot preview or apply.
- Applying twice is idempotent where expected.
- Mid-apply failure rolls back.
- Cross-community collisions stay scoped.

### Gate 6: Production Workflow Polish

Goal: improve the highest-value director and writer workflows after the data
and privacy gates are stable.

Deliverables:

- Studio operations daily console improvements.
- Application/claims review movement and conflict resolution.
- Wanted lifecycle outcomes and plotting handoff.
- Board/world editor ergonomics only where they support production workflows.
- Sidebar/navigation visual and mobile polish.
- Appearance Studio theme editor/health warnings after the core data contract
  is no longer moving underneath it.

Proof:

- Rendered privacy tests with every staff-facing workflow.
- Browser QA for dense desktop and mobile flows.

### Gate 7: Next Primitives After Production Trust

Do these after Gates 0-5 are materially closed:

- Living canon manual scene outcomes.
- Canon proposal/review layer.
- Public registration or request-access onboarding.
- Capability rows and partial staff roles.
- Catalog facets and full public search.
- Appearance variants and Blueprint round trip.

Acceptance prerequisites:

- Railway smoke is recorded against the real URL.
- Fresh/upgraded schema parity and startup seed persistence are green.
- Rendered privacy matrix gaps are reduced to explicit, accepted follow-ups.
- The release-smoke regression remains green.
- Transaction boundaries exist for the workflow family the primitive will
  extend.
- Docs say whether the primitive is current, gated, or planned.

Gate 7 is a sequencing gate, not a feature freeze. Future primitive work can
start earlier only when it directly closes a production-readiness dependency.
For example, a public catalog read model can move before broader catalog facets
because search privacy is a Gate 3 requirement; Living Canon automation cannot
move before manual scene outcomes and rendered privacy proof.

## Parity Matrix

| Contract | API/CLI | Programmatic | Protocol | Schema/Types | Docs | Examples | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Production auth/session | CLI has production flags | `create_app(debug=False)` | Session cookie + CSRF | `user_sessions` | security docs current | seed personas | local tests green; Railway staging smoke recorded |
| Tenant URL routing | N/A | resolver/middleware | `/c/{community_slug}` | `communities.slug/host` | tenant routing plan current | seeded realms | rendered tests green; Railway staging smoke recorded |
| Public catalog/search | N/A | service-owned public catalog | `/network?q=` | no catalog primitive yet | homepage plan says richer fields future | seed programs | signed-out privacy tests and browser QA green |
| Schema migration | CLI uses app factory | `create_schema()` | SQLite ledger | version 16 includes invitations and launch status | docs updated by this pass | N/A | migration, invitation lifecycle, and launch status tests green |
| Program Blueprints | N/A | preview service only | Studio paste POST | typed parser, no apply | docs updated by this pass | seed blueprints | preview tests green; apply tests open |
| S-tier flows | N/A | services/repos | rendered Chirp pages | current primitives | this roadmap | seed personas | focused tests and public browser QA green; full release smoke still evolving |

## Dependencies

1. Railway smoke depends on env/volume/redeployment access.
2. Public network/search depends on service-layer catalog privacy.
3. Registration/onboarding depends on a product decision about demo-only,
   invite/request-access, or public registration.
4. Blueprint apply depends on transaction support and collision semantics.
5. Living canon depends on privacy matrix coverage and transaction patterns.
6. Appearance variants should follow core flow/browser QA, not precede it.

## Not Now

- Broad visual redesign before storage/auth/privacy gates close.
- Public registration without preserving user/membership/face separation.
- Hosted community creation, billing, custom domains, or multi-community admin
  dashboards.
- Raw CSS, arbitrary templates, external font URLs, or per-community
  JavaScript.
- Automatic canon publication or AI-driven public wiki updates.
- Blueprint marketplace or background imports.

## Immediate PR Queue

1. Execute production bootstrap only after the go/no-go checklist is approved.
2. Run live Railway production smoke and record restart persistence.
3. Replace copy-only invitation delivery with an explicit email or resend
   contract when credentials and sender policy exist.
4. Extend access-request moderation into email delivery/resend once the sender
   contract exists.
5. Transaction helper expansion to the next high-risk workflow.
6. Blueprint diff/apply readiness remains gated behind transaction and
   collision proof.

## Progress Log

- 2026-05-09: Started Gate 1 by adding fresh-schema parity for the
  `idx_user_sessions_user` index, a fresh-vs-upgraded index parity regression,
  and a file-backed restart regression proving startup seed preserves
  director-edited boards and materials.
- 2026-05-09: Started Gate 2 by exporting the current first-class domain
  primitives, clarifying the legacy default-only community context helper, and
  marking rendered privacy matrix coverage as covered, partial, or missing for
  production route families.
- 2026-05-09: Started Gate 3 with an executable production release smoke
  regression that covers health, login, tenant-prefixed community entry,
  network search, thread reading, CSRF-protected membership switching,
  cross-realm navigation, and logout.
- 2026-05-09: Started Gate 4 with a repository transaction context, repository
  commit suppression inside transactions, and rollback proof for the
  multi-write thread creation workflow.
- 2026-05-09: Started Gate 5 by adding typed Program Blueprint hydration diff
  rows to the existing dry-run preview. Studio now names planned create/update
  work without enabling apply or database mutation.
- 2026-05-09: Started Gate 6 by adding a release-smoke lane to Director
  Operations so production-critical login, realm switching, writing,
  notification, and logout proof is visible from Studio.
- 2026-05-09: Closed the first Gate 7 sequencing pass by recording acceptance
  prerequisites for next primitives. Canon, public registration, partial staff
  capabilities, catalog facets, and appearance variants remain behind the
  production trust gates unless they directly close one of those gates.
- 2026-05-09: Paid down the first steward debt pass after pulling latest main:
  strict Blueprint staff flags, explicit demo seeding, serialized post-number
  allocation, accepted-face requirements for story actions, production
  application-room CSRF/privacy proof, safer tenant URL scoping for authored
  form values, draft-preserving composer submit behavior, shared PBP
  vocabulary validation, and repository write guards for story vocabulary.
- 2026-05-12: Recorded Railway staging smoke and restart persistence, recorded
  SQLite backup/restore drill, added director-created writer invitations with
  first-face handoff, added Guided Realm Builder minimum writes, ran public
  browser QA smoke/deep profiles, and refreshed the rendered privacy matrix.
- 2026-05-12: Added Studio invite management for pending/accepted/revoked
  invitations, rendered no-face invite continuation proof, and closed privacy
  gaps for claims notes, direct application outsider access, and cross-tenant
  plotting room id leakage.
- 2026-05-19: Added account-visitor public preview proof, tenant access request
  capture/moderation/invite linking, access-request privacy proof, no-face
  realm-home guidance, accepted-face next-move recommendations, service-owned
  Blueprint apply readiness, and the `community-landing` browser QA profile.
- 2026-05-19: Ran the community-landing browser QA profile locally, fixed the
  tablet scoped-search overflow it found, documented the runbook command,
  added access-request duplicate/status/detail hardening, and added release
  fragments for the branch's visible community entry changes.
