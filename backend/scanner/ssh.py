import subprocess
import shlex


def _parse_os_release(content: str) -> dict:
    result = {}
    for line in content.strip().splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.lower()] = value.strip('"')
    return result


def _ssh_exec(host: str, port: int, credential, command: str, timeout: int = 30) -> str:
    ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", "-p", str(port)]

    if credential.credential_type == "ssh_key":
        ssh_cmd += ["-i", credential.ssh_key_file]
    elif credential.credential_type == "password":
        ssh_cmd = ["sshpass", "-p", credential.get_secret()] + ssh_cmd

    ssh_cmd += [f"{credential.username}@{host}", command]

    result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"SSH command failed on {host}: {result.stderr.strip()}")
    return result.stdout.strip()


def scan(host: str, port: int, credential, scan_type: str) -> dict:
    os_release_raw = _ssh_exec(host, port, credential, "cat /etc/os-release")
    os_info = _parse_os_release(os_release_raw)

    hostname = _ssh_exec(host, port, credential, "hostname -f")
    kernel = _ssh_exec(host, port, credential, "uname -r")
    arch = _ssh_exec(host, port, credential, "uname -m")
    cpu_count_raw = _ssh_exec(host, port, credential, "nproc")
    mem_raw = _ssh_exec(host, port, credential, "awk '/MemTotal/{print $2}' /proc/meminfo")

    os_name = os_info.get("name", "Unknown")
    os_version = os_info.get("version_id", os_info.get("version", ""))
    os_display = f"{os_name} {os_version}".strip()

    data = {
        "hostname": hostname,
        "os": os_display,
        "os_id": os_info.get("id", ""),
        "os_version": os_version,
        "kernel": kernel,
        "arch": arch,
        "cpu_count": int(cpu_count_raw) if cpu_count_raw.isdigit() else 0,
        "memory_mb": int(int(mem_raw) / 1024) if mem_raw.isdigit() else 0,
        "products": [],
        "subscriptions": [],
    }

    if scan_type == "deep":
        try:
            sub_raw = _ssh_exec(host, port, credential, "subscription-manager list --consumed 2>/dev/null || echo 'N/A'")
            if sub_raw != "N/A":
                data["subscriptions"] = [sub_raw]
        except Exception:
            pass

        try:
            rpm_raw = _ssh_exec(host, port, credential, "rpm -qa --qf '%{NAME}\\n' 2>/dev/null | head -200")
            products = []
            if "satellite" in rpm_raw.lower():
                products.append("Satellite")
            if "ansible" in rpm_raw.lower():
                products.append("Ansible")
            if os_info.get("id") == "rhel":
                products.insert(0, "RHEL")
            data["products"] = products
        except Exception:
            if os_info.get("id") == "rhel":
                data["products"] = ["RHEL"]
    else:
        if os_info.get("id") == "rhel":
            data["products"] = ["RHEL"]

    return data
