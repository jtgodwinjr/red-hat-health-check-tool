import pytest
from credentials.models import Credential
from sources.models import Source
from scans.models import Scan, ScanResult
from reports.models import Report

pytestmark = pytest.mark.django_db


@pytest.fixture
def report():
    cred = Credential.objects.create(name="cred", credential_type="password", username="root")
    source = Source.objects.create(name="src", source_type="ssh_network", hosts=["10.0.1.1"], credential=cred)
    scan = Scan.objects.create(scan_type="quick", status="completed")
    scan.sources.add(source)
    ScanResult.objects.create(scan=scan, host="10.0.1.1", source=source, status="success", data={"os": "RHEL 9.3", "products": ["RHEL"]})
    return Report.objects.create(scan=scan, title="Test Report", summary={"total_hosts": 1, "successful_hosts": 1, "failed_hosts": 0, "os_distribution": {"RHEL 9.3": 1}, "products_found": {"RHEL": 1}})


def test_list_reports(api_client, report):
    response = api_client.get("/api/v1/reports/")
    assert response.status_code == 200
    assert len(response.data) == 1


def test_get_report_detail(api_client, report):
    response = api_client.get(f"/api/v1/reports/{report.id}/")
    assert response.status_code == 200
    assert response.data["title"] == "Test Report"
    assert response.data["summary"]["total_hosts"] == 1


def test_download_csv(api_client, report):
    response = api_client.get(f"/api/v1/reports/{report.id}/csv/")
    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert b"10.0.1.1" in response.content
