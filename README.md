# Elbysodic

Elbysodic is an early-stage play-by-post forum application built on Chirp and
Chirp-UI. The product experience starts as one community per install, while the
data and service layer are tenant-aware from the first migration.

## Development

```bash
make setup
make install
make ci
```

Useful commands:

- `make test` runs the test suite.
- `make lint` runs Ruff.
- `make format` formats the project.
- `make ty` runs Astral's `ty` checker.
- `make changelog-draft` previews Towncrier fragments.

Local development uses SQLite at `var/elbysodic.sqlite3` by default. Override it
with `ELBYSODIC_DB_PATH` or `elbysodic --db-path path/to/forum.sqlite3`.

```bash
elbysodic init-db
elbysodic serve --port 8001
```

## Architecture

The MVP resolves one default community, but forum-domain tables and services
all receive a `community_id`. See
[docs/architecture/multi-tenancy.md](docs/architecture/multi-tenancy.md) for the
current strategy.

The first product primitives live in
[docs/architecture/primitives.md](docs/architecture/primitives.md).

The product mission lives in [docs/product/mission.md](docs/product/mission.md).

Future coding agents should start with [AGENTS.md](AGENTS.md), which captures
the current product spine, architectural invariants, and implementation style.

## Current Slice

The development forum currently includes community-scoped boards, threads,
posts, character rosters, active face switching, safe post markup, composer
preview/drafts, read-state queues, first-unread jumps, post editing with
revision history, staff thread controls, thread watches, character and writer
mentions, and a notification inbox.

It also includes early PBP-native structure beyond threads: director-defined
facets, plot discovery, world materials for premise/factions/applications/events,
wanted hooks, richer seed writers, and character profile hubs with plotter and
tracker sections.
