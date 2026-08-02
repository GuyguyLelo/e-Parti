"""Admin membership — validation et génération de cartes."""
from django.contrib import admin, messages
from django.utils.html import format_html

from membership.models import Adhesion, CarteMembre, Membre
from membership.services.carte import generate_membership_card


@admin.action(description="Valider et générer carte")
def valider_et_generer_carte(modeladmin, request, queryset):
    ok, err = 0, 0
    for adhesion in queryset:
        try:
            adhesion.valider(user=request.user)
            ok += 1
        except Exception as exc:
            err += 1
            modeladmin.message_user(
                request, f"Erreur {adhesion} : {exc}", level=messages.ERROR
            )
    modeladmin.message_user(
        request, f"{ok} adhésion(s) validée(s). {err} erreur(s).", level=messages.SUCCESS
    )


@admin.register(Adhesion)
class AdhesionAdmin(admin.ModelAdmin):
    list_display = (
        "nom_complet",
        "numero_membre",
        "telephone",
        "statut",
        "province_display",
        "section_locale",
        "date_creation",
    )
    list_filter = (
        "statut",
        "qualite",
        "sexe",
        "section_locale__commune__ville__province",
        "date_creation",
    )
    search_fields = (
        "nom",
        "post_nom",
        "prenom",
        "numero_membre",
        "telephone",
        "email",
        "numero_piece_identite",
    )
    readonly_fields = ("numero_membre", "date_creation", "date_modification", "photo_preview")
    actions = [valider_et_generer_carte]
    date_hierarchy = "date_creation"
    autocomplete_fields = ("province_origine", "section_locale")

    @admin.display(description="Province")
    def province_display(self, obj):
        return obj.section_locale.province.nom

    @admin.display(description="Photo")
    def photo_preview(self, obj):
        if obj.photo1:
            return format_html('<img src="{}" style="max-height:120px"/>', obj.photo1.url)
        return "—"


@admin.register(Membre)
class MembreAdmin(admin.ModelAdmin):
    list_display = ("__str__", "actif", "date_activation", "numero")
    list_filter = ("actif", "adhesion__section_locale__commune__ville__province")
    search_fields = (
        "adhesion__nom",
        "adhesion__post_nom",
        "adhesion__prenom",
        "adhesion__numero_membre",
    )
    autocomplete_fields = ("adhesion",)

    @admin.display(description="N° membre")
    def numero(self, obj):
        return obj.numero_membre


@admin.register(CarteMembre)
class CarteMembreAdmin(admin.ModelAdmin):
    list_display = (
        "numero_carte",
        "membre",
        "date_emission",
        "date_expiration",
        "actif",
        "pdf_link",
    )
    list_filter = ("actif", "date_emission")
    search_fields = ("numero_carte", "membre__adhesion__numero_membre")
    actions = ["regenerer_cartes"]

    @admin.display(description="PDF")
    def pdf_link(self, obj):
        if obj.fichier_pdf:
            return format_html('<a href="{}" target="_blank">Télécharger</a>', obj.fichier_pdf.url)
        return "—"

    @admin.action(description="Régénérer les cartes sélectionnées")
    def regenerer_cartes(self, request, queryset):
        for carte in queryset:
            generate_membership_card(carte.membre)
        self.message_user(request, f"{queryset.count()} carte(s) régénérée(s).")
