Railway deploy healthchecks now target `/ready` (SQLite-backed readiness) instead of `/health`; the app keeps `/health` as a middleware-aware alias while Chirp probes live at `/livez` and `/ready`.
