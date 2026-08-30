import pytest
from unittest.mock import patch
from credentials.models import Credential
from sources.models import Source
from scans.models import Scan, ScanResult
from reports.models import Report

pytestmark = pytest.mark.django_db


@patch("scans.tasks.scan_host")
def test_full_workflow(mock_scan_host, api_client):
    """End-to-end: create credential -> create source -> run scan -> check report."""
    mock_scan_host.return_value = {
        "hostname": "server1.example.com",
        "os": "Red Hat Enterprise Linux 9.3",
        "os_id": "rhel",
        "os_version": "9.3",
        "kernel": "5.14.0-362.el9.x86_64",
        "arch": "x86_64",
        "cpu_count": 4,
        "memory_mb": 8192,
        "products": ["RHEL"],
        "subscriptions": [],
    }

    # Step 1: Create credential
    cred_resp = api_client.post(
        "/api/v1/credentials/",
        {"name": "test-cred", "credential_type": "password", "username": "root", "secret": "password"},
        format="json",
    )
    assert cred_resp.status_code == 201
    cred_id = cred_resp.data["id"]

    # Step 2: Create source
    source_resp = api_client.post(
        "/api/v1/sources/",
        {"name": "test-source", "source_type": "ssh_network", "hosts": ["10.0.1.1"], "port": 22, "credential": cred_id},
        format="json",
    )
    assert source_resp.status_code == 201
    source_id = source_resp.data["id"]

    # Step 3: Run scan (Huey runs immediately in DEBUG/test mode)
    scan_resp = api_client.post(
        "/api/v1/scans/",
        {"scan_type": "quick", "source_ids": [source_id]},
        format="json",
    )
    assert scan_resp.status_code == 201

    # Step 4: Verify scan completed and report was generated
    scan = Scan.objects.get(id=scan_resp.data["id"])
    assert scan.status == "completed"
    assert ScanResult.objects.filter(scan=scan, status="success").count() == 1

    report = Report.objects.get(scan=scan)
    assert report.summary["total_hosts"] == 1
    assert report.summary["successful_hosts"] == 1
    assert "RHEL" in report.summary["products_found"]

    # Step 5: Verify report API
    report_resp = api_client.get(f"/api/v1/reports/{report.id}/")
    assert report_resp.status_code == 200
    assert report_resp.data["summary"]["total_hosts"] == 1

    # Step 6: Verify CSV export
    csv_resp = api_client.get(f"/api/v1/reports/{report.id}/csv/")
    assert csv_resp.status_code == 200
    assert b"10.0.1.1" in csv_resp.content
    assert b"Red Hat Enterprise Linux 9.3" in csv_resp.content
