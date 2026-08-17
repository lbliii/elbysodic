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
| Spec-driven swarm lifecycle | Complete | saga [#295](https://github.com/lbliii/elbysodic/issues/295), epic [#296](https://github.com/lbliii/elbysodic/issues/296), leaf [#297](https://github.com/lbliii/elbysodic/issues/297), PR [#298](https://github.com/lbliii/elbysodic/pull/298) | 2026-08-17 | Harness on main; saga remains as living process parent |
| Chirp-UI exit | Active | saga [#217](https://github.com/lbliii/elbysodic/issues/217), design [#293](https://github.com/lbliii/elbysodic/issues/293), ADR [0002](../docs/adr/0002-chirp-ui-exit.md), epic [#300](https://github.com/lbliii/elbysodic/issues/300), leaves [#301](https://github.com/lbliii/elbysodic/issues/301) [#302](https://github.com/lbliii/elbysodic/issues/302) | 2026-08-31 | `chirp-ui` extra gone; Alpine via Chirp; no new `chirpui-*` |
| Chirp official patterns | Active | sagas [#214](https://github.com/lbliii/elbysodic/issues/214) [#216](https://github.com/lbliii/elbysodic/issues/216), design [#299](https://github.com/lbliii/elbysodic/issues/299), leaf [#303](https://github.com/lbliii/elbysodic/issues/303) | 2026-08-31 | Page actions one route at a time; signals/AuthSpec/Kida 0.12 still need designs |
| Production trust and Railway | Active | saga [#141](https://github.com/lbliii/elbysodic/issues/141), epic [#54](https://github.com/lbliii/elbysodic/issues/54), epic [#220](https://github.com/lbliii/elbysodic/issues/220), design [#294](https://github.com/lbliii/elbysodic/issues/294), leaves [#276](https://github.com/lbliii/elbysodic/issues/276) [#292](https://github.com/lbliii/elbysodic/issues/292) | 2026-08-31 | Live Railway smoke recorded or explicit blocked-by owner |
| Account security AuthSpec | Parked | saga [#215](https://github.com/lbliii/elbysodic/issues/215), epic [#224](https://github.com/lbliii/elbysodic/issues/224) | later | Own design before any `ready` leaf (Stop And Ask) |
| Continuity / scene media / wanted-scene | Deferred | archived plans; no ready leaves | not-now | Provenance, review, and schema design issues exist before implementation |

## Archived 2026-08-17

Twenty-six stale `plans/in-progress/` snapshots moved to
[`archive/2026/`](archive/2026/) with archival notes. They are not
executable specs.
