# Elbysodic Agent Guide

This file is the handoff note for future coding agents. Read it before making
product or architecture decisions.

## Mission

Elbysodic is a roleplay-native play-by-post forum platform. It is not a generic
forum skin. The product should understand the culture of Jcink, InvisionFree,
all things roleplay directories, Tumblr roleplay, and long-form collaborative
fiction communities.

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
- Thread watches, `@Character` mention detection, notification inbox, and shell
  notification counts.

## Architecture Rules

- Keep tenant boundaries explicit in schema, repository, services, permissions,
  cache keys, exports, and tests.
- Add service-layer methods that accept or resolve community/membership context
  rather than reaching around it in page handlers.
- Prefer repository methods over ad hoc SQL in web pages.
- When adding a new forum primitive, ask:
  - Is it community-scoped?
  - Is it membership-scoped or character-scoped?
  - Does it need export support later?
  - Can it leak staff/private data across communities or roles?
- Tests should cover behavior through both repository boundaries and rendered
  pages when the feature affects user workflow.

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
"scene", "needs reply", "waiting", "caught up", and "watching" over generic
forum jargon when the PBP concept is more precise.

The interface should feel like a calm, capable writing room: dense enough for
regular players, gentle enough for long sessions, and expressive enough to let
communities feel like themselves.
