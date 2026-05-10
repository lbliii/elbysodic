# Research

Research captures input signal for Elbysodic: user needs, market patterns,
roleplay ecosystem norms, competitive audits, public source notes, interviews,
and outreach leads.

This folder is not product doctrine. Elbysodic uses research the way an
opinionated product studio should: ingest broad signal, identify patterns,
reject weak or misaligned assumptions, and distill the remainder into a clear
branded perspective. Product doctrine lives in `docs/product/`. Roadmap
commitments live in `plans/`.

## Operating Model

```text
public source or product artifact
  -> source note / audit
  -> research synthesis
  -> synthetic panel critique
  -> product hypothesis
  -> prototype or implemented flow
  -> simulated UAT
  -> real interview, usability test, or alpha observation
  -> accepted doctrine, roadmap item, test, or not-now decision
```

Research should preserve the difference between:

- **Source signal:** what a public source, participant, community, or product
  actually says or demonstrates.
- **Inference:** what we think that signal means.
- **Synthetic panel:** simulated user critique seeded from research and product
  constraints.
- **Simulated UAT:** task-based critique by synthetic users against a concrete
  artifact, route, screenshot, plan, prototype, or implemented flow.
- **Real UXR:** interviews, observed usability tasks, alpha observation, support
  conversations, or analytics.
- **Product implication:** what Elbysodic might do with it.
- **Doctrine:** what Elbysodic has accepted as part of its own product point of
  view.

## Directory Map

```text
research/
  AGENTS.md
  README.md
  templates/
    source-note.md
    competitive-audit.md
    synthetic-panel-run.md
    simulated-uat-session.md
    real-interview-note.md
    real-uat-observation.md
  sources/
    roleplay-ecosystem/
    platform-audits/
    blogs-and-thinkers/
  interviews/
    protocols/
    notes/
    synthesis/
  outreach/
    leads.md
    templates.md
    contact-log.md
  uat/
    protocols/
    simulated/
    observed/
  synthesis/
    2026-05-10-simulated-user-panel.md
    2026-wave-2-modern-pbp-delta.md
    2014-delta-agenda.md
    roleplayer-segments.md
    painpoints.md
    throughlines.md
    product-bets.md
    open-questions.md
```

Create subdirectories only when they are needed. Keep small research efforts in
one well-sourced note instead of scattering fragments.

## Product Posture

Elbysodic should learn from forum PBP, Discord RP, Reddit partner search,
Tumblr indie RP, TTRPG PbP, MMO/live RP, OC/art communities, and hybrid
operators without becoming a lowest-common-denominator tool.

The intended product stance is opinionated:

- Preserve character identity, scene continuity, pseudonymity, consent,
  community atmosphere, and board-running work.
- Treat durable PBP forum structure as the backbone: boards, scenes, threads,
  rosters, faces, claims, reserves, wanted hooks, guidebooks, archives, and
  staff/director workflows remain the source of truth.
- Treat lite rapid touchpoints as escape hatches and adjuncts: chatbox-style
  banter, IC texts, AIM-like exchanges, phone-call transcripts, quick scene
  beats, and Discord-like coordination can exist, but they should not replace
  the durable scene and community record.
- Provide knobs inside a curated spectrum of control.
- Prefer excellent defaults over open-ended configuration.
- Refuse controls that break safety, readability, authorship, privacy,
  continuity, or PBP-native vocabulary.
- Treat raw ecosystem demand as signal, not instruction.

## Founder Baseline

Current founder context:

- The remembered high-water mark is roughly 2014-era forum PBP: durable boards,
  threaded scenes, claims, applications, rosters, skins, plotters, cboxes,
  Bravenet/chatbox side channels, AIM/text-message style rapid beats, and
  director-run community ritual.
- The suspected modern gap is that RP culture has splintered into Discord,
  Reddit partner search, Tumblr, aging forums, private servers, and niche
  tooling without one dedicated platform that treats PBP as the product center.
- Research's job is to find the delta since that baseline, not to validate
  nostalgia. Preserve what still matters, reject what was brittle, and identify
  which modern habits deserve first-class product primitives.

## Promotion Rules

Promote research when it becomes stable enough to guide product work:

- `docs/product/`: accepted product language, UX doctrine, product principles,
  and branded point of view.
- `docs/architecture/`: accepted tenant, identity, privacy, persistence, or
  security implications.
- `plans/`: sequenced roadmap work or implementation slices.
- root/scoped `AGENTS.md`: durable agent operating rules or steward checklists.

Do not promote:

- one-off anecdotes
- unvalidated assumptions
- private interview details
- competitor features that conflict with Elbysodic standards
- broad "users want" claims without source breadth

## Confidence Labels

Use these labels in notes and synthesis:

- `high`: repeated source signal plus real UXR or live alpha behavior.
- `medium`: repeated source signal plus synthetic panel convergence, or one
  strong real-user finding that still needs broader validation.
- `low`: plausible single-source or synthetic-only signal.
- `conflict`: credible sources disagree or cultures value opposite outcomes.

## Templates

Start from `research/templates/` when adding new notes:

- `source-note.md`
- `competitive-audit.md`
- `synthetic-panel-run.md`
- `simulated-uat-session.md`
- `real-interview-note.md`
- `real-uat-observation.md`
