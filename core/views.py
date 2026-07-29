"""Vues dashboard, statistiques et pages publiques."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from core.permissions import role_required
from finances.models import Cotisation
from membership.models import Adhesion, Membre
from organisation.models import Evenement
from territoires.models import Province


def _json_safe(value):
    """Sérialise les types non JSON (Decimal) pour Chart.js."""
    if isinstance(value, Decimal):
        return float(value)
    return value


def home(request):
    stats = {
        "membres": Membre.objects.filter(actif=True).count(),
        "provinces": Province.objects.filter(actif=True).count(),
        "adhesions_attente": Adhesion.objects.filter(statut=Adhesion.Statut.EN_ATTENTE).count(),
    }
    return render(request, "core/home.html", {"stats": stats})


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def dashboard(request):
    user = request.user
    adhesions = Adhesion.objects.all()
    membres = Membre.objects.filter(actif=True)

    if user.is_provincial and user.province_id:
        adhesions = adhesions.filter(section_locale__commune__ville__province=user.province)
        membres = membres.filter(adhesion__section_locale__commune__ville__province=user.province)
    elif user.is_local and user.section_locale_id:
        adhesions = adhesions.filter(section_locale=user.section_locale)
        membres = membres.filter(adhesion__section_locale=user.section_locale)

    membres_par_province = list(
        membres.values("adhesion__section_locale__commune__ville__province__nom")
        .annotate(total=Count("id"))
        .order_by("-total")[:12]
    )

    six_months_ago = timezone.now() - timedelta(days=180)
    croissance = list(
        membres.filter(date_activation__gte=six_months_ago)
        .annotate(mois=TruncMonth("date_activation"))
        .values("mois")
        .annotate(total=Count("id"))
        .order_by("mois")
    )

    total_membres = membres.count()
    actifs_recents = membres.filter(
        date_activation__gte=timezone.now() - timedelta(days=90)
    ).count()
    taux_activite = round((actifs_recents / total_membres) * 100, 1) if total_membres else 0

    cotisations = Cotisation.objects.filter(membre__in=membres)
    total_finances = cotisations.aggregate(s=Sum("montant"))["s"] or 0
    finances_par_type = list(
        cotisations.values("type").annotate(total=Sum("montant"), n=Count("id")).order_by("-total")
    )

    adhesions_attente = adhesions.filter(statut=Adhesion.Statut.EN_ATTENTE).count()
    adhesions_validees = adhesions.filter(statut=Adhesion.Statut.VALIDE).count()
    adhesions_rejetees = adhesions.filter(statut=Adhesion.Statut.REJETE).count()

    # Données Chart.js (JSON)
    chart_provinces = {
        "labels": [
            row["adhesion__section_locale__commune__ville__province__nom"] or "—"
            for row in membres_par_province
        ],
        "data": [row["total"] for row in membres_par_province],
    }
    chart_croissance = {
        "labels": [
            row["mois"].strftime("%b %Y") if row["mois"] else "—"
            for row in croissance
        ],
        "data": [row["total"] for row in croissance],
    }
    chart_statuts = {
        "labels": ["En attente", "Validées", "Rejetées"],
        "data": [adhesions_attente, adhesions_validees, adhesions_rejetees],
    }
    type_labels = {
        "adhesion": "Adhésion",
        "mensuelle": "Mensuelle",
        "don": "Don",
        "exceptionnelle": "Exceptionnelle",
    }
    chart_finances = {
        "labels": [type_labels.get(r["type"], r["type"]) for r in finances_par_type],
        "data": [_json_safe(r["total"] or 0) for r in finances_par_type],
    }

    context = {
        "total_membres": total_membres,
        "adhesions_attente": adhesions_attente,
        "adhesions_validees": adhesions_validees,
        "adhesions_rejetees": adhesions_rejetees,
        "membres_par_province": membres_par_province,
        "croissance": croissance,
        "taux_activite": taux_activite,
        "total_finances": total_finances,
        "evenements_a_venir": Evenement.objects.filter(
            date__gte=timezone.now(), actif=True
        ).order_by("date")[:5],
        "dernieres_adhesions": adhesions.order_by("-date_creation")[:8],
        "chart_provinces": chart_provinces,
        "chart_croissance": chart_croissance,
        "chart_statuts": chart_statuts,
        "chart_finances": chart_finances,
    }
    return render(request, "core/dashboard.html", context)
