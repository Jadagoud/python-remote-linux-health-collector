import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import paramiko

from src.logger_config import setup_logger
from src.report_generator import ReportGenerator
from src.ssh_connection import SSHConnection
from src.system_metrics import SystemMetrics

INVENTORY_FILE = "config/inventory.json"
THRESHOLDS_FILE = "config/thresholds.json"


def get_health_status(value, warning, critical):

    if value >= critical:
        return "CRITICAL"

    if value >= warning:
        return "WARNING"

    return "HEALTHY"


def collect_server(server, thresholds, logger):

    ssh = SSHConnection(
        hostname=server["host"],
        username=server["username"],
        key_file=server["key_file"],
    )

    try:
        # Stage 1: Establish SSH connection
        try:
            ssh.connect()

            logger.info(f"SSH connection established: {server['name']}")

        except paramiko.AuthenticationException as error:
            logger.warning(f"Authentication failed: {server['name']} - {error}")

            return {
                "server_name": server["name"],
                "hostname": server["host"],
                "status": "AUTHENTICATION_FAILED",
                "error": str(error),
            }

        except paramiko.BadHostKeyException as error:
            logger.error(f"Host key verification failed: {server['name']} - {error}")

            return {
                "server_name": server["name"],
                "hostname": server["host"],
                "status": "HOST_KEY_VERIFICATION_FAILED",
                "error": str(error),
            }

        except (
            TimeoutError,
            paramiko.ssh_exception.NoValidConnectionsError,
            OSError,
        ) as error:
            logger.warning(f"Server unreachable: {server['name']} - {error}")

            return {
                "server_name": server["name"],
                "hostname": server["host"],
                "status": "UNREACHABLE",
                "error": str(error),
            }

        except paramiko.SSHException as error:
            logger.error(f"SSH connection failed: {server['name']} - {error}")

            return {
                "server_name": server["name"],
                "hostname": server["host"],
                "status": "CONNECTION_FAILED",
                "error": str(error),
            }

        # Stage 2: Collect system metrics
        try:
            metrics = SystemMetrics(ssh)

            cpu = metrics.get_cpu_usage()
            memory = metrics.get_memory_usage()
            disk = metrics.get_disk_usage()

            result = {
                "server_name": server["name"],
                "hostname": server["host"],
                "status": "SUCCESS",
                "metrics": {
                    "cpu": {
                        "usage": cpu,
                        "status": get_health_status(
                            cpu,
                            thresholds["cpu"]["warning"],
                            thresholds["cpu"]["critical"],
                        ),
                    },
                    "memory": {
                        "usage": memory,
                        "status": get_health_status(
                            memory,
                            thresholds["memory"]["warning"],
                            thresholds["memory"]["critical"],
                        ),
                    },
                    "disk": {
                        "usage": disk,
                        "status": get_health_status(
                            disk,
                            thresholds["disk"]["warning"],
                            thresholds["disk"]["critical"],
                        ),
                    },
                },
            }

            logger.info(f"Metrics collected successfully: {server['name']}")

            return result

        except (
            paramiko.SSHException,
            OSError,
            RuntimeError,
            ValueError,
            IndexError,
            KeyError,
        ) as error:
            logger.error(f"Metric collection failed: {server['name']} - {error}")

            return {
                "server_name": server["name"],
                "hostname": server["host"],
                "status": "MONITORING_FAILED",
                "error": str(error),
            }

    finally:
        # Always close the SSH client, including after connection failures.
        ssh.close()


def main():

    logger = setup_logger()

    logger.info("Starting remote server health monitoring")

    try:
        # Load inventory configuration
        with open(INVENTORY_FILE, "r", encoding="utf-8") as file:
            inventory = json.load(file)

        # Load health thresholds
        with open(THRESHOLDS_FILE, "r", encoding="utf-8") as file:
            thresholds = json.load(file)

        servers = inventory["servers"]

        if not isinstance(servers, list) or not servers:
            raise ValueError("Inventory must contain at least one server")

        results = []

        max_workers = min(5, len(servers))

        print(f"Starting monitoring of {len(servers)} servers")

        print(f"Parallel workers: {max_workers}")

        logger.info(f"Monitoring {len(servers)} servers using {max_workers} workers")

        # Parallel server monitoring
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_server = {
                executor.submit(collect_server, server, thresholds, logger): server
                for server in servers
            }

            for future in as_completed(future_to_server):
                server = future_to_server[future]

                try:
                    result = future.result()

                except Exception as error:
                    logger.exception(
                        f"Unexpected monitoring error: {server.get('name', 'unknown')}"
                    )

                    result = {
                        "server_name": server.get("name", "unknown"),
                        "hostname": server.get("host", "unknown"),
                        "status": "MONITORING_FAILED",
                        "error": str(error),
                    }

                results.append(result)

                print(f"\nCompleted: {server.get('name', 'unknown')}")

                print(json.dumps(result, indent=4))

                if result["status"] == "SUCCESS":
                    logger.info(f"Monitoring successful: {server['name']}")

                else:
                    logger.warning(
                        f"Monitoring failed: {server['name']} - {result['status']}"
                    )

        # Monitoring summary
        successful = sum(1 for result in results if result["status"] == "SUCCESS")

        failed = len(results) - successful

        print("\n========== MONITORING SUMMARY ==========")

        print(f"Total servers: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")

        logger.info(
            f"Monitoring completed | Total: {len(results)} | "
            f"Successful: {successful} | Failed: {failed}"
        )

        # Generate JSON and CSV reports
        report_generator = ReportGenerator()

        report_files = report_generator.generate_reports(results)

        print("\n========== REPORTS GENERATED ==========")

        print(f"JSON: {report_files['json_report']}")

        print(f"CSV:  {report_files['csv_report']}")

        logger.info(f"JSON report generated: {report_files['json_report']}")

        logger.info(f"CSV report generated: {report_files['csv_report']}")

        logger.info("Health monitoring execution completed")

        return results

    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        logger.exception("Application configuration or execution error")
        raise


if __name__ == "__main__":
    main()
