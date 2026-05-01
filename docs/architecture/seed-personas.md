# Seed Personas

Seed personas are the browser QA layer for Elbysodic's identity model. They are
not product accounts, fixtures for every test, or a replacement for the real
authorization checks. They are stable named entry points for manually testing
global account, community membership, role, and active-face combinations.

Use `src/elbysodic/db/seed.py` as the source of truth. The `SEED_PERSONAS`
catalog gives each persona a semantic key, account email, community,
membership username, default face, default route, and QA purpose.

Tests should use `resolve_seed_persona(repo, "<key>")` when they need a seeded
identity by purpose instead of hard-coding a username and hoping the role is
obvious.

## Matrix

| Key | Account | Community | Membership | Role | Face | QA Purpose |
| --- | --- | --- | --- | --- | --- | --- |
| `xmen_writer` | `writer@example.com` | X-Men Apocalypse | `starlane` | Member | Rogue | ordinary writer, accepted faces, active-face queue, scene posting |
| `xmen_staff` | `moira@example.com` | X-Men Apocalypse | `moira` | Staff | Moira MacTaggert | Studio, applications, claims, private production rooms |
| `xmen_mod` | `alex@example.com` | X-Men Apocalypse | `alex` | Moderator | Cyclops | thread lifecycle and moderation controls |
| `xmen_partner` | `charlie@example.com` | X-Men Apocalypse | `charlie` | Member | Charles Xavier | wanted, plotter, plotting-room, and notification counterparty checks |
| `xmen_applicant` | `mira@example.com` | X-Men Apocalypse | `mira` | Member | Kitty Pryde | submitted application and writer-side revision workflow |
| `xmen_outsider` | `simon@example.com` | X-Men Apocalypse | `simon` | Member | Bolivar Trask | outsider, private-room denial, and notification visibility checks |
| `xmen_inactive` | `inactive@example.com` | X-Men Apocalypse | `sleepingstar` | Member | Sleeping Star | inactive membership denial and recovery checks |
| `hp_director` | `writer@example.com` | HP Universe | `starlane` | Director | Rowan Ash | same account with staff power in another community |
| `jp_director` | `writer@example.com` | Jurassic Park Universe | `starlane` | Director | Dr. Lena Marquez | visual/theme and director controls in another genre |
| `nyc_writer` | `writer@example.com` | RL NYC | `starlane` | Member | Lena Park | same account without staff power in another community |
| `smalltown_writer` | `writer@example.com` | RL Small Town | `starlane` | Member | June Calloway | low-stakes ensemble writer checks |

## Browser QA

When development tools are enabled, `/dev/personas` lists these personas and
can switch the current local identity. The page must remain development-only:
production or disabled dev-tools mode should return 404.

Login sessions use the same catalog indirectly: seeded accounts currently use
the local password `password`, and the request resolver still resolves staff
power through the selected community membership and role.

## Boundaries

- Staff power is never global. `writer@example.com` is a Director in HP and
  Jurassic Park, but only a Member in X-Men, RL NYC, and RL Small Town.
- Characters remain community-local and membership-owned.
- Inactive personas should be visible for QA, but not switchable into an active
  viewer.
- Dev persona switching is a local QA shortcut. Real flows should use login
  sessions and normal membership resolution.
