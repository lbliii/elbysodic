# Elbysodic

Elbysodic is a roleplay-native play-by-post community platform built on Chirp
and Chirp-UI. It starts with the familiar forum loop of boards, threads, posts,
and long-form replies, then makes the surrounding PBP studio work native:
characters, rosters, facets, world materials, wanted hooks, casting needs,
applications, queues, notifications, and continuity.

The MVP experience is one community per install. The architecture is
tenant-aware from the beginning, so community identity, membership permissions,
rosters, posts, materials, and staff workflows stay scoped by `community_id`
even while local development seeds a single default community.

## Product Shape

Elbysodic is not a generic forum skin. It is designed for communities shaped by
Jcink, InvisionFree, roleplay directories, Tumblr roleplay, and long-form
collaborative fiction spaces.

The forum remains the heart of play, but the product treats board-running
materials as first-class objects when threads are the wrong shape for the job.
Characters are public posting identities, not profile decoration. Facets are
director-defined world lenses, not just tags. Wanted hooks are structured plot
and casting invitations. World materials carry premise, rules, factions,
application guidance, events, and future claims or reserves.

The interface should feel like a calm writing room: dense enough for regular
players, gentle enough for long sessions, and expressive enough for a community
to feel like itself.

## Current Slice

The development app currently includes:

- Community-scoped boards, threads, posts, and seeded demo content.
- Global users with community-local memberships, roles, usernames, permissions,
  and default face settings.
- Character-authored posting with community-local rosters and active face
  switching.
- Board, thread, home, character, member, community, locations, world, casting,
  applications, wanted, Writer Desk, My Threads, and notification views.
- Safe post markup rendering, composer toolbar affordances, preview toggle, and
  local draft restore.
- Thread read state, first-unread jumps, next-unread navigation, sidebar board
  counts, and caught-up status.
- Queue language for needs reply and waiting on others.
- Post editing with revision history.
- Staff thread lifecycle controls: pin, lock, unlock, unpin, and move.
- Thread watches, character and writer mention detection, and notification
  inbox counts.
- Director-defined facets for characters, boards, threads, world materials,
  discovery, and wanted hooks.
- World materials for premise, rules, factions, application guidance, and
  events outside the forum/thread format.
- Wanted hooks as first-class plot and casting invitations linked to
  characters, world materials, and facets.
- Character profile hubs with identity, plotter hooks, tracker context, and
  recent posts.

## Architecture

The core product primitives are documented in
[docs/architecture/primitives.md](docs/architecture/primitives.md). The
multi-tenancy strategy lives in
[docs/architecture/multi-tenancy.md](docs/architecture/multi-tenancy.md). The
product mission and UI vocabulary live in
[docs/product/mission.md](docs/product/mission.md) and
[docs/product/information-hierarchy.md](docs/product/information-hierarchy.md).

Future coding agents should start with [AGENTS.md](AGENTS.md). It captures the
current product spine, architectural invariants, vocabulary, implementation
style, and local development expectations.

Important invariants:

- Users are global login accounts.
- `CommunityMembership` is the user's identity inside one community.
- Permissions, roles, usernames, display names, and default character settings
  belong to membership.
- Characters belong to exactly one membership in exactly one community.
- Store membership identity for ownership and permissions, and character
  identity for public authorship or story context.
- New structured content should be community-scoped from its first schema.
- Prefer repository and service methods over ad hoc SQL in page handlers.
- Prefer server-rendered Chirp pages with small progressive-enhancement islands.
- Put repeated PBP UI concepts in
  `src/elbysodic/web/pages/_components/` before they become page-local CSS.
- Put Elbysodic theme tokens in
  `src/elbysodic/web/static/elbysodic-theme.css`.

## Local Dependency Layout

The package declares normal published dependencies:

```toml
bengal-chirp[config,forms,sessions,ui]>=0.5.0
chirp-ui>=0.5.0
```

For local development, `uv` overrides the owned stack with editable sibling
checkouts:

```toml
[tool.uv.sources]
bengal-chirp = { path = "../python/b-stack/chirp", editable = true }
chirp-ui = { path = "../python/chirp-ui", editable = true }
kida-templates = { path = "../python/b-stack/kida", editable = true }
bengal-pounce = { path = "../python/b-stack/pounce", editable = true }
```

`make install` runs `uv sync --active --group dev --frozen`, so those local
paths must exist when working from the checked-in lockfile. Third-party
dependencies still resolve from the lockfile and registry.

## Development

Create the Python 3.14t environment and install the project:

```bash
make setup
make install
```

Run the local gate:

```bash
make ci
```

Useful commands:

- `make test` runs the test suite.
- `make lint` runs Ruff.
- `make format` formats the project.
- `make format-check` checks Ruff formatting.
- `make ty` runs Astral's `ty` checker.
- `make changelog-draft` previews Towncrier fragments.
- `make build` builds distribution packages.

The full handoff gate used by agents is:

```bash
uv run ruff check .
uv run ruff format . --check
uv run pytest -q --tb=short
uv run ty check src/elbysodic/ tests/
uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"
```

## Running Locally

Local development uses SQLite at `var/elbysodic.sqlite3` by default. Override it
with `ELBYSODIC_DB_PATH` or `elbysodic --db-path path/to/forum.sqlite3`.

```bash
elbysodic init-db
elbysodic serve --port 8001
```

In this workspace, the direct app form is also useful:

```bash
.venv/bin/python -c "from elbysodic.web import create_app; create_app(debug=False).run(port=8001)"
```

## Product Voice

Use language that fits roleplayers. Prefer face, roster, thread, scene,
plotter, wanted, claims, reserves, needs reply, waiting, caught up, and
watching when those words are more precise than generic forum jargon.
