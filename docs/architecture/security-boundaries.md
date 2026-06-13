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

Policy diagnostics use the same named capability contract. When a maintainer or
future recovery surface needs to explain a denial, use the service-owned
capability diagnostic helper rather than inspecting role fields in a page or
template. Diagnostics may name the requested capability and a generic reason,
such as inactive membership, missing role, cross-community role, mismatched
role assignment, or role lacking staff power. They must not include private
target details, staff notes, application body, access-request notes, raw
tokens, or role/member display names.

V1 keeps `roles.is_admin` as the storage shorthand for "has every current
staff capability." Do not add role-capability rows until partial staff roles
become product-visible. Even while storage is coarse, page handlers and
workflow services should still depend on named policy helpers rather than the
storage flag.

`src/elbysodic/services/policies.py` owns the current staff capability contract
registry. Each entry names the helper, V1 storage shorthand, membership actor
contract, protected workflow families, and candidate audit-event actions for
future storage. This is an audit map, not a role editor: it must not introduce
global user staff power, page-local checks, or public audit output.

## Production Request Identity

Production mode is enabled with `ELBYSODIC_ENV=production` or `staging`.
Production request identity is session-backed:

- normal app routes require a valid `elbysodic_session`
- `/health`, `/login`, `/logout`, `/`, `/network`, `/search`,
  `/request-access`, `/invite/{token}`, and static assets are public
- signed-out shared-host tenant preview routes are public for `GET`/`HEAD` only:
  `/c/{community}/`, `/c/{community}/world`,
  `/c/{community}/world/{material_slug}`, `/c/{community}/wanted`,
  `/c/{community}/wanted/{wanted_slug}`, `/c/{community}/search`, and
  `/c/{community}/request-access`
- dev identity headers are ignored
- unsigned `elbysodic_dev_identity` cookies are ignored and are not issued
- `/dev/personas` is unavailable even when `ELBYSODIC_DEV_TOOLS` is set
- logout revokes the stored session and clears its selected community and
  membership so stale cookies cannot carry forward active realm identity state

`auth_trust_posture()` in `src/elbysodic/services/auth.py` provides a redacted
operations diagnostic for this posture. It reports environment, production
mode, demo-mode seed password posture, secret-key presence/minimum status,
session cookie name, session TTL, development identity availability, and
session-required status without exposing secret values, token hashes, raw
cookies, account emails, membership names, or private identity state.

The logged-out `/` and `/network` surfaces use public catalog read models.
They can show realm names, public premise or current-event summaries, public
media, roster counts, and wanted-hook counts. They must not render membership
names, active faces, unread counts, staff signals, identity switch forms, or
private writer queues.

Signed-out tenant previews use the same posture inside one public-ready realm.
They can show published guidebook materials, public premise/current-event
summaries, non-archived wanted hooks, public media, face counts, and
request-access/login calls to action. They must not render draft materials,
private or raw scene/thread activity, wanted interest notes, reserves, plotting
room links, lifecycle controls, identity menus, unread counts, or any mutating
forms. Raising interest, reserving, applying, replying, watching, and staff
workflow actions still require a valid session and community-local membership.

A signed-in account without a membership in the current community keeps the
same public-safe preview boundary. The shell may identify the global account
and offer request-access or network-return actions, but it must not render the
community shell, Desk, active face, unread counts, private continuation, or
staff controls.

Community access requests are interest records, not permission records.
`CommunityAccessRequest` rows are scoped by `community_id` and may include the
writer's email, display name, face concept, wanted-hook interest, and private
notes for directors. When the visitor is already signed in to Elbysodic, the
request may link `account_user_id` and the rendered request flow should treat it
as an account-linked entry request rather than asking the writer to retype or
exchange contact email. Creating a request must not create a `User`,
`CommunityMembership`, role, character, reserve, claim, invitation, session, or
active-face state. Public realm previews may submit a request and show
account-vs-anonymous posture, but only director-capable memberships in the same
community can list or inspect request details.

Duplicate open access requests are deduplicated by email inside one community.
If a later duplicate arrives from a signed-in account for the same email, the
existing anonymous request may link `account_user_id`; it must not create a
second request or grant membership, role, face, invite, reserve, claim, session,
or active-face state. The account-link event is recorded for director-visible
history, but it does not change request status or expose private request details
to the applicant or public preview.

The access-request lifecycle is `pending -> reviewed -> invited` or
`pending/reviewed -> declined`. An invited request may link to the invitation
row that was created from it, but the raw invite token is still shown only at
creation time because stored invitations retain token hashes. A lost link
requires revoking the pending invitation and creating a fresh one; the original
access request remains the audit trail for why the invite was issued.
Director-visible access-request activity events are stored in
`community_access_request_events` with `community_id`, request id, optional
actor membership, status transition, optional invitation id, and timestamp.
Submitted, account-linked, reviewed, invited, and declined events are staff
workflow history, not public preview data.

Community export manifests are director-only backend read models. They may count
community-scoped workflow rows and preserve source links, membership ownership,
and character authorship, but the general manifest excludes global users,
password hashes, session state, token hashes, raw invitation tokens, and private
access-request notes. A future detail export for staff workflow records needs a
separate privacy review before it can include applicant emails, notes, or
invitation audit material.

The export service also owns privacy profiles for four archive tiers. A public
export profile is limited to public-safe realm identity, approved roster,
non-archived wanted hooks, claimed public casting values, and published material
metadata. A member profile may add member-visible threads and posts, but not
staff queues, private notes, another writer's private records, draft materials,
notification rows, inactive identities, or cross-community records. A staff
profile may include current-community operational state only for workflows the
staff capability covers; it still excludes global auth material, sessions, raw
invite tokens, notification rows, and other communities. A director archive
profile names sensitive domains such as membership state, roles, inactive
identities, draft materials, private plotting rooms, invitation state,
notification rows, and staff queues, while still excluding global users,
password hashes, sessions, raw invite tokens, applicant private notes, and
cross-community rows.

First-realm creation is not a public web permission. The current setup path is
the operator-only `bootstrap-first-realm` CLI command, which creates a global
login user plus a community-local director membership in the same transaction.
An empty configured realm remains backstage in public catalog read models until
it has public-ready content. Directors see setup continuation through their own
membership; ordinary members cannot enter `/studio/launch`.

Director-created invitation links are the only public account/membership
creation path. Invite acceptance resolves the token server-side, rejects
accepted, revoked, or expired tokens, creates or reuses the global `User`,
creates the `CommunityMembership` only inside the invited community, and can
create the writer's first face as that membership's default character. Invite
tokens must not grant access to Studio, staff queues, draft materials, or any
other realm. Studio invitation management may list invitation state and revoke
pending invites, but only the creation response renders the raw invite link
because stored invitations retain token hashes.

When an existing global account accepts an invitation for another community,
the new membership and optional first face are local to the invited community.
Existing memberships, default faces, roles, and active-face state in other
communities must not be changed by the invite acceptance flow.

Invitation delivery is copy-only until a sender policy exists. "Resend" means
reissue, not recover: a director revokes the pending invitation and creates a
fresh token for the same email. Accepted, revoked, or expired invitations do
not expose raw tokens and should not be resurrected.

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

Notification inbox rows, shell counts, redirects, and mark-read actions are
also privacy boundaries. Each supported notification kind must use the
service-owned target contract for required fields and visibility. A notification
delivered to the right membership is still treated as inaccessible when its
target is private, belongs to another community, lacks the required target
fields, or resolves to a row the membership cannot view. Post mention and
watched-thread fanout also runs that target contract before inserting
notifications, so inactive members and memberships that cannot enter the target
board do not receive rows merely to be filtered later.

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

## Continuity Graph Gate

Continuity Graph schema, services, routes, notifications, and export behavior
must satisfy `docs/architecture/continuity-graph-readiness.md` before shipping.
Until that gate moves with implementation proof, there should be no public
continuity route family and no automatic canon publication from thread text,
plotting-room notes, application review, staff notes, or access-request notes.
