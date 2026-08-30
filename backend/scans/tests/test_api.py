import pytest
from credentials.models import Credential
from sources.models import Source
from scans.models import Scan

pytestmark = pytest.mark.django_db


@pytest.fixture
def source():
    cred = Credential.objects.create(name="cred", credential_type="password", username="root")
    return Source.objects.create(name="src", source_type="ssh_network", hosts=["10.0.1.1"], credential=cred)


def test_create_scan(api_client, source):
    response = api_client.post(
        "/api/v1/scans/",
        {"scan_type": "quick", "source_ids": [source.id]},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["status"] == "pending"
    assert response.data["scan_type"] == "quick"


def test_list_scans(api_client, source):
    scan = Scan.objects.create(scan_type="quick")
    scan.sources.add(source)
    response = api_client.get("/api/v1/scans/")
    assert response.status_code == 200
    assert len(response.data) == 1


def test_get_scan_status(api_client, source):
    scan = Scan.objects.create(scan_type="deep", status="running")
    scan.sources.add(source)
    scan.progress = {"total_hosts": 5, "completed_hosts": 2, "found_systems": 1, "current_source": "src"}
    scan.save()
    response = api_client.get(f"/api/v1/scans/{scan.id}/status/")
    assert response.status_code == 200
    assert response.data["status"] == "running"
    assert response.data["progress"]["completed_hosts"] == 2


def test_cancel_scan(api_client, source):
    scan = Scan.objects.create(scan_type="quick", status="running")
    scan.sources.add(source)
    response = api_client.post(f"/api/v1/scans/{scan.id}/cancel/")
    assert response.status_code == 200
    scan.refresh_from_db()
    assert scan.status == "cancelled"
