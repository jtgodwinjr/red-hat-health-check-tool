import pytest
from unittest.mock import patch, MagicMock
from credentials.models import Credential
from sources.models import Source
from scans.models import Scan, ScanResult
from scans.tasks import run_scan

pytestmark = pytest.mark.django_db


@pytest.fixture
def scan_with_source():
    cred = Credential.objects.create(name="cred", credential_type="password", username="root")
    cred.set_secret("pass")
    cred.save()
    source = Source.objects.create(name="src", source_type="ssh_network", hosts=["10.0.1.1", "10.0.1.2"], credential=cred)
    scan = Scan.objects.create(scan_type="quick")
    scan.sources.add(source)
    return scan


@patch("scans.tasks.scan_host")
def test_run_scan_completes(mock_scan_host, scan_with_source):
    mock_scan_host.return_value = {
        "os": "RHEL 9.3",
        "kernel": "5.14.0-362.el9.x86_64",
        "products": ["RHEL"],
    }
    run_scan(scan_with_source.id)
    scan_with_source.refresh_from_db()
    assert scan_with_source.status == "completed"
    assert scan_with_source.completed_at is not None
    assert ScanResult.objects.filter(scan=scan_with_source).count() == 2
    assert all(r.status == "success" for r in ScanResult.objects.filter(scan=scan_with_source))


@patch("scans.tasks.scan_host")
def test_run_scan_handles_host_failure(mock_scan_host, scan_with_source):
    mock_scan_host.side_effect = [
        {"os": "RHEL 9.3"},
        ConnectionError("SSH connection failed"),
    ]
    run_scan(scan_with_source.id)
    scan_with_source.refresh_from_db()
    assert scan_with_source.status == "completed"
    results = ScanResult.objects.filter(scan=scan_with_source).order_by("host")
    assert results[0].status == "success"
    assert results[1].status == "failed"
    assert "SSH connection failed" in results[1].error_message


@patch("scans.tasks.scan_host")
def test_run_scan_updates_progress(mock_scan_host, scan_with_source):
    mock_scan_host.return_value = {"os": "RHEL 9.3"}
    run_scan(scan_with_source.id)
    scan_with_source.refresh_from_db()
    assert scan_with_source.progress["total_hosts"] == 2
    assert scan_with_source.progress["completed_hosts"] == 2
