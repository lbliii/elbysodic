# Elbysodic

Elbysodic is a roleplay-native play-by-post community platform built on Chirp
and Chirp-UI. It starts with the familiar forum loop of boards, threads, posts,
and long-form replies, then makes the surrounding PBP studio work native:
characters, rosters, facets, world materials, wanted hooks, casting needs,
applications, queues, notifications, and continuity.

The MVP experience is one primary community per production install, with a
seeded multi-community network for local and Railway demo QA. The architecture
is tenant-aware from the beginning, so community identity, membership
permissions, rosters, posts, materials, and staff workflows stay scoped by
`community_id`. On shared hosts, community links use `/c/{community_slug}` so a
realm is resolved before local slugs are looked up.

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

The top-level strategy is organized around three pillars:

- **Realm Studio**: director and staff workflows for opening, running, shaping,
  reviewing, exporting, and preserving PBP realms.
- **Writer Network**: writer-facing identity, active face, obligations,
  discovery, continuation, wanted hooks, plotting, and cross-realm entry paths.
- **Continuity Graph**: reviewed, source-linked memory from completed scenes
  into canon, characters, locations, events, claims, reserves, wanted hooks,
  and world materials.

See [docs/product/strategy-spine.md](docs/product/strategy-spine.md) for the
canonical product spine that guides roadmap and steward decisions.

The interface should feel like a calm writing room: dense enough for regular
players, gentle enough for long sessions, and expressive enough for a community
to feel like itself.

## Current Slice

The development app currently includes:

- Community-scoped boards, threads, posts, and seeded demo content.
- Global users with community-local memberships, roles, usernames, permissions,
  and default face settings.
- Local login/logout sessions, production-mode session gating, CSRF-protected
  forms, and development-only persona switching.
- Character-authored posting with community-local rosters and active face
  switching.
- Tenant-prefixed shared-host routing for seeded realms and a platform/network
  home at `/` and `/network`.
- Board, thread, home, character, member, community, locations, world, casting,
  claims, applications, wanted, Writer Desk, My Threads, plotting,
  interactions, Studio, and notification views.
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
- Claims, reserves, applications, review rooms, plotting rooms, and
  notification-backed writing/workflow handoffs.
- Character profile hubs with identity, plotter hooks, tracker context, and
  recent posts.
- Studio production surfaces for operations, boards, Blueprint intake,
  and board-running controls.
- Safe Program Blueprint parsing, validation, and dry-run preview, followed by
  transactional apply with stale-preview checks and idempotent replay.

Gated production-readiness work is tracked on GitHub saga
[#141](https://github.com/lbliii/elbysodic/issues/141) and the live index in
[plans/README.md](plans/README.md).
The current launch posture is invite-style access: public discovery and a
request-access placeholder are visible, while account and membership creation
happens through director-created invite links until a full registration
contract is explicitly designed.

Creator onboarding is tracked as a director-led realm opening flow, not public
self-serve registration. A production install starts with no realm or one empty
configured realm, then Studio guides directors through realm identity, scene
hubs, director materials, intake and claims, appearance, invitations, and a
launch checklist before public preview.

The current first-realm path is an operator bootstrap command. It creates the
community, first director login account, community-local director membership,
sidebar defaults, and default theme inside one transaction; it does not create
placeholder threads, claims, wanted hooks, or invite-management rows. Directors
can use the Studio launch room afterward to create the minimum opening packet
and invite writers.

```bash
uv run elbysodic bootstrap-first-realm \
  --realm-name "Example Realm" \
  --realm-slug example-realm \
  --director-email director@example.com \
  --director-password "change-me-before-use" \
  --director-username director \
  --director-name "Realm Director"
```

Until the realm has a published premise and at least one public scene hub,
logged-out `/` and `/network` treat it as backstage. Directors can continue
setup from `/c/{realm_slug}/studio/launch`.

## Architecture

The core product primitives are documented in
[docs/architecture/primitives.md](docs/architecture/primitives.md). The
product strategy spine lives in
[docs/product/strategy-spine.md](docs/product/strategy-spine.md). The
multi-tenancy strategy lives in
[docs/architecture/multi-tenancy.md](docs/architecture/multi-tenancy.md).
Schema migration rules live in
[docs/architecture/migrations.md](docs/architecture/migrations.md), and tenant
and permission boundaries live in
[docs/architecture/security-boundaries.md](docs/architecture/security-boundaries.md).
The product mission and UI vocabulary live in
[docs/product/mission.md](docs/product/mission.md) and
[docs/product/information-hierarchy.md](docs/product/information-hierarchy.md).

Future coding agents should start with [AGENTS.md](AGENTS.md). It captures the
current product spine, architectural invariants, vocabulary, implementation
style, local development expectations, and the GitHub saga → epic → design →
leaf work lifecycle. Specs live in issues; see
[docs/plan/issue-lifecycle.md](docs/plan/issue-lifecycle.md).

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
bengal-chirp[auth,config,forms,passkeys,sessions,ui]>=0.10.0
bengal-pounce>=0.9.1,<0.10.0
chirp-ui>=0.11.0
```

For local development, you can keep editable sibling checkout overrides in an
ignored `uv.toml`:

```toml
[tool.uv.sources]
bengal-chirp = { path = "../python/b-stack/chirp", editable = true }
chirp-ui = { path = "../python/chirp-ui", editable = true }
kida-templates = { path = "../python/b-stack/kida", editable = true }
bengal-pounce = { path = "../python/b-stack/pounce", editable = true }
```

The checked-in `pyproject.toml` and `uv.lock` intentionally do not include
those local paths, so Railway and other clean builders resolve the Chirp stack
from the registry. Third-party dependencies still resolve from the lockfile.

## Development

Create the pinned Python 3.14.2 environment and install the project. Install
Node.js 22 or newer for executable composer behavior tests (no npm packages
are required). Node is a development prerequisite, not an app runtime:

```bash
make setup
make install
```

Standard and free-threaded Python are supported. To exercise the CI runtime,
use `make setup PYTHON_VERSION=3.14.2t` in a separate checkout, then
`make install` and `PYTHON_GIL=0 make test-cov`. Local process smoke verifies
the subprocess reports the same GIL posture as its interpreter.

Run the local gate:

```bash
make ci
```

Useful commands:

- `make test` runs the test suite.
- `make test-cov` runs parallel-safe tests with pytest-xdist, then appends the
  three serial process tests to one coverage result; CI enforces an 80% floor
  via pytest-cov and reports the slowest tests.
- `make lint` runs Ruff.
- `make format` formats the project.
- `make format-check` checks Ruff formatting.
- `make ty` runs Astral's `ty` checker.
- `make milo-check` verifies typed command schemas plus the documented CLI,
  LLM-discovery, and MCP surface allowlist.
- `make changelog-draft` previews Towncrier fragments.
- `make build` builds distribution packages.
- `uv run pounce check --app elbysodic.web:create_app --format plain` validates
  the Pounce import/config path used by the Chirp production server.

Make, Poe, and `elbysodic dev check` share `elbysodic.checks`. The full
handoff gate includes lint, formatting, types, strict app checks, Kida,
hypermedia baseline, executable client tests, pytest, and contract diff:

```bash
uv run python -m elbysodic.checks --full
```

`make check` runs the same checks without pytest or contract diff. The CLI's
`dev check --quick` retains all static/client checks, narrows pytest to the CLI,
and omits contract diff.

## Running Locally

Local development uses SQLite at `var/elbysodic.sqlite3` by default. Override it
with `ELBYSODIC_DB_PATH` or `elbysodic --db-path path/to/forum.sqlite3`.

```bash
elbysodic init-db
elbysodic seed-demo
elbysodic serve --port 8001
```

For the standard seeded local preview, developers can use the Milo-backed dev
namespace:

```bash
elbysodic dev preview
```

It prepares the local SQLite database with demo realm data and serves the app
at `http://127.0.0.1:8001/`. Pass `--no-seed-demo` when you only want schema
initialization before serving.

For local navigation and htmx timing checks, use the production-like preview
task. It keeps `debug=False` while enabling dev tools, including the htmx timing
harness.

```bash
uv run poe preview-prod-devtools
```

With that preview running, the latest-click-wins browser harness can exercise
rapid htmx navigation settlement:

```bash
uv run poe latest-click-wins-qa
```

The first-writer activation browser harness covers invite acceptance, the
first-face application handoff, wanted browsing, and plotting entrypoints:

```bash
uv run poe writer-activation-qa
```

Stop local servers with `Ctrl-C`/`SIGINT` or `SIGTERM` so Elbysodic can close
its app services and SQLite connection. Debug-mode `serve` and `dev preview`
also treat `SIGHUP` as a local shutdown signal. Deleting or archiving a live
worktree is not a clean shutdown contract; stop the process first, then archive
or remove the isolated checkout.

Use the developer DB helpers before copying or preserving a local realm
database:

```bash
elbysodic dev db checkpoint
elbysodic dev db backup --output var/elbysodic-backup.sqlite3
```

`checkpoint` runs a TRUNCATE WAL checkpoint against the configured SQLite file.
`backup` uses SQLite's online backup API and refuses to overwrite an existing
file unless `--overwrite` is passed.

To verify a copied database without restoring it destructively, run the
read-only restore-check service against the candidate file:

```bash
uv run python -c "from pathlib import Path; from elbysodic.services.operations import format_restore_check_report, restore_check_database; print(format_restore_check_report(restore_check_database(Path('var/elbysodic-backup.sqlite3'))))"
```

The report includes integrity, schema/migration versions, core counts, and
service readback status. It deliberately omits emails, token hashes, session
tokens, post bodies, private notes, and credentials.

Before handing off a branch, run the developer gate:

```bash
elbysodic dev check
```

Use `--quick` when iterating on the CLI itself; it keeps all static and client
checks, narrows pytest to the CLI tests, and skips the hypermedia contract diff.

In this workspace, the direct app form is also useful:

```bash
.venv/bin/python -c "from elbysodic.web import create_app; create_app(debug=False).run(port=8001)"
```

Keep local dependency source overrides out of committed project metadata.
`pyproject.toml` and `uv.lock` should resolve Chirp stack packages from the
registry so Railway can build the app. Local-only uv config belongs in ignored
`uv.toml`, and committed lockfile updates should be regenerated without local
editable path sources.

The checked-in lockfile tracks Chirp 0.10, Chirp-UI 0.11, Kida 0.11, and
Pounce 0.9.1. The strict app check treats warnings as failures. When moving
templates inside a folder, prefer Kida's `./` relative imports for sibling
`_components` references so local component groups stay refactor-safe.

## Deploying To Railway

The repository includes `railway.json` for Railpack deployments. Railway starts
the app with:

```bash
elbysodic --host 0.0.0.0 --port $PORT --no-debug
```

The app creates the SQLite schema on startup. Seed the demo forum intentionally
with `elbysodic seed-demo` before sharing demo credentials. For a long-lived
demo, attach a Railway Volume to the service. Railway
exposes the mount at `RAILWAY_VOLUME_MOUNT_PATH`, and Elbysodic stores SQLite at
`$RAILWAY_VOLUME_MOUNT_PATH/elbysodic.sqlite3` unless `ELBYSODIC_DB_PATH` is set.
The recommended mount path is `/app/var`, which also matches the local
`var/elbysodic.sqlite3` layout.

Set these Railway variables before sharing the app:

- `ELBYSODIC_ENV=production`
- `ELBYSODIC_SECRET_KEY` to a random value of at least 32 characters
- `ELBYSODIC_DEMO_MODE=1` only when seeded demo credentials should work

For the shared staging demo, set `ELBYSODIC_ENV=staging`,
`ELBYSODIC_DEMO_MODE=1`, `ELBYSODIC_AUTO_SEED_DEMO=1`, and
`ELBYSODIC_DB_PATH=/app/var/elbysodic.sqlite3`. This lets staging self-heal
missing demo rows on startup while still requiring demo mode and the
volume-backed database path. Do not set `ELBYSODIC_AUTO_SEED_DEMO` in
production.

`ELBYSODIC_ALLOWED_HOSTS` is optional for Railway because production defaults
allow Railway domains. Set it only after confirming the exact public or custom
host list; values are comma-separated hostnames without `https://`.

When demo mode is enabled, seed users can log in with password `password`,
including `writer@example.com`, `moira@example.com`, and `alex@example.com`.
Without `ELBYSODIC_DEMO_MODE=1`, production rejects those seed password hashes.
New real accounts use argon2id password hashes. A successful login upgrades
legacy Elbysodic PBKDF2 or Chirp scrypt hashes to argon2id with a compare-and-swap
write; failed logins and demo-seed hashes never trigger that write.

Post-deploy smoke for the shared Railway host:

- confirm `/health` returns `200`
- confirm logged-out `/` and `/network?q=magic` render the public realm catalog
- confirm logged-out `/studio` redirects to `/login?next=/studio`
- log in with the intended demo account policy
- open `/c/x-men-apocalypse/world/b-24-winter`
- open `/c/jurassic-park-universe/boards/paddock-twelve`
- hard-refresh both tenant-prefixed routes in a fresh browser session
- click boosted navigation between world, wanted, board, and thread routes and
  confirm the shell never swaps to an empty main area
- submit one low-risk write path, such as a membership or face switch, to prove
  session cookies and CSRF work together
- log out, then confirm replaying the old `elbysodic_session` cannot open
  `/studio`
- confirm seed media under `/elbysodic-static/seed-media/...` returns `200`
- keep the Railway service at one replica while SQLite is volume-backed

Use [docs/operations/railway-smoke.md](docs/operations/railway-smoke.md) as the
recorded runbook before sharing the URL. The production gate is still open until
that smoke includes restart persistence on the attached volume.
Record the first production run in
[docs/operations/railway-production-smoke-record.md](docs/operations/railway-production-smoke-record.md).
The current SQLite operating contract is documented in
[docs/operations/sqlite-production.md](docs/operations/sqlite-production.md).
Before creating the first real production realm, use
[docs/operations/production-bootstrap.md](docs/operations/production-bootstrap.md)
as the go/no-go checklist.
For the first controlled writer session, use
[docs/operations/invite-only-alpha.md](docs/operations/invite-only-alpha.md).

## Product Voice

Use language that fits roleplayers. Prefer face, roster, thread, scene,
plotter, wanted, claims, reserves, needs reply, waiting, caught up, and
watching when those words are more precise than generic forum jargon.
