"""Vues organisation : événements et affectations."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.permissions import role_required
from membership.forms import EvenementForm
from organisation.models import AffectationPolitique, Evenement


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def evenement_list(request):
    evenements = Evenement.objects.select_related("organisateur", "province").filter(actif=True)
    return render(request, "organisation/evenement_list.html", {"evenements": evenements[:100]})


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def evenement_create(request):
    if request.method == "POST":
        form = EvenementForm(request.POST)
        if form.is_valid():
            ev = form.save(commit=False)
            ev.organisateur = request.user
            ev.save()
            messages.success(request, "Événement créé.")
            return redirect("organisation:evenement_list")
    else:
        form = EvenementForm()
    return render(request, "organisation/evenement_form.html", {"form": form})


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL")
def affectation_list(request):
    affectations = AffectationPolitique.objects.select_related(
        "membre__adhesion", "province", "commune", "section_locale"
    ).filter(actif=True)
    return render(
        request,
        "organisation/affectation_list.html",
        {"affectations": affectations[:100]},
    )
