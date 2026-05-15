# Static Scene Context Mock Notes

Status: design artifact
Date: 2026-05-14
Artifact: `design/static-scene-context-mock.html`

## Purpose

This prototype explores what Elbysodic can learn from Slack-style layered
navigation without adopting Slack's workplace-chat posture.

The accepted pattern is not "channels and chat threads." It is a scene reader
that keeps location, writer obligation, and story grounding context close
without forcing the writer through a full page transition.

## Prototype Shape

The mock uses four layers:

- `primary_rail`: persistent community rooms such as World Home, Locations,
  Wanted, Desk, and Studio.
- `location_scene_lane`: a minified, scannable view of the current location's
  active scenes, watched scenes, and nearby story context.
- `scene_reader`: the selected scene with prose-first rhythm, turn state, and
  active-face reply affordances.
- `scene_grounding_inspector`: a collapsible right panel for location summary,
  present faces, linked wanted/current-event objects, and visibility notes.
- `scene_media_band`: an optional Apple TV / Netflix-like image treatment for
  director-approved scene, location, or event media.
- `character_post_art`: stronger face graphics beside posts so the active
  character identity remains vivid inside long-form reading. The mock uses the
  official `2:3` poster ratio for post-side face art and alternates the rail
  side by post, matching the existing live post-profile direction. The current
  mock uses a larger poster-wrap treatment where prose flows around the face
  art like an editorial page.

It also includes a small `writer_activity_drawer` to show how Slack's Activity
shape can become an Elbysodic obligations surface: `Needs reply`, `Waiting`,
`Watching`, `Caught up`, claims, reserves, and wanted updates.

## Accepted Design Moves

- Keep the scene as the emotional center. Rails and inspectors support
  orientation; they do not compete with the transcript.
- Use split context to preserve place memory: a writer can read a scene while
  still seeing what else is happening in the location.
- Treat the second rail as desktop affordance, not a tablet tax. At narrower
  widths, location context should become a drawer or scoped overlay opened by a
  clear `Scenes here` control.
- Treat activity as writer work, not generic notifications.
- Use hovercards for "should I click?" context on faces, locations, wanted
  hooks, claims, reserves, and canon/source references.
- Keep active face visible at commitment points: `Reply as Rogue`, composer
  state, and relevant activity rows.
- Make the context panel collapsible by defaultable preference so long-form
  reading can become quiet when needed.
- Preserve imagery as a first-class part of the scene experience: optional
  scene heroes can carry location or event mood, and post-level character art
  can make each face feel distinct without making the transcript feel like a
  media feed.
- Use official media ratios from `design/image-dimensions.md`: scene media can
  use widescreen/thread-stage ratios, while character post rails should use
  `2:3` poster or `4:5` portrait crops instead of square avatar treatments.

## Rejected Slack/Discord Transfers

- Do not make canonical scene prose into nested reply threads.
- Do not use presence, badges, or unread pressure to create chat-like urgency.
- Do not flatten account, membership, face, and character identity into one
  user profile pattern.
- Do not let popovers become unsourced canon summaries. Canon or continuity
  context needs provenance and review status.
- Do not make the sidebar a complete route directory. Each chrome layer needs a
  distinct job.

## Component Candidates

- `scene_context_shell`: layout wrapper for a scene opened inside a grounding
  context such as location, event, wanted hook, or character.
- `location_scene_lane`: compact list of active, watched, closed, and relevant
  scenes inside one location.
- `scene_grounding_inspector`: collapsible read model for present faces,
  linked story objects, visibility, and source/provenance notes.
- `writer_activity_drawer`: fast obligations layer backed by Writer Desk.
- `pbp_hovercard`: reusable hover/focus card for face, location, wanted,
  claim, reserve, and canon/source snippets.
- `scene_media_band`: optional scene, event, or location image slot with
  restrained metadata and no required carousel behavior.
- `character_post_art`: face-owned post graphic treatment that can use uploaded
  character media, generated-safe placeholders, or theme-derived color when no
  image exists. Alternating left/right rails can create page-turn rhythm, but
  the prose measure must stay calm and readable. A larger poster-wrap variant
  is worth testing for dramatic scenes, but it needs browser QA because long
  words, short posts, and mobile widths can make wrapping feel cramped.

## Post Customization Fit

Elbysodic already has post style concepts in the live read model:

- profile rail variants: `bio`, `poster`, `dock`, `crest`
- accent styles: `soft`, `line`, `glow`, `block`
- border styles: `none`, `hairline`, `bracket`, `double`
- title styles: `standard`, `serif`, `condensed`, `mono`
- density: `calm`, `compact`, `dramatic`

The scene-context prototype should not erase that system. The better direction
is to let character customization shape the face rail, accent wash, post title,
and density while the scene reader keeps a continuous transcript rhythm. Hard
horizontal rules between every post are off by default in this mock because
they fight the larger poster-wrap treatment; character-selected border styles
can still reintroduce visible frames where the realm allows them.

## Polish Touches Worth Carrying Forward

- Keep forum heritage through small post permalinks like `#1`, `#2`, and edit
  metadata, but make them quiet enough that prose and face art lead.
- Use editorial details such as drop caps and restrained beat notes only when
  they clarify reading rhythm. They should be theme/post-style aware, not
  hardcoded everywhere.
- End scenes with continuation affordances from the Writer Desk model: `Next
  unread`, `Mark caught up`, `Scenes here`, or the next relevant obligation.
- Treat pull notes such as `Current beat` as optional scene-state summaries,
  not generated canon. They need clear provenance if they become dynamic.

## Product Questions

- Should the right inspector remember per-user collapse state, per-device
  state, or route-local state only?
- Which pages can open a scene in-context: location, event, wanted hook,
  character hub, Writer Desk, and search results are all candidates.
- Which context belongs in the page read model versus a lazy progressive
  enhancement fetch?
- How much of the desktop location lane should appear in the mobile/tablet
  drawer before the reader needs a full location route?
- How much scene state should be public-safe versus member-only or
  staff-only?
- Should scene media be attached to the scene, inherited from the location,
  inherited from the current event, or selected as a director-approved override?
- Can a future "page turn" or per-post focus mode change the visual treatment
  by active speaker without making canonical scene reading feel like a short
  video feed?

## Implementation Notes

Before this becomes live behavior, consult the Surface Contract Steward because
this changes a rendered scene surface and creates a page-level context read
model. The likely service boundary is a named scene reader contract that
combines:

- selected scene and posts
- current viewer membership and active face
- location lane rows
- writer obligation state
- linked wanted/plotter/current-event context
- privacy-filtered visibility notes

Rendered tests should prove that public, member, owner, involved-face, and
staff audiences receive the correct lane rows, counts, context labels, and
hidden/private object behavior.
