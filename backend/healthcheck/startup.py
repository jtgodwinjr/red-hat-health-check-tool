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
