from django.urls import path
from wizard.views import WizardStateView

urlpatterns = [
    path("state/", WizardStateView.as_view(), name="wizard-state"),
]
