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
- Read state, watches, notifications, roles, and moderation powers are scoped to
  community membership, not global user.

## First Slice

The current dev app seeds one community, one membership, a small character
roster, boards, threads, and posts. The topbar character selector updates the
membership's default character, while the thread composer and reply composer can
still choose any character in the active roster for a specific post.

The first slice now also includes read-state queues, post editing, revision
history, staff thread controls, thread watches, direct mentions, and a
notification inbox.
