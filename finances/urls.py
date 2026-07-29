from django.urls import path

from . import views

app_name = "finances"

urlpatterns = [
    path("cotisations/", views.cotisation_list, name="cotisation_list"),
    path("cotisations/nouvelle/", views.cotisation_create, name="cotisation_create"),
    path("rapports/", views.rapport_financier, name="rapport"),
    path("export/excel/", views.export_excel, name="export_excel"),
]
