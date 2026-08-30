import json
import ssl
import urllib.request


def scan(host: str, port: int, credential, scan_type: str) -> dict:
    base_url = host.rstrip("/")
    token = credential.get_secret()

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    config = _api_get(f"{base_url}/api/v2/config/", token, ctx)
    inventories = _api_get(f"{base_url}/api/v2/inventories/?page_size=50", token, ctx)

    return {
        "hostname": base_url,
        "os": "Ansible Automation Platform",
        "aap_version": config.get("version", "unknown"),
        "inventory_count": inventories.get("count", 0),
        "products": ["Ansible Automation Platform"],
    }


def _api_get(url: str, token: str, ctx) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    return json.loads(resp.read().decode())
