---
name: elbysodic-product-research
description: Use for Elbysodic product research, user research, UXR, UAT, synthetic user-panel critique, roleplay segment research, competitor audits, source notes, interview prep, observed alpha feedback, and promotion of research findings into product docs, plans, tests, or doctrine.
metadata:
  short-description: Run Elbysodic research, UXR, UAT, and user-panel workflows
---

# Elbysodic Product Research

Use this skill to route plain-language research and UX requests into the
repo's research system. Keep the skill as an orchestrator; the durable process,
templates, and protocols live in the repo.

## Core Rule

Never confuse evidence types:

- `source signal`: public source, product audit, market observation, or real
  community artifact.
- `research inference`: what Elbysodic thinks that signal means.
- `synthetic panel`: simulated user critique seeded from research and product
  constraints.
- `simulated UAT`: task-based synthetic critique against a concrete artifact.
- `real UXR`: interviews, usability tests, alpha observation, support
  conversations, or analytics.
- `product doctrine`: accepted Elbysodic stance after filtering through mission,
  tenant/identity constraints, privacy standards, and product taste.

Synthetic output is useful pressure-testing, not real interview evidence.

## Start Here

For most requests, read only the files needed:

- Research operating model: `research/README.md`
- Research steward rules: `research/AGENTS.md`
- Persona panel: `docs/product/user-personas-panel.md`
- Research system plan (archived methodology): `plans/archive/2026/product-research-system-2026-05-10.md`
- Templates: `research/templates/`
- UAT protocols: `research/uat/protocols/`

If evaluating product behavior, also read the relevant product doc, plan, route,
template, test, screenshot, or local artifact being evaluated.

## Request Routing

Classify the user's request, then use the matching artifact.

| User says | Route to | Usually read |
| --- | --- | --- |
| "turn this blog/source into research" | source note | `research/templates/source-note.md` |
| "audit RPHub/RPR/RPoL/Jcink/Discord/etc." | competitive audit | `research/templates/competitive-audit.md` |
| "ask the user panel" | synthetic panel run | `docs/product/user-personas-panel.md`, `research/templates/synthetic-panel-run.md` |
| "simulate UAT" or "test this flow" | simulated UAT | relevant `research/uat/protocols/`, `research/templates/simulated-uat-session.md` |
| "interview users" or "prep UXR" | real interview prep | `research/interviews/`, `research/templates/real-interview-note.md` |
| "observe alpha/users using it" | observed UAT | `research/templates/real-uat-observation.md` |
| "synthesize findings" | synthesis | `research/synthesis/README.md` |
| "promote this into doctrine/roadmap" | promotion review | product docs, plans, tests, `AGENTS.md` as needed |

## Workflow

1. State the evidence mode: source note, audit, synthetic panel, simulated UAT,
   real UXR, synthesis, or promotion.
2. Load the smallest useful set of docs/templates/protocols.
3. If an artifact is needed and exists, inspect it directly.
4. Write the research artifact to the appropriate folder when the user asks to
   create or run the workflow.
5. Label confidence: `high`, `medium`, `low`, or `conflict`.
6. End with accepted, proposed, deferred, rejected, and not-now findings when
   useful.
7. Promote only stable findings to `docs/product/`, `docs/architecture/`,
   `plans/`, `tests/`, or `AGENTS.md`.

## Subagents And Panels

Only spawn subagents when the user explicitly asks for agents, parallel panel
work, simulated interviews via agents, or similar delegation.

When using subagents:

- Give each panelist one persona from `docs/product/user-personas-panel.md`.
- Ask each panelist to advocate only from that user point of view.
- Require the User Panel Signal Format.
- Do not let subagents edit files unless the user explicitly asks for worker
  agents to create separate artifacts.
- The main agent owns synthesis, decisions, and file updates.

When not using subagents, run the panel locally and label it as simulated.

## UAT Selection

Prefer existing protocols:

- Public preview: `research/uat/protocols/public-realm-preview.md`
- First face: `research/uat/protocols/first-face-onboarding.md`
- Wanted handoff: `research/uat/protocols/wanted-to-plotting-handoff.md`

If no protocol exists, create a narrow protocol only when the flow is likely to
be reused. Otherwise, use `research/templates/simulated-uat-session.md`
directly.

## Promotion Rules

Promotion requires a decision:

- `accepted`: update product docs, roadmap, tests, or agent rules now.
- `proposed`: promising but needs more evidence or scoping.
- `deferred`: likely valid, but sequence later.
- `rejected`: conflicts with Elbysodic standards or weak evidence.
- `not-now`: plausible but outside the current backbone.

Do not promote:

- private interview details
- synthetic-only findings as real evidence
- one-off anecdotes as broad "users want" claims
- competitor features that violate Elbysodic's PBP, privacy, identity, or
  source-of-truth standards

## Safety And Privacy

Do not commit private handles, emails, Discord IDs, raw DMs, recordings,
screenshots from private spaces, or sensitive participant data without explicit
permission.

For real UXR, record consent level:

- `private`
- `unattributed`
- `attributed`
- `publishable`

When in doubt, summarize without identifying details.
