# Simulated UAT Session: Community Landing And First-Face Handoff

Status: simulated UAT
Date: 2026-05-19
Researcher: Codex
Artifact inspected: rendered-route contracts, tests, and current product copy
Artifact path or URL: `/c/afterlight-accord`, `/network`,
`/applications/new`, `/applications/<character>`,
`src/elbysodic/web/pages/community_gateway/page.html`,
`src/elbysodic/web/pages/applications/page.py`
Synthetic user: Invited/New Face Applicant plus Hook Hunter, Community
Director, and Safety-Boundary Writer lenses
Seed docs: `docs/product/user-personas-panel.md`,
`research/uat/protocols/public-realm-preview.md`,
`research/uat/protocols/first-face-onboarding.md`
Confidence: medium for copy and journey risks, low for observed usability

This is simulated task testing. It can expose likely friction, but it does not
replace observed user behavior.

## Task

Move from a public realm landing page into the correct next step, then continue
from an accepted first face toward a writing move without confusing signed-out,
signed-in account visitor, member, application, or face states.

## Success Criteria

- User can tell whether they are signed out, signed in but not a member, or a
  community member.
- User can describe the realm premise, current movement, and access posture
  without seeing private staff or member data.
- Search scope reads as realm-specific without making the global account state
  unclear.
- A no-face member can find first-face application, claims, reserves, wanted,
  and location context.
- An accepted applicant reaches at least one next writing move: wanted hook,
  location, claim/reserve follow-up, or scene path.

## Starting State

- User role: prospective writer or newly accepted member.
- Community/membership state: one pass as signed-out visitor, one pass as
  signed-in account visitor with no membership, one pass as no-face member.
- Face/application state: no face at first; accepted application in the
  handoff pass.
- Device or viewport: desktop route contract; mobile browser QA still needed.
- Privacy/audience state: public preview, account visitor preview, applicant,
  and staff-reviewed application state.

## Expected Path

1. Land on `/c/afterlight-accord`.
2. Identify whether the shell is signed out, signed in but not a member, or a
   member of the realm.
3. Read premise, current chapter, places in play, and public wanted context.
4. Use scoped search or request-access/application entry without assuming the
   user is logged out.
5. As a no-face member, start first-face application and check claims,
   reserves, wanted, and locations before committing.
6. After acceptance, follow the handoff to claims, wanted, locations, or the
   next writing surface.

## Simulated Task Path

1. The signed-out pass reads the page as a public realm preview and uses
   `Log in` or `Request access` as expected.
2. The signed-in non-member pass needs distinct account visitor language. If
   the page only shows logged-out actions, the user assumes the session failed
   or the realm blocked them without explanation.
3. The search field benefits from compact realm initials because `AA Search`
   or an `AA` scope badge makes the query feel contained to Afterlight Accord.
   The full realm name still needs to remain available in nearby text or an
   accessible label so initials do not become mystery meat.
4. The member pass should not lose story context. Current chapter, places, and
   wanted material are still useful after joining; they orient the writer before
   they choose a face or scene.
5. The accepted application pass now has enough handoff shape if it links to
   claims, wanted, and locations. The remaining gap is that it still does not
   prove a single canonical first-scene destination.

## Failure Points

- Signed-in non-members can read logged-out CTAs as a broken session instead of
  an account visitor state.
- Realm initials in search help scoping, but unexplained initials can confuse a
  first-time visitor or screen-reader user.
- Members still need the public story layer; hiding it after access makes the
  realm feel less alive precisely when the writer needs orientation.
- Request access remains an informational action, not an interest-capture or
  application workflow.
- Accepted first-face handoff points to useful rooms, but there is not yet a
  single service-owned "start writing here" recommendation.

## Trust Breaks

- Wrong-face risk: medium after application acceptance until default face and
  reply/join actions are consistently face-named.
- Privacy/audience risk: medium on public preview; public story movement must
  remain curated and service-owned.
- Source-of-truth risk: medium if wanted or accepted-face context points people
  to external chat instead of object-bound plotting and scenes.
- Data-loss/draft risk: low on landing, high in first-face application fields
  that need browser QA.
- Design credibility risk: medium; the route is visually strong, but state
  language must be as precise as the design.

## Vocabulary Breaks

- Avoid `profile`, `workspace`, `signup funnel`, `content`, and `project`.
- Prefer `account visitor`, `member`, `face`, `roster`, `application`,
  `claims`, `reserves`, `wanted`, `locations`, `scene`, and `thread`.

## Recommended Changes

- P0: Keep signed-out and signed-in non-member states visually and verbally
  distinct on community landing pages.
- P1: Use abbreviated community initials for search scope, with full community
  name preserved in accessible text, placeholder context, or scope copy.
- P1: Preserve public story sections for members so the realm home remains a
  story orientation surface, not only an access gate.
- P1: Keep accepted application handoff links close to the accepted status and
  include claims, wanted, and locations.
- P2: Add a request-access capture flow after production smoke and invite
  safety gates are stable.
- P2: Add a service-owned accepted-face "next writing move" recommendation
  once scenes, wanted interest, and plotting contracts converge.
- P2: Run mobile browser QA against the landing page, application start, and
  accepted application handoff.

## Required Proof

- Rendered test: signed-out, account visitor, no-face member, ordinary member,
  staff, and director community landing states.
- Service test: public preview excludes private/staff/member-only data and
  accepted application handoff uses membership-scoped ownership.
- Browser QA: desktop and mobile screenshots for public landing, scoped search,
  first-face application start, and accepted handoff.
- Copy check: `account visitor`, `face`, `claims`, `reserves`, `wanted`, and
  `scene` vocabulary.
- Accessibility check: scoped-search label exposes the full realm name when
  the visible control uses initials.
- Real UAT: run the same task with 2 to 3 PBP writers after live Railway smoke
  is available.
- No collateral:

## Decisions

- Accepted: the signed-in non-member state should not look logged out.
- Accepted: scoped search should use compact realm initials when the full
  realm name is still recoverable.
- Accepted: public story orientation remains valuable for members and staff.
- Accepted: accepted application pages need immediate next-room handoff.
- Proposed: add request-access capture after production smoke is proven.
- Proposed: create a service-owned accepted-face next-move recommendation.
- Deferred: real UAT until the route is reachable in production and browser QA
  screenshots are current.
- Rejected: collapsing account visitor, member, and signed-out states into one
  generic landing variant.
- Not-now: turning the public landing page into a full application wizard.
