# Elbysodic Primitives

These are the first architectural primitives for the play-by-post forum core.
They are intentionally small, but they name the product rules that should stay
stable as the implementation grows.

## Identity

`User` is the private global login account.

`CommunityMembership` is the user's account inside one community. Roles,
permissions, community-local username, roster preferences, and moderation power
belong here.

`Character` is the public posting identity. Characters are not global. A
character belongs to exactly one membership in exactly one community.

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

Notifications are community-scoped and delivered to memberships. The first
implemented notification kinds are:

- `thread_reply` for replies to watched threads.
- `mention` for simple `@Character` mentions.

Notification targets point at posts so the inbox can jump directly to the
relevant beat.

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
Future workflows can add interest, claims, reserve expiry, staff review, and
application spawning without turning wanted hooks into generic threads.

## Character Hubs

Character profiles are becoming hubs rather than static profile pages. The
current hub contains identity, facets, wanted hooks, tracker/queue context, and
recent posts. Future hub sections can add relationships, claims/reserves,
application status, plot pages, or world-material links.

## Moderation

Thread lifecycle controls are staff-only and membership-role based. The current
primitive set includes pinning, locking, unlocking, unpinning, and moving a
thread between visible boards.

Moving a thread must not rewrite post history, revisions, read state, watches,
or notification targets.

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

## First Slice

The current dev app seeds one community, one membership, a small character
roster, boards, threads, and posts. The topbar character selector updates the
membership's default character, while the thread composer and reply composer can
still choose any character in the active roster for a specific post.

The first slice now also includes read-state queues, post editing, revision
history, staff thread controls, thread watches, character and writer mentions, a
notification inbox, director-defined facets, world materials, wanted hooks, and
the first character hub shape.
