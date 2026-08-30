from django.db import models
from credentials.models import Credential


class Source(models.Model):
    SOURCE_TYPES = [
        ("ssh_network", "SSH Network"),
        ("openshift", "OpenShift"),
        ("satellite", "Red Hat Satellite"),
        ("ansible_aap", "Ansible Automation Platform"),
        ("vcenter", "VMware vCenter"),
    ]

    name = models.CharField(max_length=255, unique=True)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    hosts = models.JSONField(default=list)
    port = models.IntegerField(default=22)
    credential = models.ForeignKey(
        Credential, on_delete=models.CASCADE, related_name="sources"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.source_type})"
