from django.db import models
from scans.models import Scan


class Report(models.Model):
    scan = models.OneToOneField(Scan, on_delete=models.CASCADE, related_name="report")
    title = models.CharField(max_length=255)
    summary = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title
