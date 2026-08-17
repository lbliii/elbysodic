# Plans

GitHub issues are the durable spec store and work DAG. `plans/` is a live
index and evidence queue. Plans are not scratchpads, executable specs, or a
second issue tracker.

See [`docs/plan/issue-lifecycle.md`](../docs/plan/issue-lifecycle.md) and
[`docs/adr/0001-issue-lifecycle.md`](../docs/adr/0001-issue-lifecycle.md).

Use a plan file only when a decision needs continuity that does not yet
have a GitHub saga/epic: steward evidence packets, or a short index note.
Keep ordinary work on GitHub issue bodies.

## Strategy Anchor

All product-facing work should align with
[`docs/product/strategy-spine.md`](../docs/product/strategy-spine.md):

- Realm Studio
- Writer Network
- Continuity Graph

Production trust is a foundation saga, not a fourth pillar. Multiple root
sagas are allowed. Do not flatten them into one evergreen ranking file.

## Lifecycle

Use one of these labels near the top of every remaining plan file:

| Label | Meaning |
|---|---|
| `Active` | Current index row or near-term sequencing. |
| `Deferred` | Worth keeping, but not scheduled. |
| `Superseded` | Replaced by a newer plan, ADR, shipped doc, or GitHub tree. |
| `Complete` | Implemented; retain outcome links. |
| `Evidence` | Review packet or raw input for later synthesis. |

When a plan is no longer live:

- move it to `plans/archive/YYYY/`
- remove it from the Live Index
- leave a short archival note explaining why it moved

`plans/in-progress/` stays empty unless an Evidence packet or a single
current snapshot still needs a file. Git is the historical archive.

## Naming

```text
plans/in-progress/<topic>-<yyyy-mm-dd>.md
```

## Live Index

Review by 2026-08-31. Rows point at GitHub, not at plan files.

| Row | Status | GitHub parent | Review by | Closure |
| --- | --- | --- | --- | --- |
| Production trust and Railway | Active | saga [#141](https://github.com/lbliii/elbysodic/issues/141), epic [#54](https://github.com/lbliii/elbysodic/issues/54), epic [#220](https://github.com/lbliii/elbysodic/issues/220), design [#294](https://github.com/lbliii/elbysodic/issues/294), leaves [#276](https://github.com/lbliii/elbysodic/issues/276) [#292](https://github.com/lbliii/elbysodic/issues/292) | 2026-08-31 | Live Railway smoke recorded or explicit blocked-by owner; pickup leaves have owned paths + machine acceptance |
| Spec-driven swarm lifecycle | Active | saga [#295](https://github.com/lbliii/elbysodic/issues/295), epic [#296](https://github.com/lbliii/elbysodic/issues/296), leaf [#297](https://github.com/lbliii/elbysodic/issues/297) | 2026-08-31 | Templates, labels, thinned plans index, and one closed docs-only leaf |
| Chirp platform currency | Parked | saga [#214](https://github.com/lbliii/elbysodic/issues/214) | later session | No ready leaves until a later planning wave |
| Chirp-UI adopt vs exit | Parked / design | saga [#217](https://github.com/lbliii/elbysodic/issues/217), design [#293](https://github.com/lbliii/elbysodic/issues/293) | later session | Design #293 closed before any #231/#232/#233 leaf is `ready` |
| Account security / hypermedia / tooling | Parked | sagas [#215](https://github.com/lbliii/elbysodic/issues/215) [#216](https://github.com/lbliii/elbysodic/issues/216) [#218](https://github.com/lbliii/elbysodic/issues/218) | later session | Unbeleafed until the later catch-up wave |
| Continuity / scene media / wanted-scene | Deferred | archived plans; no ready leaves | not-now | Provenance, review, and schema design issues exist before implementation |

## Archived 2026-08-17

Twenty-six stale `plans/in-progress/` snapshots moved to
[`archive/2026/`](archive/2026/) with archival notes. They are not
executable specs.
