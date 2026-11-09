import csv
import json

from src.report_generator import ReportGenerator


def sample_results():

    return [
        {
            "server_name": "server-01",
            "hostname": "192.168.1.10",
            "status": "SUCCESS",
            "metrics": {
                "cpu": {"usage": 25.0, "status": "HEALTHY"},
                "memory": {"usage": 40.0, "status": "HEALTHY"},
                "disk": {"usage": 60.0, "status": "HEALTHY"},
            },
        },
        {
            "server_name": "server-02",
            "hostname": "192.168.1.20",
            "status": "UNREACHABLE",
            "error": "Connection timed out",
        },
    ]


def test_generate_json_report(tmp_path):

    generator = ReportGenerator(tmp_path)

    results = sample_results()

    report_file = tmp_path / "test_report.json"

    generator.generate_json_report(results, report_file)

    with open(report_file, encoding="utf-8") as file:
        report = json.load(file)

    assert report["total_servers"] == 2
    assert report["successful"] == 1
    assert report["failed"] == 1
    assert len(report["servers"]) == 2


def test_generate_csv_report(tmp_path):

    generator = ReportGenerator(tmp_path)

    results = sample_results()

    report_file = tmp_path / "test_report.csv"

    generator.generate_csv_report(results, report_file)

    with open(report_file, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 2

    assert rows[0]["server_name"] == "server-01"
    assert rows[0]["cpu_usage"] == "25.0"

    assert rows[1]["server_name"] == "server-02"
    assert rows[1]["status"] == "UNREACHABLE"
    assert rows[1]["error"] == "Connection timed out"


def test_generate_both_reports(tmp_path):

    generator = ReportGenerator(tmp_path)

    results = sample_results()

    files = generator.generate_reports(results)

    assert files["json_report"]
    assert files["csv_report"]

    assert (tmp_path / files["json_report"].split("/")[-1]).exists()
    assert (tmp_path / files["csv_report"].split("/")[-1]).exists()
