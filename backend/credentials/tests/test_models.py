import pytest
from credentials.models import Credential
from credentials.encryption import decrypt_value

pytestmark = pytest.mark.django_db


def test_create_credential_password():
    cred = Credential.objects.create(
        name="test-server",
        credential_type="password",
        username="admin",
    )
    cred.set_secret("s3cret")
    cred.save()
    cred.refresh_from_db()
    assert cred.name == "test-server"
    assert cred.credential_type == "password"
    assert cred.username == "admin"
    assert cred.encrypted_secret != "s3cret"
    assert decrypt_value(cred.encrypted_secret) == "s3cret"


def test_create_credential_token():
    cred = Credential.objects.create(
        name="openshift-cluster",
        credential_type="token",
        username="",
    )
    cred.set_secret("sha256~abcdef1234567890")
    cred.save()
    cred.refresh_from_db()
    assert cred.credential_type == "token"
    assert decrypt_value(cred.encrypted_secret) == "sha256~abcdef1234567890"


def test_credential_str():
    cred = Credential(name="my-cred", credential_type="password")
    assert str(cred) == "my-cred (password)"
