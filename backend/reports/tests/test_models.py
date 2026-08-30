import pytest
from credentials.models import Credential
from sources.models import Source
from scans.models import Scan, ScanResult
from reports.models import Report

pytestmark = pytest.mark.django_db


@pytest.fixture
def completed_scan():
    cred = Credential.objects.create(name="cred", credential_type="password", username="root")
    source = Source.objects.create(name="src", source_type="ssh_network", hosts=["10.0.1.1"], credential=cred)
    scan = Scan.objects.create(scan_type="quick", status="completed")
    scan.sources.add(source)
    ScanResult.objects.create(scan=scan, host="10.0.1.1", source=source, status="success", data={"os": "RHEL 9.3", "products": ["RHEL"]})
    return scan


def test_create_report(completed_scan):
    report = Report.objects.create(
        scan=completed_scan,
        title="Health Check Report",
        summary={
            "total_hosts": 1,
            "successful_hosts": 1,
            "failed_hosts": 0,
            "os_distribution": {"RHEL 9.3": 1},
            "products_found": {"RHEL": 1},
        },
    )
    assert report.title == "Health Check Report"
    assert report.summary["total_hosts"] == 1


def test_report_str(completed_scan):
    report = Report(scan=completed_scan, title="Test Report")
    assert str(report) == "Test Report"
