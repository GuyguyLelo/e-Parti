"""Vues finances : cotisations, rapports, export Excel."""
from datetime import date
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render

from core.permissions import role_required
from finances.models import Cotisation
from membership.forms import CotisationForm


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def cotisation_list(request):
    qs = Cotisation.objects.select_related("membre__adhesion")
    user = request.user
    if user.is_provincial and user.province_id:
        qs = qs.filter(
            membre__adhesion__section_locale__commune__ville__province=user.province
        )
    elif user.is_local and user.section_locale_id:
        qs = qs.filter(membre__adhesion__section_locale=user.section_locale)

    total = qs.aggregate(s=Sum("montant"))["s"] or 0
    return render(
        request,
        "finances/cotisation_list.html",
        {"cotisations": qs[:200], "total": total},
    )


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def cotisation_create(request):
    if request.method == "POST":
        form = CotisationForm(request.POST)
        if form.is_valid():
            cotisation = form.save(commit=False)
            cotisation.enregistre_par = request.user
            cotisation.save()
            messages.success(request, "Cotisation enregistrée.")
            return redirect("finances:cotisation_list")
    else:
        form = CotisationForm(initial={"date_paiement": date.today()})
    return render(request, "finances/cotisation_form.html", {"form": form})


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL")
def rapport_financier(request):
    qs = Cotisation.objects.all()
    user = request.user
    if user.is_provincial and user.province_id:
        qs = qs.filter(
            membre__adhesion__section_locale__commune__ville__province=user.province
        )

    par_type = qs.values("type").annotate(total=Sum("montant"), n=Count("id"))
    return render(
        request,
        "finances/rapport.html",
        {
            "par_type": par_type,
            "total_global": qs.aggregate(s=Sum("montant"))["s"] or 0,
        },
    )


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL")
def export_excel(request):
    from openpyxl import Workbook

    qs = Cotisation.objects.select_related("membre__adhesion").all()
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
