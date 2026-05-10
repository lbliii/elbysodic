# SQLite Production-Like Operations

Elbysodic can run a production-like Railway demo on SQLite when the deployment
is deliberately constrained. This is the operating contract until the project
chooses a different persistence backend.

## Runtime Contract

- Run exactly one web replica against the SQLite file.
- Store the database on an attached Railway Volume, not the ephemeral app
  filesystem.
- Prefer the default Railway path:
  `$RAILWAY_VOLUME_MOUNT_PATH/elbysodic.sqlite3`.
- Set `ELBYSODIC_DB_PATH` only when the deployment needs a different attached
  volume path.
- Seed demo data intentionally with `elbysodic seed-demo`; app startup creates
  the schema but should not be treated as a demo reset.

## Persistence Checks

Before sharing a URL, prove these survive restart or redeploy:

- writer posts
- thread read/watch state
- membership and active face selection
- director-edited boards
- director-edited world materials
- application/review room state
- wanted interest and plotting room state

The Railway smoke runbook records this as restart persistence. If any of these
rows reset after restart, stop the launch and inspect the volume mount path,
replica count, and seed command history.

## Backup And Export Expectation

For the first production-like community demos, take a volume/database snapshot
before:

- manual demo seed refreshes
- schema migrations
- public test sessions with real writers
- long-running director editing sessions

Keep the backup process simple and explicit. A copied SQLite file is acceptable
when the service is stopped or quiescent; a live backup command can replace
that once the deployment runbook grows a maintenance window.
