# Rendered Route Privacy Matrix

This matrix is the route-level companion to `security-boundaries.md`. Use it
when adding a rendered page, route action, sidebar count, notification surface,
or Studio room that can expose community-, membership-, role-, or
character-scoped data.

Rendered privacy tests should prove what the user can see, not only what a
repository method returns. Prefer one focused test per route family unless a
workflow has several identity shapes.

## Identity Modes

Use these viewer modes when a route can expose scoped data:

| Mode | Meaning | Must Prove |
| --- | --- | --- |
| member | Active non-staff membership in the current community. | Public/published data is visible; staff-only and private data is absent. |
| owner | Membership that owns the object or created the hook/room/application. | Owner-only controls appear without granting staff-only power. |
| staff | Active membership with the named capability for the current community. | Staff controls and draft/private data appear only inside this community. |
| inactive | Membership exists but is inactive. | Actions fail and private data stays hidden. |
| cross-tenant | Membership belongs to another community or route slug exists elsewhere. | Current community does not leak the other community's object. |
| faceless | Membership has no active/current character. | Character-backed actions disappear or ask for a face instead of guessing. |

## Route Families

| Route Family | Sensitive Data | Member | Owner | Staff | Cross-Tenant / Missing | Coverage |
| --- | --- | --- | --- | --- | --- | --- |
| `/world`, `/world/{material}` | Draft materials, Material Studio controls, current event links. | Published materials only. | Same as member unless staff. | Drafts and edit controls visible. | Recovery page; no draft body. | covered for draft material regressions |
| `/wanted`, `/wanted/{wanted}` | Archived hooks, interested faces, lifecycle controls, private interest notes, plotting-room links, and scene-handoff links. | Open/non-archived hooks only; unrelated members do not see another writer's note or room link. | Own hook controls and interest notes visible. | Casting controls and interest notes visible. | Recovery page; no archived body, private note, or room link. | covered for prospective-note privacy and wanted backstage handoff |
| `/applications`, `/applications/{character}` | Applicant draft body, staff notes, checklist, revision notes. | Own applications only. | Own applicant controls. | Review queue and staff notes visible. | Recovery page or local applications hub. | partial |
| `/plotting`, `/plotting/{room}` | Private planning notes, messages, participants, backstage stage grouping. | Participant rooms only. | Owner plan controls. | Staff access only when explicitly designed. | Recovery page; no room notes. | partial; notification leakage and wanted stage grouping covered |
| `/notifications` | Membership-specific inbox and unread counts, wanted-interest notes, plotting-room targets. | Own visible notifications only; forged inaccessible wanted/room targets are hidden. | Same as member. | Staff still sees own inbox, not global inbox. | No other membership notifications. | partial; forged wanted/room target regressions covered |
| `/studio`, `/studio/*` | Draft materials, private boards, production health, launch checklist, edit forms. | Read-only preview or forbidden controls absent. | Same as capability. | Capability-scoped controls and setup signals visible. | No staff power leakage across communities. | partial; launch room route covered |
| `/boards/{board}`, `/boards/{board}/threads/{thread}` | Private boards, private threads, post bodies, moderation controls. | Public visible boards only. | Thread author controls where allowed. | Moderation controls visible. | Not found/recovery; no private activity. | partial |
| `/members`, `/members/{username}` | Private activity and private-board latest lines. | Public cast/activity only. | Own profile controls when present. | Staff-only private activity only when designed. | No other community profile data. | covered for inactive identity regressions |
| `/network`, `/network?q=...` | Public catalog cards, signed-in continuation, staff/member counts, backstage realm names. | Safe public or own membership data only; backstage realms stay hidden unless scoped to the viewer. | Own continuation lanes only. | Staff signals only where policy allows. | No private/staff data from other realms. | signed-out public catalog and backstage realm filtering covered |
| shell/sidebar counts | Private board counts, notification counts, Studio attention counts. | Own permitted counts only. | Same as member. | Capability-scoped counts only. | No cross-realm or private counts. | partial |

## Test Checklist

For each new rendered surface, decide whether it needs tests for:

- direct route access
- index/list visibility
- sidebar or shell counts
- action form visibility
- POST permission failure
- recovery page content
- cross-community slug collision
- inactive membership behavior
- active-face or faceless behavior

Keep assertions semantic. It is usually better to assert that a title, note, or
control appears or does not appear than to snapshot large HTML sections.

## Covered Regressions

- Draft world materials stay staff-only on `/world`, direct material routes,
  and Studio/editor surfaces.
- Inactive memberships are absent from `/members`, `/members/{username}`, and
  direct character profile routes, and recovery does not offer cross-realm
  switches for inactive faces.
- Plotting room notifications do not render private room titles, unread counts,
  or open redirects for memberships that are not room owners, participants, or
  casting-capable staff.
- Wanted-interest notifications do not render prospective pitch notes or open
  redirects for memberships that are not the interested writer, hook creator,
  or casting-capable staff.
- Studio operations renders as a read-only console for ordinary members without
  exposing submitted application names or review queue counts.
- Studio launch room renders the realm opening checklist from existing
  community-scoped setup state.
- Wanted detail hides private interest notes from unrelated ordinary members
  while showing hook creators and casting staff the backstage controls needed
  to start or open plotting rooms.

## Current Gaps

- Production public catalog/search proof for signed-out and signed-in users.
- Application review room owner/staff/outsider route-family coverage.
- Claims conflict and reserve visibility coverage beyond happy-path directory
  rendering.
- Plotting room rendered page coverage across participant, owner, outsider,
  staff, and cross-tenant identities.
- Notification inbox and shell/sidebar count coverage across membership,
  inactive, faceless, and cross-tenant identities.
- Browser QA evidence for responsive privacy-adjacent surfaces where counts,
  drawers, or recovery actions can render differently from desktop.
