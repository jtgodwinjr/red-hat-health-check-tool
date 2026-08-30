import pytest
from django.urls import reverse
from credentials.models import Credential

pytestmark = pytest.mark.django_db


def test_create_credential(api_client):
    response = api_client.post(
        "/api/v1/credentials/",
        {
            "name": "test-cred",
            "credential_type": "password",
            "username": "admin",
            "secret": "s3cret",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["name"] == "test-cred"
    assert "secret" not in response.data
    assert "encrypted_secret" not in response.data
    cred = Credential.objects.get(name="test-cred")
    assert cred.get_secret() == "s3cret"


def test_list_credentials(api_client):
    Credential.objects.create(name="cred1", credential_type="password", username="u1")
    Credential.objects.create(name="cred2", credential_type="token", username="u2")
    response = api_client.get("/api/v1/credentials/")
    assert response.status_code == 200
    assert len(response.data) == 2


def test_list_credentials_hides_secrets(api_client):
    cred = Credential.objects.create(name="cred1", credential_type="password", username="u1")
    cred.set_secret("hidden")
    cred.save()
    response = api_client.get("/api/v1/credentials/")
    assert response.status_code == 200
    for item in response.data:
        assert "secret" not in item
        assert "encrypted_secret" not in item


def test_get_credential_detail(api_client):
    cred = Credential.objects.create(name="detail-cred", credential_type="ssh_key", username="root")
    response = api_client.get(f"/api/v1/credentials/{cred.id}/")
    assert response.status_code == 200
    assert response.data["name"] == "detail-cred"


def test_update_credential(api_client):
    cred = Credential.objects.create(name="old-name", credential_type="password", username="admin")
    response = api_client.put(
        f"/api/v1/credentials/{cred.id}/",
        {"name": "new-name", "credential_type": "password", "username": "admin"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["name"] == "new-name"


def test_delete_credential(api_client):
    cred = Credential.objects.create(name="to-delete", credential_type="token", username="")
    response = api_client.delete(f"/api/v1/credentials/{cred.id}/")
    assert response.status_code == 204
    assert Credential.objects.count() == 0
