# Linux Monitor (Demo)

Local demo web app for viewing Linux server metrics (CPU, memory, network, ports) in a **read-only** UI — no day-to-day SSH login for checks.

Spec: [docs/requirements.md](docs/requirements.md) · Tasks: [docs/TODO.md](docs/TODO.md) · Security: [docs/security.md](docs/security.md)

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set SECRET_KEY
python app.py
```

Open [http://127.0.0.1:5005](http://127.0.0.1:5005).

### Demo login

- Username: `admin`
- Password: `admin123` (stored hashed; plaintext is not saved)

Auth is required for all monitoring pages.

### Add a server (SSH login required)

1. Sign in to the dashboard (`admin` / `admin123`).
2. Enter **Hostname / IP**, **SSH username**, and **SSH password**.
3. Click **Add server** — the app **verifies SSH login first**; the host is saved only if SSH succeeds.
4. Use **Update** / **Delete** on the same page (POST only). On update, leave password blank to keep the existing one (SSH is re-checked).

Inventory is stored in `data/servers.json` (gitignored). SSH passwords are stored encrypted with `SECRET_KEY` (demo only — not for production).

### Metrics (via SSH)

CPU %, memory used/available, network RX/TX byte counters from `/proc/net/dev`, and listening TCP ports (`ss`), collected over **SSH** with the saved credentials and allowlisted commands.

Dashboard auto-refreshes every **30 seconds**.

**Note:** The target host must allow SSH password authentication (or accept the credentials you enter).

## Run tests

```bash
pytest
```

Lint: `ruff check .`

## CI

GitHub Actions (`.github/workflows/ci.yml`) installs dependencies, runs `ruff`, and runs `pytest` on push/PR to `main`. No secrets are stored in the workflow file.

## Notes

- Metrics UI is **read-only** (display only).
- App binds to **127.0.0.1:5005** (localhost only).
- Do not commit secrets (`.env` is gitignored). Set `SECRET_KEY` via `.env`.
