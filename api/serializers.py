"""Serializers API REST e-Parti."""
from rest_framework import serializers

from finances.models import Cotisation
from membership.models import Adhesion, CarteMembre, Membre
from organisation.models import AffectationPolitique, Evenement
from territoires.models import Commune, Province, SectionLocale, Ville


class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ("id", "nom", "code", "slug", "actif")


class VilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ville
        fields = ("id", "nom", "province", "slug", "actif")


class CommuneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commune
        fields = ("id", "nom", "ville", "slug", "actif")


class SectionLocaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionLocale
        fields = (
            "id",
            "nom",
            "code",
            "commune",
            "adresse",
            "telephone",
            "actif",
            "latitude",
            "longitude",
        )


class AdhesionSerializer(serializers.ModelSerializer):
    nom_complet = serializers.CharField(read_only=True)

    class Meta:
        model = Adhesion
        fields = "__all__"
        read_only_fields = ("numero_membre", "statut", "valide_par", "date_creation")


class MembreSerializer(serializers.ModelSerializer):
    nom_complet = serializers.CharField(read_only=True)
    numero_membre = serializers.CharField(read_only=True)
    adhesion = AdhesionSerializer(read_only=True)

    class Meta:
        model = Membre
        fields = (
            "id",
            "adhesion",
            "actif",
            "date_activation",
            "notes",
            "nom_complet",
            "numero_membre",
        )


class CarteMembreSerializer(serializers.ModelSerializer):
    membre_numero = serializers.CharField(source="membre.numero_membre", read_only=True)
    est_expiree = serializers.BooleanField(read_only=True)

    class Meta:
        model = CarteMembre
        fields = (
            "id",
            "membre",
            "membre_numero",
            "numero_carte",
            "date_emission",
            "date_expiration",
            "qr_code",
            "fichier_pdf",
            "actif",
            "est_expiree",
        )


class CotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = "__all__"
        read_only_fields = ("enregistre_par", "date_creation")


class EvenementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evenement
        fields = "__all__"


class AffectationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffectationPolitique
        fields = "__all__"
