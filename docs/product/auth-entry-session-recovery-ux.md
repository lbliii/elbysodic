# Auth Entry And Session Recovery UX

Status: rendered UX contract for #114
Owner: Web, auth/service, surface-contract, and product stewardship
Last updated: 2026-06-04

Auth entry is a trust surface for writers. It must explain the difference
between a global Elbysodic account, a community-local membership, and an active
face without leaking private realm state or implying global staff power.

This guide does not define authentication mechanisms, password policy, session
storage, or production enforcement. Those remain in the auth/security backend
contracts. This guide defines the rendered posture that login, request access,
account visitor previews, logout, identity switching, and recovery pages should
preserve.

## Viewer States

| State | What The User Has | Rendered Posture | Must Not Render |
|---|---|---|---|
| Signed-out visitor | No active account session. | Public preview, login, and request-access actions. | Community shell, Desk, active face, unread counts, staff controls, private queues, member actions. |
| Signed-in account visitor | Global login, no membership in the viewed community. | Signed-in account identity plus public-safe realm preview and request-access action. | Active face, local membership controls, unread counts, Desk, staff links, private forms, private queues. |
| Member without face | Local membership but no posting identity. | First-face/application continuation before ordinary queue work. | Another writer's application, staff notes, active-face controls, private review state. |
| Active-face writer | Membership plus current character. | Writer shell, active face, reply/plotting/application obligations, and local role controls. | Global character identity or staff power outside the current community. |
| Staff/director | Membership with current-community capabilities. | Staff or Studio controls attached to current-community workflows. | Staff power in another realm or public/account visitor views. |
| Inactive membership | Historical local identity that cannot enter. | Recovery or denial with generic posture and no private rows. | Inactive profile details, private queues, notifications, staff controls, switch options that cannot enter. |
| Stale or cross-community selection | Account/session points at a missing, wrong, or different-community identity. | Recovery page names the safe target and offers a sanitized switch or public fallback. | Raw tokens, private target names the viewer cannot access, cross-realm private state, unsafe return URLs. |

## Surface Contracts

### Login

Login names the account first. It can say that Elbysodic resolves community
membership and active face after login, but it must not imply that logging in
creates a realm membership or grants staff power. The request-access link stays
available for writers who need a director-reviewed way in.

### Request Access

Request access is interest, not permission. Signed-out visitors provide writer
email and first-face context. Signed-in account visitors reuse the account and
do not need a separate email handoff. Confirmation copy can say the request was
received, but it must not expose director review notes, invitation links, or
staff queue details.

### Account Visitor Preview

An account visitor can browse public realm previews while signed in. The shell
may show account identity and logout/theme tools, but it must not show the
community shell, Desk, active face, unread counts, staff controls, private
queues, or mutating member forms for the viewed realm.

### Logout

Logout clears account and development identity cookies and returns to login.
Logout copy and links should avoid implying that writer names, memberships, or
faces were deleted.

### Recovery

Recovery is service-owned. Templates render the safe `RecoveryView` only:
kicker, title, summary, detail, sanitized switch action, and public fallback
links. The switch form keeps `membership_id`, `character_id`, and `next`
service-provided; templates do not infer cross-community destinations.

## Copy Rules

- Use account for global login identity.
- Use membership for local realm identity and role/capability context.
- Use face for public character/posting identity.
- Use realm, writer, director, roster, request access, invitation, first face,
  application, claims, reserves, wanted, scene, and Desk.
- Avoid generic signup, workspace, project, team, organization, task, admin,
  and dashboard language unless quoting technical configuration.

## Required Proof

Rendered auth-entry PRs should include focused proof for:

- signed-out login/request-access pages without community shell or private state
- signed-in account visitor preview without local membership affordances
- request-access account reuse without exposing director review state
- member/staff login preserving current-community membership and face context
- inactive, stale, revoked, or cross-community recovery without private leakage
- mobile/browser QA when layout, keyboard, drawer, or focus behavior changes

Docs and tests can update this contract without browser screenshots when no
rendered markup, layout, CSS, route, or auth behavior changes.
