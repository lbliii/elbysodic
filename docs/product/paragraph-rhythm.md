# Paragraph Rhythm And Text Roles

Elbysodic is a text-based writing app, so paragraph styling is not decoration.
It is product infrastructure. Every `<p>` should have a job: story prose,
atmosphere, summary, helper copy, metadata, status, or empty-state guidance.

Use this guide before adding or changing paragraph output in templates,
components, composer previews, rendered markup, hero sections, cards, forms, or
post frames.
Use `docs/product/typography-strategy.md` alongside it when a text element is a
heading, eyebrow, label, metadata line, or public-story shelf title rather than
paragraph-like copy.

## Inventory Baseline

Current template and preview output contains about 293 `<p>` outputs across the
web layer. The largest concentrations are:

- `src/elbysodic/web/pages/studio/page.html`: director guidance, row decisions,
  health warnings, empty states, and production room copy.
- `src/elbysodic/web/pages/boards/{board_slug}/threads/{thread_slug}/page.html`:
  scene header copy, transcript metadata, composer helper text, and rendered
  post bodies.
- `src/elbysodic/web/pages/boards/{board_slug}/page.html`: board hero loglines,
  descriptions, section introductions, and empty states.
- `src/elbysodic/web/pages/characters/{character_slug}/page.html`: profile
  summaries, plotter/wanted descriptions, edit hints, and tracker empty states.
- `src/elbysodic/web/pages/_components/thread_summary.html`: scene-card
  summaries, metadata, credits, and snippets.
- `src/elbysodic/web/pages/_components/posts.html` plus
  `src/elbysodic/services/markup.py` and
  `src/elbysodic/web/static/elbysodic-composer.js`: the highest-value
  paragraph system, because this is where writers read and preview posts.

The current weakness is not that `<p>` appears often. The weakness is that many
paragraphs rely on generic inheritance or `chirpui-text-muted` when they are
doing different jobs. Muted hero lead, muted card summary, muted form hint, and
muted metadata should not all be one visual voice.

## Paragraph Roles

### Story Prose

Use for rendered posts, post previews, quoted text, and future long-form canon
body. This is the most important paragraph role in the product.

Contract:

- Keep a stable readable measure, usually `64ch` to `72ch`.
- Use relaxed line height, with meaningful space between paragraphs.
- Never let custom post borders, cards, rails, or controls touch the prose.
- Preserve author formatting from safe markup without letting it break the
  reading column.
- Treat blockquotes as prose blocks, not generic callouts.

Current anchors:

- `.elbysodic-prose-body`
- `.elbysodic-post-content`
- `.elbysodic-prose-body--canon`
- `.elbysodic-prose-body--hook`
- `.elbysodic-composer-preview`
- rendered `<p>` from `services/markup.py`
- client preview `<p>` from `elbysodic-composer.js`

Posts, canon, and hooks share the same safe markup shape, but they should not
all borrow post-specific naming. Use `.elbysodic-prose-body` for the shared
reading contract. Compose it with `.elbysodic-post-content` for character posts
and composer previews, `.elbysodic-prose-body--canon` for world materials, and
`.elbysodic-prose-body--hook` for wanted and plot-hook pitches.

### Hero Lead

Use for the main atmospheric line below a page hero title: world gateway,
guidebook, board stage, scene stage, material pages, character profile, and
studio command surfaces.

Contract:

- Larger than card summaries and helper text.
- Not too pale; it should carry atmosphere, not disappear.
- Line height should feel calm on mobile and desktop.
- Keep width narrower than the full page so the line reads like authored copy.

Prefer a named class such as `elbysodic-copy-lead` or a component-specific class
when the hero has special layout constraints.

### Section Intro

Use for short paragraphs beneath section headings: "Scenes here", "Write now",
"Desk shortcuts", "Sublocations", or similar local guidance.

Contract:

- Medium weight and muted enough to stay below the heading.
- Should not look like metadata.
- Usually one sentence. If it becomes longer, it may need a card, disclosure, or
  a stronger content component.

Prefer `elbysodic-copy-section` over a bare `<p>` when the text is repeated.

### Card Summary

Use for summaries on scene cards, wanted hooks, plot hooks, members, characters,
materials, locations, and preview rows.

Contract:

- Scannable before beautiful.
- Use line-height around `1.35` to `1.5`.
- Clamp only when the card layout requires a stable height; otherwise let the
  text breathe.
- Do not style as a pill or badge. A summary is prose, not a tag.

Prefer product-specific classes such as `elbysodic-thread-card__summary`,
`elbysodic-board-card__description`, or a shared summary helper when the shape
repeats.

### Helper Copy

Use for form hints, composer hints, explainers inside controls, and director
setup guidance.

Contract:

- Muted, compact, and close to the control it explains.
- Clear enough to reduce anxiety, but never the most visually prominent thing in
  the room.
- Prefer action-specific wording over generic instructions.

Use ChirpUI field help classes for field-adjacent copy. Use an Elbysodic helper
class for product guidance inside cards or disclosures.

### Metadata Paragraph

Use only when a paragraph-shaped block is the right semantic fit for metadata:
writer lines, latest snippets, credits, status descriptions, or counts with
context.

Contract:

- Small, muted, and stable.
- If it is just a label/value fact, prefer a `span`, `time`, `dl`, or the
  existing metadata vocabulary instead of `<p>`.
- If it is clickable navigation context, use `LatestLine` or a named local
  metadata class.

Do not use `chirpui-text-muted` as a catch-all for every metadata paragraph.

### Kicker And Type Label

Current templates often render kickers as `<p>`. This is acceptable when the
kicker is visual supporting text rather than a document heading.

Contract:

- Uppercase, compact, and strong enough to orient the section.
- Never carry paragraph rhythm or prose spacing.
- Use only with a named kicker/type class.
- Never compete with the adjacent heading. A kicker is quieter than the title in
  size, weight, color, and meaning.
- Do not require kickers in public shelf components; most public shelves should
  use a title and optional intro instead.

If the text is the actual section heading, use a heading element instead.

### Empty State

Use for quiet absences: no threads, no visible posts, no active reserves, no
notifications, no matching discovery results.

Contract:

- Reassuring and specific.
- Enough contrast to be readable, but visually quiet.
- Can include a next action nearby, but the paragraph itself should not pretend
  to be the action.
- For queues, prefer "caught up" or "nothing is waiting" over generic absence.
- Name the surface in product language: scenes, faces, hooks, guidance, raised
  hands, or director attention.
- Avoid dead-end "No X yet" copy unless the object itself is the important
  noun and no stronger workflow context exists.

Use `elbysodic-empty-state` or a component-specific empty-state class.

### Live Status

Use for draft save status, preview empty text, validation messages, and aria
live feedback.

Contract:

- Compact and local.
- The style should distinguish neutral status from errors and successes.
- Keep `aria-live` text short; long live paragraphs become noisy.

## Design Matrix

| Role | Typical Surfaces | Voice | Size | Measure | Rhythm |
| --- | --- | --- | --- | --- | --- |
| Story Prose | Posts, composer preview, canon body | readable, immersive | base | 64-72ch | relaxed, paragraph gap |
| Hero Lead | Home, board, scene, material, character, studio heroes | atmospheric | lg-xl | narrow | calm, no crowding |
| Section Intro | Section headers and local workrooms | orienting | base-md | medium | light gap under heading |
| Card Summary | Scene cards, wanted, plot hooks, roster, previews | scannable | sm-base | card-bound | compact |
| Helper Copy | Forms, composer, setup panels | practical | sm | local | tight to control |
| Metadata Paragraph | bylines, credits, latest, snippets | factual | xs-sm | inline or short block | tight |
| Kicker/Type Label | cards, room headers, stage labels | structural | xs-sm | short | no paragraph rhythm |
| Empty State | lists and queues | reassuring | sm-base | medium | centered or local |
| Live Status | drafts, validation, preview | immediate | xs-sm | local | no extra rhythm |

## Implementation Rules

- Do not add bare `<p>` in a shared component unless its parent component owns
  the paragraph styling.
- Do not use `chirpui-text-muted` as a substitute for deciding the paragraph's
  role.
- Product copy that appears in more than one surface should use a shared
  Elbysodic role class or component slot.
- Real prose should stay inside `.elbysodic-prose-body` plus the appropriate
  variant: post, canon, hook, or preview.
- Hero and card paragraphs should not inherit prose paragraph gaps.
- Metadata that is not sentence-like should usually not be a paragraph.
- If a paragraph is visible next to a control, decide whether it is helper copy,
  status, or metadata before styling it.
- If a paragraph is hidden behind hover, disclosure, or a compact menu, it still
  needs a role class because hidden text often becomes visible on mobile.

## Sweep Plan

1. Name the shared paragraph roles in CSS: lead, section intro, card summary,
   helper, metadata, empty state, live status, and prose body.
2. Move repeated anonymous paragraphs in shared components to those role
   classes first: thread cards, wanted/plot hook cards, board/place cards,
   command panels, lane previews, post previews, and composer shells.
3. Audit page-local bare paragraphs and decide whether each is hero lead,
   section intro, helper copy, or metadata.
4. Strengthen `.elbysodic-prose-body` as the canonical PBP reading rhythm and
   mirror the post variant in composer preview so writers trust what they see
   before posting.
5. Add visual/browser checks for representative surfaces: home, board, thread,
   character profile, wanted detail, material page, Studio, Writer Desk, and
   mobile thread reading.
6. After role classes are stable, consider replacing paragraph-shaped metadata
   with semantic `span`, `time`, `dl`, or vocabulary helpers where it improves
   accessibility and scan.

## Review Questions

When touching a `<p>`, ask:

- Is this meant to be read as prose, skimmed as summary, or noticed as
  metadata?
- Should this paragraph affect layout rhythm, or should the parent component
  own spacing?
- Is muted color enough, or does this paragraph need a named role?
- Could this be a heading, label, `time`, `span`, or description list instead?
- Does it still read well on mobile, where hidden or secondary copy often
  becomes stacked and more prominent?
