# Railway Auth Hardening Plan

Created: 2026-05-02
Last updated: 2026-05-02
Review by: 2026-05-09
Owner: Auth, service, web, and deployment stewardship
Status: in-progress

## Problem

Elbysodic is close to being deployable on Railway as a long-lived demo, but the
current auth boundary is still shaped for local browser QA. The app has real
pieces of a server-side auth model: users, community memberships, roles,
characters, session rows, password hashes, service-layer policies, and
tenant-aware repositories. The launch risk is that development identity
shortcuts still participate in request identity resolution.

Before sharing a Railway URL widely, production mode must stop trusting:

- `x-elbysodic-user-id`
- `x-elbysodic-membership-id`
- `x-elbysodic-community`
- unsigned `elbysodic_dev_identity`
- seeded fallback identity for mutation-capable requests

The goal is not to build the final hosted auth product. The goal is to make a
Railway deployment safe enough to inspect, use for a real demo, and keep alive
without giving anonymous visitors staff or writer powers by accident.

## Steward Consultation Rollup

Checkout freshness: ran `git status --short --branch`, fetched `origin`, and
created this plan branch from latest `origin/main` after the Railway
production-readiness merge. The separate volume/dependency fix branch
`codex/railway-volume-persistence` remains a prerequisite for durable Railway
state and registry-only builds.

Consulted stewards:

| Steward | Top Priority | Confidence | Evidence | Dependencies / Ordering | Risks | Not Now | Opportunities |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Root product constitution | Preserve user/membership/face separation while making launch safe. | High | Root guide says users are global, permissions belong to `CommunityMembership`, and staff power is not global. | Resolver work must come before public demo sharing. | Flattening identity into user-level auth would break PBP pseudonymity. | Hosted billing, OAuth, public registration. | Auth can reinforce the PBP face/current-lens model. |
| Docs / architecture | Document production auth as current behavior, not aspiration. | High | `docs/architecture/security-boundaries.md` calls current request identity scaffolding and points to rendered privacy matrix. | Update docs with implementation PRs, not only this plan. | Prose that weakens tenant boundaries. | Generic SaaS auth docs. | Add a crisp production auth boundary doc. |
| Package / tooling | Keep Railway config, CLI, env vars, and README aligned. | High | CLI now supports `--no-debug`; Railway uses config-as-code. Chirp `AppConfig` has `secret_key`, `allowed_hosts`, and production safety checks. | Deployment config first, then auth runtime behavior. | Hidden env requirements causing failed deploys. | Packaging experiments. | Use one env-driven app config path for local and Railway. |
| Service layer | Split development identity resolution from production identity resolution. | Very high | `RequestIdentityResolver` currently accepts dev headers and unsigned dev identity cookie; service methods already centralize policies. | Must land before CSRF is considered sufficient. | Any production path that resolves a membership without a session can mutate data. | New role editor. | Keep all authz checks in services/policies instead of page-local guards. |
| Web / rendering | Server-rendered Chirp is a good fit if forms get CSRF and cookies become secure. | High | Chirp includes `SessionMiddleware`, `CSRFMiddleware`, `SetCookie(secure=...)`, allowed hosts, and template CSRF helpers. | Secret/session middleware before CSRF fields and tests. | Missing CSRF tokens can break all POST routes at once. | SPA/client auth. | Server-rendered forms make auth and CSRF easier than a client API split. |
| Storage / migrations | Persist session identity selection server-side instead of trusting a client cookie. | High | `user_sessions` exists with token hash, last seen, expiry, revocation. | Migration needed if session rows store selected membership/community. | Cross-community membership selection if foreign-key/check logic is weak. | Full account recovery schema. | Add session preference columns or table with tenant-aware tests. |
| Domain model | Do not introduce global characters or user-level staff power. | High | Domain steward protects explicit User, CommunityMembership, Character primitives. | Domain changes only if session selection needs a typed record. | Confusing current face vs current membership. | Capability-row domain expansion unless staff roles become visible. | A typed auth context can clarify writer vs face in read models. |
| Test steward | Prove rendered and POST boundaries, not just helper functions. | Very high | Privacy matrix requires rendered route checks for private/staff/member surfaces. Existing tests already cover forged cookies and dev persona gating. | Tests should drive each phase. | False confidence if tests only hit repository methods. | Large snapshots. | Add reusable CSRF/login helpers for future workflow tests. |
| Blueprint steward | Keep blueprint and seed import out of auth hardening except demo account posture. | Medium | Blueprint scope is director-authored starter packets, not login. | Only touch if seed persona creation changes. | Accidentally tying import/hydration to staff session state. | Blueprint auth/permissions UI. | Future blueprint install could create initial director membership intentionally. |

Weighted recommendation: implement production auth hardening before sharing the
Railway app beyond trusted collaborators. The highest-weight convergence is
service-layer identity trust, followed by CSRF/secure cookies, then deployment
configuration and demo account posture.

## Product Decision

Use an authenticated-only first Railway demo.

That means:

- `/health`, static assets, `/login`, and `/logout` remain public enough to
  operate.
- Forum, Studio, writing, and identity routes require a valid login session in
  production mode.
- Anonymous read-only browsing is explicitly deferred. It is desirable later,
  but it requires an intentional anonymous viewer/read model so we do not
  accidentally expose member/staff/private data through the seeded fallback.

This is the smallest safe launch shape. It preserves the current PBP identity
model and avoids a large anonymous-permission refactor before the first Railway
demo.

## Phases

### Phase 0: Deployment Guardrails

Goal: keep the live Railway surface controlled while auth hardening is in
progress.

Work:

- Merge or include the registry-dependency and Railway-volume work from
  `codex/railway-volume-persistence`.
- Attach a Railway Volume and confirm the app uses
  `$RAILWAY_VOLUME_MOUNT_PATH/elbysodic.sqlite3`.
- Treat the Railway URL as trusted-collaborator-only until Phase 2 and Phase 4
  are complete.
- Decide the demo account posture:
  - private demo: known seed credentials are acceptable for collaborators
  - public demo: staff seed credentials must be rotated, disabled, or generated
    out-of-band

Acceptance checks:

- Railway build passes `uv sync --locked --no-dev --no-install-project`.
- `/health` passes.
- Volume-backed SQLite persists across redeploy.

### Phase 1: Production App Config

Goal: make production security settings explicit and testable.

Work:

- Add Elbysodic env resolution around Chirp `AppConfig`:
  - `ELBYSODIC_ENV` or equivalent production mode flag
  - `ELBYSODIC_SECRET_KEY`
  - `ELBYSODIC_ALLOWED_HOSTS`
  - optional strict transport security setting
- In non-debug production, fail fast when `ELBYSODIC_SECRET_KEY` is missing or
  too short.
- Configure host allow-listing for Railway's public domain and future custom
  domains. Keep localhost behavior development-only.
- Centralize cookie options in one helper, including `Secure`, `HttpOnly`,
  `SameSite=Lax`, and path.
- Add tests for app config resolution, missing secret behavior, cookie flags,
  and allowed-host parsing.

Acceptance checks:

- `create_app(debug=False)` in production mode has a non-empty secret key.
- Session-related cookies set `Secure` in production and not in local HTTP
  development.
- Unknown production hosts are rejected once an allowed-host list is configured.

### Phase 2: Production Request Identity

Goal: remove all development identity trust from production.

Work:

- Introduce an explicit auth mode for request identity:
  - development mode can keep seed fallback, dev headers, `/dev/personas`, and
    `elbysodic_dev_identity`
  - production mode ignores dev headers and unsigned dev identity cookies
- Require a valid `elbysodic_session` for all normal app routes in production.
  Exempt only `/health`, static assets, `/login`, and logout handling.
- Update `RequestIdentityResolver` so production user identity comes from the
  session only.
- Ensure inactive memberships cannot become the viewer in either mode.
- Keep service-layer policy helpers as the authorization boundary; page handlers
  should not grow ad hoc role checks.

Acceptance checks:

- In production mode, forged dev headers do not change the viewer.
- In production mode, forged `elbysodic_dev_identity` does not change the
  viewer.
- Without a valid session, GET routes redirect to `/login` or return an
  intentional 401/403 shape.
- Without a valid session, POST routes cannot mutate data.
- `/dev/personas` is 404 in production.

### Phase 3: Server-Side Membership Selection

Goal: make current membership/community selection session-bound instead of
client-trusted.

Work:

- Store selected membership and selected community server-side. Candidate
  implementations:
  - add nullable `selected_community_id` and `selected_membership_id` to
    `user_sessions`
  - or add a `user_session_identity` table keyed by session id
- Update login to choose a default active membership for the resolved host or
  default community.
- Update `/identity` membership switching to validate the membership belongs to
  the session user, then update server-side session selection.
- Keep active/default face selection as membership-owned state; do not make
  characters global or session-global.
- Keep the dev identity cookie only for development mode, or replace it with
  the same server-side selection path.

Acceptance checks:

- Same global user can be staff in HP/Jurassic Park and ordinary member
  elsewhere without role leakage.
- Forged membership ids cannot switch the viewer.
- Cross-community route recovery does not leak private bodies or staff controls.
- Logout revokes session and clears any selected identity state.

### Phase 4: CSRF For Server-Rendered Writes

Goal: protect all state-changing forms before public use.

Work:

- Add Chirp `SessionMiddleware` with the production secret.
- Add Chirp `CSRFMiddleware` after session middleware.
- Register/use Chirp `csrf_field()` and `csrf_token()` instead of the current
  Chirp-UI empty fallback.
- Add `{{ csrf_field() }}` to every server-rendered POST form:
  - login/logout
  - identity switching/current face
  - composer reply/start/edit
  - thread lifecycle controls
  - Studio forms
  - applications, claims, wanted, plot hooks, plotting rooms, interactions
- Add a test helper that fetches a form, extracts `_csrf_token`, and submits it.
- Update POST tests to prove missing/invalid tokens fail and valid tokens pass.

Acceptance checks:

- App contract check no longer warns that `csrf_token()` has no real provider.
- Mutating POST without CSRF returns 403.
- Existing writer/staff workflows pass with valid CSRF.

### Phase 5: Demo Account Posture

Goal: avoid shipping public staff credentials by accident.

Work:

- Decide whether production Railway runs in `demo` mode.
- If demo mode is on:
  - seed accounts can remain, but document them as demo-only
  - staff credentials should be rotated out of the public README or generated
    via Railway variables
  - consider ordinary-writer-only public credentials and staff credentials kept
    private
- If demo mode is off:
  - do not accept `dev-password-hash` in production
  - add an explicit admin/bootstrap command or env-driven first admin creation
- Add tests for production password behavior.

Acceptance checks:

- Production mode cannot log in with `dev-password-hash` unless demo mode is
  explicitly enabled.
- Staff access on Railway is intentional and documented outside public code if
  needed.

### Phase 6: Launch Hardening Extras

Goal: reduce common public-deploy risks after the core auth boundary is fixed.

Work:

- Add login throttling or rate limiting. Chirp has production rate-limit
  configuration; decide whether global limits are enough or login needs a small
  application-level throttle.
- Add security headers:
  - HSTS when served behind HTTPS
  - strict allowed hosts
  - CSP nonce if inline behavior requires it
- Add structured auth/security events for:
  - failed login
  - revoked/expired session
  - forbidden staff action
  - CSRF rejection
- Confirm SQLite-on-volume operational constraints:
  - one Railway replica
  - backups enabled
  - no multi-writer deployment pattern

Acceptance checks:

- Repeated login failures are observable and limited.
- Security headers are visible in a Railway smoke check.
- Deployment docs mention single-replica SQLite volume constraints.

### Phase 7: Documentation And QA

Goal: leave future agents with a clear production auth contract.

Work:

- Update `docs/architecture/security-boundaries.md` with the production request
  identity model.
- Update `docs/architecture/multi-tenancy.md` request identity section.
- Update `docs/architecture/rendered-route-privacy-matrix.md` with auth-mode
  route expectations.
- Update `docs/architecture/seed-personas.md` to distinguish local QA personas
  from production demo accounts.
- Add a short Railway operations checklist to README or a deployment doc.
- Run one browser smoke on Railway after merge:
  - health
  - login
  - writer view
  - staff view
  - forbidden forged identity attempt if practical

Acceptance checks:

- Docs and tests describe the same production behavior.
- Steward Notes in the implementation PR name consulted guides and remaining
  auth risks.

## Dependency Order

1. Merge deployment foundation: Railway start command, Python version,
   registry lockfile, and Railway volume path.
2. Land Phase 1 config/cookie helpers.
3. Land Phase 2 production resolver and login gate.
4. Land Phase 3 session-bound membership selection.
5. Land Phase 4 CSRF across all writes.
6. Decide Phase 5 demo account posture before public sharing.
7. Add Phase 6 hardening once the core boundary works.
8. Close with Phase 7 docs and Railway smoke.

Phase 1 and Phase 2 can be split into separate PRs, but Phase 2 should not be
considered complete until tests prove forged dev identity is ignored in
production. Phase 4 may be the largest PR because every POST test and form has
to learn CSRF.

## Risks And Mitigations

- Risk: gating all app routes behind login makes the demo less browsable.
  Mitigation: accept this for first safe launch; add intentional anonymous
  read-only mode later.
- Risk: CSRF rollout breaks many workflows.
  Mitigation: add the test helper first, convert route families incrementally,
  and keep one focused acceptance test per major workflow.
- Risk: production mode accidentally uses the seeded default identity.
  Mitigation: tests for unauthenticated GET and POST in production mode.
- Risk: staff power leaks across communities for same global user.
  Mitigation: keep membership-scoped role resolution and same-user
  multi-community tests.
- Risk: demo credentials become de facto production credentials.
  Mitigation: explicit demo mode and production rejection of `dev-password-hash`
  unless demo mode is enabled.
- Risk: SQLite volume creates operational assumptions.
  Mitigation: one replica, backups, and documented migration/export path.

## Tempting Not-Now Items

- OAuth/social login.
- Public registration.
- Email verification and password reset.
- Two-factor authentication.
- Invite and waitlist flows.
- Role/capability editing UI.
- Anonymous public read-only browsing.
- Billing, hosted community creation, and custom-domain onboarding.
- Full audit dashboard.

These are real future needs, but they should not block a safe first Railway
demo.

## Suggested Next Checks

- Inspect Chirp `SessionMiddleware` and `CSRFMiddleware` behavior against the
  published package versions in `uv.lock`.
- Add a spike test that creates a production app with session + CSRF middleware
  and verifies one form POST.
- Inventory every POST route and template form before Phase 4.
- Decide whether Phase 3 stores selected identity on `user_sessions` or a
  separate table.
- Decide the Railway demo credential policy before sharing the URL.

## Closure Criteria

This plan can close when:

- production mode no longer trusts dev headers or unsigned dev identity cookies
- production app routes require a valid session unless explicitly public
- current membership selection is session-bound and server-validated
- all mutating forms require CSRF
- production cookies are secure
- seed/demo credentials are intentionally configured
- rendered privacy tests cover the launch-critical route families
- Railway deployment has been smoke-tested after merge

When closed, archive this plan or replace it with a narrower account-onboarding
or anonymous-read-only plan.
