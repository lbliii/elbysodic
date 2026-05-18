# Surface Quality Bar

Status: product, design, and web doctrine
Owner: Product, design, web, research, and surface-contract stewardship
Last updated: 2026-05-18

This guide prevents Elbysodic surfaces from becoming dated, overwhelming,
generic SaaS, or visually noisy. Use it before implementing or materially
reshaping any public, ritual, discovery, onboarding, writing, or Studio
surface. Use `docs/product/typography-strategy.md` with this guide when a
surface needs page titles, shelf headings, eyebrows, metadata, or public-story
copy.

Evidence mode: accepted product doctrine promoted from existing product
strategy, design composition rules, research synthesis, and synthetic
user-panel assumptions. Confidence is medium until reinforced by real UXR and
observed alpha behavior.

## Product Standard

Elbysodic should feel elegant, breathable, modern, and roleplay-native. It
should help a visitor, writer, hook hunter, director, or staff member focus on
the right thing, feel the realm's promise, understand where they are, and move
with confidence.

The reference balance is:

- **Apple TV and Netflix for editorial clarity:** public homes, realm previews,
  story shelves, location gateways, wanted discovery, and other story-facing
  surfaces should sell the world with strong media, concise copy, curated
  shelves, and just enough metadata to compare fit.
- **Slack and Discord for power and layered context:** navigation, drawers,
  activity lenses, side panels, and quick return paths should reduce page
  hopping without importing chat urgency, presence pressure, or unread shame.
- **Jcink and forum PBP for depth:** guidebooks, rosters, claims, reserves,
  applications, plotters, boards, threads, scenes, and skin culture remain the
  backbone, but their density must be translated into modern information
  hierarchy instead of old forum chrome.

The product fails this bar when it looks like a Salesforce-style CRM, generic
admin dashboard, static forum index, streaming clone, or decorative skin demo.

## Surface Intent Brief

Every substantial surface change should start with a short brief. Keep it in
the plan, PR notes, or commit notes when the work is meaningful enough to
affect product direction.

- **Audience:** public visitor, invited writer, member, active-face writer,
  hook hunter, director, staff, returning regular, or safety-boundary writer.
- **First five seconds:** what should the user understand or feel before
  scrolling?
- **Primary object:** realm, place, scene, face, wanted hook, guidebook
  material, application, claim, reserve, event, Desk obligation, or Studio
  room.
- **Primary decision/action:** enter, keep reading, compare fit, start
  application, raise interest, reserve, reply, review, publish, or continue.
- **Dominant reference job:** editorial discovery, layered context, PBP depth,
  operational production, or prose-first reading.
- **Negative reference:** the specific failure to avoid, such as CRM metrics,
  card soup, route directory, launch checklist, old forum index, or chat feed.
- **Progressive disclosure:** what must be visible now, what can be one click
  away, and what belongs in a drawer or scoped page.

Do not start by asking which database fields exist. Start by naming the user
job and the emotional read.

## Density Budget

Use a density budget before adding modules, cards, metrics, badges, or helper
copy.

- One first-viewport story promise or workflow thesis.
- One primary action cluster per viewport region.
- One dominant visual object per section.
- Two or three metadata axes per story-object card unless the surface is a
  focused operations room.
- Counts only when they change confidence, urgency, privacy, availability, or
  the next action.
- No child object type labels inside homogeneous sections.
- No route-shortcut panels when persistent navigation or object-local links
  already provide the path.
- No equal-weight card grid unless the user is truly comparing peer objects.
- No elevated command panel unless the page has one contained command, warning,
  form, or preview that needs containment.

If the surface feels dense because the product has many real options, choose a
dominant journey and disclose the rest through shelves, filters, drawers, or
scoped pages.

## Anti-CRM Rules

The most common failure mode is rendering structured product data too
literally. These rules are hard stops:

- Do not turn story-facing pages into metrics dashboards.
- Do not make every section a card, every row a tile, every datum a badge, or
  every action a CTA.
- Do not expose internal taxonomy as public marketing copy.
- Do not use generic labels such as `status`, `type`, `item`, `record`,
  `project`, `task`, or `workspace` when PBP or story language exists.
- Do not show launch, readiness, moderation, or setup scaffolding to visitors
  unless that scaffolding is the actual user job.
- Do not make public/editorial pages explain implementation state instead of
  selling premise, tone, cast, places, lore, factions, hooks, activity, and
  access posture.
- Do not let staff, director, or admin controls visually dominate reader,
  applicant, or hook-hunter journeys.

Operational surfaces can be denser, but even Studio should feel like a
director production room, not enterprise software.

## Label And Copy Discipline

Context carries labels. The page title, section title, route, card shape, and
nearby action often already identify the object. Child copy should add story,
state, relationship, timing, privacy, urgency, ownership, or active-face
relevance.

Typography carries the visible contract. A heading cluster should have one
dominant phrase; qualifiers, eyebrows, and helper lines must be quieter both in
meaning and visual weight. If two adjacent lines feel like peer headings, remove
one or demote it through the typography strategy.

Before adding any eyebrow, badge, metric label, helper line, or footer, answer:

- Does the parent context already say this?
- Does it distinguish unlike objects in this exact set?
- Does it change what the user should read, click, reserve, join, answer, or
  avoid?
- Would removing it create confusion, privacy risk, or a wrong action?

If not, remove it. Spend the space on more useful story copy or let the surface
breathe.

## Visual QA Gate

For substantial rendered UI work, browser QA is part of done:

- Capture desktop and mobile screenshots or inspect the running page directly.
- Check the first viewport before scrolling.
- Confirm the eye lands on the intended object, not on chrome or metadata.
- Verify text does not overlap, truncate awkwardly, or fight its container.
- Check empty, sparse, and dense seeded states when available.
- Audit repeated labels, repeated actions, metric clutter, card soup, and
  route-directory behavior.
- Ask whether the screen still feels like modern PBP software, not generic
  forum, chat, streaming, CMS, or CRM UI.

Rendered tests prove behavior. Screenshot QA proves composition. Both matter
when a surface is visually or interactionally meaningful.

## Promotion And Proof

Accepted surface-quality findings should become at least one of:

- product docs or design doctrine
- a shared `_components/` pattern
- a service read model that prevents template-level guesswork
- rendered-page tests for behavior, privacy, labels, or available actions
- browser QA notes for substantial layout and responsive changes
- plan or not-now item when the finding is valid but out of scope

Do not leave repeated design corrections only in chat history.
