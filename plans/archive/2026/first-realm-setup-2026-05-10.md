# First Realm Setup Plan

Status: archived 2026-05-18; implemented and merged
Owner: Service/auth, storage, web, tests, docs, and planning stewardship
Created: 2026-05-10
Last updated: 2026-05-12
Review by: 2026-05-24
Closure criteria: the no-realm to empty-configured-realm transition is
implemented or superseded by a narrower bootstrap plan; accepted steward
findings have proof/collateral, and remaining onboarding work is linked back
to the community creator onboarding plan.

## Archival Note

Archived after the local full test gate passed on 2026-05-18 and the remaining
onboarding work was confirmed as owned by `community-creator-onboarding` and
production-readiness follow-ups. This plan is historical context for the
bootstrap boundary.

## Implementation Update

Landed commits:

- `837b4ee` added `bootstrap-first-realm`, the service-owned
  `create_first_realm(...)` workflow, CLI tests for success/duplicate setup,
  and rollback proof for setup defaults.
- `819b1da` kept empty configured realms backstage by filtering public `/` and
  `/network` catalog entries until a realm has a published premise and public
  scene hub.
- `ac4a7a5` made `/studio/launch` director-only and redirected directors from
  an empty configured `/studio` to the launch room.
- `1eb8bce` moved the empty-community guard inside the first-realm transaction
  boundary.

The implementation now includes a persisted `community.launch_status` column
with `backstage`, `invite-only`, and `public-preview` states. Public catalog
readiness still also requires published premise and public scene-hub content so
an empty realm cannot become public-ready by status alone. CLI setup does not
update a web session because there is no web-triggered setup path yet.

Remaining onboarding work moves back to the creator-onboarding roadmap:
invitation delivery polish, no-face first-face UX polish, and hosted launch
operations proof.

## Purpose

This plan scopes the sensitive transition from **no realm exists** to **empty
configured realm**. It follows the steward synthesis requested after the first
Studio launch-room slice.

The next implementation must create a real community-local director identity
without inventing global staff power, exposing backstage realms publicly, or
leaving partial setup rows behind.

This is a Realm Studio foundation slice for the strategy spine in
`docs/product/strategy-spine.md`. It creates the authority boundary that later
creator onboarding, invitation, Blueprint, and Writer Network entry flows need.

## Steward Synthesis

Consulted stewards:

- Storage and Migration
- Service/Auth
- Web/UI
- Tests and Privacy
- Product Docs and Planning

Convergence:

- First realm setup must be explicit, privileged, and atomic.
- No implementation should call `viewer()` or render a community shell until a
  `CommunityMembership` exists.
- Public `/` and `/network` must not expose empty configured realms as public
  catalog entries.
- Empty configured realm means identity/settings only. Scene hubs, director
  materials, intake/claims, wanted hooks, invites, and launch readiness remain
  setup lanes.
- The existing `/studio/launch` room is useful after a community-local
  director membership exists, but it is not the authority for no-realm setup.

Minority reports:

- Web/UI left open a possible app-global setup route with
  `show_community_shell=False`; Service/Auth and Docs considered that higher
  risk because it needs a setup authority outside normal membership
  resolution. This plan chooses the lower-risk CLI/bootstrap path first.

## Accepted Findings

### P1: No Global Director Authority

Invariant: staff/director power belongs to `CommunityMembership`, not global
`User`.

Decision: the first implementation path is a CLI/bootstrap-owned command that
creates the first community and first director membership together. A future
web no-realm setup route is deferred until an explicit setup-authority model is
designed.

Required proof:

- production no-realm signed-out routes stay public/sparse
- no user without community membership can access Studio
- post-setup director session resolves through the created membership

Collateral:

- `docs/architecture/security-boundaries.md`
- `docs/architecture/multi-tenancy.md`
- README deployment/setup notes

### P1: Atomic First Realm Creation

Invariant: the transition must create community, director role, director
membership, session selection, and minimum defaults in one tenant-aware
operation.

Decision: add a service-owned first-realm setup command using
`repo.transaction()`. Page handlers must not assemble setup rows manually.

Required proof:

- successful setup creates exactly one community, one director role, and one
  director membership for the selected user
- every created scoped row has the new `community_id`
- duplicate/second setup is rejected
- injected failure rolls back community, role, membership, sidebar/default
  settings, launch-status rows, and session selection

Collateral:

- storage/migration notes if schema changes land
- README/operations notes for command usage

### P1: Backstage Public Visibility

Invariant: empty configured realms are backstage and must not appear as public
catalog entries.

Decision: public catalog visibility needs an explicit boundary before first
realm setup ships. This implementation uses a derived gate: a realm is public
catalog-ready only after it has a published premise material and at least one
public scene hub board. A persisted community launch status remains deferred
because that data-model change requires human confirmation before
implementation.

Required proof:

- signed-out `/` and `/network` with one backstage realm do not render realm
  name, slug, shell, roster count, wanted count, materials, or entry links
- signed-in director can see their realm continuation/setup
- ordinary member or non-member cannot see backstage setup controls
- public preview, when later implemented, exposes only approved public fields

Collateral:

- `docs/architecture/rendered-route-privacy-matrix.md`
- `docs/architecture/multi-tenancy.md`
- changelog fragment for user-visible route behavior

### P1: Session Selection After Setup

Invariant: after setup, the active request/session must resolve to the newly
created director membership.

Decision: CLI usage reports the created realm and director membership clearly.
Session selection is deferred until there is an authenticated web-triggered
setup path. Any future web setup path must update
`user_sessions.selected_community_id` and `selected_membership_id` before
redirecting to Studio.

Required proof:

- session row is selected after setup
- next GET to `/c/{slug}/studio/launch` resolves as director
- wrong-user and inactive membership selection are denied

Collateral:

- security boundaries session section

### P2: Minimum Defaults Are Setup State

Invariant: empty configured realm defaults should be created during setup, not
only as a side effect of later reads.

Decision: setup should explicitly initialize sidebar section defaults and any
minimum theme/post-style defaults that define an empty configured realm. It
must not create placeholder scene hubs or placeholder director materials.

Required proof:

- defaults exist immediately after setup before rendering Studio
- rollback test proves defaults roll back with setup failure

Collateral:

- seed/demo docs only if default catalog changes

### P2: Launch Room Authorization

Invariant: Studio setup affordances must be director/capability scoped.

Decision: the implementation PR that touches setup routing should also harden
`/studio/launch` so ordinary members either get a sanitized read-only state or
are denied. Director-only is preferred until invited-writer launch visibility
is designed.

Required proof:

- director allowed
- ordinary member denied or sanitized
- signed-out redirected
- same global user with director power in one realm but member power in
  another cannot see director setup affordances in the member realm

Collateral:

- rendered route privacy matrix

## Proposed Implementation Sequence

Local status:

- PR 1 landed as the CLI/service setup slice.
- PR 2 landed as the derived backstage visibility gate.
- PR 3 landed for Studio continuation and director-only launch access.
- PR 4 remains out of scope and should be split from the creator-onboarding
  roadmap.

### PR 1: Bootstrap-Owned Empty Realm

Goal: safely create the first empty configured realm without a web-global
director concept.

Scope:

- add a service command such as `create_first_realm(...)`
- expose it through a CLI/bootstrap command, not public web setup
- require zero existing communities before first-realm creation
- create community, director role, director membership, sidebar/default
  settings, and optional launch-status default inside `repo.transaction()`
- keep demo seed and `seed_default_community()` separate from this path

Resolved follow-up:

- persisted `community.launch_status` now exists with `backstage`,
  `invite-only`, and `public-preview`; public catalog exposure still requires
  public-ready content in addition to the status.

Proof:

- focused service/storage tests for success and rollback
- CLI smoke test for command behavior
- `init-db` remains schema-only by default
- `seed-demo` remains explicit and idempotent

Collateral:

- README deployment/setup section
- `docs/architecture/security-boundaries.md`
- `docs/architecture/multi-tenancy.md`
- changelog fragment

### PR 2: Backstage Visibility Gate

Goal: prevent empty configured realms from leaking into public discovery.

Scope:

- make `public_studio_network()` filter out backstage/non-public realms
- keep no-realm/backstage public copy sparse
- allow signed-in directors to see setup continuation for their own realm
- deny or sanitize ordinary member backstage launch controls

Proof:

- rendered tests for signed-out `/` and `/network`
- signed-in director `/network`
- ordinary member/non-member `/network`
- direct `/c/{slug}` and `/studio/launch` privacy

Collateral:

- rendered route privacy matrix
- information hierarchy update if route behavior changes

### PR 3: Session And Studio Continuation

Goal: make post-setup navigation land the first director in the right realm.

Scope:

- update selected session identity after web-authenticated setup command usage
  if a web-triggered internal path exists
- redirect to `/c/{slug}/studio/launch` after setup where applicable
- make `/studio` launch-first for empty configured realms
- harden `/studio/launch` authorization

Proof:

- session row assertions
- rendered director launch-room test
- ordinary member/cross-tenant denial or sanitized read-only test
- Chirp app check

Collateral:

- security boundaries session section
- navigation docs if Studio entry changes

### PR 4: Guided Builder Writes

Goal: only after the first-realm boundary is safe, add writes for scene hubs,
director materials, intake/claims, appearance, and invites one slice at a time.

Status: first slice landed for scene hub, premise material, application guide,
and default appearance tokens. Wanted hooks, richer intake/claim defaults,
invite management, and launch status remain community-creator onboarding work.

## Parity Matrix

| Contract | API/CLI | Programmatic | Protocol | Schema/Types | Docs | Examples | Tests |
|---|---|---|---|---|---|---|---|
| First realm setup creates community-local director identity | CLI command required | `create_first_realm` service command | no public HTTP setup in PR 1 | `community.launch_status`; community/role/membership rows scoped | README, security, multi-tenancy | CLI usage snippet if command lands | service/storage/CLI tests |
| Empty configured realm stays backstage | CLI reports backstage status | public catalog read model filters backstage | signed-out `/` and `/network` sparse | persisted status preferred; needs approval | privacy matrix, information hierarchy | none | rendered public/privacy tests |
| Session selects new director membership | optional CLI note; web-auth path if present | returns `RequestIdentityContext` | session row selected before redirect | `user_sessions.selected_*` existing fields | security boundaries | none | session/security tests |
| Studio launch room remains director-scoped | none | launch read model/policy method | `/studio/launch` denied or sanitized | no new schema | privacy matrix | none | director/member/cross-tenant rendered tests |

## Deferred Findings

- Public self-serve creator signup.
- Hosted setup authority outside community membership.
- Billing, plan limits, and custom domains.
- Invitation lifecycle and first-face handoff, except where route copy must not
  promise them yet.
- Program Blueprint Apply.
- Raw CSS/theme uploads.
- Fine-grained role capability tables.

## Required Gates

For implementation PRs in this slice:

- `uv run ruff check .`
- `uv run ruff format . --check`
- `uv run pytest -q --tb=short`
- `uv run ty check src/elbysodic/ tests/`
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`

Focused proof should include:

- `tests/test_tenant_repository.py`
- `tests/test_web_security.py`
- `tests/test_forum_slice.py`
- a focused setup service/CLI test if a new module is clearer

## Steward Notes

Accepted all P1 findings from storage, service/auth, web/UI, tests/privacy, and
docs/planning. Merged duplicate findings around public backstage visibility,
atomic setup, no global director power, and session selection. Deferred the
web-global setup route because it creates a harder setup-authority problem than
a CLI/bootstrap-owned first realm. Deferred builder writes until the first
realm boundary is implemented and proven.
