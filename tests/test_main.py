from main import get_health_status


def test_cpu_healthy():
    assert get_health_status(50, 70, 90) == "HEALTHY"


def test_cpu_warning():
    assert get_health_status(75, 70, 90) == "WARNING"


def test_cpu_critical():
    assert get_health_status(95, 70, 90) == "CRITICAL"


def test_exact_warning_threshold():
    assert get_health_status(70, 70, 90) == "WARNING"


def test_exact_critical_threshold():
    assert get_health_status(90, 70, 90) == "CRITICAL"
