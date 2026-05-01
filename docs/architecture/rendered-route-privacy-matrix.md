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

| Route Family | Sensitive Data | Member | Owner | Staff | Cross-Tenant / Missing |
| --- | --- | --- | --- | --- | --- |
| `/world`, `/world/{material}` | Draft materials, Material Studio controls, current event links. | Published materials only. | Same as member unless staff. | Drafts and edit controls visible. | Recovery page; no draft body. |
| `/wanted`, `/wanted/{wanted}` | Archived hooks, interested faces, lifecycle controls. | Open/non-archived hooks only. | Own hook controls visible. | Casting controls visible. | Recovery page; no archived body. |
| `/applications`, `/applications/{character}` | Applicant draft body, staff notes, checklist, revision notes. | Own applications only. | Own applicant controls. | Review queue and staff notes visible. | Recovery page or local applications hub. |
| `/plotting`, `/plotting/{room}` | Private planning notes, messages, participants. | Participant rooms only. | Owner plan controls. | Staff access only when explicitly designed. | Recovery page; no room notes. |
| `/notifications` | Membership-specific inbox and unread counts. | Own notifications only. | Same as member. | Staff still sees own inbox, not global inbox. | No other membership notifications. |
| `/studio`, `/studio/*` | Draft materials, private boards, production health, edit forms. | Read-only preview or forbidden controls absent. | Same as capability. | Capability-scoped controls visible. | No staff power leakage across communities. |
| `/boards/{board}`, `/boards/{board}/threads/{thread}` | Private boards, private threads, post bodies, moderation controls. | Public visible boards only. | Thread author controls where allowed. | Moderation controls visible. | Not found/recovery; no private activity. |
| `/members`, `/members/{username}` | Private activity and private-board latest lines. | Public cast/activity only. | Own profile controls when present. | Staff-only private activity only when designed. | No other community profile data. |

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
