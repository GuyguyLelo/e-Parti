"""
Utilisateur personnalisé e-Parti.
Rôles : Admin national, Provincial, Local.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN_NATIONAL = "ADMIN_NATIONAL", "Administrateur national"
        PROVINCIAL = "PROVINCIAL", "Responsable provincial"
        LOCAL = "LOCAL", "Responsable local"

    nom = models.CharField("Nom", max_length=100, blank=True)
    post_nom = models.CharField("Post-nom", max_length=100, blank=True)
    prenom = models.CharField("Prénom", max_length=100, blank=True)
    telephone = models.CharField("Téléphone", max_length=30, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.LOCAL,
        db_index=True,
    )
    # Périmètre territorial (optionnel selon le rôle)
    province = models.ForeignKey(
        "territoires.Province",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responsables",
        verbose_name="Province assignée",
    )
    section_locale = models.ForeignKey(
        "territoires.SectionLocale",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responsables",
        verbose_name="Section locale assignée",
    )

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["nom", "post_nom", "prenom"]

    def __str__(self):
        full = self.get_full_display_name()
        return full or self.username

    def get_full_display_name(self):
        parts = [self.nom, self.post_nom, self.prenom]
        return " ".join(p for p in parts if p).strip()

    @property
    def is_admin_national(self):
        return self.role == self.Role.ADMIN_NATIONAL or self.is_superuser

    @property
    def is_provincial(self):
        return self.role == self.Role.PROVINCIAL

    @property
    def is_local(self):
        return self.role == self.Role.LOCAL
