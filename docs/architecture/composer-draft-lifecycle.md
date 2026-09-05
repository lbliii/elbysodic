# Composer draft lifecycle

Status: accepted implementation contract

Elbysodic keeps posting drafts in browser storage so a reload, validation error,
or network interruption does not discard long-form writing. The storage record
is scoped by community/object composer key and face ID:

```text
elbysodic:draft:<composer-kind>:<community-id>:<object-id>:<face-id>
```

Each face owns a complete `{body, title}` snapshot. Empty strings are stored as
intentional values and differ from a missing record. On a face switch, the
composer first saves the outgoing snapshot, then restores the incoming face's
record or initializes an empty draft when none exists. Initial server-rendered
values remain the baseline when the composer first mounts, including values
returned after server validation.

Submitting a form saves the current snapshot with its random submission token.
The browser does not delete the draft at submit time. A successful server
redirect includes `draft_ack=<token>` in the destination URL; failed validation
and failed requests do not include a receipt. The global composer script
consumes the receipt before any destination composer restores state, scans all
composer records so redirects may change draft keys, and deletes a record only
when its token and current `{body, title}` exactly match the submitted snapshot.
If the text changed after submission, the newer record remains. The script then
removes `draft_ack` from the visible URL while preserving other query parameters
and the fragment.

Storage and History APIs are browser effects rather than posting authority.
Access failures must leave the textarea, face selector, preview, validation, and
submission usable. The status reports `Draft autosave unavailable.` instead of
claiming that a draft was saved. In-memory face snapshots keep identity switches
independent for the life of the page even when persistent storage is unavailable.
The receipt only controls local cleanup; it does not grant permission, bypass
validation, or alter server idempotency.

Mention searches use monotonically increasing request generations. Only the
latest generation may update results, selection, open state, or loading state,
so a slow older response cannot replace suggestions for newer text or reopen a
picker the writer dismissed.
