# Data Integrity Contracts

Elbysodic stores global users and community-scoped creative records. Repository
methods keep `community_id` explicit, but SQLite constraints must also prevent
impossible tenant pairings wherever the data model can express them.

## Tenant-Paired Rows

A tenant-paired row stores `community_id` and one or more foreign keys to rows
that also belong to a community. Those references must resolve in the same
community before the row is persisted.

High-risk tenant-paired rows include:

- memberships and roles
- characters and memberships
- boards, threads, posts, and public authorship
- command submissions and the membership that reserved the command
- applications and review events
- realm interaction definitions, responses, answers, and options
- wanted hooks, interests, reserves, and claims
- plotting rooms, source interests, target scenes, participants, and messages
- reactions, reads, watches, and thread participants
- notifications and sidebar counts
- user-session selected membership

## Enforcement Layers

Use all three layers:

- Schema: composite foreign keys, unique pairs, checks, or triggers.
- Repository: scoped methods that load parent rows by `community_id`.
- Services: workflow validation using resolved viewer, policy helpers, and
  explicit actor shapes.

Diagnostics are not a substitute for constraints. They are the repair and
operations surface for old data, migrations, imports, and local demo databases.
`ForumRepository.list_tenant_pair_integrity_issues()` is the shared repository
diagnostic for tenant-paired creative and workflow rows, including membership
roles, default faces, character ownership, command submissions, authorship,
claims, realm interactions, plotting rooms, reactions, thread state, and
notifications. Diagnostic rows report ids, table names, tenant ids, and
content-free relationship reasons so operators can plan repair work without
exposing private posts, room notes, application answers, or staff-only details.

`src/elbysodic/services/tenant_integrity.py` wraps those repository diagnostics
as a read-only service report. The report groups findings by `community_id` and
severity, preserves table/domain/row ids for repair planning, and keeps output
free of post bodies, private notes, applicant emails, room notes, and account
secrets. Director-scoped reads filter to the current community through
`tenant_integrity_audit_for_viewer`; ordinary members, inactive memberships,
public visitors, and staff from another community must not see a realm's audit
findings. CLI exposure and nonzero-exit behavior remain deferred until the
operator command shape is approved.

## Tenant Integrity Audit Matrix

This matrix is the planning spine for #55, #56, and #141. It does not approve
schema, migration, trigger, public command, lifecycle, concurrency, or repair
changes. Each future implementation slice should update the row for the family
it hardens and include the proof group named below.

| Row Family | Invalid Pairings To Reject | Runtime Owner | Storage/Diagnostic Owner | Current Proof Or Gap | Migration Risk |
|---|---|---|---|---|---|
| Memberships and roles | Membership role from another community; inactive membership selected as active viewer; user-level staff power inferred outside membership. | Request identity resolver and policy helpers. | `community_memberships`, `roles`, session-selection diagnostics. | Tenant audit covers membership role drift; production auth tests cover selected membership constraints. | High if stricter constraints must repair legacy sessions or role ids. |
| Characters and default faces | Character owned by another membership or community; default face points at a wrong-community or inactive face. | Character services and viewer resolution. | Character ownership diagnostics. | Tenant audit covers default-face and character ownership drift. | Medium; repair may clear default face rather than move ownership. |
| Threads, posts, and participants | Thread board, author membership, author face, post author face, participants, watches, and read state cross community or membership. | Posting/thread services and explicit-character validation. | Thread/post/read/watch diagnostics and future composite constraints. | Wrong-face authorship and rollback proof exist; matrix still needs per-row negative repository tests before constraints. | High; story-visible rows need careful repair policy. |
| Command submissions | Idempotency key reserved for a membership or community that does not match the executed command. | Command binding and service transaction owners. | `command_submissions` diagnostics. | Reply/start-thread duplicate and retry tests exist; broader command-family coverage is partial. | Medium; stale reservations may need safe deletion. |
| Applications and review events | Application face, applicant membership, reviewer membership, mapped claims/reserves, and review events disagree on community. | Application/review services. | Application and event diagnostics; future tenant-paired indexes. | First-face rollback exists; late acceptance rollback remains a gap. | High; review history may contain private staff notes and must be redacted in diagnostics. |
| Access requests and invitations | Request, event, linked invitation, account link, inviter, and accepted membership drift across community or create permission before invite acceptance. | Access-request and invitation services. | `community_access_requests`, events, invitations, token-hash diagnostics. | Invite/status rollback and token redaction tests exist; lifecycle matrix remains separate in #167. | High; token and applicant privacy make repair behavior sensitive. |
| Wanted hooks, interests, reserves, and claims | Wanted hook, interested membership or face, claim type, reserve owner, claimed face, and staff reviewer disagree on community or membership. | Wanted, claim, reserve, and application handoff services. | Wanted/claim/reserve diagnostics and future uniqueness constraints. | Visibility and duplicate proof exist; rollback and storage negative tests remain partial. | Medium-high; public claims and private reserves need different repair handling. |
| Plotting rooms, messages, and scene handoffs | Room community, source wanted interest, target scene, participants, messages, and attached scene cross community or exclude authorized participants. | Plotting and scene handoff services. | Plotting diagnostics and transaction proof. | Scene handoff rollback exists; room creation rollback is partial. | Medium; room privacy means diagnostics stay content-free. |
| Realm interactions and answers | Prompt, option, response, answer, membership, face, and community point to different tenant roots. | Interaction/application services. | Realm-interaction diagnostics. | Diagnostic coverage exists; constraint parity proof is still future work. | Medium; malformed answers may be cleared rather than repaired. |
| Notifications and shell counts | Notification membership, target community, target row, href, read state, and visibility resolver disagree. | Notification target resolver and shell/inbox read models. | Notification diagnostics plus future registered-kind contract. | Target resolver expansion is tracked in #170. | High; hidden rows must not leak through counts or redirects. |
| Sessions and selected identity | Session user, selected membership, selected community, role, active face, and route tenant prefix drift. | Auth service and request identity resolver. | Session repository diagnostics and auth trust posture. | Auth trust diagnostics and rendered security tests exist; storage constraints remain future work. | High; stale production sessions must fail closed without leaking another realm. |
| Continuity/export source links | Source family, source community, source row, source thread for posts, affected object, and viewer visibility disagree. | Continuity/export services. | Future continuity/export diagnostics. | Continuity source visibility and export redaction proof exists for readiness; backend expansion remains future work. | Medium-high; export must preserve provenance without leaking private source material. |

## Hardening Slices And Proof

Use these slices to keep future PRs reviewable:

1. Diagnostic slice: add or expand repository diagnostics for one row family,
   prove corrupt legacy rows are detected, and keep output content-free.
2. Negative repository slice: add tenant-pair tests showing wrong-community or
   wrong-membership writes fail before or at persistence.
3. Service rollback/idempotency slice: add failure-injection or duplicate-submit
   proof for one workflow family from
   `docs/architecture/transactional-workflow-coverage.md`.
4. Migration/constraint slice: after diagnostics and tests exist, add the fresh
   schema, ordered migration, parity proof, and repair or rejection policy.
5. Operations slice: expose read-only diagnostics only after operator output,
   redaction, exit behavior, and runbook language are approved.

Proof groups:

| Proof Group | Required Coverage |
|---|---|
| Repository | Multiple communities, same global user in different communities, wrong-membership faces, wrong-role memberships, and direct corrupt-row diagnostics. |
| Service | Resolved viewer, explicit actor shape, policy failure, stale command behavior, rollback after late write failure, and duplicate/idempotency behavior where the workflow creates visible rows. |
| Rendered POST | CSRF, tenant-prefixed route, hidden `next` or return path, active-face/staff-role drift, and privacy-safe failure copy. |
| Migration parity | Fresh schema and upgraded schema include the same tables, indexes, triggers, constraints, `PRAGMA foreign_key_check` behavior, and migration ledger version. |
| Operations | Redacted report output, no private story text or applicant notes, director-scoped audit visibility, and non-destructive default behavior. |

Stop and ask before any slice adds schema, migrations, triggers, repair
behavior, public CLI/API/route contracts, persistence lifecycle changes,
concurrency changes, or command protocol changes.

## Session Selection

A persisted selected session identity must identify one active membership owned
by the session user. The selected community and selected membership cannot drift.

The preferred long-term shape is to store one selected membership and derive the
community and user. If redundant columns remain, the database must enforce the
pair with triggers or composite constraints.

## Authorship

Story-visible rows must preserve authorship:

- a post's thread, author membership, and author character belong to one
  community
- a post character belongs to the post membership
- a thread author character belongs to the thread author membership
- staff actor rows name staff membership separately from public character
  context

Wrong-face authorship is a product safety issue, not only a database bug.

## Migration Rules

Schema hardening should land in waves:

1. Add diagnostics and negative tests.
2. Repair or clear invalid existing rows in a migration.
3. Add constraints or triggers.
4. Prove fresh and upgraded schema parity.
5. Run `PRAGMA foreign_key_check` and targeted integrity checks.

Each migration should keep fresh schema and ordered migrations equivalent.
