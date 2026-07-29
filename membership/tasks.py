"""Tâches Celery optionnelles."""
from celery import shared_task


@shared_task
def task_generate_card(membre_id: int):
    from membership.models import Membre
    from membership.services.carte import generate_membership_card

    membre = Membre.objects.get(pk=membre_id)
    generate_membership_card(membre)
    return f"Carte générée pour membre {membre_id}"


@shared_task
def task_send_sms(telephone: str, message: str):
    """
    Stub SMS RDC — brancher une API locale (Africastalking, Twilio, opérateur).
    """
    # Placeholder : journaliser / appeler le gateway SMS
    return {"telephone": telephone, "status": "queued", "message": message[:80]}
