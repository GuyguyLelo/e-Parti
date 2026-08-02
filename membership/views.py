"""Vues membership : adhésion, validation, cartes, vérification."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.pagination import paginate
from core.permissions import (
    role_required,
    scope_adhesions,
    scope_membres,
    user_can_access_adhesion,
    user_can_access_membre,
)
from membership.forms import AdhesionForm, MembreUpdateForm, RejetAdhesionForm
from membership.models import Adhesion, CarteMembre, Membre
from membership.services.carte import _carte_basename, generate_membership_card
from membership.services.fiche_adhesion import fiche_basename, generate_fiche_adhesion_pdf


def _deny_scope(request, redirect_name="membership:membre_list"):
    messages.error(
        request,
        "Accès limité aux membres de votre section / province.",
    )
    return redirect(redirect_name)


def adhesion_create(request):
    """Formulaire public d'adhésion."""
    if request.method == "POST":
        form = AdhesionForm(request.POST, request.FILES)
        if form.is_valid():
            adhesion = form.save()
            messages.success(
                request,
                "Votre demande d'adhésion a été enregistrée. "
                "Elle sera examinée par les responsables du parti.",
            )
            return redirect("membership:adhesion_success", pk=adhesion.pk)
    else:
        form = AdhesionForm()
    return render(request, "membership/adhesion_form.html", {"form": form})


def adhesion_success(request, pk):
    adhesion = get_object_or_404(Adhesion, pk=pk)
    return render(request, "membership/adhesion_success.html", {"adhesion": adhesion})


@login_required
@role_required("ADMIN_NATIONAL")
def adhesion_list(request):
    qs = scope_adhesions(
        Adhesion.objects.select_related(
            "section_locale__commune__ville__province", "province_origine"
        ).filter(statut=Adhesion.Statut.EN_ATTENTE),
        request.user,
    )

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(nom__icontains=q)
            | Q(post_nom__icontains=q)
            | Q(prenom__icontains=q)
            | Q(numero_membre__icontains=q)
            | Q(telephone__icontains=q)
        )
    page = paginate(request, qs)
    return render(
        request,
        "membership/adhesion_list.html",
        {
            "adhesions": page,
            "page_obj": page,
            "q": q,
            "section_locale": getattr(request.user, "section_locale", None),
        },
    )


@login_required
@role_required("ADMIN_NATIONAL")
def adhesion_detail(request, pk):
    adhesion = get_object_or_404(
        Adhesion.objects.select_related(
            "section_locale__commune__ville__province", "province_origine"
        ),
        pk=pk,
    )
    if not user_can_access_adhesion(request.user, adhesion):
        return _deny_scope(request, "membership:adhesion_list")
    rejet_form = RejetAdhesionForm()
    return render(
        request,
        "membership/adhesion_detail.html",
        {"adhesion": adhesion, "rejet_form": rejet_form},
    )


@login_required
@role_required("ADMIN_NATIONAL")
@require_POST
def adhesion_valider(request, pk):
    adhesion = get_object_or_404(
        Adhesion.objects.select_related("section_locale__commune__ville__province"),
        pk=pk,
    )
    if not user_can_access_adhesion(request.user, adhesion):
        return _deny_scope(request, "membership:adhesion_list")
    try:
        membre = adhesion.valider(user=request.user)
        messages.success(
            request,
            f"Adhésion validée. Membre {membre.numero_membre} créé et carte générée.",
        )
    except Exception as exc:
        messages.error(request, f"Erreur lors de la validation : {exc}")
    return redirect("membership:adhesion_detail", pk=pk)


@login_required
@role_required("ADMIN_NATIONAL")
@require_POST
def adhesion_rejeter(request, pk):
    adhesion = get_object_or_404(
        Adhesion.objects.select_related("section_locale__commune__ville__province"),
        pk=pk,
    )
    if not user_can_access_adhesion(request.user, adhesion):
        return _deny_scope(request, "membership:adhesion_list")
    form = RejetAdhesionForm(request.POST)
    if form.is_valid():
        adhesion.rejeter(motif=form.cleaned_data["motif"], user=request.user)
        messages.warning(request, "Adhésion rejetée.")
    else:
        messages.error(request, "Motif de rejet requis.")
    return redirect("membership:adhesion_detail", pk=pk)


def adhesion_fiche_pdf(request, pk):
    """Téléchargement PDF — réservé aux adhésions validées."""
    adhesion = get_object_or_404(
        Adhesion.objects.select_related(
            "section_locale__commune__ville__province",
            "province_origine",
            "valide_par",
        ),
        pk=pk,
        statut=Adhesion.Statut.VALIDE,
    )
    pdf_bytes = generate_fiche_adhesion_pdf(adhesion)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="{fiche_basename(adhesion)}.pdf"'
    )
    return response


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def membre_list(request):
    """Liste des membres : un local ne voit que sa section."""
    qs = scope_membres(
        Membre.objects.select_related(
            "adhesion__section_locale__commune__ville__province"
        ).filter(actif=True),
        request.user,
    )

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(adhesion__nom__icontains=q)
            | Q(adhesion__post_nom__icontains=q)
            | Q(adhesion__prenom__icontains=q)
            | Q(adhesion__numero_membre__icontains=q)
        )
    page = paginate(request, qs)
    return render(
        request,
        "membership/membre_list.html",
        {
            "membres": page,
            "page_obj": page,
            "q": q,
            "section_locale": getattr(request.user, "section_locale", None),
        },
    )


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def membre_detail(request, pk):
    """Fiche détail d'un membre avec photo."""
    membre = get_object_or_404(
        Membre.objects.select_related(
            "adhesion__section_locale__commune__ville__province",
            "adhesion__province_origine",
            "carte",
        ),
        pk=pk,
    )
    if not user_can_access_membre(request.user, membre):
        return _deny_scope(request)

    adhesion = membre.adhesion
    carte = getattr(membre, "carte", None)
    return render(
        request,
        "membership/membre_detail.html",
        {
            "membre": membre,
            "adhesion": adhesion,
            "carte": carte,
        },
    )


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def membre_edit(request, pk):
    """Modification d'un membre (données d'adhésion + statut actif)."""
    membre = get_object_or_404(
        Membre.objects.select_related(
            "adhesion__section_locale__commune__ville__province",
            "adhesion__province_origine",
            "carte",
        ),
        pk=pk,
    )
    if not user_can_access_membre(request.user, membre):
        return _deny_scope(request)

    adhesion = membre.adhesion
    before = {
        "nom": adhesion.nom,
        "post_nom": adhesion.post_nom,
        "prenom": adhesion.prenom,
        "date_naissance": adhesion.date_naissance,
        "photo1": adhesion.photo1.name if adhesion.photo1 else "",
    }

    if request.method == "POST":
        form = MembreUpdateForm(
            request.POST, request.FILES, instance=adhesion, membre=membre
        )
        if form.is_valid():
            form.save()
            membre.refresh_from_db()
            adhesion.refresh_from_db()
            after_photo = adhesion.photo1.name if adhesion.photo1 else ""
            changed_for_card = (
                before["nom"] != adhesion.nom
                or before["post_nom"] != adhesion.post_nom
                or before["prenom"] != adhesion.prenom
                or before["date_naissance"] != adhesion.date_naissance
                or before["photo1"] != after_photo
            )
            if changed_for_card and getattr(membre, "carte", None):
                try:
                    generate_membership_card(membre)
                except Exception:
                    messages.warning(
                        request,
                        "Membre mis à jour, mais la carte n'a pas pu être régénérée.",
                    )
                    return redirect("membership:membre_detail", pk=membre.pk)
            messages.success(request, "Fiche membre mise à jour.")
            return redirect("membership:membre_detail", pk=membre.pk)
    else:
        form = MembreUpdateForm(instance=adhesion, membre=membre)

    return render(
        request,
        "membership/membre_form.html",
        {"form": form, "membre": membre, "adhesion": adhesion},
    )


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def carte_detail(request, membre_id):
    membre = get_object_or_404(
        Membre.objects.select_related("adhesion__section_locale"),
        pk=membre_id,
    )
    if not user_can_access_membre(request.user, membre):
        return _deny_scope(request)
    carte = getattr(membre, "carte", None)
    return render(
        request,
        "membership/carte.html",
        {"membre": membre, "carte": carte},
    )


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
@require_POST
def carte_generer(request, membre_id):
    membre = get_object_or_404(
        Membre.objects.select_related("adhesion__section_locale"),
        pk=membre_id,
    )
    if not user_can_access_membre(request.user, membre):
        return _deny_scope(request)
    generate_membership_card(membre)
    messages.success(request, "Carte régénérée avec succès.")
    return redirect("membership:carte_detail", membre_id=membre.pk)


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def carte_telecharger(request, membre_id):
    membre = get_object_or_404(
        Membre.objects.select_related("adhesion__section_locale"),
        pk=membre_id,
    )
    if not user_can_access_membre(request.user, membre):
        return _deny_scope(request)
    carte = getattr(membre, "carte", None)
    if not carte or not carte.fichier_pdf:
        raise Http404("Carte PDF introuvable")
    return FileResponse(
        carte.fichier_pdf.open("rb"),
        as_attachment=True,
        filename=f"{_carte_basename(membre)}.pdf",
    )


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL", "LOCAL")
def impression_batch(request):
    """Impression en lot des cartes (limité au périmètre de l'utilisateur)."""
    membres_qs = scope_membres(Membre.objects.filter(actif=True), request.user)
    ids = request.GET.getlist("ids") or request.POST.getlist("ids")
    cartes = (
        CarteMembre.objects.filter(
            membre_id__in=ids,
            membre__in=membres_qs,
            fichier_pdf__isnull=False,
        )
        .exclude(fichier_pdf="")
        .select_related("membre__adhesion")
    )

    if request.method == "POST" and request.POST.get("action") == "download_zip":
        import zipfile
        from io import BytesIO

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for carte in cartes:
                name = f"{_carte_basename(carte.membre)}.pdf"
                with carte.fichier_pdf.open("rb") as f:
                    zf.writestr(name, f.read())
        buf.seek(0)
        response = HttpResponse(buf.read(), content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="cartes_eparti.zip"'
        return response

    return render(
        request,
        "membership/impression.html",
        {
            "cartes": cartes,
            "membres": membres_qs.select_related(
                "adhesion__section_locale"
            ).order_by("adhesion__nom", "adhesion__post_nom", "adhesion__prenom")[:300],
        },
    )


def verifier_membre(request, numero_membre):
    """Vérification publique via QR code."""
    adhesion = get_object_or_404(
        Adhesion, numero_membre=numero_membre, statut=Adhesion.Statut.VALIDE
    )
    membre = getattr(adhesion, "membre", None)
    carte = getattr(membre, "carte", None) if membre else None
    return render(
        request,
        "membership/verification.html",
        {
            "adhesion": adhesion,
            "membre": membre,
            "carte": carte,
            "valide": bool(
                membre
                and membre.actif
                and carte
                and carte.actif
                and not carte.est_expiree
            ),
        },
    )
