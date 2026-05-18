# Product Experience Direction

Status: product and design doctrine
Owner: Product, design, web, research, and steward coordination
Last updated: 2026-05-18

This is the short synthesis for Elbysodic's current product experience
direction. Use it with `docs/product/strategy-spine.md`,
`docs/product/appearance-studio.md`, `docs/product/navigation-menus.md`,
`docs/product/information-hierarchy.md`,
`docs/product/surface-quality-bar.md`, and `design/technicolor-futurism.md`.
Use `docs/product/typography-strategy.md` when deciding how page titles,
shelves, labels, metadata, and prose should visually relate.
Use `design/composition-bible.md` when the question is page rhythm, surface
choice, chrome layering, media placement, mobile composition, or bad layout
patterns.

It distills the latest research, static mocks, user-panel synthesis, and
implementation direction into one decision rule:

> Elbysodic is Jcink/forum PBP source-of-truth depth, Slack-like layered
> context, and Netflix/Apple TV-like editorial discovery, filtered through
> technicolor futurism, PBP vocabulary, tenant privacy, active-face safety, and
> community aesthetic control.

This is not a style mashup. Each reference class contributes a job, and
Elbysodic rejects the parts that would weaken long-form writing, pseudonymous
identity, staff trust, or durable archives.

## Reference Translation

### Jcink And Forum PBP: Cultural Backbone

Carry forward:

- boards, threads, scenes, guidebooks, rosters, faces, applications, claims,
  reserves, wanted ads, plotters, staff rooms, activity expectations, archives,
  and skin culture
- directors' need to make a realm feel authored and socially specific
- writers' need for face identity, posting context, long-form prose rhythm,
  and stable scene URLs

Translate into native product objects:

- claims, reserves, wanted hooks, plotters, applications, events, materials,
  and operation queues should have state, permissions, reminders, and handoffs
  instead of living only as manually edited threads
- visual identity should come through safe tokens, media slots, presentation
  variants, and health checks, not raw CSS, arbitrary templates, scripts, or
  external font URLs

Reject:

- nostalgia as default art direction
- global characters or staff power detached from community membership
- board-running material forced into generic threads when it deserves a
  product primitive
- "prettier Jcink" as the product strategy

### Slack And Discord: Layered Context, Not Chat Replacement

Carry forward:

- layered navigation where a writer can keep location, scene, obligations, and
  nearby context in view
- drawers, side panels, activity lenses, and quick context previews that reduce
  page-hopping
- fast recognition of what needs reply, what is waiting, what is watched, and
  what is caught up

Translate into PBP grammar:

- `writer_activity_drawer` becomes Writer Desk work: needs reply, waiting,
  watching, caught up, claims, reserves, wanted updates, and plotting handoffs
- `location_scene_lane` becomes a scene-in-place reader aid, not a channel list
- `scene_grounding_inspector` becomes service-owned place, cast, event,
  visibility, and future source/provenance context

Reject:

- canonical scene prose as nested chat replies
- presence pressure, unread anxiety, or chat-like urgency as the default tone
- flattening account, membership, face, and character into one user-profile
  pattern
- Discord as the canonical archive

### Netflix And Apple TV: Editorial Discovery, Not Passive Viewing

Carry forward:

- cinematic world identity, large media, curated shelves, continuation lanes,
  tight metadata, and quick decision context
- a public home that answers which realm a writer might want to enter now
- Explore/search surfaces that help writers compare mood, genre, wanted
  pressure, activity, and access posture

Translate into PBP actions:

- replace passive "watch" language with enter realm, continue writing, answer
  queue, start application, express interest, reserve a wanted, open a plotting
  room, or browse scenes
- use structured public catalog read models so editorial rows do not leak
  membership, active-face, application, private, or staff state

Reject:

- streaming choice paralysis
- autoplay, hidden essential controls, or cinematic treatment that buries the
  next writing action
- a dark Netflix clone

### RPHub And Modern RP Platforms: Minimum Polish Bar

Carry forward:

- clean, current, image-rich, mobile-conscious roleplay software can exist in
  this category
- character, community, event, gallery, forum, moderation, and roadmap surfaces
  can look modern without abandoning RP-native primitives

Translate into Elbysodic:

- the default experience should feel alive before a director customizes it
- public and ritual surfaces should be media-aware and roleplay-specific
- operational surfaces should stay calm, precise, and readable while inheriting
  the realm's atmosphere through tokens and small visual signals

Reject:

- copying RPHub's visual language
- letting "forum backbone" become permission to ship dated defaults

## System Rules

- **Source of truth over touchpoint:** Discord, chatbox, IC text, phone-call,
  and other rapid-touch flows may support play, but durable scene continuity,
  face identity, privacy, and archive state live in Elbysodic.
- **Reading first:** prose, scene context, active face, and safe composer
  behavior outrank atmosphere on thread and writing surfaces.
- **Layered, not duplicated:** outer rail, inner shell, page chrome, drawers,
  and object-local controls must each answer a different question.
- **Context carries labels:** page and section framing identify the object
  class; child cards, rows, badges, and footers add only distinctions the
  parent context does not already provide. A `Places` shelf does not need
  `Scene hub` on every place, a wanted room does not need `Wanted hook` on
  every hook, and a current-premise hero should not repeat the same chapter
  label as an eyebrow, sentence, metric, and footer.
- **Editorial, not dashboard:** Studio and Desk can be dense, but they should
  use edited rows, lanes, command areas, and state language instead of generic
  SaaS cards everywhere.
- **Aesthetic sovereignty inside guardrails:** communities should look like
  themselves through safe tokens, media, variants, density, and vocabulary, not
  unsafe skin imports.
- **Privacy is visible UX:** public, member, participant, staff, owner, draft,
  and external boundaries should be visible in copy and enforced before
  rendering.
- **Active face is a trust surface:** commitment controls should say `Reply as
  <face>`, `Join as <face>`, or `Raise interest as <face>` whenever authorship
  or story context matters.

## Surface Implications

| Surface | Direction |
| --- | --- |
| Public home | Cinematic editorial front door with featured realm media, continuation lanes when signed in, curated shelves, and privacy-safe public metadata. |
| Explore | Search and browse by story fit: genre, mood, wanted pressure, public activity, access posture, and open playable context. |
| Community shell | Icon-first persistent rooms plus explanatory inner context. Navigation is a privacy boundary. |
| Location and thread reader | Scene remains the emotional center; location lane and grounding inspector support orientation without becoming chat chrome. |
| Writer Desk | Obligations and continuation, not a generic inbox. Needs reply, waiting, watching, caught up, plotting, applications, and wanted handoffs lead. |
| Wanted and Backstage | Discovery becomes story intent with clear handoff states, participant privacy, and playable next steps. |
| Studio | Director jobs grouped by launch, operations, intake, boards, materials, appearance, and continuity; use production language, not admin SaaS language. |
| Appearance Studio | Safe community art direction through tokens, media, presentation variants, previews, and health warnings. |

## Review Questions

- Which reference job is this borrowing: forum/PBP backbone, layered context,
  editorial discovery, or modern polish?
- Which parts of that reference are explicitly rejected here?
- Does the surface keep PBP language visible: face, roster, thread, scene,
  plotter, wanted, claims, reserves, needs reply, waiting, caught up, watching?
- Is the active face and public authorship clearer at the point of commitment?
- Does any cinematic, glass, drawer, card, rail, or activity treatment hide a
  privacy boundary or make long-form prose harder to read?
- Has the decision been promoted to the right durable place: product docs,
  design docs, service read model, shared component, tests, plan, or not-now
  item?
- Does the surface pass the Surface Quality Bar: intent brief, density budget,
  anti-CRM rules, label discipline, and screenshot QA when rendered composition
  matters?
