from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.static import serve


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("separator.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve frontend assets and SPA
if hasattr(settings, "FRONTEND_DIST") and settings.FRONTEND_DIST.exists():
    urlpatterns += [
        # Serve frontend static assets (JS, CSS, images)
        re_path(
            r"^assets/(?P<path>.*)$",
            serve,
            {"document_root": str(settings.FRONTEND_DIST / "assets")},
        ),
        # Serve other frontend static files (favicon.svg, etc.)
        re_path(
            r"^(?P<path>favicon\.svg|icons\.svg)$",
            serve,
            {"document_root": str(settings.FRONTEND_DIST)},
        ),
        # SPA catch-all for all other routes
        re_path(r"^(?!api/|admin/|media/).*$", TemplateView.as_view(template_name="index.html")),
    ]
