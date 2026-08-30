import json
import ssl
import urllib.request
import base64


def scan(host: str, port: int, credential, scan_type: str) -> dict:
    base_url = host.rstrip("/")
    auth_header = _build_auth(credential)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    status = _api_get(f"{base_url}/katello/api/v2/ping", auth_header, ctx)
    hosts_data = _api_get(f"{base_url}/api/v2/hosts?per_page=250", auth_header, ctx)

    hosts = []
    for h in hosts_data.get("results", []):
        hosts.append({
            "hostname": h.get("name", ""),
            "os": h.get("operatingsystem_name", ""),
            "environment": h.get("environment_name", ""),
        })

    return {
        "hostname": base_url,
        "os": "Red Hat Satellite",
        "satellite_version": status.get("version", "unknown"),
        "managed_host_count": hosts_data.get("total", 0),
        "managed_hosts": hosts[:50],
        "products": ["Satellite"],
    }


def _build_auth(credential) -> str:
    if credential.credential_type == "token":
        return f"Bearer {credential.get_secret()}"
    creds = f"{credential.username}:{credential.get_secret()}"
    encoded = base64.b64encode(creds.encode()).decode()
    return f"Basic {encoded}"


def _api_get(url: str, auth_header: str, ctx) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Authorization", auth_header)
    req.add_header("Accept", "application/json")
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    return json.loads(resp.read().decode())
