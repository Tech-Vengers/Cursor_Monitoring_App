# Ansible deploy — Cursor Monitoring App

Deploys https://github.com/Tech-Vengers/Cursor_Monitoring_App to hosts listed in inventory.

## Files

| File | Purpose |
|------|---------|
| `inventory.ini` | Target hosts (example with username/password placeholders) |
| `playbook.yml` | Clone repo, venv, deps, `.env`, systemd service |
| `ansible.cfg` | Defaults (inventory path) |
| `templates/` | `.env` and systemd unit templates |

## Before you run

1. Edit `inventory.ini` — replace `CHANGEME` and set a real `ansible_host`.
2. Do **not** commit real passwords.

Example inventory line:

```ini
example-server ansible_host=192.168.1.10 ansible_user=CHANGEME ansible_password=CHANGEME ansible_become_password=CHANGEME
```

## Run

```bash
cd ansible
ansible-playbook playbook.yml
```

Optional: limit to one host:

```bash
ansible-playbook playbook.yml --limit example-server
```

## After deploy

- App path: `/opt/cursor_monitoring_app`
- Service: `cursor-monitoring` (systemd)
- Binds to `0.0.0.0:5005` on the remote host
- URL: `http://<ansible_host>:5005` (example: `http://44.197.202.81:5005`)
- Demo login: `admin` / `admin123`
- Playbook waits for apt/dpkg locks (avoids `unattended-upgr` failures)
