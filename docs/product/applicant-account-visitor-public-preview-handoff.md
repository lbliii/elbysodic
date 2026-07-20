# Applicant And Account-Visitor Public Preview Handoff

Status: rendered handoff contract for #119
Owner: Web, surface-contract, auth/service, product, and user-panel stewardship
Last updated: 2026-06-04

Public preview is the handoff between discovery and local realm identity. It
must let applicants, hook hunters, signed-in account visitors, invited writers,
and faceless members understand what they can do next without granting a local
membership or exposing member/staff state.

This guide does not introduce public self-serve registration, public membership
creation, marketplace ranking, or billing. Request access remains interest, not
permission. Membership creation remains invitation-backed.

## Viewer States And Next Actions

| State | Public-Safe View | Next Action | Must Not Render |
|---|---|---|---|
| Public visitor | Realm premise, public wanted hooks, guidebook/application materials, places, public activity, and access posture. | Log in or request access. | Desk, active face, unread counts, staff controls, private queues, mutating member forms. |
| Signed-in account without local membership | Account identity plus public preview and account-linked request-access action. | Request access with this account or browse other realms. | Community shell, active face, local membership actions, staff routes, private forms. |
| Pending access requester | Confirmation that the account/email request was received. A signed-in owner may withdraw from the immediate receipt. | Wait for a director invitation, withdraw, or keep browsing public previews. | Lifecycle status, director review notes, invite links, staff queue state, private request metadata, or another request. |
| Invited writer | Invitation acceptance for one realm. | Accept invite and create local writer identity. | Public self-serve membership creation or cross-realm staff power. |
| Faceless member | Member posture with first-face/application continuation. | Start a face, continue application, browse wanted, or find a first scene. | Ordinary queue pressure as primary path, active-face controls, another writer's application. |
| Applicant | Own application room and allowed continuation. | Submit, revise, resolve claims/reserves, answer wanted hooks. | Staff notes unless staff, another writer's draft, private review queues. |
| Member with face | Local writer shell and active-face work. | Reply, plot, raise interest, reserve, or start a scene. | Global character identity or cross-community posting authority. |
| Staff/director | Capability-scoped Studio and review controls. | Review or invite from current-community workflows. | Global staff power or public visitor state. |
| Inactive/cross-community viewer | Recovery or public-safe preview. | Switch safely, log in, or request access where allowed. | Private target names, inactive switch options, private queues, staff state. |

## Surface Contracts

### Public Realm Preview

Public previews sell the realm: premise, tone, places, wanted hooks, guidebook
paths, application material, public activity, and access posture. They do not
show launch blockers, staff notes, invite links, private queues, unread counts,
Desk routes, or active-face controls.

### Account Visitor Shell Posture

A signed-in account visitor can see account identity in the shell, but not the
community shell. The account visitor panel should say they are not a member of
the realm yet and can browse the public preview before requesting access.

### Wanted And Application Handoffs

Public wanted detail pages can show public-safe hook copy and request-access
actions. Signed-in account visitors should see `Request access to raise
interest`; signed-out visitors should see login and request-access actions.
Prospective interest or plotting-room actions are only available when the
service-owned viewer state allows them.

Application materials can be public guidebook links, but applicant forms,
review notes, claim conflicts, reserves, staff notes, and application review
rooms stay local to authorized members/staff.

### Faceless Continuation

Faceless members should be routed toward first-face/application work before
ordinary queue state. Continuation affordances can include start a face,
continue application, claims/reserves, wanted hooks, and first scene, but must
not show another writer's application or active-face controls.

## Copy Rules

Use account, membership, face, writer, realm, roster, request access,
invitation, first face, application, claims, reserves, wanted, plotting, and
scene. Avoid signup, workspace, project, task, lead, ticket, application funnel,
CRM, or dashboard language.

## Required Proof

Front-end public-preview handoff work should include:

- rendered tests for public visitor, signed-in account visitor, pending
  requester, invited writer, faceless member, applicant, member, staff/director,
  inactive, and cross-community states as applicable
- negative assertions for Desk, active face, unread counts, staff controls,
  private notes, invite links, application review state, plotting rooms, and
  reserves where unauthorized
- browser QA screenshots for substantial desktop/mobile layout or interaction
  changes
- docs updates to rendered privacy, information hierarchy, public discovery,
  or onboarding guidance when behavior changes

Docs/test-only contract updates do not require browser screenshots when no
markup, CSS, route, schema, auth, access-request, invite, application, or
wanted behavior changes.
