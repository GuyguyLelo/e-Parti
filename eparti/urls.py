"""URLs racine — e-Parti."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "E.C.C.O. — Administration e-Parti"
admin.site.site_title = "E.C.C.O. e-Parti"
admin.site.index_title = "Ensemble, Changeons le Congo"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("adhesions/", include("membership.urls")),
    path("finances/", include("finances.urls")),
    path("organisation/", include("organisation.urls")),
    path("api/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
