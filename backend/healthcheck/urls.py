from django.urls import include, path

urlpatterns = [
    path("api/v1/credentials/", include("credentials.urls")),
    path("api/v1/sources/", include("sources.urls")),
    path("api/v1/scans/", include("scans.urls")),
    path("api/v1/reports/", include("reports.urls")),
    path("api/v1/wizard/", include("wizard.urls")),
]

from healthcheck.startup import get_frontend_urls
urlpatterns += get_frontend_urls()
