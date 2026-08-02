from django.contrib import admin

from finances.models import Cotisation


@admin.register(Cotisation)
class CotisationAdmin(admin.ModelAdmin):
    list_display = ("membre", "montant_fmt", "type", "date_paiement", "mode_paiement", "has_preuve")
    list_filter = ("type", "devise", "mode_paiement", "date_paiement")
    search_fields = (
        "membre__adhesion__nom",
        "membre__adhesion__numero_membre",
        "reference",
    )
    date_hierarchy = "date_paiement"
    autocomplete_fields = ("membre",)
    readonly_fields = ()

    @admin.display(description="Montant", ordering="montant")
    def montant_fmt(self, obj):
        return obj.montant_affiche

    @admin.display(description="Preuve", boolean=True)
    def has_preuve(self, obj):
        return bool(obj.preuve)
