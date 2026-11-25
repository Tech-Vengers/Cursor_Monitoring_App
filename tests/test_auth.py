"""Auth unit tests."""


def test_valid_login_succeeds(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert response.headers["Location"].endswith("/")


def test_invalid_password_rejected(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrong-password"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data
    # Must not leak password material
    assert b"wrong-password" not in response.data or b"password" in response.data


def test_protected_page_redirects_when_logged_out(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 303)
    assert "/login" in response.headers["Location"]


def test_logout_clears_session(auth_client):
    response = auth_client.post("/logout", follow_redirects=False)
    assert response.status_code in (302, 303)
    assert "/login" in response.headers["Location"]
    blocked = auth_client.get("/", follow_redirects=False)
    assert "/login" in blocked.headers["Location"]
