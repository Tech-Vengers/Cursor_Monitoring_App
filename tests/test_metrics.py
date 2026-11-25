"""Metrics parsing / collection unit tests (mocked SSH runner)."""

from metrics_ssh import collect_metrics, format_bytes, verify_ssh_login


def test_collect_metrics_with_mock_runner():
    responses = {
        "cpu": "12.5",
        "mem": "1073741824 2147483648",
        "net": "1000 2000",
        "ports": "22\n5001\n80",
    }

    def fake_run(host: str, command: str) -> str:
        assert host == "127.0.0.1"
        if "/proc/stat" in command:
            return responses["cpu"]
        if "free -b" in command:
            return responses["mem"]
        if "/proc/net/dev" in command:
            return responses["net"]
        if "ss -lntH" in command:
            return responses["ports"]
        raise AssertionError(f"unexpected command: {command}")

    data = collect_metrics("127.0.0.1", run=fake_run)
    assert data["error"] is None
    assert data["cpu_percent"] == 12.5
    assert data["memory"]["used_bytes"] == 1073741824
    assert data["network"]["rx_bytes"] == 1000
    assert data["network"]["tx_bytes"] == 2000
    assert [p["port"] for p in data["ports"]] == ["22", "80", "5001"]


def test_collect_metrics_requires_credentials():
    data = collect_metrics("127.0.0.1")
    assert data["error"] == "SSH username and password are required"


def test_collect_metrics_ssh_failure():
    def boom(host: str, command: str) -> str:
        raise RuntimeError("connection refused")

    data = collect_metrics("127.0.0.1", run=boom)
    assert data["error"] == "connection refused"
    assert data["cpu_percent"] is None


def test_format_bytes():
    assert format_bytes(None) == "—"
    assert format_bytes(512) == "512 B"
    assert "KB" in format_bytes(2048)


def test_ports_ignore_non_numeric():
    def fake_run(host: str, command: str) -> str:
        if "ss -lntH" in command:
            return "22\nabc\n99999\n443"
        if "/proc/stat" in command:
            return "1.0"
        if "free -b" in command:
            return "1 1"
        return "0 0"

    data = collect_metrics("localhost", run=fake_run)
    ports = [p["port"] for p in data["ports"]]
    assert "22" in ports
    assert "443" in ports
    assert "abc" not in ports
    assert "99999" not in ports


def test_verify_ssh_login_maps_auth_errors(monkeypatch):
    import paramiko

    class FakeClient:
        def set_missing_host_key_policy(self, _policy):
            return None

        def connect(self, **kwargs):
            raise paramiko.AuthenticationException("bad")

        def close(self):
            return None

    monkeypatch.setattr("metrics_ssh.paramiko.SSHClient", FakeClient)
    try:
        verify_ssh_login("127.0.0.1", "u", "p")
        assert False, "expected failure"
    except RuntimeError as exc:
        assert "authentication failed" in str(exc).lower()
