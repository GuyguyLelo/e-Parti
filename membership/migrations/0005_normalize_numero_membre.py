"""Normalise les matricules : EPARTI-AAAA-000001 → 000001."""

from django.db import migrations
from django.utils import timezone


def extract_ordre(numero: str) -> int:
    if not numero:
        return 0
    if "-" in numero:
        try:
            return int(numero.rsplit("-", 1)[-1])
        except ValueError:
            return 0
    try:
        return int(numero)
    except ValueError:
        digits = "".join(c for c in numero if c.isdigit())
        return int(digits[-6:]) if digits else 0


def forwards_normalize(apps, schema_editor):
    Adhesion = apps.get_model("membership", "Adhesion")
    CarteMembre = apps.get_model("membership", "CarteMembre")

    rows = list(
        Adhesion.objects.exclude(numero_membre__isnull=True)
        .exclude(numero_membre="")
        .values("pk", "numero_membre")
    )

    updates = []
    for row in rows:
        ordre = extract_ordre(row["numero_membre"])
        if not ordre:
            continue
        new_num = f"{ordre:06d}"
        if new_num != row["numero_membre"]:
            updates.append((row["pk"], new_num))

    for pk, _new in updates:
        Adhesion.objects.filter(pk=pk).update(numero_membre=f"__tmp_{pk}")

    for pk, new in updates:
        Adhesion.objects.filter(pk=pk).update(numero_membre=new)

    for carte in CarteMembre.objects.select_related("membre__adhesion").all():
        num = carte.membre.adhesion.numero_membre or ""
        if not num:
            continue
        suffix = num.split("-")[-1] if "-" in num else num
        try:
            suffix = f"{int(suffix):06d}"
        except ValueError:
            continue
        year = None
        if carte.numero_carte and carte.numero_carte.startswith("CARD-"):
            parts = carte.numero_carte.split("-")
            if len(parts) >= 2 and parts[1].isdigit():
                year = parts[1]
        if not year and carte.date_emission:
            year = str(carte.date_emission.year)
        if not year:
            year = str(timezone.now().year)
        new_carte = f"CARD-{year}-{suffix}"
        if carte.numero_carte != new_carte:
            carte.numero_carte = new_carte
            carte.save(update_fields=["numero_carte"])


def backwards(apps, schema_editor):
    # Non réversible de façon fiable (préfixe / année perdus).
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("membership", "0004_remove_carte_modele_fields"),
    ]

    operations = [
        migrations.RunPython(forwards_normalize, backwards),
    ]
