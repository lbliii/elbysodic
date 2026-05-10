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

The checked-in Railway config requires `/app/var` and one replica for all
environments. The `staging` environment also runs the idempotent demo seed
command before starting the app so seeded demo accounts and realms are present.
Production does not auto-seed on startup; seed production intentionally only
when the deployment is being used as a seeded demo.

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
