"""Permissions par rôle et périmètre territorial."""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def role_required(*roles):
    """Décorateur : accès limité aux rôles listés (ou superuser)."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect("accounts:login")
            if user.is_superuser or getattr(user, "role", None) in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "Accès non autorisé pour votre rôle.")
            return redirect("core:dashboard")

        return _wrapped

    return decorator


def _effective_role(user):
    """
    Rôle territorial effectif.
    Un compte LOCAL/PROVINCIAL reste limité à son périmètre
    même s'il est aussi superuser.
    """
    role = getattr(user, "role", None)
    if role in ("LOCAL", "PROVINCIAL", "ADMIN_NATIONAL"):
        return role
    if getattr(user, "is_superuser", False):
        return "ADMIN_NATIONAL"
    return role


def scope_adhesions(qs, user):
    """
    Filtre les adhésions selon le rôle :
    - Admin national : tout
    - Provincial : sa province
    - Local : uniquement sa section
    """
    role = _effective_role(user)
    if role == "ADMIN_NATIONAL":
        return qs
    if role == "PROVINCIAL":
        if not user.province_id:
            return qs.none()
        return qs.filter(section_locale__commune__ville__province_id=user.province_id)
    if role == "LOCAL":
        if not user.section_locale_id:
            return qs.none()
        return qs.filter(section_locale_id=user.section_locale_id)
    return qs.none()


def scope_membres(qs, user):
    """Filtre les membres selon le rôle (via l'adhésion liée)."""
    role = _effective_role(user)
    if role == "ADMIN_NATIONAL":
        return qs
    if role == "PROVINCIAL":
        if not user.province_id:
            return qs.none()
        return qs.filter(
            adhesion__section_locale__commune__ville__province_id=user.province_id
        )
    if role == "LOCAL":
        if not user.section_locale_id:
            return qs.none()
        return qs.filter(adhesion__section_locale_id=user.section_locale_id)
    return qs.none()


def scope_cotisations(qs, user):
    """Filtre les cotisations : un local ne voit que celles de sa section."""
    role = _effective_role(user)
    if role == "ADMIN_NATIONAL":
        return qs
    if role == "PROVINCIAL":
        if not user.province_id:
            return qs.none()
        return qs.filter(
            membre__adhesion__section_locale__commune__ville__province_id=user.province_id
        )
    if role == "LOCAL":
        if not user.section_locale_id:
            return qs.none()
        return qs.filter(
            membre__adhesion__section_locale_id=user.section_locale_id
        )
    return qs.none()


def user_can_access_adhesion(user, adhesion) -> bool:
    role = _effective_role(user)
    if role == "ADMIN_NATIONAL":
        return True
    if role == "PROVINCIAL":
        if not user.province_id:
            return False
        return (
            adhesion.section_locale.commune.ville.province_id == user.province_id
        )
    if role == "LOCAL":
        if not user.section_locale_id:
            return False
        return adhesion.section_locale_id == user.section_locale_id
    return False


def user_can_access_membre(user, membre) -> bool:
    return user_can_access_adhesion(user, membre.adhesion)
