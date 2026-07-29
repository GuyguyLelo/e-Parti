"""Gestion financière : cotisations et dons."""
from django.db import models


class Cotisation(models.Model):
    class TypeCotisation(models.TextChoices):
        ADHESION = "adhesion", "Frais d'adhésion"
        MENSUELLE = "mensuelle", "Cotisation mensuelle"
        DON = "don", "Don"
        EXCEPTIONNELLE = "exceptionnelle", "Cotisation exceptionnelle"

    membre = models.ForeignKey(
        "membership.Membre",
        on_delete=models.CASCADE,
        related_name="cotisations",
    )
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    devise = models.CharField(max_length=5, default="CDF")
    date_paiement = models.DateField()
    type = models.CharField(
        max_length=20, choices=TypeCotisation.choices, default=TypeCotisation.MENSUELLE
    )
    reference = models.CharField(max_length=80, blank=True)
    mode_paiement = models.CharField(
        max_length=40,
        blank=True,
        help_text="Espèces, Mobile Money, Banque…",
    )
    notes = models.TextField(blank=True)
    enregistre_par = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cotisations_enregistrees",
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cotisation"
        verbose_name_plural = "Cotisations"
        ordering = ["-date_paiement", "-date_creation"]

    def __str__(self):
        return f"{self.membre} — {self.montant} {self.devise} ({self.get_type_display()})"
