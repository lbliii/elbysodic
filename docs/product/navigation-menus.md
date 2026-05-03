# Navigation Menus

Elbysodic navigation has to do more than move between URLs. It has to preserve
the feeling that a community is a playable world, while still giving writers
fast access to queues, characters, hooks, and production tools.

Use this guide when adding routes, changing the topbar, shaping the sidebar,
choosing between tabs and filters, or deciding whether a set of links deserves
a label, dropdown, disclosure, or admin-configurable collection.

## Navigation Jobs

Every navigation surface should have one clear job.

| Surface | Job | Question It Answers |
| --- | --- | --- |
| Topbar | Community mode switcher plus global utilities | "Which major part of this community am I in?" |
| Sidebar | Current mode/object contents | "What is inside this place?" |
| Breadcrumbs | Object lineage | "How did I get to this object?" |
| Inline nav/filter rail | Local page movement or list narrowing | "What part of this object/list am I viewing?" |
| Action bar/buttons | Doing work | "What can I do now?" |
| Dropdown/menu | Secondary or space-constrained choices | "What else is available without making the page noisy?" |

Do not make two surfaces answer the same question at the same weight. Duplicate
links are sometimes useful, but duplicated hierarchy is usually confusing.

## Topbar

The topbar is the stable community switcher plus the LBSodic/platform shell.
It should stay quiet, but it may own the handful of major community modes so
writers do not have to hunt in the sidebar for the primary shape of the
community.

On shared hosts, `/` is the Elbysodic/LBSodic home for exploring reachable
communities. A community home lives at `/c/{community_slug}`. Inside a
community, the brand/title links to that community home and replaces any
separate `Home` or `Now` topbar item.

Topbar owns:

- Current community identity and future community switching.
- The community brand/title as the community home affordance.
- Primary community modes after home: `World`, `Play`, `Desk`, and `Studio`.
- Future global/community search entry.
- Future explore/browse communities entry from the LBSodic home.
- Notifications indicator.
- Writer account, membership, and active-face identity menu.
- Theme, accessibility, and account utilities.
- Mobile navigation trigger.
- At most one cross-cutting create/action control when it is truly global.

Topbar does not own local contents. Boards, locations, threads, materials,
applications, claims, roster, plotting rooms, wanted hooks, and discovery
filters belong in the sidebar or object-local controls.

Avoid adding topbar items for:

- One-off tools.
- Individual boards, materials, characters, or rooms.
- Filters or local page modes.
- Staff-only tasks that belong inside `Studio`.
- Future features that are not yet part of the daily loop.

If a topbar item starts to need children, keep the parent in the topbar and put
the children in the sidebar. Topbar dropdowns are reserved for global/account
utilities because they hide structure and add hover/tap fragility on mobile.

### Topbar Exceptions

Notifications are not a topbar realm. They are a shell attention affordance:
show a compact always-visible bubble/count near the identity cluster, and route
the full inbox through Writer Desk. The bubble answers "something needs me";
Writer Desk answers "what exactly do I owe?"

The identity cluster lives in the topbar area but is not topbar navigation. It
represents operating state: the writer account/membership and the active face
being worn. It may use a dropdown because the current face is visible, the
roster can grow, and changing it affects defaults across the app.

Account owns access. Membership owns community identity. Face owns story
context. Notifications belong to the writer, but can expose face-scoped queues
inside the identity menu or Writer Desk.

Writer Desk is the operating room that cashes out the shell promise. It should
start with "what needs me," then let the writer narrow by face lane or move to
work lanes: Queue, Inbox, Roster, Plotting, Applications, Discovery, and
Casting/Wanted. Desk should feel like a writing cockpit, not a generic tool
directory.

## Sidebar

The sidebar is the contextual map for the current community mode or local
object. It is not a second topbar, a marketing menu, or a dumping ground for
every tool. Inside a community, the topbar chooses the major mode and the
sidebar shows what is inside that mode.

The sidebar has two jobs:

- Show the current mode's contents using distinct local language.
- Hydrate with context for the current location, material, wanted hook, desk
  lane, or Studio surface.

Sidebar rules:

- Do not repeat the topbar's primary mode menu on desktop.
- Keep route parents clickable, active, and count-bearing when counts matter.
- Prefer route rows over section labels when the row itself names the group.
- Use labels only as optional dividers between unlike contextual lists.
- Use local labels such as `In World`, `In Play`, `On Your Desk`, and
  `In Studio` so the sidebar reads as contents, not another main menu.
- Keep visible items biased toward writer movement; staff/director controls can
  live in `Studio` or in object-local management areas.

Topbar community modes:

```text
Community brand/title
World
Play
Desk
Studio
```

Sidebar context examples:

```text
In World
  Locations
    Xavier Institute
      Med Bay
      Cerebro
  Guidebook
  Community Table
    Members
    Announcements
```

```text
On Your Desk
  Desk home (only away from /desk)
  Queue
  Inbox
  Roster
  Plotting
  Applications
  Discovery
```

```text
In Play
  Wanted board (only away from /wanted)
  Casting desk
  Claims
  Active Face
    Cass Mercer
  Related Wants
```

Mobile may show both the community mode list and the local context inside the
drawer because the horizontal topbar nav is hidden. Desktop should not show both
at the same time.

### Sidebar Toggle

The sidebar may have a hide/show navigation toggle. The toggle changes available
space; it does not change navigation meaning.

Allowed states:

- Expanded: normal community navigation.
- Hidden or focus: page gets more room for reading or writing.
- Mobile: same sidebar content in a drawer.

Do not use the sidebar toggle for IC/OOC, in-world/out-of-world, director/writer
mode, or active-face mode switching. Those distinctions are represented through
grouping, object context, permissions, and the active-face lens.

On desktop, the sidebar edge is the visibility affordance. Do not add a
separate visible `<` or `>` pill when the hit edge already changes cursor and
can receive focus.

An icon rail is deferred. If added later, it must be a secondary compact state
for stable universal destinations, not the main navigation experience. PBP
terms such as `Wanted`, `Roster`, `Queue`, `Plotting`, `Claims`, `Reserves`,
and `Studio` need visible words.

### In-World And Writer Work

Do not split the sidebar with an IC/OOC or in-world/out-of-world mode switch.
The product objects do not divide cleanly:

- `World` is story-facing but contains board structure.
- `Guidebook` is about canon/world materials but is director-authored.
- `Wanted` is story-facing but operational and casting-oriented.
- `Writer Desk` is out-of-character work tied to active character obligations.
- `Studio` is production/admin.

Use language and grouping instead:

- World-facing: `World`, `Guidebook`, `Wanted`.
- Writer work: `Queue`, `Roster`, `Plotting`, `Applications`, `Discovery`.
- Director work: `Studio`, `Navigation`, `Board taxonomy`, `Production`.

Active face is a lens and identity state, not a navigation mode. It may appear
as a compact sidebar context module where relevant, but it must not hide or
replace the canonical community map.

### Labels

Labels are not navigation. They are dividers.

Use unlabeled groups when the first row already names the category:

- `Locations`
- `Community`
- `Start Here`
- `Guides`
- `Events`
- `Production`

Use labels when they introduce a contextual list that is not itself a route
parent:

- `Current Event`
- `Current Material`
- `Related`
- `Active Face`
- `Open Wants`
- `Related Wants`
- Future director-configured collections, such as `Event Threads`, `House
  Boards`, `Claims`, or `Staff Queue`.

If a label and the first link say the same thing, remove the label. If a label
is the only way to understand the list, keep it.

### Sidebar Exceptions

Guidebook sidebars may include same-page anchors when they behave like a
durable table of contents for a stable director-authored collection. This is an
exception to the usual "inline rails for page jumps" rule. It stays valid only
when the anchors lead to sections that also contain object links, such as
featured materials, guides, events, and application materials.

Studio may link to writer-facing destinations when directors need to inspect
the public object from a production context. These should read as cross-realm
jumps, not as active Studio subsections. If a production area needs its own
state, queue, or settings, create a real Studio route instead of making a
writer route look like a Studio parent.

Contextual sidebar labels are allowed when the list is generated by the object
being viewed, such as related wants or current material. They should disappear
when empty.

Studio can use local room rails on long production pages. These rails move
within the current route and group controls by director intent, such as World
structure, Navigation, Identity, Casting, and Continuity. They are not sidebar
groups and should not redefine the topbar realm. Use them when the page has
several production surfaces that benefit from quick in-page movement.

### Grouping

Prefer shallow groups. A sidebar group should usually have one parent route and
its immediate children, or one contextual label with a short list.

Good shapes:

```text
Locations
  Xavier Institute
    Med Bay
    Cerebro
Community
  Members
  Announcements
  Plotting
```

```text
Desk home
My threads
Notifications
Characters
Applications
Plotting
Discover
```

Avoid shapes where every two links get a label. Labels create visual stops; too
many stops make the sidebar feel heavier than the page.

### Admin Configuration

Future forum admins should be able to configure some sidebar collections, but
not the whole navigation model.

Configurable:

- Which boards are `location`, `sublocation`, `community`, `archive`, `desk`,
  or `staff`.
- Which sidebar section a board belongs to: `locations`, `community`, `desk`,
  or `studio`. Board kind answers "what kind of object is this?"; sidebar
  section answers "where should writers reach it from?"
- Sidebar section language and rhythm: directors can rename a section, edit
  its short description, choose its relative order, and decide whether its
  divider label is visible. This is for community vocabulary, not for inventing
  new routing rules.
- Studio's Board Taxonomy editor is the canonical place to review and adjust
  this classification. Treat it as production direction: changing a board kind
  changes the board's meaning; changing sidebar placement changes navigation
  without pretending the board is a different kind of object.
- Board Taxonomy rows should foreground the director decision first: board
  name, kind, sidebar placement, visibility, and parent/child relationship.
  Form controls belong behind an `Edit placement` disclosure so the list stays
  scannable, especially on mobile.
- Studio's board editor is the deeper production room for each board: identity,
  parent, media, sort order, navigation order, visibility, and access belong
  there when a quick taxonomy row is not enough.
- Studio's Navigation Composer preview is the canonical place to inspect the
  result. It must distinguish configured sections, app-owned rows,
  board-derived rows, material-derived rows, identity-derived rows, and
  wanted-derived rows so directors understand what they are configuring.
- Optional named sidebar collections inside a realm.
- Ordering and visibility of board-derived links within allowed sections.
- Hidden boards may remain reachable by direct URL and visible in page content
  where appropriate; "hidden from navigation" means the sidebar stops
  advertising them, not that the board is deleted or permission-denied.
- Labels for custom collections, such as houses, claims, events, or staff
  queues.

Rename a section when the community has different language for the same
navigation job: `Locations` can become `Realms`, `Districts`, `Planets`, or
`Houses` if it still points at the playable map. Create or propose a new board
kind only when the underlying object meaning changes, not when the label wants
more flavor.

### Navigation Health

Navigation health warnings are soft production notes. They catch configurations
that may feel odd to writers even though the app can still render them:

- Hidden parent boards with visible children.
- Visible children whose parent is hidden from navigation.
- Places outside the map lane.
- Community boards placed inside the location map.
- Private boards in public-facing sections.
- Public boards in Studio.
- Visible section labels that do not currently introduce any board-derived
  rows.
- Labels that duplicate the first route row.

Use hard validation only when structure would break or privacy could leak
across permissions or communities. Use health warnings when the issue is
coherence, scannability, or writer expectation. Warnings should link directors
to the relevant board editor or section control, but should not block saving in
V1.

Not configurable in ordinary admin UI:

- The existence of topbar global utilities.
- The existence of canonical sidebar community rooms.
- The meaning of board kinds and sidebar sections.
- The difference between labels and route rows.
- Accessibility requirements for active states, counts, and mobile drawers.

This keeps communities expressive without making each board invent a new
navigation grammar.

## Route Pathing

Paths should reflect product meaning, not implementation convenience.

Use nouns for stable places:

- `/` for the world gateway.
- `/locations` for the playable world map.
- `/community` for community boards and writer-side public rooms.
- `/boards/{board_slug}` for forum boards, with `board_kind` deciding how they
  are presented.
- `/world` and `/world/{material_slug}` for guidebook/world materials.
- `/wanted` and `/wanted/{wanted_slug}` for structured casting hooks.
- `/desk`, `/my/threads`, `/characters`, `/applications`, `/plotting`,
  `/discover`, `/notifications` for writer work.
- `/studio` for director/admin production.

Nested routes should mean ownership or object containment:

- `/boards/{board_slug}/threads/{thread_slug}`: a thread belongs to a board.
- `/characters/{character_slug}/hooks/{hook_slug}`: a plot hook belongs to a
  character.
- `/plotting/{room_id}`: a plotting room detail.

Do not force structured primitives into board/thread paths just because old
forums did. Wanted hooks, materials, applications, reserves, and plot hooks can
have their own routes.

## Active State

Active state follows meaning, not URL prefix alone.

Examples:

- `/boards/announcements` activates `World` in the topbar because community
  boards live in the world/community surface, but activates `Community` in the
  sidebar because `announcements` is a `community` board.
- `/boards/frozen-midtown` activates `World` in the topbar and `Locations` in
  the sidebar because it is a `sublocation`.
- `/world/b-24-winter` activates `Guidebook`, not `World`, even when the
  material affects locations.
- `/applications` currently belongs to `Writer Desk` when the writer is acting
  on their own work, but may appear as a linked production destination inside
  `Studio`.

When URL prefix and navigation placement disagree, sidebar placement wins for
sidebar state. This lets a community keep domain language honest while still
making room for authored navigation: a public record board can be a community
board, a production-facing board can live in Studio, and a house/faction board
can sit where directors expect writers to find it.

## Breadcrumbs

Breadcrumbs are for lineage inside an object, not for primary navigation.

Use breadcrumbs when they clarify containment:

```text
World / New York City / Frozen Midtown
Guidebook / Current Event: B-24 Winter
Community / Announcements
Danger Room / Moonlight skirmish
```

Breadcrumbs should not carry high-priority actions. Keep actions near the
object area where the user becomes ready to act.

## Inline Nav And Filters

Inline nav/filter rails belong inside the page. They are for local movement,
not product navigation.

Use inline rails for:

- Thread list filters: `All`, `New replies`, `Needs reply`, `Mine`, `Pinned`,
  `Locked`.
- Long-page section jumps inside one object.
- Discovery/list narrowing.
- Roster or hook slices.

Inline rails should preserve the object context. If clicking a control changes
the user's mental room, it is not an inline rail.

## Tabs

Tabs are narrow. Use them only for peer views of the same durable object or
workspace.

Good future candidates:

- Character profile sections if they become real peer routes.
- Director settings sections.
- Guidebook admin views.
- Application review workspace subsections.

Avoid tabs for:

- Broad writer desk routes.
- Global product realms.
- Ordinary sidebar groups.
- List filters.
- Jump links.

Tabs say "same object, different view." If that sentence is not true, use the
sidebar, inline filters, or a page section instead.

## Dropdowns And Menus

Dropdowns hide choices. Use them when hiding choices is a feature, not a
shortcut.

Good uses:

- Active face switcher, because the current face is visible and the list can be
  long.
- Compact repeated row actions after the main action is visible.
- Staff-only secondary actions: move, lock, archive, duplicate, request
  revision.
- Long, known option lists where showing every option would crowd the main
  writing task.

Avoid dropdowns for:

- Primary navigation realms.
- The only way to find common writer actions.
- Short choices that teach the feature by being visible.
- Destructive actions without confirmation.

If a dropdown becomes the place where users always go first, promote its
contents into visible navigation or a contextual action area.

## Mobile Shape

Mobile keeps the same hierarchy but changes the container.

- The topbar keeps global/platform utilities and exposes a navigation drawer
  trigger.
- The drawer reuses the same canonical community map and current-room
  hydration as desktop. It must not introduce a separate mobile-only route
  model.
- Route parents remain visible links.
- Active face remains accessible from the shell.
- Notifications attach to the identity cluster as a compact bubble/count, not
  as an orphaned second control.
- For signed-in writers, account identity, active face, notifications, and
  theme live inside one identity menu at every width. The topbar should not
  split them into sibling buttons that compete with the community map.
- Primary page actions stay in the page, not hidden inside the drawer.

Do not create a separate mobile navigation model unless the desktop model is
already too complex.

## Decision Checklist

Before adding or moving navigation, answer:

1. Is this a realm, contextual destination, object lineage, local filter, or
   action?
2. Does this destination belong to the user's current mental room?
3. Is the route parent already naming the group?
4. Would a label clarify unlike links, or merely repeat a link?
5. Is active state determined by URL prefix, domain kind, or both?
6. Should the active face change the default destination or ordering?
7. Is this link useful to ordinary writers, directors, or both?
8. Should this be configurable by admins, or is it part of the product grammar?
9. What happens to this control on mobile?

If the answers are muddy, prefer a visible route row in the contextual sidebar
or an inline page control. Avoid adding topbar items, tabs, and dropdowns until
the mental model is clear.

## Current Sweep Notes

These are the navigation pressure points to revisit as Elbysodic grows:

- `Notifications` is intentionally visible in the shell and reachable from
  Writer Desk because it is a cross-cutting attention surface, not a realm.
- The Guidebook sidebar is acting as a table of contents plus object directory.
  Keep it only while the sections remain stable director-authored collections.
- Studio's `Production` grouping currently jumps to writer-facing routes such
  as `/applications`, `/wanted`, and `/casting`. This is acceptable as a
  shortcut, but a future production workflow should get a real `/studio/...`
  route instead of overloading those public surfaces.
- `/applications` is a current edge case: writers submit or track their own
  applications, while directors review production flow. Treat it as Writer Desk
  by default until a distinct Studio application-review route exists.
- Mobile drawer labels must match topbar realm names. Use `World`, not `Map`,
  unless the whole realm is renamed.
- Board routes depend on `board_kind` for presentation and sidebar active
  state. Do not assume every `/boards/{slug}` route is a location.
