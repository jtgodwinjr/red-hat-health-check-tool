import pytest
from unittest.mock import patch, MagicMock
from credentials.models import Credential
from sources.models import Source
from sources.connectivity import test_source_connectivity as check_connectivity

pytestmark = pytest.mark.django_db


@pytest.fixture
def ssh_source():
    cred = Credential.objects.create(name="ssh-cred", credential_type="password", username="root")
    cred.set_secret("password123")
    cred.save()
    return Source.objects.create(
        name="test-ssh",
        source_type="ssh_network",
        hosts=["10.0.1.1", "10.0.1.2"],
        port=22,
        credential=cred,
    )


@patch("sources.connectivity._test_ssh_host")
def test_ssh_connectivity_success(mock_test, ssh_source):
    mock_test.return_value = {"host": "10.0.1.1", "status": "success", "message": "SSH connection successful"}
    results = check_connectivity(ssh_source)
    assert len(results) == 2
    assert all(r["status"] == "success" for r in results)


@patch("sources.connectivity._test_ssh_host")
def test_ssh_connectivity_failure(mock_test, ssh_source):
    mock_test.return_value = {"host": "10.0.1.1", "status": "failed", "message": "Connection refused — is SSH running on port 22?"}
    results = check_connectivity(ssh_source)
    assert len(results) == 2
    assert all(r["status"] == "failed" for r in results)


@patch("sources.connectivity._test_api_endpoint")
def test_openshift_connectivity(mock_test):
    cred = Credential.objects.create(name="ocp-token", credential_type="token", username="")
    cred.set_secret("sha256~abc")
    cred.save()
    source = Source.objects.create(
        name="ocp-cluster",
        source_type="openshift",
        hosts=["https://api.cluster.example.com:6443"],
        port=6443,
        credential=cred,
    )
    mock_test.return_value = {"host": "https://api.cluster.example.com:6443", "status": "success", "message": "API endpoint reachable"}
    results = check_connectivity(source)
    assert len(results) == 1
    assert results[0]["status"] == "success"
