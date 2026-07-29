"""Organisation territoriale RDC : Province → Ville → Commune → SectionLocale."""
from django.db import models
from django.utils.text import slugify


class Province(models.Model):
    """Province de la République Démocratique du Congo."""

    nom = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=10, unique=True, help_text="Ex: KIN, KOC")
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Province"
        verbose_name_plural = "Provinces"
        ordering = ["nom"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom


class Ville(models.Model):
    """Ville / territoire au sein d'une province."""

    province = models.ForeignKey(
        Province, on_delete=models.CASCADE, related_name="villes"
    )
    nom = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Ville"
        verbose_name_plural = "Villes"
        ordering = ["nom"]
        unique_together = [("province", "nom")]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} ({self.province.nom})"


class Commune(models.Model):
    """Commune / secteur rattaché à une ville."""

    ville = models.ForeignKey(
        Ville, on_delete=models.CASCADE, related_name="communes"
    )
    nom = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Commune"
        verbose_name_plural = "Communes"
        ordering = ["nom"]
        unique_together = [("ville", "nom")]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} — {self.ville.nom}"

    @property
    def province(self):
        return self.ville.province


class SectionLocale(models.Model):
    """Cellule de base du parti au niveau local."""

    commune = models.ForeignKey(
        Commune, on_delete=models.CASCADE, related_name="sections"
    )
    nom = models.CharField(max_length=150)
    code = models.CharField(max_length=30, unique=True)
    adresse = models.CharField(max_length=255, blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    actif = models.BooleanField(default=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    class Meta:
        verbose_name = "Section locale"
        verbose_name_plural = "Sections locales"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.commune})"

    @property
    def province(self):
        return self.commune.ville.province
