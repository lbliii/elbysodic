# Multi-Tenant Strategy

Elbysodic launches as a single-community forum product, but its database and
service layer are tenant-aware from the beginning.

## Decision

Build the MVP as a single-tenant product experience with tenant-aware
architecture.

- MVP users see one forum.
- MVP admins manage one forum.
- The app seeds one default community.
- Core forum tables include `community_id`.
- Core services accept `community_id` even while it is always `1`.
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

## Request Identity Boundary

The web layer treats community and writer identity as request-scoped, even in
development. A shared `AppServices` instance owns the repository, then
`for_request(request)` creates a scoped facade that resolves:

- community from an explicit development header, a configured host, or the
  seeded default community
- user from a development identity header or the seeded dev user
- membership from the resolved user inside the resolved community

This is not final authentication. It is the boundary that lets hosted programs,
membership switching, and real login sessions arrive without service methods
continuing to depend on the seeded demo identity.
