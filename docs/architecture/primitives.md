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

## Invariants

- No global characters.
- A character cannot move across communities implicitly.
- A character cannot belong to a different user's membership.
- Community export includes only characters owned by that community's
  memberships.
- Queries that load rosters, posts, or starter metadata include `community_id`.

## First Slice

The current dev app seeds one community, one membership, a small character
roster, boards, threads, and posts. The topbar character selector updates the
membership's default character, while the reply composer can still choose any
character in the active roster for a specific post.
