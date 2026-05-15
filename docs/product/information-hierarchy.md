# Information Hierarchy And UI Vocabulary

Elbysodic uses ChirpUI for primitives and defines a small product vocabulary on
top of it. The goal is not to create a second design system. The goal is to
make repeated PBP concepts read the same way everywhere: scenes, faces, world
lenses, activity, and writer obligations should have a stable visual grammar.

This document explains what repeated concepts mean visually. Use
`docs/product/control-topology.md` alongside it when deciding how visible,
compact, editable, or collapsed a control should be.
Use `docs/product/navigation-menus.md` when deciding route placement, topbar
realms, sidebar grouping, breadcrumbs, tabs, dropdowns, and active states.
Use `docs/product/paragraph-rhythm.md` before adding or changing paragraph
output; Elbysodic is a text-first app, so prose, summaries, helper copy, and
metadata need distinct paragraph roles.
Use `docs/product/notices-admonitions.md` before adding current-event bridges,
warnings, staff notices, toasts, or other page-local alerts.
Use `docs/product/appearance-studio.md` before adding theme controls,
community media slots, or presentation variants for ritual surfaces.
Use `docs/product/experience-direction.md` when deciding how much of the
current Jcink/PBP, layered-context, editorial-discovery, and technicolor
futurism synthesis should shape a surface.
Use `design/composition-bible.md` when deciding whether the surface should be
open layout, compact rows, story-object cards, or an elevated command panel.

## Audit Baseline

The current app has several information-heavy surfaces:

- Home/world gateway: atmosphere first, then locations, queues, and activity.
- Network launch state: when no realm exists, platform identity and next
  access action come before community navigation.
- Studio launch room: when a realm exists but is still backstage, director
  setup progress comes before ordinary production queues.
- Board page: place identity, sublocations, filters, and direct scenes.
- Thread page: scene state, cast, metadata, posts, and writing actions.
- Character page: face identity, facets, plotter/wanted hooks, queue, posts.
- Wanted and casting: structured hooks, interest, reserves, and related faces.
- Wanted backstage: raised hands, private interest notes, plotting-room
  handoffs, ready-for-scene state, and scene links for involved writers,
  hook owners, and casting staff.
- Writer Desk, My Threads, Notifications: meta-work that supports writing.

These screens repeat the same concepts. When they are styled ad hoc, everything
competes for attention. Elbysodic should instead decide which concepts are
identity, which are action, which are metadata, and which are signals.

## Simplification Doctrine

Simplification is not minimalism for its own sake. It is the discipline of
letting the primary PBP object stay foregrounded while supporting context,
counts, controls, and director tools recede until they are useful.

### Hub Page Contract

A hub page is not an index of every adjacent route. It earns its place only
when it answers one cross-cutting question better than the scoped pages can.

Use this contract before adding or expanding a hub:

- **Writer Desk** answers: what needs the writer now? It can surface reply,
  reading, waiting, plotting, application, and notification work only when
  there is active work behind the lane. It should not mirror the sidebar,
  roster, applications, casting, discovery, or inbox as persistent shortcuts.
- **Studio** answers: what needs a director now? It can surface launch
  blockers, review queues, production health, navigation warnings, and current
  publishing work. It should not also be the full board taxonomy editor,
  navigation composer, appearance editor, casting desk, and continuity editor
  unless those are the current director job.
- **Community home** answers: where am I in the world? It should orient around
  realm identity, playable locations, current activity, and reply pressure. It
  should not become a second Writer Desk or Studio dashboard.
- **Character hub** answers: what is true and playable for this face? It can
  show profile identity, active hooks, recent scenes, tracker context, and
  character-specific actions. It should not repeat roster-wide work that the
  Writer Desk already owns.

Scoped pages own durable workflows:

- `/my/threads` owns queue filtering, roster-wide thread state, and deeper
  reply/waiting scans.
- `/notifications` owns notification history and bulk inbox actions.
- `/applications` owns draft, submitted, and revision-requested intake.
  Accepted applications become character pages.
- `/plotting` owns planning rooms and interest handoffs.
- `/studio/operations` owns daily director production work.
- `/studio/launch` owns launch readiness and setup sequencing.
- Future Studio routes should own appearance, navigation, board taxonomy,
  materials, and casting/review work before those editors are removed from the
  Studio home.

A hub section should pass at least one test:

- It changes with active work, urgency, or production health.
- It prevents a wrong next action.
- It explains the current state of the realm, writer, director, or face.
- It is the fastest safe path into a focused scoped page.

If a section exists only to prove that another route exists, remove it from the
hub and let the sidebar or object-local navigation do that work.

This depends on navigation staying available. A fully invisible sidebar makes
hub pages compensate by repeating routing options. Prefer a compact icon rail
as the ordinary space-saving state so hubs can stay focused on current work
instead of becoming backup navigation.

Use this surface ladder before introducing a new frame, card, panel, or CTA:

1. Open layout: page identity, section rhythm, prose, filters, and long lists.
2. Compact rows: queues, notifications, claims, reserves, applications,
   plotting rooms, recent activity, and thread lists.
3. Story-object cards: faces, places, wanted hooks, guidebook materials, and
   other repeated objects where media, identity, or comparison matters.
4. Elevated command panels: one current page command, one form, one warning, or
   one preview surface that needs to feel contained.

Not every repeated datum deserves a card, chip, badge, or button. Metadata can
be a line. Counts can be quiet metrics. Related objects can be rows. Secondary
actions can be inline links or overflow menus. Negative space is part of the
hierarchy when it separates jobs and gives story material room to breathe.

### Divider Rhythm

Dividers mark workflow mode changes; whitespace marks narrative hierarchy. Use
borders for action zones, records, forms, dense lists, moderation tools, and
scene/thread modules. Use spacing, alignment, shelf headings, media, or quiet
metadata for ordinary story context.

Avoid stacking a section-header rule, container border, filter rule, and
empty-state rule inside the same module. Atmospheric pages such as world,
location, wanted, character, and member surfaces should prefer shelf rhythm and
cards. Operational pages such as Studio, casting, claims, applications, queues,
and plotting rooms may use more structure, but should still keep one primary
boundary per workflow region.

Before adding a new component shape, ask:

- Is this concept identity, action, metadata, status, or navigation?
- Would a row, text line, metric, or local rail do the job with less chrome?
- Is this action already available in the topbar, sidebar, local rail, command
  area, object title, or row link?
- Does this page already have an elevated command surface? If so, a second
  elevated panel needs a distinct job.
- Is the visual weight appropriate for the user's current journey: orient,
  read or compare, act, continue?

When two links lead to the same place from the same visual area, keep the one
that matches user intent. A character poster and character name can both open a
profile because they are identity affordances; a third `Open profile` button
usually repeats the same action without adding confidence. A Desk command area
can link to Queue or Inbox; a separate shortcut panel should exist only when it
adds a different browsing model.

## Creator Launch Hierarchy

Creator onboarding is a director launch room, not a generic signup wizard. The
surface should preserve the difference between platform access, realm identity,
and writing readiness:

1. Platform access: sign in, request access, or accept a director invitation.
2. Realm identity: name, slug, director display name, premise, and launch
   status.
3. Play surface: scene hubs, public/private boundaries, and director materials.
4. Roster intake: application questions, claims, reserves, first-face state,
   and staff review visibility.
5. Atmosphere: approved appearance tokens and media metadata.
6. Opening: staff/writer invites, public preview readiness, and launch
   checklist.

The no-realm state should stay sparse and direct. It should not show a fake
community shell or empty forum map. The empty configured realm state should
show the community shell only to users who can resolve a community-local
membership, and director setup controls should stay in Studio.

Progress indicators in the launch room should name director work in PBP terms:
"Scene hubs", "Director materials", "Intake and claims", "Wanted hooks",
"Appearance", "Invites", and "Launch checklist". Avoid generic steps such as
"Configure content" or "Set up workspace".

## Vocabulary

### Component Promotion

Promote a page-local shape into `src/elbysodic/web/pages/_components/` when it
appears in more than one product area or clearly represents a PBP-native
concept. The goal is shared meaning, not generic abstraction. Prefer component
names that describe the writer/director job they support.

Current promoted component shapes:

- `local_rail`: in-page navigation for dense rooms such as Writer Desk, Studio,
  character hubs, and application/casting surfaces. It moves within the current
  route; it is not a sidebar substitute and should not carry global active
  state.
- `preview_row`: compact linked object summary with title, badge, metadata, and
  snippet. Use for recent notifications, queue items, plotting rooms, and other
  scannable work previews.
- `metric_item`: compact stable quantity inside a command surface, queue focus,
  or production overview. It is not a button; pair it with nearby actions when
  the number should lead somewhere.
- `command_action`: short action tile for the first few things a writer or
  director can do from a command surface. Use when the action benefits from one
  sentence of context and an optional count; use a plain button/link when the
  action is already obvious.
- `command_panel`: compact elevated summary for a page or workroom. Use when a
  page needs one explanatory title plus a small set of metrics or immediate
  actions, such as applications, plotting rooms, or queue focus.
- `lane_preview`: a bounded work lane with count, explanation, deeper-room
  action, and a small list of `preview_row` items. Use when the page is a
  command surface and the deeper workflow lives elsewhere. Prefer an open
  section with rows when several lanes are already visible and the card frame
  would make everything feel equally important.
- `production_room_card`: a Studio-style room tile for director/admin surfaces
  where the card represents an area of board production rather than a single
  story object. Use sparingly, mainly for a launch or room chooser. On a page
  where directors already have local rail navigation, prefer a compact room
  index or open sections so Studio does not become a grid of equal-weight
  cards before the actual work.
- `room_header`: a kicker, title, and short explanation for one room within a
  dense production surface. Use when a route is divided into several stable
  workrooms and those rooms need consistent anchor targets.

Do not promote a shape just because it has similar CSS. Promote it when reusing
the component makes the page's meaning clearer: writer attention lanes should
feel like writer attention lanes everywhere, and director production rooms
should feel like director production rooms everywhere.

### PlaceTile

Use for world locations and sublocations. It carries atmosphere and identity:
image or generated visual field, tagline, title, description, compact counters,
facets, child-place links, and latest activity.

The place name is primary. Counts and facets are secondary. Latest activity is
tertiary.

On board pages, parent locations should read as playable hubs. Use the hero for
identity and emotional framing, then use clear section rhythm for sublocations,
nearby places, and scenes. Avoid making counters, facets, latest activity, and
child links all compete at the same weight.

The short line on the image is the place tagline, or logline. It is the
emotional hook: a poster-line that tells the writer why the location matters.
The description below the image is explanatory body copy: it can give practical
context, setting detail, and plot affordances. The tagline should sit with the
title; the description should sit outside the image with the rest of the card
metadata.

Do not render taglines as pills. They are not tags, filters, states, or
actions. Prefer poster-copy treatment: plain text, a small accent rule, or
another typographic cue that feels attached to the title rather than like a
clickable chip.

Active-face relevance, such as `Relevant to the active face`, is a smart
contextual signal. It belongs on the image as a compact ASCII/icon overlay
because it is about the relationship between the current face and the place,
not a count, facet, or generic status. Keep the visible mark small and expose
the full meaning through hover/focus disclosure and `aria-label`. Use the
shared `meta_hint()` helper for this disclosure so the visible mark stays quiet
while the explanation remains available.

### Counter

Use for small stable quantities that help scan a page but should not dominate
it: threads, posts, replies, places, active scenes, reserves, and queue counts.

Counters use an ASCII or icon mark, number, and short label. They are not
buttons. They should stay compact and visually stable.

Current marks:

- `T`: threads
- `P`: posts
- `R`: replies
- `>`: child places or sublocations
- `!`: needs attention, future use
- `@`: mentions or cast, future use

### MetaLine

Use for contextual facts that explain an object without becoming the object:
writer, face, updated time, location, timeline, related material, or board.

Metadata should be small, muted, and usually inline. It should not look like a
chip or action unless the link itself is the useful target.

### LatestLine

Use for "latest", "your last post", and related jump targets. This is a
specialized metadata row: label, linked target, optional author, optional
writer, optional time.

LatestLine should answer "where do I go next?" without becoming a full activity
card.

The visible line should stay compact. Prefer showing the target and the
story-facing character, then move writer ownership and exact updated time into a
hover/focus disclosure. The disclosure is additive context, not required for the
basic action. Use ChirpUI's `tooltip` primitive for compact, non-interactive
metadata disclosure before adding a bespoke hovercard.

Example:

```text
Latest: The med-bay lights stay on by Moira MacTaggert
```

Hovering or focusing the thread title can reveal:

```text
Latest details
The med-bay lights stay on
by Moira MacTaggert
writer moira
Apr 25, 2026 6:35 PM UTC
```

### SceneStateBadge

Use for operational state: open, active, paused, complete, private, archived,
watching, pinned, locked, caught up.

These are not facets. They describe workflow or visibility, not worldbuilding.

### FacetChip

Use for director-defined world lenses: faction, species, house, nation, event
pressure, access lane, relationship status, application category, or other
board-specific dimensions.

Facets describe the story grammar. They should be small and consistent. They
may be clickable in discovery/filter contexts later, but they should not look
like primary actions on atmospheric pages.

Avoid letting every repeated datum become a pill. Pills are strongest for
filters, removable selections, and explicit tags. Other concepts should get
their own shapes: counters can be compact icon-number pairs, loglines can be
typographic, latest activity can be a text line, and active-face relevance can
be an ASCII/icon overlay.

### ActivitySignal

Use for writer obligations and freshness: needs reply, waiting, new replies,
unread, watched, mentioned.

Activity signals should be concise and action-adjacent. The strongest signals
belong in Writer Desk, My Threads, Notifications, and relevant board/thread
lists. On a thread detail page, `Previous unreplied` and `Next unread` follow
the visible community attention queue and sit beneath the last post, while
previous/next scene links sit in the transcript header for same-board skimming.
Thread watch controls can be compact icon toggles when their accessible label
and state badge remain clear. They should not overpower the world gateway.

Thread reader controls follow this hierarchy:

- Breadcrumbs and scene identity orient the reader.
- Transcript header controls support local skim decisions.
- Stage actions support immediate reading or writing: reply/join first, then a
  compact watch toggle paired with `Read latest`.
- End-of-thread controls support queue continuation across visible community
  obligations.

### CastFaces

Use for character participants and related faces. Cast is story-facing, so it
should use avatars or initials and link to character hubs.

Writer names belong in metadata. Character faces belong in cast.

Cast should compose ChirpUI's `avatar` primitive so status, sizing, fallback
initials, and future avatar-stack behavior stay consistent across thread cards,
wanted hooks, casting, and character hubs.

### Wanted Backstage

Use for the coordination lane attached to wanted hooks. Backstage is not a
global feed and not a generic DM surface. It is the object-bound handoff from a
writer raising a hand to a hook owner or casting-capable director opening a
plotting room, marking it ready for scene, and linking the resulting scene.

The public wanted hook can show safe movement signals such as `Raised hand`,
`In plotting`, `Ready for scene`, `Scene started`, or `Reserved`. Private
interest notes, prospective pitches, room links, and scene-handoff controls
belong only to the interested writer, hook creator, room participants, or
casting staff.

The visual priority is:

1. Hook identity and world context.
2. Casting packet details: why the role matters, first-scene invitations,
   relationship lanes, and negotiables.
3. Public movement state.
4. Private backstage action for eligible viewers.
5. Reserve or lifecycle controls for hook owners and casting staff.

### PostProfileRail

Use for the character identity block attached to each post. It owns a stable
physical footprint so the prose column does not shift as controls or profile
details change.

The rail may support presentation variants:

- `bio`: visible name, writer, tagline, and profile note.
- `poster`: portrait-only at rest; reveal name, writer, tagline, and profile
  details on hover/focus/tap.
- `dock`: image first, with a persistent identity strip and richer details
  available inside the strip.
- `crest`: fallback initial art in the same geometry when no portrait
  exists.

Variants may change density inside the frame, but they must preserve immediate
author recognition, keyboard/touch access to hidden details, and no layout
shift between posts.

### Sidebar Groups

The app sidebar is the canonical community and local navigation map. The topbar
owns platform/global utilities; the sidebar owns community rooms and current
object context. Do not duplicate a primary route family in both places.

Use the stable community map to orient writers:

- `World`, `Guidebook`, and `Wanted` are world-facing community rooms.
- `Writer Desk`, `Roster`, `Queue`, and `Plotting` are writer-work routes.
- `Studio` is director work and appears only when the viewer can access it.

Hydrate below or within the active room with local context: current location
branch, current material, related wants, desk lane, or Studio production
surface. Empty contextual collections disappear.

The sidebar should not add a section label when the first row is already the
named route parent.

Use an unlabeled group when the row itself is the category: `Locations`,
`Community`, `Overview`, `Start Here`, `Guides`, `Events`, `Wanted board`, or
`Production`. Use labels only as optional dividers between unlike/contextual
lists, such as `Current Event`, `Open Wants`, `Related Wants`, or future
director-configured sidebar collections.

Route parents stay clickable, active, counted rows. Labels are not routes and
should never carry the main active state for a category.

### Sidebar Toggle

Use hide/show navigation for focus and space management only. It must not
switch IC/OOC, in-world/out-of-world, director/writer, or active-face modes.
The current face is an identity lens that can influence defaults and contextual
signals; it is not a separate navigation tree.

### LocationTree

Use for the world map sidebar and nested board orientation. LocationTree is not
a generic tool menu; it is the reader's map of the setting. Parent locations
must remain direct links. Sublocations should reveal only for the current
branch so the sidebar orients the writer without spoiling the atmospheric board
surface.

The server owns `open` and `active` branch state. In boosted app-shell sidebars,
render LocationTree links with app-owned anchors when generic route-aware
component links would add the wrong swap target. ChirpUI `nav_tree` remains a
good fit for non-shell trees or shells whose route-link attributes match the
intended target.

Top-level locations should stay legible as places. Sublocations should be
visible enough to communicate depth, but the tree should not become the primary
atmospheric surface; PlaceTile and board pages still carry the world feeling.

On small screens, keep the same contextual navigation in a ChirpUI drawer
rather than turning the sidebar into a horizontal strip. The drawer should
reuse the same canonical community map and current-room hydration used on
desktop. This preserves orientation without making the world compete with
mobile navigation chrome.

### RouteTabs

Use ChirpUI `route_tabs` only for local subsection navigation where two or more
closely related routes are unmistakably peer views of the same object or
workspace: future character profile sections, future guidebook sections, or
director tools.

Route tabs are page chrome. They should not replace the topbar's global
navigation, bridge broad feature areas, or replace the sidebar's world
orientation.

### InlineFilterRail

Use the compact underline rail for local filters and long-page jumps: thread
list filters, roster slices, material-page sections, and future event indexes.
It is intentionally quieter than tabs. It should feel like a reading aid or
collection control, not a new page mode.

Use this rail when the object stays the same and the writer is narrowing or
jumping within nearby content. For server-filtered lists, swap only the local
region with HTMX and preserve scroll position. For long pages, use same-page
anchor links with clear section IDs.

Use route tabs instead when each item is a stable subsection route with its own
mental model, such as profile sections, director settings, or guidebook admin
views. Tabs say "different view of this object." Filter rails say "same object,
smaller slice or nearby section."

### Fragment And Island Regions

Use native Chirp `{% fragment name %}` blocks for swap-only or response-only
template regions: validation results, success panels, SSE payloads, and OOB
targets that should never render inline during a full page request.

Use ChirpUI `safe_region` or `fragment_island_with_result` for HTMX mutation
regions inside boosted shells, especially when the form and result target need
to stay in the same DOM subtree.

Use Alpine islands for local-only state that should not touch the server:
draft previews, presentational toggles, inline disclosure, small editors, and
try-on previews. Use SSE only for server-originated changes after page load,
such as notifications, live thread activity, or cross-writer presence.

### ThreadByline

Use when explaining authorship: started by character, writer username, updated
time, and optional board/location. ThreadByline should distinguish public face
from writer ownership without making every card feel administrative.

### SceneCard

Use for thread list rows/cards on board, character, member, and writer-desk
surfaces. A thread is a scene, so the card should scan like an episode in a
place: location/timeline eyebrow, scene title, started-by face, short premise,
state/activity signals, cast, facets, and latest jump target.

Use the `Scene Slate` treatment for full cards: a stable place-media poster at
the left, title/premise as the main reading lane, and cast/activity in a quieter
footer rail. This borrows from story/event browsing patterns: the card is
primarily an entry point into a scene, not a miniature database row.

The title and premise are primary. Workflow signals such as needs reply, new
replies, pinned, locked, and reply counts are secondary. Cast, facets, and
latest activity are tertiary unless the current surface is specifically a
queue.

Do not make every fact a pill. Use badges for workflow state, counters for
small quantities, cast faces for participants, facets for director-defined
world lenses, and latest lines for jumps.

Avoid repeating a state in multiple places on the same card. If a scene is
already labeled `open to join`, the poster does not also need to say `open`.
Hide zero counters, and prefer ChirpUI avatar stacks for cast when space is
tight so the card keeps its story shape.

### SceneHeader

Use at the top of thread pages. A thread is a scene in a place, so the header
should carry place path, title, state, cast, location/timeline, and the primary
writer action together. The header should answer "where am I, who is here, and
what can I do next?" before the reader reaches the post list.

Keep prose posts visually distinct from scene metadata. Character identity
belongs beside each post; writer ownership and edit/revision controls should
stay quieter than the writing itself.

### ComposerShell

Use for new-thread, reply, and edit writing surfaces. The composer should feel
like a calm writing room, not a generic form. Separate scene setup from the
writing area when starting a thread. On replies, keep the setup minimal and let
the active face carry the context.

Composer controls should stay close to the writing surface: view toggle,
formatting toolbar, draft status, and submit action. Character selectors should
remain available, but active-face defaults should reduce the need to think
about them.

### PostFrame

Use for individual posts inside a thread. A post is the place where the
character becomes most present, so it should carry both prose and identity. The
prose remains the primary object. The character poster rail provides emotional
presence, avatar/art space, writer attribution, and a compact profile cue.

Alternate the poster rail left and right on desktop so the thread feels like
characters are facing one another. Do not alternate or zig-zag the prose itself;
long-form reading needs a stable column. On small screens, collapse posts into
a single column with the poster above the prose.

The character name, writer, summary, and post permalink should remain visible.
Hover/focus profile detail can add texture, but it must not be required to
understand who wrote the post or what action is available.

### SceneSurface

Use for the top of a thread page. A scene surface should answer, in order:
where this is happening, what the scene is called, what state it is in, who is
in it, what the last beat was, and what the viewer can do next.

Scene metadata should be split by job:

- Status badges: state such as open, active, paused, private, caught up, or
  watched.
- Scene pulse: compact counts and modes such as replies, cast, and freeform or
  posting order.
- Last beat: the latest character and timestamp as a re-entry cue.
- Facets: world lenses, not action controls.
- Primary action: usually `Reply as <active face>` or `Join as <active face>`.

Director and staff controls should be available without becoming the emotional
surface of the thread. Prefer collapsed management disclosures unless the user
is already inside a dedicated admin or desk workflow.

### MaterialPage

Use for director-authored canon: premise, rules, factions, application guidance,
events, and other production material. A material page should feel like a studio
document, not a forum thread. The hierarchy is title, summary, facets, canon
body, then story affordances.

Material pages may surface:

- Wanted hooks tied to the same material or world lens.
- Active scenes carrying the material into play.
- Locations where the material matters.
- Related materials that share facets.

Use a compact `StudioFacts` treatment for structured production metadata such
as status, featured state, related scenes, wanted hooks, and relevant locations.
This should compose ChirpUI's `description_list` primitive through the shared
Elbysodic helper rather than custom key-value markup.

Director editing belongs in a collapsed `Material studio` disclosure on the
page for now. This proves the authoring loop without turning the guidebook into
a full admin app too early.

### EventPage

An event is a material with higher urgency. Use it when a board-wide plot
pressure should generate scenes, wanted roles, faction decisions, and location
stakes. Event pages should emphasize the current hook, open roles, related
locations, and active scenes before general related reading.

Use `ContinuityTimeline` when an event needs to show how canon pressure is
moving into play. It should compose ChirpUI's `timeline` primitive through the
shared Elbysodic helper and should read as story continuity, not project
management activity. The first pass may derive beats from material metadata,
related locations, active scenes, and wanted hooks before dedicated event-beat
editing exists.

Use event action cards near the top of event pages to answer the writer's most
important question: "What can I do with this right now?" Derive the first pass
from open scenes, wanted hooks, affected locations, and discovery facets. These
cards are campaign prompts, not generic dashboard stats.

When a board or thread shares facets with a current event, surface a compact
event bridge back to the event page. This gives locations and scenes a sense of
seasonal pressure without requiring directors to manually wire every thread to
an event before the event model exists.

### CharacterPoster

Use for the large visual identity area inside a post. Prefer real character
poster art when supplied. Avatars remain the small navigational face used in
chips, nav, and compact mentions; posters are the cinematic identity surface for
posts and profile heroes. When no poster exists, use a stable,
character-specific poster treatment with initials so the space still feels
intentional rather than empty.

Character identity fields are:

- `avatar_url`: compact face for chips and menus.
- `poster_url` and `poster_alt`: large post/profile visual.
- `tagline`: short emotional handle, not a badge or facet.
- `accent_color`: character-specific highlight for poster frames and compact
  signals.

The poster is atmosphere and identity. It is not a navigation menu, not a badge
collection, and not a replacement for readable prose.

## Expressive Customization Contract

Elbysodic should preserve the expressive pleasure of old-school PBP templates
without letting character customization break the thread.

Customization belongs in bounded surfaces:

- The system owns grid, spacing, prose readability, mobile behavior, required
  identity, and contrast.
- Writers can customize approved character presentation tokens: post profile
  variant, accent treatment, border treatment, identity type, density, poster
  art, tagline, and accent color.
- Communities may eventually decide which token choices are available, but V1
  uses app-approved constants.
- Directors can curate which approved post tokens are available to writers.
  Disabled values should disappear from new-character controls, while existing
  characters that already use a disabled value should still render and remain
  editable until the writer chooses a different value.
- A community may choose one facet group as its identity accent source. When a
  character has no explicit accent override, post atmosphere inherits from that
  character's first matching facet color in the chosen group.
- Roster and profile surfaces should disclose the current accent source with a
  compact swatch and label so automatic direction feels intentional rather than
  mysterious.
- Do not allow arbitrary CSS, raw style blocks, scriptable templates, or layout
  controls that resize the prose column.
- Required identity stays present in markup even when a visual variant hides it
  until hover/focus/tap.

Safe token examples:

- `post_profile_variant`: `bio`, `poster`, `dock`, `crest`.
- `post_accent_style`: `soft`, `line`, `glow`, `block`.
- `post_border_style`: `none`, `hairline`, `bracket`, `double`.
- `post_title_style`: `standard`, `serif`, `condensed`, `mono`.
- `post_density`: `calm`, `compact`, `dramatic`.

These tokens map to CSS classes and design tokens, not user-authored CSS.
Post-level atmosphere should attach to the post surface/container when possible;
the semantic article should remain focused on identity, metadata, and prose.
This keeps decorative borders and washes outside the reading grid and lets
Chirp-UI surface padding protect the text from tight custom frames.

## Size Strategy

- Page title: world, place, thread, or character identity.
- Section title: navigation rhythm and grouping.
- Card title: clickable object name.
- Metadata: small and muted.
- Counters: compact, stable, one line when possible.
- Chips and badges: small, consistent height.
- Buttons: actual actions only.
- Text links: navigation or jump targets, never decorative emphasis.

## Condensing Rules

- The global identity cluster owns the current membership and active face name.
  Do not repeat `playing as <face>` or `Current face: <face>` in page headers,
  passive helper copy, cards, stats, or sidebars. Use state language such as
  `active-face matches`, `active-face reserves`, or `Relevant to the active
  face`.
- Name the face at identity-sensitive commitment points: `Reply as <face>`,
  `Join as <face>`, `Message as <face>`, `I'm interested as <face>`, and
  `Reserve for <face>`. Also name it inside explicit switchers or
  cross-community identity menus where the user is choosing which face travels
  with a realm.
- Decide whether emptiness is useful before rendering an empty structure. Show
  empty states when they reduce anxiety or teach a next step: no scenes need
  reply, no notifications are waiting, an application form is incomplete, or a
  staff review queue is clear. Hide empty optional lanes, shortcut panels,
  duplicate CTAs, and zero-count rows when they only prove that nothing is
  happening.
- Treat accepted applications as resolved intake. They become character pages,
  roster entries, profile hubs, and posting identities; they should not keep
  appearing as application work unless a review/audit surface explicitly needs
  historical acceptance state.
- Place controls by page rhythm: orient first, let the user read or compare,
  show the action at the point of intent, and put continuation controls after
  completion. Previous/next thread controls can stay near the top when they
  help users skim nearby scenes; attention controls such as `Previous
  unreplied` and `Next unread` belong beneath the last post because they answer
  "what needs me after reading?"
- Prefer active-face defaults over repeated controls when the action is safe:
  `Join as Rogue` beats a roster dropdown.
- Use `docs/product/control-topology.md` before collapsing a visible action into
  an icon, overflow menu, disclosure, or inline edit affordance.
- Hide optional sections when empty unless the empty state teaches the next
  useful action.
- Do not duplicate the same title above and inside a visual tile.
- Do not show facets, statuses, and child links with the same shape.
- Keep staff/director controls visually behind the writing experience unless
  the user is actively managing the scene.
- Use the world/sidebar tree for orientation, not as a dumping ground for every
  tool.

## Implementation Contract

Shared Elbysodic vocabulary lives in:

```text
src/elbysodic/web/pages/_components/ui.html
src/elbysodic/web/pages/_components/boards.html
src/elbysodic/web/pages/_components/posts.html
src/elbysodic/web/pages/_components/thread_summary.html
src/elbysodic/web/pages/_components/facets.html
src/elbysodic/web/pages/_components/wanted.html
```

App-specific styling belongs in:

```text
src/elbysodic/web/static/elbysodic-theme.css
src/elbysodic/web/static/elbysodic-theme/
```

ChirpUI remains the primitive layer. Elbysodic components should compose
ChirpUI surfaces, badges, buttons, layout helpers, `tooltip`, `avatar`, and
tokens rather than creating page-local component systems. Use heavier
navigation primitives such as `route_tabs` sparingly, only when their
interaction model fits the product surface.

Use `docs/architecture/theme-css-architecture.md` when deciding whether a
selector should be a Chirp primitive override, an Elbysodic PBP component, a
page composition, or a temporary legacy entry.

For compact disclosures, prefer `_components/ui.html` `meta_hint()` before
adding page-local tooltip markup. It follows the ChirpUI tooltip contract while
keeping the PBP meaning in Elbysodic's vocabulary layer.

For compact studio metadata, prefer `_components/ui.html` `studio_facts()`
before adding page-local description-list markup. It follows the ChirpUI
description-list contract while keeping director-facing material facts visually
secondary to canon and atmosphere.

## Next Audit Targets

- Convert large `chirpui/stat` usage on desk-like pages into counters where the
  values are scan helpers rather than hero metrics.
- Introduce a `MetaLine` helper if metadata patterns keep spreading across
  wanted, casting, members, and character hubs.
- Make thread bylines explicit enough to preserve face/writer distinction while
  staying quieter than scene titles.
- Decide when facets become clickable filters and keep that affordance
  visually different from non-clickable descriptive chips.
