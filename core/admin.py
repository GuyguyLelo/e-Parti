from django.contrib import admin

from core.models import ActionLog, Notification


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "path", "ip_address", "created_at")
    list_filter = ("created_at",)
    search_fields = ("action", "path", "user__username")
    readonly_fields = ("user", "action", "objet", "details", "ip_address", "path", "created_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("titre", "destinataire", "canal", "lu", "envoye", "created_at")
    list_filter = ("canal", "lu", "envoye")
    search_fields = ("titre", "message", "telephone", "email")
