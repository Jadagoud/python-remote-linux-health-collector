import paramiko
from paramiko import RSAKey


class SSHConnection:
    def __init__(self, hostname, username, key_file):
        self.hostname = hostname
        self.username = username
        self.key_file = key_file
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.RejectPolicy())

        self.client.connect(
            hostname=self.hostname,
            username=self.username,
            pkey=RSAKey.from_private_key_file(self.key_file),
            timeout=10,
            auth_timeout=10,
            banner_timeout=10,
            look_for_keys=False,
            allow_agent=False,
        )

        print(f"Connected to {self.hostname}")

    def execute_command(self, command):
        if self.client is None:
            raise RuntimeError("SSH connection not established")

        _stdin, stdout, stderr = self.client.exec_command(command, timeout=15)

        exit_code = stdout.channel.recv_exit_status()

        return {
            "command": command,
            "exit_code": exit_code,
            "stdout": stdout.read().decode(errors="replace").strip(),
            "stderr": stderr.read().decode(errors="replace").strip(),
        }

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None
