# Elbysodic Agent Guide

This file is the handoff note for future coding agents. Read it before making
product or architecture decisions.

## Mission

Elbysodic is a roleplay-native play-by-post forum platform. It is not a generic
forum skin. The product should understand the culture of Jcink, InvisionFree,
all things roleplay directories, Tumblr roleplay, and long-form collaborative
fiction communities.

Elbysodic is becoming the studio layer for PBP. Treat a community as a small
creative production with directors, writers, characters, scenes, locations,
events, canon, casting needs, and continuity. The product should make those
ideas native to the code instead of forcing communities to fake them with
generic forums, templates, and manual lists.

The north star is to give PBP a new lease on life: preserve character identity,
thread continuity, community aesthetic control, and the emotional safety of
pseudonymous writing spaces, while removing the repetitive manual work older
platforms forced roleplayers to do.

## Stack And Style

- The app is built on Chirp and Chirp-UI.
- Prefer server-rendered Chirp pages and small progressive-enhancement islands.
- Chirp supports Alpine; use it for focused client-side interactions like the
  composer, not for turning the app into an SPA.
- Use Chirp-UI components, shell patterns, and token names first.
- Elbysodic-specific design belongs in `src/elbysodic/web/static/elbysodic-theme.css`
  as an app token layer on top of Chirp-UI, including light, dark, and system
  theme behavior.
- Repeated PBP UI concepts belong in the Elbysodic vocabulary components under
  `src/elbysodic/web/pages/_components/` before they become page-local CSS.
  Use `docs/product/information-hierarchy.md` for the meaning of counters,
  facets, state badges, latest lines, cast faces, and metadata.
- Keep frontend controls complete and ergonomic for roleplayers doing real
  writing: stable composer dimensions, previews, drafts, toolbar affordances,
  and clear character context.

## Product Decisions

- MVP experience is one community per install.
- Architecture is tenant-aware from day one; forum-domain rows and service
  operations stay scoped by `community_id`.
- Users are global login accounts.
- `CommunityMembership` is the user's identity inside one community.
- Permissions, roles, usernames, display names, and default character settings
  belong to membership, not user.
- There are no global characters. A character belongs to exactly one membership
  in exactly one community.
- Characters are public posting identities, aliases, and roster faces. They are
  core product primitives, not profile decoration.
- The active/default face is a product lens, not just a composer default. When
  a writer is browsing as a character, discovery, queues, joins, and future
  filters should reduce cognitive load by assuming that face where safe.
- Facets are director-defined world lenses. They can describe species,
  factions, locations, plot lanes, application categories, or any other
  community-specific dimension the board uses to make its world playable.
- Pillar content does not have to be a thread. World materials, events,
  application guides, claims, reserves, and wanted hooks can be first-class
  objects when that better fits the PBP ritual.

## Current Product Spine

The current prototype already has:

- Seeded SQLite development forum with one default community.
- Boards, threads, posts, and character-authored posting.
- Community-local character roster and active/default face switching.
- Board, thread, home, character, and "My threads" views.
- Safe post markup rendering, composer toolbar, preview toggle, and local draft
  restore.
- Thread read state, first-unread jumps, next-unread navigation, sidebar board
  counts, and "caught up" status.
- Queue language for "needs reply" and "waiting on others" rather than generic
  unread-only forum language.
- Post editing and revision history.
- Staff thread lifecycle controls: pin, lock, unlock, unpin, and move.
- Thread watches, character and writer mention detection, notification inbox,
  and shell notification counts.
- Director-defined facets for characters, boards, threads, materials, discovery,
  and wanted hooks.
- World materials for premise, rules, factions, application guidance, and
  events outside the forum/thread format.
- Wanted hooks as first-class plot and casting invitations linked to characters,
  world materials, and facets.
- Character profiles are becoming hubs: profile identity, plotter hooks,
  writing tracker, and recent posts.

## Product Shape To Preserve

- The world should be the default emotional surface. Writer/admin tooling should
  support the fiction without visually outshouting the community's atmosphere.
- Character pages should continue moving toward a hub model: identity at the
  top, plotter and wanted material near the character, tracker/queue below it,
  and world/facet context where it helps.
- Wanted hooks should stay more structured than ordinary plotter threads. They
  can become claimable/reservable, notify creators, spawn applications, or spawn
  plotting threads, but they should remain a first-class object.
- Applications, claims, reserves, canons, face claims, and wanted ads belong near
  the "materials of running a board." They may integrate with threads, but they
  should not be forced to be threads by default.
- Plot discovery should use facets and the active face to help writers find
  compatible people, open scenes, event roles, and faction pressure.
- Keep visual and cognitive load low by using the current face, current lens,
  and director-authored structure to choose sensible defaults.
- When a feature feels like board production material, consider whether it
  belongs in the studio layer: world materials, events, applications, claims,
  reserves, casting, wanted hooks, and future director tools.

## Architecture Rules

- Keep tenant boundaries explicit in schema, repository, services, permissions,
  cache keys, exports, and tests.
- Add service-layer methods that accept or resolve community/membership context
  rather than reaching around it in page handlers.
- Prefer repository methods over ad hoc SQL in web pages.
- New structured content should be community-scoped from the first schema, even
  when the MVP only exposes one community.
- If a feature can involve a writer identity and a character identity, store both
  intentionally: membership for ownership/permissions, character for public
  authorship or story context.
- When adding a new forum primitive, ask:
  - Is it community-scoped?
  - Is it membership-scoped or character-scoped?
  - Is it director-authored, writer-authored, or both?
  - Should it be a thread, or does it deserve a structured primitive?
  - Does the active face provide a safe default?
  - Does it need export support later?
  - Can it leak staff/private data across communities or roles?
- Tests should cover behavior through both repository boundaries and rendered
  pages when the feature affects user workflow.

## Scoped Agent Guides

Root `AGENTS.md` is currently the source of truth. Add nested `AGENTS.md` files
only when a subtree has materially different rules, such as a future package
with its own design contract, migration workflow, or generated assets. When
nested guides exist, the closest guide should refine this one rather than
contradicting the mission or tenant-boundary rules.

## Development Commands

Use the project tools before handing work back:

```bash
uv run ruff check .
uv run ruff format . --check
uv run pytest -q --tb=short
uv run ty check src/elbysodic/ tests/
uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"
```

For local browser QA, run the app on port 8001:

```bash
elbysodic serve --port 8001
```

or, in this workspace, the known direct form:

```bash
.venv/bin/python -c "from elbysodic.web import create_app; create_app(debug=False).run(port=8001)"
```

## Product Voice

Use language that fits roleplayers. Prefer "face", "roster", "thread",
"scene", "plotter", "wanted", "claims", "reserves", "needs reply", "waiting",
"caught up", and "watching" over generic forum jargon when the PBP concept is
more precise.

The interface should feel like a calm, capable writing room: dense enough for
regular players, gentle enough for long sessions, and expressive enough to let
communities feel like themselves.
