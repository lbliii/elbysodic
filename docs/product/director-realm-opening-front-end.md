# Director Realm Opening Front-End

Status: rendered surface contract for #115
Owner: Realm Studio, web, product design, surface-contract, and test stewardship
Last updated: 2026-06-04

Opening a realm should feel like a director production room, not a generic
setup wizard. The front end should preserve the difference between platform
access, realm identity, director preparation, invite-only opening, public
preview readiness, and the first writer handoff.

This guide does not define first-realm creation, invitation backend behavior,
schema changes, public self-serve creator signup, billing, or Program
Blueprint Apply. It defines the rendered contract for the no-realm/backstage
path, Studio Launch, opening packet, invitations, and public-safe readiness
posture.

## Opening States

| State | Audience | Rendered Contract | Must Not Render |
|---|---|---|---|
| No realm | Signed-out visitor or account visitor. | Sparse platform identity and safe request-access/login posture. | Fake community shell, empty forum map, Director Studio, launch blockers. |
| Empty configured realm | Director/staff with capability. | Studio Launch as the default room, with opening checklist and minimum packet work. | Public preview as if the realm is ready, generic setup wizard language. |
| Backstage realm | Director/staff. | Director-only readiness, opening status, builder, invites, access requests, and launch blockers. | Public launch blockers, invitation links, staff notes, private setup state. |
| Invite-only realm | Invited writers and directors. | Invitation and first-face handoff with local membership context. | Public self-serve membership creation or global staff power. |
| Public-preview realm | Public/account visitors and members. | Public-safe premise, places, wanted hooks, guidebook paths, and request-access posture. | Director checklist state, draft materials, private setup notes, invite links. |

## Studio Launch Contract

Studio Launch answers one director question: what must be true before writers
can enter this realm safely?

The first read should name:

- `Open realm`
- scene hubs
- director materials
- intake and claims
- wanted hooks
- appearance
- invites
- launch checklist

The current rendered room should keep these areas in PBP language:

- **Opening status:** backstage, invite-only, or public preview.
- **Opening checklist:** required and optional lanes with clear production
  actions.
- **Opening packet:** the minimum scene hub, premise, and application guide.
- **Opening boundary:** what is deliberately not in this slice.
- **Writer invitations:** copy-only delivery, pending/accepted/revoked/expired
  posture, and account-to-membership handoff.
- **Access requests:** director-visible request review without exposing notes
  to public/member surfaces.

## Public Boundary

Public and account visitors can see only public preview material and safe
request-access actions. They do not see launch blockers, private setup notes,
draft director materials, invitation links, access-request review state, staff
controls, active-face controls, or member queues.

Ordinary members who lack director capability cannot use Studio Launch to infer
private setup work. They should receive recovery/permission handling without
the Launch room body.

## Copy Rules

- Use open a realm, director, Studio Launch, scene hubs, director materials,
  intake, claims, reserves, wanted hooks, appearance, invites, launch
  checklist, first face, and scene.
- Avoid setup wizard, workspace, project, task board, admin dashboard,
  organization, user management, or onboarding checklist language unless a
  technical runbook is being quoted.
- Treat invitations as membership creation inside one realm, not generic user
  signup.

## Required Proof

Front-end changes to this area should include:

- rendered tests for director/staff, ordinary member, signed-out visitor,
  account visitor, inactive, and cross-community states as applicable
- negative assertions for public/member absence of launch blockers, private
  setup notes, invitation links, staff controls, and access-request review state
- browser QA screenshots for Studio Launch and public transition states when
  layout or responsive behavior changes
- docs updates to information hierarchy, rendered privacy, security, or
  onboarding plans when visible behavior changes

Docs/test-only contract updates do not require browser screenshots when no
markup, CSS, layout, route, schema, auth, or invite behavior changes.
