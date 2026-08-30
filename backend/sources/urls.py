from rest_framework.routers import DefaultRouter
from sources.views import SourceViewSet

router = DefaultRouter()
router.register("", SourceViewSet, basename="source")

urlpatterns = router.urls
