# ADR 0005: Keep tenant authorization service-owned during AuthSpec migration

- **Status:** Proposed
- **Date:** 2026-09-23
- **Saga:** GitHub [#215](https://github.com/lbliii/elbysodic/issues/215)
- **Epic:** GitHub [#224](https://github.com/lbliii/elbysodic/issues/224)
- **Design:** GitHub [#374](https://github.com/lbliii/elbysodic/issues/374)

## Context

Chirp `AuthSpec` is a pre-handler route gate. Its authenticated principal is
`request.user`, which Elbysodic intentionally adapts to the global login
`User`. Community, membership, role, active-face, and record visibility are
resolved later through the request tenant and `AppServices.viewer()`. The
community-local capability checks live in `services/policies.py`; scoped data
reads and writes remain in services and tenant-aware repositories.

The current production `RequireLoginMiddleware` also owns the public-route
allowlist and signed-out tenant-preview exceptions. Replacing it wholesale with
route metadata would duplicate and risk changing those public and caching
contracts. A global-user permission or generic Chirp access-grant check cannot
represent Elbysodic's tenant and membership boundaries.

## Decision

1. **Keep the DB-backed Elbysodic session as login authority.** The adapter
   continues to expose only the global account through `request.user`.
   `RequireLoginMiddleware` remains responsible for production login redirects,
   public paths, and tenant-preview exceptions during this migration.
2. **Keep `AppServices.viewer()` and `services/policies.py` authoritative for
   community-local identity and staff capabilities.** A route `AuthSpec` may
   only add a pre-handler gate whose registered named policy resolves the
   current request's viewer and delegates to the existing named capability
   helper. Do not encode membership or staff power in
   `AuthSpec.permissions` on the global user.
3. **Migrate one route family at a time.** The first slice is `GET` and `POST`
   `/studio/discovery`, shadow-gated by `manage_world`. Its GET and update
   service methods already require that capability, and the profile is scoped
   to the resolved community. Keep both service checks in place; this first
   slice does not remove or relocate authorization.
4. **Preserve development identity behavior.** `AuthSpec` always requires an
   authenticated `request.user`, while local demo-persona requests may resolve
   without a signed login session. The first route metadata is therefore active
   only for production-like environments, selected by dynamic `_meta.py`
   using a registered `WebSecurityConfig` provider. Development identity
   headers, cookies, and seeded fallback behavior remain unchanged.
5. **Do not use generic per-record access grants for Elbysodic records.** The
   generic grant model is keyed by global user/group principals and does not
   carry `community_id`, membership ownership, or character authorship. Keep
   record, room, application, notification, and private-board visibility in
   existing service policies and tenant-aware repository queries. Any future
   grant model needs a separate design with explicit tenant and actor semantics.
6. **Keep existing failure and lifecycle boundaries.** An unauthenticated
   production request to a private route continues to redirect through
   `RequireLoginMiddleware`; a logged-in account without the route capability
   gets a generic 403 before the handler; route policy names must pass Chirp's
   startup `auth_spec` contract check. Service checks, CSRF, and durable
   community-local staff audit events remain in force. Chirp's optional generic
   security-event sink is not a replacement for the Elbysodic staff audit
   trail.
7. **Do not use route metadata to authorize a long-lived stream.** SSE room
   reads continue to reload active membership, role, room, and participants on
   each poll. Losing membership or participation must stop new private events
   even after the stream was opened.

## Evidence and parity matrix

The app pins `bengal-chirp>=0.10.0`; the locally inspected `v0.10.0`
source at commit `3f80f81d587e81a72dfacc7f7148e79bf1134d99` contains the
dynamic metadata and typed provider-injection seam used by this proposal:
[`shell_context.py`](https://github.com/lbliii/chirp/blob/3f80f81d587e81a72dfacc7f7148e79bf1134d99/src/chirp/pages/shell_context.py#L15-L80),
[`registry.py`](https://github.com/lbliii/chirp/blob/3f80f81d587e81a72dfacc7f7148e79bf1134d99/src/chirp/app/registry.py#L340-L370),
and [`App.provide` / named policy registration](https://github.com/lbliii/chirp/blob/3f80f81d587e81a72dfacc7f7148e79bf1134d99/src/chirp/app/__init__.py#L236-L237). This is source-level evidence for the pinned release, not a separate
compatibility guarantee. Elbysodic must register the `WebSecurityConfig`
provider before dynamic metadata can resolve it, then prove production-only
selection and local demo-persona parity with app-level tests. That provider is
not registered today.

This ADR remains proposed until the migration owner and security/product
reviewer accept the authority boundary and the first implementation leaf is
approved with its parity proof.

| Boundary | Current authority | `AuthSpec` role in this migration | Evidence / required proof |
|---|---|---|---|
| Public catalog and signed-out tenant preview | `RequireLoginMiddleware` public allowlist plus service-owned public read models | No gate on public routes; preserve GET/HEAD-only tenant previews | `test_production_routes_require_session`, `test_anonymous_public_catalog_gets_do_not_issue_or_vary_on_session_cookie`, rendered-route privacy matrix |
| Global login and stale/revoked session | DB-backed `elbysodic_session`, `AppSessionIdentityMiddleware`, `RequireLoginMiddleware` | Route metadata does not replace session validation or redirect behavior | `test_request_user_exposes_global_account_before_membership_resolution`, production session/login and stale-session tests |
| Community and membership selection | Tenant prefix first, then `AppServices.viewer()` verifies same-user membership, active state, and role/community match | Named policy obtains the request viewer; never infer tenant identity from `request.user` | `test_request_identity_does_not_leak_roles_between_communities`, `test_production_tenant_prefix_overrides_session_selected_community`, inactive and cross-user membership tests |
| Staff capability | Existing `services/policies.py` helper against the resolved membership and role | Shadow gate only; delegate to the same helper and keep service checks | Director/member `/studio/discovery` tests; add a production test for the route gate on GET and POST |
| Record-level privacy | Service visibility and tenant-scoped repository access | No generic grants and no removal of service checks | Existing application, plotting-room, notification, board, and public-preview privacy tests |
| CSRF and mutations | Chirp CSRF middleware plus service command validation | Auth gate runs before the handler; it does not replace CSRF or command checks | Production CSRF tests plus valid/invalid `/studio/discovery` POST proof |
| Long-lived SSE audience | Revalidated service poll on each event batch | No route-level replacement; initial gate alone is insufficient | `test_local_queue_message_rechecks_access_before_rendering` and `docs/architecture/stream-read-contracts.md` |

## First implementation leaf

Create one `type:leaf` under #224 after this design closes:

- **Outcome:** Add a production-only `AuthSpec(policy=...)` shadow gate for
  `/studio/discovery` GET/POST that calls the existing `manage_world` policy,
  with service-side authorization unchanged.
- **Owned paths:**
  - `src/elbysodic/web/app.py` — one named policy and the security-config
    provider, with a narrow carve-out in this megafile.
  - `src/elbysodic/web/pages/studio/discovery/_meta.py`
  - `tests/test_web_security.py`
  - `tests/test_forum_slice.py`
- **Acceptance:** `uv run pytest` over the two discovery-profile route tests,
  the production login/inactive-membership/tenant-prefix tests, and
  `tests/test_stream_read_efficiency.py::test_local_queue_message_rechecks_access_before_rendering`.
  The new production route proof must cover signed-out redirect, director allow,
  member deny with no staff data, same global account with different
  community-local roles, inactive membership deny, CSRF preservation, and
  tenant-prefix selection. Local demo-persona discovery access must remain
  unchanged. The stream test remains a no-change guard.
- **Out of scope:** Removing `RequireLoginMiddleware`; changing any service or
  repository policy; changing CSRF, session, public-preview, SSE, or staff-audit
  behavior; applying global permission names to memberships; introducing
  per-record grants.

No later route family becomes ready by implication. Each must name its
community-local policy, public exception, record-level service checks, and
parity proof before adding route metadata.

## Consequences

- Route metadata may provide an early, declarative policy gate, but does not
  become the source of tenant identity or record visibility.
- The first route demonstrates parity while service checks remain in place;
  no broad cutover is authorized by this ADR.
- Stream authorization remains time-sensitive and service-owned.

## Non-goals

- Replacing the app session or changing `request.user` identity shape
- Moving membership or role state onto global users
- Replacing service policies with Chirp access grants
- Reworking all route middleware or adding permissions to public routes
