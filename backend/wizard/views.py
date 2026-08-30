from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from wizard.models import WizardState
from wizard.serializers import WizardStateSerializer


class WizardStateView(APIView):
    def get(self, request):
        state, _ = WizardState.objects.get_or_create(
            defaults={"current_step": 1, "completed_steps": [], "data": {}}
        )
        serializer = WizardStateSerializer(state)
        return Response(serializer.data)

    def put(self, request):
        state, _ = WizardState.objects.get_or_create(
            defaults={"current_step": 1, "completed_steps": [], "data": {}}
        )
        serializer = WizardStateSerializer(state, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
