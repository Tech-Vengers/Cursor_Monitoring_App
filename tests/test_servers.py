"""Server inventory unit tests."""

import pytest

from server_store import add_server, validate_hostname_or_ip


@pytest.fixture(autouse=True)
def _mock_ssh_login(monkeypatch):
    monkeypatch.setattr(
        "app.verify_ssh_login",
        lambda host, username, password: None,
    )


def test_validate_rejects_shell_metacharacters():
    with pytest.raises(ValueError):
        validate_hostname_or_ip("host;rm -rf /")
    with pytest.raises(ValueError):
        validate_hostname_or_ip("$(reboot)")


def test_add_edit_delete_server(auth_client):
    add = auth_client.post(
        "/servers",
        data={
            "add-hostname_or_ip": "127.0.0.1",
            "add-ssh_username": "demo",
            "add-ssh_password": "secret",
        },
        follow_redirects=True,
    )
    assert add.status_code == 200
    assert b"127.0.0.1" in add.data
    assert b"demo" in add.data

    from server_store import list_servers

    servers = list_servers()
    assert len(servers) == 1
    server_id = servers[0]["id"]
    assert "ssh_password_token" in servers[0]
    assert "secret" not in str(servers[0])

    edited = auth_client.post(
        f"/servers/{server_id}/edit",
        data={
            "edit-hostname_or_ip": "localhost",
            "edit-ssh_username": "demo",
            "edit-ssh_password": "",
        },
        follow_redirects=True,
    )
    assert edited.status_code == 200
    assert b"localhost" in edited.data

    deleted = auth_client.post(
        f"/servers/{server_id}/delete",
        data={},
        follow_redirects=True,
    )
    assert deleted.status_code == 200
    assert list_servers() == []


def test_add_rejects_failed_ssh(auth_client, monkeypatch):
    def boom(host, username, password):
        raise RuntimeError("SSH authentication failed — check username/password")

    monkeypatch.setattr("app.verify_ssh_login", boom)
    response = auth_client.post(
        "/servers",
        data={
            "add-hostname_or_ip": "127.0.0.1",
            "add-ssh_username": "demo",
            "add-ssh_password": "bad",
        },
        follow_redirects=True,
    )
    assert b"SSH authentication failed" in response.data
    from server_store import list_servers

    assert list_servers() == []


def test_add_invalid_hostname_rejected(auth_client):
    response = auth_client.post(
        "/servers",
        data={
            "add-hostname_or_ip": "bad host",
            "add-ssh_username": "demo",
            "add-ssh_password": "secret",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"invalid" in response.data.lower() or b"Invalid" in response.data


def test_mutate_requires_login(client):
    response = client.post(
        "/servers",
        data={
            "add-hostname_or_ip": "127.0.0.1",
            "add-ssh_username": "demo",
            "add-ssh_password": "secret",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert "/login" in response.headers["Location"]


def test_add_server_helper():
    entry = add_server("127.0.0.1", "demo", "secret", "test-secret-key")
    assert entry["hostname_or_ip"] == "127.0.0.1"
    assert entry["ssh_username"] == "demo"
    assert entry["id"] >= 1
    assert "ssh_password" not in entry
