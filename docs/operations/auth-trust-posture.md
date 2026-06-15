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

## Production Readiness

A launch-readiness record should treat `production_blocking: yes` as a blocker
until remediated or explicitly scoped to a staging rehearsal. A staging record
may include `auth.demo_mode.seed_passwords` only when the smoke run is meant to
exercise seeded demo accounts and the record says so.
