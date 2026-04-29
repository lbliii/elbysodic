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
