from django.urls import path

from . import views

app_name = "organisation"

urlpatterns = [
    path("evenements/", views.evenement_list, name="evenement_list"),
    path("evenements/nouveau/", views.evenement_create, name="evenement_create"),
    path("affectations/", views.affectation_list, name="affectation_list"),
]
