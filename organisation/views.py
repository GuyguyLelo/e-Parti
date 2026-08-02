"""Vues organisation : événements et affectations."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from core.pagination import paginate
from core.permissions import role_required
from membership.forms import EvenementForm
from organisation.models import AffectationPolitique, Evenement


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def evenement_list(request):
    evenements = Evenement.objects.select_related("organisateur", "province").order_by(
        "-date"
    )
    page = paginate(request, evenements)
    return render(
        request,
        "organisation/evenement_list.html",
        {"evenements": page, "page_obj": page},
    )


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def evenement_create(request):
    if request.method == "POST":
        form = EvenementForm(request.POST)
        if form.is_valid():
            ev = form.save(commit=False)
            ev.organisateur = request.user
            ev.save()
            messages.success(request, "Campagne enregistrée.")
            return redirect("organisation:evenement_list")
    else:
        form = EvenementForm(initial={"actif": True})
    return render(
        request,
        "organisation/evenement_form.html",
        {"form": form, "is_edit": False, "title": "Créer une campagne"},
    )


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def evenement_edit(request, pk):
    evenement = get_object_or_404(
        Evenement.objects.select_related("province", "section_locale"),
        pk=pk,
    )
    if request.method == "POST":
        form = EvenementForm(request.POST, instance=evenement)
        if form.is_valid():
            form.save()
            messages.success(request, "Campagne mise à jour.")
            return redirect("organisation:evenement_list")
    else:
        form = EvenementForm(instance=evenement)
    return render(
        request,
        "organisation/evenement_form.html",
        {
            "form": form,
            "is_edit": True,
            "title": f"Modifier — {evenement.titre}",
            "evenement": evenement,
        },
    )


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL")
def affectation_list(request):
    affectations = AffectationPolitique.objects.select_related(
        "membre__adhesion", "province", "commune", "section_locale"
    ).filter(actif=True)
    page = paginate(request, affectations)
    return render(
        request,
        "organisation/affectation_list.html",
        {"affectations": page, "page_obj": page},
    )
