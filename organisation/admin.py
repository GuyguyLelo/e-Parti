from django.contrib import admin

from organisation.models import AffectationPolitique, Evenement


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ("titre", "type", "date", "lieu", "province", "actif")
    list_filter = ("type", "province", "actif")
    search_fields = ("titre", "lieu")
    date_hierarchy = "date"


@admin.register(AffectationPolitique)
class AffectationPolitiqueAdmin(admin.ModelAdmin):
    list_display = ("membre", "role", "province", "commune", "section_locale", "actif")
    list_filter = ("role", "province", "actif")
    search_fields = ("membre__adhesion__nom", "membre__adhesion__numero_membre")
    autocomplete_fields = ("membre", "province", "commune", "section_locale")
