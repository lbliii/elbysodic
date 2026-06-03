# Data Integrity Contracts

Elbysodic stores global users and community-scoped creative records. Repository
methods keep `community_id` explicit, but SQLite constraints must also prevent
impossible tenant pairings wherever the data model can express them.

## Tenant-Paired Rows

A tenant-paired row stores `community_id` and one or more foreign keys to rows
that also belong to a community. Those references must resolve in the same
community before the row is persisted.

High-risk tenant-paired rows include:

- memberships and roles
- characters and memberships
- boards, threads, posts, and public authorship
- command submissions and the membership that reserved the command
- applications and review events
- realm interaction definitions, responses, answers, and options
- wanted hooks, interests, reserves, and claims
- plotting rooms, source interests, target scenes, participants, and messages
- reactions, reads, watches, and thread participants
- notifications and sidebar counts
- user-session selected membership

## Enforcement Layers

Use all three layers:

- Schema: composite foreign keys, unique pairs, checks, or triggers.
- Repository: scoped methods that load parent rows by `community_id`.
- Services: workflow validation using resolved viewer, policy helpers, and
  explicit actor shapes.

Diagnostics are not a substitute for constraints. They are the repair and
operations surface for old data, migrations, imports, and local demo databases.
`ForumRepository.list_tenant_pair_integrity_issues()` is the shared repository
diagnostic for tenant-paired creative and workflow rows, including membership
roles, default faces, character ownership, command submissions, authorship,
claims, realm interactions, plotting rooms, reactions, thread state, and
notifications. Diagnostic rows report ids, table names, tenant ids, and
content-free relationship reasons so operators can plan repair work without
exposing private posts, room notes, application answers, or staff-only details.

## Session Selection

A persisted selected session identity must identify one active membership owned
by the session user. The selected community and selected membership cannot drift.

The preferred long-term shape is to store one selected membership and derive the
community and user. If redundant columns remain, the database must enforce the
pair with triggers or composite constraints.

## Authorship

Story-visible rows must preserve authorship:

- a post's thread, author membership, and author character belong to one
  community
- a post character belongs to the post membership
- a thread author character belongs to the thread author membership
- staff actor rows name staff membership separately from public character
  context

Wrong-face authorship is a product safety issue, not only a database bug.

## Migration Rules

Schema hardening should land in waves:

1. Add diagnostics and negative tests.
2. Repair or clear invalid existing rows in a migration.
3. Add constraints or triggers.
4. Prove fresh and upgraded schema parity.
5. Run `PRAGMA foreign_key_check` and targeted integrity checks.

Each migration should keep fresh schema and ordered migrations equivalent.
