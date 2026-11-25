# Security checklist (local demo)

Minimal hardening for the Linux Monitor demo. Not a production security review.

- [x] `SECRET_KEY` from environment / `.env` (see `.env.example`); not committed
- [x] Default `admin` password stored as **hash only** (Werkzeug); plaintext never persisted
- [x] App binds to `127.0.0.1:5005` (localhost only)
- [x] Hostname/IP validated; shell metacharacters rejected
- [x] Mutating actions use **POST** + login (+ CSRF when enabled)
- [x] Jinja template auto-escaping left on; metrics treated as text
- [x] SSH uses allowlisted commands; password auth verified before a server is added
- [x] SSH passwords encrypted at rest with `SECRET_KEY` (local demo file; never logged)
- [x] Session cookie `HttpOnly` (+ `SameSite=Lax`)
- [x] CI workflow contains no repository secrets

## Auth note

Monitoring pages require sign-in. Demo login is documented in the README only for local use — change the seeded password before any shared deployment.
