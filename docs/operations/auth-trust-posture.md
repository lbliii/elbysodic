# Auth Trust Posture Diagnostics

`auth_trust_posture()` reports a redacted deployment checklist for login,
session, demo-account, and entry-flow trust. It is diagnostic-only: it does not
change route access, session resolution, cookie handling, CSRF enforcement, or
writer entry policy.

Never paste secret values, session tokens, token hashes, passwords, raw cookies,
account emails, membership names, private notes, or invite tokens into a smoke
record. Use the diagnostic code, severity, production-blocking posture, and
recommended fix.

## Warning Codes

| Code | Severity | Surface | Production blocking | Meaning | Recommended fix |
|---|---|---|---|---|---|
| `auth.secret_key.too_short` | blocker | session secret | yes | `ELBYSODIC_SECRET_KEY` is missing or shorter than the production minimum. | Set `ELBYSODIC_SECRET_KEY` to a random value with at least 32 characters before serving a shared environment. |
| `auth.demo_mode.seed_passwords` | warning | demo login | yes for `production`/`prod`; staging exception | Seeded demo password hashes are accepted because `ELBYSODIC_DEMO_MODE=1`. | Unset `ELBYSODIC_DEMO_MODE` for real production. Keep it only for staging or seeded demo rehearsals. |
| `auth.development_identity.shortcuts` | note | local identity | no | Local development identity shortcuts are enabled outside production-like environments. | Accept only for local development. Use `ELBYSODIC_ENV=production` or `staging` before shared smoke runs. |

## Informational Codes

| Code | Surface | Meaning | Operator check |
|---|---|---|---|
| `auth.secret_key.configured` | session secret | The current environment has acceptable session-secret posture. | No action for this environment. |
| `auth.secure_cookies.expected` | session cookie | Shared deployments are expected to issue Secure, HttpOnly, SameSite=Lax session cookies through app security config. | Run shared deployments with `ELBYSODIC_ENV=production` or `staging` and debug disabled. |
| `auth.csrf.configured` | mutating forms | Server-rendered mutating forms depend on Chirp CSRF middleware and rendered `csrf_field()` inputs. | Keep POST forms rendering `csrf_field()` and keep CSRF middleware enabled in the app factory. |
| `auth.forwarded_headers.not_trusted` | request origin | Login trust decisions do not depend on spoofable forwarded headers. | Do not add forwarded-header trust without proxy configuration and security tests. |
| `auth.invite_only.entry` | writer entry | Public self-registration is not part of the current auth posture. | Keep new writer entry behind request-access and invitation flows until a separate registration policy is approved. |
| `auth.deployment_environment` | deployment mode | The diagnostic names which `ELBYSODIC_ENV` posture was evaluated. | Use `production` for production and `staging` for shared seeded smoke rehearsals. |

## Local Development Exceptions

Local development may report:

- `auth.development_identity.shortcuts`
- non-secure local session-cookie posture
- seed passwords enabled without demo mode

Those are acceptable for local fixture work only. They are not evidence that a
shared Railway, staging, or production deployment is safe.

## Password Hash Lifecycle

- New real accounts use argon2id through the installed `bengal-chirp[auth]`
  extra.
- Successful logins accept legacy Elbysodic PBKDF2 and Chirp scrypt hashes and
  replace them with argon2id through an atomic compare-and-swap.
- Failed passwords, current argon2id hashes, and `dev-password-hash` demo
  accounts do not trigger replacement writes.
- The compare-and-swap is global-user scoped. It does not modify a writer's
  community memberships, roles, default faces, or active session identity.
- Smoke records name hash formats only. Never record hashes, passwords, email
  addresses, session cookies, or reset material.

Login lookup uses Chirp's enumeration-safe verification contract. An unknown
email still performs one password verification against Chirp's process-wide
decoy hash before returning the same rendered error as a known account with a
wrong password. Elbysodic keeps its legacy PBKDF2 and demo-seed adapters around
that contract until those stored formats disappear. Malformed PBKDF2, scrypt,
argon2, and unsupported hashes fail closed without a session or password write.

Elbysodic does not currently register Chirp `AuditMiddleware` or consume
`authz.permission.denied` events, so the upstream `details["missing"]`
sorted-list shape has no downstream consumer in this release. Issue #277 owns
the metadata-audit adopt/defer decision, and #104 owns any future persistent
staff capability audit trail.

## Request Identity And Session Signing

- `elbysodic_session` remains the database-backed revocation, expiry, and
  selected-identity authority. Its cookie name, schema, and 30-day TTL are
  unchanged.
- One request adapter validates that app session, caches its global account,
  and exposes the account through Chirp `request.user` before membership and
  active-face resolution.
- Chirp signs every newly issued `chirp_session` with SHA-256. Its temporary
  SHA-1 fallback reads a pre-rollout cookie and immediately reissues it with
  SHA-256. Review fallback removal on or after **2026-08-20**, after the 30-day
  app-session window and a production check for remaining legacy cookies.
- Untouched anonymous catalog reads do not receive a Chirp session cookie or
  `Vary: Cookie`. Login, passkey, invite-acceptance, and access-request pages
  intentionally establish CSRF or ceremony session state.

Chirp `AuditMiddleware(level="metadata")` is **deferred** for Studio/director
mutations. Its HTTP event identifies only the global `request.user` plus request
metadata; it does not provide #104's required `community_id`, actor membership,
capability, target family/id, action outcome, durable retention, or
capability-scoped reads. Enabling it now would create a second, non-durable
trail that could be mistaken for the product audit contract. Issue #104 remains
the owner of the tenant-scoped persistent event design; generic request
metadata can be reconsidered there as optional operational telemetry.

## Production Readiness

A launch-readiness record should treat `production_blocking: yes` as a blocker
until remediated or explicitly scoped to a staging rehearsal. A staging record
may include `auth.demo_mode.seed_passwords` only when the smoke run is meant to
exercise seeded demo accounts and the record says so.
