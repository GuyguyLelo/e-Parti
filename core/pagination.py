"""Pagination commune pour les listes e-Parti."""
from django.core.paginator import Paginator

DEFAULT_PER_PAGE = 25


def paginate(request, queryset, per_page=DEFAULT_PER_PAGE):
    """Retourne la page courante (Django Page) pour un queryset."""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))
