# Request Identity And Command Protocol

Elbysodic renders server pages for writers who may switch realms, memberships,
and active faces during long sessions. Every page and POST command must preserve
the difference between login account, community membership, public character
authorship, and staff power.

## Viewer Identity

Resolved viewer identity has these parts:

- `community`: the realm currently being rendered or acted inside.
- `user`: the global login account.
- `membership`: the user's identity inside the community.
- `role`: the membership-local role for permissions in that community.
- `current_character`: the active face used as a browsing and composer lens.

The request tenant prefix wins before session-selected identity. A selected
membership is usable only when it belongs to the resolved community, belongs to
the resolved user, is active, and has a role in the same community.

Malformed session-backed identity must be auditable and fail closed or recover
deterministically. Development cookie fallback can recover stale local state, but
production session corruption must not silently become an unrelated identity.

## Actor Shapes

Commands should name which actor shape they use:

- `membership-only`: the command belongs to the writer membership, not a face.
- `explicit-character`: the form names a `character_id` and services validate
  that character belongs to the current membership and community.
- `current-face`: the command uses `viewer.current_character` at POST time.
  Reserve this for low-risk commands or add stale-state proof.
- `prospective-character`: the command records a concept before a character
  exists.
- `staff-actor`: the command is performed by membership-local staff power and
  may optionally include a character context for story-facing output.

Story-visible writes should prefer `explicit-character` over `current-face`.
Hidden `community_id`, `membership_id`, `role_id`, or staff flags from forms are
not trusted. Services reload scoped rows through the resolved viewer.

## Command Binding

Every mutating rendered form should declare:

- command kind
- pending label
- pending scope
- actor shape
- target object
- stale command behavior
- whether a server idempotency key is required

Client submit guards improve feedback, but server behavior owns correctness.
Commands that create posts, scenes, rooms, reserves, claims, applications,
notifications, or identity transitions need either idempotency or a deliberate
duplicate policy.

Chirp `_actions.py` dispatch may be used as transport plumbing for command
routing only after the action path preserves request-scoped services. Elbysodic
commands must still resolve tenant, membership, active face, and staff power
from the current request rather than a process-global provider.

## Stale Commands

A stale command is a POST submitted after the rendered assumptions changed. A
service should reject or recover stale commands when any of these differ from
the current resolved viewer:

- community
- membership
- active/explicit character ownership
- role or capability needed for the command
- target object community or visibility

Controlled failure copy must say whether the realm, membership, active face, and
authored object changed. Retry-safe actions should be explicit.

## Recovery

Route recovery is a privacy-sensitive workflow. Services decide whether a
cross-realm object can be named, whether the viewer can switch to it, and what
fallback links are safe. Web templates render the prepared recovery read model.

Recovery must not reveal private/staff object existence through shell counts,
links, command labels, or exact target copy unless that reveal is allowed by the
recovery visibility policy.
