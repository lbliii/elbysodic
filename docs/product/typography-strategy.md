# Typography Strategy

Status: product, design, and web doctrine
Owner: Product design, web, docs, and surface-contract stewardship
Last updated: 2026-05-18

Elbysodic is a text-first roleplay product. Typography is not decoration; it is
how the product decides what is story, what is action, what is metadata, and
what is merely supporting context.

Use this guide before adding page headers, shelf headings, card titles,
eyebrows, labels, helper copy, metadata, body copy, or prose styles. Use it
with `docs/product/paragraph-rhythm.md`,
`docs/product/information-hierarchy.md`,
`docs/product/surface-quality-bar.md`, and `design/composition-bible.md`.

## Evidence Mode

This is product doctrine promoted from:

- source signal: Apple Human Interface Guidelines typography guidance for
  platform text styles, large editorial layouts, and readable scaling
  ([Apple HIG Typography](https://developer.apple.com/design/human-interface-guidelines/typography))
- source signal: Material Design's semantic type roles: display, headline,
  title, body, and label
  ([Android Material 3 Typography](https://developer.android.com/develop/ui/compose/designsystems/material3))
- source signal: Carbon's split between expressive and productive type sets for
  different product moments
  ([Carbon Typography Type Sets](https://carbondesignsystem.com/elements/typography/type-sets/))
- source signal: USWDS design-token discipline for limited type scales,
  normalized type families, line height, and measure
  ([USWDS Typesetting](https://designsystem.digital.gov/design-tokens/typesetting/overview/))
- source signal: Atlassian's guidance to use typography tokens/components and
  avoid heading styles inside small components where body text with weight is
  enough
  ([Atlassian Applying Typography](https://atlassian.design/foundations/typography/applying-typography))
- internal source: product design steward review of current Elbysodic docs,
  gateway components, and theme CSS

Confidence is medium-high. These source systems agree on roles, tokens,
hierarchy, and limited scales. Elbysodic's specific public-story register still
needs real user observation.

## Core Principle

Every visible text element must have one job and one register.

Do not let two adjacent text elements compete for the same job. If an eyebrow,
heading, subtitle, badge, helper line, and card label all orient the user, the
surface becomes noisy even when each phrase is individually clear.

The strongest public pages should read like an authored story offer. Operational
rooms can read like production tools. Neither should read like a design plan,
data model, or dashboard inventory.

## Type Ladder

Use this ladder before choosing a font size, weight, color, or text transform.

| Role | Job | Register | Typical treatment |
| --- | --- | --- | --- |
| Display title | Names the realm, place, face, scene, or ritual object | singular and emotional | largest size, display stack when useful, tight line height |
| Page title | Names the current page or workroom | clear and primary | large heading, no competing label beside it |
| Section heading | Names the next shelf or workflow region | scannable | one strong phrase, usually sentence case |
| Eyebrow/kicker | Adds a distinct axis before a heading | quiet and structural | xs, muted, uppercase only when truly structural |
| Section intro | Adds one sentence of orientation under a heading | explanatory but subordinate | body or small body, muted but readable |
| Card title | Names the story object | concrete | medium-bold, no repeated object type |
| Card summary | Sells or distinguishes the object | scannable prose | small/base, calm line height |
| Metadata | Adds timing, privacy, lifecycle, ownership, cast, or fit | factual | xs/sm, low contrast, no paragraph rhythm |
| Helper/status | Reduces uncertainty beside a control | practical | compact, local, never louder than the control |
| Prose | Carries authored writing or canon body | immersive | stable measure, relaxed line height, no chrome collision |

HTML heading level and visual type role are related but not identical. Preserve
semantic heading order for accessibility, then style through named product
roles.

## Register Rules

1. **One register per header cluster.** A shelf header can have a title, or a
   quiet eyebrow plus title, or title plus short intro. It should not have two
   co-equal title-like phrases.
2. **Eyebrows must earn a distinct axis.** Use them for audience, privacy,
   lifecycle, urgency, ownership, or mixed-object type. Do not use them only to
   restate the section category.
3. **Public landing pages do not explain themselves.** Avoid copy that names
   UX intent, product strategy, surface contracts, or implementation posture.
   The page should sell the realm, not describe the page design.
4. **Homogeneous shelves do not repeat child type labels.** In `Places`,
   children do not need `Place`. In `Wanted`, children do not need `Wanted
   hook`. In `Guidebook`, children do not need material type labels unless the
   shelf intentionally mixes unlike objects.
5. **Muted text is not hierarchy by itself.** Size, placement, spacing, and
   role must also show what matters.
6. **Uppercase is scarce.** All-caps can orient, but too many all-caps labels
   create a shouting scaffold. Keep it for compact structural markers, not
   sentence-like guidance.
7. **Component typography is a contract.** Shared components must expose named
   roles such as title, eyebrow, intro, summary, metadata, and helper. Templates
   should not freestyle weight and size for each page.

## Public Story Surfaces

Applies to `/`, `/network`, `/c/{community_slug}`, public place pages, wanted
discovery, guidebook landing pages, and first-face entry paths.

Public-story typography should feel editorial, confident, and breathable:

- Lead with the realm, place, face, chapter, hook, or guidebook object.
- Use one large story promise in the first viewport.
- Let section headings be short: `In play`, `Scenes`, `Guidebook`, `Cast`,
  `Claims`, `Wanted`, or a more authored equivalent.
- Put explanatory sentences below headings only when they add confidence or
  next-action clarity.
- Treat fit metadata as sentence-like copy when it wraps, not as a row of
  equal-weight badges.
- Keep activity and compatibility language late and quiet.

Forbidden public-story patterns:

- planning copy: `surface`, `read model`, `entry path`, `public-safe`,
  `workflow`, `preview readiness`, `setup`, `program`, `catalog`
- explanatory UX copy: `ways in before a writer has a face here`, `public
  scenes carrying the premise`, `what to know before a first face`
- repeated prefixes: `Current Chapter:` or `Premise:` inside a section already
  framed as current story, premise, or guidebook
- dashboard register: `status`, `type`, `record`, `metric`, `task`, `project`,
  `workspace`

## Productive Surfaces

Applies to Studio, Desk, casting, claims, applications, notifications, launch,
and moderation rooms.

Productive typography can be denser, but it still needs hierarchy:

- Use compact headings for rooms and rows; do not import landing-page display
  scale into production rooms.
- Use rows for comparison and queues; cards only when identity or media matters.
- Helper copy should be close to the control it explains.
- Status labels should be compact and useful: waiting, needs reply, watching,
  caught up, private, staff, draft, archived, reserved.
- Counts need an operational reason: urgency, workload, readiness, privacy, or
  availability.

## Prose And Roleplay Writing

Prose is the product's highest-trust text role.

- Keep post and canon prose in stable reading measures.
- Do not place translucent, patterned, or interactive chrome behind body prose.
- Character identity can frame prose, but it must not interrupt line rhythm.
- Composer preview should mirror the final reading rhythm closely enough that
  writers trust it before posting.

## Component Contracts

Shared components should prefer these slots:

- `eyebrow`: compact structural marker; optional; subordinate
- `title`: the main readable phrase
- `intro`: one sentence under the title; optional
- `summary`: card or row prose
- `metadata`: factual comparison details
- `action`: command text

Do not make `eyebrow` required for a shelf component. Required qualifier text
is how same-register noise becomes the default.

For public shelf headers:

- default: `title`
- optional: `title + intro`
- exception: `eyebrow + title` only when the eyebrow adds a distinct axis that
  the title cannot carry

For cards inside homogeneous shelves:

- default: `title + summary`
- optional: metadata only when it changes comparison or commitment
- exception: type label only when the shelf mixes unlike object types

## QA Checklist

Before shipping a meaningful rendered surface:

- Can a user identify the primary object in five seconds?
- Does every heading cluster have one dominant phrase?
- Are eyebrows visually and semantically subordinate?
- Could any visible text have come from a plan, schema, or test fixture?
- Does any child card repeat the parent section label?
- Does mobile stacking make secondary text louder than intended?
- Are font sizes, line heights, and measures drawn from product roles rather
  than arbitrary local values?
- Does browser QA inspect the first viewport and at least one dense lower
  section?

Accepted failures should become one of: a product doc update, a shared
component contract, a rendered-copy test, or a browser QA note.
