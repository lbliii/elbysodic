# Current Epic Priority Rollup


## Archival Note

Lifecycle: Superseded

Archived 2026-08-17. Ranked issues that are now mostly closed (#139, #138, #137, #107, #104, #86, #85, #79, #78, #56, #55). Live board is GitHub; see plans/README.md. Do not replace this with another evergreen ranking file (ADR 0001 D8).

Status: active sequencing snapshot after issue burn-down
Owner: Cross-steward planning, production trust, storage, service, web, docs, tests, Blueprint, and Continuity stewardship
Created: 2026-06-15
Last updated: 2026-07-20
Review by: 2026-06-29
Closure criteria: remaining open sagas/epics are split into approved PR-sized slices, approval-bound decisions are recorded on the relevant issues or docs, and the next implementation wave has local proof or a live-ops owner where required.

## Purpose

### 2026-07-20 execution update

The local trust sequence has advanced: transaction rollback (#56), tenant
integrity (#55), capability/audit (#78/#104), Blueprint apply (#85), and the
manual Continuity Graph backend (#79) now have implementation PRs or merged
proof. For #79, schema v27, repository/service lifecycle, visibility-filtered
notification target planning, and export provenance are implemented; routes,
fanout, and automatic canon remain not-now. The historical ranking below is
retained as the decision record for why those dependencies were ordered first.

This plan refreshes the priority order after the June 2026 issue burn-down.
The remaining open GitHub issues are all sagas or epics. There are no open
`type:task` issues and no open PRs at the time of this snapshot. The next work
is important, but much of it crosses explicit Stop And Ask boundaries:
transaction and persistence behavior, schema and migrations, route/public
contracts, auth/security behavior, Blueprint apply semantics, Continuity Graph
backend storage, and Railway/live production proof.

This is not a replacement for the issues. It is a sequencing and unblock map so
future agents can ask for the right approvals instead of treating every
remaining epic as equally urgent.

## Consulted Sources

- GitHub issues: #141, #139, #138, #137, #107, #104, #86, #85, #79, #78, #56,
  #55, and #54.
- Strategy spine: `docs/product/strategy-spine.md`.
- Active plans: `plans/in-progress/production-readiness-roadmap-2026-05-09.md`,
  `plans/in-progress/program-blueprint-hydration-2026-05-02.md`, and
  `plans/in-progress/living-canon-layer-2026-05-02.md`.
- Architecture contracts:
  `docs/architecture/transactional-workflow-coverage.md`,
  `docs/architecture/data-integrity.md`,
  `docs/architecture/security-boundaries.md`, and
  `docs/architecture/continuity-graph-readiness.md`.
- Steward guidance: domain, storage, service, web, Blueprint, docs, tests, and
  plans scoped `AGENTS.md`.
- User panel: `docs/product/user-personas-panel.md` for onboarding, writer
  activation, and director trust risks.

## Ranked Backlog

| Rank | Issues | Why This Comes Next | Blocking Decisions | First Unblock Work |
| --- | --- | --- | --- | --- |
| 1 | #141, #54 | Production trust is the foundation for every real writer, director, staff, and public-preview path. Auth/session/CSRF, demo-mode posture, persistent SQLite, and Railway smoke decide whether the product can be safely shared. | Which Railway environment is authoritative; whether a Railway-connected operator is available; demo credential posture; seed/reset policy; exact volume DB path; whether live smoke may perform one protected write. | Record live Railway smoke or, if live access is unavailable, add a read-only ops checklist/comment naming the missing operator inputs and keep local auth/security gates current. |
| 2 | #56 | Transaction safety protects story-visible and staff-visible workflows from partial writes. It is the safest high-value local implementation slice because the architecture map already names focused gaps. | Approval to change service transaction/persistence behavior for application acceptance, wanted interest, and plotting-room start. No schema change is required for the first rollback probes unless implementation discovers one. | Add late-failure rollback tests and wrap the named service methods in repository transactions, then update `docs/architecture/transactional-workflow-coverage.md`. |
| 3 | #55 | Tenant integrity is the storage backstop for wrong-face, wrong-membership, wrong-community, and stale-session failures. It should follow transaction probes with diagnostics and negative tests before constraints. | Which row family gets hardened first; whether diagnostics-only work is acceptable before schema constraints; repair policy for legacy malformed rows; fresh-vs-upgraded parity scope. | Start with a diagnostic or negative-test slice for the highest-risk row family, then only add migration/constraint work after repair semantics are approved. |
| 4 | #107, #86 | Access-request lifecycle V2 directly affects real realm entry and writer safety. Current proof covers many flows, but expiration, withdrawal, reopen/reissue semantics, and applicant-visible posture need explicit policy. | Invite reissue linkage for access-request-created invitations; decline/reopen policy; expiration and withdrawal states; applicant-visible status copy; email delivery vs copy-only invitations. | Write the lifecycle state matrix and route/privacy expectations first; implement only the approved states and replay behavior. |
| 5 | #104, #78 | Staff audit and capability V2 become more important before sensitive operations expand. They also affect Blueprint apply and future Continuity review authority. | Capability storage shape; whether audit events are persistent now or service-neutral first; retention/redaction policy; whether partial staff roles become product-visible. | Spike the audit event primitive and capability storage options in docs/tests, then choose the smallest tenant-scoped persistent shape. |
| 6 | #85, #138 | Program Blueprint apply can save director labor, but it writes many realm primitives and must not land before transaction, tenant, permission, collision, and optional audit decisions are settled. | Apply modes; stale-preview fingerprint behavior; collision semantics; interim no-audit behavior if audit storage is not ready; route/control exposure. | Keep apply gated; use the existing dry-run contract to specify the exact apply modes and collision decisions before implementing mutating apply. |
| 7 | #139 | Realm opening and writer activation remain product-critical, but the hardest remaining pieces depend on production trust, access lifecycle policy, and invitation delivery decisions. | Invite delivery/resend policy; no-face continuation detail; first-scene guidance; whether email exists before alpha or copy-only remains policy. | After #107 decisions, polish the no-face and accepted-face next-move regression pack and browser QA. |
| 8 | #79, #137 | The manual Continuity Graph backend is implemented after transaction, tenant, capability, visibility, and export proof; rendered grounding remains gated. | Route timing; notification fanout/copy; retraction or supersession; public canon navigation; AI/automation remains not-now. | Use the v27 redacted read models for a separately approved rendered slice; do not infer or auto-publish canon. |

## Convergence

All consulted stewards point to the same dependency order:

- Production trust and auth/session correctness before public sharing.
- Transaction and tenant integrity before broad workflow expansion.
- Access-request lifecycle decisions before real invite-first alpha scale.
- Audit/capability storage before expanding sensitive staff operations.
- Blueprint apply only after diff, collision, tenant, transaction, and
  permission contracts are stable.
- Continuity Graph after production, privacy, transaction, provenance, and
  review gates are proven.

The user panel adds one product pressure: do not let infrastructure work erase
the new writer path. The invited applicant needs enough realm preview, first
face, wanted, application, and next-scene clarity to trust the community. That
does not outrank production trust, but it argues for keeping #107/#139 close
behind #56/#55 rather than deferring onboarding indefinitely.

## Minority Reports

- Realm Studio pressure: Blueprint apply (#85/#138) is tempting because it
  reduces director setup labor. It should stay behind transaction and tenant
  proof because a partial or cross-tenant apply would damage the exact director
  trust the feature is meant to build.
- Continuity pressure: Continuity Graph (#79/#137) is one of the clearest
  product differentiators. It should still wait because public or semi-public
  canon without source visibility, audit/review authority, and export privacy
  would create a higher-risk class of leaks than ordinary board-running data.
- Writer Network pressure: access lifecycle (#107/#86/#139) is more visible to
  early users than schema hardening. It should move immediately after the next
  local trust slices, not after every possible storage constraint is complete.

## Outstanding Questions

### Production Trust And Railway

- Which Railway service/environment is the authoritative smoke target?
- Who can authorize live reads/writes and restarts?
- What is the canonical persistent SQLite path and volume mount?
- Is demo seeding allowed in the target, and is it create-missing-only or a
  deliberate reset?
- Which demo credentials are allowed in production-like mode?
- Which protected write should the smoke use without disturbing real content?
- Where should the final smoke evidence live: operations doc, issue comment,
  or both?

### Transaction Safety

- May service methods that currently perform multi-step writes be wrapped in
  `repo.transaction()` as behavior hardening?
- Should application acceptance surface late notification failures to staff or
  convert them into a safe review-room error?
- Should wanted interest and plotting-room start use the same duplicate/replay
  posture as thread commands, or just atomic rollback for now?
- Do any of the remaining workflows require new idempotency storage, or can the
  first slice avoid schema by focusing on rollback only?

### Tenant Integrity

- Which row family is first: sessions, posts/authorship, applications, wanted
  and claims, plotting rooms, or notifications?
- Are diagnostics-only slices acceptable before constraints?
- For malformed legacy rows, should repair clear references, mark rows
  inactive, reject migration, or create an operator report only?
- How much fresh-vs-upgraded schema parity belongs in one PR before it becomes
  too broad?

### Access Request Lifecycle

- Does a reissued invitation created from an access request update the request
  linkage to the new pending invitation, keep historical linkage to the old
  revoked invitation, or record both through events only?
- Can declined requests be reopened, or must applicants submit a new request?
- Are expiration and withdrawal first-class states now or future states?
- What can an applicant see after pending, reviewed, invited, declined,
  expired, or withdrawn?
- Does email delivery exist for alpha, or is copy-only invitation delivery
  still the policy?

### Staff Audit And Capabilities

- Should V2 capability storage be role-capability rows, typed role flags, or a
  separate community-scoped grant table?
- Which actions must emit audit events in the first slice?
- Should rejected permission attempts be audited, or only accepted sensitive
  actions?
- What retention and redaction policy applies to audit event reasons?
- Are partial staff roles product-visible in alpha, or is this backend-only for
  now?

### Blueprint Apply

- Which apply modes are accepted for the first mutating slice: create-only,
  explicit update, skip existing, or dry-run only plus stale rejection?
- What is the stale-preview fingerprint contract?
- Are collisions row-family specific or one global mode?
- Should Blueprint apply wait for audit storage or document interim no-audit
  behavior?
- Which Studio route/control exposes apply, and what rendered states prove it?

### Continuity Graph

- What is the first source family: scene/thread only, or thread plus post with
  explicit `source_thread_id`?
- Which affected object families are allowed in the first slice?
- Who can review: director only, current admin, named capability, or future
  continuity steward?
- Are public canon surfaces out of scope until staff/member proposal views are
  proven?
- How should exports carry hidden source identifiers without leaking private
  text, staff notes, or cross-community references?

## Spike Queue

These are the unblocking spikes that can be done before large implementation:

1. Railway smoke readiness spike (#141/#54): produce a short operator checklist
   with environment, volume, DB path, demo mode, seed posture, smoke account,
   protected write, restart proof, and evidence destination.
2. Transaction rollback design spike (#56): inspect application acceptance,
   wanted interest, and plotting-room start for late-write injection points;
   confirm no schema/idempotency change is needed for the first rollback PR.
3. Tenant row-family selection spike (#55): rank row families by blast radius,
   current diagnostics, migration risk, and test fixture availability.
4. Access lifecycle matrix spike (#107/#86): document legal states,
   transitions, replay behavior, applicant-visible posture, and invitation
   linkage semantics before code changes.
5. Audit/capability storage spike (#104/#78): compare storage shapes and define
   the smallest event record that keeps community, actor membership, target,
   action, outcome, timestamp, and redaction safe.
6. Blueprint apply decision spike (#85): define first apply modes, collision
   policy, stale fingerprint, and no-audit stance.
7. Continuity pre-schema spike (#79/#137): turn the readiness contract into
   test names, source/affected object allow-lists, and review actor policy.

## Recommended Next Approval

Approve the #56 transaction rollback slice first:

- wrap application acceptance, wanted interest, and plotting-room start in
  service-owned repository transactions where missing
- add deterministic late-failure rollback tests for each
- avoid schema/idempotency changes in this first pass unless inspection proves
  they are required
- update `docs/architecture/transactional-workflow-coverage.md`

This moves the production-trust foundation forward using local code and tests,
does not require live Railway access, and creates proof needed by Blueprint
apply, access lifecycle hardening, Continuity, and tenant integrity work.

## Framework Adoption Priorities

The Chirp 0.8 upgrade added useful framework pressure for this backlog. Treat
these as part of the production-trust path, not as generic framework churn.

| Rank | Adoption | Issue Tie-In | Status | Next Proof |
| --- | --- | --- | --- | --- |
| 1 | Keep Chirp contract checks strict with `warnings_as_errors=True`. | #141, #54 | Adopted locally through the app check gate. | Continue running the app check in local gates and before release handoff. |
| 2 | Declare HTMX provisioning through `AppConfig(htmx=True)` instead of relying on incidental scripts. | #141, #54 | Adopted locally. | Rendered test proves pages include Chirp's HTMX marker. |
| 3 | Keep `SecurityHeadersMiddleware` registered for every app mode so mutating route checks stay clean and development mirrors production security posture. | #54 | Adopted locally; HSTS still remains environment-driven. | Security tests prove headers in development and production. |
| 4 | Use Pounce 0.8 production checks in Railway smoke and deployment readiness. | #141, #54 | Planned. | Add Pounce check output to the Railway smoke record once an operator runs the live environment. |
| 5 | Decide explicit request/upload/static streaming limits instead of relying forever on framework defaults. | #141, #54, #55 | Planned; no runtime change yet. | Add an ops/design note naming accepted body size, upload size, static streaming, and failure posture before exposing uploads or larger media. |
| 6 | Decide Railway trusted-proxy/forwarded-host settings from Chirp/Pounce config once the live deployment topology is confirmed. | #141, #54 | Planned; blocked on Railway environment details. | Record the exact proxy/hop settings in the live smoke notes. |
| 7 | Evaluate metrics, request queue, and observability hooks after the first production smoke. | #141 | Not now. | Adopt only after deciding whether metrics/Sentry/OTel endpoints are part of alpha operations. |

## Not Now

- Public self-serve registration.
- Global staff roles or global characters.
- Public Continuity/canon surfaces.
- Blueprint marketplace or arbitrary plugin system.
- AI-generated canon, moderation, or automatic summaries.
- Multi-replica SQLite or switching databases before the single-replica
  production trust gate is resolved.
