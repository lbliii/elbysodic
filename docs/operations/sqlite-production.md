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
- Demo seeding is idempotent for interrupted local/staging setup. If a seed run
  is stopped partway through, rerun `elbysodic seed-demo` or
  `elbysodic dev preview` against the same database to repair the missing demo
  rows before using the realm.

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

Studio Operations exposes the runtime inspection only to members who can manage
the realm. Use it to confirm the app is pointed at the expected database file,
the SQLite journal mode, the integrity check result, schema/user version,
migration ledger, realm count, and launch status. The journal mode should be
`wal` for filesystem-backed Railway and local production-like databases, and
the integrity check should report `ok`.

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

For local and staging-like developer workflows, use the Milo-backed helpers:

```bash
elbysodic dev db checkpoint --db-path /app/var/elbysodic.sqlite3
elbysodic dev db backup --db-path /app/var/elbysodic.sqlite3 \
  --output /app/var/elbysodic-backup.sqlite3
```

`checkpoint` performs `PRAGMA wal_checkpoint(TRUNCATE)` against the configured
file. `backup` uses SQLite's online backup API and verifies
`PRAGMA integrity_check` on the copied database before reporting success. It
will not overwrite an existing backup unless `--overwrite` is passed.

After a restore, open the restored file with Elbysodic services or Studio
Operations and verify service readback for the realm plus the same `wal` journal
mode, `ok` integrity check, schema version, migration ledger, and realm count
expected for the source environment. Do not paste secrets, session cookies,
reset links, or raw credentials into the drill record.

For a copied candidate database, run the read-only restore-check service before
any destructive restore step:

```bash
uv run python -c "from pathlib import Path; from elbysodic.services.operations import format_restore_check_report, restore_check_database; print(format_restore_check_report(restore_check_database(Path('/app/var/elbysodic-backup.sqlite3'))))"
```

The restore-check opens the file read-only, runs `PRAGMA integrity_check`,
`PRAGMA foreign_key_check`, schema and migration version checks, core row
counts, and service readback for communities, memberships, boards/materials,
threads/posts, sessions, and workflow rows. The formatted report is redacted:
record counts and statuses only, not emails, token hashes, session tokens,
private notes, post bodies, application answers, or credentials.

For tenant-boundary incidents, migration rehearsals, imported data, or
pre-launch checks, use the read-only tenant integrity audit service before any
manual repair. The service groups findings by community and severity, names the
affected table/domain/row id, and reports content-free reasons and remediation
hints. Director-scoped reads are limited to the current realm; the general
operator report is still a backend service contract, not an approved public CLI
or route. Do not treat the audit as a repair command: fix or remove invalid
rows through a reviewed migration or narrowly scoped repository repair plan.

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
