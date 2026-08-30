import pytest
from credentials.models import Credential
from sources.models import Source

pytestmark = pytest.mark.django_db


@pytest.fixture
def credential():
    return Credential.objects.create(name="test-cred", credential_type="password", username="admin")


def test_create_source(api_client, credential):
    response = api_client.post(
        "/api/v1/sources/",
        {
            "name": "test-source",
            "source_type": "ssh_network",
            "hosts": ["10.0.1.1", "10.0.1.2"],
            "port": 22,
            "credential": credential.id,
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["name"] == "test-source"
    assert response.data["hosts"] == ["10.0.1.1", "10.0.1.2"]


def test_list_sources(api_client, credential):
    Source.objects.create(name="s1", source_type="ssh_network", hosts=["10.0.1.1"], credential=credential)
    Source.objects.create(name="s2", source_type="openshift", hosts=["https://api.ocp.example.com"], credential=credential)
    response = api_client.get("/api/v1/sources/")
    assert response.status_code == 200
    assert len(response.data) == 2


def test_get_source_detail(api_client, credential):
    source = Source.objects.create(name="detail-src", source_type="satellite", hosts=["sat.example.com"], credential=credential)
    response = api_client.get(f"/api/v1/sources/{source.id}/")
    assert response.status_code == 200
    assert response.data["name"] == "detail-src"


def test_delete_source(api_client, credential):
    source = Source.objects.create(name="to-delete", source_type="vcenter", hosts=["vc.example.com"], credential=credential)
    response = api_client.delete(f"/api/v1/sources/{source.id}/")
    assert response.status_code == 204
    assert Source.objects.count() == 0
