# PRD: Demo Linux Server Monitoring (Local)

## 1. Overview

Local demo web app so internal L1/L2/L3 and app teams can view live Linux server metrics without SSH login.

**Scope:** Single host (the machine where the app runs). Flask UI on port **5005**. Python + venv. Not for production.

## 2. Problem

Today, checking CPU, memory, network, and ports means logging into each server. This demo shows the same data in a read-only browser UI.

## 3. Users

| Role | Access |
|------|--------|
| Internal L1 / L2 / L3, infra & app teams | Sign in as `admin`, view metrics, manage server inventory |

Single user: **admin** (no multi-user / RBAC).

## 4. Goals

- One-page UI with live metrics (auto-refresh every **30 seconds**)
- Metrics read-only
- Add / edit / delete monitored Linux server entries
- Collect metrics via **SSH (agentless)** from the local machine
- Simple local run: venv + `python`

## 5. Non-Goals (out of scope)

Alerts, historical charts, Windows hosts, multi-user RBAC, HTTPS, cloud deploy, Docker.

## 6. Features

### F1 — Read-only metrics UI

- One page showing all metrics for the monitored host
- Attractive, simple Flask frontend (tables and % bars are enough)
- Metrics display only; no user edits to metric values
- Auto-refresh every **30 seconds**

**Metrics**

| Metric | Display |
|--------|---------|
| CPU | Usage % |
| Memory | Used / available (and % if useful) |
| Network | In / out rates |
| Ports | Listening / open ports |

### F2 — Sign-in

- Default username: `admin`
- Password stored as a **hash** (e.g. bcrypt)
- Demo default password: `admin123` (changeable later if needed)
- Unauthenticated users cannot view metrics or manage servers

### F3 — Server inventory (local Linux)

- Provision to **add**, **edit**, and **delete** Linux server entries
- Required field on add/edit: **hostname / IP**
- Demo targets **this machine only** (localhost / local IP)
- Collection method: **SSH agentless** from the Flask app

## 7. Tech Stack

| Layer | Choice |
|-------|--------|
| Language | Python |
| Web | Flask |
| UI | Server-rendered templates + light CSS (attractive, minimal) |
| Auth | Session login; hashed password |
| Metrics | SSH to local host; parse standard Linux commands / tools |
| Run | Local venv; app binds to port **5005** |

## 8. UX (minimal)

1. Open login → sign in as `admin`
2. Land on **one page**: server list controls + live metrics
3. Add / edit / delete server by hostname/IP
4. Metrics refresh every 30s without full manual reload (or simple page poll)

## 9. Local run (minimal)

```bash
cd <project>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: `http://127.0.0.1:5005`  

Login: `admin` / `admin123`

## 10. Acceptance criteria (demo)

- [x] Login works with `admin` and hashed password check
- [x] Wrong password rejected
- [x] After login, one page shows CPU %, memory used/available, network in/out, listening/open ports
- [x] Metrics refresh about every 30 seconds
- [x] Can add, edit, and delete a server entry by hostname/IP
- [x] Metrics are read-only in the UI
- [x] App runs locally on port 5005 via venv + Python

## 11. Assumptions

- App listens on port **5005** (updated from earlier 5001); port *metrics* mean listening/open ports on the monitored host
- Question 12 (charts vs bars) defaulted to **tables / % bars** for a minimal demo
- SSH to localhost is available for agentless collection in this environment
