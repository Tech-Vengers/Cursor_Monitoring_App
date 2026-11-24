# TODO: Demo Linux Server Monitoring

Small increments for AI-assisted development. Check items off as you complete them.  
Aligns with [requirements.md](requirements.md). Local demo only (port **5001**).

---

## Phase 0 — Project initialization and Basic UI

### 0.1 Scaffold project
- [x] Create minimal layout: `app.py`, `requirements.txt`, `templates/`, `static/css/`, `tests/`, `docs/`
- [x] Add `.gitignore` (`.venv/`, `__pycache__/`, `.env`, `*.pyc`, IDE junk)
- [x] **Security:** Do not commit secrets; keep future credentials out of git
- [x] **Docs:** Short root `README.md` — what the demo is + link to `docs/requirements.md`

### 0.2 Virtualenv and Flask hello
- [x] Pin Flask (and later deps) in `requirements.txt`
- [x] App binds to `127.0.0.1:5001` (localhost only)
- [x] **Security:** Bind to localhost, not `0.0.0.0`, for local demo
- [x] **Docs:** Add “Run locally” 4-line steps to `README.md`

### 0.3 Basic UI shell
- [x] Base template + one CSS file (clean layout, tables / % bars ready)
- [x] Placeholder dashboard page (static labels: CPU, Memory, Network, Ports)
- [x] **Security:** No inline user-controlled HTML yet; keep templates escaping on
- [x] **Docs:** Note UI is read-only for metrics in `README.md` or `docs/requirements.md`

---

## Phase 1 — Sign-in and unit tests

### 1.1 Password hashing
- [ ] Add `bcrypt` (or Werkzeug password hashing) dependency
- [ ] Store default `admin` password **hashed** only (seed `admin123` for demo)
- [ ] **Security:** Never store plaintext password; hash at seed time
- [ ] **Docs:** Document default demo login in `README.md` (`admin` / `admin123`)

### 1.2 Login / logout routes
- [ ] Login form page + POST handler
- [ ] Session-based auth after successful login
- [ ] Logout clears session
- [ ] **Security:** Use Flask secret key from env / local `.env` (not hardcoded in git); set `SESSION_COOKIE_HTTPONLY`
- [ ] **Docs:** Document `SECRET_KEY` / `.env.example` (no real secrets)

### 1.3 Protect routes
- [ ] Redirect unauthenticated users to login
- [ ] Dashboard / metrics require login
- [ ] **Security:** Deny-by-default on app routes except login + static
- [ ] **Docs:** Note “auth required for all monitoring pages”

### 1.4 Unit tests for auth
- [ ] Add `pytest` (+ Flask test client) to `requirements.txt` or `requirements-dev.txt`
- [ ] Test: valid login succeeds
- [ ] Test: invalid password rejected
- [ ] Test: protected page redirects when logged out
- [ ] **Security:** Tests must not print or assert plaintext hashes carelessly in logs
- [ ] **Docs:** Add “Run tests” one-liner: `pytest`

---

## Phase 2 — CI/CD (GitHub Actions)

### 2.1 Minimal CI workflow
- [ ] Add `.github/workflows/ci.yml`
- [ ] On push/PR: install deps, run `pytest`
- [ ] Use Python version matching local demo
- [ ] **Security:** No secrets in workflow YAML; use `GITHUB_TOKEN` defaults only if needed
- [ ] **Docs:** One paragraph in `README.md` — “CI runs tests on PR”

### 2.2 Lint / basic hygiene (optional small step)
- [ ] Optional: `ruff` or `flake8` in CI
- [ ] **Security:** Fail CI on obvious secret patterns if a simple check is added later
- [ ] **Docs:** Mention lint command if added

---

## Phase 3 — Server inventory (CRUD)

### 3.1 Data store for servers
- [ ] Minimal storage (SQLite or JSON file) for server entries: `id`, `hostname_or_ip`
- [ ] **Security:** Validate hostname/IP format; reject shell metacharacters
- [ ] **Docs:** Document storage file path and that demo is single-host focused

### 3.2 Add server
- [ ] Form/control on the one-page UI to add hostname/IP
- [ ] Persist and show in list
- [ ] **Security:** CSRF-safe form pattern (Flask-WTF or token); require login
- [ ] **Docs:** Screenshot or short “Add server” steps in `README.md`

### 3.3 Edit and delete server
- [ ] Edit hostname/IP
- [ ] Delete with confirm (simple confirm dialog or POST)
- [ ] Unit tests: add / edit / delete (happy path + invalid input)
- [ ] **Security:** Only authenticated users; POST for mutating actions (no GET delete)
- [ ] **Docs:** Update acceptance notes for CRUD

---

## Phase 4 — Metrics collection (SSH agentless, local host)

### 4.1 SSH helper (localhost)
- [ ] Add Paramiko (or similar) dependency
- [ ] Connect to configured local hostname/IP over SSH
- [ ] **Security:** Prefer SSH keys; never log passwords; timeout connections; no `shell=True` subprocess for remote
- [ ] **Docs:** Document local SSH prerequisite (key-based localhost access)

### 4.2 CPU and memory
- [ ] Collect CPU % and memory used/available via remote commands over SSH
- [ ] Render as read-only table / % bars
- [ ] Unit tests with mocked SSH responses
- [ ] **Security:** Allowlist commands; parse output safely; treat metrics as untrusted text (escape in templates)
- [ ] **Docs:** List exact metrics shown

### 4.3 Network in/out
- [ ] Collect network RX/TX (simple rates or counters)
- [ ] Show on same page
- [ ] Mocked unit test
- [ ] **Security:** Same allowlisted command approach
- [ ] **Docs:** Note how network numbers are derived (brief)

### 4.4 Listening / open ports
- [ ] Collect listening ports (e.g. `ss`/`netstat` style via SSH)
- [ ] Read-only table on the page
- [ ] Mocked unit test
- [ ] **Security:** Escape port/process strings; do not execute returned data
- [ ] **Docs:** Clarify “ports” = listening/open on the host

---

## Phase 5 — One-page UX polish

### 5.1 Single dashboard page
- [ ] Combine: login gate → one page with server CRUD + all metrics
- [ ] Metrics remain non-editable
- [ ] **Security:** Re-check auth on page and any metrics API/partial
- [ ] **Docs:** Match UX steps in PRD §8

### 5.2 Auto-refresh (30 seconds)
- [ ] Meta-refresh or light JS poll every 30s
- [ ] **Security:** Refresh must not expose data without session; no open CORS
- [ ] **Docs:** Note 30s refresh in `README.md`

---

## Phase 6 — Hardening pass (demo-minimal)

### 6.1 Security checklist
- [ ] Secret key not committed
- [ ] Password hashed
- [ ] Localhost bind on 5001
- [ ] Input validation on hostname/IP
- [ ] Mutating actions via POST + auth
- [ ] Template auto-escaping verified
- [ ] **Docs:** Add `docs/security.md` with this short checklist

### 6.2 Final demo verification
- [ ] Manual pass against PRD acceptance criteria
- [ ] All unit tests green locally and in CI
- [ ] **Docs:** Mark acceptance criteria checkboxes in `docs/requirements.md` when verified

---

## Suggested implement order (AI sessions)

| Session | Do next |
|---------|---------|
| 1 | Phase 0 (init + basic UI) |
| 2 | Phase 1 (sign-in + auth tests) |
| 3 | Phase 2 (GitHub Actions CI) |
| 4 | Phase 3 (server CRUD) |
| 5 | Phase 4 (metrics via SSH, one metric group at a time) |
| 6 | Phase 5–6 (refresh + hardening + docs) |

Work **one checkbox group** per AI turn when possible.
