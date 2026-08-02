from django.urls import path

from . import views

app_name = "territoires"

urlpatterns = [
    path("", views.parametres_hub, name="parametres_hub"),
    path("provinces/", views.province_list, name="province_list"),
    path("provinces/nouvelle/", views.province_create, name="province_create"),
    path("provinces/<int:pk>/modifier/", views.province_edit, name="province_edit"),
    path("villes/", views.ville_list, name="ville_list"),
    path("villes/nouvelle/", views.ville_create, name="ville_create"),
    path("villes/<int:pk>/modifier/", views.ville_edit, name="ville_edit"),
    path("communes/", views.commune_list, name="commune_list"),
    path("communes/nouvelle/", views.commune_create, name="commune_create"),
    path("communes/<int:pk>/modifier/", views.commune_edit, name="commune_edit"),
    path("sections/", views.section_list, name="section_list"),
    path("sections/nouvelle/", views.section_create, name="section_create"),
    path("sections/<int:pk>/modifier/", views.section_edit, name="section_edit"),
]
