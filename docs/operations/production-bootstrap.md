# Production Bootstrap Go/No-Go

Use this checklist before running `elbysodic bootstrap-first-realm` against a
real production Railway database. Staging smoke proves deploy mechanics;
production bootstrap creates the first real director identity and realm.

## Go Criteria

- The Railway service is running one replica.
- A Railway Volume is mounted and the app database path resolves to that
  volume, usually `/app/var/elbysodic.sqlite3`.
- `ELBYSODIC_ENV=production` or `staging` is intentional for the target.
- `ELBYSODIC_SECRET_KEY` is present and at least 32 characters.
- Demo mode is off for production unless the session is explicitly a demo.
- The redacted auth trust posture reports the expected production, demo-mode,
  secret-key minimum, session cookie, and session-required settings.
- A fresh backup exists, or the database is confirmed empty.
- Studio Operations shows the expected environment, database path, journal
  mode, integrity check, schema version, migration ledger, realm count, and
  launch status.
- The first realm name, slug, director email, director username, and director
  display name have been reviewed for typos.

## No-Go Conditions

- The seed command or Studio Operations points at a non-volume path such as
  `var/elbysodic.sqlite3`.
- Studio Operations reports a filesystem SQLite journal mode other than `wal`
  or an integrity check other than `ok`.
- More than one Railway replica is active while SQLite is the backing store.
- The migration ledger is behind the app schema version.
- The realm slug is uncertain or conflicts with planned host routing.
- There is no rollback path for a mistaken director email, slug, or empty realm.
- Secrets, variable values, or generated passwords would be pasted into a public
  note or PR.

## Execution Record

Record values, not secrets:

```text
Production bootstrap:
- Date:
- Operator:
- Railway project/service/environment:
- Deployment:
- App URL:
- Volume path:
- Database path:
- Journal mode:
- Integrity check:
- Schema version:
- Migration ledger:
- Auth trust posture:
- Replica count:
- Existing realm count before:
- Realm name:
- Realm slug:
- Director email:
- Director username:
- Launch status after:
- Backup path or empty-DB proof:
- Result:
```

## Current Gate Record

```text
Production bootstrap:
- Date: 2026-05-19
- Operator: Codex local workspace
- Railway project/service/environment: intuitive-friendship / elbysodic / staging
- Deployment: 8ba55b0f-996e-4059-8592-642273696787
- App URL: https://elbysodic-staging.up.railway.app
- Volume path: /app/var
- Database path: not inspected from app runtime in this run
- Journal mode: not inspected from app runtime in this run
- Integrity check: not inspected from app runtime in this run
- Schema version: not inspected from app runtime in this run
- Migration ledger: not inspected from app runtime in this run
- Replica count: not inspected from app runtime in this run
- Existing realm count before: not inspected from app runtime in this run
- Realm name: not executed
- Realm slug: not executed
- Director email: not executed
- Director username: not executed
- Launch status after: not executed
- Backup path or empty-DB proof: not inspected
- Result: no-go for production bootstrap. The linked Railway context is staging,
  not an approved production target, and the app-level inspection fields still
  need a signed-in Studio Operations check before any production bootstrap.
```

## Post-Bootstrap Proof

After the command succeeds:

1. Visit `/health`.
2. Log in as the director.
3. Open `/studio/operations` and verify the hosted inspection panel.
4. Open `/studio/launch` and confirm launch status is `backstage`.
5. Create or verify the minimum opening packet.
6. Set launch status to `invite-only` only after the checklist is ready.
7. Create one writer invitation, copy the link, then revoke it if it was only a
   proof link.
8. Restart the Railway service and confirm the realm, launch status, and
   director login persist.

Do not set `public-preview` until the public catalog copy, published premise,
public scene hub, and signed-out privacy smoke all pass.
