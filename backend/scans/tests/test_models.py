import pytest
from credentials.models import Credential
from sources.models import Source
from scans.models import Scan, ScanResult

pytestmark = pytest.mark.django_db


@pytest.fixture
def source():
    cred = Credential.objects.create(name="cred", credential_type="password", username="root")
    return Source.objects.create(name="src", source_type="ssh_network", hosts=["10.0.1.1"], credential=cred)


def test_create_scan(source):
    scan = Scan.objects.create(scan_type="quick")
    scan.sources.add(source)
    assert scan.status == "pending"
    assert scan.scan_type == "quick"
    assert scan.sources.count() == 1


def test_scan_progress_default(source):
    scan = Scan.objects.create(scan_type="deep")
    assert scan.progress == {"total_hosts": 0, "completed_hosts": 0, "found_systems": 0, "current_source": ""}


def test_create_scan_result(source):
    scan = Scan.objects.create(scan_type="quick")
    scan.sources.add(source)
    result = ScanResult.objects.create(
        scan=scan,
        host="10.0.1.1",
        source=source,
        status="success",
        data={"os": "RHEL 9.3", "kernel": "5.14.0-362.el9.x86_64"},
    )
    assert result.status == "success"
    assert result.data["os"] == "RHEL 9.3"


def test_scan_str(source):
    scan = Scan.objects.create(scan_type="quick")
    assert "quick" in str(scan).lower()
