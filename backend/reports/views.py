from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from reports.models import Report
from reports.serializers import ReportSerializer
from reports.generators import generate_csv, generate_pdf


class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Report.objects.all().order_by("-created_at")
    serializer_class = ReportSerializer

    @action(detail=True, methods=["get"])
    def csv(self, request, pk=None):
        report = self.get_object()
        csv_content = generate_csv(report)
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="health-check-{report.id}.csv"'
        return response

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        report = self.get_object()
        pdf_bytes = generate_pdf(report)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="health-check-{report.id}.pdf"'
        return response
