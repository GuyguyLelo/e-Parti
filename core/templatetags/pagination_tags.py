"""Tags de pagination."""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def page_url(context, page_number):
    """Conserve les filtres GET en changeant uniquement ?page=."""
    request = context.get("request")
    if request is None:
        return f"?page={page_number}"
    params = request.GET.copy()
    params["page"] = str(page_number)
    return f"?{params.urlencode()}"


@register.simple_tag
def pagination_window(page_obj, neighbors=2):
    """Numéros de page à afficher (avec None pour les ellipses)."""
    current = page_obj.number
    last = page_obj.paginator.num_pages
    if last <= 1:
        return []

    pages = set(range(max(1, current - neighbors), min(last, current + neighbors) + 1))
    pages.add(1)
    pages.add(last)

    result = []
    prev = None
    for num in sorted(pages):
        if prev is not None and num - prev > 1:
            result.append(None)
        result.append(num)
        prev = num
    return result
