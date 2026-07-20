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

The web stack resolves that database-backed session once per request and adapts
its global `User` through Chirp `AuthMiddleware`. `request.user` therefore names
only the authenticated login account. The tenant resolver consumes the same
cached request login before it selects a community membership, role, or active
face; none of those community-local identities are added to Chirp's global-user
adapter. Revoked, expired, missing, or orphaned app sessions resolve as
anonymous even when a Chirp session cookie still contains an older user id.

Chirp session cookies are newly signed with SHA-256. The SHA-1 fallback remains
read-only for cookies issued before this rollout: a readable SHA-1 cookie is
reissued with SHA-256 on its next request, and no new cookie is SHA-1-signed.
Review removal on or after **2026-08-20**, once the 30-day app-session window has
elapsed and production evidence shows no pre-rollout Chirp sessions remain.

Anonymous public catalog `GET`/`HEAD` requests that do not arrive with a Chirp
session do not emit `Set-Cookie` or vary on cookies, so `/`, `/network`, health,
static assets, and public tenant preview reads remain eligible for shared
caching. `/login`, `/login/passkeys/*`, `/invite/*`, and tenant or global
`/request-access` intentionally touch Chirp session state for CSRF or passkey
ceremonies and are not part of that cacheable catalog contract.

`auth_trust_posture()` in `src/elbysodic/services/auth.py` provides a redacted
operations diagnostic for this posture. It reports environment, production
mode, demo-mode seed password posture, secret-key presence/minimum status,
session cookie name, session TTL, development identity availability, and
session-required status without exposing secret values, token hashes, raw
cookies, account emails, membership names, or private identity state. Each
warning also has a stable code, severity, affected surface, recommended fix,
production-blocking flag, and local-development exception flag. The operator
remediation guide lives in `docs/operations/auth-trust-posture.md`.

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

The access-request lifecycle is service-owned and director-private. It is the
planning contract for #107, #86, #57, and #139, not approval to add schema,
routes, token behavior, or privacy-boundary changes without a separate review.
Access requests are interest records; only explicit invitation acceptance can
create or reuse a global `User`, create `CommunityMembership`, create a first
face, select session identity, or hand the writer into first-face/application
work.

| State | Entry Transition | Allowed Next Transitions | Idempotency And Replay | Visibility |
|---|---|---|---|---|
| `submitted` / `pending` | Public or account visitor submits request access for one community. | Account link, director review, decline, invite, withdraw or expire when implemented. | Duplicate open request for the same community/email returns or links the existing record; it does not create membership, role, face, invite, reserve, claim, session, or active-face state. | Public/account visitor may see receipt posture only; same-community directors may inspect details. |
| `account_linked` | Signed-in account submits or claims a duplicate request for the same email. | Review, decline, invite, withdraw or expire when implemented. | Repeated account-link attempts are no-ops when linked to the same user; wrong-account or cross-community attempts must fail without exposing another request. | Applicant still cannot see review notes, invite linkage, staff history, or other applicant data. |
| `reviewed` | Director marks the request reviewed or records director-only context. | Invite, decline, withdraw or expire when implemented. | Re-review updates director workflow state only through an approved service transition; it must not send or recover an invite token. | Director-only; hidden from public, account visitors, ordinary members, inactive members, and other communities. |
| `invited` | Director creates an invitation from the request. | Invite acceptance through `/invite/{token}`, revoke/reissue while pending, or expire when implemented. | Replayed invite creation should reuse the existing linked invitation or require explicit reissue; raw invite token is visible only at creation/reissue. | Directors may see linked invitation state; applicant never sees the raw token from request status. |
| `accepted` | Invitation token is accepted and creates/reuses account plus local membership. | First-face or application handoff. | Replaying the accepted token fails without exposing Studio, staff queues, or membership internals. | Writer sees the invited realm membership path; access-request notes and director review history remain staff-only. |
| `declined` | Director declines the request. | Reopen only through a separately approved transition. | Duplicate submissions after decline follow the approved duplicate/reopen policy; they must not reveal prior notes or invitation state. | Applicant may see generic closed or received posture if surfaced; director details stay private. |
| `withdrawn` | Applicant withdraws interest when that route exists. | Reopen through a new request or approved recovery path. | Replayed withdraw is a no-op; director history remains audit-only. | Public/account view must not expose director notes or staff state. |
| `expired` | System or director expiry closes stale interest when implemented. | New request or explicit director reactivation. | Replayed links and stale actions fail closed. | Expiry reason is director-private unless a public-safe receipt state is approved. |

Visibility rules:

| Viewer | May See | Must Not See |
|---|---|---|
| Public visitor | Public request-access form, receipt posture, and realm-safe entry copy. | Applicant email from another request, private notes, review state, invitation link, account-link history, staff queues, or membership state. |
| Account visitor | Account-linked request posture for their own submitted email in the current community. | Director notes, invite linkage, raw token, another account's request, or local membership controls before invitation acceptance. |
| Ordinary member | Public-safe preview and member shell for their own realm. | Request queue, applicant notes, invitation state, account-link history, or director review state. |
| Inactive member | Public-safe preview or recovery copy only. | Request queue, switch options, private request data, staff controls, or local entry grants. |
| Director/staff with capability | Current-community request details, lifecycle history, duplicate/account-link context, and linked invitation state. | Raw invite token after creation/reissue, token hashes, passwords, sessions, other-community requests, or unrelated applicant data. |
| Cross-community staff/director | Nothing beyond public-safe preview for the target realm. | Request existence, applicant email, notes, review state, linked invitation, lifecycle history, or counts. |

Transition proof required before implementation:

- Service tests for legal transitions, duplicate email recovery,
  same-account idempotency, wrong-account replay, stale invite replay, decline,
  withdrawal, and expiry once those states become behavior.
- Rendered privacy tests for public visitor, account visitor, ordinary member,
  inactive member, same-community director, and cross-community staff/director
  if any route or read model changes.
- Security tests proving raw tokens appear only in creation/reissue responses
  and token hashes, private notes, applicant emails, and staff review history do
  not leak through public/account/member surfaces.
- Repository tests proving request, event, invitation, actor membership, and
  account link rows remain scoped to the same `community_id`.

Director-visible access-request activity events are stored in
`community_access_request_events` with `community_id`, request id, optional
actor membership, status transition, optional invitation id, and timestamp.
Submitted, account-linked, reviewed, invited, accepted, declined, withdrawn,
and expired events are staff workflow history, not public preview data.

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
cross-community rows. The export inclusion, redaction, provenance, and proof
matrix lives in `docs/architecture/primitives.md`.

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
not expose raw tokens and should not be resurrected. Bounced email, mistaken
recipient, or lost-link support follows the same rule: if the invitation is
still pending, revoke and reissue; if it is accepted, revoked, or expired, use
membership/account support or create a deliberately new invitation after
confirming the corrected recipient. Support replies may name the email and
state but must not include token hashes, raw tokens recovered from storage, staff
notes, or private access-request details.

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

New real accounts store argon2id hashes through Chirp's password primitives.
The login service can verify the previous Elbysodic PBKDF2 format and Chirp's
scrypt PHC format, then derives an argon2id replacement only after the password
has verified. The repository persists that replacement with a compare-and-swap
against the exact hash that was verified, so concurrent successful logins may
both establish sessions but only one can replace the legacy value. A failed
password never writes, a current argon2id hash is not rewritten, and a
`dev-password-hash` seed account stays on the explicit demo-mode boundary.
Password hashes remain global login-account material; the upgrade does not
change community membership, role, active face, or tenant ownership.

An unknown login account still runs Chirp's process-wide decoy password
verification and returns the same generic rendered failure as a known account
with a wrong password. Malformed legacy or PHC hashes fail closed without
creating a session or mutating credentials. This credential check remains a
global-user authentication boundary; membership and active-face resolution
still happen only after authentication succeeds.

Production mutating requests are protected by Chirp session-backed CSRF.
Rendered POST form templates include the active CSRF field explicitly, and
unsafe methods are rejected when the token is missing or invalid.

Notification inbox rows, shell counts, redirects, and mark-read actions are
also privacy boundaries. Each supported notification kind must use the
service-owned target contract for required fields and visibility. The
target-kind matrix lives in
`docs/architecture/request-identity-and-command-protocol.md`. A notification
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
