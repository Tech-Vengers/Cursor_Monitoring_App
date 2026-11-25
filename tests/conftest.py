"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from app import create_app
from server_store import SERVERS_FILE, _ensure_store


@pytest.fixture()
def app(tmp_path, monkeypatch):
    store = tmp_path / "servers.json"
    monkeypatch.setattr("server_store.SERVERS_FILE", store)
    monkeypatch.setattr("server_store.DATA_DIR", tmp_path)
    _ensure_store()

    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key-not-for-production",
            "WTF_CSRF_ENABLED": False,
        }
    )
    yield application
    if SERVERS_FILE.exists() and str(SERVERS_FILE).startswith(str(tmp_path)):
        pass


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_client(client):
    client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=True,
    )
    return client
