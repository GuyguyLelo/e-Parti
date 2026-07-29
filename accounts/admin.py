"""Admin Django — comptes utilisateurs."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "nom",
        "post_nom",
        "prenom",
        "role",
        "province",
        "telephone",
        "is_active",
    )
    list_filter = ("role", "province", "is_active", "is_staff")
    search_fields = ("username", "nom", "post_nom", "prenom", "email", "telephone")
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Profil e-Parti",
            {
                "fields": (
                    "nom",
                    "post_nom",
                    "prenom",
                    "telephone",
                    "role",
                    "province",
                    "section_locale",
                )
            },
        ),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Profil e-Parti",
            {
                "fields": (
                    "nom",
                    "post_nom",
                    "prenom",
                    "telephone",
                    "role",
                    "province",
                    "section_locale",
                )
            },
        ),
    )
