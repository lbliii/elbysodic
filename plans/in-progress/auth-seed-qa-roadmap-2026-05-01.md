# Auth And Seed QA Roadmap

Created: 2026-05-01
Last updated: 2026-05-09
Review by: 2026-05-30
Owner: Auth, seed, and browser QA stewardship
Status: mostly implemented; onboarding posture and capability granularity remain

## 2026-05-09 Verification Update

Seed personas, `/dev/personas`, local login/logout sessions, session-bound
membership selection, seed persona docs, and production dev-helper gating are
implemented and covered by focused tests. Public registration remains a
non-goal in this plan and no `/register` route exists.

The production-readiness follow-up is to decide the first shared-host
onboarding posture: login-only demo, invite/request-access, or real
registration. Startup seed persistence also needs hardening so long-lived
Railway data is not casually overwritten by demo refreshes.

## Problem

Elbysodic has the right internal identity model: global `User`,
community-local `CommunityMembership`, membership-scoped roles, and
membership-owned characters. The browser experience is still hard to test
because identity is mostly a development switcher layered over the seeded user.

That makes staff/member differences, multi-community membership, inactive
memberships, and active-face behavior technically covered in tests but awkward
to exercise manually.

## Current Boundary

- `users.password_hash` already exists, but there are no login/logout routes.
- `RequestIdentityResolver` resolves request identity from dev headers, host,
  a development identity cookie, or the seeded default.
- `/identity` can switch among memberships for the current seeded user.
- Studio edit access is correctly membership-role based through named policy
  helpers.
- Seed data has useful roles and characters, but persona intent is implicit.

## Goals

1. Make manual browser QA possible across predictable user, membership, role,
   and face combinations.
2. Keep staff power community-local. A user who is staff in one board must not
   gain staff powers elsewhere.
3. Preserve pseudonymous PBP identity: login account, community membership, and
   character face stay distinct.
4. Add enough real auth flow to test the product without committing to hosted
   account recovery, email verification, billing, or OAuth.
5. Keep all dev QA helpers visibly development-only.

## Non-Goals

- Public registration.
- Password reset and email verification.
- OAuth/social login.
- Invite-only onboarding.
- Multi-tenant billing, custom domain onboarding, or hosted community creation.
- A full permission matrix UI. V1 can keep role capabilities mapped through
  `role.is_admin` while preserving named policy helpers.

## Phase 1: Seed Personas And QA Directory

Goal: make the current dev identity switcher reliable and understandable.

Work:

- Define named seed personas with stable email, password, membership, role,
  default face, and test purpose.
- Add a `/dev/personas` or Studio-only QA panel listing seeded personas,
  community memberships, roles, active/default faces, and direct switch actions.
- Rename or supplement ambiguous seeded identities so the browser tells the
  tester what each persona is for.
- Ensure each core community has at least:
  - one director/staff membership
  - one ordinary writer with accepted faces
  - one writer with an application/draft-facing flow
  - one outsider/non-participant for private room and notification checks
  - one inactive membership for denial/recovery checks
- Keep persona seed data idempotent.

Acceptance checks:

- Browser can switch to each seeded persona without knowing database IDs.
- Studio controls are editable for staff personas and read-only for ordinary
  writers.
- Notifications, private rooms, applications, claims, wanted interest, and
  plotting rooms have at least one manual QA persona each.
- Tests assert the persona directory does not render outside development mode.

## Phase 2: Minimal Local Login Session

Goal: replace the seeded-user assumption with a real signed-in user session for
local/manual QA while keeping the same request identity boundary.

Work:

- Add `user_sessions` table with `id`, `user_id`, `token_hash`, `created_at`,
  `last_seen_at`, and optional `expires_at`/`revoked_at`.
- Add repository methods to create, look up, touch, and revoke sessions.
- Add `AuthService` methods for login, logout, and current-user resolution.
- Add `/login` and `/logout` routes with server-rendered forms.
- Resolve user from a secure-ish local session cookie first, then fall back to
  dev identity behavior only when development mode is enabled.
- Keep membership selection separate from login. Login selects the user;
  community/host and membership resolver selects the community-local identity.

Acceptance checks:

- Signing in as one seeded account shows only that user's memberships in the
  identity menu.
- Logout clears the session and returns to the intended development fallback.
- A forged membership id cannot be used by another logged-in user.
- Inactive membership cannot become the viewer.
- Session cookies use `HttpOnly`, `SameSite=Lax`, and a path scoped to the app.

## Phase 3: Persona Matrix Seed Upgrade

Goal: seed data should be a deliberate QA fixture, not just sample content.

Work:

- Add a small typed seed layer for personas, separate from world/story seed
  content.
- Document the matrix in a product or architecture page:
  - account
  - community
  - membership username/display name
  - role/capabilities
  - default face
  - relevant workflows
- Add repository helpers or seed helpers that can assert a persona exists and
  return its stable ids for tests.
- Align Program Blueprint starter communities with explicit director/member
  persona expectations.

Acceptance checks:

- Tests can ask for personas by semantic key rather than hard-coded username
  guesses.
- The matrix covers multi-community role differences: same user staff in one
  program, member in another.
- Seed reset stays idempotent and does not duplicate personas, memberships,
  characters, notifications, or rooms.

## Phase 4: Capability Granularity

Goal: make authz testable before role editing exists.

Work:

- Keep named policy helpers as the public contract.
- Decide whether V1 needs role-capability rows or whether `role.is_admin`
  remains sufficient until staff role editing.
- If adding capability rows, migrate existing admin roles into full capability
  grants and update tests for partial staff roles.
- Add manual QA personas for partial staff if and only if partial capability
  roles become real product behavior.

Acceptance checks:

- Staff actions continue to route through policy helpers.
- A partial staff persona, if introduced, can manage only its own capability
  area.
- No page handler directly checks `role.is_admin`.

## Suggested Persona Matrix

| Key | Account | Community | Membership | Role | Face | QA Purpose |
| --- | --- | --- | --- | --- | --- | --- |
| `xmen_writer` | `writer@example.com` | X-Men Apocalypse | `starlane` | Member | Rogue | ordinary writer, active face, queue, thread posting |
| `xmen_staff` | `moira@example.com` | X-Men Apocalypse | `moira` | Staff | Moira | Studio, applications, claims, private staff rooms |
| `xmen_mod` | `alex@example.com` | X-Men Apocalypse | `alex` | Moderator | Cyclops | thread lifecycle, moderation controls |
| `xmen_partner` | `charlie@example.com` | X-Men Apocalypse | `charlie` | Member | Xavier | wanted/plotting-room counterparty |
| `xmen_applicant` | `mira@example.com` | X-Men Apocalypse | `mira` | Member | Kitty | application and revision workflow |
| `hp_director` | `writer@example.com` | HP Universe | `starlane` | Director | Rowan Ash | same login with staff power in another community |
| `jp_director` | `writer@example.com` | Jurassic Park Universe | `starlane` | Director | Dr. Mara Vale | visual/theme and director controls |
| `nyc_writer` | `writer@example.com` | RL NYC | `starlane` | Member | Mina Park | same login without staff power in another community |
| `smalltown_writer` | `writer@example.com` | RL Small Town | `starlane` | Member | June Calloway | low-stakes writer community |

## Ordering

1. Phase 1 first. It gives immediate browser QA value without schema risk.
2. Phase 2 next. Login/session should reuse the same resolver instead of
   replacing it.
3. Phase 3 after login shape is clear, so seed personas match how testers enter
   the app.
4. Phase 4 only when staff role differences become product-visible.

## Risks

- Dev helpers accidentally becoming production UI. Gate them through explicit
  development mode and tests.
- Confusing user, membership, and face labels. The UI should call them account,
  membership, and wearing/current face consistently.
- Overbuilding auth before hosted product needs are clear. Keep V1 local and
  session-based.
- Letting a global user carry staff power across communities. Tests must cover
  same-user, different-community role differences.

## Steward Notes

Consulted:

- root `AGENTS.md`: global user, community-local membership, no global
  characters, staff power belongs to membership.
- `src/elbysodic/services/AGENTS.md`: request identity, policy helpers, and
  inactive-membership boundaries.
- `src/elbysodic/web/AGENTS.md`: server-rendered flows and no private data
  leakage into rendered surfaces.
- `src/elbysodic/db/AGENTS.md`: idempotent seed data and tenant-scoped storage.
- `src/elbysodic/domain/AGENTS.md`: identity primitives remain explicit.
- `docs/architecture/multi-tenancy.md` and
  `docs/architecture/security-boundaries.md`: request identity is current
  scaffolding, not final authentication.

Open follow-up:

- Decide exact development-mode flag name before building `/dev/personas`.
- Decide whether to use a simple standard-library password hash first or bring
  in a dedicated password hashing dependency.
