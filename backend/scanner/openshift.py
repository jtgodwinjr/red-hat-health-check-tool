import json
import ssl
import urllib.request


def scan(host: str, port: int, credential, scan_type: str) -> dict:
    base_url = host.rstrip("/")
    token = credential.get_secret()

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    version_data = _api_get(f"{base_url}/version", token, ctx)
    nodes_data = _api_get(f"{base_url}/api/v1/nodes", token, ctx)

    nodes = []
    for node in nodes_data.get("items", []):
        info = node.get("status", {}).get("nodeInfo", {})
        nodes.append({
            "hostname": node.get("metadata", {}).get("name", ""),
            "os": info.get("osImage", ""),
            "kernel": info.get("kernelVersion", ""),
            "arch": info.get("architecture", ""),
            "container_runtime": info.get("containerRuntimeVersion", ""),
        })

    return {
        "hostname": base_url,
        "os": f"OpenShift {version_data.get('gitVersion', 'unknown')}",
        "cluster_version": version_data.get("gitVersion", ""),
        "node_count": len(nodes),
        "nodes": nodes,
        "products": ["OpenShift"],
    }


def _api_get(url: str, token: str, ctx) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    return json.loads(resp.read().decode())
