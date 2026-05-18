# Composition Bible

Status: living design doctrine
Owner: Product design, web, docs, and surface-contract stewardship
Last updated: 2026-05-18

This guide answers: what should an Elbysodic screen feel like, and how should
it be arranged?

Use it before adding or reshaping heroes, rails, cards, rows, dashboards,
drawers, page headers, media bands, command panels, or dense production rooms.
It does not replace `docs/product/experience-direction.md`,
`docs/product/surface-quality-bar.md`, `design/technicolor-futurism.md`,
`docs/product/information-hierarchy.md`, or
`docs/product/control-topology.md`; it makes their composition rules easier to
apply.

## Thesis

Elbysodic composition is a cinematic PBP control room, built for writers first.

The screen should make a writer or director know:

- where they are in the realm
- which face, scene, hook, location, or production object matters now
- what context is nearby
- what they can safely do next
- what is public, private, staff-only, waiting, watched, caught up, or needs a
  reply

The product may feel atmospheric, editorial, and media-rich, but it is never
passive entertainment UI. The page exists to help people write, choose, review,
continue, and preserve play.

## Reference Jobs

Borrow jobs, not surface costumes.

| Reference | Keep | Reject |
| --- | --- | --- |
| Jcink/forum PBP | cultural ritual, board identity, skins, guidebooks, claims, reserves, wanted, applications, scenes, archives | old-forum nostalgia, raw skin chaos, manual-thread labor as product strategy |
| Slack/Discord | layered context, drawers, activity lenses, quick object previews, reduced page hopping | chat urgency, presence pressure, nested story replies, Discord as archive |
| Netflix/Apple TV | editorial discovery, large media, curated shelves, continuation lanes, quick decision metadata | passive watching, autoplay, streaming choice paralysis, dark clone aesthetics |
| RPHub/modern RP platforms | current polish, image-rich RP-native surfaces, mobile consciousness | copying another platform's visual language |

## The Surface Ladder

Choose the lightest structure that gives the user confidence.

1. **Open layout**
   Use for page identity, prose, section rhythm, filters, and long lists. This
   is the default for reading and orientation.

2. **Compact rows**
   Use for queues, notifications, claims, reserves, applications, plotting
   rooms, recent activity, and thread lists. Rows are good when comparison and
   scanning matter more than atmosphere.

3. **Story-object cards**
   Use for faces, places, wanted hooks, guidebook materials, events, and realm
   cards where media, identity, or comparison matters. Cards should represent a
   story object, not arbitrary information.

4. **Elevated command panels**
   Use for one current command, form, warning, preview, setup step, or summary
   that needs containment. Most pages should not have several competing command
   panels.

If every section becomes a card, nothing is important. If every datum becomes a
badge, nothing is readable. If every action becomes a CTA, the product becomes
a dashboard.

## Page Rhythm

Most pages should follow this journey:

1. **Orient**
   Show the current realm, room, object, state, audience, and active face when
   relevant.

2. **Read or compare**
   Put prose, scene setup, roster identity, wanted fit, or queue rows in the
   calmest part of the page.

3. **Act**
   Place commitment controls near intent: `Reply as <face>`, `Join as <face>`,
   `Raise interest`, `Reserve`, `Submit`, `Review`, `Publish`, `Save`.

4. **Continue**
   After the user finishes an object, offer the next meaningful movement:
   `Next unread`, `Previous unreplied`, `Scenes here`, Desk obligation, related
   wanted hook, plotting room, or Studio queue.

Do not lead with admin chrome when the user came to read a scene. Do not hide
commitment controls when the user has reached the point of action.

## Layered Chrome

Navigation and context use layers with separate jobs.

- **Outer rail:** persistent, icon-first movement across stable rooms such as
  World Home, Locations, Wanted, Desk, and Studio.
- **Inner shell:** explanatory text or icon-plus-text rows for the current room
  or object family.
- **Page chrome:** task-local controls for the displayed content: compose,
  reply, filter, sort, watch, save, review, publish.
- **Drawers and inspectors:** optional context that keeps the primary object in
  view, such as scenes in this location, grounding notes, activity, or object
  previews.

Duplicate links are acceptable only when they serve a different journey moment.
A page action bar should not become a backup route directory.

## Surface Types

### Public Home

Use cinematic editorial composition: featured realm media, high-confidence
copy, curated shelves, public wanted pressure, and small signed-in continuation
lanes. The first screen should prove this is a modern roleplay product, not a
forum index.

Protect: public privacy, clear access posture, next section visible, no passive
streaming behavior.

### Explore

Use search and shelf composition. Help writers compare story fit through mood,
genre, wanted hooks, public activity, access posture, and playable openings.

Protect: no membership, active-face, staff, application, private room, or queue
leakage in public cards.

### Community Home And Locations

Use atmosphere plus structure: world identity, location media, playable places,
active scenes, current event context, and direct scene movement.

Protect: board hierarchy, private-board visibility, and readable local
navigation.

### Thread Reader

The scene is the emotional center. Use prose-first rhythm with face-forward
post rails, active-face commitment, optional scene media, and continuation
controls. Location lanes and grounding inspectors support reading; they do not
compete with it.

Protect: prose measure, no glass behind body copy, no chat pressure, active
face clarity, public/member/staff context filtering.

### Writer Desk

Use obligations, lanes, and rows. This is not a generic inbox. It should answer
what needs the writer now: needs reply, waiting, watching, caught up,
applications, plotting, wanted handoffs, and notifications.

Protect: low-shame commitment language, no noisy shortcut panels, clear next
actions.

### Wanted And Backstage

Use story-object cards and handoff state. Wanted should feel like casting and
plot opportunity, not a static ad board. Backstage should feel like the missing
middle between public hook and private scene.

Protect: participant privacy, hook status, prospective face context, reserve
and interest workflow clarity.

### Studio

Use compact production composition: local rails, room headers, rows, command
areas, and clear state. Studio should feel like director workflow support, not
an enterprise dashboard.

Protect: labels, validation, staff-only access, launch/operation sequencing,
and one clear command area per room.

### Appearance Studio

Use preview-first composition. Directors should see what a choice does to
prose, media, postbits, state colors, and ritual surfaces before publishing.

Protect: contrast, alt text, raw CSS/script boundaries, and health warnings.

## Media Rules

- Use strong media on ritual surfaces: public home, realm gateway, locations,
  wanted hooks, characters, guidebook covers, events, and selected scene
  stages.
- Use thumbnails or quiet media on operational surfaces where scanning matters.
- Keep prose backgrounds stable and opaque.
- Put text over media only when contrast, crop, and fallback states are proven.
- Use official ratios from `design/image-dimensions.md`.
- Media should reveal the realm, place, face, hook, event, or scene state. Do
  not use vague atmosphere when the user needs inspection.

## Visual Weight

Give weight by user need:

- highest: current story object, active face, scene/wanted commitment, public
  privacy, staff/private warnings
- medium: related context, filters, counts, recent activity, local navigation
- low: metadata, secondary links, decorative atmosphere, route reassurance

Color is for identity, state, focus, and atmosphere. It is not a substitute for
hierarchy.

## Mobile Composition

Mobile is not collapsed desktop.

- Keep the primary reader or current workflow first.
- Move auxiliary context into drawers or scoped overlays.
- Keep commitment controls close to intent.
- Do not make the user scroll past route chrome to reach the scene or form.
- Prefer rows and shelves over dense card grids.
- Test long names, long titles, many facets, no media, and reduced motion.

## Bad Patterns

- Generic SaaS dashboard: equal-weight cards, metrics everywhere, "projects"
  and "tasks" language.
- Card soup: every section framed and elevated until the page has no rhythm.
- Streaming clone: cinematic rows that imply passive browsing instead of
  writing action.
- Chat takeover: presence, unread pressure, nested replies, and rapid-response
  cues overwhelming PBP pace.
- Nostalgic skin archive: old forum chrome as default product identity.
- Hidden safety: privacy, staff-only state, active face, or public authorship
  implied only by color or buried in metadata.

## Acceptance Questions

- What is the Surface Intent Brief: audience, first-five-second read, primary
  object, primary decision, dominant reference job, negative reference, and
  progressive disclosure plan?
- What is the primary object: realm, place, scene, face, wanted hook, desk
  obligation, application, claim, reserve, material, event, or Studio room?
- Which ladder level does this surface need: open layout, row, story-object
  card, or command panel?
- Does the density budget hold, or did structured data turn into visible
  clutter?
- Does the page journey clearly move from orient to read/compare to act to
  continue?
- Which context belongs in chrome, which belongs in the page, and which belongs
  in a drawer?
- Does the surface avoid CRM/dashboard failure modes: equal-weight cards,
  metrics everywhere, repeated labels, route-directory panels, and generic
  admin language?
- Does media clarify identity or atmosphere without hiding controls?
- Can a writer read or write for a long session here?
- Are active face, authorship, privacy, and staff boundaries visible before the
  user acts?
- Does this still feel like PBP, not generic forum, chat, streaming, or SaaS UI?
