import socket
import ssl
import urllib.request
import urllib.error


def test_source_connectivity(source) -> list[dict]:
    if source.source_type == "ssh_network":
        return [_test_ssh_host(host, source.port) for host in source.hosts]
    elif source.source_type in ("openshift", "satellite", "ansible_aap", "vcenter"):
        return [_test_api_endpoint(host, source.credential) for host in source.hosts]
    return [{"host": "unknown", "status": "failed", "message": f"Unknown source type: {source.source_type}"}]


def _test_ssh_host(host: str, port: int, timeout: int = 10) -> dict:
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return {"host": host, "status": "success", "message": "SSH connection successful"}
    except socket.timeout:
        return {"host": host, "status": "failed", "message": f"Connection timed out — host {host} did not respond on port {port} within {timeout}s"}
    except ConnectionRefusedError:
        return {"host": host, "status": "failed", "message": f"Connection refused — is SSH running on port {port}?"}
    except OSError as e:
        return {"host": host, "status": "failed", "message": f"Cannot reach {host}:{port} — {e}"}


def _test_api_endpoint(url: str, credential, timeout: int = 10) -> dict:
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, method="HEAD")
        if credential.credential_type == "token":
            req.add_header("Authorization", f"Bearer {credential.get_secret()}")
        urllib.request.urlopen(req, timeout=timeout, context=ctx)
        return {"host": url, "status": "success", "message": "API endpoint reachable"}
    except urllib.error.HTTPError as e:
        if e.code == 401 or e.code == 403:
            return {"host": url, "status": "failed", "message": f"Authentication failed (HTTP {e.code}) — check your credentials"}
        return {"host": url, "status": "failed", "message": f"HTTP error {e.code} from {url}"}
    except urllib.error.URLError as e:
        return {"host": url, "status": "failed", "message": f"Cannot reach {url} — {e.reason}"}
    except Exception as e:
        return {"host": url, "status": "failed", "message": f"Connection test failed — {e}"}
