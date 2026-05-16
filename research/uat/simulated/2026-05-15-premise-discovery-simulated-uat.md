# Simulated UAT Session: Premise Discovery And Studio Profile

Status: simulated UAT
Date: 2026-05-15
Researcher: Codex
Artifact inspected: rendered route contracts, seed personas, browser QA profile,
and implemented Studio discovery editor
Artifact path or URL: `/network`, `/studio/discovery`,
`scripts/browser_qa.py --profile premise`,
`tests/test_forum_slice.py::test_original_premise_discovery_routes_support_persona_qa`
Synthetic user: Hook Hunter, Invited/New Face Applicant, Community Director,
and Safety-Boundary Writer
Seed docs: `docs/product/user-personas-panel.md`,
`docs/architecture/seed-personas.md`,
`research/uat/protocols/public-realm-preview.md`
Confidence: medium

This is simulated task testing. It can expose likely friction, but it does not
replace observed user behavior.

## Task

Find a premise-based realm that looks playable, understand why it fits, then
verify that a director can tune the public discovery profile without leaking
member, active-face, or staff state.

## Success Criteria

- A prospective writer can filter or search by premise language such as
  `weird-town mystery`, `small-town social web`, and `strange frontier`.
- Public cards explain premise, current chapter, access posture, roster energy,
  and safe wanted/application signals.
- A director can reach `Discovery profile` from Studio and edit the catalog
  posture through PBP-native fields.
- Public discovery does not expose active-face, private queue, staff, or
  member-only state.

## Starting State

- User role: signed-out prospective writer, then seeded original-premise
  director.
- Community/membership state: no membership for public catalog; Director role
  for `harbor_director`, `signal_director`, and `wayfarer_director`.
- Face/application state: no public face; seeded director faces for Studio.
- Device or viewport: desktop and mobile browser QA profile.
- Privacy/audience state: public catalog plus director-only Studio editor.

## Expected Path

1. Open `/network`.
2. Search or scan discovery filters for a premise engine.
3. Choose a realm whose public profile gives a clear way in.
4. Switch to an original-premise director persona.
5. Open `/studio/discovery` and verify the public profile can be maintained.

## Simulated Task Path

1. The Hook Hunter searches `/network?q=weird-town mystery` and sees Signal
   Creek surfaced by the premise label and profile fields.
2. The New Face Applicant scans filter groups for play engine, lore aperture,
   ways in, pace, and touchpoint posture before opening a realm.
3. The Director uses the seeded original-premise persona default path,
   `/studio/discovery`, to inspect and maintain the public profile.
4. The Safety-Boundary Writer checks that public catalog copy does not mention
   the current active face, writer queue, staff controls, or private room data.

## Failure Points

- Discovery filters are useful only if counts remain visible and grounded in
  public-ready communities.
- Archetype labels help exploration, but overly academic labels can feel less
  playable than concrete public pitches and current chapter copy.
- Studio editing is route-proven, but the director still needs later preview
  affordances to see exactly how catalog changes will read in context.
- Browser QA now has a premise profile, but real observed UAT is still needed
  with writers who browse by trope, actor/face interest, and friend invites.

## Trust Breaks

- Wrong-face risk: low in public catalog; medium in Studio if director identity
  is unclear, mitigated by seeded persona route proof.
- Privacy/audience risk: medium because discovery aggregates public signals;
  mitigated by service-owned public read models and rendered tests.
- Source-of-truth risk: low because discovery profile is edited in Studio and
  rendered back into public catalog cards.
- Data-loss/draft risk: low for profile fields; no long-form drafts in this
  flow.
- Design credibility risk: medium until the premise profile gets routine
  desktop/mobile screenshot review.

## Vocabulary Breaks

- Avoid `workspace`, `tenant profile`, `metadata`, and `content type` in the
  rendered flow.
- Prefer `realm`, `premise`, `roster`, `wanted`, `claims`, `reserves`,
  `application`, `current chapter`, `public discovery profile`, and `ways in`.

## Recommended Changes

- P0: Keep public discovery grounded in published communities only.
- P1: Use the `premise` browser QA profile before calling the public catalog
  alpha-ready.
- P1: Preserve original-premise seed personas as the primary demo posture for
  discovery QA.
- P2: Add a Studio-side preview of the public catalog card once discovery
  editing becomes a frequent director task.
- P2: Run real UAT with hook hunters and new-face applicants after the next
  seed expansion.

## Required Proof

- Rendered test:
  `test_original_premise_discovery_routes_support_persona_qa` covers public
  network search, original-premise director Studio access, and active-face
  absence from public discovery.
- Service test: existing network read-model tests cover public/private split
  and dynamic profile counts.
- Browser QA: `uv run python scripts/browser_qa.py --profile premise --base-url
  http://127.0.0.1:8003` captures desktop/mobile public catalog, original
  premise realm hubs, and the director Studio discovery editor.
- Copy check: PBP-native vocabulary appears in the route contracts and seed
  persona docs.
- Accessibility check: browser QA checks horizontal overflow and control/text
  overflow for desktop and mobile.
- Real UAT: deferred until a larger seeded catalog exists.
- No collateral:

## Decisions

- Accepted: premise discovery needs its own browser QA profile rather than only
  generic network crawl coverage.
- Accepted: original-premise director personas are the right QA handles for
  public discovery and Studio discovery profile maintenance.
- Proposed: add public catalog card preview inside Studio discovery.
- Deferred: real UAT and screenshot critique until the expanded seed catalog is
  complete.
- Rejected: treating trope browsing, face interest, or wanted hooks as a
  substitute for premise-based community discovery.
- Not-now: adding TV Tropes or cinematic-reference skeleton fields to the
  database.
