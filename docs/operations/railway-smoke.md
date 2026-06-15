# Railway Smoke Runbook

Use this runbook before sharing a production Railway URL with writers or
directors. A local test can prove the route contract, but this run records the
real host, volume, cookie, static media, and restart posture.

## Required Posture

- `ELBYSODIC_ENV=production`
- `ELBYSODIC_SECRET_KEY` is set to a random value of at least 32 characters.
- `ELBYSODIC_ALLOWED_HOSTS` includes the Railway host and any custom host.
- `ELBYSODIC_DEMO_MODE=1` only when seeded demo credentials should work.
- A Railway Volume is attached and mounted at `/app/var`, or
  `ELBYSODIC_DB_PATH` points at an attached volume path.
- The service runs one replica while SQLite is the production-like store.

## Managing Staging

Staging is the rehearsal environment for Railway deploys, seeded demo data,
volume persistence, login/session behavior, and tenant-prefixed realm routes.
Keep it separated from production by environment, secret, volume, and database
path.

Current staging posture:

- URL: `https://elbysodic-staging.up.railway.app`
- Railway project: `intuitive-friendship`
- Railway service: `elbysodic`
- Railway environment: `staging`
- SQLite volume mount: `/app/var`
- SQLite database path: `/app/var/elbysodic.sqlite3`
- Demo credentials: enabled with `ELBYSODIC_DEMO_MODE=1`
- Seed command: `elbysodic seed-demo`

Required staging variables:

- `ELBYSODIC_ENV=staging`
- `ELBYSODIC_DEMO_MODE=1`
- `ELBYSODIC_AUTO_SEED_DEMO=1`
- `ELBYSODIC_SECRET_KEY=<staging-only random secret>`
- `ELBYSODIC_DB_PATH=/app/var/elbysodic.sqlite3`

Use a staging-only Railway Volume mounted at `/app/var`. Attaching the volume is
not enough by itself; confirm the running app writes SQLite to
`/app/var/elbysodic.sqlite3`, not `var/elbysodic.sqlite3` inside the disposable
container filesystem.

Useful staging commands:

```bash
railway link --environment staging --service elbysodic
railway volume list --json
railway variable list --service elbysodic --environment staging --kv
railway ssh --service elbysodic elbysodic seed-demo
railway service redeploy --service elbysodic --yes
railway service restart --service elbysodic --yes
```

Do not paste or publish `railway variable list --kv` output; it includes secret
values. When recording a run, list variable names only.

After changing volume or DB path settings, redeploy staging before seeding. A
plain restart may keep the previous runtime environment. The seed command should
report:

```text
seeded /app/var/elbysodic.sqlite3
```

If it reports `seeded var/elbysodic.sqlite3`, the app is still writing to the
container filesystem and persistence is not proven.

With `ELBYSODIC_AUTO_SEED_DEMO=1`, staging also runs the idempotent demo seed
path during app startup. The flag is accepted only when
`ELBYSODIC_ENV=staging` and `ELBYSODIC_DEMO_MODE=1`; using it outside staging
is a configuration error. Keep the manual `railway ssh --service elbysodic
elbysodic seed-demo` step available for immediate repair and for proving the
database path printed by the seed command.

## Empty Catalog Diagnostics

When `/network` renders "No public-ready realms are open yet.", treat the page
as a successful public request with an empty catalog, not as proof that Railway
is healthy. Open Studio Operations as a director and inspect the read-only
Runtime and persistence panel:

- `Database path`: should match `ELBYSODIC_DB_PATH`, normally
  `/app/var/elbysodic.sqlite3` on staging.
- `Database directory` and `Database file`: both should be present. A missing
  directory points to a wrong volume mount or path; a missing file points to an
  uninitialized database path.
- `Volume mount`: should show the configured Railway mount path as present when
  `RAILWAY_VOLUME_MOUNT_PATH` is set.
- `Realms`: `0` means Railway is using an empty schema-only database or the
  wrong path.
- `Public-ready realms`: `0` with nonzero realms means the database has tenant
  roots, but no realm is both `public-preview` and ready for catalog discovery.
- `Seed demo mode`: disabled means seeded demo passwords are not available; on
  staging, confirm `ELBYSODIC_DEMO_MODE=1`.
- `Auto seed demo`: disabled on staging means an empty volume will not self-heal
  on app startup; confirm `ELBYSODIC_AUTO_SEED_DEMO=1` before relying on
  automatic repair.
- `Schema` and `Migration ledger`: both should equal the current schema version.
  A mismatch means the database is not at the expected migration state.

Common diagnoses:

- Empty schema-only DB: `Realms=0`, schema and migration ledger are current,
  and the database file is present. Run the staging seed command against the
  displayed database path.
- Wrong volume path: `Database path` is `var/elbysodic.sqlite3` or another
  container-local path instead of `/app/var/elbysodic.sqlite3`, or the displayed
  directory/file is missing. Fix Railway variables or the mounted volume path,
  then redeploy before seeding.
- Unseeded volume: database directory and file are present, schema is current,
  but `Realms=0`. Run `elbysodic seed-demo` for staging or bootstrap the first
  realm for production.
- Real no-public-realms launch state: `Realms>0` and `Public-ready realms=0`.
  Use Studio Launch and public preview readiness checks instead of reseeding.

Staging smoke should include:

- `GET /health` returns `200`.
- `GET /network` renders seeded realms such as `Jurassic Park Universe`,
  `RL NYC`, and `X-Men Apocalypse`.
- At least one seed media URL, such as
  `/elbysodic-static/seed-media/xmen-hero.svg`, returns `200`.
- A restart preserves database row counts and rendered seeded realms.
- A copied staging database reports `restore-check ok` through the read-only
  restore-check service before any destructive restore rehearsal. Use the
  operator contract in `docs/operations/sqlite-production.md` for accepted
  inputs, redacted output, success criteria, and failure handling.
- Demo login works for the intended seed account policy.

Known follow-up: `HEAD` requests to some app and static routes can currently
produce a Railway `502` through the Pounce/Chirp response path. Use `GET` for
staging smoke until that server bug is fixed, and keep the bug visible in PR or
plan notes.

## Smoke Script

Record the date, Railway deployment ID, public URL, and tester account used.

1. Visit `/health` and confirm `200`.
2. Visit `/network?q=magic` while signed out and confirm only public catalog
   language appears. No writer username, active face, unread count, staff note,
   or identity menu should render.
3. Log in with the intended demo or invite account.
4. Enter `/c/x-men-apocalypse` and confirm the realm, membership label, and
   active face are correct.
5. Open a board and thread, then confirm composer controls show the intended
   posting face.
6. Switch to another membership through the rendered identity control and
   confirm the destination keeps the `/c/{community_slug}` prefix.
7. Open wanted, applications, plotting, notifications, and Studio surfaces as
   the permitted viewer.
8. Complete one CSRF-protected write, such as switching membership, updating a
   draft, or posting in a safe test scene.
9. Open at least one seed media URL from the rendered page and confirm it
   returns successfully.
10. Log out and confirm protected routes redirect to `/login`.
11. Restart or redeploy the service, then confirm the write from step 8 and any
    director-edited board/world data still exist.

## Pass Record

Paste a short record into the relevant PR or plan update:

```text
Railway smoke:
- Date:
- URL:
- Deployment:
- Volume path:
- Replica count:
- Demo mode:
- Account:
- Write tested:
- Restart persistence:
- Seed media:
- Result:
```

Do not mark the production gate closed until the smoke record includes restart
persistence and the one-replica SQLite posture.
Use `docs/operations/railway-production-smoke-record.md` for the first
production run so staging proof and production proof stay distinct.

## Staging Record

Latest known staging smoke:

```text
Railway smoke:
- Date: 2026-06-15
- URL: https://elbysodic-staging.up.railway.app
- Deployment: ad3dcc24-06fc-4211-a5f1-f780c78c94dc
- Commit: b6b4f5919a80cc6458e67aeb4b1309682dd89d05
- Railway project: intuitive-friendship
- Railway service: elbysodic
- Railway environment: staging
- Volume path: /app/var
- Volume: elbysodic-volume, READY, about 59 MB used of 500 MB
- Database path: /app/var/elbysodic.sqlite3
- Replica count: 1
- Demo mode: on for staging demo credentials
- Variable proof: do not paste `railway variable list` output because Railway
  CLI JSON and KV modes include raw values. Runtime evidence confirmed staging
  posture: demo login worked, auto-seed ran only on staging/demo mode, and the
  seed command printed the configured /app/var database path.
- Account: seeded writer account class
- Auto seed: startup log reported `auto-seeded staging demo data at /app/var/elbysodic.sqlite3`
- Manual seed: `elbysodic seed-demo` reported `seeded /app/var/elbysodic.sqlite3`
- Public GETs: /health, /, /network, /network?q=magic,
  /c/x-men-apocalypse, and /elbysodic-static/seed-media/xmen-hero.svg
  returned 200
- Authenticated GETs: /c/x-men-apocalypse,
  /c/x-men-apocalypse/boards/danger-room/threads/sentinel-drill,
  /c/x-men-apocalypse/wanted, /c/x-men-apocalypse/applications,
  /c/x-men-apocalypse/plotting, /c/x-men-apocalypse/notifications, and
  /c/x-men-apocalypse/studio returned 200
- Write tested: CSRF-protected identity switch from X-Men Apocalypse member
  Rogue to HP Universe director Rowan Ash returned 302 to /c/hp-universe
- Restart persistence: passed after Railway service restart. Logs showed the
  volume mounted and auto-seed ran at /app/var/elbysodic.sqlite3; the same
  authenticated session then rendered HP Universe with Rowan Ash, and public
  /network still rendered HP Universe, Jurassic Park Universe, RL NYC, and
  X-Men Apocalypse.
- Logout boundary: /logout returned 302 to /login, and protected /studio
  redirected to /login?next=/studio after logout
- Seed media: passed after restart
- Result: staging is volume-backed, one-replica, seeded, demo-login capable,
  and restart-persistent for the tested identity-switch write and seeded rows

Railway staging seed repair:
- Date: 2026-06-13
- URL: https://elbysodic-staging.up.railway.app
- Deployment: 598b31a9-b9cf-4253-9b25-09fc558df7bb
- Commit: c165e0d469650a3487cb9f620130175ce8bc84e6
- Volume path: /app/var
- Database path: /app/var/elbysodic.sqlite3
- Demo mode: on
- Auto seed: ELBYSODIC_AUTO_SEED_DEMO=1 set for future staging deploys
- Manual seed: `elbysodic seed-demo` reported `seeded /app/var/elbysodic.sqlite3`
- Public GETs: /health, /network, /c/x-men-apocalypse, and
  /elbysodic-static/seed-media/xmen-hero.svg returned 200
- Restart persistence: not rerun in this repair pass
- Result: staging seed data is restored on the volume-backed database; future
  staging app startups can self-heal missing seed rows once this code is
  deployed.

Railway smoke:
- Date: 2026-05-12
- URL: https://elbysodic-staging.up.railway.app
- Deployment: 13a712ad-da07-4d8f-8617-078a1ca4add6
- Commit: f08eae8ea1ec79e7830b17bf1317aec2fc092996
- Volume path: /app/var
- Replica count: 1
- Demo mode: on
- Account: writer@example.com demo account
- Public GETs: /health, /network?q=magic, /c/x-men-apocalypse, and
  /elbysodic-static/seed-media/xmen-hero.svg returned 200
- Authenticated GETs: /c/x-men-apocalypse,
  /c/x-men-apocalypse/boards/danger-room/threads/sentinel-drill,
  /c/x-men-apocalypse/applications, and /c/x-men-apocalypse/studio returned 200
- Write tested: CSRF-protected identity switch from X-Men Apocalypse member
  Rogue to HP Universe director Rowan Ash
- Restart persistence: passed after Railway service restart; the switched
  identity still rendered HP Universe with Rowan Ash
- Logout boundary: protected Studio route redirected to login after logout
- Seed media: passed
- Result: staging is volume-backed, one-replica, demo-login capable, and
  restart-persistent for the tested write
```
