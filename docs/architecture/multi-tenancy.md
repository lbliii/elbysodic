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
- Shared-host routing uses explicit community prefixes; see
  [Route And Link Contract](#route-and-link-contract).
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

Program Blueprint Studio apply is a current-realm operation. The packet's
program slug must match the resolved community before mutation, all slug
lookups remain inside that `community_id`, and starter faces and wanted hooks
belong to the importing membership in that same community. A same-slug object
in another realm neither counts as a collision nor becomes an apply target.

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

Tenant-pair diagnostics cover stored workflow rows that join community-local
objects, including plotting-room source interests and target scenes, realm
interaction questions/options, reactions, thread reads/watches, notifications,
and authorship rows. These diagnostics exist for operations and migration
repair planning; repository and service methods still enforce tenant scope
before normal writes.
The row-family audit matrix in `docs/architecture/data-integrity.md` is the
source of truth for which tenant pairings need diagnostics, negative tests,
service proof, and storage enforcement. Schema version `23` installs
insert/update guards for every row family currently emitted by that diagnostic
and rejects a legacy upgrade before installing them when an invalid row is
present. Community reassignment is likewise blocked for guarded rows; repair is
an explicit operator decision rather than an automatic cross-realm move.
Community export is also single-community by default: the export boundary
matrix in `docs/architecture/primitives.md` names the allowed row families,
redactions, and provenance fields before any future cross-community export mode
can be proposed.

## Route And Link Contract

On shared hosts, `/` and `/network` are platform/network surfaces. A
single-community production install may present the configured community at
`/`, but shared-host community identity is always explicit.

Shared-host community URLs use `/c/{community_slug}`. The tenant prefix resolves
the intended realm before local slugs are looked up, and canonical community
links use `/c/{community_slug}` unless a community has its own host.

Tenant-scoped transports include rendered HTML links and forms, redirects, htmx
attributes, SSE fragments, and JSON payloads that carry local `href` values.
Query strings and hidden `next`, `redirect`, or `return_to` paths must remain
intact after scoping.

Tenant-prefixed requests attach Chirp's request URL scope before page handlers
run. New generated route values should use request-aware URL helpers so local
paths are born inside `/c/{community_slug}`. The response rewriter remains as a
compatibility net for existing templates and redirects until all tenant-scoped
surfaces generate scoped URLs directly.

Malformed tenant-local paths such as `/c/{community_slug}//login` fail closed
instead of wrapping platform/global routes inside a community prefix.

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
- Shared Railway host: route and link behavior follows the
  [Route And Link Contract](#route-and-link-contract).

These modes share the same identity model. Users are global login accounts,
memberships are community-local, and staff power belongs to explicit
capabilities granted to community-local membership roles. Staff audit actors
are memberships, with an optional face owned by that same membership.

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

Public discovery metadata is tenant-scoped structured data. Discovery profiles
use one row per community, and discovery tags are unique only within
`(community_id, tag_type, tag_key)`. Public Explore/search services may use
these rows only after the normal public-readiness gates pass; discovery rows on
backstage or invite-only realms do not make those realms public or searchable.

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

Web request identity uses `AppServices.for_request()` and
`RequestIdentityResolver` only. `CommunityContext()` defaults and
`resolve_current_community()` are not a request minting path.
`resolve_current_community()` remains a legacy helper; it is not called from
request resolution. Seed and session setup may still use
`DEFAULT_COMMUNITY_SLUG` / `DEFAULT_COMMUNITY_ID`. Unknown-host fallthrough
is unchanged.

Production mode requires a valid `elbysodic_session` for normal app routes and
ignores development identity headers and unsigned development identity cookies.
Development mode can keep seed fallback identity and `/dev/personas` for QA,
but those shortcuts must not participate in production request resolution.
