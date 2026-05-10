# Simulated UAT Session: Public Realm Preview

Status: simulated UAT
Date: 2026-05-10
Researcher: Codex
Artifact inspected: product docs and roadmap; rerun required against rendered
route or screenshot
Artifact path or URL: `docs/product/user-personas-panel.md`,
`plans/in-progress/non-ai-pbp-studio-roadmap-2026-05-10.md`,
`research/uat/protocols/public-realm-preview.md`
Synthetic user: Invited/New Face Applicant plus Modern Design Skeptic
Seed docs: `research/synthesis/2026-05-10-simulated-user-panel.md`
Confidence: medium

This is simulated task testing. It can expose likely friction, but it does not
replace observed user behavior.

## Task

Figure out whether this realm is accepting new faces, what kind of story it is,
how active it feels, and what the next safe step is.

## Success Criteria

- User can describe premise, tone, activity posture, and recruitment state.
- User can tell whether access is invite-only, request-access, closed, or open
  to applications.
- User can find guidebook/application/wanted context without seeing private
  member or staff data.
- User trusts the product enough to continue.

## Starting State

- User role: signed-out prospective writer.
- Community/membership state: no membership.
- Face/application state: no face and no application.
- Device or viewport: mobile and desktop should both work.
- Privacy/audience state: public-only.

## Expected Path

1. Land on public realm preview or public catalog card.
2. Read premise, tone, activity posture, and access state.
3. Inspect wanted hooks, guidebook/application guidance, or safe recent
   activity.
4. Choose `Request access`, `Start application`, `View wanted`, or understand
   that the realm is closed/private.

## Simulated Task Path

1. User looks for visible signs that the realm is alive and roleplay-native.
2. User tries to infer whether they can join, whether the realm is invite-only,
   and whether a first face is possible.
3. User checks whether recent activity, roster, or wanted pressure feels safe
   and current.
4. User decides whether to continue based on visual credibility and clarity of
   next action.

## Failure Points

- If the first viewport only says platform/realm name, the user cannot judge
  story premise, activity, or fit.
- If access posture is hidden behind generic signup language, the user cannot
  tell whether they are welcome.
- If recent activity is absent, stale, or too private, the realm reads as dead
  or unsafe.
- If public wanted hooks lack status, the user cannot tell whether openings are
  real.
- If the page looks dated, correct PBP primitives may still be discounted.

## Trust Breaks

- Wrong-face risk: low on signed-out public preview.
- Privacy/audience risk: public recent activity, roster summaries, wanted
  pressure, and counts can leak private participation if not service-owned.
- Source-of-truth risk: public page may imply Discord or external chat is where
  the real activity lives.
- Data-loss/draft risk: none.
- Design credibility risk: high.

## Vocabulary Breaks

- Avoid generic `community signup`, `profile`, `content`, `dashboard`, and
  `workspace` language.
- Prefer `realm`, `face`, `roster`, `wanted`, `claims`, `reserves`, `scene`,
  `thread`, `request access`, and `application`.

## Recommended Changes

- P0: Public preview must not leak private member/staff data through counts,
  recent activity, hidden route labels, or roster pressure.
- P1: Public preview should show premise, tone, activity posture, access state,
  content posture, and safe recent movement.
- P1: Primary CTA should match posture: `Request access`, `Start application`,
  `View wanted`, `Accept invite`, or closed/private state.
- P2: Add safe public statuses for wanted/opening cards so stale or filled
  hooks do not look open.
- P2: Include mobile screenshot QA before treating the public page as alpha
  ready.

## Required Proof

- Rendered test: signed-out, no-face member, ordinary member, staff, director,
  and outsider states.
- Service test: public read model excludes private/staff/member-only data.
- Browser QA: public realm preview and public catalog card at mobile and
  desktop widths.
- Copy check: PBP-native vocabulary and clear access posture.
- Accessibility check: contrast, readable long-form premise, focus order, and
  CTA clarity.
- Real UAT: applicant/design-skeptic task against screenshot or route.
- No collateral:

## Decisions

- Accepted: public preview is a trust screen, not marketing decoration.
- Accepted: design quality and safe activity signals are part of alpha
  readiness.
- Proposed: add public preview UAT to Phase 6 proof in the non-AI roadmap.
- Deferred: real UAT until a rendered preview or screenshot is available.
- Rejected: treating signed-out discovery as generic SaaS signup.
