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
- For staging, set `ELBYSODIC_DB_PATH=/app/var/elbysodic.sqlite3` alongside the
  `/app/var` volume mount so seed and app startup always agree on the
  persistent database file.
- Seed demo data intentionally with `elbysodic seed-demo`; app startup creates
  the schema but should not be treated as a demo reset.

## Shutdown Contract

`elbysodic serve` and `elbysodic dev preview` own the app service lifecycle for
the process they start. On normal server exit, Elbysodic closes the shared
SQLite connection and best-effort checkpoints WAL data for filesystem-backed
databases before releasing the connection.

Supported clean stop paths are:

- `SIGTERM` from a process manager or deployment platform.
- `SIGINT`, including local `Ctrl-C`.
- `SIGHUP` for local debug-mode `serve` and `dev preview` processes.

Abrupt filesystem removal is outside that contract. Do not delete, archive, or
move an isolated worktree while an Elbysodic server from that checkout is still
running; the process can still hold its port and SQLite handles while page and
static assets disappear from disk. Stop the process first, verify the port is
free, then archive or remove the checkout.

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

The seed command prints the database path it touched. Treat
`seeded /app/var/elbysodic.sqlite3` as the expected staging proof. Treat
`seeded var/elbysodic.sqlite3` as a warning that the app wrote to the
container filesystem instead of the Railway Volume.

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

## Backup/Restore Drill Record

Latest known staging drill:

```text
SQLite backup/restore:
- Date: 2026-05-12
- Environment: Railway staging
- Source path: /app/var/elbysodic.sqlite3 with matching -wal and -shm files
- Backup path: /app/var/elbysodic-smoke-backup-2026-05-12.sqlite3
- Restore-check path: /private/tmp/elbysodic-smoke-restore-check.sqlite3
- Integrity check: ok
- Core counts: users 7, communities 5, threads 16, posts 21
- Service readback: X-Men Apocalypse and HP Universe resolved from the restored copy
- Result: staging SQLite file, WAL, and SHM can be copied, integrity-checked,
  and opened by Elbysodic services for readback
```

Do not treat this as a substitute for a real maintenance-window backup plan.
The drill proves the current volume-backed staging database can be copied and
read back; before real writer sessions, prefer either a paused service window or
a scripted SQLite online backup that avoids WAL-copy timing risk.
