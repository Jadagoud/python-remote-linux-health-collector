from unittest.mock import Mock, patch

import paramiko

from main import collect_server

THRESHOLDS = {
    "cpu": {"warning": 70, "critical": 90},
    "memory": {"warning": 75, "critical": 90},
    "disk": {"warning": 80, "critical": 90},
}

SERVER = {
    "name": "test-server",
    "host": "192.168.1.10",
    "username": "ubuntu",
    "key_file": "/tmp/test.pem",
}


@patch("main.SSHConnection")
def test_authentication_failure(mock_ssh):

    ssh = mock_ssh.return_value

    ssh.connect.side_effect = paramiko.AuthenticationException("Authentication failed")

    result = collect_server(SERVER, THRESHOLDS, Mock())

    assert result["status"] == "AUTHENTICATION_FAILED"
    ssh.close.assert_called_once()


@patch("main.SSHConnection")
def test_unreachable_server(mock_ssh):

    ssh = mock_ssh.return_value

    ssh.connect.side_effect = TimeoutError("Connection timed out")

    result = collect_server(SERVER, THRESHOLDS, Mock())

    assert result["status"] == "UNREACHABLE"
    ssh.close.assert_called_once()


@patch("main.SSHConnection")
def test_ssh_connection_failure(mock_ssh):

    ssh = mock_ssh.return_value

    ssh.connect.side_effect = paramiko.SSHException("SSH protocol error")

    result = collect_server(SERVER, THRESHOLDS, Mock())

    assert result["status"] == "CONNECTION_FAILED"
    ssh.close.assert_called_once()


@patch("main.SystemMetrics")
@patch("main.SSHConnection")
def test_metric_collection_failure(mock_ssh, mock_metrics):

    ssh = mock_ssh.return_value

    metrics = mock_metrics.return_value

    ssh.connect.return_value = None

    metrics.get_cpu_usage.side_effect = RuntimeError("CPU metrics unavailable")

    result = collect_server(SERVER, THRESHOLDS, Mock())

    assert result["status"] == "MONITORING_FAILED"
    ssh.close.assert_called_once()
