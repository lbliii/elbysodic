# Rendered Route Privacy Matrix

This matrix is the route-level companion to `security-boundaries.md`. Use it
when adding a rendered page, route action, sidebar count, notification surface,
or Studio room that can expose community-, membership-, role-, or
character-scoped data.

Use `surface-contract-architecture.md` for the broader service/read-model,
template, and proof contract that should exist before a rendered surface grows
privacy, filtering, ranking, or lifecycle decisions.

Canonical shared-host route and link scoping rules live in
`docs/architecture/multi-tenancy.md#route-and-link-contract`; this matrix tracks
rendered privacy expectations and proof for route families.

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
| public | Signed-out visitor on a public-ready tenant preview route. | Published premise, guidebook, and wanted context is visible; identity, staff, queues, drafts, private notes, reserves, and POST actions stay hidden or blocked. |

## Route Families

| Route Family | Sensitive Data | Member | Owner | Staff | Cross-Tenant / Missing | Coverage |
| --- | --- | --- | --- | --- | --- | --- |
| `/c/{community}/`, `/c/{community}/world`, `/c/{community}/world/{material}` | Draft materials, Material Studio controls, current event links, raw scene/thread activity, private queue state, active-face continuation. | Community home renders the public premise gateway plus viewer-scoped continuation; member-local `/world` uses published materials only. | Same as member unless staff. | Drafts and edit controls visible only in material/studio surfaces, not public gateway previews. | Recovery page or 404; no draft body, active-face state, Desk lane, private board, or staff queue. | covered for draft material regressions, signed-out public tenant preview, original-premise gateway privacy, and premise browser QA |
| `/c/{community}/wanted`, `/c/{community}/wanted/{wanted}` | Archived hooks, interested faces, lifecycle controls, private interest notes, plotting-room links, reserves, and scene-handoff links. | Open/non-archived hooks only; unrelated members do not see another writer's note or room link. | Own hook controls and interest notes visible. | Casting controls and interest notes visible. | Recovery page or 404; no archived body, private note, reserve, or room link. | covered for prospective-note privacy, wanted backstage handoff, and signed-out public tenant preview |
| `/claims`, `/claims?...` | Claim and reserve state, filtered counts, character links, director notes, staff maintenance controls. | Public claim/reserve directory state only; staff controls and director notes absent. | Same as member unless staff. | Claims maintenance forms and director notes visible only with casting/staff capability. | No claim, reserve, character, or count data from another community. | covered for rendered directory state, staff write controls, application conflict handling, and tenant-scoped query/link regressions |
| `/casting` | Casting desk lanes, active-face prompts, wanted handoffs, reserves, private notes surfaced through casting workflows. | Own visible casting opportunities and face-specific prompts. | Own hook/interest handoffs where applicable. | Casting controls, review lanes, and private notes visible only with capability. | No wanted, reserve, claim, or face data from another community. | partial |
| `/applications`, `/applications/{character}` | Applicant draft body, staff notes, checklist, revision notes. | Own applications only; faceless members are routed to first-face work without another writer's application. | Own applicant controls. | Review queue, staff notes, claim conflicts, revision requests, and accept controls visible. | Recovery page or local applications hub; identity switch sanitizes cross-realm application URLs. | covered for draft, submit, review, revision, acceptance, claim conflict, faceless, and cross-realm recovery paths |
| `/plotting`, `/plotting/{room}` | Private planning notes, messages, participants, backstage stage grouping. | Participant rooms only. | Owner plan controls. | Casting-capable staff access only where the handoff policy allows. | Recovery/403; no room notes, messages, or notification targets. | covered for wanted and plot-hook handoffs, tenant-prefixed live routes, outsider denial, notification leakage, scene handoff, and rollback paths |
| `/notifications` | Membership-specific inbox and unread counts, wanted-interest notes, plotting-room targets, watched-thread and mention snippets. | Own visible notifications only; forged inaccessible wanted/room targets are hidden. | Same as member. | Staff still sees own inbox, not global inbox. | No other membership notifications; inaccessible room/wanted targets do not contribute unread counts. | covered for own inbox, unread/read state, watched-thread replies, mentions, plotting-room leakage, and wanted-interest leakage |
| `/studio`, `/studio/*` | Draft materials, private boards, production health, launch checklist, discovery-profile editing, edit forms. | Read-only preview or forbidden controls absent; launch room and discovery-profile setup are denied without director capability. | Same as capability. | Capability-scoped controls and setup signals visible; discovery edits write only public catalog metadata for the current community. | No staff power leakage or discovery-profile writes across communities. | partial; launch room director/member and discovery-profile editor route covered |
| `/boards/{board}`, `/boards/{board}/threads/{thread}` | Private boards, private threads, post bodies, moderation controls. | Public visible boards only. | Thread author controls where allowed. | Moderation controls visible. | Not found/recovery; no private activity. | partial |
| `/members`, `/members/{username}` | Private activity and private-board latest lines. | Public cast/activity only. | Own profile controls when present. | Staff-only private activity only when designed. | No other community profile data. | covered for inactive identity regressions |
| `/network`, `/network?q=...` | Public catalog cards, discovery profiles/tags, signed-in continuation, staff/member counts, backstage realm names. | Public catalog cards may show only public profile fields, public discovery tags, published premise/current chapter links, safe roster/wanted/claim counts, access/application posture, ratings, and pace; member continuation stays separate and viewer-scoped. | Own continuation lanes only. | Staff signals only where policy allows and never inside public catalog cards. | No private/staff data, discovery tags, member state, active faces, unread counts, applications, plotting rooms, drafts, or backstage realm names from other realms. | signed-out public catalog, profile/tag search, backstage realm filtering, Railway smoke, local browser QA, and premise browser QA covered |
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

- Browser QA smoke and deep profiles passed on 2026-05-12 against a local seeded
  app on port 8004. The deep profile skipped only the director-only launch room
  with expected 403 responses.
- Draft world materials stay staff-only on `/world`, direct material routes,
  and Studio/editor surfaces.
- Director-created invitation acceptance is public only through `/invite/{token}`;
  accepted/revoked/expired invite tokens fail instead of revealing launch-room
  or membership internals. Studio invite management lists invitation state and
  can revoke pending invitations without rendering token hashes.
- Inactive memberships are absent from `/members`, `/members/{username}`, and
  direct character profile routes, and recovery does not offer cross-realm
  switches for inactive faces.
- Plotting room notifications do not render private room titles, unread counts,
  or open redirects for memberships that are not room owners, participants, or
  casting-capable staff.
- Tenant-prefixed plotting room routes do not leak an existing planning room
  when the current realm does not own that room id.
- Wanted-interest notifications do not render prospective pitch notes or open
  redirects for memberships that are not the interested writer, hook creator,
  or casting-capable staff.
- Studio operations renders as a read-only console for ordinary members without
  exposing submitted application names or review queue counts.
- Studio launch room renders the realm opening checklist from existing
  community-scoped setup state and denies non-director memberships.
- Studio discovery profile editor lets directors update public catalog metadata
  for the current community and denies ordinary member GET/POST access.
- Premise browser QA covers `/network` profile queries, original-premise realm
  hubs, and `/studio/discovery` as an original-premise director persona.
- Community premise gateway tests cover public hero/action/signal/scene-hub
  contracts, tenant-scoped wanted and entry links, wanted previews, and absence
  of staff/application/active-face signals for signed-out visitors.
- Guided Realm Builder writes the minimum scene hub, premise material,
  application guide, and default appearance tokens only for the director's
  current community.
- Wanted detail hides private interest notes from unrelated ordinary members
  while showing hook creators and casting staff the backstage controls needed
  to start or open plotting rooms.
- Application review rooms deny unrelated members direct access to another
  writer's application body and staff review surface.
- Claims directory rendering hides director claim notes and maintenance
  controls from ordinary members while preserving staff edit visibility.

## Current Gaps

- Notifications still need shell/sidebar count coverage across inactive and
  faceless identities; current proof covers forged targets, own inbox,
  watched-thread replies, and mentions.
