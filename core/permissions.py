"""Permissions par rôle."""
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
