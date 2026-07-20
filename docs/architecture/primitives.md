# Elbysodic Primitives

These are the architectural primitives for the play-by-post studio core. They
name the product rules that should stay stable as the implementation grows.

The product strategy spine in `docs/product/strategy-spine.md` organizes these
primitives into three pillars: Realm Studio, Writer Network, and Continuity
Graph. Architecture should preserve the shared foundation for all three:
tenant-aware data, global users, community-local memberships, local faces,
membership-scoped permissions, character-authored story context, service-owned
workflow policy, and rendered privacy proof.

## Identity

`User` is the private global login account.

`CommunityMembership` is the user's account inside one community. Roles,
permissions, community-local username, roster preferences, and moderation power
belong here.

Staff power is expressed and stored as named membership-scoped capabilities,
not user-level authority. `role_capabilities` grants each community role only
the powers it needs. Legacy director roles marked `is_admin` are migrated to
all registered capabilities, while partial staff roles can hold a strict
subset without teaching pages to read storage flags directly.

The service policy module keeps an executable capability contract registry for
the current staff surface. Sensitive accepted, rejected, and failed actions
can be recorded in `staff_audit_events` with the community, actor membership,
optional actor face, capability, target family/id, action, outcome, reason,
public aftermath, and timestamp. Audit reads are tenant- and
capability-scoped; there is no public audit feed.

`Character` is the public posting identity. Characters are not global. A
character belongs to exactly one membership in exactly one community.

## Public Identifiers

Database ids are internal persistence identities. They are for foreign keys,
repository joins, audit trails, and service internals, not public URLs or
visible labels.

Public identities should be scoped to the object writers already understand:

- named community objects use community-scoped slugs, such as character,
  material, wanted, board, and claim-type slugs
- named child objects use parent-scoped slugs, such as thread slugs under a
  board or plot-hook slugs under a character
- visible append-only records use parent-scoped ordinals, such as post numbers
  inside one thread
- private, sensitive, or capability-bearing records should use opaque public
  ids when they need public links at all

Ordinals are assigned once and are not reused. A later hide, tombstone, or
moderation action must not renumber the surrounding stream, because
notifications, read jumps, exports, and copied scene links should keep pointing
at the same beat.

## Character Roster

When a user enters a community, that community resolves the user's membership
and activates only that membership's character roster.

A membership may set a `default_character_id`. The composer and user-facing
forum chrome should use that character as the default face for the member. The
member can still switch character per post.

The active face is also a browsing lens. When a member is wearing a character,
Elbysodic can safely bias discovery, open-scene joins, queue views, and future
filters toward that character. This reduces visual load while preserving
explicit controls where the user may need to act as someone else.

## Authorship

Posts are visibly authored by a character:

```text
posts.author_character_id
```

Posts also store the owning membership for auditability and permission checks:

```text
posts.author_membership_id
```

Thread starter metadata follows the same pattern. Permissions are evaluated
through the membership unless Elbysodic later adds an explicit
character-specific restriction.

## Thread State And Queues

Thread participation is tracked through characters, but obligations are
membership-aware. A writer needs a reply when someone outside their roster has
the latest post in a participated thread. A writer is waiting when one of their
characters currently has the last word.

Read state is stored per membership and thread:

```text
thread_reads.community_id
thread_reads.thread_id
thread_reads.membership_id
```

This supports first-unread jumps, next-unread navigation, sidebar board counts,
and "caught up" thread status without confusing one writer's reading state with
another's.

## Watches And Notifications

Thread watches are explicit membership intent:

```text
thread_watches.community_id
thread_watches.thread_id
thread_watches.membership_id
```

Starting or replying to a thread auto-watches it for the posting membership.
Watches can also be toggled from the thread page.

Notifications are community-scoped and delivered to memberships. Implemented
notification target families include:

- watched-thread replies and `@Character` or writer mentions that target posts
- wanted interest and reserve updates that target wanted hooks or interest rows
- character plot-hook, plotting-room, and scene-started updates
- character application updates for applicant and casting workflows

Notification kinds register their target family and required target fields in
the service layer. The same contract gates shell counts, inbox rows, open
redirects, and mark-read flows so stale or malformed rows cannot reveal private
room titles, wanted notes, application state, or cross-community targets.

Mention parsing supports both character and writer handles. Character mentions
are story-facing and should resolve to character profiles. Writer mentions are
OOC-facing and should resolve to membership profiles.

## World Facets

Facets are director-defined world lenses. They are community-scoped and grouped
by a director-controlled taxonomy, such as:

```text
facet_groups.community_id
facets.community_id
facets.facet_group_id
```

The seed forum currently demonstrates species, affiliation, location, and plot
lane groups, but the primitive is intentionally broader. Other boards might use
houses, clans, bending types, supernatural courts, nations, careers, ship
status, or event roles.

Facets can be assigned to characters, boards, threads, world materials, and
wanted hooks. They are not only decoration; they are a discovery and automation
surface for finding compatible characters, relevant boards, open threads, event
roles, and faction pressure.

## World Materials

World materials are director-authored pillar content outside the thread format.
They are community-scoped structured pages for premise, rules, factions,
application guidance, events, or other board-defining material.

Current material types are intentionally bounded: premise, guide, factions,
application, and event. Repository writes reject unknown material types so
director-authored material does not become a generic CMS page.

Materials can be facet-tagged so the same world lenses can connect lore,
characters, boards, scenes, and wanted hooks. This is the current home for
special pages that old PBP forums often represented as pinned information
threads.

## Wanted Hooks

Wanted hooks are first-class plot and casting invitations. They are not ordinary
threads, though they may later spawn plotting threads, applications, claims, or
notifications.

The core shape is:

```text
wanted_ads.community_id
wanted_ads.creator_membership_id
wanted_ads.creator_character_id
wanted_ads.related_material_id
```

`creator_membership_id` records ownership and permissions.
`creator_character_id` records the public story face when the hook is
character-authored. `related_material_id` can connect the hook to an event,
premise page, faction guide, or application guide.

Wanted hooks can also list related characters and facets. That lets a hook like
"Human UN liaison for B-24 talks" participate in the same discovery grammar as
characters, threads, and event pages.

Current statuses are intentionally small: open, reserved, filled, and archived.
Current wanted-hook types are canon, connection, event role, faction need, plot
role, relationship, and rival.
Future workflows can add interest, claims, reserve expiry, staff review, and
application spawning without turning wanted hooks into generic threads.

## Applications, Claims, And Reserves

Applications are casting and roster review records. They are scoped to one
community, one membership, and one character. Application events store the
membership that made a review move and optionally the character face that gives
story context.

Claims and reserves are director-defined casting constraints, not generic tags.
Claim types are community-scoped, and character claims connect the claimed
value to the owning character and membership. Reserves protect a future casting
intention for a membership and community. These surfaces need staff/applicant
privacy proof because they often include private review notes, conflict
resolution, or unpublished character intent.

## Plot Hooks And Plotting Rooms

Character plot hooks are face-authored invitations for relationship, scene, or
arc discovery. They belong to a community, membership, and character.
Current plot-hook types are scene, relationship, connection, event, and other.

Plotting rooms are structured handoff spaces between wanted interest, character
hooks, and scenes. They store participants, messages, planning fields, target
boards or threads, and notification targets. Because plotting rooms can be
private or participant-limited, rendered route and notification tests must
prove that outsiders do not see private room titles, messages, counts, or
recovery links.

## Character Hubs

Character profiles are becoming hubs rather than static profile pages. The
current hub contains identity, facets, wanted hooks, tracker/queue context, and
recent posts. Character hubs can also surface claims/reserves, application
status, plot hooks, and world-material links when privacy rules allow them.

## Studio Network And Tenant Routes

The seeded development and Railway demo app can expose multiple communities on
one shared host. Canonical shared-host community links use
`/c/{community_slug}` so the realm is resolved before local board, material,
wanted, character, or thread slugs are looked up.

`/` and `/network` are platform/network surfaces, not one community's world
home. Public catalog/search uses `PublicCatalogCard` read models that carry
only public realm profile, published material, safe counts, discovery tags, and
entry posture. Signed-in continuation stays in separate Network return-path or
Studio network read models so active faces, staff role, unread notifications,
applications, plotting rooms, and membership identity cannot contaminate public
realm cards.

## Program Blueprints

Program Blueprints are director-authored starter packets for communities,
starter faces, boards, materials, wanted hooks, theme tokens, appearance
choices, and board media. Current Studio intake supports parsing, validation,
and dry-run preview. Apply/hydration is intentionally gated until a typed diff,
collision handling, transaction, rollback, and tenant tests exist.

## Moderation

Thread lifecycle controls are staff-only and membership-role based. The current
primitive set includes pinning, locking, unlocking, unpinning, and moving a
thread between visible boards.

Moving a thread must not rewrite post history, revisions, read state, watches,
or notification targets.

## Community Export

Community export currently starts as an internal service-owned manifest, not a
public CLI, API, or self-serve UI. The manifest is scoped to one community and
summarizes counts, ownership edges, stable source links, and redaction rules
through tenant-aware repository methods.

The export contract preserves membership ownership and character authorship as
separate facts. It deliberately excludes global login users, password hashes,
sessions, token hashes, raw invite tokens, and private access-request notes from
the general community archive manifest. Director-only detail export can be
designed later if those private workflow records need a separate archive path.

Export privacy profiles live with the service manifest. They define the allowed
domain lists for public export, member export, staff operations export, and
director archive export before any binary/archive artifact exists. Every profile
and manifest section carries `community_id`, and every tier explicitly excludes
cross-community records. Lower tiers keep private notes, staff queues, inactive
identities, draft materials, notification rows, and other writers' private
records out of export scope. The director archive profile names sensitive
domains so operators can see which PBP workflow records require privacy review
before preservation.

The export boundary matrix below is the planning contract for #81, #137, and
#168. It does not approve a public CLI, API, UI, service API expansion,
cross-community export mode, or privacy-boundary change without a separate
review.

| Manifest Section | Include | Exclude Or Redact | Provenance Fields |
|---|---|---|---|
| Realm profile | Current community name, slug, launch/export posture, public premise pointers, and archive tier. | Other communities, hosted network state, global user data, and deployment secrets. | `community_id`, `community_slug`, profile tier, source route where applicable. |
| Membership ownership | Community-local memberships, roles, inactive state only for approved staff/director tiers, and ownership edges to faces and workflow records. | Global account emails unless a future detail export approves them, password hashes, sessions, selected identity state, and user-level staff power. | `community_id`, membership id, role id, status, owned record kind/id. |
| Face authorship | Public faces, face ownership, post authorship, wanted/plotter authorship, and application posture for approved tiers. | Global characters, cross-community faces, another writer's private application draft outside the tier, and inactive faces in public/member tiers. | `community_id`, character id, owner membership id, public slug, authored record kind/id. |
| Boards, scenes, threads, and posts | Community boards, visible scene/thread metadata, post ids, post numbers, author membership, and author face for approved tiers. | Private boards/posts outside the tier, unrelated communities, raw private queue state, and session/read cookies. | `/c/{community}/boards/{board}/threads/{thread}#post-*`, board id/slug, thread id/slug, post id/number. |
| Director materials | Published material metadata for public/member tiers; draft director material only for staff/director archive tiers. | Draft bodies in lower tiers, external secrets, layout-breaking theme inputs, or raw uploaded credentials. | `/c/{community}/world/{material}`, material id/slug, status, source material type. |
| Claims, reserves, and wanted hooks | Claim type/value state, reserve state, wanted hook state, creator membership, creator face, and public hook route according to tier. | Director notes, private reserve/support notes, expired/private state outside the tier, and cross-community claims. | `/c/{community}/wanted/{wanted}`, claim/reserve/wanted ids, membership id, character id where applicable. |
| Plot hooks and plotting rooms | Plotter hooks and plotting-room state only for tiers allowed to see owner/participant/staff handoff context. | Private plotting notes for public/member tiers, nonparticipant room messages, hidden targets, and unrelated rooms. | Character hook route, plotting room id, owner membership id, participant ids when tier-approved. |
| Access requests and invitations | Counts and lifecycle metadata only in director archive profile unless a future detail export approves more. Invitation state without raw tokens. | Applicant emails, private notes, face concepts, wanted-hook private interest text, token hashes, raw invite tokens, and account-link history outside director/staff review. | Request id, invitation id, status, event timestamps, `community_id`; no raw token or hash. |
| Notifications and queues | Notification row counts and target families only after target visibility review in director archive profile. | Public/member notification rows, inaccessible target labels, private snippets, cross-community targets, and global inbox framing. | Notification id, target kind, target family, visible target route if approved by target contract. |
| Continuity-ready source links | Stable source references for scenes, posts, materials, claims, reserves, wanted hooks, and future reviewed canon proposals. | Unreviewed summaries, private source text, staff notes, access-request notes, and automatic canon from private material. | Source family, `community_id`, source id, optional source thread id for posts, visibility status. |

Export proof groups:

| Proof Group | Required Coverage |
|---|---|
| Tenant scope | Two communities, same global user in multiple communities, and proof that export rows, links, counts, ownership edges, and redactions all carry one `community_id`. |
| Auth redaction | Global users, password hashes, sessions, selected identity state, token hashes, raw invite tokens, cookies, and credentials are absent from rendered/serialized manifest output. |
| Privacy tiers | Public, member, staff, and director archive profiles include only their allowed domains and name sensitive domains before detail export work starts. |
| Ownership/authorship | Membership ownership and character authorship stay separate for faces, posts, wanted hooks, plot hooks, and plotting rooms. |
| Staff workflow privacy | Access-request notes, applicant emails, invitation audit material, notification rows, staff queues, and private plotting rooms are excluded or marked sensitive according to tier. |
| Provenance | Source links use tenant-prefixed routes or source-family references for posts, materials, claims, reserves, wanted hooks, and continuity-ready records. |

Stop and ask before adding public export commands, public APIs, route surfaces,
download formats, destructive import/restore behavior, cross-community export,
or service API changes that alter which domains are included.

## Continuity Graph

Continuity Graph is not yet a persistence primitive in this repo. Existing
world materials and wanted-hook vocabulary can refer to canon, and
`src/elbysodic/domain/continuity.py` names schema-neutral draft primitives for
manual proposals, source citations, affected objects, review events, lifecycle
state, and approved canon entries. Storage, services, notifications, rendered
surfaces, and public canon read models remain gated by
`docs/architecture/continuity-graph-readiness.md`.

The first approved slice must be manual, source-linked, and reviewed. It must
keep staff membership review authority separate from public character context,
and it must prove that private scenes, plotting rooms, applications, staff
notes, access-request notes, and unreviewed summaries cannot become public
canon.

## Invariants

- No global characters.
- A character cannot move across communities implicitly.
- A character cannot belong to a different user's membership.
- Community export includes only characters owned by that community's
  memberships.
- Queries that load rosters, posts, or starter metadata include `community_id`.
- Queries that load facets, materials, wanted hooks, claims, reserves, or
  applications include `community_id`.
- Read state, watches, notifications, roles, and moderation powers are scoped to
  community membership, not global user.
- Structured board-running material should not be forced into threads when a
  typed primitive better represents the ritual.

## Current Slice

The current dev app seeds several communities for tenant and persona QA. The
identity menu updates the membership's default character, while the thread
composer and reply composer can still choose any character in the active roster
for a specific post.

The first slice now also includes read-state queues, post editing, revision
history, staff thread controls, thread watches, character and writer mentions, a
notification inbox, director-defined facets, world materials, wanted hooks,
claims, reserves, applications, plotting rooms, realm interactions, Studio
operations, Program Blueprint dry-run preview, tenant-prefixed shared-host
routes, and character hub surfaces.
