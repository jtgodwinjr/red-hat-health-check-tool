from rest_framework import serializers
from sources.models import Source


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ["id", "name", "source_type", "hosts", "port", "credential", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
