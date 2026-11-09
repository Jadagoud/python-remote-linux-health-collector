import time


class SystemMetrics:
    def __init__(self, ssh):
        self.ssh = ssh

    def get_cpu_usage(self):

        first = self.ssh.execute_command("cat /proc/stat")

        if first["exit_code"] != 0:
            raise RuntimeError(first["stderr"])

        cpu1 = first["stdout"].splitlines()[0].split()[1:]
        values1 = [int(value) for value in cpu1]

        time.sleep(1)

        second = self.ssh.execute_command("cat /proc/stat")

        if second["exit_code"] != 0:
            raise RuntimeError(second["stderr"])

        cpu2 = second["stdout"].splitlines()[0].split()[1:]
        values2 = [int(value) for value in cpu2]

        total1 = sum(values1)
        total2 = sum(values2)

        idle1 = values1[3] + values1[4]
        idle2 = values2[3] + values2[4]

        total_delta = total2 - total1
        idle_delta = idle2 - idle1

        if total_delta <= 0:
            raise RuntimeError("Invalid CPU counter delta")

        cpu_usage = ((total_delta - idle_delta) / total_delta) * 100

        return round(cpu_usage, 2)

    def get_memory_usage(self):

        result = self.ssh.execute_command("free -b")

        if result["exit_code"] != 0:
            raise RuntimeError(result["stderr"])

        for line in result["stdout"].splitlines():
            if line.startswith("Mem:"):
                values = line.split()

                total = int(values[1])
                available = int(values[6])

                used_percentage = ((total - available) / total) * 100

                return round(used_percentage, 2)

        raise RuntimeError("Memory information not found")

    def get_disk_usage(self):

        result = self.ssh.execute_command("df -P /")

        if result["exit_code"] != 0:
            raise RuntimeError(result["stderr"])

        lines = result["stdout"].splitlines()

        if len(lines) < 2:
            raise RuntimeError("Disk information not found")

        usage = lines[1].split()[4]

        return float(usage.rstrip("%"))
