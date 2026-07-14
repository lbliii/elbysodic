# Railway Production Smoke Record

Use this file for the first production Railway smoke run. Do not mark the
production gate closed until every required item below has a dated result.

## Status

Production smoke has not been run yet.

## Attempt Log

```text
Railway staging upgrade smoke:
- Date: 2026-07-14
- Operator: Codex local workspace
- URL: https://elbysodic-staging.up.railway.app
- Deployment: 7fd9bb62-a214-438e-baf8-b0ea3952d776 (SUCCESS)
- Commit: 1f1d5f84c80a7c79f82daaa985327ceae3e79b9e, deployed from the
  verified local branch through Railway CLI
- Railway project/service/environment: Elbysodic / elbysodic / staging
- Deploy posture: one replica, /ready healthcheck, 5-second overlap,
  15-second drain, and /app/var volume mount
- Local Pounce check: pounce 0.9.1; app import, config validation, and
  127.0.0.1:8765 port availability all passed
- Staging runtime: startup log reported Pounce 0.9.1, Python 3.14.2, GIL
  enabled, and process-worker mode. Do not treat this run as free-threaded
  runtime proof.
- Probe smoke: HEAD /health, /livez, /ready, and /readyz had correct bodyless
  semantics; GET /ready and /readyz passed. /_pounce/info redirected to the
  app login boundary, so no public build-id or gil_enabled assertion was made.
- Seed/login smoke: the public catalog rendered Jurassic Park Universe,
  RL NYC, and X-Men Apocalypse; X-Men seed media returned 200; a seeded writer
  login resolved the intended X-Men Apocalypse membership and face. No
  credentials, cookies, or account identifiers beyond the seed class are
  recorded here.
- Browser QA: browser-qa-deep, rapid-click-qa, latest-click-wins-qa, and
  writer-activation-qa passed. The accepted visual fix stacks the Director
  Studio hero before tablet shell columns collide; no privacy or service
  contract changed.
- Password rehash evidence: aggregate-only SSH inspection found 11 demo-seed
  hashes and zero scrypt or argon2id hashes. A scrypt-to-argon2 staging login
  is therefore not executable against the current seed corpus. Elbysodic #273
  owns application integration and a safe legacy fixture; upstream Chirp #751
  owns the verify_and_upgrade opt-in/documentation mismatch.
- Result: staging deploy, runtime, public probes, and visual/interaction QA
  passed. The password-rehash acceptance criterion remains blocked on #273
  and lbliii/chirp#751; production smoke remains unrun.

Chirp/Pounce 0.8 production-check adoption:
- Date: 2026-06-15
- Operator: Codex local workspace
- Commit: b729c599
- Local app check:
  `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check(warnings_as_errors=True)"`
  passed with 52 routes, 283 templates, Chirp-UI 0.9, and no warnings.
- Local Pounce 0.8 check:
  `.venv/bin/pounce check --app elbysodic.web:create_app --host 127.0.0.1 --port 8765 --format plain`
  passed: app import ok, config validation valid, and local port
  `127.0.0.1:8765` available.
- Live Railway Pounce check: not run. This still requires a
  Railway-connected operator to run the same check in the target service
  environment and record the target deployment, host, replica count, volume
  path, database path, and one-replica SQLite posture.
- Trusted proxy / forwarded-hop posture: deferred until the live Railway
  topology is inspected. Do not set `trusted_proxies` or forwarded-hop
  overrides from local assumptions.
- Request body / upload / static streaming limits: no runtime override adopted
  in this pass. Keep Chirp 0.8 defaults until an upload/media workflow or
  Railway memory budget requires explicit product limits.
- Result: local framework preflight is adopted; live Railway execution remains
  an operator task inside the production smoke, not evidence that production
  itself has passed.

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
