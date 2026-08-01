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


def scope_adhesions(qs, user):
    """
    Filtre les adhésions selon le rôle :
    - Admin national : tout
    - Provincial : sa province
    - Local : uniquement sa section
    """
    if getattr(user, "is_admin_national", False):
        return qs
    if user.is_provincial:
        if not user.province_id:
            return qs.none()
        return qs.filter(section_locale__commune__ville__province_id=user.province_id)
    if user.is_local:
        if not user.section_locale_id:
            return qs.none()
        return qs.filter(section_locale_id=user.section_locale_id)
    return qs.none()


def scope_membres(qs, user):
    """Filtre les membres selon le rôle (via l'adhésion liée)."""
    if getattr(user, "is_admin_national", False):
        return qs
    if user.is_provincial:
        if not user.province_id:
            return qs.none()
        return qs.filter(
            adhesion__section_locale__commune__ville__province_id=user.province_id
        )
    if user.is_local:
        if not user.section_locale_id:
            return qs.none()
        return qs.filter(adhesion__section_locale_id=user.section_locale_id)
    return qs.none()


def user_can_access_adhesion(user, adhesion) -> bool:
    if getattr(user, "is_admin_national", False):
        return True
    if user.is_provincial:
        if not user.province_id:
            return False
        return (
            adhesion.section_locale.commune.ville.province_id == user.province_id
        )
    if user.is_local:
        if not user.section_locale_id:
            return False
        return adhesion.section_locale_id == user.section_locale_id
    return False


def user_can_access_membre(user, membre) -> bool:
    return user_can_access_adhesion(user, membre.adhesion)
