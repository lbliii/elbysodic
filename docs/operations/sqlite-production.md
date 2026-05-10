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

`railway.json` keeps production on normal startup and constrains the service to
one replica with the `/app/var` volume mount. Its `staging` override runs
`elbysodic seed-demo --db-path "$RAILWAY_VOLUME_MOUNT_PATH/elbysodic.sqlite3"`
before startup. That staging seed is idempotent and intended for demo QA; do
not mirror that auto-seed behavior into production once real writer data exists.

Use `elbysodic bootstrap-admin` for the first production director account. It
creates or reuses the target community, creates or upgrades the admin role,
creates or reuses the user, and creates or promotes the community membership.
It does not create characters or demo content.

```bash
elbysodic bootstrap-admin \
  --db-path "$RAILWAY_VOLUME_MOUNT_PATH/elbysodic.sqlite3" \
  --email you@example.com \
  --username llane \
  --display-name "Your Name" \
  --community-name "Elbysodic"
```

Rerunning the command is idempotent. Existing user passwords are preserved
unless `--reset-password` is passed.

## Railway Database Inspection

SQLite does not include a hosted admin UI. Use the Elbysodic Studio screens for
normal product administration, and use direct SQLite inspection only for
operations, support, triage, and carefully planned repair work.

For staging:

```bash
railway ssh -e staging -s <service-name>
sqlite3 "$RAILWAY_VOLUME_MOUNT_PATH/elbysodic.sqlite3"
```

For production:

```bash
railway ssh -e production -s <service-name>
sqlite3 "$RAILWAY_VOLUME_MOUNT_PATH/elbysodic.sqlite3"
```

Start with read-only triage:

```sql
.tables
.schema users
.schema communities
SELECT id, name, slug, host FROM communities ORDER BY id;
SELECT id, email, created_at FROM users ORDER BY id;
SELECT id, community_id, slug, name, is_admin FROM roles ORDER BY community_id, id;
SELECT id, community_id, user_id, username, display_name, role_id, is_active
FROM community_memberships
ORDER BY community_id, id;
SELECT id, community_id, name, slug, application_status FROM characters ORDER BY community_id, id;
```

Useful support checks:

```sql
SELECT u.email, c.name AS community, m.username, m.display_name, r.name AS role, r.is_admin
FROM community_memberships AS m
JOIN users AS u ON u.id = m.user_id
JOIN communities AS c ON c.id = m.community_id
JOIN roles AS r ON r.id = m.role_id AND r.community_id = m.community_id
ORDER BY c.name, m.username;

SELECT community_id, COUNT(*) AS boards
FROM boards
GROUP BY community_id;

SELECT community_id, COUNT(*) AS threads
FROM threads
GROUP BY community_id;

SELECT community_id, COUNT(*) AS posts
FROM posts
GROUP BY community_id;
```

Avoid manual writes during live use. If a direct write is unavoidable:

- prefer an Elbysodic CLI command, repository script, or migration over ad hoc
  SQL
- take a database or Railway volume snapshot first
- keep the service stopped or quiescent when copying the SQLite file
- write down the exact SQL or script used and the reason
- re-run the relevant smoke path before sharing the URL again

For local GUI inspection, copy a backup of the SQLite file out of Railway first
and open the copy in a SQLite client such as DB Browser for SQLite, TablePlus,
Beekeeper Studio, or Datasette. Do not connect GUI tools directly to the live
volume.

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
