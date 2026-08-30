from rest_framework import serializers
from reports.models import Report
from scans.serializers import ScanResultSerializer


class ReportSerializer(serializers.ModelSerializer):
    results = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = ["id", "scan", "title", "summary", "results", "created_at"]

    def get_results(self, obj):
        from scans.models import ScanResult
        results = ScanResult.objects.filter(scan=obj.scan)
        return ScanResultSerializer(results, many=True).data
