from django.db import models


class WizardState(models.Model):
    current_step = models.IntegerField(default=1)
    completed_steps = models.JSONField(default=list)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "wizard state"
