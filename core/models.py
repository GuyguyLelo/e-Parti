"""Journal d'actions et utilitaires transverses."""
from django.conf import settings
from django.db import models


class ActionLog(models.Model):
    """Journal des actions utilisateurs (audit)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions",
    )
    action = models.CharField(max_length=100)
    objet = models.CharField(max_length=200, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    path = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Journal d'action"
        verbose_name_plural = "Journal des actions"
        ordering = ["-created_at"]

    def __str__(self):
        who = self.user or "anonyme"
        return f"{who} — {self.action} ({self.created_at:%Y-%m-%d %H:%M})"


class Notification(models.Model):
    """Notification interne (email/SMS optionnel)."""

    class Canal(models.TextChoices):
        INTERNE = "INTERNE", "Interne"
        EMAIL = "EMAIL", "Email"
        SMS = "SMS", "SMS"

    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    titre = models.CharField(max_length=200)
    message = models.TextField()
    canal = models.CharField(max_length=10, choices=Canal.choices, default=Canal.INTERNE)
    lu = models.BooleanField(default=False)
    envoye = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return self.titre
