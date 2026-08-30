from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from scans.models import Scan
from scans.serializers import ScanSerializer


class ScanViewSet(viewsets.ModelViewSet):
    queryset = Scan.objects.all().order_by("-created_at")
    serializer_class = ScanSerializer
    http_method_names = ["get", "post", "head"]

    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        scan = self.get_object()
        return Response({
            "id": scan.id,
            "status": scan.status,
            "progress": scan.progress,
            "started_at": scan.started_at,
            "completed_at": scan.completed_at,
        })

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        scan = self.get_object()
        if scan.status in ("pending", "running"):
            scan.status = "cancelled"
            scan.save()
        return Response({"id": scan.id, "status": scan.status})
