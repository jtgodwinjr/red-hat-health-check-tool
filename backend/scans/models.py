from django.db import models
from sources.models import Source


class Scan(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]
    SCAN_TYPES = [
        ("quick", "Quick Inventory"),
        ("deep", "Deep Inspection"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    scan_type = models.CharField(max_length=10, choices=SCAN_TYPES, default="quick")
    sources = models.ManyToManyField(Source, related_name="scans")
    progress = models.JSONField(default=dict)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.progress:
            self.progress = {
                "total_hosts": 0,
                "completed_hosts": 0,
                "found_systems": 0,
                "current_source": "",
            }
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Scan {self.id} ({self.scan_type} — {self.status})"


class ScanResult(models.Model):
    STATUS_CHOICES = [
        ("success", "Success"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),
    ]

    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="results")
    host = models.CharField(max_length=255)
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="scan_results")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    data = models.JSONField(default=dict)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.host} — {self.status}"
