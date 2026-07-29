"""Notifications internes et stubs SMS/email."""
from core.models import Notification


def notify_user(user, titre, message, canal=Notification.Canal.INTERNE):
    return Notification.objects.create(
        destinataire=user,
        titre=titre,
        message=message,
        canal=canal,
        email=getattr(user, "email", "") or "",
        telephone=getattr(user, "telephone", "") or "",
    )


def notify_sms(telephone, titre, message):
    """Crée une notification SMS (envoi réel via Celery / gateway)."""
    notif = Notification.objects.create(
        telephone=telephone,
        titre=titre,
        message=message,
        canal=Notification.Canal.SMS,
    )
    try:
        from membership.tasks import task_send_sms

        task_send_sms.delay(telephone, message)
        notif.envoye = True
        notif.save(update_fields=["envoye"])
    except Exception:
        pass
    return notif
