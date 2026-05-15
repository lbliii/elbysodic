# Appearance Studio

Appearance Studio is the product boundary for community art direction. It lets
directors make a board feel like itself without making every community invent a
new forum engine.

Contemporary PBP boards use visual identity as culture: a supernatural small
town, a gothic horror town, a slice-of-life city, and a fandom academy should
not feel like the same room with different accent colors. Elbysodic should
support that range through safe tokens, media, vocabulary, and approved
presentation variants while preserving the same operational grammar.

Use this guide before adding theme controls, visual variants, community media,
skin-like settings, guidebook layouts, postbit options, or program blueprint
appearance fields.

Use `docs/product/experience-direction.md` first when the visual decision needs
the current reference synthesis. Appearance Studio should preserve Jcink/forum
aesthetic sovereignty, meet modern RP-platform polish expectations, support
cinematic/editorial ritual surfaces, and keep Slack-like context or activity
patterns subordinate to PBP prose, active-face safety, and privacy.

## Modern Design Bar

Elbysodic must not look like preserved 2014 forum software with a nicer coat of
paint. The product should preserve forum-PBP power while feeling contemporary,
calm, and roleplay-native on first contact.

Elbysodic's default visual direction is technicolor futurism: saturated enough
to feel alive, speculative enough to feel current, and expressive enough to
honor board culture. That does not mean every screen should be loud. The
strongest color, media, glow, texture, and poster treatment should appear where
they carry identity, ritual, or atmosphere. Operational surfaces should inherit
that world through tokens, accents, and restrained material choices while
staying quiet enough for writers and directors to scan, compare, and act.

Competitive signal from RPHub matters here. RPHub demonstrates that a modern
roleplay platform can look clean, current, image-rich, mobile-conscious, and
visibly built for roleplayers without abandoning character identity,
communities, events, galleries, forum feedback, or moderation policy. Elbysodic
should treat that as the minimum public-facing design bar, not as a style to
copy.

The visual standard:

- First viewport says "purpose-built roleplay product," not generic SaaS,
  generic forum, or nostalgic skin archive.
- Character, community, scene, and wanted surfaces use strong media and clear
  identity hierarchy without burying the next action.
- Dense operational screens still feel current through spacing, typography,
  contrast, motion restraint, and clear state, not decoration.
- Mobile layouts feel designed, not collapsed from desktop.
- Default themes are good enough that a director can launch without custom
  skin labor.
- Customization improves atmosphere within Elbysodic's control spectrum; it
  must not be required to make the product feel alive.

## Technicolor Restraint

The product should feel more like a polished application for vivid writing
worlds than a dashboard wrapped in forum skin. Use technicolor futurism as a
controlled atmosphere system:

- Let identity surfaces carry the brightest treatment: world gateways,
  board/location heroes, character hubs, wanted hooks, guidebook covers, and
  event notices.
- Let work surfaces breathe: Writer Desk, queues, notifications, applications,
  claims, reserves, Studio production rooms, and form-heavy pages should use
  open rhythm, smaller headings, quiet borders, compact rows, and one clear
  command area.
- Prefer atmospheric accents over framed decoration on operational pages:
  color bars, status dots, media thumbnails, subtle texture, and typography can
  carry the room without putting every object inside an elevated card.
- Reserve high-contrast panels for current commands, forms, warnings, previews,
  and selected story objects. A page section does not need a card just because
  it has a heading.
- Size app-room typography one notch below landing or ritual surfaces. Hero
  scale belongs to public promise and major world identity, not every Studio or
  Desk header.
- Keep negative space useful. Openness should separate jobs and give prose room
  to lead; it should not hide next actions, active-face context, or state.

Reference patterns worth studying:

- Railway Central Station keeps a high-volume community/support surface
  scannable with search, sparse navigation, compact CTA/stat treatment, and
  plain thread lists.
- Linear's 2026 interface refresh is a useful model for reducing equal-weight
  chrome: important work stays foregrounded while navigation, borders, icons,
  and support controls recede.
- Vercel and shadcn-style application layouts show how modern app shells use
  stable navigation, compact headers, grouped sidebars, command/search
  shortcuts, tables, rows, and only a small number of summary cards.

These are reference behaviors, not styles to copy. Elbysodic should translate
them into PBP-native surfaces with faces, scenes, wanted hooks, claims,
reserves, plotters, and active-face identity intact.

## Product Boundary

Appearance Studio changes atmosphere. It does not change safety contracts.

Allowed:

- Light, dark, and system theme color tokens.
- Display, body, and mono font stack keys from an allowlist.
- Radius, density, and texture presets.
- Community, board, material, event, badge, facet, and character media slots.
- Approved presentation variants for repeated PBP surfaces.
- Community vocabulary for director-owned labels, facets, and navigation
  section language.
- Preview and health-warning tools that show how a board will read before
  changes publish.

Disallowed in ordinary director tools:

- Raw CSS selectors.
- Arbitrary HTML templates.
- External font URLs.
- Script tags or per-community JavaScript.
- Full layout builders.
- Theme controls that alter permissions, private/staff visibility, canonical
  workflow state, or route ownership.
- Per-community topbar realm structure.

If a proposed control needs raw CSS, arbitrary markup, or custom script to
work, it is not an Appearance Studio V1 control. It may belong in a future
curated skin-pack or plugin system with a separate safety model.

## Stable Product Grammar

These surfaces are operational. They may inherit theme tokens, but their
structure and behavior stay product-owned:

- Composer controls, preview parity, local drafts, and mention helpers.
- Queue actions, unread navigation, notifications, and Writer Desk obligations.
- Staff review workflows, permissions, private rooms, and recovery pages.
- Topbar realms and the difference between World, Guidebook, Wanted, Writer
  Desk, and Studio.
- Form labels, validation, destructive confirmations, and keyboard reachability.
- Safe post/canon/hook markup rendering.

Directors can make the room feel different around these workflows. They should
not be able to hide required controls, make labels unreadable, or resize the
writing surface into instability.

## Ritual Surfaces

Ritual surfaces are where PBP culture expects art direction. They carry mood,
identity, and community promise.

| Surface | Expression Level | Safe Controls | Product-Owned Constraints |
| --- | --- | --- | --- |
| World gateway | High | hero media, theme tokens, texture, density, featured board/material treatment | topbar realm, active-face context, readable section rhythm |
| Guidebook/material pages | High | cover media, material variant, theme tokens, event/current-material notices | safe prose, status visibility, draft privacy |
| Board/location pages | High | board image, tagline treatment, place variant, facet colors | board hierarchy, thread actions, private-board rules |
| Thread postbit | High | post rail variant, character accent, border/accent/title/density tokens | prose measure, composer placement, author recognition, preview parity |
| Character hub | High | poster/avatar, profile variant, accent source, facet/member-group color | ownership actions, active-face defaults, profile privacy |
| Wanted hooks | High | wanted variant, related material/event styling, creator face media | interest/reserve workflow, hook status, prospective concept rules |
| Event notices | High | notice variant, event accent/media, seasonal pressure copy | notice role, action placement, warning semantics |
| Applications and claims | Medium-high | application guide styling, claim group colors/icons, role/category visuals | staff review privacy, revision state, claim/reserve rules |
| Roster and discovery cards | Medium | card density, avatar/poster treatment, facet colors | filter meaning, active-face relevance, accessible links |
| Sidebar labels | Medium | section labels, ordering, optional configured collections | realm model, active state, permission filtering |
| Studio forms | Low | theme inheritance only | form labels, validation, health warnings, staff-only access |
| Recovery and private surfaces | Low | theme inheritance only | privacy, clarity, route recovery logic |

When a surface moves from one-off styling into a repeated PBP concept, promote
the shape into `src/elbysodic/web/pages/_components/` and document the visual
meaning in `docs/product/information-hierarchy.md` or this file.

## Token Families

### Theme Mode Tokens

Each community theme can define light and dark values for:

- background
- subtle background
- surface
- elevated surface
- border
- text
- muted text
- accent
- accent hover
- accent dim
- secondary accent
- success
- warning
- error

System mode resolves to light or dark values based on the viewer's preferred
color scheme.

### Typography Tokens

Typography uses allowlisted stack keys:

- `system`
- `serif`
- `condensed`
- `mono`

Do not add arbitrary font URLs to community input. If a new stack is useful
for multiple boards, add it as a named allowlist key and test representative
surfaces.

### Shape And Texture Tokens

Radius, density, and texture should remain presets. They can change the room's
character without changing the underlying layout contract.

Current safe texture direction:

- `none`
- `grid`
- `paper`
- `scanline`

Textures must stay subtle enough that story prose remains the foreground.

## Presentation Variants

Presentation variants are named component states, not templates. They may
change composition inside a stable frame, but they must preserve:

- semantic headings and labels
- keyboard and touch access
- mobile wrapping
- contrast and prose readability
- safe markup output
- permission and role visibility
- no layout shift in repeated reading surfaces

Candidate variant families:

- Guidebook material: `chapter`, `dossier`, `noticeboard`, `archive`.
- Board/location hero: `poster`, `map`, `directory`, `field-note`.
- Wanted hook: `casting-call`, `relationship`, `faction-seat`, `event-role`.
- Character hub: `profile-dossier`, `poster-profile`, `roster-sheet`,
  `journal`.
- Event notice: `seasonal-pressure`, `danger-bridge`, `festival-banner`,
  `staff-briefing`.

Add a variant only when it represents a repeated PBP ritual. Do not add a
variant just to satisfy one board's one-off skin idea.

## Media Slots

Media should map to product meaning:

- community mark
- world hero image
- board/location image
- material cover
- event banner
- badge image
- facet or member-group icon
- character avatar
- character poster

Director-managed media needs alt text or a documented decorative role. Start
with URL-backed fields where the product already uses URLs. Do not add an
upload pipeline without a separate storage, moderation, and security plan.

## Health Warnings

Appearance Studio should warn directors when a choice may hurt readability or
coherence.

Hard validation:

- invalid color syntax
- unknown font/radius/density/texture key
- unknown presentation variant
- missing required alt text for meaningful media

Soft warnings:

- low text/background contrast
- low muted-text contrast
- accent too close to the background or surface
- warning/error colors too close to the surface
- theme density that makes long-form prose feel cramped

Warnings should name the affected PBP surface: "Guidebook body text may be hard
to read" is better than "contrast ratio failed."

## Blueprint Boundary

Program Blueprints may carry approved appearance tokens and variant keys. They
must not become a CSS or layout format.

Blueprint validation should reject:

- raw CSS
- scripts
- external font URLs
- unknown token keys
- unknown variant keys
- invalid colors

Blueprint preview should summarize appearance in director language, such as:

```text
1 theme, 2 guidebook variants, postbit: poster rail + hairline frame
```

Hydration should use normal service and repository boundaries, keep objects
community-scoped, and set defaults only through explicit theme/appearance
fields.

## Review Questions

Before adding an appearance control, ask:

1. Is this changing atmosphere or changing workflow?
2. Which PBP ritual surface does it serve?
3. Can it be expressed as a token, media slot, vocabulary choice, or approved
   variant?
4. Does it preserve composer stability, safe prose rendering, mobile layout,
   and keyboard access?
5. Does it need light, dark, and system behavior?
6. Can a health warning catch risky but nonfatal choices?
7. Is the setting community-scoped?
8. Does the value need to be importable/exportable through Program Blueprints
   later?
