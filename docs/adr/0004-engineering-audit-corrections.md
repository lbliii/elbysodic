# ADR 0004: Engineering audit correction contracts

- Status: Accepted
- Date: 2026-09-05
- Authorization: User requested correction of all findings in the September 5 engineering audit.
- Scope: A01–A11 correctness, error handling, composition, query costs, and verification parity.

## Decisions

1. Keep tenant, membership, face, visibility and capability boundaries. Use the existing SQLite transaction mechanism; no schema migration or new runtime dependency is needed.
2. Application services own atomic post/scene changes and command execution. The authoritative reads, mutation, and command result are committed together. Failed commands roll back; repeated successful tokens return the persisted result. Allocate thread slugs inside the write transaction. Preserve existing public facade methods while extracting a small command helper if useful.
3. Blueprint apply fingerprints include the live state of all existing objects affected by the packet. Revalidate under the write transaction before writes. Skip-existing never assigns a foreign-owned face as the importing membership's default or wanted author. Correct and execute the canonical example.
4. Drafts are independent by realm/composer/face, including empty values. Save outgoing state and initialize the incoming face. Associate a submission token with the exact submitted draft snapshot. Successful server redirects carry a `draft_ack` query parameter equal to the existing random idempotency token (edit forms may supply a separate random draft token). Browser acknowledgement removes only that submitted version, retaining newer edits and drafts on failed/network-invalid submissions. Consume the receipt before restore and remove it from the visible URL. This receipt controls local draft cleanup only; it never grants permission or suppresses server validation.
5. Guard browser storage effects; failures leave composition usable with truthful autosave status. Mention lookup applies only the latest query/cursor generation. Add executable JavaScript regressions; Node is a development/test prerequisite, not a runtime application dependency.
6. SSE generators own and await all child tasks on normal completion, exception, cancellation and disconnect. Poll authorized incremental message rows, not full room histories; recheck current access and preserve cross-worker delivery. Batch notification/author lookups and retain privacy/read-state behavior under query budgets.
7. Standard Python 3.14.2 remains supported locally and in production; free-threaded Python is additionally tested in CI. General health smoke validates the expected running interpreter's GIL posture rather than unconditionally requiring free-threading. Explicit free-threaded checks remain available and strict. No production deployment/config change is part of this correction.
8. One canonical developer check definition supplies CLI/task-runner/Make parity for lint, formatting, types, strict application checks, Kida, hypermedia baseline and client behavior tests; the full gate additionally runs tests and contract diff. Required-stage tests are independent of the producer. Changelog selection excludes configured guidance files while malformed real fragments fail.
9. Keep framework lifecycle integration behind an adapter, adopt available supported public seams, and test the adapter with a lifecycle canary. Do not guess an unsupported upstream method or silently upgrade dependencies. If the frozen framework lacks a public seam, eliminate avoidable private references, isolate any essential compatibility bridge, document and test it explicitly.
10. Use focused workflow/read-model extractions while correcting these bugs. No wholesale facade rewrite, new cache infrastructure, feature expansion, or product redesign.

## Proof and collateral

Every leaf includes the relevant fault-injection, concurrency, JavaScript, lifecycle or query-budget regression, plus its affected docs and changelog. Existing route/identity/privacy proofs remain mandatory. Integrated validation runs lint/format/type/template/hypermedia gates, the split coverage suite, process tests on supported runtimes, and focused browser checks for draft submission flows.

Source and tests shared by posting, composer acknowledgement and stream work require explicit carve-outs or integration ordering. Separate leaf branches may be integrated locally for combined validation without authorizing merge or deployment.
