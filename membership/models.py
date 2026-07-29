"""
Modèles d'adhésion, membres et cartes e-Parti.
"""
from datetime import date

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class Adhesion(models.Model):
    """Demande d'adhésion au parti."""

    class Sexe(models.TextChoices):
        M = "M", "Masculin"
        F = "F", "Féminin"

    class EtatCivil(models.TextChoices):
        CELIBATAIRE = "CELIBATAIRE", "Célibataire"
        MARIE = "MARIE", "Marié(e)"
        DIVORCE = "DIVORCE", "Divorcé(e)"
        VEUF = "VEUF", "Veuf / Veuve"
        UNION_LIBRE = "UNION_LIBRE", "Union libre"

    class TypePiece(models.TextChoices):
        CARTE_ELECTEUR = "CARTE_ELECTEUR", "Carte d'électeur"
        PASSEPORT = "PASSEPORT", "Passeport"
        PERMIS = "PERMIS", "Permis de conduire"
        AUTRE = "AUTRE", "Autre"

    class NiveauEtudes(models.TextChoices):
        SANS = "SANS", "Sans niveau"
        PRIMAIRE = "PRIMAIRE", "Primaire"
        SECONDAIRE = "SECONDAIRE", "Secondaire"
        UNIVERSITAIRE = "UNIVERSITAIRE", "Universitaire"
        POST_UNIVERSITAIRE = "POST_UNIV", "Post-universitaire"

    class Statut(models.TextChoices):
        EN_ATTENTE = "EN_ATTENTE", "En attente"
        VALIDE = "VALIDE", "Validée"
        REJETE = "REJETE", "Rejetée"

    # Identité
    nom = models.CharField(max_length=100)
    post_nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=150)
    sexe = models.CharField(max_length=1, choices=Sexe.choices)
    etat_civil = models.CharField(max_length=20, choices=EtatCivil.choices)
    adresse = models.CharField(max_length=255)
    telephone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    nationalite = models.CharField(max_length=80, default="Congolaise")
    province_origine = models.ForeignKey(
        "territoires.Province",
        on_delete=models.PROTECT,
        related_name="adhesions_origine",
        verbose_name="Province d'origine",
    )

    # Pièce d'identité
    type_piece_identite = models.CharField(
        max_length=20, choices=TypePiece.choices, default=TypePiece.CARTE_ELECTEUR
    )
    numero_piece_identite = models.CharField(max_length=80)

    # Profil
    niveau_etudes = models.CharField(
        max_length=20, choices=NiveauEtudes.choices, blank=True
    )
    profession = models.CharField(max_length=120, blank=True)
    deja_membre = models.BooleanField("Déjà membre auparavant ?", default=False)
    details_membre = models.TextField(blank=True)
    motivations = models.TextField()
    certifie_exactitude = models.BooleanField(default=False)
    date_signature = models.DateField(default=date.today)

    # Photos
    photo1 = models.ImageField(
        "Photo d'identité", upload_to="adhesions/photos/%Y/%m/", blank=True
    )
    photo2 = models.ImageField(
        "Photo supplémentaire", upload_to="adhesions/photos/%Y/%m/", blank=True
    )

    # Traitement
    statut = models.CharField(
        max_length=15,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE,
        db_index=True,
    )
    numero_membre = models.CharField(
        max_length=30, unique=True, null=True, blank=True, db_index=True
    )
    section_locale = models.ForeignKey(
        "territoires.SectionLocale",
        on_delete=models.PROTECT,
        related_name="adhesions",
    )
    motif_rejet = models.TextField(blank=True)
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="adhesions_validees",
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    # Géolocalisation optionnelle
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    class Meta:
        verbose_name = "Adhésion"
        verbose_name_plural = "Adhésions"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.nom_complet} — {self.get_statut_display()}"

    @property
    def nom_complet(self):
        return f"{self.nom} {self.post_nom} {self.prenom}".strip()

    @staticmethod
    def extraire_ordre(numero: str) -> int:
        """Extrait le numéro d'ordre depuis un matricule (ancien ou nouveau format)."""
        if not numero:
            return 0
        if "-" in numero:
            try:
                return int(numero.rsplit("-", 1)[-1])
            except ValueError:
                pass
        try:
            return int(numero)
        except ValueError:
            digits = "".join(c for c in numero if c.isdigit())
            return int(digits[-6:]) if digits else 0

    @staticmethod
    def generer_numero_membre():
        """Génère un numéro d'ordre séquentiel (000001, 000002, …)."""
        nums = Adhesion.objects.exclude(numero_membre__isnull=True).exclude(
            numero_membre=""
        ).values_list("numero_membre", flat=True)
        max_seq = max((Adhesion.extraire_ordre(n) for n in nums), default=0)
        return f"{max_seq + 1:06d}"

    @transaction.atomic
    def valider(self, user=None):
        """Valide l'adhésion, crée le Membre et génère la carte."""
        if self.statut == self.Statut.VALIDE and hasattr(self, "membre"):
            return self.membre

        if not self.numero_membre:
            self.numero_membre = self.generer_numero_membre()

        self.statut = self.Statut.VALIDE
        self.valide_par = user
        self.motif_rejet = ""
        self.save()

        membre, _ = Membre.objects.get_or_create(
            adhesion=self,
            defaults={"actif": True, "date_activation": timezone.now()},
        )
        if not membre.actif:
            membre.actif = True
            membre.date_activation = timezone.now()
            membre.save(update_fields=["actif", "date_activation"])

        from membership.services.carte import generate_membership_card

        generate_membership_card(membre)
        return membre

    def rejeter(self, motif="", user=None):
        self.statut = self.Statut.REJETE
        self.motif_rejet = motif
        self.valide_par = user
        self.save(update_fields=["statut", "motif_rejet", "valide_par", "date_modification"])


class Membre(models.Model):
    """Membre actif issu d'une adhésion validée."""

    adhesion = models.OneToOneField(
        Adhesion, on_delete=models.CASCADE, related_name="membre"
    )
    actif = models.BooleanField(default=True, db_index=True)
    date_activation = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Membre"
        verbose_name_plural = "Membres"
        ordering = ["-date_activation"]

    def __str__(self):
        return f"{self.adhesion.nom_complet} ({self.adhesion.numero_membre})"

    @property
    def numero_membre(self):
        return self.adhesion.numero_membre

    @property
    def nom_complet(self):
        return self.adhesion.nom_complet

    @property
    def section_locale(self):
        return self.adhesion.section_locale

    @property
    def province(self):
        return self.adhesion.section_locale.province


class CarteMembre(models.Model):
    """Carte de membre avec QR code et PDF imprimable."""

    membre = models.OneToOneField(
        Membre, on_delete=models.CASCADE, related_name="carte"
    )
    numero_carte = models.CharField(max_length=40, unique=True, db_index=True)
    date_emission = models.DateField(default=date.today)
    date_expiration = models.DateField()
    qr_code = models.ImageField(upload_to="cartes/qr/%Y/%m/", blank=True)
    image_carte = models.ImageField(
        "Aperçu carte", upload_to="cartes/img/%Y/%m/", blank=True
    )
    fichier_pdf = models.FileField(upload_to="cartes/pdf/%Y/%m/", blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Carte de membre"
        verbose_name_plural = "Cartes de membre"
        ordering = ["-date_emission"]

    def __str__(self):
        return self.numero_carte

    @property
    def est_expiree(self):
        return date.today() > self.date_expiration
