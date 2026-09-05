# SQLite Request Lifecycle

Elbysodic uses SQLite for the current local and Railway deployment shape. The
request lifecycle must treat SQLite connection ownership as part of the tenant
and identity safety contract, not as incidental plumbing.

## Contract

- App startup may keep a root service facade for seed data, tests, CLI access,
  and app-owned shutdown.
- Filesystem-backed web requests use a request-scoped repository connection and
  close it after the response settles.
- Authenticated page branches must obtain request services through
  `get_services(request)`. Manual `get_services().for_request(request)` calls
  bypass the shared request cache and are not an accepted web entrypoint.
  Signed-out public preview fallbacks may use the root public facade after
  request identity has failed.
- `:memory:` test services may share one synchronized connection because each
  new connection would create an empty database.
- `connect()` owns SQLite pragmas: foreign keys, busy timeout, and WAL for
  filesystem databases.
- Studio Operations reads journal mode and `PRAGMA integrity_check` through the
  operations service read model so director/operator diagnostics do not drift
  into page-local SQL or ordinary member surfaces.
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

## Route Timing Capture

Use the browser and server timing channels together when investigating local
slowness:

- Start the production-like preview with `uv run poe preview-prod-devtools`.
- In the browser console, inspect `window.__elbysodicHtmxTimings` after route
  clicks. It records htmx request timing from the client side, so use it for
  perceived navigation delay and latest-click-wins checks.
- Inspect the response `Server-Timing` header for server-side route duration.
  Use this when the browser timing is high and you need to separate template or
  SQLite work from client-side rendering and network overhead.
- Production JSON access logs already carry Pounce's end-to-end
  `duration_ms`. The app-owned timing middleware remains intentionally narrower:
  it supplies the response `Server-Timing`/`X-Elbysodic-Route-Time-Ms` headers
  used by browser QA and the local diagnostic harness. It does not emit a
  second request log or replace the framework access-log clock.
- Reproduce suspicious fanout with the query-budget tests in
  `tests/test_forum_slice.py`. Budgets are the regression contract; browser and
  `Server-Timing` captures explain where to look before changing them.
