# Simulated UAT Session: Wanted Hook To Plotting Handoff

Status: simulated UAT
Date: 2026-05-10
Researcher: Codex
Artifact inspected: product docs and roadmap; rerun required against rendered
route or screenshot
Artifact path or URL: `docs/product/user-personas-panel.md`,
`plans/in-progress/non-ai-pbp-studio-roadmap-2026-05-10.md`,
`research/uat/protocols/wanted-to-plotting-handoff.md`
Synthetic user: Hook Hunter and Reddit 1x1 Seeker plus Director/Staff lens
Seed docs: `research/synthesis/2026-05-10-simulated-user-panel.md`
Confidence: medium

This is simulated task testing. It can expose likely friction, but it does not
replace observed user behavior.

## Task

Find a wanted hook that fits, raise interest safely, understand what happens
next, and follow the handoff into plotting or a scene.

## Success Criteria

- User can tell whether the hook is open, raised-hand, checking-fit, in
  plotting, reserved, ready for scene, scene started, filled, paused, passed,
  or archived.
- User can raise interest with an existing face or prospective concept.
- User knows what is public, hook-owner-visible, participant-visible, and
  staff-visible.
- Hook owner has a clear next action.
- Plotting room connects back to the wanted hook and forward to the scene.
- Public surfaces show safe movement without leaking private notes.

## Starting State

- User role: member or prospective applicant browsing hooks.
- Community/membership state: may or may not have a playable face.
- Face/application state: existing face or prospective concept.
- Device or viewport: mobile and desktop.
- Privacy/audience state: public/community wanted page plus private handoff.

## Expected Path

1. Browse wanted hooks.
2. Filter or inspect hook fit.
3. Review status, compatibility, boundaries, and next action.
4. Raise interest with existing face or prospective concept.
5. Hook owner sees attention-needed state.
6. Handoff moves into private plotting room.
7. Plotting room marks ready for scene and creates/links scene.
8. Wanted status updates safely.

## Simulated Task Path

1. User scans for an opening that is active and socially available.
2. User checks whether cadence, writing style, boundaries, and OOC posture fit.
3. User raises interest and looks for reassurance about visibility.
4. User expects a clear owner response and private plotting destination.
5. User expects wanted status and scene link to update after handoff.

## Failure Points

- If hook statuses are too coarse, open hooks may actually be socially stale.
- If compatibility fields are absent, mismatch and ghosting risk increase.
- If compatibility fields are too heavy, the hook feels like a dating form
  instead of story intent.
- If raised interest creates a generic message instead of object-bound
  backstage, source of truth drifts to DMs or Discord.
- If public surfaces show raised-hand counts or room links unsafely, private
  interest leaks.
- If scene creation does not update hook status, directors must clean up by
  hand.

## Trust Breaks

- Wrong-face risk: high when raising interest or starting the scene.
- Privacy/audience risk: high around interest notes, room links, hook owner
  queue, and public movement state.
- Source-of-truth risk: high if plotting is not attached to the wanted object.
- Data-loss/draft risk: medium for long interest notes.
- Design credibility risk: medium; wanted hooks need to feel like story
  openings, not classified ads.

## Vocabulary Breaks

- Avoid `lead`, `ticket`, `deal`, `message thread`, `inquiry`, and `applicant
  pipeline`.
- Prefer `wanted`, `raised hand`, `checking fit`, `in plotting`, `reserved`,
  `ready for scene`, `scene started`, `filled`, `paused`, `passed`, and
  `archived`.

## Recommended Changes

- P0: Interest notes, private room links, and counts must not leak to unrelated
  viewers.
- P0: All interest and scene-start actions should show active face or
  prospective-face context.
- P1: Wanted lifecycle should carry public-safe status and private production
  state.
- P1: Hook owner needs an attention-needed queue and clear next action.
- P1: Plotting room should be object-bound and link back to hook and forward to
  scene.
- P2: Compatibility fields should stay lightweight and story-oriented.
- P2: Add graceful `passed`, `paused`, and `closed` states to reduce ghosting.

## Required Proof

- Rendered test: hook owner, interested writer, ordinary member, participant,
  staff, director, outsider, and cross-community states.
- Service test: lifecycle transitions, interest visibility, plotting-room
  participants, scene-start status update.
- Browser QA: wanted board, wanted detail, interest form, plotting room, scene
  handoff at mobile and desktop widths.
- Copy check: lifecycle labels and compatibility fields.
- Accessibility check: forms, status labels, and private/public badges.
- Real UAT: hook hunter task against rendered wanted flow.
- No collateral:

## Decisions

- Accepted: wanted hooks are structured story-intent objects, not only ads.
- Accepted: handoff integrity is as important as discovery.
- Proposed: add wanted-to-scene simulated UAT to the wanted backstage plan's
  proof before closure.
- Deferred: real UAT until rendered wanted/plotting artifacts are available.
- Rejected: generic private messaging as the first answer to wanted handoffs.
