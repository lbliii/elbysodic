# Community Landing Browser QA

Use this checklist before calling the public realm landing, scoped search, and
first-face handoff visually ready. Rendered tests prove route contracts; this
pass catches viewport, focus, overflow, and state-language regressions.

## Required Viewports

- Desktop: 1440 x 1000.
- Tablet: 900 x 1100.
- Mobile: 390 x 844.

## Required States

- Signed-out visitor on `/c/afterlight-accord`.
- Signed-in account visitor on `/c/afterlight-accord`.
- No-face member on `/c/x-men-apocalypse`.
- Ordinary member with accepted face on `/c/x-men-apocalypse`.
- Applicant viewing an accepted application room.
- Director viewing Studio Operations and Studio Launch.

## Tasks

1. Open the realm home and confirm the first viewport names the realm, premise,
   public movement, and access posture without private staff or active-face
   data.
2. Confirm signed-out visitors see anonymous actions, and signed-in account
   visitors see account posture instead of logged-out copy.
3. Search inside the realm. The visible search scope may use initials, but the
   full realm name must be present in the label, button text, title, or
   equivalent accessibility surface.
4. Submit a request-access form from a tenant preview and confirm Studio Launch
   shows the request without creating membership, role, face, or invite rows.
5. Start or open first-face application work and confirm claim conflicts
   explain that an exclusive value must change before acceptance.
6. Open an accepted application room and confirm the first handoff includes the
   service-owned next writing move plus claims, wanted, and location links.
7. Open Studio Operations and confirm access requests, invitations, no-face
   members, application review, raised hands, and scene handoffs route to the
   expected queues.

## Pass Criteria

- No text overlaps, clipped buttons, horizontal scroll, or unusable controls at
  the required viewports.
- Keyboard focus reaches search, request access, application, and Studio queue
  links in a coherent order.
- Public pages do not render staff notes, private activity, unread counts,
  active-face controls, or member-only desk links for signed-out visitors or
  account visitors.
- Account, membership, face, application, claim, reserve, wanted, scene, and
  thread language remains visible where each state needs it.
- Screenshots or artifact paths are recorded in the PR or release notes.

## Current Status

Not run in this workspace. The local route and contract checks passed, but this
browser QA still needs a running app URL and screenshots for the required
viewports.
