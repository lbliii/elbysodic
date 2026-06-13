# Invite To First Face Onboarding Journey

Status: rendered journey contract for #116
Owner: Web, auth/service, surface-contract, product, and user-panel stewardship
Last updated: 2026-06-04

The onboarding journey should let a new writer understand where they are in the
realm without implying public self-serve membership. The path is:

```text
public preview -> request access or invitation -> local membership -> first face
-> application -> claims/reserves and wanted hooks -> first scene
```

This guide does not define the backend lifecycle for access requests,
invitations, membership creation, sessions, claims, reserves, or applications.
Those stay in the existing backend issues. This guide defines what rendered
pages must communicate while using those service-owned contracts.

## Journey States

| State | What They Know | Primary Next Action | Must Not Render |
|---|---|---|---|
| Public visitor | The realm premise, public wanted hooks, guidebook paths, and access posture. | Request access or log in. | Desk, active face, unread counts, staff controls, private queues, application review state. |
| Signed-in account visitor | They have an Elbysodic account but no local membership. | Request access with this account. | Writer shell, active face, local membership actions, private forms, staff routes. |
| Pending requester | The access request was received for their email or account. | Wait for director invitation or browse public previews. | Director review notes, invitation links, staff queues, private request metadata. |
| Invited writer | A director invitation targets one realm. | Accept invitation and create the local writer identity. | Global character creation, public self-serve signup, other realm staff power. |
| Faceless member | They have a local membership but no posting face. | Start a face or continue application work. | Ordinary queue pressure as the primary action, another writer's application, active-face controls. |
| Applicant | They are drafting or revising a first face. | Submit/revise application, resolve claims/reserves, answer wanted hooks. | Staff notes, another writer's draft, raw review state outside allowed controls. |
| Accepted face | They have a public posting identity. | Set or use active face, answer wanted hooks, start first scene. | Global face identity or cross-realm posting authority. |
| Inactive or cross-community visitor | Their current identity cannot enter this realm. | Recover, switch safely, log in, or return to public preview. | Private target names, switch options for inactive faces, staff/private data. |

## Rendered Surface Contract

### Public Preview To Request Access

Public previews should expose only public-safe premise, places, wanted hooks,
guidebook/application materials, and request-access actions. Request access is
interest, not permission. It asks for writer email, writer name, face concept,
wanted hook or way in, and notes for directors.

### Account Visitor To Request Access

When a global account is signed in but not a local member, the page should say
the account can request access without a separate email handoff. The form uses
the account email behind the service boundary and should not render a writer
email field.

### Invitation Acceptance

Invitation acceptance says the login works across Elbysodic, but writer name,
role, and faces belong to the invited realm. It asks for writer username,
display name, password, and optional first face. Accepting an invitation creates
or reuses a global account only as needed, then creates the local membership.

### First Face And Application

The first-face starter should name `Start a face` and `Begin a new face`, then
tell faceless writers that the draft becomes their first active face after it
is created. It should keep application materials visible and point accepted
faces toward claims/reserves, open wanted calls, and the first scene.

### Privacy

Unauthorized onboarding views must not show applicant notes, director review
state, invitation links, staff notes, private queues, raw tokens, or another
writer's application. Cross-community and inactive states recover through the
service-owned recovery contract.

## Copy Rules

Use realm, writer, face, roster, invitation, request access, first face,
application, claims, reserves, wanted, plotting, and scene. Avoid signup,
project, workspace, user profile, task, ticket, dashboard, and onboarding
pipeline language unless a technical runbook is being quoted.

## Required Proof

Front-end onboarding PRs should include:

- rendered tests for public visitor, account visitor, invited writer, faceless
  member, applicant, accepted face, staff/director, inactive, and
  cross-community states as applicable
- negative assertions for private notes, raw tokens, staff review state,
  invitation links, private queues, active-face controls, and other writers'
  applications
- CSRF/POST tests only when the PR changes forms or submission behavior
- browser QA screenshots for substantial layout, mobile, keyboard, or focus
  changes

Docs/test-only contract updates do not require browser screenshots when no
markup, CSS, route, schema, auth, invite, claim, reserve, or application
behavior changes.
