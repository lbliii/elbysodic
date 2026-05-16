# Seed Personas

Seed personas are the browser QA layer for Elbysodic's identity model. They are
not product accounts, fixtures for every test, or a replacement for the real
authorization checks. They are stable named entry points for manually testing
global account, community membership, role, and active-face combinations.

Use `src/elbysodic/db/seed.py` as the source of truth. The `SEED_PERSONAS`
catalog gives each persona a semantic key, account email, community,
membership username, default face, default route, and QA purpose.

The public demo posture is shifting toward original premise communities. The
literal-IP coded personas remain compatibility fixtures for older route,
identity, and privacy tests; new discovery and seed-depth checks should prefer
the original-premise personas below.

Original-premise communities also seed four shared ordinary writer accounts in
addition to `starlane`: `juniper.gray@example.com`, `miles.north@example.com`,
`cass.marlow@example.com`, and `lena.wren@example.com`. Each original-premise
realm has a `member` role for these writers, and its eight accepted faces are
distributed across those memberships plus the `starlane` director membership.
These accounts are not currently first-class dev persona switcher entries; they
exist so rosters, posts, claims, and entry-path QA do not collapse into one
writer wearing every face.

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
| `harbor_director` | `writer@example.com` | Harbor Society | `starlane` | Director | Maris Vale | coastal gala pressure and public entry checks |
| `signal_director` | `writer@example.com` | Signal Creek | `starlane` | Director | Ira Bell | original weird-town mystery, current chapter, and open-lore QA |
| `nocturne_director` | `writer@example.com` | Nocturne Row | `starlane` | Director | Marcel Voss | original urban supernatural, faction, rating, and species-pressure QA |
| `crownfall_director` | `writer@example.com` | Crownfall | `starlane` | Director | Seren Vale | original court-and-faction fantasy, claims, houses, and succession QA |
| `afterlight_director` | `writer@example.com` | Afterlight Accord | `starlane` | Director | Orin Vale | broken accord, inherited duty, and public entry checks |
| `brightline_director` | `writer@example.com` | Brightline | `starlane` | Director | Viv Marlowe | original fame and industry, public-image, and career-pressure QA |
| `emberhouse_director` | `writer@example.com` | Emberhouse | `starlane` | Director | Nara Vale | original survival trials, institution pressure, and consent-safe QA |
| `gaslight_director` | `writer@example.com` | Gaslight Ward | `starlane` | Director | Ada Vale | original occult historical, class, inquiry, and respectability QA |
| `wayfarer_director` | `writer@example.com` | Wayfarer Station | `starlane` | Director | Mara Voss | original strange frontier, scarcity, station law, and signal QA |

## Browser QA

When development tools are enabled, `/dev/personas` lists these personas and
can switch the current local identity. The page must remain development-only:
production or disabled dev-tools mode should return 404.

Login sessions use the same catalog indirectly: seeded accounts currently use
the local password `password`, and the request resolver still resolves staff
power through the selected community membership and role.

## Boundaries

- Staff power is never global. `writer@example.com` is a Director in HP,
  Jurassic Park, and the original-premise communities, but only a Member in
  X-Men, RL NYC, and RL Small Town.
- Characters remain community-local and membership-owned.
- Original-premise demo rosters should preserve multiple writer memberships;
  avoid adding all accepted faces back to `starlane`.
- Inactive personas should be visible for QA, but not switchable into an active
  viewer.
- Dev persona switching is a local QA shortcut. Real flows should use login
  sessions and normal membership resolution.
