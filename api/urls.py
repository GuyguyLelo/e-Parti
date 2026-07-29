"""Routes API REST + JWT."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.views import (
    AdhesionViewSet,
    AffectationViewSet,
    CarteMembreViewSet,
    CotisationViewSet,
    EvenementViewSet,
    MembreViewSet,
    ProvinceViewSet,
    SectionLocaleViewSet,
    StatsAPIView,
)

router = DefaultRouter()
router.register("adhesions", AdhesionViewSet, basename="adhesion")
router.register("membres", MembreViewSet, basename="membre")
router.register("cartes", CarteMembreViewSet, basename="carte")
router.register("cotisations", CotisationViewSet, basename="cotisation")
router.register("evenements", EvenementViewSet, basename="evenement")
router.register("affectations", AffectationViewSet, basename="affectation")
router.register("provinces", ProvinceViewSet, basename="province")
router.register("sections", SectionLocaleViewSet, basename="sectionlocale")

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("stats/", StatsAPIView.as_view(), name="api_stats"),
    path("", include(router.urls)),
]
