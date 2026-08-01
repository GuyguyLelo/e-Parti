from django import template

from finances.formatting import format_montant

register = template.Library()


@register.filter(name="montant")
def montant_filter(value, devise=None):
    """Formate un montant : {{ 12500|montant }} ou {{ m|montant:c.devise }}."""
    return format_montant(value, devise=devise or None)
