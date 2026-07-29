"""Campagnes, événements et affectations politiques."""
from django.conf import settings
from django.db import models


class Evenement(models.Model):
    """Événement de campagne ou mobilisation."""

    class TypeEvenement(models.TextChoices):
        MEETING = "MEETING", "Meeting"
        MOBILISATION = "MOBILISATION", "Mobilisation"
        FORMATION = "FORMATION", "Formation"
        ASSEMBLEE = "ASSEMBLEE", "Assemblée"
        AUTRE = "AUTRE", "Autre"

    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type = models.CharField(
        max_length=20, choices=TypeEvenement.choices, default=TypeEvenement.MEETING
    )
    date = models.DateTimeField()
    lieu = models.CharField(max_length=255)
    organisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="evenements_organises",
    )
    province = models.ForeignKey(
        "territoires.Province",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evenements",
    )
    section_locale = models.ForeignKey(
        "territoires.SectionLocale",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evenements",
    )
    participants_attendus = models.PositiveIntegerField(default=0)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.titre} — {self.date:%d/%m/%Y}"


class AffectationPolitique(models.Model):
    """Affectation d'un membre à un rôle politique sur une zone."""

    class RolePolitique(models.TextChoices):
        COORDINATEUR = "COORDINATEUR", "Coordinateur"
        MOBILISATEUR = "MOBILISATEUR", "Mobilisateur"
        SECRETAIRE = "SECRETAIRE", "Secrétaire"
        TRESORIER = "TRESORIER", "Trésorier"
        PRESIDENT_SECTION = "PRESIDENT_SECTION", "Président de section"
        AUTRE = "AUTRE", "Autre"

    membre = models.ForeignKey(
        "membership.Membre",
        on_delete=models.CASCADE,
        related_name="affectations",
    )
    role = models.CharField(max_length=30, choices=RolePolitique.choices)
    province = models.ForeignKey(
        "territoires.Province",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="affectations",
    )
    commune = models.ForeignKey(
        "territoires.Commune",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="affectations",
    )
    section_locale = models.ForeignKey(
        "territoires.SectionLocale",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="affectations",
    )
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    actif = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Affectation politique"
        verbose_name_plural = "Affectations politiques"
        ordering = ["-date_debut"]

    def __str__(self):
        zone = self.section_locale or self.commune or self.province or "—"
        return f"{self.membre} — {self.get_role_display()} ({zone})"
