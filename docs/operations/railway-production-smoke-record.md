# Railway Production Smoke Record

Use this file for the first production Railway smoke run. Do not mark the
production gate closed until every required item below has a dated result.

## Status

Production smoke has not been run yet.

## Attempt Log

```text
Railway staging smoke:
- Date: 2026-05-19
- Operator: Codex local workspace
- URL: https://elbysodic-staging.up.railway.app
- Deployment: 8ba55b0f-996e-4059-8592-642273696787
- Commit: e262ccde
- Railway project/service/environment: intuitive-friendship / elbysodic / staging
- Volume path: /app/var, Railway status reported elbysodic-volume mounted
- Database path: not inspected from app runtime in this run
- Journal mode: not inspected from app runtime in this run
- Integrity check: not inspected from app runtime in this run
- Replica count: not inspected from app runtime in this run
- Demo mode: not inspected from app runtime in this run
- Public GETs: `/health` 200, `/` 200, `/network` 200
- Tenant-prefixed public realm: `/c/afterlight-accord` 404 and
  `/c/x-men-apocalypse` 404 in the linked staging database
- Static media: `/elbysodic-static/brand/elbysodic-mark.svg` 200
- HEAD behavior: `curl -I /health` and `curl -I /network` returned Railway-edge
  502 because the app attempted to send a body with a 405 HEAD response.
- Result: incomplete staging smoke. Public product routes and static media
  respond to GET, but seeded tenant-preview smoke cannot pass against this
  staging database and HEAD handling needs follow-up before load balancer or
  monitor HEAD probes can be trusted.

Railway production smoke:
- Date: 2026-05-19
- Operator: Codex local workspace
- URL: not tested
- Deployment: not tested
- Commit: 9d8542a3
- Railway project/service/environment: unavailable locally
- Volume path: not tested
- Database path: not tested
- Journal mode: not tested
- Integrity check: not tested
- Replica count: not tested
- Demo mode: not tested
- Account tested: not tested
- Public GETs: not tested
- Authenticated GETs: not tested
- Tenant-prefixed hard refresh: not tested
- CSRF-protected write tested: not tested
- Logout boundary: not tested
- Seed media: not tested
- Restart persistence: not tested
- Result: incomplete. Railway CLI is not installed in this workspace, so the
  real host, volume, static media, cookie, and restart checks still require a
  Railway-connected operator or environment.
```

## Required Record

```text
Railway production smoke:
- Date:
- Operator:
- URL:
- Deployment:
- Commit:
- Railway project/service/environment:
- Volume path:
- Database path:
- Journal mode:
- Integrity check:
- Replica count:
- Demo mode:
- Account tested:
- Public GETs:
- Authenticated GETs:
- Tenant-prefixed hard refresh:
- CSRF-protected write tested:
- Logout boundary:
- Seed media:
- Restart persistence:
- Result:
```

## Required Pass Criteria

- `/health` returns `200`.
- `/`, `/network`, `/search`, and a tenant-prefixed public realm preview render
  without staff, private, active-face, or unread-count leakage while signed out.
- Login works only for the intended production account policy.
- Member and staff views resolve from `elbysodic_session`, not development
  identity headers or cookies.
- A tenant-prefixed board/thread route survives hard refresh on the shared
  Railway host.
- One CSRF-protected write succeeds, then remains visible after restart.
- Logout revokes the session; replaying the stale session cannot open Studio.
- Seed media under `/elbysodic-static/seed-media/...` returns `200`.
- Studio Operations shows one replica, the expected volume-backed database
  path, WAL journal mode, `ok` integrity check, current schema version,
  migration ledger, and launch status.

## First Run Notes

- Do not paste Railway variable values, session cookies, password reset links,
  or generated passwords into this file.
- If any item fails, keep the status as failed/incomplete and link the fix
  commit or follow-up plan.
- If the run uses demo credentials, explicitly record `Demo mode: on` and do
  not reuse that record to approve a non-demo production launch.
