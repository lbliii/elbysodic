# Seed Personas

Seed personas are the browser QA layer for Elbysodic's identity model. They are
not product accounts, fixtures for every test, or a replacement for the real
authorization checks. They are stable named entry points for manually testing
global account, community membership, role, and active-face combinations.

Use `src/elbysodic/db/seed.py` as the source of truth. The `SEED_PERSONAS`
catalog gives each persona a semantic key, account email, community,
membership username, optional default face, default route, and QA purpose.

The public demo posture is shifting toward original premise communities. The
literal-IP coded personas remain compatibility fixtures for older route,
identity, and privacy tests; new discovery and seed-depth checks should prefer
the original-premise personas below.

The seeded catalog includes realm-specific heroes for all 14 realms, 22
location covers, and portraits for seeded faces and writer memberships. The
nine original-premise realms have dedicated hero art shaped around their
current chapter: Afterlight's broken accord, Brightline's awards-night
sabotage, Crownfall's vacant throne, Harbor Society's Founders Gala, Nocturne
Row's treaty breach, Signal Creek's midnight transmission, Emberhouse's
tampered selection, Gaslight Ward's impossible murder, and Wayfarer Station's
missing convoy. The visual brief is in `docs/product/seed-art-direction.md`.
Seed reruns replace prior generated defaults while retaining media a director
has customized.

Original-premise communities also seed four shared ordinary writer accounts in
addition to `starlane`: `juniper.gray@example.com`, `miles.north@example.com`,
`cass.marlow@example.com`, and `lena.wren@example.com`. Each original-premise
realm has a `member` role for these writers, and its eight accepted faces are
distributed across those memberships plus the `starlane` director membership.
These accounts exist so rosters, posts, claims, and entry-path QA do not
collapse into one writer wearing every face. `harbor_writer` is the explicit
switcher entry for inspecting the completed invite-to-writer path.

Tests should use `resolve_seed_persona(repo, "<key>")` when they need a seeded
identity by purpose instead of hard-coding a username and hoping the role is
obvious.

## Matrix

| Key | Account | Community | Membership | Role | Face | QA Purpose |
| --- | --- | --- | --- | --- | --- | --- |
| `xmen_writer` | `writer@example.com` | X-Men Apocalypse | `starlane` | Member | Rogue | ordinary writer, active-face reserve, casting handoffs, scene posting |
| `xmen_staff` | `moira@example.com` | X-Men Apocalypse | `moira` | Staff | Moira MacTaggert | Studio, applications, claims, private production rooms |
| `xmen_mod` | `alex@example.com` | X-Men Apocalypse | `alex` | Moderator | Cyclops | thread moderation QA on readable boards: pin, lock, move, and update scene status |
| `xmen_partner` | `charlie@example.com` | X-Men Apocalypse | `charlie` | Member | Charles Xavier | wanted and character plot-hook interest, private plotting rooms, notification handoffs, and counterparty checks |
| `xmen_applicant` | `mira@example.com` | X-Men Apocalypse | `mira` | Member | Kitty Pryde | structured submitted application, answered entry prompt, writer-side revision workflow, prospective-face plotting handoff, and writer-mention inbox state |
| `xmen_outsider` | `simon@example.com` | X-Men Apocalypse | `simon` | Member | Bolivar Trask | outsider, private-room denial, and notification visibility checks |
| `xmen_inactive` | `inactive@example.com` | X-Men Apocalypse | `sleepingstar` | Member | Sleeping Star | inactive membership denial and recovery checks |
| `hp_director` | `writer@example.com` | HP Universe | `starlane` | Director | Rowan Ash | invite-only Studio Launch posture |
| `jp_director` | `writer@example.com` | Jurassic Park Universe | `starlane` | Director | Dr. Lena Marquez | backstage Studio Launch posture |
| `nyc_writer` | `writer@example.com` | RL NYC | `starlane` | Member | Lena Park | same account without staff power in another community |
| `smalltown_writer` | `writer@example.com` | RL Small Town | `starlane` | Member | June Calloway | low-stakes ensemble writer checks |
| `harbor_director` | `writer@example.com` | Harbor Society | `starlane` | Director | Maris Vale | coastal gala pressure, public entry, writer intake, and face-application review |
| `harbor_writer` | `juniper.gray@example.com` | Harbor Society | `junipergray` | Member | Celia Fairbourne | accepted invitation, multi-writer scenes, and two submitted second-face applications from a wanted hook |
| `signal_director` | `writer@example.com` | Signal Creek | `starlane` | Director | Ira Bell | original weird-town mystery, current chapter, and open-lore QA |
| `signal_new_writer` | `firstface@example.com` | Signal Creek | `newarrival` | Member | — | Writer Desk's first-face entry path before the member has an application or posting face; pending cross-realm request to Harbor Society |
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

The X-Men demo seed includes a live casting path: Rogue is reserved for the
winter rescue wanted hook, Mira raises prospective-face interest as Dr. Dana
Park and plots privately with Charles, and Charles follows up on Rogue's
relationship hook in a second private room. That second room is ready to become
a scene in Mutant Underground, so `xmen_writer` opens `/plotting` to review the
room and start the handoff as Rogue. These records populate the casting desk,
plotting list, and relevant notification inboxes without treating Dana as an
accepted face or exposing room notes on public pages.

Kitty's application is a complete review-room example: it has answered
director-defined claim fields, a prior revision request, a writer resubmission,
and private staff review notes. The applicant and director personas should see
the same status history while only the director sees production notes and the
checklist.

The X-Men OOC introductions thread contains a writer-facing `@mira` mention
from Charlie, with the matching membership-scoped inbox item. The featured
Afterlight Accord opening scene has a seeded edit-history entry, so its first
post demonstrates the post revision reader without altering the public scene
text.

Harbor Society demonstrates writer entry: Juniper's request is reviewed,
invited, and accepted into the existing Celia Fairbourne membership, while
Eloise Byrne's request remains in the director's review queue. The accepted
invitation is historical seed data; the database contains no usable invite
token. Juniper also has submitted Daphne Pike and Beatrice Crane applications
linked to the Reporter source at the club wanted hook. Daphne links directly to
the public hook; Beatrice links through a private wanted-interest record. Both
application rooms show the public hook context, while Beatrice's private note
stays out of the review room.

Harbor Society also includes an unpublished Founders Gala event brief. The
director sees it in the Studio publishing queue and can open or publish it;
writer personas see only the published Guidebook materials until the director
releases the draft.

Realm Artifacts are seeded with story-specific prompts for every original-
premise community. Application prompts have one answered example; general polls
have a small spread of answers from active writer memberships, so the demo can
show both an individual response state and aggregate results. Each original-
premise realm also has two public sample scenes tied to its active story beat,
with distinct titles, prose, and in-world timelines. Each scene seeds all four
posts in the signed-out preview window, so the demo reaches the same preview
boundary writers see when browsing a public realm; a fifth post stays behind
the realm gate for members. Seeded premise and event materials use reader-
facing titles so discovery leads with the story. X-Men's applicant persona has
answered Pressure Lane Finder.

Studio Launch has a seeded director entry for each opening posture: Jurassic
Park Universe is backstage, HP Universe is invite-only, and the original-
premise communities remain public-preview realms for catalog and writer-entry
QA. The two legacy genre fixtures stay out of public discovery while preserving
their distinct Studio Launch states.

Signal Creek also has an active member with no characters or applications.
Switch to `signal_new_writer` and open `/desk` to review the first-face path;
the account remains separate from the shared director login and the four
multi-realm writer accounts. The same global account has a pending Harbor
Society access request linked to that account, so directors can review linked-
account state and its request history while the writer keeps a separate local
membership and role in each community.

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
