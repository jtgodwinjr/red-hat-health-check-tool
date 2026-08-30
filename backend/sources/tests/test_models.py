import pytest
from credentials.models import Credential
from sources.models import Source

pytestmark = pytest.mark.django_db


def test_create_ssh_source():
    cred = Credential.objects.create(name="ssh-cred", credential_type="password", username="root")
    source = Source.objects.create(
        name="dev-servers",
        source_type="ssh_network",
        hosts=["10.0.1.1", "10.0.1.2", "10.0.1.3"],
        port=22,
        credential=cred,
    )
    assert source.source_type == "ssh_network"
    assert len(source.hosts) == 3
    assert source.credential == cred


def test_create_openshift_source():
    cred = Credential.objects.create(name="ocp-token", credential_type="token", username="")
    source = Source.objects.create(
        name="prod-cluster",
        source_type="openshift",
        hosts=["https://api.cluster.example.com:6443"],
        port=6443,
        credential=cred,
    )
    assert source.source_type == "openshift"


def test_source_str():
    source = Source(name="my-source", source_type="ssh_network")
    assert str(source) == "my-source (ssh_network)"


def test_source_types():
    valid_types = [choice[0] for choice in Source.SOURCE_TYPES]
    assert "ssh_network" in valid_types
    assert "openshift" in valid_types
    assert "satellite" in valid_types
    assert "ansible_aap" in valid_types
    assert "vcenter" in valid_types
