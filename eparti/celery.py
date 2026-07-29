"""Configuration Celery pour tâches asynchrones (génération cartes, SMS, etc.)."""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eparti.settings")

app = Celery("eparti")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
