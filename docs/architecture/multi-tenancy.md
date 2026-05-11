# Multi-Tenant Strategy

Elbysodic launches with one primary community per production install, but its
database, service layer, and shared-host demo routes are tenant-aware from the
beginning.

## Decision

Build the MVP as a one-community product experience with tenant-aware
architecture and explicit shared-host routing for seeded/demo networks.

- A production install can present one primary community as the default realm.
- Local development and the Railway demo can seed several communities so
  cross-realm identity, routing, and privacy are tested before hosted
  multi-community creation exists.
- Shared-host community URLs use `/c/{community_slug}` so links resolve the
  intended realm before local slugs are looked up.
- Tenant-scoped transports include rendered HTML links and forms, redirects,
  htmx attributes, SSE fragments, and JSON payloads that carry local `href`
  values. Query strings and hidden return paths must remain intact after
  scoping.
- Malformed tenant-local paths such as `/c/{community_slug}//login` fail closed
  instead of wrapping platform/global routes inside a community prefix.
- Core forum tables include `community_id`.
- Core services accept and propagate `community_id`; it must not be assumed to
  be `1`.
- New structured primitives, including facets, materials, wanted hooks, claims,
  reserves, and applications, should follow the same rule from their first
  schema.

## Identity Model

Users are global login accounts. Memberships are community-local identities.

That means a user can later belong to multiple communities with different
usernames, display names, avatars, roles, and public identities. Permissions are
membership-based instead of user-based, so admin power never leaks across
communities.

Characters are membership-owned posting identities. They are scoped to one
community and one membership; Elbysodic does not have global characters.

Director-authored world structure is also community-local. Facet names,
application templates, wanted-hook categories, claims, reserves, and event pages
should be configurable per community rather than shared globally.

## Query Rule

Forum-domain queries should include community scope:

```sql
WHERE community_id = :community_id
```

Tests should seed multiple communities whenever possible and assert that reads
for one community do not return rows from another.

This applies to non-thread primitives too. A wanted hook, facet, material,
claim, reserve, or application in one community must not be addressable through
another community's resolver or service layer.

## Deferred Hosted Features

The MVP does not include hosted forum creation, billing, custom domains,
cross-community dashboards, community discovery, tenant analytics, or
per-community backup UI. The resolver abstraction keeps those options open.

## Deployment Modes

Elbysodic currently has three relevant modes:

- Single-community production install: one primary community is the default
  realm, while all product rows and service calls remain community-scoped.
- Local seeded network: several communities exist for QA personas, staff/member
  role differences, active-face behavior, and cross-tenant route tests.
- Shared Railway host: `/` and `/network` are platform/network surfaces, and
  canonical community links use `/c/{community_slug}` unless a community has
  its own host.

These modes share the same identity model. Users are global login accounts,
memberships are community-local, and staff power belongs to membership roles.

## First Realm Boundary

The first production realm has two distinct pre-launch states:

- No realm exists: the database has no configured community for the install.
  Public `/` and `/network` render the platform launch state. Signed-out
  visitors can log in or request access, but there is no community shell,
  roster, scene hub, or director material to enter.
- Empty configured realm: the install has a community, director role,
  director membership, and minimum settings, but it has not passed the launch
  checklist. Directors work from Studio to add scene hubs, director materials,
  intake rules, appearance, wanted hooks, and invitations.

The transition from no realm to empty configured realm is a privileged setup
operation. The current implementation is the `bootstrap-first-realm` CLI
command. It creates the first community, first global login user,
community-local director role and membership, sidebar defaults, and default
theme inside one repository transaction. It must not grant global staff power,
infer a community from an unscoped user, or create placeholder scene hubs,
threads, director materials, claims, wanted hooks, or invitations.

Empty configured realms stay backstage for public discovery. Until a realm has
a published premise material and at least one public scene hub board, logged-out
`/` and `/network` filter it out of the public catalog. Signed-in directors can
still reach their realm through their community-local membership and continue
from `/studio/launch`.

Public hosted community creation is separate future work. Until invitation,
first-face onboarding, abuse posture, email delivery, and support boundaries
are designed, the production path remains invite-style and director-led.

## Request Identity Boundary

The web layer treats community and writer identity as request-scoped, even in
development. A shared `AppServices` instance owns the repository, then
`for_request(request)` creates a scoped facade that resolves:

- community from an explicit tenant prefix, a configured host, a session
  selection, development-only identity hints, or the deployment default
- user from a production session, or development-only identity hints/fallbacks
  when development mode allows them
- membership from the resolved user inside the resolved community, with inactive
  memberships rejected

Production mode requires a valid `elbysodic_session` for normal app routes and
ignores development identity headers and unsigned development identity cookies.
Development mode can keep seed fallback identity and `/dev/personas` for QA,
but those shortcuts must not participate in production request resolution.
