"""Gestion financière : cotisations et dons."""
from django.db import models

from finances.formatting import format_montant


class Cotisation(models.Model):
    class TypeCotisation(models.TextChoices):
        ADHESION = "adhesion", "Frais d'adhésion"
        MENSUELLE = "mensuelle", "Cotisation mensuelle"
        DON = "don", "Don"
        EXCEPTIONNELLE = "exceptionnelle", "Cotisation exceptionnelle"

    class Devise(models.TextChoices):
        CDF = "CDF", "Franc congolais (CDF)"
        USD = "USD", "Dollar américain (USD)"
        EUR = "EUR", "Euro (EUR)"

    class ModePaiement(models.TextChoices):
        ESPECES = "especes", "Espèces"
        MPESA = "mpesa", "M-Pesa"
        AIRTEL = "airtel", "Airtel Money"
        ORANGE = "orange", "Orange Money"
        BANQUE = "banque", "Virement / Banque"
        CHEQUE = "cheque", "Chèque"
        CARTE = "carte", "Carte bancaire"
        AUTRE = "autre", "Autre"

    membre = models.ForeignKey(
        "membership.Membre",
        on_delete=models.CASCADE,
        related_name="cotisations",
    )
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    devise = models.CharField(
        max_length=5,
        choices=Devise.choices,
        default=Devise.CDF,
    )
    date_paiement = models.DateField()
    type = models.CharField(
        max_length=20, choices=TypeCotisation.choices, default=TypeCotisation.MENSUELLE
    )
    reference = models.CharField(max_length=80, blank=True)
    mode_paiement = models.CharField(
        max_length=20,
        choices=ModePaiement.choices,
        blank=True,
        default="",
    )
    preuve = models.ImageField(
        "Preuve de paiement",
        upload_to="cotisations/preuves/%Y/%m/",
        blank=True,
        null=True,
        help_text="Capture d'écran, reçu ou photo du paiement",
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

    @property
    def montant_affiche(self) -> str:
        return format_montant(self.montant, self.devise)

    def __str__(self):
        return f"{self.membre} — {self.montant_affiche} ({self.get_type_display()})"
