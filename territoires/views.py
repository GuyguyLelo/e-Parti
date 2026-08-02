"""Paramètres admin : gestion des tables référentielles territoriales."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from core.pagination import paginate
from core.permissions import role_required
from territoires.forms import CommuneForm, ProvinceForm, SectionLocaleForm, VilleForm
from territoires.models import Commune, Province, SectionLocale, Ville


@login_required
@role_required("ADMIN_NATIONAL")
def parametres_hub(request):
    """Accueil Paramètres — tables référentielles."""
    cards = [
        {
            "title": "Provinces",
            "count": Province.objects.count(),
            "actifs": Province.objects.filter(actif=True).count(),
            "url": "territoires:province_list",
            "create_url": "territoires:province_create",
            "desc": "Provinces de la RDC",
            "accent": "blue",
            "step": "01",
            "icon": "map",
        },
        {
            "title": "Villes",
            "count": Ville.objects.count(),
            "actifs": Ville.objects.filter(actif=True).count(),
            "url": "territoires:ville_list",
            "create_url": "territoires:ville_create",
            "desc": "Villes / territoires",
            "accent": "yellow",
            "step": "02",
            "icon": "city",
        },
        {
            "title": "Communes",
            "count": Commune.objects.count(),
            "actifs": Commune.objects.filter(actif=True).count(),
            "url": "territoires:commune_list",
            "create_url": "territoires:commune_create",
            "desc": "Communes / secteurs",
            "accent": "red",
            "step": "03",
            "icon": "grid",
        },
        {
            "title": "Sections locales",
            "count": SectionLocale.objects.count(),
            "actifs": SectionLocale.objects.filter(actif=True).count(),
            "url": "territoires:section_list",
            "create_url": "territoires:section_create",
            "desc": "Cellules de base du parti",
            "accent": "deep",
            "step": "04",
            "icon": "pin",
        },
    ]
    return render(request, "territoires/parametres_hub.html", {"cards": cards})


def _cell_value(obj, key):
    val = getattr(obj, key, "")
    if isinstance(val, bool):
        return "Oui" if val else "Non"
    return val


def _list_view(request, *, title, create_url, edit_url_name, queryset, search_fields, columns):
    q = request.GET.get("q", "").strip()
    actif = request.GET.get("actif", "")
    qs = queryset
    if q and search_fields:
        query = Q()
        for field in search_fields:
            query |= Q(**{f"{field}__icontains": q})
        qs = qs.filter(query)
    if actif == "1":
        qs = qs.filter(actif=True)
    elif actif == "0":
        qs = qs.filter(actif=False)

    page = paginate(request, qs)
    rows = []
    for obj in page.object_list:
        rows.append(
            {
                "pk": obj.pk,
                "cells": [_cell_value(obj, key) for key, _label in columns],
                "actif": obj.actif,
            }
        )

    return render(
        request,
        "territoires/ref_list.html",
        {
            "title": title,
            "create_url": create_url,
            "edit_url_name": edit_url_name,
            "columns": columns,
            "rows": rows,
            "page_obj": page,
            "q": q,
            "actif": actif,
        },
    )


@login_required
@role_required("ADMIN_NATIONAL")
def province_list(request):
    return _list_view(
        request,
        title="Provinces",
        create_url="territoires:province_create",
        edit_url_name="territoires:province_edit",
        queryset=Province.objects.order_by("nom"),
        search_fields=["nom", "code"],
        columns=[
            ("nom", "Nom"),
            ("code", "Code"),
            ("actif", "Actif"),
        ],
    )


@login_required
@role_required("ADMIN_NATIONAL")
def ville_list(request):
    return _list_view(
        request,
        title="Villes",
        create_url="territoires:ville_create",
        edit_url_name="territoires:ville_edit",
        queryset=Ville.objects.select_related("province").order_by(
            "province__nom", "nom"
        ),
        search_fields=["nom", "province__nom"],
        columns=[
            ("nom", "Nom"),
            ("province", "Province"),
            ("actif", "Actif"),
        ],
    )


@login_required
@role_required("ADMIN_NATIONAL")
def commune_list(request):
    return _list_view(
        request,
        title="Communes",
        create_url="territoires:commune_create",
        edit_url_name="territoires:commune_edit",
        queryset=Commune.objects.select_related("ville__province").order_by(
            "ville__province__nom", "ville__nom", "nom"
        ),
        search_fields=["nom", "ville__nom", "ville__province__nom"],
        columns=[
            ("nom", "Nom"),
            ("ville", "Ville"),
            ("actif", "Actif"),
        ],
    )


@login_required
@role_required("ADMIN_NATIONAL")
def section_list(request):
    return _list_view(
        request,
        title="Sections locales",
        create_url="territoires:section_create",
        edit_url_name="territoires:section_edit",
        queryset=SectionLocale.objects.select_related(
            "commune__ville__province"
        ).order_by("nom"),
        search_fields=["nom", "code", "commune__nom"],
        columns=[
            ("nom", "Nom"),
            ("code", "Code"),
            ("commune", "Commune"),
            ("actif", "Actif"),
        ],
    )


def _form_view(request, form_class, instance, title, list_url, success_msg):
    if request.method == "POST":
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, success_msg)
            return redirect(list_url)
    else:
        form = form_class(instance=instance)
    return render(
        request,
        "territoires/ref_form.html",
        {
            "form": form,
            "title": title,
            "list_url": list_url,
            "is_edit": instance is not None and instance.pk is not None,
        },
    )


@login_required
@role_required("ADMIN_NATIONAL")
def province_create(request):
    return _form_view(
        request,
        ProvinceForm,
        None,
        "Nouvelle province",
        "territoires:province_list",
        "Province enregistrée.",
    )


@login_required
@role_required("ADMIN_NATIONAL")
def province_edit(request, pk):
    obj = get_object_or_404(Province, pk=pk)
    return _form_view(
        request,
        ProvinceForm,
        obj,
        f"Modifier — {obj.nom}",
        "territoires:province_list",
        "Province mise à jour.",
    )


@login_required
@role_required("ADMIN_NATIONAL")
def ville_create(request):
    return _form_view(
        request,
        VilleForm,
        None,
        "Nouvelle ville",
        "territoires:ville_list",
        "Ville enregistrée.",
    )


@login_required
@role_required("ADMIN_NATIONAL")
def ville_edit(request, pk):
    obj = get_object_or_404(Ville, pk=pk)
    return _form_view(
        request,
        VilleForm,
        obj,
        f"Modifier — {obj.nom}",
        "territoires:ville_list",
        "Ville mise à jour.",
    )


@login_required
@role_required("ADMIN_NATIONAL")
def commune_create(request):
    return _form_view(
        request,
        CommuneForm,
        None,
        "Nouvelle commune",
        "territoires:commune_list",
        "Commune enregistrée.",
    )


@login_required
@role_required("ADMIN_NATIONAL")
def commune_edit(request, pk):
    obj = get_object_or_404(Commune, pk=pk)
    return _form_view(
        request,
        CommuneForm,
        obj,
        f"Modifier — {obj.nom}",
        "territoires:commune_list",
        "Commune mise à jour.",
    )


@login_required
@role_required("ADMIN_NATIONAL")
def section_create(request):
    return _form_view(
        request,
        SectionLocaleForm,
        None,
        "Nouvelle section locale",
        "territoires:section_list",
        "Section enregistrée.",
    )


@login_required
@role_required("ADMIN_NATIONAL")
def section_edit(request, pk):
    obj = get_object_or_404(SectionLocale, pk=pk)
    return _form_view(
        request,
        SectionLocaleForm,
        obj,
        f"Modifier — {obj.nom}",
        "territoires:section_list",
        "Section mise à jour.",
    )
