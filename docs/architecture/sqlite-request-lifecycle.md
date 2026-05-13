# SQLite Request Lifecycle

Elbysodic uses SQLite for the current local and Railway deployment shape. The
request lifecycle must treat SQLite connection ownership as part of the tenant
and identity safety contract, not as incidental plumbing.

## Contract

- App startup may keep a root service facade for seed data, tests, CLI access,
  and app-owned shutdown.
- Filesystem-backed web requests use a request-scoped repository connection and
  close it after the response settles.
- `:memory:` test services may share one synchronized connection because each
  new connection would create an empty database.
- `connect()` owns SQLite pragmas: foreign keys, busy timeout, and WAL for
  filesystem databases.
- Repository list/read methods must not perform incidental writes or commits.
  Defaults and reconciliation belong to schema creation, community creation,
  migrations, seed/bootstrap, or explicit maintenance workflows.
- Query/read-model batching must keep `community_id` explicit and leave policy,
  membership posture, active face selection, and PBP queue vocabulary in
  services.

## Free-Threading Note

Local development uses Python 3.14t in this workspace. Without the GIL,
unsynchronized shared `sqlite3.Connection` access can fail under rapid
navigation even when individual queries are valid. The app therefore avoids
using `check_same_thread=False` as a concurrency strategy. It is only a
compatibility setting for connections that are otherwise scoped or synchronized.

## Proof

- Concurrent rendered GET tests cover rapid htmx-style navigation against a
  file-backed database.
- Read-only GET tests trace SQL and fail if normal navigation performs writes.
- Query-budget tests should be added for shell navigation, board thread lists,
  writer queues, and network catalog read models as those surfaces move to
  batched APIs.

## Query Budgets

Query budgets are route-specific guardrails, not performance targets. They
should start from measured local baselines, include enough slack for harmless
template or seed movement, and ratchet down only after a batch read API lands.

Budgets should protect two contracts:

- warm rendered routes do not reintroduce accidental per-board, per-thread, or
  per-face query fanout after batching
- performance work preserves tenant, membership, role, active-face, and
  publication boundaries in the service read model

Scale fixtures should be added when a surface has a true batch read contract.
Those fixtures should seed multiple communities, boards, faces, scenes, claims,
reserves, wanted hooks, private rows, and staff rows, then assert query growth is
bounded against the number of rendered cards.
