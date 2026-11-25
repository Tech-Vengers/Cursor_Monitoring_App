"""JSON-backed server inventory (SSH credentials required)."""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path

from itsdangerous import BadSignature, URLSafeSerializer

DATA_DIR = Path(__file__).resolve().parent / "data"
SERVERS_FILE = DATA_DIR / "servers.json"

# Hostname labels or IPv4; reject shell metacharacters
_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)"
    r"(?:localhost|"
    r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?|"
    r"(?:\d{1,3}\.){3}\d{1,3})$"
)
_UNSAFE = re.compile(r"[;|&`$<>(){}[\]\\'\"\n\r\t ]")
_USER_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")

_lock = threading.Lock()


def validate_hostname_or_ip(value: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError("Hostname/IP is required")
    if _UNSAFE.search(cleaned):
        raise ValueError("Hostname/IP contains invalid characters")
    if not _HOSTNAME_RE.match(cleaned):
        raise ValueError("Invalid hostname or IP format")
    return cleaned


def validate_ssh_username(value: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError("SSH username is required")
    if not _USER_RE.match(cleaned):
        raise ValueError("Invalid SSH username")
    return cleaned


def validate_ssh_password(value: str) -> str:
    if value is None or value == "":
        raise ValueError("SSH password is required")
    if len(value) > 256:
        raise ValueError("SSH password is too long")
    return value


def _serializer(secret_key: str) -> URLSafeSerializer:
    return URLSafeSerializer(secret_key, salt="ssh-password-v1")


def encrypt_password(password: str, secret_key: str) -> str:
    return _serializer(secret_key).dumps(password)


def decrypt_password(token: str, secret_key: str) -> str:
    try:
        return _serializer(secret_key).loads(token)
    except BadSignature as exc:
        raise ValueError("Could not decrypt stored SSH password") from exc


def _ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SERVERS_FILE.exists():
        SERVERS_FILE.write_text("[]\n", encoding="utf-8")


def list_servers() -> list[dict]:
    _ensure_store()
    with _lock:
        return json.loads(SERVERS_FILE.read_text(encoding="utf-8"))


def _write(servers: list[dict]) -> None:
    _ensure_store()
    with _lock:
        SERVERS_FILE.write_text(
            json.dumps(servers, indent=2) + "\n", encoding="utf-8"
        )


def add_server(
    hostname_or_ip: str,
    ssh_username: str,
    ssh_password: str,
    secret_key: str,
) -> dict:
    host = validate_hostname_or_ip(hostname_or_ip)
    user = validate_ssh_username(ssh_username)
    password = validate_ssh_password(ssh_password)
    servers = list_servers()
    next_id = max((s["id"] for s in servers), default=0) + 1
    entry = {
        "id": next_id,
        "hostname_or_ip": host,
        "ssh_username": user,
        "ssh_password_token": encrypt_password(password, secret_key),
    }
    servers.append(entry)
    _write(servers)
    return {
        "id": entry["id"],
        "hostname_or_ip": entry["hostname_or_ip"],
        "ssh_username": entry["ssh_username"],
    }


def update_server(
    server_id: int,
    hostname_or_ip: str,
    ssh_username: str,
    ssh_password: str | None,
    secret_key: str,
) -> dict:
    host = validate_hostname_or_ip(hostname_or_ip)
    user = validate_ssh_username(ssh_username)
    servers = list_servers()
    for server in servers:
        if server["id"] == server_id:
            server["hostname_or_ip"] = host
            server["ssh_username"] = user
            if ssh_password:
                server["ssh_password_token"] = encrypt_password(
                    validate_ssh_password(ssh_password), secret_key
                )
            elif not server.get("ssh_password_token"):
                raise ValueError("SSH password is required")
            _write(servers)
            return {
                "id": server["id"],
                "hostname_or_ip": server["hostname_or_ip"],
                "ssh_username": server["ssh_username"],
            }
    raise KeyError(f"Server id {server_id} not found")


def delete_server(server_id: int) -> None:
    servers = list_servers()
    new_servers = [s for s in servers if s["id"] != server_id]
    if len(new_servers) == len(servers):
        raise KeyError(f"Server id {server_id} not found")
    _write(new_servers)


def get_server(server_id: int) -> dict | None:
    for server in list_servers():
        if server["id"] == server_id:
            return server
    return None


def get_ssh_password(server: dict, secret_key: str) -> str:
    token = server.get("ssh_password_token")
    if not token:
        raise ValueError("Server has no SSH password — re-add the server")
    return decrypt_password(token, secret_key)
