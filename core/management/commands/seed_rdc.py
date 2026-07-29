"""
Charge les provinces RDC et un jeu de données de démonstration.
Usage: python manage.py seed_rdc
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from territoires.models import Commune, Province, SectionLocale, Ville

# Principales provinces de la RDC (liste officielle simplifiée)
PROVINCES_RDC = [
    ("Kinshasa", "KIN"),
    ("Kongo-Central", "KOC"),
    ("Kwango", "KWA"),
    ("Kwilu", "KWI"),
    ("Mai-Ndombe", "MND"),
    ("Kasaï", "KAS"),
    ("Kasaï-Central", "KAC"),
    ("Kasaï-Oriental", "KAO"),
    ("Lomami", "LOM"),
    ("Sankuru", "SAN"),
    ("Maniema", "MAN"),
    ("Sud-Kivu", "SKV"),
    ("Nord-Kivu", "NKV"),
    ("Ituri", "ITU"),
    ("Haut-Uele", "HUE"),
    ("Bas-Uele", "BUE"),
    ("Tshopo", "TSH"),
    ("Tshuapa", "TSP"),
    ("Mongala", "MON"),
    ("Nord-Ubangi", "NUB"),
    ("Sud-Ubangi", "SUB"),
    ("Équateur", "EQU"),
    ("Haut-Lomami", "HLM"),
    ("Lualaba", "LUA"),
    ("Haut-Katanga", "HKT"),
    ("Tanganyika", "TAN"),
]


class Command(BaseCommand):
    help = "Initialise provinces RDC, sections démo et compte admin"

    def handle(self, *args, **options):
        self.stdout.write("Création des provinces RDC…")
        for nom, code in PROVINCES_RDC:
            Province.objects.update_or_create(code=code, defaults={"nom": nom, "actif": True})

        kin = Province.objects.get(code="KIN")
        ville, _ = Ville.objects.get_or_create(province=kin, nom="Kinshasa")
        for commune_nom in ("Gombe", "Lingwala", "Kalamu", "Ngaliema", "Lemba"):
            commune, _ = Commune.objects.get_or_create(ville=ville, nom=commune_nom)
            SectionLocale.objects.update_or_create(
                code=f"KIN-{commune_nom[:3].upper()}-01",
                defaults={
                    "nom": f"Section {commune_nom}",
                    "commune": commune,
                    "adresse": f"Avenue principale, {commune_nom}",
                    "actif": True,
                    "latitude": -4.325,
                    "longitude": 15.322,
                },
            )

        # Autres exemples
        for code, ville_nom, commune_nom in (
            ("NKV", "Goma", "Goma"),
            ("HKT", "Lubumbashi", "Lubumbashi"),
            ("SKV", "Bukavu", "Ibanda"),
        ):
            prov = Province.objects.get(code=code)
            v, _ = Ville.objects.get_or_create(province=prov, nom=ville_nom)
            c, _ = Commune.objects.get_or_create(ville=v, nom=commune_nom)
            SectionLocale.objects.update_or_create(
                code=f"{code}-SEC-01",
                defaults={
                    "nom": f"Section {commune_nom}",
                    "commune": c,
                    "actif": True,
                },
            )

        User = get_user_model()
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@eparti.cd",
                "nom": "Admin",
                "post_nom": "National",
                "prenom": "eParti",
                "role": User.Role.ADMIN_NATIONAL,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write(self.style.SUCCESS("Compte admin créé (admin / admin123)"))
        else:
            self.stdout.write("Compte admin déjà existant")

        # Adhésion démo en attente
        from membership.models import Adhesion

        section = SectionLocale.objects.filter(code__startswith="KIN").first()
        if section and not Adhesion.objects.filter(telephone="+243810000001").exists():
            Adhesion.objects.create(
                nom="Mukendi",
                post_nom="Kabongo",
                prenom="Jean",
                date_naissance=date(1990, 5, 12),
                lieu_naissance="Kinshasa",
                sexe=Adhesion.Sexe.M,
                etat_civil=Adhesion.EtatCivil.CELIBATAIRE,
                adresse="Av. de la Libération, Gombe",
                telephone="+243810000001",
                email="jean.mukendi@example.cd",
                nationalite="Congolaise",
                province_origine=kin,
                type_piece_identite=Adhesion.TypePiece.CARTE_ELECTEUR,
                numero_piece_identite="CE-123456789",
                niveau_etudes=Adhesion.NiveauEtudes.UNIVERSITAIRE,
                profession="Enseignant",
                motivations="Servir la nation et renforcer la démocratie locale.",
                certifie_exactitude=True,
                date_signature=timezone.now().date(),
                section_locale=section,
            )
            self.stdout.write("Adhésion démo créée (en attente)")

        self.stdout.write(self.style.SUCCESS("Seed RDC terminé."))
