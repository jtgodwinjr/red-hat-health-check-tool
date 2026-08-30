from rest_framework import serializers
from scans.models import Scan, ScanResult


class ScanResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanResult
        fields = ["id", "host", "source", "status", "data", "error_message", "created_at"]


class ScanSerializer(serializers.ModelSerializer):
    source_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    results = ScanResultSerializer(many=True, read_only=True)

    class Meta:
        model = Scan
        fields = [
            "id", "status", "scan_type", "sources", "source_ids",
            "progress", "results", "started_at", "completed_at", "created_at",
        ]
        read_only_fields = ["id", "status", "sources", "progress", "results", "started_at", "completed_at", "created_at"]

    def create(self, validated_data):
        source_ids = validated_data.pop("source_ids")
        scan = Scan.objects.create(**validated_data)
        scan.sources.set(source_ids)
        from scans.tasks import run_scan
        run_scan(scan.id)
        return scan
