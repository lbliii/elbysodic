# Stream read contracts

Plotting-room streams combine a process-local queue with an authorized database
poll. The queue gives same-worker writes low latency. The database cursor is the
cross-worker source of truth: each poll selects messages after the last database
message id, then batches the author and membership context for only those rows.
A local queue event does not advance that cursor, so an earlier row written by
another worker cannot be skipped.

Every poll reloads the membership, role, room, and participant list. An inactive
membership or a writer who is no longer a participant loses access before new
messages are returned. The initial room render remains capped at 100 messages;
later polls have a fixed query cost independent of that history.

The stream generator owns its queue, drain, and timer tasks. Each loop cancels
and awaits all three tasks in a `finally` block, including when the client
disconnects or cancels the generator. During worker drain, queued local events
are flushed, the database is checked once more, and the stream closes.

Notification inbox rendering builds one context for the visible batch. Posts
are selected by notification target id, authors and memberships are selected by
id, and the realm mention roster is loaded once. Unrelated history in a notified
scene is not loaded. Each item keeps the existing target visibility checks and
unread behavior while reusing that context for snippets.

## Chirp and Pounce lifecycle compatibility

Chirp 0.10 exposes public `freeze` and ASGI application seams. Its public `run`
method always serves the Chirp application itself, so it cannot launch the
draining-aware ASGI wrapper required by Pounce 0.9. The compatibility bridge is
isolated in `pounce_railway.run_chirp_asgi_adapter`: it freezes through the public
method, then uses Chirp's private `_server` launcher to serve the wrapper. A
pre-0.10 `_ensure_frozen` fallback remains solely for the existing lifecycle
canary.

The adapter test verifies that public freeze happens first and that the wrapper,
host, port, and lifecycle collector reach the launcher. Re-evaluate and remove
the private launcher bridge whenever Chirp changes version or adds a supported
wrapped-application startup API.
