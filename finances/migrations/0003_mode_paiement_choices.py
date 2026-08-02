# Generated manually for mode_paiement choices

from django.db import migrations, models


def normalize_modes(apps, schema_editor):
    Cotisation = apps.get_model("finances", "Cotisation")
    mapping = {
        "espèces": "especes",
        "especes": "especes",
        "cash": "especes",
        "m-pesa": "mpesa",
        "mpesa": "mpesa",
        "airtel money": "airtel",
        "airtel": "airtel",
        "orange money": "orange",
        "orange": "orange",
        "mobile money": "mpesa",
        "banque": "banque",
        "virement": "banque",
        "virement / banque": "banque",
        "chèque": "cheque",
        "cheque": "cheque",
        "carte": "carte",
        "carte bancaire": "carte",
        "autre": "autre",
    }
    valid = {
        "especes",
        "mpesa",
        "airtel",
        "orange",
        "banque",
        "cheque",
        "carte",
        "autre",
        "",
    }
    for c in Cotisation.objects.all():
        raw = (c.mode_paiement or "").strip()
        if not raw:
            continue
        key = raw.lower()
        new_val = mapping.get(key, "autre" if key not in valid else key)
        if new_val != c.mode_paiement:
            c.mode_paiement = new_val
            c.save(update_fields=["mode_paiement"])


class Migration(migrations.Migration):
    dependencies = [
        ("finances", "0002_devise_choices"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cotisation",
            name="mode_paiement",
            field=models.CharField(
                blank=True,
                choices=[
                    ("especes", "Espèces"),
                    ("mpesa", "M-Pesa"),
                    ("airtel", "Airtel Money"),
                    ("orange", "Orange Money"),
                    ("banque", "Virement / Banque"),
                    ("cheque", "Chèque"),
                    ("carte", "Carte bancaire"),
                    ("autre", "Autre"),
                ],
                default="",
                max_length=20,
            ),
        ),
        migrations.RunPython(normalize_modes, migrations.RunPython.noop),
    ]
