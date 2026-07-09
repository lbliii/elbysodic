# Production metrics notes

Observability hooks for Elbysodic on Pounce 0.9 / Chirp 0.10 production
launch. Enable with `AppConfig(metrics_enabled=True)` and
`metrics_path="/metrics"` when Railway alpha ops adopt Prometheus scraping.

## HTTP stream gauges (Pounce)

Pounce's built-in `LifecycleCollector` exports:

- `http_streams_active` — gauge of open streaming HTTP responses (SSE,
  `TemplateStream`, chunked HTML). Plotting-room live chat holds one stream per
  connected writer; reload should see this gauge step down as
  `pounce.worker.draining` closes streams before the old generation exits.
- `http_stream_duration_seconds` — histogram of completed stream lifetimes.
  After #242, draining-triggered closes should land in this histogram instead
  of timing out at the worker shutdown window.

Correlate stream duration with `http_connections_active` and
`http_requests_in_flight` during hot reload smoke: a healthy drain shows active
streams returning to zero before the supervisor retires the old worker.

## Plotting-room SSE (#242)

- `AppConfig.sse_close_event="pounce.worker.draining"` — Chirp emits
  `event: pounce.worker.draining` / `data: complete` when a stream ends under
  drain.
- Page wiring: `sse-close="pounce.worker.draining"` on the plotting-room
  `sse-connect` wrapper so htmx-sse reconnects to the new generation.
- Server wiring: `elbysodic.web.worker_draining` signals generators on the
  `pounce.worker.draining` ASGI scope; plotting stream unsubscribes in
  `finally` before the close frame is sent.

Regression proof: `test_plotting_room_sse_closes_cleanly_on_worker_draining` —
reload under an open stream delivers the ready event, queued messages, and the
`pounce.worker.draining` close frame (zero dropped SSE writes).
