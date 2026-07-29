from django.contrib import admin

from territoires.models import Commune, Province, SectionLocale, Ville


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "actif")
    search_fields = ("nom", "code")
    list_filter = ("actif",)


@admin.register(Ville)
class VilleAdmin(admin.ModelAdmin):
    list_display = ("nom", "province", "actif")
    list_filter = ("province", "actif")
    search_fields = ("nom",)


@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display = ("nom", "ville", "actif")
    list_filter = ("ville__province", "actif")
    search_fields = ("nom",)


@admin.register(SectionLocale)
class SectionLocaleAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "commune", "actif")
    list_filter = ("commune__ville__province", "actif")
    search_fields = ("nom", "code")
