from unittest.mock import Mock

from src.system_metrics import SystemMetrics


def test_cpu_usage():

    ssh = Mock()

    ssh.execute_command.side_effect = [
        {"exit_code": 0, "stdout": "cpu 100 0 50 800 50 0 0 0", "stderr": ""},
        {"exit_code": 0, "stdout": "cpu 120 0 60 820 50 0 0 0", "stderr": ""},
    ]

    metrics = SystemMetrics(ssh)

    # Replace the one-second wait to keep tests fast.
    import src.system_metrics as system_metrics_module

    system_metrics_module.time.sleep = Mock()

    result = metrics.get_cpu_usage()

    assert result == 60


def test_memory_usage():

    ssh = Mock()

    ssh.execute_command.return_value = {
        "exit_code": 0,
        "stdout": (
            "               total        used        free "
            "shared  buff/cache   available\n"
            "Mem:     1000000000   600000000   100000000 "
            "10000000   300000000   400000000\n"
        ),
        "stderr": "",
    }

    metrics = SystemMetrics(ssh)

    result = metrics.get_memory_usage()

    assert result == 60.0


def test_disk_usage():

    ssh = Mock()

    ssh.execute_command.return_value = {
        "exit_code": 0,
        "stdout": (
            "Filesystem 1024-blocks Used Available Capacity Mounted on\n"
            "/dev/root 1000000 700000 300000 70% /\n"
        ),
        "stderr": "",
    }

    metrics = SystemMetrics(ssh)

    result = metrics.get_disk_usage()

    assert result == 70.0
