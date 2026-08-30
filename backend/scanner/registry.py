from scanner.ssh import scan as ssh_scan
from scanner.openshift import scan as openshift_scan
from scanner.satellite import scan as satellite_scan
from scanner.aap import scan as aap_scan
from scanner.vcenter import scan as vcenter_scan

_SCANNERS = {
    "ssh_network": ssh_scan,
    "openshift": openshift_scan,
    "satellite": satellite_scan,
    "ansible_aap": aap_scan,
    "vcenter": vcenter_scan,
}


def scan_host(host: str, port: int, credential, source_type: str, scan_type: str) -> dict:
    if source_type not in _SCANNERS:
        raise ValueError(f"Unknown source type: {source_type}")
    return _SCANNERS[source_type](host, port, credential, scan_type)
