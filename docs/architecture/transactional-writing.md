# Transactional writing

Writing workflows use the repository's SQLite transaction boundary to keep a
writer's visible action and its supporting records together.

## Post and scene edits

A post edit reads the authoritative post, checks edit permission, records the
revision, and changes the body in one transaction. If either write fails, the
old body remains current and no revision is retained.

A scene edit reads the authoritative thread, checks management permission,
updates scene metadata, derives required cast members from existing posts, and
replaces the participant set in one transaction. A failure leaves both the
metadata and participant set unchanged.

## Posting commands

Start-thread and reply submissions execute through the service command helper.
The helper begins an immediate transaction, checks for a completed submission,
reserves a new token, performs the posting workflow, and persists its result
path before commit. A failure rolls back both the story writes and reservation.
A repeated completed token returns its persisted result without running the
posting workflow again. A pending reservation from an older release is
ambiguous because its story writes may have committed before result
persistence failed, so it fails closed and asks the writer to reload instead
of risking a duplicate post. The older `AppServices` command lookup,
reservation, completion, and discard methods remain available for
compatibility.

Thread slug selection happens after the write transaction begins. Concurrent
same-title requests therefore observe earlier committed threads and choose the
next available suffix under the database write lock.

Successful start and reply result paths include `draft_ack` with the submitted
idempotency token. Post edits use their separate random `draft_token`. These
receipts only identify the submitted browser draft for cleanup; authorization
and validation still run on the server.

Regression proof lives in `tests/test_posting_atomicity.py`. It injects late
edit and command-result failures, exercises command replay, and starts
same-title scenes through separate database connections.
