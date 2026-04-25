# Information Hierarchy And UI Vocabulary

Elbysodic uses ChirpUI for primitives and defines a small product vocabulary on
top of it. The goal is not to create a second design system. The goal is to
make repeated PBP concepts read the same way everywhere: scenes, faces, world
lenses, activity, and writer obligations should have a stable visual grammar.

## Audit Baseline

The current app has several information-heavy surfaces:

- Home/world gateway: atmosphere first, then locations, queues, and activity.
- Board page: place identity, sublocations, filters, and direct scenes.
- Thread page: scene state, cast, metadata, posts, and writing actions.
- Character page: face identity, facets, plotter/wanted hooks, queue, posts.
- Wanted and casting: structured hooks, interest, reserves, and related faces.
- Writer Desk, My Threads, Notifications: meta-work that supports writing.

These screens repeat the same concepts. When they are styled ad hoc, everything
competes for attention. Elbysodic should instead decide which concepts are
identity, which are action, which are metadata, and which are signals.

## Vocabulary

### PlaceTile

Use for world locations and sublocations. It carries atmosphere and identity:
image or generated visual field, tagline, title, description, compact counters,
facets, child-place links, and latest activity.

The place name is primary. Counts and facets are secondary. Latest activity is
tertiary.

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

Active-face relevance, such as `Relevant for Magneto`, is a smart contextual
signal. It belongs on the image as a compact ASCII/icon overlay because it is
about the relationship between the current face and the place, not a count,
facet, or generic status. Keep the visible mark small and expose the full
meaning through `title` and `aria-label`.

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
basic action.

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
lists. They should not overpower the world gateway.

### CastFaces

Use for character participants and related faces. Cast is story-facing, so it
should use avatars or initials and link to character hubs.

Writer names belong in metadata. Character faces belong in cast.

### ThreadByline

Use when explaining authorship: started by character, writer username, updated
time, and optional board/location. ThreadByline should distinguish public face
from writer ownership without making every card feel administrative.

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

- Prefer active-face defaults over repeated controls when the action is safe:
  "Join as Rogue" beats a roster dropdown.
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
src/elbysodic/web/pages/_components/thread_summary.html
src/elbysodic/web/pages/_components/facets.html
src/elbysodic/web/pages/_components/wanted.html
```

App-specific styling belongs in:

```text
src/elbysodic/web/static/elbysodic-theme.css
```

ChirpUI remains the primitive layer. Elbysodic components should compose
ChirpUI surfaces, badges, buttons, layout helpers, and tokens rather than
creating page-local component systems.

## Next Audit Targets

- Convert large `chirpui/stat` usage on desk-like pages into counters where the
  values are scan helpers rather than hero metrics.
- Introduce a `MetaLine` helper if metadata patterns keep spreading across
  wanted, casting, members, and character hubs.
- Make thread bylines explicit enough to preserve face/writer distinction while
  staying quieter than scene titles.
- Decide when facets become clickable filters and keep that affordance
  visually different from non-clickable descriptive chips.
