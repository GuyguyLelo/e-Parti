"""Vues dashboard, statistiques et pages publiques."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from core.permissions import role_required, scope_adhesions, scope_membres
from finances.formatting import format_montant
from finances.models import Cotisation
from membership.models import Adhesion, Membre
from organisation.models import Evenement
from territoires.models import Province, SectionLocale


def _json_safe(value):
    """Sérialise les types non JSON (Decimal) pour Chart.js."""
    if isinstance(value, Decimal):
        return float(value)
    return value


def home(request):
    stats = {
        "membres": Membre.objects.filter(actif=True).count(),
        "provinces": Province.objects.filter(actif=True).count(),
        "adhesions_attente": Adhesion.objects.filter(
            statut=Adhesion.Statut.EN_ATTENTE
        ).count(),
    }
    now = timezone.now()
    base = Evenement.objects.filter(actif=True).select_related(
        "province", "section_locale"
    )
    upcoming = list(base.filter(date__gte=now).order_by("date")[:10])
    remaining = 10 - len(upcoming)
    past = (
        list(base.filter(date__lt=now).order_by("-date")[:remaining])
        if remaining
        else []
    )
    campagnes = upcoming + past
    return render(
        request,
        "core/home.html",
        {"stats": stats, "campagnes": campagnes, "now": now},
    )


def _sections_disponibles(user):
    """Sections que l'utilisateur peut sélectionner sur le dashboard."""
    qs = SectionLocale.objects.filter(actif=True).select_related(
        "commune__ville__province"
    )
    if user.is_admin_national:
        return qs.order_by("commune__ville__province__nom", "nom")
    if user.is_provincial and user.province_id:
        return qs.filter(commune__ville__province_id=user.province_id).order_by("nom")
    if user.is_local and user.section_locale_id:
        return qs.filter(pk=user.section_locale_id)
    return SectionLocale.objects.none()


def _resolve_dashboard_scope(request):
    """
    Détermine le périmètre du dashboard :
    - local → toujours sa section
    - provincial → province, ou une section via ?section=
    - admin → national, ou une section via ?section=
    """
    user = request.user
    sections_qs = _sections_disponibles(user)
    section_id = request.GET.get("section", "").strip()
    section = None

    if user.is_local:
        section = user.section_locale
        return {
            "level": "section",
            "label": f"Section {section.nom}" if section else "Section non assignée",
            "section": section,
            "province": section.province if section else None,
            "sections": sections_qs,
            "can_filter_section": False,
        }

    if section_id:
        section = sections_qs.filter(pk=section_id).first()
        if section:
            return {
                "level": "section",
                "label": f"Section {section.nom}",
                "section": section,
                "province": section.province,
                "sections": sections_qs,
                "can_filter_section": True,
            }

    if user.is_provincial:
        province = user.province
        return {
            "level": "province",
            "label": f"Province {province.nom}" if province else "Province non assignée",
            "section": None,
            "province": province,
            "sections": sections_qs,
            "can_filter_section": True,
        }

    return {
        "level": "national",
        "label": "Niveau national",
        "section": None,
        "province": None,
        "sections": sections_qs,
        "can_filter_section": True,
    }


def _apply_scope_to_qs(adhesions, membres, scope):
    """Restreint les querysets au niveau section si demandé (admin/provincial)."""
    section = scope.get("section")
    if section:
        adhesions = adhesions.filter(section_locale_id=section.pk)
        membres = membres.filter(adhesion__section_locale_id=section.pk)
    return adhesions, membres


def _scope_evenements(user, scope):
    qs = Evenement.objects.filter(date__gte=timezone.now(), actif=True)
    if scope["level"] == "section" and scope["section"]:
        return qs.filter(
            Q(section_locale_id=scope["section"].pk)
            | Q(section_locale__isnull=True, province_id=scope["section"].province.pk)
        ).order_by("date")[:5]
    if scope["level"] == "province" and scope["province"]:
        return qs.filter(
            Q(province_id=scope["province"].pk)
            | Q(section_locale__commune__ville__province_id=scope["province"].pk)
        ).order_by("date")[:5]
    if user.is_admin_national:
        return qs.order_by("date")[:5]
    return qs.none()


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def dashboard(request):
    user = request.user
    scope = _resolve_dashboard_scope(request)

    adhesions = scope_adhesions(Adhesion.objects.all(), user)
    membres = scope_membres(Membre.objects.filter(actif=True), user)
    adhesions, membres = _apply_scope_to_qs(adhesions, membres, scope)

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
    taux_activite = (
        round((actifs_recents / total_membres) * 100, 1) if total_membres else 0
    )

    cotisations = Cotisation.objects.filter(membre__in=membres)
    totaux_finances = [
        format_montant(row["total"] or 0, row["devise"] or "CDF")
        for row in cotisations.values("devise")
        .annotate(total=Sum("montant"))
        .order_by("devise")
    ]
    finances_par_type = list(
        cotisations.values("type")
        .annotate(total=Sum("montant"), n=Count("id"))
        .order_by("-total")
    )

    adhesions_attente = adhesions.filter(statut=Adhesion.Statut.EN_ATTENTE).count()
    adhesions_validees = adhesions.filter(statut=Adhesion.Statut.VALIDE).count()
    adhesions_rejetees = adhesions.filter(statut=Adhesion.Statut.REJETE).count()

    # Graphique géographique selon le niveau
    if scope["level"] == "national":
        geo_rows = list(
            membres.values("adhesion__section_locale__commune__ville__province__nom")
            .annotate(total=Count("id"))
            .order_by("-total")[:12]
        )
        geo_title = "Membres par province"
        chart_geo = {
            "labels": [
                r["adhesion__section_locale__commune__ville__province__nom"] or "—"
                for r in geo_rows
            ],
            "data": [r["total"] for r in geo_rows],
        }
    elif scope["level"] == "province":
        geo_rows = list(
            membres.values("adhesion__section_locale__nom")
            .annotate(total=Count("id"))
            .order_by("-total")[:12]
        )
        geo_title = "Membres par section"
        chart_geo = {
            "labels": [r["adhesion__section_locale__nom"] or "—" for r in geo_rows],
            "data": [r["total"] for r in geo_rows],
        }
    else:
        geo_title = "Répartition dans la section"
        chart_geo = {
            "labels": ["Membres actifs", "Nouveaux (90 j)"],
            "data": [total_membres, actifs_recents],
        }

    chart_croissance = {
        "labels": [
            row["mois"].strftime("%b %Y") if row["mois"] else "—" for row in croissance
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
        "scope": scope,
        "geo_title": geo_title,
        "total_membres": total_membres,
        "adhesions_attente": adhesions_attente,
        "adhesions_validees": adhesions_validees,
        "adhesions_rejetees": adhesions_rejetees,
        "taux_activite": taux_activite,
        "total_finances": totaux_finances,
        "evenements_a_venir": _scope_evenements(user, scope),
        "dernieres_adhesions": adhesions.order_by("-date_creation")[:8],
        "derniers_membres": membres.select_related(
            "adhesion__section_locale"
        ).order_by("-date_activation")[:8],
        "chart_geo": chart_geo,
        "chart_croissance": chart_croissance,
        "chart_statuts": chart_statuts,
        "chart_finances": chart_finances,
        "show_adhesions_panel": user.is_admin_national and scope["level"] != "section",
    }
    return render(request, "core/dashboard.html", context)
