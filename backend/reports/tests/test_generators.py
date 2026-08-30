import pytest
from credentials.models import Credential
from sources.models import Source
from scans.models import Scan, ScanResult
from reports.generators import generate_report, generate_csv

pytestmark = pytest.mark.django_db


@pytest.fixture
def completed_scan():
    cred = Credential.objects.create(name="cred", credential_type="password", username="root")
    source = Source.objects.create(name="src", source_type="ssh_network", hosts=["10.0.1.1", "10.0.1.2"], credential=cred)
    scan = Scan.objects.create(scan_type="quick", status="completed")
    scan.sources.add(source)
    ScanResult.objects.create(scan=scan, host="10.0.1.1", source=source, status="success", data={"hostname": "server1", "os": "RHEL 9.3", "kernel": "5.14.0", "arch": "x86_64", "cpu_count": 4, "memory_mb": 8192, "products": ["RHEL"]})
    ScanResult.objects.create(scan=scan, host="10.0.1.2", source=source, status="failed", data={}, error_message="Connection refused")
    return scan


def test_generate_report(completed_scan):
    report = generate_report(completed_scan)
    assert report.title == "Health Check Report"
    assert report.summary["total_hosts"] == 2
    assert report.summary["successful_hosts"] == 1
    assert report.summary["failed_hosts"] == 1
    assert report.summary["os_distribution"]["RHEL 9.3"] == 1
    assert report.summary["products_found"]["RHEL"] == 1


def test_generate_csv(completed_scan):
    report = generate_report(completed_scan)
    csv_content = generate_csv(report)
    assert "host" in csv_content
    assert "10.0.1.1" in csv_content
    assert "RHEL 9.3" in csv_content
    assert "10.0.1.2" in csv_content
    assert "Connection refused" in csv_content
