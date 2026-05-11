# Sidebar Icon Vocabulary

Elbysodic needs icons that make the collapsed sidebar useful without forcing
hub pages to repeat navigation. The icon system should clarify major product
rooms and repeated PBP objects, while keeping the expanded sidebar text-first.

The first SVG sprite lives at
`src/elbysodic/web/static/icons/sidebar.svg`.

## Principles

- Use icons for stable app-owned destinations, not every generated object.
- Keep expanded sidebar labels as the default. Icons support scanning and the
  compact rail; they do not replace words where space exists.
- Treat outermost chrome as icon-first. Inner shells can use text or
  icon-plus-text; page action bars should stay scoped to the displayed content.
- Make the collapsed rail an ordinary navigation state. Fully hidden sidebar is
  a focus mode only.
- Keep metaphors specific to roleplay work: scenes, faces, wanted hooks,
  plotting, claims, reserves, applications, and director studio operations.
- Use one icon per concept across the app. Do not create page-local variants.
- Avoid using the same star, diamond, grid, or gear for unrelated destinations.
- Keep SVGs monoline, 24x24, `currentColor`, rounded caps/joins, and no text.
- Let technicolor futurism come from state, color, glow, and motion tokens, not
  from overly decorative icon shapes.

## SVG Contract

All sidebar icons use:

- `viewBox="0 0 24 24"`
- `fill="none"`
- `stroke="currentColor"`
- `stroke-width="1.75"`
- `stroke-linecap="round"`
- `stroke-linejoin="round"`

Render icons as decorative when a label is visible:

```html
<svg class="elbysodic-nav-icon" aria-hidden="true">
  <use href="/elbysodic-static/icons/sidebar.svg#elbysodic-icon-desk"></use>
</svg>
```

In compact rail mode, every icon-only link needs a stable accessible label via
`aria-label` and a hover/focus tooltip. Counts should render as a separate badge
overlay, not as part of the SVG.

## Primary Rail

These are the only destinations that should appear in the collapsed rail by
default. They are stable, app-owned, and broad enough to survive route cleanup.

| Destination | Icon ID | Visual Metaphor | Notes |
|---|---|---|---|
| World Home | `home` | house/gate | Realm landing page: premise, current pulse, orientation, and entry points. |
| Locations | `locations` | folded map | In-character place navigation: location tree, active scenes, and place context. |
| Wanted | `wanted` | star hook | Writer-facing entry into wanted hooks, casting, claims, and reserves. Prefer this over a vague `Play` icon. |
| Desk | `desk` | writing surface with pen | Personal attention cockpit: reply queue, inbox, roster, current work. |
| Studio | `studio` | director diamond with controls | Staff/director operating room. Do not use a generic gear. |
| Network | `network` | orbiting nodes | Cross-realm or global writer network when it exists as a real route. |

Rail visibility is audience-aware:

- Anonymous and public preview viewers get public-safe realm navigation only.
- Signed-in community members can see Desk and member-appropriate badges.
- Staff/directors can see Studio and staff-appropriate production state.
- Counts, badges, tooltips, and disabled labels must not reveal private
  objects, active face, application state, staff notes, or cross-community
  work.

## Sidebar Destination Set

These are the major icons available to sidebar sections. Rail eligibility means
the item can appear in the compact rail or compact section popover without a
page duplicating the same route.

| Concept | Icon ID | Rail Eligible | Meaning |
|---|---:|---:|---|
| Home | `home` | Yes | Current room landing page. |
| World Home | `home` | Yes | Realm landing page and orientation surface. |
| World | `world` | No | Broad public-world context when the product needs the umbrella term. Prefer `World Home` or `Locations` in navigation. |
| Wanted | `wanted` | Yes | Hooks, casting, claims, reserves entry. |
| Desk | `desk` | Yes | Writer attention and personal work. |
| Studio | `studio` | Yes | Director/staff tools. |
| Network | `network` | Yes | Cross-realm writer network. |
| Locations | `locations` | Yes | Places, regions, and scene geography. |
| Guidebook | `guidebook` | Yes | Director-authored reference material. |
| Community | `community` | Yes | Realm people and social surface. |
| Members | `members` | Yes | Membership and staff-facing people lists. |
| Queue | `queue` | Yes | Threads/scenes needing action. |
| Inbox | `inbox` | Yes | Notifications, mentions, pings, and replies. |
| Roster | `roster` | Yes | Owned faces and character pages. |
| Plotting | `plotting` | Yes | Plotter rooms and collaboration planning. |
| Applications | `applications` | Yes | Drafts and submitted applications. Accepted applications should leave this lane and become roster/face pages. |
| Artifacts | `artifacts` | No | Derived or linked realm material. Keep scoped unless it becomes a primary workflow. |
| Discovery | `discovery` | Yes | Finding scenes, hooks, people, and opportunities. |
| Casting | `casting` | Yes | Open faces and application-facing cast work. |
| Claims | `claims` | Yes | Taken or requested claims. |
| Reserves | `reserves` | Yes | Temporarily held faces, claims, or slots. |
| Operations | `operations` | Yes | Studio dashboard and active staff work. |
| Launch | `launch` | Yes | Realm setup, opening, and launch checklist. |
| Boards | `boards` | Yes | Forum board structure. |
| Navigation | `navigation` | Yes | Menus and route organization. |
| Appearance | `appearance` | Yes | Theme, tone, visual system, and surface polish. |
| Intake | `intake` | Yes | Applications, submissions, and reviews from a staff lens. |
| Continuity | `continuity` | Yes | Canon, provenance, reviewed scene memory. |
| Materials | `materials` | Yes | World materials, guides, events, canon docs. |
| Events | `events` | Yes | Time-bound realm events. |
| Scene | `scene` | No | Individual threads/scenes. Use in rows, not primary rail. |
| Face | `face` | No | Individual public posting identity. Use in rows/cards/profile chips. |
| Notifications | `notifications` | Yes | Notification center when separated from inbox. |
| Settings | `settings` | No | Generic settings only. Prefer specific icons for Studio pages. |

## Current Route Mapping

Use this mapping as the first pass before route reorganization.

| Current Route | Label | Icon ID | Sidebar Room |
|---|---|---|---|
| `/` | World Home | `home` | Primary rail |
| `/locations` | Locations | `locations` | Primary rail |
| `/wanted` | Wanted | `wanted` | Primary rail |
| `/desk` | Desk | `desk` | Primary rail |
| `/studio` | Studio | `studio` | Primary rail |
| `/guidebook` | Guidebook | `guidebook` | World Home |
| `/members` | Community | `community` | World Home |
| `/my/threads` | Queue | `queue` | Desk |
| `/notifications` | Inbox | `inbox` | Desk |
| `/characters` | Roster | `roster` | Desk |
| `/plotting` | Plotting | `plotting` | Desk/Wanted |
| `/applications` | Applications | `applications` | Desk now, Intake later |
| `/interactions` | Realm Artifacts | `artifacts` | Desk |
| `/discover` | Discovery | `discovery` | Desk/Wanted |
| `/casting` | Casting | `casting` | Wanted/Studio |
| `/claims` | Claims | `claims` | Wanted/Studio |
| `/studio/taxonomy` | Taxonomy | `materials` | Studio |
| `/studio/navigation` | Navigation | `navigation` | Studio |
| `/studio/boards` | Boards | `boards` | Studio |
| `/studio/world` | World Materials | `materials` | Studio |
| `/studio/guidebook` | Guidebook | `guidebook` | Studio |

## Proposed Studio Split

If we reorganize Studio, use these icon anchors instead of allowing Studio to
become another dumping drawer:

| Proposed Route | Icon ID | Focus |
|---|---|---|
| `/studio/operations` | `operations` | Staff work queue, moderation, health, recent production activity. |
| `/studio/launch` | `launch` | Blueprint, setup, opening checklist, launch readiness. |
| `/studio/navigation` | `navigation` | Menus, hierarchy, sidebar behavior, route ordering. |
| `/studio/boards` | `boards` | Board structure and forum surfaces. |
| `/studio/appearance` | `appearance` | Theme, layout density, color, polish, visual controls. |
| `/studio/intake` | `intake` | Applications, submissions, review lanes, casting operations. |
| `/studio/continuity` | `continuity` | Reviewed scene memory, canon, provenance, timeline, claims lineage. |

## Not Iconified

Keep these expanded-only or row-level:

- Generated board names.
- Generated location trees.
- Individual faces.
- Individual scenes.
- Individual guidebook entries.
- Staff-only moderation actions.
- Duplicate shortcuts that only repeat visible sidebar routes.
