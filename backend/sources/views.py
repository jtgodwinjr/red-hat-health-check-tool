from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from sources.models import Source
from sources.serializers import SourceSerializer
from sources.connectivity import test_source_connectivity


class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all().order_by("-created_at")
    serializer_class = SourceSerializer

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        source = self.get_object()
        results = test_source_connectivity(source)
        return Response({"results": results}, status=status.HTTP_200_OK)
