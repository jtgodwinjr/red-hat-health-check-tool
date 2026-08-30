import json
import ssl
import urllib.request
import base64


def scan(host: str, port: int, credential, scan_type: str) -> dict:
    base_url = host.rstrip("/")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    session_id = _create_session(base_url, credential, ctx)
    vms = _api_get(f"{base_url}/api/vcenter/vm", session_id, ctx)

    vm_list = []
    for vm in vms:
        vm_list.append({
            "name": vm.get("name", ""),
            "power_state": vm.get("power_state", ""),
            "cpu_count": vm.get("cpu_count", 0),
            "memory_mb": vm.get("memory_size_MiB", 0),
        })

    return {
        "hostname": base_url,
        "os": "VMware vCenter",
        "vm_count": len(vm_list),
        "vms": vm_list[:100],
        "products": ["VMware vCenter"],
    }


def _create_session(base_url: str, credential, ctx) -> str:
    url = f"{base_url}/api/session"
    creds = f"{credential.username}:{credential.get_secret()}"
    encoded = base64.b64encode(creds.encode()).decode()
    req = urllib.request.Request(url, method="POST", data=b"")
    req.add_header("Authorization", f"Basic {encoded}")
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    return json.loads(resp.read().decode())


def _api_get(url: str, session_id: str, ctx) -> list:
    req = urllib.request.Request(url)
    req.add_header("vmware-api-session-id", session_id)
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    return json.loads(resp.read().decode())
