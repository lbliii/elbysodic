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

Authentication resolves first and remains global-account scoped. The existing
database-backed `elbysodic_session` is validated once and exposed through
Chirp's `request.user` accessor; the request tenant resolver then derives the
community-local membership and face from that same cached login. Code reading
`request.user` must not infer a membership, role, staff capability, current
community, or active face from the global account adapter.

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

The current rollback and duplicate-submit coverage map lives in
`docs/architecture/transactional-workflow-coverage.md`. Update it when a
workflow gains new side effects, a test moves, or a remaining gap becomes
covered proof.
The tenant integrity audit matrix in `docs/architecture/data-integrity.md`
names the row families whose command protocol changes need service rollback,
repository tenant-pair, rendered POST, and migration parity proof before they
become stricter storage or public command contracts.

High-risk multi-row commands should put story-visible and attention-visible
side effects in one service transaction. Replying to a thread creates the post,
fanout notifications, watch state, and read marker inside one transaction so a
late notification/watch failure cannot leave a stranded reply. Starting a thread
similarly keeps thread, participants, opening post, watch, and read marker
together.

When a command-token form reserves a server idempotency key and then fails
before producing the canonical result path, the incomplete reservation must be
discarded. Validation errors, stale actor failures, and rolled-back service
exceptions should let the same rendered key retry the corrected command instead
of becoming a permanent no-result duplicate.

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

Identity-switch `next` recovery applies the same rule to stale community paths.
Character, application, wanted, world-material, plotting-room, board, and
thread destinations must either remain valid inside the selected realm or fall
back to a safe local hub for that route family.
Access-request recovery follows the lifecycle matrix in
`docs/architecture/security-boundaries.md`: duplicate, account-link, replayed
invite, decline, withdrawal, and expiry states cannot reveal request notes,
invitation links, raw tokens, staff review state, or another community's
request history.

## Notification Read Models

Notification counts and inbox rows are service-owned read models for the
resolved membership. Counts, page lists, mark-all behavior, and open redirects
must run notification targets through the same visibility policy before they
render or mutate state. Page limits apply after filtering inaccessible targets
so private, staff, stale, or forged notification rows cannot hide older visible
obligations while the shell still reports unread work.

Each supported notification kind is registered in the service-owned target
contract table with its label, target family, required target fields, and
visibility, redirect, and fallback behavior. New kinds must add a contract
entry and proof before they can contribute to shell counts, inbox rows,
redirects, or mark-read behavior. Rows with an unregistered kind or missing
required target fields are treated as inaccessible even when they belong to the
resolved membership, which protects rendered pages from legacy or damaged
notification data. Creation-time fanout should use the same target contract
before inserting rows; post mentions and watched-thread replies already skip
inactive memberships and memberships that cannot view the target board.

This matrix is the planning contract for #82, #140, and #170. It does not
approve notification fanout changes, route redirects, privacy-rule changes, or
public rendered contract changes without a separate review.

| Kind | Target Family | Required Fields | Visible To | Label/Snippet Source | Href And Redirect | Hidden/Malformed Outcome |
|---|---|---|---|---|---|---|
| `mention` | thread post | `thread_id`, `post_id` | Memberships that can read the target board. | Thread title plus rendered post snippet; actor from membership/face. | Open target thread at the post anchor. | Hide from inbox/counts, keep unread, and refuse open when thread, post, or board is missing or private to the viewer. |
| `thread_reply` | thread post | `thread_id`, `post_id` | Watched memberships that can read the target board. | Thread title plus rendered post snippet; actor from membership/face. | Open target thread at the post anchor. | Hide from inbox/counts, keep unread, and refuse open when thread, post, or board is missing or private to the viewer. |
| `wanted_interest` | wanted interest | `wanted_ad_id`, `wanted_ad_interest_id` | Interested writer, hook creator, or casting-capable staff. | Wanted title plus safe interest snippet; private notes only for authorized viewers. | Open wanted hook detail. | Hide private note, hide from unauthorized inbox/counts, keep unread, and refuse open when hook or interest is missing. |
| `wanted_reserved` | wanted hook | `wanted_ad_id` | Memberships that can read the wanted hook. | Wanted title plus reserve action snippet. | Open wanted hook detail. | Hide from inbox/counts, keep unread, and refuse open when hook is missing or inaccessible. |
| `reserve_created` | wanted hook | `wanted_ad_id` | Memberships that can read the wanted hook. | Wanted title plus reserve-created snippet. | Open wanted hook detail. | Hide from inbox/counts, keep unread, and refuse open when hook is missing or inaccessible. |
| `plot_hook_interest` | plot hook | `character_plot_hook_id` | Hook author or casting-capable staff. | Plot hook title plus interest snippet. | Open character plot hook detail. | Hide from inbox/counts, keep unread, and refuse open when plot hook or face is missing. |
| `plotting_room_created` | plotting room | `plotting_room_id` | Room owner, participant, or casting-capable staff. | Plotting room title plus room-started snippet. | Open plotting room. | Hide room title, hide from inbox/counts, keep unread, and refuse open when room is missing or viewer cannot enter. |
| `plotting_room_threaded` | plotting room | `plotting_room_id` | Room owner, participant, or casting-capable staff. | Plotting room title plus scene-started snippet. | Open plotting room. | Hide room title, hide from inbox/counts, keep unread, and refuse open when room is missing or viewer cannot enter. |
| `application_submitted` | character application | `character_id` | Character owner or casting-capable staff. | Face name plus submitted-for-review snippet. | Open character application room. | Hide from inbox/counts, keep unread, and refuse open when face is missing or viewer cannot review/own it. |
| `application_accepted` | character application | `character_id` | Character owner or casting-capable staff. | Face name plus accepted snippet. | Open character application room. | Hide from inbox/counts, keep unread, and refuse open when face is missing or viewer cannot review/own it. |
| `application_revision_requested` | character application | `character_id` | Character owner or casting-capable staff. | Face name plus revision-requested snippet. | Open character application room. | Hide from inbox/counts, keep unread, and refuse open when face is missing or viewer cannot review/own it. |

Resolver invariants:

- Staff notification behavior remains membership-local; staff can see its own
  inbox, not a global queue, unless a future staff queue explicitly owns a
  target family.
- Hidden, deleted, archived, private, cross-community, inactive,
  wrong-membership, unregistered, and missing-field targets do not contribute
  to visible unread counts, inbox rows, open redirects, or mark-read mutation.
- Inbox limits apply after target visibility filtering so inaccessible rows
  cannot crowd visible obligations out of the page.
- Mark-all-read and open-notification actions may mark only notifications whose
  target resolves through the same contract that rendered them.
- Creation-time fanout should check deliverability before inserting rows; new
  notification kinds must prove this or explicitly document why the kind is
  stored first and filtered later.

Required proof for future changes:

- Service contract tests that every registered kind is unique, has required
  fields, names visibility/redirect/fallback behavior, and rejects unregistered
  or missing-field rows.
- Service visibility tests for deleted, archived, private, cross-community,
  inactive, faceless, owner, member, wrong-membership, and staff scenarios as
  applicable to the target family.
- Rendered tests for inbox rows, shell unread counts, open redirects,
  mark-all-read, and mark-read behavior.
- Fanout tests proving unauthorized or inactive memberships do not receive
  obviously inaccessible rows when the target family can be checked before
  insertion.
- Docs collateral in `docs/architecture/rendered-route-privacy-matrix.md`,
  `docs/architecture/security-boundaries.md`, and this protocol whenever a new
  kind, target family, redirect behavior, or privacy rule is introduced.
