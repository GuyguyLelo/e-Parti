"""Vues authentification et gestion des utilisateurs."""
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.forms import LoginForm, UserCreateForm, UserUpdateForm
from accounts.models import User
from core.permissions import role_required


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


def logout_view(request):
    logout(request)
    return redirect("core:home")


def _users_queryset(request_user):
    qs = User.objects.select_related("province", "section_locale").order_by(
        "role", "nom", "username"
    )
    if request_user.is_admin_national:
        return qs
    if request_user.is_provincial and request_user.province_id:
        return qs.filter(
            role=User.Role.LOCAL,
            section_locale__commune__ville__province_id=request_user.province_id,
        )
    return qs.none()


def _can_manage_user(request_user, target: User) -> bool:
    if request_user.is_admin_national:
        return True
    if request_user.is_provincial and request_user.province_id:
        return (
            target.role == User.Role.LOCAL
            and target.section_locale_id
            and target.section_locale.province == request_user.province
        )
    return False


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL")
def user_list(request):
    qs = _users_queryset(request.user)
    q = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").strip()
    if q:
        qs = qs.filter(
            Q(username__icontains=q)
            | Q(nom__icontains=q)
            | Q(post_nom__icontains=q)
            | Q(prenom__icontains=q)
            | Q(email__icontains=q)
            | Q(telephone__icontains=q)
        )
    if role:
        qs = qs.filter(role=role)
    return render(
        request,
        "accounts/user_list.html",
        {
            "users": qs[:300],
            "q": q,
            "role": role,
            "roles": User.Role.choices,
        },
    )


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL")
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST, request_user=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Utilisateur « {user.username} » créé.")
            return redirect("accounts:user_list")
    else:
        form = UserCreateForm(request_user=request.user)
    return render(
        request,
        "accounts/user_form.html",
        {"form": form, "title": "Nouvel utilisateur", "is_create": True},
    )


@login_required
@role_required("ADMIN_NATIONAL", "PROVINCIAL")
def user_edit(request, pk):
    user_obj = get_object_or_404(
        User.objects.select_related("province", "section_locale"), pk=pk
    )
    if not _can_manage_user(request.user, user_obj):
        messages.error(request, "Accès non autorisé pour cet utilisateur.")
        return redirect("accounts:user_list")

    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user_obj, request_user=request.user)
        if form.is_valid():
            if user_obj.pk == request.user.pk and not form.cleaned_data.get("is_active"):
                messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
                return redirect("accounts:user_edit", pk=pk)
            form.save()
            messages.success(request, f"Utilisateur « {user_obj.username} » mis à jour.")
            return redirect("accounts:user_list")
    else:
        form = UserUpdateForm(instance=user_obj, request_user=request.user)
    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "title": f"Modifier {user_obj}",
            "is_create": False,
            "edited_user": user_obj,
        },
    )
