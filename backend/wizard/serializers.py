from rest_framework import serializers
from wizard.models import WizardState


class WizardStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WizardState
        fields = ["id", "current_step", "completed_steps", "data", "updated_at"]
        read_only_fields = ["id", "updated_at"]
