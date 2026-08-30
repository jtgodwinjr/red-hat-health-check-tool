from rest_framework.routers import DefaultRouter
from credentials.views import CredentialViewSet

router = DefaultRouter()
router.register("", CredentialViewSet, basename="credential")

urlpatterns = router.urls
