# Railway Production Smoke Record

Use this file for the first production Railway smoke run. Do not mark the
production gate closed until every required item below has a dated result.

## Status

Production smoke has not been run yet.

## Attempt Log

```text
Railway production smoke:
- Date: 2026-05-19
- Operator: Codex local workspace
- URL: not tested
- Deployment: not tested
- Commit: 9d8542a3
- Railway project/service/environment: unavailable locally
- Volume path: not tested
- Database path: not tested
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
  path, current schema version, migration ledger, and launch status.

## First Run Notes

- Do not paste Railway variable values, session cookies, password reset links,
  or generated passwords into this file.
- If any item fails, keep the status as failed/incomplete and link the fix
  commit or follow-up plan.
- If the run uses demo credentials, explicitly record `Demo mode: on` and do
  not reuse that record to approve a non-demo production launch.
