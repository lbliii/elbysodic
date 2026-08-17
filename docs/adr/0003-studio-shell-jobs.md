# ADR 0003: Studio shell jobs (Today, Shape, Open)

- **Status:** Accepted
- **Date:** 2026-08-17
- **Saga:** GitHub [#329](https://github.com/lbliii/elbysodic/issues/329)
- **Epic:** GitHub [#330](https://github.com/lbliii/elbysodic/issues/330)
- **Design:** GitHub [#331](https://github.com/lbliii/elbysodic/issues/331)

## Context

Studio inner navigation listed seven sibling production rooms (Operations,
Launch, Discovery profile, Structure, Intake, Appearance, Content). Desk inner
navigation listed Queue, Inbox, Roster, Plotting, Applications, Discovery, and
Realm Artifacts. Wanted repeated Applications, Plotting, and Discovery. The
identity menu also duplicated Queue and Threads.

That tree preserved Jcink Admin CP depth as a sitemap. Directors hunted rooms
instead of acting on work. The accepted shell mapping in
`docs/product/navigation-menus.md` encoded the seven-room contract.

## Decision

1. **Outer rail is unchanged:** World Home, Locations, Wanted, Desk, Studio.
   Do not add Account as a sixth rail item.
2. **Studio inner shell has three jobs:** Today (`/studio`), Shape
   (`/studio/structure`), Open (`/studio/launch`). Run folds into Today.
3. **Keep existing `/studio/*` URLs.** No `/studio/run` or `/studio/open`.
   `/studio/operations` redirects to `/studio`. Appearance, content, intake,
   discovery, and per-board editors remain deep links, not inner-nav siblings.
4. **Config vs queue:** pending applications and access-request *counts* belong
   on Today. Application fields, claims policy, and Blueprint preview stay
   Shape (`/studio/intake`). Launch posture and discovery profile stay Open.
5. **Desk inner shell (persistent):** Queue (`/my/threads`) and Inbox
   (`/notifications`). Roster, Plotting, Applications, Discovery, and Realm
   Artifacts leave the inner shell. Desk home may surface Plotting,
   Applications, and Discovery only when there is active work.
6. **Wanted inner shell (persistent):** Wanted board, Casting, Claims. Drop
   Applications, Plotting, and Discovery from Wanted inner nav.
7. **Identity menu:** Face switch, Writer profile, Identity & security, Theme,
   Logout. Drop Queue/Threads rows. The notification badge still opens Inbox.
8. **Object-local staff tools stay on the object.** Pin, lock, and move remain
   on the thread. Board and realm-home director menus remain the first edit
   path for places and appearance.

## Consequences

- `docs/product/navigation-menus.md`, `information-hierarchy.md`, and
  `control-topology.md` describe jobs, not a seven-room production sitemap.
- `src/elbysodic/web/navigation.py` is the single inner-shell implementation.
  Leaves that change Studio, Desk, and Wanted inner lists serialize on that
  file.
- Shell, forum-slice, and director-opening tests lock Today/Shape/Open and
  Desk Queue/Inbox instead of the seven Studio keys.
- Public and member pages must not gain Studio inner rows. Capability gating
  is unchanged.

## Non-goals

- New public routes (`/studio/run`, `/backstage`, Account rail item)
- Shape search or a command palette
- Chirp-UI re-adoption (ADR 0002)
- Merging Launch into Today for live invite-only realms
- Configurable director sidebar collections
- Continuity Graph
