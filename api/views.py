"""ViewSets API DRF."""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import (
    AdhesionSerializer,
    AffectationSerializer,
    CarteMembreSerializer,
    CotisationSerializer,
    EvenementSerializer,
    MembreSerializer,
    ProvinceSerializer,
    SectionLocaleSerializer,
)
from finances.models import Cotisation
from membership.models import Adhesion, CarteMembre, Membre
from membership.services.carte import generate_membership_card
from organisation.models import AffectationPolitique, Evenement
from territoires.models import Province, SectionLocale


class IsStaffOrReadCreate(permissions.BasePermission):
    """Lecture/création publique pour adhésions ; écriture admin sinon."""

    def has_permission(self, request, view):
        if view.basename == "adhesion" and request.method in ("POST", "OPTIONS"):
            return True
        if request.method in permissions.SAFE_METHODS and view.basename in (
            "province",
            "sectionlocale",
        ):
            return True
        return request.user and request.user.is_authenticated


class AdhesionViewSet(viewsets.ModelViewSet):
    queryset = Adhesion.objects.select_related(
        "section_locale__commune__ville__province", "province_origine"
    ).all()
    serializer_class = AdhesionSerializer
    permission_classes = [IsStaffOrReadCreate]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["statut", "sexe", "section_locale"]
    search_fields = ["nom", "post_nom", "prenom", "numero_membre", "telephone"]
    ordering_fields = ["date_creation", "nom"]

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def valider(self, request, pk=None):
        adhesion = self.get_object()
        membre = adhesion.valider(user=request.user)
        return Response(
            {"status": "validée", "numero_membre": membre.numero_membre},
            status=status.HTTP_200_OK,
        )


class MembreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Membre.objects.select_related("adhesion").filter(actif=True)
    serializer_class = MembreSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["actif"]
    search_fields = [
        "adhesion__nom",
        "adhesion__post_nom",
        "adhesion__prenom",
        "adhesion__numero_membre",
    ]


class CarteMembreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CarteMembre.objects.select_related("membre__adhesion").all()
    serializer_class = CarteMembreSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["numero_carte", "membre__adhesion__numero_membre"]

    @action(detail=True, methods=["post"])
    def regenerer(self, request, pk=None):
        carte = self.get_object()
        generate_membership_card(carte.membre)
        return Response({"status": "régénérée"})


class CotisationViewSet(viewsets.ModelViewSet):
    queryset = Cotisation.objects.select_related("membre__adhesion").all()
    serializer_class = CotisationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["type", "devise"]

    def perform_create(self, serializer):
        serializer.save(enregistre_par=self.request.user)


class EvenementViewSet(viewsets.ModelViewSet):
    queryset = Evenement.objects.all()
    serializer_class = EvenementSerializer
    permission_classes = [permissions.IsAuthenticated]


class AffectationViewSet(viewsets.ModelViewSet):
    queryset = AffectationPolitique.objects.all()
    serializer_class = AffectationSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProvinceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Province.objects.filter(actif=True)
    serializer_class = ProvinceSerializer
    permission_classes = [permissions.AllowAny]


class SectionLocaleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SectionLocale.objects.filter(actif=True)
    serializer_class = SectionLocaleSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ["commune"]


class StatsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models import Count

        membres_par_province = list(
            Membre.objects.filter(actif=True)
            .values("adhesion__section_locale__commune__ville__province__nom")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        return Response(
            {
                "membres_actifs": Membre.objects.filter(actif=True).count(),
                "adhesions_attente": Adhesion.objects.filter(
                    statut=Adhesion.Statut.EN_ATTENTE
                ).count(),
                "membres_par_province": membres_par_province,
            }
        )
