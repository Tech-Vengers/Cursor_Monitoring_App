# Linux Monitor (Demo)

Local demo web app for viewing Linux server metrics (CPU, memory, network, ports) in a **read-only** UI — no SSH login needed for day-to-day checks.

Spec: [docs/requirements.md](docs/requirements.md) · Tasks: [docs/TODO.md](docs/TODO.md)

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5001](http://127.0.0.1:5001).

## Notes

- Metrics UI is **read-only** (display only; no editing of values).
- App binds to **127.0.0.1:5001** (localhost only).
- Do not commit secrets (`.env` is gitignored).
