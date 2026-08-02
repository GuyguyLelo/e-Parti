"""Vues finances : cotisations, rapports, export Excel."""
from datetime import date
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render

from core.pagination import paginate
from core.permissions import role_required, scope_cotisations, scope_membres
from finances.formatting import format_montant
from finances.models import Cotisation
from membership.forms import CotisationForm
from membership.models import Membre


def _totaux_par_devise(qs):
    """Liste de montants formatés, un par devise (évite de mélanger CDF/USD/EUR)."""
    rows = (
        qs.values("devise")
        .annotate(total=Sum("montant"))
        .order_by("devise")
    )
    return [
        format_montant(row["total"] or 0, row["devise"] or "CDF")
        for row in rows
    ]


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def cotisation_list(request):
    qs = scope_cotisations(
        Cotisation.objects.select_related(
            "membre__adhesion__section_locale"
        ),
        request.user,
    )

    page = paginate(request, qs)
    return render(
        request,
        "finances/cotisation_list.html",
        {
            "cotisations": page,
            "page_obj": page,
            "totaux": _totaux_par_devise(qs),
            "section_locale": getattr(request.user, "section_locale", None),
        },
    )


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def cotisation_create(request):
    if request.method == "POST":
        form = CotisationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            cotisation = form.save(commit=False)
            cotisation.enregistre_par = request.user
            cotisation.save()
            messages.success(request, "Cotisation enregistrée.")
            return redirect("finances:cotisation_list")
    else:
        form = CotisationForm(
            user=request.user,
            initial={"date_paiement": date.today(), "devise": Cotisation.Devise.CDF},
        )
    return render(request, "finances/cotisation_form.html", {"form": form})


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL")
def rapport_financier(request):
    qs = scope_cotisations(Cotisation.objects.all(), request.user)

    today = date.today()
    mois_param = (request.GET.get("mois") or "").strip()
    try:
        annee, mois = map(int, mois_param.split("-"))
        if not (1 <= mois <= 12 and annee >= 2026):
            raise ValueError
    except (TypeError, ValueError):
        annee, mois = today.year, today.month
        mois_param = f"{annee:04d}-{mois:02d}"

    qs = qs.filter(date_paiement__year=annee, date_paiement__month=mois)

    type_labels = dict(Cotisation.TypeCotisation.choices)
    par_type = [
        {
            **row,
            "type_label": type_labels.get(row["type"], row["type"]),
        }
        for row in qs.values("type", "devise")
        .annotate(total=Sum("montant"), n=Count("id"))
        .order_by("type", "devise")
    ]

    # Options mois : depuis le mois courant, sans les années < 2026
    mois_options = []
    y, m = today.year, today.month
    mois_fr = [
        "",
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre",
    ]
    while y >= 2026:
        val = f"{y:04d}-{m:02d}"
        mois_options.append({"value": val, "label": f"{mois_fr[m]} {y}"})
        m -= 1
        if m == 0:
            m = 12
            y -= 1

    return render(
        request,
        "finances/rapport.html",
        {
            "par_type": par_type,
            "totaux": _totaux_par_devise(qs),
            "mois": mois_param,
            "mois_label": f"{mois_fr[mois]} {annee}",
            "mois_options": mois_options,
        },
    )


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL")
def export_excel(request):
    from openpyxl import Workbook

    qs = scope_cotisations(
        Cotisation.objects.select_related("membre__adhesion"),
        request.user,
    )
    mois_param = (request.GET.get("mois") or "").strip()
    if mois_param:
        try:
            annee, mois = map(int, mois_param.split("-"))
            if 1 <= mois <= 12:
                qs = qs.filter(date_paiement__year=annee, date_paiement__month=mois)
        except (TypeError, ValueError):
            pass

    wb = Workbook()
    ws = wb.active
    ws.title = "Cotisations"
    ws.append(
        ["Date", "Membre", "N° membre", "Type", "Montant", "Devise", "Mode", "Référence"]
    )
    for c in qs:
        ws.append(
            [
                c.date_paiement.isoformat(),
                c.membre.nom_complet,
                c.membre.numero_membre,
                c.get_type_display(),
                float(c.montant),
                c.devise,
                c.get_mode_paiement_display() or c.mode_paiement,
                c.reference,
            ]
        )
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    filename = (
        f"cotisations_eparti_{mois_param.replace('-', '_')}.xlsx"
        if mois_param
        else "cotisations_eparti.xlsx"
    )
    response = HttpResponse(
        buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
