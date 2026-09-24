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

Review by 2026-10-23. Rows point at GitHub, not at plan files.

| Row | Status | GitHub parent | Review by | Closure |
| --- | --- | --- | --- | --- |
| Spec-driven swarm lifecycle | Complete | saga [#295](https://github.com/lbliii/elbysodic/issues/295), epic [#296](https://github.com/lbliii/elbysodic/issues/296), leaf [#297](https://github.com/lbliii/elbysodic/issues/297), PR [#298](https://github.com/lbliii/elbysodic/pull/298) | 2026-08-17 | Harness on main; saga remains as living process parent |
| Chirp-UI exit | Active | saga [#217](https://github.com/lbliii/elbysodic/issues/217), design [#293](https://github.com/lbliii/elbysodic/issues/293), ADR [0002](../docs/adr/0002-chirp-ui-exit.md), epic [#300](https://github.com/lbliii/elbysodic/issues/300), leaves [#301](https://github.com/lbliii/elbysodic/issues/301) [#302](https://github.com/lbliii/elbysodic/issues/302) [#364](https://github.com/lbliii/elbysodic/issues/364) [#369](https://github.com/lbliii/elbysodic/issues/369) [#371](https://github.com/lbliii/elbysodic/issues/371) [#383](https://github.com/lbliii/elbysodic/issues/383) | 2026-10-23 | `chirp-ui` extra gone; Alpine via Chirp; no new `chirpui-*` |
| Chirp official patterns | Active | sagas [#214](https://github.com/lbliii/elbysodic/issues/214) [#216](https://github.com/lbliii/elbysodic/issues/216), design [#299](https://github.com/lbliii/elbysodic/issues/299), epics [#226](https://github.com/lbliii/elbysodic/issues/226) [#227](https://github.com/lbliii/elbysodic/issues/227) [#228](https://github.com/lbliii/elbysodic/issues/228) [#229](https://github.com/lbliii/elbysodic/issues/229), designs [#373](https://github.com/lbliii/elbysodic/issues/373) [#374](https://github.com/lbliii/elbysodic/issues/374), closed leaf [#372](https://github.com/lbliii/elbysodic/issues/372) | 2026-10-23 | Page actions one route at a time; freeze signal audiences before migration; AuthSpec and Kida 0.12 remain separate |
| Production trust and Railway | Active | saga [#141](https://github.com/lbliii/elbysodic/issues/141), epic [#54](https://github.com/lbliii/elbysodic/issues/54), related epic [#220](https://github.com/lbliii/elbysodic/issues/220), design [#294](https://github.com/lbliii/elbysodic/issues/294), closed design [#375](https://github.com/lbliii/elbysodic/issues/375), leaves [#276](https://github.com/lbliii/elbysodic/issues/276) [#292](https://github.com/lbliii/elbysodic/issues/292) | 2026-10-23 | Single-worker lifecycle seam frozen; #292 is the ready local canary; #276 awaits #294 cleanup and staging smoke; production stays separate |
| Account security AuthSpec | Active | saga [#215](https://github.com/lbliii/elbysodic/issues/215), epic [#224](https://github.com/lbliii/elbysodic/issues/224), design [#374](https://github.com/lbliii/elbysodic/issues/374) | 2026-10-23 | Freeze policy authority and parity before opening implementation leaves |
| Custom-host fallback | Deferred | closed epic [#318](https://github.com/lbliii/elbysodic/issues/318), blocked design [#320](https://github.com/lbliii/elbysodic/issues/320) | later | Reopen or reparent when custom-host or named production-host work enters scope |
| Continuity / scene media / wanted-scene | Deferred | archived plans; no ready leaves | not-now | Provenance, review, and schema design issues exist before implementation |
| Realm Studio 2026 CP | Active | saga [#329](https://github.com/lbliii/elbysodic/issues/329), epic [#330](https://github.com/lbliii/elbysodic/issues/330), design [#331](https://github.com/lbliii/elbysodic/issues/331), ADR [0003](../docs/adr/0003-studio-shell-jobs.md), leaves [#334](https://github.com/lbliii/elbysodic/issues/334)–[#339](https://github.com/lbliii/elbysodic/issues/339) | 2026-10-23 | Studio Today/Shape/Open; Desk Queue/Inbox; Wanted without Applications/Plotting/Discovery; `/studio/operations` aliases `/studio` |
| Story and staff journeys | Complete | saga [#380](https://github.com/lbliii/elbysodic/issues/380), epics [#381](https://github.com/lbliii/elbysodic/issues/381) [#382](https://github.com/lbliii/elbysodic/issues/382) [#404](https://github.com/lbliii/elbysodic/issues/404), leaves [#405](https://github.com/lbliii/elbysodic/issues/405) [#406](https://github.com/lbliii/elbysodic/issues/406) [#407](https://github.com/lbliii/elbysodic/issues/407), PRs [#408](https://github.com/lbliii/elbysodic/pull/408) [#409](https://github.com/lbliii/elbysodic/pull/409) [#410](https://github.com/lbliii/elbysodic/pull/410) | 2026-10-23 | Staff decision and thread-reading epics closed; public-entry epic closed after its leaves merged in #408–#410; CI and mobile/desktop browser review passed |

## Archived 2026-08-17

Twenty-six stale `plans/in-progress/` snapshots moved to
[`archive/2026/`](archive/2026/) with archival notes. They are not
executable specs.
