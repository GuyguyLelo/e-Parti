"""URLs racine — e-Parti."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "E.C.C.O. — Administration e-Parti"
admin.site.site_title = "E.C.C.O. e-Parti"
admin.site.index_title = "Ensemble, Changeons le Congo"

urlpatterns = [
    # Rediriger la racine vers login
    
    # Toutes les URLs avec le préfixe e-parti/
    path('e-parti/admin/', admin.site.urls),
    path('e-parti/', include('core.urls')),
    path('e-parti/accounts/', include('accounts.urls')),
    path('e-parti/adhesions/', include('membership.urls')),
    path('e-parti/finances/', include('finances.urls')),
    path('e-parti/organisation/', include('organisation.urls')),
    path('e-parti/api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)