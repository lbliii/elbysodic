# Security And Tenant Boundaries

Elbysodic is a single-community MVP with multi-tenant architecture. The app
should behave as if multiple communities already exist, because that is how we
avoid data leaks when hosted or multi-community features arrive later.

## Boundary Model

- `User` is global and private.
- `CommunityMembership` is the writer identity inside one community.
- `Character` is a public face owned by one membership in one community.
- Staff power belongs to membership and role context, never directly to the
  global user.
- Product objects such as boards, threads, posts, facets, materials, wanted
  hooks, applications, reserves, and plotting rooms are community-scoped.

## Repository Rules

Repository methods that read or write product objects should accept
`community_id` and include it in the query. Writes that join two scoped objects
must resolve both objects through the same community before inserting the join
row.

When a workflow stores both writer and character identity, validate both:

- membership id for ownership and permission checks
- character id for public authorship or story context
- character membership id when a character is claimed by a writer action

Raise `TenantBoundaryError` when a write would connect rows across communities
or attach a character to the wrong membership.

## Permission Rules

Page handlers should not make permission decisions directly. They should call
service methods, and services should route decisions through policy helpers.

Policy checks expose named capabilities, even while the MVP still maps them to
admin roles:

- `manage_threads`
- `manage_world`
- `manage_applications`
- `manage_casting`
- `manage_navigation`

Named capabilities should remain membership-scoped. A global user with staff
power in one community must not gain staff power in another.

When adding a staff workflow, add or reuse a named capability in
`src/elbysodic/services/policies.py` and route service-layer checks through the
helper. Avoid direct `role.is_admin` checks outside the policy module.

V1 keeps `roles.is_admin` as the storage shorthand for "has every current
staff capability." Do not add role-capability rows until partial staff roles
become product-visible. Even while storage is coarse, page handlers and
workflow services should still depend on named policy helpers rather than the
storage flag.

## Production Request Identity

Production mode is enabled with `ELBYSODIC_ENV=production` or `staging`.
Production request identity is session-backed:

- normal app routes require a valid `elbysodic_session`
- `/health`, `/login`, `/logout`, `/`, `/network`, `/request-access`, and static assets are public
- dev identity headers are ignored
- unsigned `elbysodic_dev_identity` cookies are ignored and are not issued
- `/dev/personas` is unavailable even when `ELBYSODIC_DEV_TOOLS` is set

The logged-out `/` and `/network` surfaces use public catalog read models.
They can show realm names, public premise or current-event summaries, public
media, roster counts, and wanted-hook counts. They must not render membership
names, active faces, unread counts, staff signals, identity switch forms, or
private writer queues.

First-realm creation is not a public web permission. The current setup path is
the operator-only `bootstrap-first-realm` CLI command, which creates a global
login user plus a community-local director membership in the same transaction.
An empty configured realm remains backstage in public catalog read models until
it has public-ready content. Directors see setup continuation through their own
membership; ordinary members cannot enter `/studio/launch`.

Current community and membership selection is stored on `user_sessions` as
`selected_community_id` and `selected_membership_id`. Switching membership
validates that the target membership belongs to the session user and is active
before updating the session row. Staff power continues to resolve from the
selected membership's community-local role.

Development mode can still use seed fallback identity, dev headers,
`elbysodic_dev_identity`, and the `/dev/personas` switcher for browser QA.
Those shortcuts must not participate in production request resolution.

Production also requires `ELBYSODIC_SECRET_KEY` with at least 32 characters.
Seed `dev-password-hash` accounts are accepted in production only when
`ELBYSODIC_DEMO_MODE=1` is set; otherwise those hashes are rejected.

Production mutating requests are protected by Chirp session-backed CSRF.
Rendered POST form templates include the active CSRF field explicitly, and
unsafe methods are rejected when the token is missing or invalid.

Production responses also set a Content Security Policy sized to the current
server-rendered Chirp and Chirp-UI stack. The policy keeps framing, object,
base URI, image, and connection boundaries narrow, while allowing inline styles
and Alpine expression evaluation until those upstream-rendered shell, theme,
and progressive-enhancement patterns are replaced with CSP-stricter assets.

## Nullable Identity Shapes

Some PBP workflows support a character-backed path and a prospective-character
path. Examples include wanted interest and plotting rooms. These flows need
partial unique indexes rather than one broad unique constraint with nullable
columns, because SQLite allows multiple `NULL` values in a unique constraint.

Use separate uniqueness rules for:

- existing character identity
- prospective/new-character identity
- membership-only ownership when no character is present

## Tests To Add With New Features

For every new first-class primitive, add at least one boundary test that seeds
two communities and proves:

- community A cannot read community B's object through an A-scoped resolver
- a membership cannot act with a character owned by another membership
- a non-staff membership cannot use staff-only actions
- an inactive membership cannot act
- nullable/prospective identity flows cannot create duplicate live rows

Rendered page tests should cover privacy when a workflow exposes a new route or
surface. Repository-only tests are enough for low-level constraints, but not
for user-visible private rooms, staff desks, or notification inboxes.

Use `docs/architecture/rendered-route-privacy-matrix.md` as the standing route
checklist for rendered privacy coverage. Update it when adding a new route
family, identity shape, or user-visible scoped data surface.

Use `docs/architecture/seed-personas.md` when a test or browser QA pass needs a
stable seeded account, membership, role, and active-face combination.
