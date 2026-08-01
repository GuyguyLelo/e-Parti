"""Vues finances : cotisations, rapports, export Excel."""
from datetime import date
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render

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

    return render(
        request,
        "finances/cotisation_list.html",
        {
            "cotisations": qs[:200],
            "totaux": _totaux_par_devise(qs),
            "section_locale": getattr(request.user, "section_locale", None),
        },
    )


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def cotisation_create(request):
    if request.method == "POST":
        form = CotisationForm(request.POST, user=request.user)
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

    par_type = (
        qs.values("type", "devise")
        .annotate(total=Sum("montant"), n=Count("id"))
        .order_by("type", "devise")
    )
    return render(
        request,
        "finances/rapport.html",
        {
            "par_type": par_type,
            "totaux": _totaux_par_devise(qs),
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
                c.mode_paiement,
                c.reference,
            ]
        )
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(
        buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="cotisations_eparti.xlsx"'
    return response
