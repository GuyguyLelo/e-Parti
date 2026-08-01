"""Formatage des montants (style fr-FR)."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation


def format_montant(value, devise: str | None = None, decimals: int = 2) -> str:
    """Ex. 1250000.5 → '1 250 000,50' ou '1 250 000,50 CDF'."""
    if value is None or value == "":
        return "—"
    try:
        n = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return str(value)

    q = Decimal("1").scaleb(-decimals)  # 0.01 for decimals=2
    n = n.quantize(q)
    sign = "-" if n < 0 else ""
    n = abs(n)
    raw = f"{n:.{decimals}f}"  # 1234567.50
    entier, frac = raw.split(".")
    groupes = []
    while entier:
        groupes.append(entier[-3:])
        entier = entier[:-3]
    entier_fmt = " ".join(reversed(groupes))
    montant = f"{sign}{entier_fmt},{frac}"
    if devise:
        return f"{montant} {devise}"
    return montant
