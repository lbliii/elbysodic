# Navigation Menus

Elbysodic navigation has to do more than move between URLs. It has to preserve
the feeling that a community is a playable world, while still giving writers
fast access to queues, characters, hooks, and production tools.

Use this guide when adding routes, changing the topbar, shaping the sidebar,
choosing between tabs and filters, or deciding whether a set of links deserves
a label, dropdown, disclosure, or admin-configurable collection.

Use `docs/product/experience-direction.md` for the current reference
translation. Navigation may borrow layered context from Slack-like products,
but it must remain PBP-native: rooms, locations, scenes, wanted hooks, Desk,
Studio, active face, and writer obligations instead of channels, workspaces,
presence pressure, or generic dashboard shortcuts.

## Navigation Jobs

Every navigation surface should have one clear job.

| Surface | Job | Question It Answers |
| --- | --- | --- |
| Outermost topbar | Icon-first community/app switcher plus global utilities | "Which major part of this community am I in?" |
| Outermost sidebar rail | Icon-first persistent movement across stable rooms | "Where can I always go?" |
| Inner sidebar shell | Current mode/object contents | "What is inside this place?" |
| Breadcrumbs | Object lineage | "How did I get to this object?" |
| Inline nav/filter rail | Local page movement or list narrowing | "What part of this object/list am I viewing?" |
| Action bar/buttons | Doing work | "What can I do now?" |
| Dropdown/menu | Secondary or space-constrained choices | "What else is available without making the page noisy?" |

Do not make two surfaces answer the same question at the same weight. Duplicate
links are sometimes useful, but duplicated hierarchy is usually confusing.

When a page already has shell navigation, local navigation, and object links,
be skeptical of additional shortcut panels. A repeated link should earn its
place by serving a different journey moment: orientation, local movement,
acting, or continuation. Otherwise, keep the route in the shell/sidebar or put
it in a future command/search surface instead of repeating it as another CTA.

## Chrome Layers

Use a layered chrome model:

1. Outermost chrome is icon-first. This includes the primary topbar affordances
   and any always-present collapsed sidebar rail. Labels arrive through
   accessible names, tooltips, active state, and optional wide-screen text only
   when it does not create a second local menu.
2. Inner shell navigation is explanatory. If a mode needs children, filters, or
   local hierarchy, use text or icon-plus-text rows in the inner sidebar,
   drawer, tabs, or scoped rail.
3. Page chrome is task-local. A page action bar should only control the content
   currently displayed: compose, reply, filter, sort, watch, save, review, or
   publish. It should not become another route directory.

This keeps icons useful at the persistent edge while preserving PBP language
where writers need to read and choose.

## Accepted Shell Mapping

The accepted primary shell model is:

| Outer Rail | Icon | Audience | Inner Shell | Page Chrome |
|---|---|---|---|---|
| World Home | `home` | Public-safe | `Start Here`, `Guidebook`, `Community`, current event/material, applicant entry points | Realm pulse, premise, orientation, public/request-access posture |
| Locations | `locations` | Public-safe when locations are public | Location tree, active scenes here, related wants, current place context | Start scene here, local filters, watch/read, place management when authorized |
| Wanted | `wanted` | Public/member-safe with capability-gated actions | Wanted board, Casting, Claims, Reserves, related wants, hook handoffs | Raise interest, reserve, watch, start plotting, ready for scene |
| Desk | `desk` | Signed-in community members only | Queue, Inbox, Roster, Plotting, Applications, Discovery; applicant-state rows when relevant | Reply, mark caught up, watch, continue to next attention item |
| Studio | `studio` | Staff/director only | Operations, Launch, Discovery profile, Structure, Intake, Appearance, Content | Save, publish, review, request revision, staff-only object actions |

`Network` stays out of the default rail until cross-realm network behavior is a
real workflow.

Shell rendering is a privacy boundary. Rail items, badges, tooltips, active
state, inner rows, mobile drawer content, and counts must resolve from the
current community, membership, role, and capability. Public pages must not leak
active face, private queue counts, staff/intake routes, private object names, or
application state.

Active face is not navigation. It belongs in the identity cluster and at
commitment points such as `Reply as <face>`, `Join as <face>`, or
`Raise interest as <face>`.

## Topbar

The topbar is the stable community switcher plus the LBSodic/platform shell.
It should stay quiet at the outer edge. On desktop, primary community movement
belongs in the persistent icon rail, not a duplicate text menu in the topbar.
On mobile, the topbar owns the navigation drawer trigger because the rail is
not persistently visible.

Shared-host platform and community-home route semantics follow
`docs/architecture/multi-tenancy.md#route-and-link-contract`. Inside a
community, the brand/title links to that community home and replaces any
separate `Home` or `Now` topbar item.

Topbar owns:

- Current community identity and future community switching.
- The community brand/title as the community home affordance.
- Mobile navigation trigger for `World Home`, `Locations`, `Wanted`, `Desk`,
  and `Studio`.
- Global/community search entry using the scope contract in
  `docs/product/scoped-search.md`.
- Future explore/browse communities entry from the LBSodic home.
- Notifications indicator.
- Writer account, membership, and active-face identity menu.
- Theme, accessibility, and account utilities.
- At most one cross-cutting create/action control when it is truly global.

Topbar does not own local contents. Individual boards, location branches,
threads, materials, applications, claims, roster, plotting rooms, wanted hooks,
and discovery filters belong in the sidebar or object-local controls.

Avoid adding topbar items for:

- One-off tools.
- Individual boards, materials, characters, or rooms.
- Filters or local page modes.
- Staff-only tasks that belong inside `Studio`.
- Future features that are not yet part of the daily loop.

Topbar dropdowns are reserved for global/account utilities because they hide
structure and add hover/tap fragility on mobile.

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

When a valid global account visits a public realm where it has no active
membership, the identity cluster should show signed-in account posture without
promoting the visitor into the community shell. That state may offer request
access, logout, and a return to the Studio Network, but it must not show Desk,
active-face defaults, member queues, unread counts, or staff routes for the
current realm.

Writer Desk is the operating room that cashes out the shell promise. It should
start with "what needs me," then let the writer narrow by face lane or move to
work lanes: Queue, Inbox, Roster, Plotting, Applications, Discovery, and
Casting/Wanted. Desk should feel like a writing cockpit, not a generic tool
directory.

That means Desk links into other routes only when there is active work there.
It should not permanently duplicate the sidebar as a shortcut panel, and it
should hide resolved or zero-count work unless the absence itself is useful
confirmation.

Studio follows the same rule for directors. Studio home should answer "what
needs a director now?" and hand off to scoped Studio routes. It should not be
both the launchpad and every editor at once; dense editors belong in scoped
production rooms.

Plotting is also the current backstage pulse for wanted-hook handoffs. Keep the
route as `/plotting` until a broader backstage primitive is proven. The page can
group raised hands, in-plotting rooms, ready-for-scene rooms, and threaded
handoffs, but navigation should still present it as a writer/director work lane
rather than a new global realm.

## Sidebar

The sidebar has two possible layers: an outer compact icon rail for persistent
movement, and an inner text or icon-plus-text shell for the current community
mode or local object. It is not a second topbar, a marketing menu, or a dumping
ground for every tool. Inside a community, the outer chrome chooses the major
mode and the inner sidebar shows what is inside that mode.

The inner sidebar has two jobs:

- Show the current mode's contents using distinct local language.
- Hydrate with context for the current location, material, wanted hook, desk
  lane, or Studio surface.

Sidebar rules:

- Do not repeat the topbar's primary mode menu on desktop.
- Keep route parents clickable, active, and count-bearing when counts matter.
- Prefer route rows over section labels when the row itself names the group.
- Use labels only as optional dividers between unlike contextual lists.
- Use local labels such as `In Locations`, `In Wanted`, `On Your Desk`, and
  `In Studio` so the sidebar reads as contents, not another main menu.
- Keep visible items biased toward writer movement; staff/director controls can
  live in `Studio` or in object-local management areas.

Topbar community modes:

```text
Community brand/title
Locations
Wanted
Desk
Studio
```

Sidebar context examples:

```text
In Locations
  Locations
    Xavier Institute
      Med Bay
      Cerebro
  Active scenes here
  Related wants
```

```text
On World Home
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
In Wanted
  Wanted board (only away from /wanted)
  Casting desk
  Claims
  Reserves
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
- Compact: persistent icon rail for stable app-owned destinations.
- Hidden or focus: page gets more room for reading or writing.
- Mobile: same sidebar content in a drawer.

Do not use the sidebar toggle for IC/OOC, in-world/out-of-world, director/writer
mode, or active-face mode switching. Those distinctions are represented through
grouping, object context, permissions, and the active-face lens.

Do not make the fully hidden state the ordinary collapsed state. When the
sidebar is truly invisible, pages have to duplicate routing options or the user
is stranded. That pressure turns hubs into shortcut drawers. The default
space-saving state should be a compact rail with stable icons; full hiding is a
temporary focus mode for reading, composing, or inspecting dense material.

On desktop, the sidebar edge is the visibility affordance. Do not add a
separate visible `<` or `>` pill when the hit edge already changes cursor and
can receive focus.

An icon rail is accepted as the correct compact state, but it must be a
secondary density mode for stable universal destinations, not a dumping ground
for contextual lists. PBP terms such as `Wanted`, `Roster`, `Queue`,
`Plotting`, `Claims`, `Reserves`, and `Studio` still need visible words in
expanded navigation and accessible labels or tooltips in compact navigation.
Use the canonical SVG vocabulary in `design/sidebar-icon-vocabulary.md` for
rail-eligible destinations instead of adding page-local icon metaphors.

Recommended route-active mapping:

- `/` and `/c/{slug}`: outer `World Home`; inner world home/community context.
- `/locations` and location/sublocation boards: outer `Locations`; inner
  `Locations`.
- `/world` and `/world/*`: outer `World Home`; inner `Guidebook`.
- `/members` and community boards: outer `World Home`; inner `Community`.
- `/wanted`, `/wanted/*`, `/casting`, and `/claims`: outer `Wanted`; inner
  `Wanted`.
- `/desk`, `/my/threads`, `/notifications`, `/characters`, `/applications`,
  `/interactions`, `/plotting`, and `/discover`: outer `Desk` by default.
- `/studio` and `/studio/*`: outer `Studio`; inner Studio route.
- `/network`: future global `Network`, outside the default community rail.

If `/plotting` or `/discover` are reached from a wanted hook, the page may show
hook-context links or continuation actions, but the route remains writer work
unless a future scoped handoff route changes that contract.

### In-World And Writer Work

Do not split the sidebar with an IC/OOC or in-world/out-of-world mode switch.
The product objects do not divide cleanly:

- `World` is the realm home and orientation surface.
- `Locations` is the in-character place surface.
- `Guidebook` is about canon/world materials but is director-authored.
- `Wanted` is story-facing but operational and casting-oriented.
- `Writer Desk` is out-of-character work tied to active character obligations.
- `Studio` is production/admin.

Use language and grouping instead:

- Story-facing: `World Home`, `Locations`, `Guidebook`, `Wanted`.
- Writer work: `Queue`, `Roster`, `Plotting`, `Applications`, `Discovery`.
- Director work: `Studio`, `Navigation`, `Board map`, `Production`.

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
- `Open Wants`
- `Related Wants`
- Future director-configured collections, such as `Event Threads`, `House
  Boards`, `Claims`, or `Staff Queue`.

If a label and the first link say the same thing, remove the label. If a label
is the only way to understand the list, keep it.

Do not add a sidebar section that repeats who the writer is currently wearing.
The identity menu already owns that state. Sidebar context can show object-local
lists such as related wants, current material, or location branches; active-face
shortcuts belong in the identity menu or at the point of action.

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

If Studio uses a local room rail, avoid following it with a large grid of room
cards that repeats the same destinations at the same weight. Prefer one of
these patterns:

- local rail plus open room sections
- compact room index with counts and state
- separate Studio route chooser when the page is truly a launchpad

Studio should surface the first director job quickly: review applications,
fix navigation health, update a board, adjust appearance, publish material, or
prepare launch. Room browsing is useful only when it shortens the path to that
job.

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
Plotting
Discover
```

Avoid shapes where every two links get a label. Labels create visual stops; too
many stops make the sidebar feel heavier than the page.

Do not mirror these route links again as page-bottom shortcut panels. The Desk
can link into a route when there is active work there, but the sidebar owns
routine movement.

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
- Board and location pages are the primary place to adjust that board's
  identity, parent/sub-forum relationship, sidebar placement, and navigation
  order when the viewer has permission. Studio's Board Map view is the
  canonical audit and bulk repair surface for scanning that classification
  across the whole realm. Treat it as production direction: changing a board
  kind changes the board's meaning; changing sidebar placement changes
  navigation without pretending the board is a different kind of object.
- Board Map rows should foreground the director decision first: board
  name, kind, sidebar placement, visibility, and parent/child relationship.
  Bulk controls belong behind a repair disclosure so the list stays
  scannable, especially on mobile.
- Studio's board editor is the deeper production room for each board: identity,
  parent, media, sort order, navigation order, visibility, and access belong
  there when a quick taxonomy row is not enough.
- Studio's Sidebar Audit preview is the canonical place to inspect the
  result. It must explain each sidebar context's goal first, then distinguish
  fixed routes, configured sections, board links, current events, active-face
  routes, and wanted-hook routes without making implementation labels the main
  read.
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
The canonical shared-host route and link rules for `/`, `/network`,
`/c/{community_slug}`, tenant-scoped transports, and return paths live in
`docs/architecture/multi-tenancy.md#route-and-link-contract`.

Use nouns for stable places:

- `/locations` for the playable world map.
- `/community` for community boards and writer-side public rooms.
- `/boards/{board_slug}` for forum boards, with `board_kind` deciding how they
  are presented.
- `/world` and `/world/{material_slug}` for guidebook/world materials.
- `/wanted` and `/wanted/{wanted_slug}` for structured casting hooks.
- `/desk`, `/my/threads`, `/characters`, `/applications`, `/plotting`,
  `/discover`, `/notifications` for writer work.
- `/studio` for director/admin production.

Route-active state uses the path without query strings or fragments. Filtered
lanes such as `/claims?status=reserved`, `/network?q=...`, or
`/my/threads?character=...` should keep the same topbar/sidebar room as their
base route.

Nested routes should mean ownership or object containment:

- `/boards/{board_slug}/threads/{thread_slug}`: a thread belongs to a board.
- `/characters/{character_slug}/hooks/{hook_slug}`: a plot hook belongs to a
  character.
- `/plotting/{room_id}`: a plotting room detail.

Do not add `/backstage` only to rename wanted or plotting movement. Backstage
needs a broader cross-object contract before it becomes route vocabulary.

Do not force structured primitives into board/thread paths just because old
forums did. Wanted hooks, materials, applications, reserves, and plot hooks can
have their own routes.

## Active State

Active state follows meaning, not URL prefix alone.

Examples:

- `/boards/announcements` activates `World Home` in the outer rail because
  community boards live in the realm/community surface, but activates
  `Community` in the sidebar because `announcements` is a `community` board.
- `/boards/frozen-midtown` activates `Locations` in the outer rail and
  `Locations` in the sidebar because it is a `sublocation`.
- `/world/b-24-winter` activates `World Home` in the outer rail and
  `Guidebook` in the inner shell, even when the material affects locations.
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
- Studio's inner rail stays inside Studio-owned routes. Writer-facing routes
  such as `/applications`, `/wanted`, `/claims`, `/casting`, and `/world` can
  appear as inspect links inside a Studio room, but they must not masquerade as
  Studio subsections.
- `/applications` is a current edge case: writers submit or track their own
  applications, while directors review production flow. Treat it as Writer Desk
  by default until a distinct Studio application-review route exists.
- Mobile drawer labels must match outer rail names. Use `Locations`, not
  `Map`, for in-character place navigation unless the whole realm is renamed.
- Board routes depend on `board_kind` for presentation and sidebar active
  state. Do not assume every `/boards/{slug}` route is a location.
