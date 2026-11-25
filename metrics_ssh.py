"""SSH metrics collection — login required; allowlisted commands only."""

from __future__ import annotations

import re
from typing import Any, Callable

import paramiko

# Allowlisted commands only — never interpolate user input into these strings.
CMD_CPU = (
    "grep 'cpu ' /proc/stat | "
    "awk '{u=$2+$4; t=$2+$4+$5; if(t>0) printf \"%.1f\", 100*u/t; else print 0}'"
)
CMD_MEM = "free -b | awk '/^Mem:/ {printf \"%s %s\", $3, $7}'"
CMD_NET = (
    "cat /proc/net/dev | awk -F'[: ]+' "
    "'NR>2 {rx+=$3; tx+=$11} END {printf \"%s %s\", rx+0, tx+0}'"
)
CMD_PORTS = "ss -lntH 2>/dev/null | awk '{print $4}' | sed 's/.*://' | sort -n | uniq"

ALLOWED_COMMANDS = frozenset({CMD_CPU, CMD_MEM, CMD_NET, CMD_PORTS})
SSH_TIMEOUT = 8

RunCommand = Callable[[str, str], str]


def _connect(host: str, username: str, password: str) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=host,
        username=username,
        password=password,
        timeout=SSH_TIMEOUT,
        allow_agent=False,
        look_for_keys=False,
    )
    return client


def verify_ssh_login(host: str, username: str, password: str) -> None:
    """Raise RuntimeError if SSH login fails. Does not log the password."""
    client = None
    try:
        client = _connect(host, username, password)
        # trivial command to prove a working session
        _stdin, stdout, stderr = client.exec_command("echo ok", timeout=SSH_TIMEOUT)
        out = stdout.read().decode("utf-8", errors="replace").strip()
        if out != "ok":
            err = stderr.read().decode("utf-8", errors="replace").strip()
            raise RuntimeError(err or "SSH login succeeded but shell check failed")
    except paramiko.AuthenticationException as exc:
        raise RuntimeError("SSH authentication failed — check username/password") from exc
    except Exception as exc:  # noqa: BLE001
        msg = str(exc) or exc.__class__.__name__
        if "password" in msg.lower():
            msg = "SSH connection failed"
        raise RuntimeError(f"SSH login failed: {msg}") from exc
    finally:
        if client is not None:
            client.close()


def make_ssh_runner(username: str, password: str) -> RunCommand:
    """Build a runner that executes allowlisted commands over SSH."""

    def run(host: str, command: str) -> str:
        if command not in ALLOWED_COMMANDS:
            raise ValueError("command not allowlisted")
        client = None
        try:
            client = _connect(host, username, password)
            _stdin, stdout, stderr = client.exec_command(command, timeout=SSH_TIMEOUT)
            out = stdout.read().decode("utf-8", errors="replace").strip()
            err = stderr.read().decode("utf-8", errors="replace").strip()
            if err and not out:
                raise RuntimeError(err)
            return out
        finally:
            if client is not None:
                client.close()

    return run


def _parse_cpu(raw: str) -> float | None:
    try:
        return round(float(raw.strip()), 1)
    except (TypeError, ValueError):
        return None


def _parse_mem(raw: str) -> dict[str, int | None]:
    parts = raw.split()
    if len(parts) < 2:
        return {"used_bytes": None, "available_bytes": None}
    try:
        return {
            "used_bytes": int(parts[0]),
            "available_bytes": int(parts[1]),
        }
    except ValueError:
        return {"used_bytes": None, "available_bytes": None}


def _parse_net(raw: str) -> dict[str, int | None]:
    parts = raw.split()
    if len(parts) < 2:
        return {"rx_bytes": None, "tx_bytes": None}
    try:
        return {"rx_bytes": int(parts[0]), "tx_bytes": int(parts[1])}
    except ValueError:
        return {"rx_bytes": None, "tx_bytes": None}


def _parse_ports(raw: str) -> list[dict[str, str]]:
    ports: list[dict[str, str]] = []
    for line in raw.splitlines():
        token = line.strip()
        if not token or not re.fullmatch(r"\d{1,5}", token):
            continue
        port_num = int(token)
        if 1 <= port_num <= 65535:
            ports.append({"port": str(port_num), "state": "LISTEN"})
    ports.sort(key=lambda row: int(row["port"]))
    return ports


def format_bytes(num: int | None) -> str:
    if num is None:
        return "—"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(num)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return "—"


def collect_metrics(
    host: str,
    *,
    username: str | None = None,
    password: str | None = None,
    run: RunCommand | None = None,
) -> dict[str, Any]:
    """Collect CPU, memory, network, and listening ports via SSH credentials."""
    result: dict[str, Any] = {
        "host": host,
        "error": None,
        "cpu_percent": None,
        "memory": {"used_bytes": None, "available_bytes": None, "percent": None},
        "network": {"rx_bytes": None, "tx_bytes": None},
        "ports": [],
    }

    if run is None:
        if not username or password is None:
            result["error"] = "SSH username and password are required"
            return result
        runner: RunCommand = make_ssh_runner(username, password)
    else:
        runner = run

    try:
        cpu_raw = runner(host, CMD_CPU)
        mem_raw = runner(host, CMD_MEM)
        net_raw = runner(host, CMD_NET)
        ports_raw = runner(host, CMD_PORTS)
    except Exception as exc:  # noqa: BLE001 — surface connection errors in UI
        msg = str(exc)
        if "password" in msg.lower() or "passphrase" in msg.lower():
            msg = "SSH authentication or connection failed"
        result["error"] = msg
        return result

    cpu = _parse_cpu(cpu_raw)
    mem = _parse_mem(mem_raw)
    net = _parse_net(net_raw)
    ports = _parse_ports(ports_raw)

    used = mem.get("used_bytes")
    avail = mem.get("available_bytes")
    percent = None
    if isinstance(used, int) and isinstance(avail, int) and (used + avail) > 0:
        percent = round(100.0 * used / (used + avail), 1)

    result.update(
        {
            "cpu_percent": cpu,
            "memory": {
                "used_bytes": used,
                "available_bytes": avail,
                "percent": percent,
                "used_display": format_bytes(used if isinstance(used, int) else None),
                "available_display": format_bytes(
                    avail if isinstance(avail, int) else None
                ),
            },
            "network": {
                "rx_bytes": net.get("rx_bytes"),
                "tx_bytes": net.get("tx_bytes"),
                "rx_display": format_bytes(
                    net["rx_bytes"] if isinstance(net.get("rx_bytes"), int) else None
                ),
                "tx_display": format_bytes(
                    net["tx_bytes"] if isinstance(net.get("tx_bytes"), int) else None
                ),
            },
            "ports": ports,
        }
    )
    return result
