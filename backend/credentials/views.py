from rest_framework import viewsets
from credentials.models import Credential
from credentials.serializers import CredentialSerializer


class CredentialViewSet(viewsets.ModelViewSet):
    queryset = Credential.objects.all().order_by("-created_at")
    serializer_class = CredentialSerializer
