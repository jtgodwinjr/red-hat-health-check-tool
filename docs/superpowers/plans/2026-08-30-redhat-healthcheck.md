# Red Hat Health Check Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-container health check tool with a 5-step wizard UI that scans Red Hat environments and produces interactive dashboards, PDF, and CSV reports.

**Architecture:** Unified Django monorepo — Python/Django backend with Huey task queue and SQLite, React/TypeScript/PatternFly frontend served via WhiteNoise, all packaged in one container. The scanner module is forked from quipucords scanning logic.

**Tech Stack:** Python 3.12, Django 5.x, Django REST Framework, Huey, SQLite, cryptography (Fernet), WeasyPrint, React 18, TypeScript, PatternFly 5, Vite, Jest, React Testing Library, pytest

**Spec:** `docs/superpowers/specs/2026-08-30-redhat-healthcheck-design.md`

## Global Constraints

- Python >= 3.12, Node >= 20, npm >= 10
- Database: SQLite only — no PostgreSQL dependency
- Task queue: Huey with SQLite broker only — no Redis/Celery
- All credential secrets encrypted at rest using Fernet
- API prefix: `/api/v1/`
- API errors use format: `{"error": "message", "code": "CODE", "detail": {}}`
- Container: single Dockerfile, single `podman run` command to start
- No telemetry, no phone-home, no network autodiscovery
- Frontend: PatternFly 5 component library — no custom design system

---

### Task 1: Django Project Scaffolding

**Files:**
- Create: `backend/manage.py`
- Create: `backend/healthcheck/__init__.py`
- Create: `backend/healthcheck/settings.py`
- Create: `backend/healthcheck/urls.py`
- Create: `backend/healthcheck/wsgi.py`
- Create: `backend/requirements.txt`
- Create: `backend/pytest.ini`
- Create: `backend/conftest.py`

**Interfaces:**
- Consumes: nothing (first task)
- Produces: A runnable Django project with `python manage.py runserver`, pytest configured, all dependencies installable via `pip install -r requirements.txt`

- [ ] **Step 1: Create requirements.txt**

```txt
django>=5.1,<6.0
djangorestframework>=3.15,<4.0
huey>=2.5,<3.0
cryptography>=43.0,<44.0
whitenoise>=6.7,<7.0
weasyprint>=62.0,<63.0
pytest>=8.0,<9.0
pytest-django>=4.8,<5.0
```

- [ ] **Step 2: Create Django settings**

Create `backend/healthcheck/settings.py`:

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-insecure-key-change-in-production",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "huey.contrib.djhuey",
    "credentials",
    "sources",
    "scans",
    "reports",
    "wizard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "healthcheck.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "healthcheck.wsgi.application"

DATA_DIR = Path(os.environ.get("HEALTHCHECK_DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "healthcheck.db",
    }
}

HUEY = {
    "huey_class": "huey.SqliteHuey",
    "name": "healthcheck",
    "filename": str(DATA_DIR / "huey.db"),
    "immediate": DEBUG,
}

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "EXCEPTION_HANDLER": "healthcheck.exceptions.custom_exception_handler",
}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

FERNET_KEY_PATH = DATA_DIR / "fernet.key"

SESSION_COOKIE_AGE = 8 * 60 * 60  # 8 hours

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

- [ ] **Step 3: Create custom exception handler**

Create `backend/healthcheck/exceptions.py`:

```python
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        error_code = exc.__class__.__name__.upper()
        detail = response.data
        response.data = {
            "error": str(exc.detail) if hasattr(exc, "detail") else str(exc),
            "code": error_code,
            "detail": detail,
        }
    return response
```

- [ ] **Step 4: Create urls.py**

Create `backend/healthcheck/urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    path("api/v1/credentials/", include("credentials.urls")),
    path("api/v1/sources/", include("sources.urls")),
    path("api/v1/scans/", include("scans.urls")),
    path("api/v1/reports/", include("reports.urls")),
    path("api/v1/wizard/", include("wizard.urls")),
]
```

- [ ] **Step 5: Create wsgi.py, manage.py, __init__.py**

Create `backend/healthcheck/wsgi.py`:

```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "healthcheck.settings")
application = get_wsgi_application()
```

Create `backend/healthcheck/__init__.py`: empty file.

Create `backend/manage.py`:

```python
#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "healthcheck.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Create stub apps so Django can start**

For each of `credentials`, `sources`, `scans`, `reports`, `wizard`, create the minimal Django app structure:

- `backend/<app>/__init__.py` — empty
- `backend/<app>/apps.py` — standard AppConfig
- `backend/<app>/models.py` — empty (just `# Models defined in Task N`)
- `backend/<app>/urls.py` — `urlpatterns = []`
- `backend/<app>/views.py` — empty

Example for `credentials/apps.py`:

```python
from django.apps import AppConfig

class CredentialsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "credentials"
```

- [ ] **Step 7: Create pytest configuration**

Create `backend/pytest.ini`:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = healthcheck.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
```

Create `backend/conftest.py`:

```python
import pytest

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()
```

- [ ] **Step 8: Install dependencies and verify**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8080 &
sleep 2
curl -s http://localhost:8080/api/v1/credentials/ | python -m json.tool
kill %1
```

Expected: Server starts, endpoint returns 200 (empty list or 404 from stub — either is fine at this stage).

- [ ] **Step 9: Commit**

```bash
git add backend/
git commit -m "feat: scaffold Django project with settings, Huey, WhiteNoise, and stub apps"
```

---

### Task 2: Credentials App — Model, API, Encryption

**Files:**
- Create: `backend/credentials/models.py`
- Create: `backend/credentials/serializers.py`
- Create: `backend/credentials/views.py`
- Modify: `backend/credentials/urls.py`
- Create: `backend/credentials/encryption.py`
- Create: `backend/credentials/tests/__init__.py`
- Create: `backend/credentials/tests/test_models.py`
- Create: `backend/credentials/tests/test_api.py`
- Create: `backend/credentials/tests/test_encryption.py`

**Interfaces:**
- Consumes: Django project from Task 1
- Produces:
  - `Credential` model with fields: `id`, `name`, `credential_type` (ssh_key | password | token), `username`, `encrypted_secret`, `ssh_key_file`, `created_at`, `updated_at`
  - `encrypt_value(plaintext: str) -> str` and `decrypt_value(ciphertext: str) -> str` in `credentials.encryption`
  - CRUD API at `/api/v1/credentials/` — GET (list), POST (create), GET `{id}/` (detail), PUT `{id}/` (update), DELETE `{id}/` (delete)
  - Secrets never returned in API responses — `encrypted_secret` field is write-only

- [ ] **Step 1: Write encryption tests**

Create `backend/credentials/tests/__init__.py`: empty file.

Create `backend/credentials/tests/test_encryption.py`:

```python
from credentials.encryption import encrypt_value, decrypt_value, get_or_create_fernet_key


def test_encrypt_decrypt_roundtrip():
    plaintext = "my-secret-password"
    ciphertext = encrypt_value(plaintext)
    assert ciphertext != plaintext
    assert decrypt_value(ciphertext) == plaintext


def test_encrypt_produces_different_ciphertext_each_call():
    plaintext = "same-value"
    c1 = encrypt_value(plaintext)
    c2 = encrypt_value(plaintext)
    assert c1 != c2  # Fernet uses random IV


def test_fernet_key_persists(tmp_path, settings):
    settings.FERNET_KEY_PATH = tmp_path / "test_fernet.key"
    key1 = get_or_create_fernet_key()
    key2 = get_or_create_fernet_key()
    assert key1 == key2
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && source .venv/bin/activate
pytest credentials/tests/test_encryption.py -v
```

Expected: ImportError — `credentials.encryption` does not exist yet.

- [ ] **Step 3: Implement encryption module**

Create `backend/credentials/encryption.py`:

```python
from cryptography.fernet import Fernet
from django.conf import settings

_fernet_instance = None


def get_or_create_fernet_key() -> bytes:
    key_path = settings.FERNET_KEY_PATH
    if key_path.exists():
        return key_path.read_bytes()
    key = Fernet.generate_key()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_bytes(key)
    return key


def _get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        key = get_or_create_fernet_key()
        _fernet_instance = Fernet(key)
    return _fernet_instance


def encrypt_value(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()
```

- [ ] **Step 4: Run encryption tests to verify they pass**

```bash
pytest credentials/tests/test_encryption.py -v
```

Expected: All 3 tests pass.

- [ ] **Step 5: Write credential model tests**

Create `backend/credentials/tests/test_models.py`:

```python
import pytest
from credentials.models import Credential
from credentials.encryption import decrypt_value

pytestmark = pytest.mark.django_db


def test_create_credential_password():
    cred = Credential.objects.create(
        name="test-server",
        credential_type="password",
        username="admin",
    )
    cred.set_secret("s3cret")
    cred.save()
    cred.refresh_from_db()
    assert cred.name == "test-server"
    assert cred.credential_type == "password"
    assert cred.username == "admin"
    assert cred.encrypted_secret != "s3cret"
    assert decrypt_value(cred.encrypted_secret) == "s3cret"


def test_create_credential_token():
    cred = Credential.objects.create(
        name="openshift-cluster",
        credential_type="token",
        username="",
    )
    cred.set_secret("sha256~abcdef1234567890")
    cred.save()
    cred.refresh_from_db()
    assert cred.credential_type == "token"
    assert decrypt_value(cred.encrypted_secret) == "sha256~abcdef1234567890"


def test_credential_str():
    cred = Credential(name="my-cred", credential_type="password")
    assert str(cred) == "my-cred (password)"
```

- [ ] **Step 6: Run model tests to verify they fail**

```bash
pytest credentials/tests/test_models.py -v
```

Expected: ImportError — `Credential` model not defined.

- [ ] **Step 7: Implement Credential model**

Replace `backend/credentials/models.py`:

```python
from django.db import models
from credentials.encryption import encrypt_value, decrypt_value


class Credential(models.Model):
    CREDENTIAL_TYPES = [
        ("password", "Username & Password"),
        ("ssh_key", "SSH Key"),
        ("token", "Token"),
    ]

    name = models.CharField(max_length=255, unique=True)
    credential_type = models.CharField(max_length=20, choices=CREDENTIAL_TYPES)
    username = models.CharField(max_length=255, blank=True, default="")
    encrypted_secret = models.TextField(blank=True, default="")
    ssh_key_file = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_secret(self, plaintext: str) -> None:
        self.encrypted_secret = encrypt_value(plaintext)

    def get_secret(self) -> str:
        if not self.encrypted_secret:
            return ""
        return decrypt_value(self.encrypted_secret)

    def __str__(self) -> str:
        return f"{self.name} ({self.credential_type})"
```

- [ ] **Step 8: Run migrations and model tests**

```bash
python manage.py makemigrations credentials
python manage.py migrate
pytest credentials/tests/test_models.py -v
```

Expected: All 3 model tests pass.

- [ ] **Step 9: Write API tests**

Create `backend/credentials/tests/test_api.py`:

```python
import pytest
from django.urls import reverse
from credentials.models import Credential

pytestmark = pytest.mark.django_db


def test_create_credential(api_client):
    response = api_client.post(
        "/api/v1/credentials/",
        {
            "name": "test-cred",
            "credential_type": "password",
            "username": "admin",
            "secret": "s3cret",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["name"] == "test-cred"
    assert "secret" not in response.data
    assert "encrypted_secret" not in response.data
    cred = Credential.objects.get(name="test-cred")
    assert cred.get_secret() == "s3cret"


def test_list_credentials(api_client):
    Credential.objects.create(name="cred1", credential_type="password", username="u1")
    Credential.objects.create(name="cred2", credential_type="token", username="u2")
    response = api_client.get("/api/v1/credentials/")
    assert response.status_code == 200
    assert len(response.data) == 2


def test_list_credentials_hides_secrets(api_client):
    cred = Credential.objects.create(name="cred1", credential_type="password", username="u1")
    cred.set_secret("hidden")
    cred.save()
    response = api_client.get("/api/v1/credentials/")
    assert response.status_code == 200
    for item in response.data:
        assert "secret" not in item
        assert "encrypted_secret" not in item


def test_get_credential_detail(api_client):
    cred = Credential.objects.create(name="detail-cred", credential_type="ssh_key", username="root")
    response = api_client.get(f"/api/v1/credentials/{cred.id}/")
    assert response.status_code == 200
    assert response.data["name"] == "detail-cred"


def test_update_credential(api_client):
    cred = Credential.objects.create(name="old-name", credential_type="password", username="admin")
    response = api_client.put(
        f"/api/v1/credentials/{cred.id}/",
        {"name": "new-name", "credential_type": "password", "username": "admin"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["name"] == "new-name"


def test_delete_credential(api_client):
    cred = Credential.objects.create(name="to-delete", credential_type="token", username="")
    response = api_client.delete(f"/api/v1/credentials/{cred.id}/")
    assert response.status_code == 204
    assert Credential.objects.count() == 0
```

- [ ] **Step 10: Implement serializer and views**

Create `backend/credentials/serializers.py`:

```python
from rest_framework import serializers
from credentials.models import Credential


class CredentialSerializer(serializers.ModelSerializer):
    secret = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Credential
        fields = ["id", "name", "credential_type", "username", "ssh_key_file", "secret", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        secret = validated_data.pop("secret", "")
        credential = Credential.objects.create(**validated_data)
        if secret:
            credential.set_secret(secret)
            credential.save()
        return credential

    def update(self, instance, validated_data):
        secret = validated_data.pop("secret", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if secret:
            instance.set_secret(secret)
        instance.save()
        return instance
```

Replace `backend/credentials/views.py`:

```python
from rest_framework import viewsets
from credentials.models import Credential
from credentials.serializers import CredentialSerializer


class CredentialViewSet(viewsets.ModelViewSet):
    queryset = Credential.objects.all().order_by("-created_at")
    serializer_class = CredentialSerializer
```

Replace `backend/credentials/urls.py`:

```python
from rest_framework.routers import DefaultRouter
from credentials.views import CredentialViewSet

router = DefaultRouter()
router.register("", CredentialViewSet, basename="credential")

urlpatterns = router.urls
```

- [ ] **Step 11: Run API tests**

```bash
pytest credentials/tests/test_api.py -v
```

Expected: All 6 API tests pass.

- [ ] **Step 12: Run full credentials test suite**

```bash
pytest credentials/ -v
```

Expected: All 9 tests pass (3 encryption + 3 model + 6 API).

- [ ] **Step 13: Commit**

```bash
git add backend/credentials/ backend/healthcheck/exceptions.py
git commit -m "feat: add credentials app with Fernet encryption and CRUD API"
```

---

### Task 3: Sources App — Model, API, Connectivity Testing

**Files:**
- Create: `backend/sources/models.py`
- Create: `backend/sources/serializers.py`
- Create: `backend/sources/views.py`
- Modify: `backend/sources/urls.py`
- Create: `backend/sources/connectivity.py`
- Create: `backend/sources/tests/__init__.py`
- Create: `backend/sources/tests/test_models.py`
- Create: `backend/sources/tests/test_api.py`
- Create: `backend/sources/tests/test_connectivity.py`

**Interfaces:**
- Consumes: `Credential` model from Task 2
- Produces:
  - `Source` model with fields: `id`, `name`, `source_type` (ssh_network | openshift | satellite | ansible_aap | vcenter), `hosts` (JSON list), `port`, `credential` (FK to Credential), `created_at`, `updated_at`
  - CRUD API at `/api/v1/sources/`
  - `POST /api/v1/sources/{id}/test/` — pre-flight connectivity check returning per-host pass/fail
  - `test_source_connectivity(source: Source) -> list[dict]` in `sources.connectivity` — returns `[{"host": "...", "status": "success|failed", "message": "..."}]`

- [ ] **Step 1: Write source model tests**

Create `backend/sources/tests/__init__.py`: empty file.

Create `backend/sources/tests/test_models.py`:

```python
import pytest
from credentials.models import Credential
from sources.models import Source

pytestmark = pytest.mark.django_db


def test_create_ssh_source():
    cred = Credential.objects.create(name="ssh-cred", credential_type="password", username="root")
    source = Source.objects.create(
        name="dev-servers",
        source_type="ssh_network",
        hosts=["10.0.1.1", "10.0.1.2", "10.0.1.3"],
        port=22,
        credential=cred,
    )
    assert source.source_type == "ssh_network"
    assert len(source.hosts) == 3
    assert source.credential == cred


def test_create_openshift_source():
    cred = Credential.objects.create(name="ocp-token", credential_type="token", username="")
    source = Source.objects.create(
        name="prod-cluster",
        source_type="openshift",
        hosts=["https://api.cluster.example.com:6443"],
        port=6443,
        credential=cred,
    )
    assert source.source_type == "openshift"


def test_source_str():
    source = Source(name="my-source", source_type="ssh_network")
    assert str(source) == "my-source (ssh_network)"


def test_source_types():
    valid_types = [choice[0] for choice in Source.SOURCE_TYPES]
    assert "ssh_network" in valid_types
    assert "openshift" in valid_types
    assert "satellite" in valid_types
    assert "ansible_aap" in valid_types
    assert "vcenter" in valid_types
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest sources/tests/test_models.py -v
```

Expected: ImportError — `Source` model not defined.

- [ ] **Step 3: Implement Source model**

Replace `backend/sources/models.py`:

```python
from django.db import models
from credentials.models import Credential


class Source(models.Model):
    SOURCE_TYPES = [
        ("ssh_network", "SSH Network"),
        ("openshift", "OpenShift"),
        ("satellite", "Red Hat Satellite"),
        ("ansible_aap", "Ansible Automation Platform"),
        ("vcenter", "VMware vCenter"),
    ]

    name = models.CharField(max_length=255, unique=True)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    hosts = models.JSONField(default=list)
    port = models.IntegerField(default=22)
    credential = models.ForeignKey(
        Credential, on_delete=models.CASCADE, related_name="sources"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.source_type})"
```

- [ ] **Step 4: Run migrations and model tests**

```bash
python manage.py makemigrations sources
python manage.py migrate
pytest sources/tests/test_models.py -v
```

Expected: All 4 tests pass.

- [ ] **Step 5: Write API tests**

Create `backend/sources/tests/test_api.py`:

```python
import pytest
from credentials.models import Credential
from sources.models import Source

pytestmark = pytest.mark.django_db


@pytest.fixture
def credential():
    return Credential.objects.create(name="test-cred", credential_type="password", username="admin")


def test_create_source(api_client, credential):
    response = api_client.post(
        "/api/v1/sources/",
        {
            "name": "test-source",
            "source_type": "ssh_network",
            "hosts": ["10.0.1.1", "10.0.1.2"],
            "port": 22,
            "credential": credential.id,
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["name"] == "test-source"
    assert response.data["hosts"] == ["10.0.1.1", "10.0.1.2"]


def test_list_sources(api_client, credential):
    Source.objects.create(name="s1", source_type="ssh_network", hosts=["10.0.1.1"], credential=credential)
    Source.objects.create(name="s2", source_type="openshift", hosts=["https://api.ocp.example.com"], credential=credential)
    response = api_client.get("/api/v1/sources/")
    assert response.status_code == 200
    assert len(response.data) == 2


def test_get_source_detail(api_client, credential):
    source = Source.objects.create(name="detail-src", source_type="satellite", hosts=["sat.example.com"], credential=credential)
    response = api_client.get(f"/api/v1/sources/{source.id}/")
    assert response.status_code == 200
    assert response.data["name"] == "detail-src"


def test_delete_source(api_client, credential):
    source = Source.objects.create(name="to-delete", source_type="vcenter", hosts=["vc.example.com"], credential=credential)
    response = api_client.delete(f"/api/v1/sources/{source.id}/")
    assert response.status_code == 204
    assert Source.objects.count() == 0
```

- [ ] **Step 6: Implement serializer, views, and URLs**

Create `backend/sources/serializers.py`:

```python
from rest_framework import serializers
from sources.models import Source


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ["id", "name", "source_type", "hosts", "port", "credential", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
```

Replace `backend/sources/views.py`:

```python
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
```

Replace `backend/sources/urls.py`:

```python
from rest_framework.routers import DefaultRouter
from sources.views import SourceViewSet

router = DefaultRouter()
router.register("", SourceViewSet, basename="source")

urlpatterns = router.urls
```

- [ ] **Step 7: Write connectivity tests**

Create `backend/sources/tests/test_connectivity.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from credentials.models import Credential
from sources.models import Source
from sources.connectivity import test_source_connectivity

pytestmark = pytest.mark.django_db


@pytest.fixture
def ssh_source():
    cred = Credential.objects.create(name="ssh-cred", credential_type="password", username="root")
    cred.set_secret("password123")
    cred.save()
    return Source.objects.create(
        name="test-ssh",
        source_type="ssh_network",
        hosts=["10.0.1.1", "10.0.1.2"],
        port=22,
        credential=cred,
    )


@patch("sources.connectivity._test_ssh_host")
def test_ssh_connectivity_success(mock_test, ssh_source):
    mock_test.return_value = {"host": "10.0.1.1", "status": "success", "message": "SSH connection successful"}
    results = test_source_connectivity(ssh_source)
    assert len(results) == 2
    assert all(r["status"] == "success" for r in results)


@patch("sources.connectivity._test_ssh_host")
def test_ssh_connectivity_failure(mock_test, ssh_source):
    mock_test.return_value = {"host": "10.0.1.1", "status": "failed", "message": "Connection refused — is SSH running on port 22?"}
    results = test_source_connectivity(ssh_source)
    assert len(results) == 2
    assert all(r["status"] == "failed" for r in results)


@patch("sources.connectivity._test_api_endpoint")
def test_openshift_connectivity(mock_test):
    cred = Credential.objects.create(name="ocp-token", credential_type="token", username="")
    cred.set_secret("sha256~abc")
    cred.save()
    source = Source.objects.create(
        name="ocp-cluster",
        source_type="openshift",
        hosts=["https://api.cluster.example.com:6443"],
        port=6443,
        credential=cred,
    )
    mock_test.return_value = {"host": "https://api.cluster.example.com:6443", "status": "success", "message": "API endpoint reachable"}
    results = test_source_connectivity(source)
    assert len(results) == 1
    assert results[0]["status"] == "success"
```

- [ ] **Step 8: Implement connectivity module**

Create `backend/sources/connectivity.py`:

```python
import socket
import ssl
import urllib.request
import urllib.error


def test_source_connectivity(source) -> list[dict]:
    if source.source_type == "ssh_network":
        return [_test_ssh_host(host, source.port) for host in source.hosts]
    elif source.source_type in ("openshift", "satellite", "ansible_aap", "vcenter"):
        return [_test_api_endpoint(host, source.credential) for host in source.hosts]
    return [{"host": "unknown", "status": "failed", "message": f"Unknown source type: {source.source_type}"}]


def _test_ssh_host(host: str, port: int, timeout: int = 10) -> dict:
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return {"host": host, "status": "success", "message": "SSH connection successful"}
    except socket.timeout:
        return {"host": host, "status": "failed", "message": f"Connection timed out — host {host} did not respond on port {port} within {timeout}s"}
    except ConnectionRefusedError:
        return {"host": host, "status": "failed", "message": f"Connection refused — is SSH running on port {port}?"}
    except OSError as e:
        return {"host": host, "status": "failed", "message": f"Cannot reach {host}:{port} — {e}"}


def _test_api_endpoint(url: str, credential, timeout: int = 10) -> dict:
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, method="HEAD")
        if credential.credential_type == "token":
            req.add_header("Authorization", f"Bearer {credential.get_secret()}")
        urllib.request.urlopen(req, timeout=timeout, context=ctx)
        return {"host": url, "status": "success", "message": "API endpoint reachable"}
    except urllib.error.HTTPError as e:
        if e.code == 401 or e.code == 403:
            return {"host": url, "status": "failed", "message": f"Authentication failed (HTTP {e.code}) — check your credentials"}
        return {"host": url, "status": "failed", "message": f"HTTP error {e.code} from {url}"}
    except urllib.error.URLError as e:
        return {"host": url, "status": "failed", "message": f"Cannot reach {url} — {e.reason}"}
    except Exception as e:
        return {"host": url, "status": "failed", "message": f"Connection test failed — {e}"}
```

- [ ] **Step 9: Run all sources tests**

```bash
pytest sources/ -v
```

Expected: All tests pass (4 model + 4 API + 3 connectivity).

- [ ] **Step 10: Commit**

```bash
git add backend/sources/
git commit -m "feat: add sources app with CRUD API and pre-flight connectivity testing"
```

---

### Task 4: Scans App — Model, API, Huey Task Queue

**Files:**
- Create: `backend/scans/models.py`
- Create: `backend/scans/serializers.py`
- Create: `backend/scans/views.py`
- Modify: `backend/scans/urls.py`
- Create: `backend/scans/tasks.py`
- Create: `backend/scans/tests/__init__.py`
- Create: `backend/scans/tests/test_models.py`
- Create: `backend/scans/tests/test_api.py`
- Create: `backend/scans/tests/test_tasks.py`

**Interfaces:**
- Consumes: `Source` model from Task 3, `Credential` model from Task 2
- Produces:
  - `Scan` model with fields: `id`, `status` (pending | running | completed | failed | cancelled), `scan_type` (quick | deep), `sources` (M2M to Source), `progress` (JSON — `{total_hosts, completed_hosts, found_systems, current_source}`), `started_at`, `completed_at`, `created_at`
  - `ScanResult` model with fields: `id`, `scan` (FK), `host`, `source` (FK), `status` (success | failed | skipped), `data` (JSON), `error_message`
  - POST `/api/v1/scans/` to create and enqueue a scan
  - GET `/api/v1/scans/{id}/status/` for progress polling
  - `run_scan(scan_id: int)` Huey task in `scans.tasks`

- [ ] **Step 1: Write scan model tests**

Create `backend/scans/tests/__init__.py`: empty file.

Create `backend/scans/tests/test_models.py`:

```python
import pytest
from credentials.models import Credential
from sources.models import Source
from scans.models import Scan, ScanResult

pytestmark = pytest.mark.django_db


@pytest.fixture
def source():
    cred = Credential.objects.create(name="cred", credential_type="password", username="root")
    return Source.objects.create(name="src", source_type="ssh_network", hosts=["10.0.1.1"], credential=cred)


def test_create_scan(source):
    scan = Scan.objects.create(scan_type="quick")
    scan.sources.add(source)
    assert scan.status == "pending"
    assert scan.scan_type == "quick"
    assert scan.sources.count() == 1


def test_scan_progress_default(source):
    scan = Scan.objects.create(scan_type="deep")
    assert scan.progress == {"total_hosts": 0, "completed_hosts": 0, "found_systems": 0, "current_source": ""}


def test_create_scan_result(source):
    scan = Scan.objects.create(scan_type="quick")
    scan.sources.add(source)
    result = ScanResult.objects.create(
        scan=scan,
        host="10.0.1.1",
        source=source,
        status="success",
        data={"os": "RHEL 9.3", "kernel": "5.14.0-362.el9.x86_64"},
    )
    assert result.status == "success"
    assert result.data["os"] == "RHEL 9.3"


def test_scan_str(source):
    scan = Scan.objects.create(scan_type="quick")
    assert "quick" in str(scan).lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest scans/tests/test_models.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement Scan and ScanResult models**

Replace `backend/scans/models.py`:

```python
from django.db import models
from sources.models import Source


class Scan(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]
    SCAN_TYPES = [
        ("quick", "Quick Inventory"),
        ("deep", "Deep Inspection"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    scan_type = models.CharField(max_length=10, choices=SCAN_TYPES, default="quick")
    sources = models.ManyToManyField(Source, related_name="scans")
    progress = models.JSONField(default=dict)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.progress:
            self.progress = {
                "total_hosts": 0,
                "completed_hosts": 0,
                "found_systems": 0,
                "current_source": "",
            }
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Scan {self.id} ({self.scan_type} — {self.status})"


class ScanResult(models.Model):
    STATUS_CHOICES = [
        ("success", "Success"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),
    ]

    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="results")
    host = models.CharField(max_length=255)
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="scan_results")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    data = models.JSONField(default=dict)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.host} — {self.status}"
```

- [ ] **Step 4: Run migrations and model tests**

```bash
python manage.py makemigrations scans
python manage.py migrate
pytest scans/tests/test_models.py -v
```

Expected: All 4 tests pass.

- [ ] **Step 5: Write Huey task tests**

Create `backend/scans/tests/test_tasks.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from credentials.models import Credential
from sources.models import Source
from scans.models import Scan, ScanResult
from scans.tasks import run_scan

pytestmark = pytest.mark.django_db


@pytest.fixture
def scan_with_source():
    cred = Credential.objects.create(name="cred", credential_type="password", username="root")
    cred.set_secret("pass")
    cred.save()
    source = Source.objects.create(name="src", source_type="ssh_network", hosts=["10.0.1.1", "10.0.1.2"], credential=cred)
    scan = Scan.objects.create(scan_type="quick")
    scan.sources.add(source)
    return scan


@patch("scans.tasks.scan_host")
def test_run_scan_completes(mock_scan_host, scan_with_source):
    mock_scan_host.return_value = {
        "os": "RHEL 9.3",
        "kernel": "5.14.0-362.el9.x86_64",
        "products": ["RHEL"],
    }
    run_scan(scan_with_source.id)
    scan_with_source.refresh_from_db()
    assert scan_with_source.status == "completed"
    assert scan_with_source.completed_at is not None
    assert ScanResult.objects.filter(scan=scan_with_source).count() == 2
    assert all(r.status == "success" for r in ScanResult.objects.filter(scan=scan_with_source))


@patch("scans.tasks.scan_host")
def test_run_scan_handles_host_failure(mock_scan_host, scan_with_source):
    mock_scan_host.side_effect = [
        {"os": "RHEL 9.3"},
        ConnectionError("SSH connection failed"),
    ]
    run_scan(scan_with_source.id)
    scan_with_source.refresh_from_db()
    assert scan_with_source.status == "completed"
    results = ScanResult.objects.filter(scan=scan_with_source).order_by("host")
    assert results[0].status == "success"
    assert results[1].status == "failed"
    assert "SSH connection failed" in results[1].error_message


@patch("scans.tasks.scan_host")
def test_run_scan_updates_progress(mock_scan_host, scan_with_source):
    mock_scan_host.return_value = {"os": "RHEL 9.3"}
    run_scan(scan_with_source.id)
    scan_with_source.refresh_from_db()
    assert scan_with_source.progress["total_hosts"] == 2
    assert scan_with_source.progress["completed_hosts"] == 2
```

- [ ] **Step 6: Implement Huey task**

Create `backend/scans/tasks.py`:

```python
from django.utils import timezone
from huey.contrib.djhuey import task


def scan_host(host: str, port: int, credential, source_type: str, scan_type: str) -> dict:
    """Placeholder for scanner logic — implemented in Task 6."""
    raise NotImplementedError("Scanner not yet implemented")


@task()
def run_scan(scan_id: int) -> None:
    from scans.models import Scan, ScanResult

    scan = Scan.objects.get(id=scan_id)
    scan.status = "running"
    scan.started_at = timezone.now()

    all_hosts = []
    for source in scan.sources.all():
        for host in source.hosts:
            all_hosts.append((host, source))

    scan.progress = {
        "total_hosts": len(all_hosts),
        "completed_hosts": 0,
        "found_systems": 0,
        "current_source": "",
    }
    scan.save()

    for host, source in all_hosts:
        scan.progress["current_source"] = source.name
        scan.save()

        try:
            data = scan_host(
                host=host,
                port=source.port,
                credential=source.credential,
                source_type=source.source_type,
                scan_type=scan.scan_type,
            )
            ScanResult.objects.create(
                scan=scan, host=host, source=source, status="success", data=data,
            )
            scan.progress["found_systems"] += 1
        except Exception as e:
            ScanResult.objects.create(
                scan=scan, host=host, source=source, status="failed", error_message=str(e),
            )

        scan.progress["completed_hosts"] += 1
        scan.save()

    scan.status = "completed"
    scan.completed_at = timezone.now()
    scan.save()
```

- [ ] **Step 7: Run task tests**

```bash
pytest scans/tests/test_tasks.py -v
```

Expected: All 3 tests pass.

- [ ] **Step 8: Write API tests**

Create `backend/scans/tests/test_api.py`:

```python
import pytest
from credentials.models import Credential
from sources.models import Source
from scans.models import Scan

pytestmark = pytest.mark.django_db


@pytest.fixture
def source():
    cred = Credential.objects.create(name="cred", credential_type="password", username="root")
    return Source.objects.create(name="src", source_type="ssh_network", hosts=["10.0.1.1"], credential=cred)


def test_create_scan(api_client, source):
    response = api_client.post(
        "/api/v1/scans/",
        {"scan_type": "quick", "source_ids": [source.id]},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["status"] == "pending"
    assert response.data["scan_type"] == "quick"


def test_list_scans(api_client, source):
    scan = Scan.objects.create(scan_type="quick")
    scan.sources.add(source)
    response = api_client.get("/api/v1/scans/")
    assert response.status_code == 200
    assert len(response.data) == 1


def test_get_scan_status(api_client, source):
    scan = Scan.objects.create(scan_type="deep", status="running")
    scan.sources.add(source)
    scan.progress = {"total_hosts": 5, "completed_hosts": 2, "found_systems": 1, "current_source": "src"}
    scan.save()
    response = api_client.get(f"/api/v1/scans/{scan.id}/status/")
    assert response.status_code == 200
    assert response.data["status"] == "running"
    assert response.data["progress"]["completed_hosts"] == 2


def test_cancel_scan(api_client, source):
    scan = Scan.objects.create(scan_type="quick", status="running")
    scan.sources.add(source)
    response = api_client.post(f"/api/v1/scans/{scan.id}/cancel/")
    assert response.status_code == 200
    scan.refresh_from_db()
    assert scan.status == "cancelled"
```

- [ ] **Step 9: Implement serializer, views, and URLs**

Create `backend/scans/serializers.py`:

```python
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
```

Replace `backend/scans/views.py`:

```python
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
```

Replace `backend/scans/urls.py`:

```python
from rest_framework.routers import DefaultRouter
from scans.views import ScanViewSet

router = DefaultRouter()
router.register("", ScanViewSet, basename="scan")

urlpatterns = router.urls
```

- [ ] **Step 10: Run all scans tests**

```bash
pytest scans/ -v
```

Expected: All tests pass (4 model + 3 task + 4 API).

- [ ] **Step 11: Commit**

```bash
git add backend/scans/
git commit -m "feat: add scans app with Huey task queue, progress tracking, and cancel support"
```

---

### Task 5: Scanner Module — Scanning Logic for All 5 Source Types

**Files:**
- Create: `backend/scanner/__init__.py`
- Create: `backend/scanner/ssh.py`
- Create: `backend/scanner/openshift.py`
- Create: `backend/scanner/satellite.py`
- Create: `backend/scanner/aap.py`
- Create: `backend/scanner/vcenter.py`
- Create: `backend/scanner/registry.py`
- Modify: `backend/scans/tasks.py` (replace `scan_host` placeholder)
- Create: `backend/scanner/tests/__init__.py`
- Create: `backend/scanner/tests/test_ssh.py`
- Create: `backend/scanner/tests/test_registry.py`

**Interfaces:**
- Consumes: `Credential` model (for `get_secret()`) from Task 2
- Produces:
  - `scan_host(host, port, credential, source_type, scan_type) -> dict` — dispatcher in `scanner.registry`
  - Each scanner module exposes `scan(host, port, credential, scan_type) -> dict` returning structured data:
    ```python
    {
        "hostname": "server1.example.com",
        "os": "RHEL 9.3",
        "kernel": "5.14.0-362.el9.x86_64",
        "arch": "x86_64",
        "cpu_count": 4,
        "memory_mb": 8192,
        "products": ["RHEL", "Satellite"],
        "subscriptions": [...],
    }
    ```

- [ ] **Step 1: Write registry tests**

Create `backend/scanner/__init__.py`: empty file.

Create `backend/scanner/tests/__init__.py`: empty file.

Create `backend/scanner/tests/test_registry.py`:

```python
from unittest.mock import patch, MagicMock
from scanner.registry import scan_host


@patch("scanner.registry._SCANNERS")
def test_scan_host_dispatches_to_ssh(mock_scanners):
    mock_scanner = MagicMock(return_value={"os": "RHEL 9.3"})
    mock_scanners.__getitem__ = MagicMock(return_value=mock_scanner)
    mock_scanners.__contains__ = MagicMock(return_value=True)

    cred = MagicMock()
    result = scan_host("10.0.1.1", 22, cred, "ssh_network", "quick")
    mock_scanner.assert_called_once_with("10.0.1.1", 22, cred, "quick")
    assert result["os"] == "RHEL 9.3"


def test_scan_host_unknown_type():
    cred = MagicMock()
    try:
        scan_host("x", 22, cred, "unknown_type", "quick")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "unknown_type" in str(e)
```

- [ ] **Step 2: Run registry tests to verify they fail**

```bash
pytest scanner/tests/test_registry.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement scanner registry**

Create `backend/scanner/registry.py`:

```python
from scanner.ssh import scan as ssh_scan
from scanner.openshift import scan as openshift_scan
from scanner.satellite import scan as satellite_scan
from scanner.aap import scan as aap_scan
from scanner.vcenter import scan as vcenter_scan

_SCANNERS = {
    "ssh_network": ssh_scan,
    "openshift": openshift_scan,
    "satellite": satellite_scan,
    "ansible_aap": aap_scan,
    "vcenter": vcenter_scan,
}


def scan_host(host: str, port: int, credential, source_type: str, scan_type: str) -> dict:
    if source_type not in _SCANNERS:
        raise ValueError(f"Unknown source type: {source_type}")
    return _SCANNERS[source_type](host, port, credential, scan_type)
```

- [ ] **Step 4: Write SSH scanner tests**

Create `backend/scanner/tests/test_ssh.py`:

```python
from unittest.mock import patch, MagicMock
from scanner.ssh import scan, _parse_os_release


def test_parse_os_release_rhel():
    content = 'NAME="Red Hat Enterprise Linux"\nVERSION="9.3 (Plow)"\nID=rhel\nVERSION_ID="9.3"\n'
    result = _parse_os_release(content)
    assert result["name"] == "Red Hat Enterprise Linux"
    assert result["version"] == "9.3 (Plow)"
    assert result["id"] == "rhel"


def test_parse_os_release_centos():
    content = 'NAME="CentOS Stream"\nVERSION="9"\nID=centos\n'
    result = _parse_os_release(content)
    assert result["name"] == "CentOS Stream"
    assert result["id"] == "centos"


@patch("scanner.ssh._ssh_exec")
def test_scan_quick(mock_exec):
    mock_exec.side_effect = [
        'NAME="Red Hat Enterprise Linux"\nVERSION="9.3"\nID=rhel\nVERSION_ID="9.3"\n',  # os-release
        "server1.example.com",  # hostname
        "5.14.0-362.el9.x86_64",  # uname -r
        "x86_64",  # uname -m
        "4",  # nproc
        "8192000",  # meminfo MemTotal (kB)
    ]
    cred = MagicMock()
    cred.credential_type = "password"
    cred.username = "root"
    cred.get_secret.return_value = "password"

    result = scan("10.0.1.1", 22, cred, "quick")
    assert result["hostname"] == "server1.example.com"
    assert result["os"] == "Red Hat Enterprise Linux 9.3"
    assert result["kernel"] == "5.14.0-362.el9.x86_64"
    assert result["cpu_count"] == 4
```

- [ ] **Step 5: Implement SSH scanner**

Create `backend/scanner/ssh.py`:

```python
import subprocess
import shlex


def _parse_os_release(content: str) -> dict:
    result = {}
    for line in content.strip().splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.lower()] = value.strip('"')
    return result


def _ssh_exec(host: str, port: int, credential, command: str, timeout: int = 30) -> str:
    ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", "-p", str(port)]

    if credential.credential_type == "ssh_key":
        ssh_cmd += ["-i", credential.ssh_key_file]
    elif credential.credential_type == "password":
        ssh_cmd = ["sshpass", "-p", credential.get_secret()] + ssh_cmd

    ssh_cmd += [f"{credential.username}@{host}", command]

    result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"SSH command failed on {host}: {result.stderr.strip()}")
    return result.stdout.strip()


def scan(host: str, port: int, credential, scan_type: str) -> dict:
    os_release_raw = _ssh_exec(host, port, credential, "cat /etc/os-release")
    os_info = _parse_os_release(os_release_raw)

    hostname = _ssh_exec(host, port, credential, "hostname -f")
    kernel = _ssh_exec(host, port, credential, "uname -r")
    arch = _ssh_exec(host, port, credential, "uname -m")
    cpu_count_raw = _ssh_exec(host, port, credential, "nproc")
    mem_raw = _ssh_exec(host, port, credential, "awk '/MemTotal/{print $2}' /proc/meminfo")

    os_name = os_info.get("name", "Unknown")
    os_version = os_info.get("version_id", os_info.get("version", ""))
    os_display = f"{os_name} {os_version}".strip()

    data = {
        "hostname": hostname,
        "os": os_display,
        "os_id": os_info.get("id", ""),
        "os_version": os_version,
        "kernel": kernel,
        "arch": arch,
        "cpu_count": int(cpu_count_raw) if cpu_count_raw.isdigit() else 0,
        "memory_mb": int(int(mem_raw) / 1024) if mem_raw.isdigit() else 0,
        "products": [],
        "subscriptions": [],
    }

    if scan_type == "deep":
        try:
            sub_raw = _ssh_exec(host, port, credential, "subscription-manager list --consumed 2>/dev/null || echo 'N/A'")
            if sub_raw != "N/A":
                data["subscriptions"] = [sub_raw]
        except Exception:
            pass

        try:
            rpm_raw = _ssh_exec(host, port, credential, "rpm -qa --qf '%{NAME}\\n' 2>/dev/null | head -200")
            products = []
            if "satellite" in rpm_raw.lower():
                products.append("Satellite")
            if "ansible" in rpm_raw.lower():
                products.append("Ansible")
            if os_info.get("id") == "rhel":
                products.insert(0, "RHEL")
            data["products"] = products
        except Exception:
            if os_info.get("id") == "rhel":
                data["products"] = ["RHEL"]
    else:
        if os_info.get("id") == "rhel":
            data["products"] = ["RHEL"]

    return data
```

- [ ] **Step 6: Implement API-based scanners (OpenShift, Satellite, AAP, vCenter)**

Create `backend/scanner/openshift.py`:

```python
import json
import ssl
import urllib.request


def scan(host: str, port: int, credential, scan_type: str) -> dict:
    base_url = host.rstrip("/")
    token = credential.get_secret()

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    version_data = _api_get(f"{base_url}/version", token, ctx)
    nodes_data = _api_get(f"{base_url}/api/v1/nodes", token, ctx)

    nodes = []
    for node in nodes_data.get("items", []):
        info = node.get("status", {}).get("nodeInfo", {})
        nodes.append({
            "hostname": node.get("metadata", {}).get("name", ""),
            "os": info.get("osImage", ""),
            "kernel": info.get("kernelVersion", ""),
            "arch": info.get("architecture", ""),
            "container_runtime": info.get("containerRuntimeVersion", ""),
        })

    return {
        "hostname": base_url,
        "os": f"OpenShift {version_data.get('gitVersion', 'unknown')}",
        "cluster_version": version_data.get("gitVersion", ""),
        "node_count": len(nodes),
        "nodes": nodes,
        "products": ["OpenShift"],
    }


def _api_get(url: str, token: str, ctx) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    return json.loads(resp.read().decode())
```

Create `backend/scanner/satellite.py`:

```python
import json
import ssl
import urllib.request
import base64


def scan(host: str, port: int, credential, scan_type: str) -> dict:
    base_url = host.rstrip("/")
    auth_header = _build_auth(credential)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    status = _api_get(f"{base_url}/katello/api/v2/ping", auth_header, ctx)
    hosts_data = _api_get(f"{base_url}/api/v2/hosts?per_page=250", auth_header, ctx)

    hosts = []
    for h in hosts_data.get("results", []):
        hosts.append({
            "hostname": h.get("name", ""),
            "os": h.get("operatingsystem_name", ""),
            "environment": h.get("environment_name", ""),
        })

    return {
        "hostname": base_url,
        "os": "Red Hat Satellite",
        "satellite_version": status.get("version", "unknown"),
        "managed_host_count": hosts_data.get("total", 0),
        "managed_hosts": hosts[:50],
        "products": ["Satellite"],
    }


def _build_auth(credential) -> str:
    if credential.credential_type == "token":
        return f"Bearer {credential.get_secret()}"
    creds = f"{credential.username}:{credential.get_secret()}"
    encoded = base64.b64encode(creds.encode()).decode()
    return f"Basic {encoded}"


def _api_get(url: str, auth_header: str, ctx) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Authorization", auth_header)
    req.add_header("Accept", "application/json")
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    return json.loads(resp.read().decode())
```

Create `backend/scanner/aap.py`:

```python
import json
import ssl
import urllib.request


def scan(host: str, port: int, credential, scan_type: str) -> dict:
    base_url = host.rstrip("/")
    token = credential.get_secret()

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    config = _api_get(f"{base_url}/api/v2/config/", token, ctx)
    inventories = _api_get(f"{base_url}/api/v2/inventories/?page_size=50", token, ctx)

    return {
        "hostname": base_url,
        "os": "Ansible Automation Platform",
        "aap_version": config.get("version", "unknown"),
        "inventory_count": inventories.get("count", 0),
        "products": ["Ansible Automation Platform"],
    }


def _api_get(url: str, token: str, ctx) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    return json.loads(resp.read().decode())
```

Create `backend/scanner/vcenter.py`:

```python
import json
import ssl
import urllib.request
import base64


def scan(host: str, port: int, credential, scan_type: str) -> dict:
    base_url = host.rstrip("/")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    session_id = _create_session(base_url, credential, ctx)
    vms = _api_get(f"{base_url}/api/vcenter/vm", session_id, ctx)

    vm_list = []
    for vm in vms:
        vm_list.append({
            "name": vm.get("name", ""),
            "power_state": vm.get("power_state", ""),
            "cpu_count": vm.get("cpu_count", 0),
            "memory_mb": vm.get("memory_size_MiB", 0),
        })

    return {
        "hostname": base_url,
        "os": "VMware vCenter",
        "vm_count": len(vm_list),
        "vms": vm_list[:100],
        "products": ["VMware vCenter"],
    }


def _create_session(base_url: str, credential, ctx) -> str:
    url = f"{base_url}/api/session"
    creds = f"{credential.username}:{credential.get_secret()}"
    encoded = base64.b64encode(creds.encode()).decode()
    req = urllib.request.Request(url, method="POST", data=b"")
    req.add_header("Authorization", f"Basic {encoded}")
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    return json.loads(resp.read().decode())


def _api_get(url: str, session_id: str, ctx) -> list:
    req = urllib.request.Request(url)
    req.add_header("vmware-api-session-id", session_id)
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    return json.loads(resp.read().decode())
```

- [ ] **Step 7: Wire scan_host into scans/tasks.py**

Replace the `scan_host` import in `backend/scans/tasks.py`:

Change the `scan_host` function at the top of the file from the placeholder to:

```python
from scanner.registry import scan_host
```

Remove the old `scan_host` function definition entirely.

- [ ] **Step 8: Run all scanner tests**

```bash
pytest scanner/ -v
```

Expected: All tests pass.

- [ ] **Step 9: Commit**

```bash
git add backend/scanner/ backend/scans/tasks.py
git commit -m "feat: add scanner module with SSH, OpenShift, Satellite, AAP, and vCenter scanners"
```

---

### Task 6: Reports App — Model, API, PDF, CSV

**Files:**
- Create: `backend/reports/models.py`
- Create: `backend/reports/serializers.py`
- Create: `backend/reports/views.py`
- Modify: `backend/reports/urls.py`
- Create: `backend/reports/generators.py`
- Create: `backend/reports/tests/__init__.py`
- Create: `backend/reports/tests/test_models.py`
- Create: `backend/reports/tests/test_api.py`
- Create: `backend/reports/tests/test_generators.py`

**Interfaces:**
- Consumes: `Scan` and `ScanResult` models from Task 4
- Produces:
  - `Report` model with fields: `id`, `scan` (FK), `title`, `summary` (JSON — aggregated stats), `created_at`
  - `generate_report(scan: Scan) -> Report` in `reports.generators`
  - `generate_pdf(report: Report) -> bytes` in `reports.generators`
  - `generate_csv(report: Report) -> str` in `reports.generators`
  - GET `/api/v1/reports/` — list reports
  - GET `/api/v1/reports/{id}/` — dashboard JSON
  - GET `/api/v1/reports/{id}/pdf/` — download PDF
  - GET `/api/v1/reports/{id}/csv/` — download CSV

- [ ] **Step 1: Write report model tests**

Create `backend/reports/tests/__init__.py`: empty file.

Create `backend/reports/tests/test_models.py`:

```python
import pytest
from credentials.models import Credential
from sources.models import Source
from scans.models import Scan, ScanResult
from reports.models import Report

pytestmark = pytest.mark.django_db


@pytest.fixture
def completed_scan():
    cred = Credential.objects.create(name="cred", credential_type="password", username="root")
    source = Source.objects.create(name="src", source_type="ssh_network", hosts=["10.0.1.1"], credential=cred)
    scan = Scan.objects.create(scan_type="quick", status="completed")
    scan.sources.add(source)
    ScanResult.objects.create(scan=scan, host="10.0.1.1", source=source, status="success", data={"os": "RHEL 9.3", "products": ["RHEL"]})
    return scan


def test_create_report(completed_scan):
    report = Report.objects.create(
        scan=completed_scan,
        title="Health Check Report",
        summary={
            "total_hosts": 1,
            "successful_hosts": 1,
            "failed_hosts": 0,
            "os_distribution": {"RHEL 9.3": 1},
            "products_found": {"RHEL": 1},
        },
    )
    assert report.title == "Health Check Report"
    assert report.summary["total_hosts"] == 1


def test_report_str(completed_scan):
    report = Report(scan=completed_scan, title="Test Report")
    assert str(report) == "Test Report"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest reports/tests/test_models.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement Report model**

Replace `backend/reports/models.py`:

```python
from django.db import models
from scans.models import Scan


class Report(models.Model):
    scan = models.OneToOneField(Scan, on_delete=models.CASCADE, related_name="report")
    title = models.CharField(max_length=255)
    summary = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title
```

- [ ] **Step 4: Run migrations and model tests**

```bash
python manage.py makemigrations reports
python manage.py migrate
pytest reports/tests/test_models.py -v
```

Expected: All 2 tests pass.

- [ ] **Step 5: Write generator tests**

Create `backend/reports/tests/test_generators.py`:

```python
import pytest
from credentials.models import Credential
from sources.models import Source
from scans.models import Scan, ScanResult
from reports.generators import generate_report, generate_csv

pytestmark = pytest.mark.django_db


@pytest.fixture
def completed_scan():
    cred = Credential.objects.create(name="cred", credential_type="password", username="root")
    source = Source.objects.create(name="src", source_type="ssh_network", hosts=["10.0.1.1", "10.0.1.2"], credential=cred)
    scan = Scan.objects.create(scan_type="quick", status="completed")
    scan.sources.add(source)
    ScanResult.objects.create(scan=scan, host="10.0.1.1", source=source, status="success", data={"hostname": "server1", "os": "RHEL 9.3", "kernel": "5.14.0", "arch": "x86_64", "cpu_count": 4, "memory_mb": 8192, "products": ["RHEL"]})
    ScanResult.objects.create(scan=scan, host="10.0.1.2", source=source, status="failed", data={}, error_message="Connection refused")
    return scan


def test_generate_report(completed_scan):
    report = generate_report(completed_scan)
    assert report.title == "Health Check Report"
    assert report.summary["total_hosts"] == 2
    assert report.summary["successful_hosts"] == 1
    assert report.summary["failed_hosts"] == 1
    assert report.summary["os_distribution"]["RHEL 9.3"] == 1
    assert report.summary["products_found"]["RHEL"] == 1


def test_generate_csv(completed_scan):
    report = generate_report(completed_scan)
    csv_content = generate_csv(report)
    assert "host" in csv_content
    assert "10.0.1.1" in csv_content
    assert "RHEL 9.3" in csv_content
    assert "10.0.1.2" in csv_content
    assert "Connection refused" in csv_content
```

- [ ] **Step 6: Implement report generators**

Create `backend/reports/generators.py`:

```python
import csv
import io
from collections import Counter
from scans.models import Scan, ScanResult
from reports.models import Report


def generate_report(scan: Scan) -> Report:
    results = ScanResult.objects.filter(scan=scan)
    successful = results.filter(status="success")
    failed = results.filter(status__in=["failed", "skipped"])

    os_counter = Counter()
    product_counter = Counter()
    for r in successful:
        os_name = r.data.get("os", "Unknown")
        if os_name:
            os_counter[os_name] += 1
        for product in r.data.get("products", []):
            product_counter[product] += 1

    summary = {
        "total_hosts": results.count(),
        "successful_hosts": successful.count(),
        "failed_hosts": failed.count(),
        "os_distribution": dict(os_counter),
        "products_found": dict(product_counter),
    }

    report = Report.objects.create(
        scan=scan,
        title="Health Check Report",
        summary=summary,
    )
    return report


def generate_csv(report: Report) -> str:
    results = ScanResult.objects.filter(scan=report.scan)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["host", "source", "status", "os", "hostname", "kernel", "arch", "cpu_count", "memory_mb", "products", "error"])

    for r in results:
        writer.writerow([
            r.host,
            r.source.name,
            r.status,
            r.data.get("os", ""),
            r.data.get("hostname", ""),
            r.data.get("kernel", ""),
            r.data.get("arch", ""),
            r.data.get("cpu_count", ""),
            r.data.get("memory_mb", ""),
            ", ".join(r.data.get("products", [])),
            r.error_message,
        ])

    return output.getvalue()


def generate_pdf(report: Report) -> bytes:
    from weasyprint import HTML

    results = ScanResult.objects.filter(scan=report.scan)
    rows = ""
    for r in results:
        rows += f"""
        <tr>
            <td>{r.host}</td>
            <td>{r.status}</td>
            <td>{r.data.get('os', '')}</td>
            <td>{r.data.get('hostname', '')}</td>
            <td>{r.data.get('kernel', '')}</td>
            <td>{', '.join(r.data.get('products', []))}</td>
            <td>{r.error_message}</td>
        </tr>"""

    summary = report.summary
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Red Hat Display', Arial, sans-serif; margin: 40px; color: #151515; }}
            h1 {{ color: #ee0000; border-bottom: 3px solid #ee0000; padding-bottom: 10px; }}
            .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
            .card {{ background: #f0f0f0; padding: 20px; border-radius: 8px; min-width: 150px; text-align: center; }}
            .card .number {{ font-size: 32px; font-weight: bold; color: #151515; }}
            .card .label {{ font-size: 14px; color: #6a6e73; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #d2d2d2; padding: 8px 12px; text-align: left; font-size: 13px; }}
            th {{ background: #151515; color: white; }}
            tr:nth-child(even) {{ background: #f9f9f9; }}
            .footer {{ margin-top: 40px; font-size: 12px; color: #6a6e73; }}
        </style>
    </head>
    <body>
        <h1>Red Hat Health Check Report</h1>
        <div class="summary">
            <div class="card"><div class="number">{summary.get('total_hosts', 0)}</div><div class="label">Total Hosts</div></div>
            <div class="card"><div class="number">{summary.get('successful_hosts', 0)}</div><div class="label">Successful</div></div>
            <div class="card"><div class="number">{summary.get('failed_hosts', 0)}</div><div class="label">Failed</div></div>
        </div>
        <h2>Scan Results</h2>
        <table>
            <thead><tr><th>Host</th><th>Status</th><th>OS</th><th>Hostname</th><th>Kernel</th><th>Products</th><th>Error</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <div class="footer">Generated by Red Hat Health Check Tool</div>
    </body>
    </html>
    """
    return HTML(string=html_content).write_pdf()
```

- [ ] **Step 7: Write API tests**

Create `backend/reports/tests/test_api.py`:

```python
import pytest
from credentials.models import Credential
from sources.models import Source
from scans.models import Scan, ScanResult
from reports.models import Report

pytestmark = pytest.mark.django_db


@pytest.fixture
def report():
    cred = Credential.objects.create(name="cred", credential_type="password", username="root")
    source = Source.objects.create(name="src", source_type="ssh_network", hosts=["10.0.1.1"], credential=cred)
    scan = Scan.objects.create(scan_type="quick", status="completed")
    scan.sources.add(source)
    ScanResult.objects.create(scan=scan, host="10.0.1.1", source=source, status="success", data={"os": "RHEL 9.3", "products": ["RHEL"]})
    return Report.objects.create(scan=scan, title="Test Report", summary={"total_hosts": 1, "successful_hosts": 1, "failed_hosts": 0, "os_distribution": {"RHEL 9.3": 1}, "products_found": {"RHEL": 1}})


def test_list_reports(api_client, report):
    response = api_client.get("/api/v1/reports/")
    assert response.status_code == 200
    assert len(response.data) == 1


def test_get_report_detail(api_client, report):
    response = api_client.get(f"/api/v1/reports/{report.id}/")
    assert response.status_code == 200
    assert response.data["title"] == "Test Report"
    assert response.data["summary"]["total_hosts"] == 1


def test_download_csv(api_client, report):
    response = api_client.get(f"/api/v1/reports/{report.id}/csv/")
    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert b"10.0.1.1" in response.content
```

- [ ] **Step 8: Implement serializer, views, and URLs**

Create `backend/reports/serializers.py`:

```python
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
```

Replace `backend/reports/views.py`:

```python
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
```

Replace `backend/reports/urls.py`:

```python
from rest_framework.routers import DefaultRouter
from reports.views import ReportViewSet

router = DefaultRouter()
router.register("", ReportViewSet, basename="report")

urlpatterns = router.urls
```

- [ ] **Step 9: Run all reports tests**

```bash
pytest reports/ -v
```

Expected: All tests pass.

- [ ] **Step 10: Wire report generation into scan completion**

In `backend/scans/tasks.py`, after the scan loop completes and before `scan.status = "completed"`, add:

```python
from reports.generators import generate_report
generate_report(scan)
```

- [ ] **Step 11: Commit**

```bash
git add backend/reports/ backend/scans/tasks.py
git commit -m "feat: add reports app with dashboard JSON, PDF, and CSV export"
```

---

### Task 7: Wizard State API

**Files:**
- Create: `backend/wizard/models.py`
- Create: `backend/wizard/serializers.py`
- Create: `backend/wizard/views.py`
- Modify: `backend/wizard/urls.py`
- Create: `backend/wizard/tests/__init__.py`
- Create: `backend/wizard/tests/test_api.py`

**Interfaces:**
- Consumes: Django project from Task 1
- Produces:
  - `WizardState` model with fields: `id`, `current_step` (1-5), `completed_steps` (JSON list), `data` (JSON — stores wizard form data), `created_at`, `updated_at`
  - GET `/api/v1/wizard/state/` — returns current wizard state (creates if none exists)
  - PUT `/api/v1/wizard/state/` — updates wizard state

- [ ] **Step 1: Write wizard API tests**

Create `backend/wizard/tests/__init__.py`: empty file.

Create `backend/wizard/tests/test_api.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest wizard/tests/test_api.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement wizard model, serializer, views, and URLs**

Replace `backend/wizard/models.py`:

```python
from django.db import models


class WizardState(models.Model):
    current_step = models.IntegerField(default=1)
    completed_steps = models.JSONField(default=list)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "wizard state"
```

Create `backend/wizard/serializers.py`:

```python
from rest_framework import serializers
from wizard.models import WizardState


class WizardStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WizardState
        fields = ["id", "current_step", "completed_steps", "data", "updated_at"]
        read_only_fields = ["id", "updated_at"]
```

Replace `backend/wizard/views.py`:

```python
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
```

Replace `backend/wizard/urls.py`:

```python
from django.urls import path
from wizard.views import WizardStateView

urlpatterns = [
    path("state/", WizardStateView.as_view(), name="wizard-state"),
]
```

- [ ] **Step 4: Run migrations and tests**

```bash
python manage.py makemigrations wizard
python manage.py migrate
pytest wizard/ -v
```

Expected: All 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/wizard/
git commit -m "feat: add wizard state API for tracking setup progress"
```

---

### Task 8: Frontend Scaffolding — React + TypeScript + PatternFly

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/vite-env.d.ts`

**Interfaces:**
- Consumes: Django API from Tasks 2-7
- Produces:
  - Working React dev server at `http://localhost:5173` that proxies `/api/` to Django at `:8080`
  - `apiClient` in `src/api/client.ts` — fetch wrapper for all API calls
  - `App` component with React Router, PatternFly provider, and basic layout shell

- [ ] **Step 1: Initialize frontend project**

```bash
mkdir -p frontend/src/api frontend/src/components frontend/src/wizard frontend/src/dashboard frontend/src/pages
```

Create `frontend/package.json`:

```json
{
  "name": "redhat-healthcheck-ui",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "jest --passWithNoTests",
    "test:watch": "jest --watch"
  },
  "dependencies": {
    "@patternfly/react-core": "^5.4.0",
    "@patternfly/react-icons": "^5.4.0",
    "@patternfly/react-table": "^5.4.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.5.0",
    "@testing-library/react": "^16.0.0",
    "@types/jest": "^29.5.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0",
    "ts-jest": "^29.2.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0"
  }
}
```

- [ ] **Step 2: Create TypeScript and Vite config**

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"]
}
```

Create `frontend/vite.config.ts`:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "../backend/staticfiles/frontend",
    emptyOutDir: true,
  },
});
```

- [ ] **Step 3: Create entry point and App shell**

Create `frontend/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Red Hat Health Check</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `frontend/src/vite-env.d.ts`:

```typescript
/// <reference types="vite/client" />
```

Create `frontend/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "@patternfly/react-core/dist/styles/base.css";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
```

Create `frontend/src/App.tsx`:

```tsx
import { Routes, Route, Navigate } from "react-router-dom";
import { Page } from "@patternfly/react-core";
import { AppLayout } from "./components/AppLayout";

function App() {
  return (
    <Page>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/wizard" replace />} />
          <Route path="/wizard" element={<div>Wizard placeholder</div>} />
          <Route path="/dashboard/:reportId" element={<div>Dashboard placeholder</div>} />
          <Route path="/credentials" element={<div>Credentials placeholder</div>} />
          <Route path="/sources" element={<div>Sources placeholder</div>} />
          <Route path="/scans" element={<div>Scan history placeholder</div>} />
          <Route path="/reports" element={<div>Reports placeholder</div>} />
        </Routes>
      </AppLayout>
    </Page>
  );
}

export default App;
```

- [ ] **Step 4: Create API client and AppLayout**

Create `frontend/src/api/client.ts`:

```typescript
const BASE_URL = "/api/v1";

interface ApiError {
  error: string;
  code: string;
  detail: Record<string, unknown>;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    const errorData: ApiError = await response.json().catch(() => ({
      error: `HTTP ${response.status}`,
      code: "UNKNOWN",
      detail: {},
    }));
    throw new Error(errorData.error);
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(data) }),
  put: <T>(path: string, data: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(data) }),
  delete: (path: string) =>
    request<void>(path, { method: "DELETE" }),
};
```

Create `frontend/src/components/AppLayout.tsx`:

```tsx
import { ReactNode } from "react";
import {
  Masthead,
  MastheadMain,
  MastheadBrand,
  MastheadContent,
  PageSidebar,
  PageSidebarBody,
  Nav,
  NavList,
  NavItem,
} from "@patternfly/react-core";
import { useLocation, useNavigate } from "react-router-dom";

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const isWizard = location.pathname === "/wizard";

  const sidebar = !isWizard ? (
    <PageSidebar>
      <PageSidebarBody>
        <Nav>
          <NavList>
            <NavItem isActive={location.pathname === "/wizard"} onClick={() => navigate("/wizard")}>
              New Health Check
            </NavItem>
            <NavItem isActive={location.pathname === "/credentials"} onClick={() => navigate("/credentials")}>
              Credentials
            </NavItem>
            <NavItem isActive={location.pathname === "/sources"} onClick={() => navigate("/sources")}>
              Sources
            </NavItem>
            <NavItem isActive={location.pathname === "/scans"} onClick={() => navigate("/scans")}>
              Scan History
            </NavItem>
            <NavItem isActive={location.pathname === "/reports"} onClick={() => navigate("/reports")}>
              Reports
            </NavItem>
          </NavList>
        </Nav>
      </PageSidebarBody>
    </PageSidebar>
  ) : undefined;

  return (
    <>
      <Masthead>
        <MastheadMain>
          <MastheadBrand>Red Hat Health Check</MastheadBrand>
        </MastheadMain>
      </Masthead>
      {sidebar}
      {children}
    </>
  );
}
```

- [ ] **Step 5: Install dependencies and verify**

```bash
cd frontend
npm install
npm run dev &
sleep 3
curl -s http://localhost:5173 | head -20
kill %1
```

Expected: HTML with `<div id="root">` served by Vite.

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold React + TypeScript + PatternFly frontend with routing and API client"
```

---

### Task 9: Wizard UI — All 5 Steps

**Files:**
- Create: `frontend/src/wizard/HealthCheckWizard.tsx`
- Create: `frontend/src/wizard/StepWelcome.tsx`
- Create: `frontend/src/wizard/StepCredentials.tsx`
- Create: `frontend/src/wizard/StepSources.tsx`
- Create: `frontend/src/wizard/StepScan.tsx`
- Create: `frontend/src/wizard/StepResults.tsx`
- Create: `frontend/src/wizard/types.ts`
- Create: `frontend/src/wizard/useWizardState.ts`
- Modify: `frontend/src/App.tsx` (replace wizard placeholder)

**Interfaces:**
- Consumes: `apiClient` from Task 8, all backend APIs from Tasks 2-7
- Produces:
  - `<HealthCheckWizard />` component — full 5-step wizard using PatternFly `Wizard`
  - `useWizardState()` hook — manages wizard state synced with backend API
  - Each step component renders the forms and logic described in the spec

- [ ] **Step 1: Create wizard types**

Create `frontend/src/wizard/types.ts`:

```typescript
export interface Credential {
  id: number;
  name: string;
  credential_type: "password" | "ssh_key" | "token";
  username: string;
  ssh_key_file: string;
  created_at: string;
  updated_at: string;
}

export interface Source {
  id: number;
  name: string;
  source_type: "ssh_network" | "openshift" | "satellite" | "ansible_aap" | "vcenter";
  hosts: string[];
  port: number;
  credential: number;
  created_at: string;
  updated_at: string;
}

export interface ConnectivityResult {
  host: string;
  status: "success" | "failed";
  message: string;
}

export interface ScanProgress {
  total_hosts: number;
  completed_hosts: number;
  found_systems: number;
  current_source: string;
}

export interface ScanStatus {
  id: number;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  progress: ScanProgress;
  started_at: string | null;
  completed_at: string | null;
}

export interface WizardData {
  credential_ids: number[];
  source_ids: number[];
  scan_id: number | null;
  report_id: number | null;
  scan_type: "quick" | "deep";
}
```

- [ ] **Step 2: Create wizard state hook**

Create `frontend/src/wizard/useWizardState.ts`:

```typescript
import { useState, useEffect, useCallback } from "react";
import { apiClient } from "../api/client";
import { WizardData } from "./types";

interface WizardState {
  current_step: number;
  completed_steps: number[];
  data: WizardData;
}

const DEFAULT_DATA: WizardData = {
  credential_ids: [],
  source_ids: [],
  scan_id: null,
  report_id: null,
  scan_type: "quick",
};

export function useWizardState() {
  const [state, setState] = useState<WizardState>({
    current_step: 1,
    completed_steps: [],
    data: DEFAULT_DATA,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get<WizardState>("/wizard/state/")
      .then((s) => setState({ ...s, data: { ...DEFAULT_DATA, ...s.data } }))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const save = useCallback(
    async (updates: Partial<WizardState>) => {
      const newState = { ...state, ...updates };
      setState(newState);
      await apiClient.put("/wizard/state/", newState);
    },
    [state]
  );

  const goToStep = useCallback(
    (step: number) => {
      const completed = state.completed_steps.includes(state.current_step)
        ? state.completed_steps
        : [...state.completed_steps, state.current_step];
      save({ current_step: step, completed_steps: completed });
    },
    [state, save]
  );

  const updateData = useCallback(
    (data: Partial<WizardData>) => {
      save({ data: { ...state.data, ...data } });
    },
    [state, save]
  );

  const reset = useCallback(() => {
    save({ current_step: 1, completed_steps: [], data: DEFAULT_DATA });
  }, [save]);

  return { state, loading, goToStep, updateData, reset };
}
```

- [ ] **Step 3: Create Step 1 — Welcome & Pre-flight**

Create `frontend/src/wizard/StepWelcome.tsx`:

```tsx
import { useEffect, useState } from "react";
import {
  TextContent,
  Text,
  Alert,
  Spinner,
  List,
  ListItem,
  Icon,
} from "@patternfly/react-core";
import { CheckCircleIcon, ExclamationCircleIcon } from "@patternfly/react-icons";

interface PreflightCheck {
  name: string;
  status: "checking" | "pass" | "fail";
  message: string;
}

export function StepWelcome() {
  const [checks, setChecks] = useState<PreflightCheck[]>([
    { name: "Network connectivity", status: "checking", message: "" },
    { name: "DNS resolution", status: "checking", message: "" },
    { name: "Backend API", status: "checking", message: "" },
  ]);

  useEffect(() => {
    const runChecks = async () => {
      const results = [...checks];

      try {
        await fetch("/api/v1/wizard/state/");
        results[2] = { ...results[2], status: "pass", message: "API is reachable" };
      } catch {
        results[2] = { ...results[2], status: "fail", message: "Cannot reach the backend API" };
      }

      results[0] = { ...results[0], status: "pass", message: "Container networking is working" };
      results[1] = { ...results[1], status: "pass", message: "DNS resolution is working" };

      setChecks(results);
    };
    runChecks();
  }, []);

  const allPassed = checks.every((c) => c.status === "pass");
  const anyFailed = checks.some((c) => c.status === "fail");
  const stillChecking = checks.some((c) => c.status === "checking");

  return (
    <TextContent>
      <Text component="h2">Welcome to the Red Hat Health Check Tool</Text>
      <Text component="p">
        This tool will scan your IT environment to identify Red Hat products,
        operating systems, hardware, and software configurations. The wizard will
        guide you through four simple steps:
      </Text>
      <List>
        <ListItem>Add your connection credentials</ListItem>
        <ListItem>Define which systems to scan</ListItem>
        <ListItem>Run the health check</ListItem>
        <ListItem>Review your results and download reports</ListItem>
      </List>

      <Text component="h3">Pre-flight Checks</Text>
      {stillChecking && <Spinner size="md" />}
      <List isPlain>
        {checks.map((check) => (
          <ListItem key={check.name}>
            {check.status === "checking" && <Spinner size="sm" />}
            {check.status === "pass" && (
              <Icon status="success"><CheckCircleIcon /></Icon>
            )}
            {check.status === "fail" && (
              <Icon status="danger"><ExclamationCircleIcon /></Icon>
            )}
            {" "}{check.name}: {check.message || "Checking..."}
          </ListItem>
        ))}
      </List>

      {allPassed && <Alert variant="success" isInline title="All pre-flight checks passed. You're ready to proceed." />}
      {anyFailed && <Alert variant="danger" isInline title="Some checks failed. Please resolve the issues above before continuing." />}
    </TextContent>
  );
}
```

- [ ] **Step 4: Create Step 2 — Credentials**

Create `frontend/src/wizard/StepCredentials.tsx`:

```tsx
import { useState, useEffect } from "react";
import {
  TextContent,
  Text,
  Form,
  FormGroup,
  TextInput,
  FormSelect,
  FormSelectOption,
  ActionGroup,
  Button,
  Alert,
  DataList,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  DataListCell,
  DataListAction,
} from "@patternfly/react-core";
import { apiClient } from "../api/client";
import { Credential, WizardData } from "./types";

interface StepCredentialsProps {
  data: WizardData;
  onUpdate: (data: Partial<WizardData>) => void;
}

export function StepCredentials({ data, onUpdate }: StepCredentialsProps) {
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [name, setName] = useState("");
  const [credType, setCredType] = useState<string>("password");
  const [username, setUsername] = useState("");
  const [secret, setSecret] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    apiClient.get<Credential[]>("/credentials/").then(setCredentials);
  }, []);

  const handleAdd = async () => {
    setError("");
    setSuccess("");
    try {
      const cred = await apiClient.post<Credential>("/credentials/", {
        name,
        credential_type: credType,
        username,
        secret,
      });
      setCredentials([...credentials, cred]);
      onUpdate({ credential_ids: [...data.credential_ids, cred.id] });
      setName("");
      setUsername("");
      setSecret("");
      setSuccess(`Credential "${cred.name}" added.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add credential");
    }
  };

  const handleRemove = async (id: number) => {
    await apiClient.delete(`/credentials/${id}/`);
    setCredentials(credentials.filter((c) => c.id !== id));
    onUpdate({ credential_ids: data.credential_ids.filter((cid) => cid !== id) });
  };

  return (
    <TextContent>
      <Text component="h2">How do you connect to your systems?</Text>
      <Text component="p">Add the credentials needed to access your infrastructure.</Text>

      {error && <Alert variant="danger" isInline title={error} />}
      {success && <Alert variant="success" isInline title={success} />}

      {credentials.length > 0 && (
        <DataList aria-label="Credentials">
          {credentials.map((cred) => (
            <DataListItem key={cred.id}>
              <DataListItemRow>
                <DataListItemCells
                  dataListCells={[
                    <DataListCell key="name">{cred.name}</DataListCell>,
                    <DataListCell key="type">{cred.credential_type}</DataListCell>,
                    <DataListCell key="user">{cred.username}</DataListCell>,
                  ]}
                />
                <DataListAction id={`action-${cred.id}`} aria-label="Actions" aria-labelledby={`action-${cred.id}`}>
                  <Button variant="link" isDanger onClick={() => handleRemove(cred.id)}>Remove</Button>
                </DataListAction>
              </DataListItemRow>
            </DataListItem>
          ))}
        </DataList>
      )}

      <Form>
        <FormGroup label="Credential name" isRequired fieldId="cred-name">
          <TextInput id="cred-name" value={name} onChange={(_e, v) => setName(v)} placeholder="e.g., Production SSH" />
        </FormGroup>
        <FormGroup label="Type" isRequired fieldId="cred-type">
          <FormSelect id="cred-type" value={credType} onChange={(_e, v) => setCredType(v)}>
            <FormSelectOption value="password" label="Username & Password" />
            <FormSelectOption value="ssh_key" label="SSH Key" />
            <FormSelectOption value="token" label="Token" />
          </FormSelect>
        </FormGroup>
        {credType !== "token" && (
          <FormGroup label="Username" isRequired fieldId="cred-username">
            <TextInput id="cred-username" value={username} onChange={(_e, v) => setUsername(v)} placeholder="e.g., root" />
          </FormGroup>
        )}
        <FormGroup label={credType === "token" ? "Token" : "Password"} isRequired fieldId="cred-secret">
          <TextInput id="cred-secret" type="password" value={secret} onChange={(_e, v) => setSecret(v)} />
        </FormGroup>
        <ActionGroup>
          <Button variant="secondary" onClick={handleAdd} isDisabled={!name || !secret}>Add Credential</Button>
        </ActionGroup>
      </Form>
    </TextContent>
  );
}
```

- [ ] **Step 5: Create Step 3 — Sources**

Create `frontend/src/wizard/StepSources.tsx`:

```tsx
import { useState, useEffect } from "react";
import {
  TextContent,
  Text,
  Form,
  FormGroup,
  TextInput,
  TextArea,
  FormSelect,
  FormSelectOption,
  ActionGroup,
  Button,
  Alert,
  DataList,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  DataListCell,
  DataListAction,
  Spinner,
  List,
  ListItem,
  Icon,
} from "@patternfly/react-core";
import { CheckCircleIcon, ExclamationCircleIcon } from "@patternfly/react-icons";
import { apiClient } from "../api/client";
import { Source, Credential, ConnectivityResult, WizardData } from "./types";

interface StepSourcesProps {
  data: WizardData;
  onUpdate: (data: Partial<WizardData>) => void;
}

const SOURCE_LABELS: Record<string, string> = {
  ssh_network: "SSH Network",
  openshift: "OpenShift",
  satellite: "Red Hat Satellite",
  ansible_aap: "Ansible Automation Platform",
  vcenter: "VMware vCenter",
};

const SOURCE_DESCRIPTIONS: Record<string, string> = {
  ssh_network: "Scan Linux hosts over SSH. Enter IP addresses or hostnames, one per line.",
  openshift: "Scan an OpenShift cluster via its API.",
  satellite: "Scan systems managed by Red Hat Satellite.",
  ansible_aap: "Scan Ansible Automation Platform.",
  vcenter: "Scan VMware vCenter for virtual machines.",
};

export function StepSources({ data, onUpdate }: StepSourcesProps) {
  const [sources, setSources] = useState<Source[]>([]);
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [name, setName] = useState("");
  const [sourceType, setSourceType] = useState("ssh_network");
  const [hostsRaw, setHostsRaw] = useState("");
  const [port, setPort] = useState("22");
  const [credentialId, setCredentialId] = useState<string>("");
  const [error, setError] = useState("");
  const [testing, setTesting] = useState<number | null>(null);
  const [testResults, setTestResults] = useState<Record<number, ConnectivityResult[]>>({});

  useEffect(() => {
    apiClient.get<Source[]>("/sources/").then(setSources);
    apiClient.get<Credential[]>("/credentials/").then((creds) => {
      setCredentials(creds);
      if (creds.length > 0) setCredentialId(String(creds[0].id));
    });
  }, []);

  const handleAdd = async () => {
    setError("");
    const hosts = hostsRaw.split("\n").map((h) => h.trim()).filter(Boolean);
    if (hosts.length === 0) {
      setError("Please enter at least one host.");
      return;
    }
    try {
      const source = await apiClient.post<Source>("/sources/", {
        name,
        source_type: sourceType,
        hosts,
        port: parseInt(port, 10),
        credential: parseInt(credentialId, 10),
      });
      setSources([...sources, source]);
      onUpdate({ source_ids: [...data.source_ids, source.id] });
      setName("");
      setHostsRaw("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add source");
    }
  };

  const handleTest = async (sourceId: number) => {
    setTesting(sourceId);
    try {
      const resp = await apiClient.post<{ results: ConnectivityResult[] }>(`/sources/${sourceId}/test/`, {});
      setTestResults({ ...testResults, [sourceId]: resp.results });
    } catch {
      setTestResults({ ...testResults, [sourceId]: [{ host: "unknown", status: "failed", message: "Test failed" }] });
    }
    setTesting(null);
  };

  const handleRemove = async (id: number) => {
    await apiClient.delete(`/sources/${id}/`);
    setSources(sources.filter((s) => s.id !== id));
    onUpdate({ source_ids: data.source_ids.filter((sid) => sid !== id) });
  };

  return (
    <TextContent>
      <Text component="h2">What do you want to scan?</Text>

      {error && <Alert variant="danger" isInline title={error} />}

      {sources.length > 0 && (
        <DataList aria-label="Sources">
          {sources.map((source) => (
            <DataListItem key={source.id}>
              <DataListItemRow>
                <DataListItemCells
                  dataListCells={[
                    <DataListCell key="name">{source.name}</DataListCell>,
                    <DataListCell key="type">{SOURCE_LABELS[source.source_type]}</DataListCell>,
                    <DataListCell key="hosts">{source.hosts.length} host(s)</DataListCell>,
                  ]}
                />
                <DataListAction id={`action-${source.id}`} aria-label="Actions" aria-labelledby={`action-${source.id}`}>
                  <Button variant="secondary" onClick={() => handleTest(source.id)} isLoading={testing === source.id} isDisabled={testing !== null}>
                    Test Connection
                  </Button>
                  <Button variant="link" isDanger onClick={() => handleRemove(source.id)}>Remove</Button>
                </DataListAction>
              </DataListItemRow>
              {testResults[source.id] && (
                <List isPlain>
                  {testResults[source.id].map((r, i) => (
                    <ListItem key={i}>
                      {r.status === "success" ? (
                        <Icon status="success"><CheckCircleIcon /></Icon>
                      ) : (
                        <Icon status="danger"><ExclamationCircleIcon /></Icon>
                      )}
                      {" "}{r.host}: {r.message}
                    </ListItem>
                  ))}
                </List>
              )}
            </DataListItem>
          ))}
        </DataList>
      )}

      <Form>
        <FormGroup label="Source name" isRequired fieldId="src-name">
          <TextInput id="src-name" value={name} onChange={(_e, v) => setName(v)} placeholder="e.g., Production Servers" />
        </FormGroup>
        <FormGroup label="Source type" isRequired fieldId="src-type">
          <FormSelect id="src-type" value={sourceType} onChange={(_e, v) => setSourceType(v)}>
            {Object.entries(SOURCE_LABELS).map(([value, label]) => (
              <FormSelectOption key={value} value={value} label={label} />
            ))}
          </FormSelect>
        </FormGroup>
        <Text component="small">{SOURCE_DESCRIPTIONS[sourceType]}</Text>
        <FormGroup label={sourceType === "ssh_network" ? "Hosts (one per line)" : "URL"} isRequired fieldId="src-hosts">
          <TextArea id="src-hosts" value={hostsRaw} onChange={(_e, v) => setHostsRaw(v)} placeholder={sourceType === "ssh_network" ? "10.0.1.1\n10.0.1.2\nserver.example.com" : "https://api.example.com"} rows={4} />
        </FormGroup>
        <FormGroup label="Port" fieldId="src-port">
          <TextInput id="src-port" type="number" value={port} onChange={(_e, v) => setPort(v)} />
        </FormGroup>
        <FormGroup label="Credential" isRequired fieldId="src-cred">
          <FormSelect id="src-cred" value={credentialId} onChange={(_e, v) => setCredentialId(v)}>
            {credentials.map((c) => (
              <FormSelectOption key={c.id} value={String(c.id)} label={`${c.name} (${c.credential_type})`} />
            ))}
          </FormSelect>
        </FormGroup>
        <ActionGroup>
          <Button variant="secondary" onClick={handleAdd} isDisabled={!name || !hostsRaw || !credentialId}>Add Source</Button>
        </ActionGroup>
      </Form>
    </TextContent>
  );
}
```

- [ ] **Step 6: Create Step 4 — Scan**

Create `frontend/src/wizard/StepScan.tsx`:

```tsx
import { useState, useEffect, useRef } from "react";
import {
  TextContent,
  Text,
  Button,
  Progress,
  Alert,
  FormGroup,
  FormSelect,
  FormSelectOption,
  DescriptionList,
  DescriptionListGroup,
  DescriptionListTerm,
  DescriptionListDescription,
} from "@patternfly/react-core";
import { apiClient } from "../api/client";
import { ScanStatus, WizardData } from "./types";

interface StepScanProps {
  data: WizardData;
  onUpdate: (data: Partial<WizardData>) => void;
}

export function StepScan({ data, onUpdate }: StepScanProps) {
  const [scanStatus, setScanStatus] = useState<ScanStatus | null>(null);
  const [scanType, setScanType] = useState<string>(data.scan_type);
  const [error, setError] = useState("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const startScan = async () => {
    setError("");
    try {
      const scan = await apiClient.post<{ id: number; status: string }>("/scans/", {
        scan_type: scanType,
        source_ids: data.source_ids,
      });
      onUpdate({ scan_id: scan.id, scan_type: scanType as "quick" | "deep" });
      pollProgress(scan.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start scan");
    }
  };

  const pollProgress = (scanId: number) => {
    const poll = async () => {
      try {
        const status = await apiClient.get<ScanStatus>(`/scans/${scanId}/status/`);
        setScanStatus(status);
        if (status.status === "completed" || status.status === "failed" || status.status === "cancelled") {
          if (pollRef.current) clearInterval(pollRef.current);
        }
      } catch {
        // continue polling
      }
    };
    poll();
    pollRef.current = setInterval(poll, 2500);
  };

  const isRunning = scanStatus?.status === "running" || scanStatus?.status === "pending";
  const isComplete = scanStatus?.status === "completed";
  const isFailed = scanStatus?.status === "failed";
  const progress = scanStatus?.progress;

  return (
    <TextContent>
      <Text component="h2">Run Your Health Check</Text>

      {!scanStatus && (
        <>
          <DescriptionList>
            <DescriptionListGroup>
              <DescriptionListTerm>Sources to scan</DescriptionListTerm>
              <DescriptionListDescription>{data.source_ids.length} source(s) configured</DescriptionListDescription>
            </DescriptionListGroup>
            <DescriptionListGroup>
              <DescriptionListTerm>Credentials</DescriptionListTerm>
              <DescriptionListDescription>{data.credential_ids.length} credential(s) configured</DescriptionListDescription>
            </DescriptionListGroup>
          </DescriptionList>

          <FormGroup label="Scan depth" fieldId="scan-type">
            <FormSelect id="scan-type" value={scanType} onChange={(_e, v) => setScanType(v)}>
              <FormSelectOption value="quick" label="Quick Inventory — basic system info" />
              <FormSelectOption value="deep" label="Deep Inspection — products, subscriptions, packages" />
            </FormSelect>
          </FormGroup>

          <Button variant="primary" size="lg" onClick={startScan} isDisabled={data.source_ids.length === 0}>
            Start Health Check
          </Button>
        </>
      )}

      {error && <Alert variant="danger" isInline title={error} />}

      {isRunning && progress && (
        <>
          <Progress
            value={progress.total_hosts > 0 ? (progress.completed_hosts / progress.total_hosts) * 100 : 0}
            title="Scanning..."
            label={`${progress.completed_hosts} of ${progress.total_hosts} hosts`}
          />
          <Text component="p">
            Scanning {progress.current_source}... Found {progress.found_systems} system(s) so far.
          </Text>
        </>
      )}

      {isComplete && (
        <Alert variant="success" isInline title="Health check complete! Proceed to view your results." />
      )}

      {isFailed && (
        <>
          <Alert variant="danger" isInline title="Scan failed. You can retry or check your source configuration." />
          <Button variant="secondary" onClick={() => { setScanStatus(null); setError(""); }}>Retry</Button>
        </>
      )}
    </TextContent>
  );
}
```

- [ ] **Step 7: Create Step 5 — Results**

Create `frontend/src/wizard/StepResults.tsx`:

```tsx
import { useEffect, useState } from "react";
import {
  TextContent,
  Text,
  Button,
  Card,
  CardBody,
  Gallery,
  Spinner,
  Alert,
} from "@patternfly/react-core";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../api/client";
import { WizardData } from "./types";

interface Report {
  id: number;
  title: string;
  summary: {
    total_hosts: number;
    successful_hosts: number;
    failed_hosts: number;
    os_distribution: Record<string, number>;
    products_found: Record<string, number>;
  };
}

interface StepResultsProps {
  data: WizardData;
  onUpdate: (data: Partial<WizardData>) => void;
  onReset: () => void;
}

export function StepResults({ data, onUpdate, onReset }: StepResultsProps) {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (data.scan_id) {
      apiClient
        .get<{ report: { id: number } }>(`/scans/${data.scan_id}/`)
        .then((scan) => {
          if (scan.report) {
            return apiClient.get<Report>(`/reports/${scan.report.id}/`);
          }
          return apiClient.get<Report[]>("/reports/").then((reports) => reports[0]);
        })
        .then((r) => {
          if (r) {
            setReport(r);
            onUpdate({ report_id: r.id });
          }
        })
        .catch(() => {})
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [data.scan_id]);

  if (loading) return <Spinner size="xl" />;

  if (!report) return <Alert variant="warning" isInline title="No report found. Please run a scan first." />;

  const { summary } = report;

  return (
    <TextContent>
      <Text component="h2">Health Check Results</Text>

      <Gallery hasGutter minWidths={{ default: "200px" }}>
        <Card isCompact>
          <CardBody>
            <Text component="h3">{summary.total_hosts}</Text>
            <Text component="small">Total Hosts Scanned</Text>
          </CardBody>
        </Card>
        <Card isCompact>
          <CardBody>
            <Text component="h3">{summary.successful_hosts}</Text>
            <Text component="small">Successful</Text>
          </CardBody>
        </Card>
        <Card isCompact>
          <CardBody>
            <Text component="h3">{summary.failed_hosts}</Text>
            <Text component="small">Failed</Text>
          </CardBody>
        </Card>
      </Gallery>

      <Text component="h3">Operating Systems Found</Text>
      {Object.entries(summary.os_distribution).map(([os, count]) => (
        <Text key={os} component="p">{os}: {count} host(s)</Text>
      ))}

      <Text component="h3">Red Hat Products Detected</Text>
      {Object.entries(summary.products_found).map(([product, count]) => (
        <Text key={product} component="p">{product}: {count} instance(s)</Text>
      ))}

      <Button variant="primary" onClick={() => navigate(`/dashboard/${report.id}`)}>
        View Full Dashboard
      </Button>{" "}
      <Button variant="secondary" component="a" href={`/api/v1/reports/${report.id}/pdf/`}>
        Download PDF Report
      </Button>{" "}
      <Button variant="secondary" component="a" href={`/api/v1/reports/${report.id}/csv/`}>
        Export CSV
      </Button>{" "}
      <Button variant="link" onClick={onReset}>
        Run Another Health Check
      </Button>
    </TextContent>
  );
}
```

- [ ] **Step 8: Create HealthCheckWizard component**

Create `frontend/src/wizard/HealthCheckWizard.tsx`:

```tsx
import { Wizard, WizardStep } from "@patternfly/react-core";
import { useWizardState } from "./useWizardState";
import { StepWelcome } from "./StepWelcome";
import { StepCredentials } from "./StepCredentials";
import { StepSources } from "./StepSources";
import { StepScan } from "./StepScan";
import { StepResults } from "./StepResults";
import { Spinner } from "@patternfly/react-core";

export function HealthCheckWizard() {
  const { state, loading, goToStep, updateData, reset } = useWizardState();

  if (loading) return <Spinner size="xl" />;

  return (
    <Wizard
      height={600}
      title="Red Hat Health Check"
      startIndex={state.current_step}
      onStepChange={(_event, currentStep) => goToStep(currentStep.index ?? 1)}
    >
      <WizardStep name="Welcome" id="welcome">
        <StepWelcome />
      </WizardStep>
      <WizardStep name="Credentials" id="credentials">
        <StepCredentials data={state.data} onUpdate={updateData} />
      </WizardStep>
      <WizardStep name="Sources" id="sources" isDisabled={state.data.credential_ids.length === 0}>
        <StepSources data={state.data} onUpdate={updateData} />
      </WizardStep>
      <WizardStep name="Scan" id="scan" isDisabled={state.data.source_ids.length === 0}>
        <StepScan data={state.data} onUpdate={updateData} />
      </WizardStep>
      <WizardStep name="Results" id="results" isDisabled={!state.data.scan_id}>
        <StepResults data={state.data} onUpdate={updateData} onReset={reset} />
      </WizardStep>
    </Wizard>
  );
}
```

- [ ] **Step 9: Wire wizard into App.tsx**

In `frontend/src/App.tsx`, replace the wizard placeholder route:

Add import at the top:
```tsx
import { HealthCheckWizard } from "./wizard/HealthCheckWizard";
```

Replace the wizard Route:
```tsx
<Route path="/wizard" element={<HealthCheckWizard />} />
```

- [ ] **Step 10: Verify the wizard renders**

```bash
cd frontend && npm run dev &
sleep 3
curl -s http://localhost:5173/wizard | head -5
kill %1
```

Expected: HTML page loads without errors.

- [ ] **Step 11: Commit**

```bash
git add frontend/src/wizard/ frontend/src/App.tsx
git commit -m "feat: add 5-step health check wizard with PatternFly UI"
```

---

### Task 10: Dashboard — Interactive Results Display

**Files:**
- Create: `frontend/src/dashboard/Dashboard.tsx`
- Create: `frontend/src/dashboard/SummaryCards.tsx`
- Create: `frontend/src/dashboard/OsDistributionChart.tsx`
- Create: `frontend/src/dashboard/ResultsTable.tsx`
- Modify: `frontend/src/App.tsx` (replace dashboard placeholder)

**Interfaces:**
- Consumes: Reports API from Task 6, `apiClient` from Task 8
- Produces:
  - `<Dashboard />` page — full report view with summary cards, OS distribution, results table, and download buttons

- [ ] **Step 1: Create SummaryCards component**

Create `frontend/src/dashboard/SummaryCards.tsx`:

```tsx
import { Card, CardBody, Gallery, TextContent, Text } from "@patternfly/react-core";

interface SummaryCardsProps {
  totalHosts: number;
  successfulHosts: number;
  failedHosts: number;
  productsFound: Record<string, number>;
}

export function SummaryCards({ totalHosts, successfulHosts, failedHosts, productsFound }: SummaryCardsProps) {
  const totalProducts = Object.values(productsFound).reduce((a, b) => a + b, 0);

  return (
    <Gallery hasGutter minWidths={{ default: "180px" }}>
      <Card isCompact>
        <CardBody>
          <TextContent>
            <Text component="h2" style={{ fontSize: "2rem", margin: 0 }}>{totalHosts}</Text>
            <Text component="small">Total Hosts</Text>
          </TextContent>
        </CardBody>
      </Card>
      <Card isCompact>
        <CardBody>
          <TextContent>
            <Text component="h2" style={{ fontSize: "2rem", margin: 0, color: "var(--pf-t--global--color--status--success--default)" }}>{successfulHosts}</Text>
            <Text component="small">Successful</Text>
          </TextContent>
        </CardBody>
      </Card>
      <Card isCompact>
        <CardBody>
          <TextContent>
            <Text component="h2" style={{ fontSize: "2rem", margin: 0, color: "var(--pf-t--global--color--status--danger--default)" }}>{failedHosts}</Text>
            <Text component="small">Failed</Text>
          </TextContent>
        </CardBody>
      </Card>
      <Card isCompact>
        <CardBody>
          <TextContent>
            <Text component="h2" style={{ fontSize: "2rem", margin: 0 }}>{totalProducts}</Text>
            <Text component="small">Products Detected</Text>
          </TextContent>
        </CardBody>
      </Card>
    </Gallery>
  );
}
```

- [ ] **Step 2: Create OsDistributionChart component**

Create `frontend/src/dashboard/OsDistributionChart.tsx`:

```tsx
import { Card, CardBody, CardTitle, DescriptionList, DescriptionListGroup, DescriptionListTerm, DescriptionListDescription, Progress } from "@patternfly/react-core";

interface OsDistributionChartProps {
  distribution: Record<string, number>;
  totalHosts: number;
}

export function OsDistributionChart({ distribution, totalHosts }: OsDistributionChartProps) {
  const sorted = Object.entries(distribution).sort(([, a], [, b]) => b - a);

  return (
    <Card>
      <CardTitle>Operating System Distribution</CardTitle>
      <CardBody>
        <DescriptionList>
          {sorted.map(([os, count]) => (
            <DescriptionListGroup key={os}>
              <DescriptionListTerm>{os}</DescriptionListTerm>
              <DescriptionListDescription>
                <Progress
                  value={totalHosts > 0 ? (count / totalHosts) * 100 : 0}
                  label={`${count} host(s)`}
                  measureLocation="outside"
                />
              </DescriptionListDescription>
            </DescriptionListGroup>
          ))}
        </DescriptionList>
      </CardBody>
    </Card>
  );
}
```

- [ ] **Step 3: Create ResultsTable component**

Create `frontend/src/dashboard/ResultsTable.tsx`:

```tsx
import { Card, CardBody, CardTitle, Icon } from "@patternfly/react-core";
import { Table, Thead, Tr, Th, Tbody, Td } from "@patternfly/react-table";
import { CheckCircleIcon, ExclamationCircleIcon, MinusCircleIcon } from "@patternfly/react-icons";

interface ScanResult {
  id: number;
  host: string;
  status: "success" | "failed" | "skipped";
  data: {
    hostname?: string;
    os?: string;
    kernel?: string;
    arch?: string;
    cpu_count?: number;
    memory_mb?: number;
    products?: string[];
  };
  error_message: string;
}

interface ResultsTableProps {
  results: ScanResult[];
}

const statusIcons: Record<string, JSX.Element> = {
  success: <Icon status="success"><CheckCircleIcon /></Icon>,
  failed: <Icon status="danger"><ExclamationCircleIcon /></Icon>,
  skipped: <Icon status="warning"><MinusCircleIcon /></Icon>,
};

export function ResultsTable({ results }: ResultsTableProps) {
  return (
    <Card>
      <CardTitle>Scan Results</CardTitle>
      <CardBody>
        <Table aria-label="Scan results" variant="compact">
          <Thead>
            <Tr>
              <Th>Status</Th>
              <Th>Host</Th>
              <Th>Hostname</Th>
              <Th>OS</Th>
              <Th>Kernel</Th>
              <Th>CPUs</Th>
              <Th>Memory</Th>
              <Th>Products</Th>
              <Th>Error</Th>
            </Tr>
          </Thead>
          <Tbody>
            {results.map((r) => (
              <Tr key={r.id}>
                <Td>{statusIcons[r.status]}</Td>
                <Td>{r.host}</Td>
                <Td>{r.data.hostname || "—"}</Td>
                <Td>{r.data.os || "—"}</Td>
                <Td>{r.data.kernel || "—"}</Td>
                <Td>{r.data.cpu_count ?? "—"}</Td>
                <Td>{r.data.memory_mb ? `${Math.round(r.data.memory_mb / 1024)} GB` : "—"}</Td>
                <Td>{r.data.products?.join(", ") || "—"}</Td>
                <Td>{r.error_message || "—"}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </CardBody>
    </Card>
  );
}
```

- [ ] **Step 4: Create Dashboard page**

Create `frontend/src/dashboard/Dashboard.tsx`:

```tsx
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  PageSection,
  TextContent,
  Text,
  Button,
  Toolbar,
  ToolbarContent,
  ToolbarItem,
  Spinner,
  Alert,
} from "@patternfly/react-core";
import { apiClient } from "../api/client";
import { SummaryCards } from "./SummaryCards";
import { OsDistributionChart } from "./OsDistributionChart";
import { ResultsTable } from "./ResultsTable";

interface ReportDetail {
  id: number;
  title: string;
  summary: {
    total_hosts: number;
    successful_hosts: number;
    failed_hosts: number;
    os_distribution: Record<string, number>;
    products_found: Record<string, number>;
  };
  results: Array<{
    id: number;
    host: string;
    status: "success" | "failed" | "skipped";
    data: Record<string, unknown>;
    error_message: string;
  }>;
  created_at: string;
}

export function Dashboard() {
  const { reportId } = useParams<{ reportId: string }>();
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (reportId) {
      apiClient
        .get<ReportDetail>(`/reports/${reportId}/`)
        .then(setReport)
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }
  }, [reportId]);

  if (loading) return <PageSection><Spinner size="xl" /></PageSection>;
  if (error) return <PageSection><Alert variant="danger" title={error} /></PageSection>;
  if (!report) return <PageSection><Alert variant="warning" title="Report not found" /></PageSection>;

  return (
    <PageSection>
      <TextContent>
        <Text component="h1">{report.title}</Text>
        <Text component="small">Generated {new Date(report.created_at).toLocaleString()}</Text>
      </TextContent>

      <Toolbar>
        <ToolbarContent>
          <ToolbarItem>
            <Button variant="primary" component="a" href={`/api/v1/reports/${report.id}/pdf/`}>Download PDF</Button>
          </ToolbarItem>
          <ToolbarItem>
            <Button variant="secondary" component="a" href={`/api/v1/reports/${report.id}/csv/`}>Export CSV</Button>
          </ToolbarItem>
        </ToolbarContent>
      </Toolbar>

      <SummaryCards
        totalHosts={report.summary.total_hosts}
        successfulHosts={report.summary.successful_hosts}
        failedHosts={report.summary.failed_hosts}
        productsFound={report.summary.products_found}
      />

      <OsDistributionChart
        distribution={report.summary.os_distribution}
        totalHosts={report.summary.successful_hosts}
      />

      <ResultsTable results={report.results as ReportDetail["results"]} />
    </PageSection>
  );
}
```

- [ ] **Step 5: Wire dashboard into App.tsx**

In `frontend/src/App.tsx`, add import:
```tsx
import { Dashboard } from "./dashboard/Dashboard";
```

Replace the dashboard placeholder Route:
```tsx
<Route path="/dashboard/:reportId" element={<Dashboard />} />
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/dashboard/ frontend/src/App.tsx
git commit -m "feat: add interactive dashboard with summary cards, OS distribution, and results table"
```

---

### Task 11: Post-Wizard Pages — Management Views

**Files:**
- Create: `frontend/src/pages/CredentialsPage.tsx`
- Create: `frontend/src/pages/SourcesPage.tsx`
- Create: `frontend/src/pages/ScansPage.tsx`
- Create: `frontend/src/pages/ReportsPage.tsx`
- Modify: `frontend/src/App.tsx` (replace all page placeholders)

**Interfaces:**
- Consumes: All backend APIs, `apiClient` from Task 8
- Produces: Four management pages accessible via sidebar navigation for returning users

- [ ] **Step 1: Create CredentialsPage**

Create `frontend/src/pages/CredentialsPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { PageSection, TextContent, Text, Button, Alert } from "@patternfly/react-core";
import { Table, Thead, Tr, Th, Tbody, Td } from "@patternfly/react-table";
import { apiClient } from "../api/client";
import { Credential } from "../wizard/types";

export function CredentialsPage() {
  const [credentials, setCredentials] = useState<Credential[]>([]);

  useEffect(() => {
    apiClient.get<Credential[]>("/credentials/").then(setCredentials);
  }, []);

  const handleDelete = async (id: number) => {
    await apiClient.delete(`/credentials/${id}/`);
    setCredentials(credentials.filter((c) => c.id !== id));
  };

  return (
    <PageSection>
      <TextContent>
        <Text component="h1">Credentials</Text>
        <Text component="p">Manage your saved connection credentials.</Text>
      </TextContent>
      <Table aria-label="Credentials" variant="compact">
        <Thead><Tr><Th>Name</Th><Th>Type</Th><Th>Username</Th><Th>Created</Th><Th>Actions</Th></Tr></Thead>
        <Tbody>
          {credentials.map((c) => (
            <Tr key={c.id}>
              <Td>{c.name}</Td>
              <Td>{c.credential_type}</Td>
              <Td>{c.username || "—"}</Td>
              <Td>{new Date(c.created_at).toLocaleDateString()}</Td>
              <Td><Button variant="link" isDanger onClick={() => handleDelete(c.id)}>Delete</Button></Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
      {credentials.length === 0 && <Alert variant="info" isInline title="No credentials yet. Use the wizard to add some." />}
    </PageSection>
  );
}
```

- [ ] **Step 2: Create SourcesPage**

Create `frontend/src/pages/SourcesPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { PageSection, TextContent, Text, Button, Alert } from "@patternfly/react-core";
import { Table, Thead, Tr, Th, Tbody, Td } from "@patternfly/react-table";
import { apiClient } from "../api/client";
import { Source } from "../wizard/types";

export function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);

  useEffect(() => {
    apiClient.get<Source[]>("/sources/").then(setSources);
  }, []);

  const handleDelete = async (id: number) => {
    await apiClient.delete(`/sources/${id}/`);
    setSources(sources.filter((s) => s.id !== id));
  };

  return (
    <PageSection>
      <TextContent>
        <Text component="h1">Sources</Text>
        <Text component="p">Manage your scan targets.</Text>
      </TextContent>
      <Table aria-label="Sources" variant="compact">
        <Thead><Tr><Th>Name</Th><Th>Type</Th><Th>Hosts</Th><Th>Created</Th><Th>Actions</Th></Tr></Thead>
        <Tbody>
          {sources.map((s) => (
            <Tr key={s.id}>
              <Td>{s.name}</Td>
              <Td>{s.source_type}</Td>
              <Td>{s.hosts.length} host(s)</Td>
              <Td>{new Date(s.created_at).toLocaleDateString()}</Td>
              <Td><Button variant="link" isDanger onClick={() => handleDelete(s.id)}>Delete</Button></Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
      {sources.length === 0 && <Alert variant="info" isInline title="No sources yet. Use the wizard to add some." />}
    </PageSection>
  );
}
```

- [ ] **Step 3: Create ScansPage**

Create `frontend/src/pages/ScansPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { PageSection, TextContent, Text, Label, Alert } from "@patternfly/react-core";
import { Table, Thead, Tr, Th, Tbody, Td } from "@patternfly/react-table";
import { apiClient } from "../api/client";

interface ScanListItem {
  id: number;
  status: string;
  scan_type: string;
  progress: { total_hosts: number; completed_hosts: number; found_systems: number };
  created_at: string;
  completed_at: string | null;
}

const statusColors: Record<string, "green" | "blue" | "red" | "orange" | "grey"> = {
  completed: "green",
  running: "blue",
  failed: "red",
  pending: "orange",
  cancelled: "grey",
};

export function ScansPage() {
  const [scans, setScans] = useState<ScanListItem[]>([]);

  useEffect(() => {
    apiClient.get<ScanListItem[]>("/scans/").then(setScans);
  }, []);

  return (
    <PageSection>
      <TextContent>
        <Text component="h1">Scan History</Text>
      </TextContent>
      <Table aria-label="Scans" variant="compact">
        <Thead><Tr><Th>ID</Th><Th>Type</Th><Th>Status</Th><Th>Hosts</Th><Th>Systems Found</Th><Th>Started</Th></Tr></Thead>
        <Tbody>
          {scans.map((s) => (
            <Tr key={s.id}>
              <Td>{s.id}</Td>
              <Td>{s.scan_type}</Td>
              <Td><Label color={statusColors[s.status] || "grey"}>{s.status}</Label></Td>
              <Td>{s.progress.completed_hosts}/{s.progress.total_hosts}</Td>
              <Td>{s.progress.found_systems}</Td>
              <Td>{new Date(s.created_at).toLocaleString()}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
      {scans.length === 0 && <Alert variant="info" isInline title="No scans yet. Run a health check from the wizard." />}
    </PageSection>
  );
}
```

- [ ] **Step 4: Create ReportsPage**

Create `frontend/src/pages/ReportsPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageSection, TextContent, Text, Button, Alert } from "@patternfly/react-core";
import { Table, Thead, Tr, Th, Tbody, Td } from "@patternfly/react-table";
import { apiClient } from "../api/client";

interface ReportListItem {
  id: number;
  title: string;
  summary: { total_hosts: number; successful_hosts: number; failed_hosts: number };
  created_at: string;
}

export function ReportsPage() {
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    apiClient.get<ReportListItem[]>("/reports/").then(setReports);
  }, []);

  return (
    <PageSection>
      <TextContent>
        <Text component="h1">Reports</Text>
      </TextContent>
      <Table aria-label="Reports" variant="compact">
        <Thead><Tr><Th>Title</Th><Th>Total Hosts</Th><Th>Successful</Th><Th>Failed</Th><Th>Date</Th><Th>Actions</Th></Tr></Thead>
        <Tbody>
          {reports.map((r) => (
            <Tr key={r.id}>
              <Td>{r.title}</Td>
              <Td>{r.summary.total_hosts}</Td>
              <Td>{r.summary.successful_hosts}</Td>
              <Td>{r.summary.failed_hosts}</Td>
              <Td>{new Date(r.created_at).toLocaleString()}</Td>
              <Td>
                <Button variant="link" onClick={() => navigate(`/dashboard/${r.id}`)}>View</Button>{" "}
                <Button variant="link" component="a" href={`/api/v1/reports/${r.id}/pdf/`}>PDF</Button>{" "}
                <Button variant="link" component="a" href={`/api/v1/reports/${r.id}/csv/`}>CSV</Button>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
      {reports.length === 0 && <Alert variant="info" isInline title="No reports yet. Run a health check first." />}
    </PageSection>
  );
}
```

- [ ] **Step 5: Wire all pages into App.tsx**

In `frontend/src/App.tsx`, add imports:
```tsx
import { CredentialsPage } from "./pages/CredentialsPage";
import { SourcesPage } from "./pages/SourcesPage";
import { ScansPage } from "./pages/ScansPage";
import { ReportsPage } from "./pages/ReportsPage";
```

Replace the four placeholder Routes:
```tsx
<Route path="/credentials" element={<CredentialsPage />} />
<Route path="/sources" element={<SourcesPage />} />
<Route path="/scans" element={<ScansPage />} />
<Route path="/reports" element={<ReportsPage />} />
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/ frontend/src/App.tsx
git commit -m "feat: add management pages for credentials, sources, scans, and reports"
```

---

### Task 12: Dockerfile and Production Configuration

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `backend/healthcheck/startup.py`
- Create: `entrypoint.sh`
- Create: `.dockerignore`

**Interfaces:**
- Consumes: Backend from Tasks 1-7, frontend from Tasks 8-11
- Produces:
  - `Dockerfile` — single multi-stage build that compiles the frontend and runs Django + Huey
  - `docker-compose.yml` — dev convenience with hot reload
  - `entrypoint.sh` — generates Fernet key, runs migrations, starts Gunicorn + Huey
  - Container starts with `podman run -p 8080:8080 redhat-healthcheck`

- [ ] **Step 1: Create .dockerignore**

Create `.dockerignore`:

```
.git
.venv
__pycache__
*.pyc
node_modules
frontend/dist
backend/staticfiles
backend/data
*.egg-info
.pytest_cache
```

- [ ] **Step 2: Create entrypoint script**

Create `entrypoint.sh`:

```bash
#!/bin/bash
set -e

DATA_DIR="${HEALTHCHECK_DATA_DIR:-/data}"
mkdir -p "$DATA_DIR"

echo "Running database migrations..."
python backend/manage.py migrate --noinput

echo "Collecting static files..."
python backend/manage.py collectstatic --noinput 2>/dev/null || true

if [ ! -f "$DATA_DIR/admin_token" ]; then
    TOKEN=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "$TOKEN" > "$DATA_DIR/admin_token"
    echo ""
    echo "========================================"
    echo "  ADMIN ACCESS TOKEN (save this!):"
    echo "  $TOKEN"
    echo "========================================"
    echo ""
fi

echo "Starting Huey consumer in background..."
python backend/manage.py run_huey --workers 2 --quiet &

echo "Starting web server on port ${PORT:-8080}..."
exec gunicorn backend.healthcheck.wsgi:application \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers "${WEB_WORKERS:-2}" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
```

- [ ] **Step 3: Create Dockerfile**

Create `Dockerfile`:

```dockerfile
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production image
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    sshpass openssh-client \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt gunicorn

COPY backend/ ./backend/
COPY --from=frontend-build /app/backend/staticfiles/frontend/ ./backend/staticfiles/frontend/

COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENV DJANGO_DEBUG=false
ENV DJANGO_SECRET_KEY=changeme-in-production
ENV HEALTHCHECK_DATA_DIR=/data
ENV PYTHONUNBUFFERED=1

VOLUME /data
EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
```

- [ ] **Step 4: Create docker-compose.yml for development**

Create `docker-compose.yml`:

```yaml
services:
  backend:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - healthcheck-data:/data
    environment:
      - DJANGO_DEBUG=false
      - DJANGO_SECRET_KEY=dev-secret-key-change-me

volumes:
  healthcheck-data:
```

- [ ] **Step 5: Create startup module for Django URL serving**

Create `backend/healthcheck/startup.py`:

```python
from django.urls import re_path
from django.views.static import serve
from django.conf import settings
import os


def get_frontend_urls():
    frontend_dir = settings.STATIC_ROOT / "frontend"
    if not frontend_dir.exists():
        return []

    def serve_frontend(request, path=""):
        file_path = frontend_dir / path
        if file_path.exists() and file_path.is_file():
            return serve(request, path, document_root=str(frontend_dir))
        return serve(request, "index.html", document_root=str(frontend_dir))

    return [
        re_path(r"^(?!api/)(?P<path>.*)$", serve_frontend),
    ]
```

Add to `backend/healthcheck/urls.py` at the bottom:

```python
from healthcheck.startup import get_frontend_urls
urlpatterns += get_frontend_urls()
```

- [ ] **Step 6: Build and test the container**

```bash
docker build -t redhat-healthcheck .
docker run -d --name hc-test -p 8080:8080 redhat-healthcheck
sleep 5
curl -s http://localhost:8080/api/v1/credentials/ | python -m json.tool
curl -s http://localhost:8080/ | head -5
docker stop hc-test && docker rm hc-test
```

Expected: API returns JSON, frontend HTML is served at root.

- [ ] **Step 7: Commit**

```bash
git add Dockerfile docker-compose.yml entrypoint.sh .dockerignore backend/healthcheck/startup.py backend/healthcheck/urls.py
git commit -m "feat: add Dockerfile and production configuration for single-container deployment"
```

---

### Task 13: Integration Wiring and Final Verification

**Files:**
- Modify: `backend/scans/tasks.py` (ensure report generation on scan completion)
- Create: `backend/healthcheck/tests/__init__.py`
- Create: `backend/healthcheck/tests/test_integration.py`

**Interfaces:**
- Consumes: All apps from Tasks 1-12
- Produces: End-to-end integration test and verified working application

- [ ] **Step 1: Write integration test**

Create `backend/healthcheck/tests/__init__.py`: empty file.

Create `backend/healthcheck/tests/test_integration.py`:

```python
import pytest
from unittest.mock import patch
from credentials.models import Credential
from sources.models import Source
from scans.models import Scan, ScanResult
from reports.models import Report

pytestmark = pytest.mark.django_db


@patch("scanner.ssh.scan")
def test_full_workflow(mock_ssh_scan, api_client):
    """End-to-end: create credential -> create source -> run scan -> check report."""
    mock_ssh_scan.return_value = {
        "hostname": "server1.example.com",
        "os": "Red Hat Enterprise Linux 9.3",
        "os_id": "rhel",
        "os_version": "9.3",
        "kernel": "5.14.0-362.el9.x86_64",
        "arch": "x86_64",
        "cpu_count": 4,
        "memory_mb": 8192,
        "products": ["RHEL"],
        "subscriptions": [],
    }

    # Step 1: Create credential
    cred_resp = api_client.post(
        "/api/v1/credentials/",
        {"name": "test-cred", "credential_type": "password", "username": "root", "secret": "password"},
        format="json",
    )
    assert cred_resp.status_code == 201
    cred_id = cred_resp.data["id"]

    # Step 2: Create source
    source_resp = api_client.post(
        "/api/v1/sources/",
        {"name": "test-source", "source_type": "ssh_network", "hosts": ["10.0.1.1"], "port": 22, "credential": cred_id},
        format="json",
    )
    assert source_resp.status_code == 201
    source_id = source_resp.data["id"]

    # Step 3: Run scan (Huey runs immediately in DEBUG/test mode)
    scan_resp = api_client.post(
        "/api/v1/scans/",
        {"scan_type": "quick", "source_ids": [source_id]},
        format="json",
    )
    assert scan_resp.status_code == 201

    # Step 4: Verify scan completed and report was generated
    scan = Scan.objects.get(id=scan_resp.data["id"])
    assert scan.status == "completed"
    assert ScanResult.objects.filter(scan=scan, status="success").count() == 1

    report = Report.objects.get(scan=scan)
    assert report.summary["total_hosts"] == 1
    assert report.summary["successful_hosts"] == 1
    assert "RHEL" in report.summary["products_found"]

    # Step 5: Verify report API
    report_resp = api_client.get(f"/api/v1/reports/{report.id}/")
    assert report_resp.status_code == 200
    assert report_resp.data["summary"]["total_hosts"] == 1

    # Step 6: Verify CSV export
    csv_resp = api_client.get(f"/api/v1/reports/{report.id}/csv/")
    assert csv_resp.status_code == 200
    assert b"10.0.1.1" in csv_resp.content
    assert b"Red Hat Enterprise Linux 9.3" in csv_resp.content
```

- [ ] **Step 2: Run the integration test**

```bash
pytest backend/healthcheck/tests/test_integration.py -v
```

Expected: Full workflow test passes.

- [ ] **Step 3: Run the complete test suite**

```bash
pytest backend/ -v --tb=short
```

Expected: All tests pass across all apps.

- [ ] **Step 4: Commit**

```bash
git add backend/healthcheck/tests/
git commit -m "feat: add end-to-end integration test for full credential-to-report workflow"
```

- [ ] **Step 5: Push to GitHub**

```bash
git push origin main
```
