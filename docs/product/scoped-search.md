# Scoped Search

Search is a top-chrome utility, not a page-bottom fallback panel. It should let
people move from their current context without making every page repeat a
search box, shortcut wall, or filter matrix.

## Jobs

Search has two primary scopes:

| Scope | Where It Appears | Job |
| --- | --- | --- |
| All realms | Product home, Network, signed-out product routes | Find public realms by premise, pace, hooks, roster shape, current chapter, and browsing posture. |
| Current realm | Community routes | Find public-safe material inside the current realm: guidebook entries, places, scenes, wanted hooks, cast, claims, and current premise context. |

The topbar owns the entry point because search is cross-cutting. Page content
can show search results, local filters, and advanced browse controls, but the
page should not add another generic search launcher unless search is the
surface's primary job.

## Interaction Contract

- Product routes default to `All realms`.
- Community routes default to the current realm.
- A scoped result page can offer a secondary path to broaden from current realm
  to all realms.
- Empty searches do not render a wall of every possible facet. Show the search
  control and a small set of useful browse paths instead.
- Result cards inherit their section context. Avoid repeating labels like
  `Realm`, `Scene`, `Wanted`, or `Guidebook` inside every child when the result
  group already says what is being shown.
- Topbar search must stay compact enough to coexist with identity, community
  brand, notifications, and mobile navigation.

## Visual Contract

- Use one visible scope chip or label at the start of the control.
- The full realm name is the primary scope label on roomy layouts. Compact
  topbar layouts may show the realm monogram or initials such as `AA`, but the
  accessible label and search results heading must still name the full realm.
- Use a placeholder for examples, not instructions.
- Keep the submit affordance compact; icon-only is acceptable once an
  accessible name is present.
- Do not place search under long shelves or return-path panels on the Network
  home. That position reads like leftover boilerplate and hides the utility
  when people need it.
- Results should prioritize readable titles, concise story-facing summaries,
  and direct movement. Counts belong at the card or section edge only when they
  change the user's decision.

## Privacy Contract

Current-realm search is rendered from public-safe read models for signed-out
visitors. Signed-in members may see member-safe results only when the service
contract explicitly includes membership, role, and active-face boundaries.

Search must not leak:

- private boards, scenes, or materials
- staff-only workflow state
- draft wanted hooks or unreviewed continuity
- private membership, application, queue, or notification state
- character or face data outside the current community

When in doubt, ship the public-safe result first and add member/deck lanes only
after the service contract and tests prove the boundary.
