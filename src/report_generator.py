import csv
import json
from datetime import UTC, datetime
from pathlib import Path


class ReportGenerator:
    def __init__(self, report_directory="reports"):
        self.report_directory = Path(report_directory)
        self.report_directory.mkdir(parents=True, exist_ok=True)

    def generate_reports(self, results):

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

        json_file = self.report_directory / f"health_report_{timestamp}.json"

        csv_file = self.report_directory / f"health_report_{timestamp}.csv"

        self.generate_json_report(results, json_file)
        self.generate_csv_report(results, csv_file)

        return {"json_report": str(json_file), "csv_report": str(csv_file)}

    def generate_json_report(self, results, file_path):

        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "total_servers": len(results),
            "successful": sum(1 for result in results if result["status"] == "SUCCESS"),
            "failed": sum(1 for result in results if result["status"] != "SUCCESS"),
            "servers": results,
        }

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(report, file, indent=4)

    def generate_csv_report(self, results, file_path):

        fieldnames = [
            "server_name",
            "hostname",
            "status",
            "cpu_usage",
            "cpu_status",
            "memory_usage",
            "memory_status",
            "disk_usage",
            "disk_status",
            "error",
        ]

        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()

            for result in results:
                metrics = result.get("metrics", {})

                writer.writerow(
                    {
                        "server_name": result.get("server_name"),
                        "hostname": result.get("hostname"),
                        "status": result.get("status"),
                        "cpu_usage": metrics.get("cpu", {}).get("usage"),
                        "cpu_status": metrics.get("cpu", {}).get("status"),
                        "memory_usage": metrics.get("memory", {}).get("usage"),
                        "memory_status": metrics.get("memory", {}).get("status"),
                        "disk_usage": metrics.get("disk", {}).get("usage"),
                        "disk_status": metrics.get("disk", {}).get("status"),
                        "error": result.get("error"),
                    }
                )
