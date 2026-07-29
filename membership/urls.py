"""URLs membership."""
from django.urls import path

from . import views

app_name = "membership"

urlpatterns = [
    path("nouvelle/", views.adhesion_create, name="adhesion_create"),
    path("succes/<int:pk>/", views.adhesion_success, name="adhesion_success"),
    path("", views.adhesion_list, name="adhesion_list"),
    path("<int:pk>/", views.adhesion_detail, name="adhesion_detail"),
    path("<int:pk>/fiche.pdf", views.adhesion_fiche_pdf, name="adhesion_fiche_pdf"),
    path("<int:pk>/valider/", views.adhesion_valider, name="adhesion_valider"),
    path("<int:pk>/rejeter/", views.adhesion_rejeter, name="adhesion_rejeter"),
    path("membres/", views.membre_list, name="membre_list"),
    path("membres/<int:pk>/", views.membre_detail, name="membre_detail"),
    path("membres/<int:pk>/modifier/", views.membre_edit, name="membre_edit"),
    path("cartes/<int:membre_id>/", views.carte_detail, name="carte_detail"),
    path("cartes/<int:membre_id>/generer/", views.carte_generer, name="carte_generer"),
    path("cartes/<int:membre_id>/telecharger/", views.carte_telecharger, name="carte_telecharger"),
    path("impression/", views.impression_batch, name="impression"),
    path("verifier/<str:numero_membre>/", views.verifier_membre, name="verifier"),
]
