import pytest
from wizard.models import WizardState

pytestmark = pytest.mark.django_db


def test_get_wizard_state_creates_default(api_client):
    response = api_client.get("/api/v1/wizard/state/")
    assert response.status_code == 200
    assert response.data["current_step"] == 1
    assert response.data["completed_steps"] == []


def test_get_wizard_state_returns_existing(api_client):
    WizardState.objects.create(current_step=3, completed_steps=[1, 2], data={"credentials": [1]})
    response = api_client.get("/api/v1/wizard/state/")
    assert response.status_code == 200
    assert response.data["current_step"] == 3
    assert response.data["completed_steps"] == [1, 2]


def test_update_wizard_state(api_client):
    WizardState.objects.create(current_step=1, completed_steps=[], data={})
    response = api_client.put(
        "/api/v1/wizard/state/",
        {"current_step": 2, "completed_steps": [1], "data": {"credentials": [1]}},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["current_step"] == 2
    state = WizardState.objects.first()
    assert state.current_step == 2
    assert state.data == {"credentials": [1]}


def test_reset_wizard_state(api_client):
    WizardState.objects.create(current_step=5, completed_steps=[1, 2, 3, 4], data={"big": "blob"})
    response = api_client.put(
        "/api/v1/wizard/state/",
        {"current_step": 1, "completed_steps": [], "data": {}},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["current_step"] == 1
