"""
Génération PDF de la fiche d'adhésion officielle E.C.C.O.
Mise en page inspirée du formulaire papier « FICHE ADHESION ENSEMBLE ».
"""
from __future__ import annotations

import io
import re
import unicodedata
from pathlib import Path

from django.conf import settings
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


PAGE_W, PAGE_H = A4
MARGIN = 12 * mm
INK = (0.12, 0.14, 0.16)
GRAY = (0.35, 0.38, 0.42)
HEADER_BG = (0.28, 0.30, 0.32)
BOX_BG = (0.88, 0.89, 0.90)
LINE = (0.15, 0.15, 0.15)


def _register_fonts():
    for name, path in (
        ("FicheSans", "arial.ttf"),
        ("FicheSans-Bold", "arialbd.ttf"),
    ):
        try:
            pdfmetrics.getFont(name)
        except KeyError:
            try:
                pdfmetrics.registerFont(TTFont(name, path))
            except Exception:
                return "Helvetica", "Helvetica-Bold"
    return "FicheSans", "FicheSans-Bold"


FONT, FONT_B = _register_fonts()


def _logo_path() -> Path | None:
    for p in (
        Path(settings.BASE_DIR) / "static" / "img" / "logo.png",
        Path(settings.BASE_DIR) / "static" / "img" / "logo-Ensemble.png",
        Path(settings.BASE_DIR) / "img" / "logo-Ensemble.png",
    ):
        if p.exists():
            return p
    return None


def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return text.upper() or "ADHESION"


def fiche_basename(adhesion) -> str:
    nom = _slugify(adhesion.nom_complet)
    ref = adhesion.numero_membre or f"REF{adhesion.pk:06d}"
    return f"FICHE_ADHESION_{nom}_{ref}"


def _set_fill(c: canvas.Canvas, rgb):
    c.setFillColorRGB(*rgb)


def _set_stroke(c: canvas.Canvas, rgb):
    c.setStrokeColorRGB(*rgb)


def _hline(c: canvas.Canvas, x1, y, x2, width=0.6):
    _set_stroke(c, LINE)
    c.setLineWidth(width)
    c.line(x1, y, x2, y)


def _dotted_field(c: canvas.Canvas, x, y, w, label="", value="", label_w=None):
    """Libellé + valeur sur ligne pointillée."""
    c.setFont(FONT_B if label else FONT, 9)
    _set_fill(c, INK)
    if label:
        c.drawString(x, y, label)
        lw = label_w if label_w is not None else c.stringWidth(label, FONT_B, 9) + 4
    else:
        lw = 0
    c.setFont(FONT, 9)
    if value:
        c.drawString(x + lw, y, str(value))
    # pointillés sous la zone valeur
    _set_stroke(c, GRAY)
    c.setDash(1, 2)
    c.setLineWidth(0.5)
    c.line(x + lw, y - 2, x + w, y - 2)
    c.setDash()


def _checkbox(c: canvas.Canvas, x, y, label, checked=False):
    size = 8
    _set_stroke(c, LINE)
    c.setLineWidth(0.8)
    c.rect(x, y - 1, size, size, stroke=1, fill=0)
    if checked:
        c.setFont(FONT_B, 9)
        _set_fill(c, INK)
        c.drawString(x + 1.2, y, "X")
    c.setFont(FONT, 9)
    _set_fill(c, INK)
    c.drawString(x + size + 4, y, label)


def _wrap(c: canvas.Canvas, text, font, size, max_w) -> list[str]:
    words = (text or "").split()
    if not words:
        return [""]
    lines, cur = [], words[0]
    for w in words[1:]:
        trial = f"{cur} {w}"
        if c.stringWidth(trial, font, size) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def _photo_principale_reader(adhesion) -> ImageReader | None:
    """Charge la photo d'identité (photo1) pour le PDF."""
    photo = getattr(adhesion, "photo1", None)
    if not photo:
        return None
    try:
        path = photo.path
    except Exception:
        return None
    if not path or not Path(path).exists():
        return None
    try:
        img = PILImage.open(path).convert("RGB")
        # Recadrage centré type portrait (ratio ~ 4:5)
        tw, th = 400, 500
        src_w, src_h = img.size
        scale = max(tw / src_w, th / src_h)
        nw, nh = int(src_w * scale), int(src_h * scale)
        img = img.resize((nw, nh), PILImage.Resampling.LANCZOS)
        left = (nw - tw) // 2
        top = (nh - th) // 2
        img = img.crop((left, top, left + tw, top + th))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        buf.seek(0)
        return ImageReader(buf)
    except Exception:
        return None


def generate_fiche_adhesion_pdf(adhesion) -> bytes:
    """Retourne le PDF (bytes) de la fiche d'adhésion remplie."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    left = MARGIN
    right = PAGE_W - MARGIN
    width = right - left
    y = PAGE_H - MARGIN

    # Cadre extérieur
    _set_stroke(c, LINE)
    c.setLineWidth(1.2)
    c.rect(MARGIN - 3, MARGIN - 3, PAGE_W - 2 * MARGIN + 6, PAGE_H - 2 * MARGIN + 6)

    # Bandeau titre
    band_h = 10 * mm
    _set_fill(c, HEADER_BG)
    c.rect(left, y - band_h, width, band_h, stroke=0, fill=1)
    c.setFont(FONT_B, 11)
    _set_fill(c, (1, 1, 1))
    ref = adhesion.numero_membre or str(adhesion.pk)
    created = adhesion.date_creation.strftime("%d / %m / %Y") if adhesion.date_creation else ""
    c.drawCentredString(
        PAGE_W / 2,
        y - band_h + 3.2 * mm,
        f"FORMULAIRE D'ADHESION N° {ref}",
    )
    y -= band_h + 4 * mm

    # En-tête : logo + titre + photos
    logo_size = 28 * mm
    logo_path = _logo_path()
    if logo_path:
        try:
            c.drawImage(
                ImageReader(str(logo_path)),
                left,
                y - logo_size,
                width=logo_size,
                height=logo_size,
                mask="auto",
                preserveAspectRatio=True,
                anchor="c",
            )
        except Exception:
            pass

    # Titre centre
    c.setFont(FONT_B, 13)
    _set_fill(c, INK)
    c.drawCentredString(PAGE_W / 2, y - 8 * mm, "ENSEMBLE, CHANGEONS LE CONGO")
    c.setFont(FONT_B, 18)
    c.drawCentredString(PAGE_W / 2, y - 15 * mm, "E. C. C. O")

    # Encadré bienvenue
    welcome = (
        "Vous souhaitez adhérer au Parti E.C.C.O ; nous vous en remercions et nous vous "
        "souhaitons la bienvenue. Complétez le formulaire ci-dessous. Il sera transmis "
        "à votre fédération provinciale qui prendra contact avec vous."
    )
    box_x = left + logo_size + 4 * mm
    box_w = width - logo_size - 32 * mm
    box_h = 18 * mm
    box_y = y - logo_size + 2 * mm
    _set_fill(c, BOX_BG)
    c.roundRect(box_x, box_y, box_w, box_h, 2, stroke=0, fill=1)
    c.setFont(FONT, 7.5)
    _set_fill(c, INK)
    wy = box_y + box_h - 4 * mm
    for line in _wrap(c, welcome, FONT, 7.5, box_w - 6 * mm):
        c.drawString(box_x + 3 * mm, wy, line)
        wy -= 3.2 * mm

    # Cadre photo principale
    photo_w, photo_h = 28 * mm, 35 * mm
    photo_x = right - photo_w
    photo_y = y - photo_h
    _set_stroke(c, LINE)
    c.setLineWidth(1)
    c.setFillColorRGB(1, 1, 1)
    c.rect(photo_x, photo_y, photo_w, photo_h, stroke=1, fill=1)
    photo_reader = _photo_principale_reader(adhesion)
    if photo_reader:
        c.drawImage(
            photo_reader,
            photo_x + 1,
            photo_y + 1,
            width=photo_w - 2,
            height=photo_h - 2,
            preserveAspectRatio=False,
            mask="auto",
        )
    else:
        c.setFont(FONT, 8)
        _set_fill(c, GRAY)
        c.drawCentredString(photo_x + photo_w / 2, photo_y + photo_h / 2 + 2 * mm, "PHOTO")
        c.drawCentredString(photo_x + photo_w / 2, photo_y + photo_h / 2 - 2 * mm, "PRINCIPALE")

    y = min(box_y, photo_y) - 5 * mm
    _hline(c, left, y, right, 0.8)
    y -= 6 * mm

    # 1. Identité
    c.setFont(FONT_B, 9)
    _set_fill(c, INK)
    c.drawString(left, y, "1.")
    _dotted_field(c, left + 8 * mm, y, width - 8 * mm, "Nom (s) :", adhesion.nom)
    y -= 6 * mm
    _dotted_field(c, left + 8 * mm, y, width - 8 * mm, "Post-nom (s) :", adhesion.post_nom)
    y -= 6 * mm
    _dotted_field(c, left + 8 * mm, y, width - 8 * mm, "Prénom (s) :", adhesion.prenom)
    y -= 6 * mm
    dn = adhesion.date_naissance.strftime("%d / %m / %Y") if adhesion.date_naissance else ""
    _dotted_field(
        c,
        left + 8 * mm,
        y,
        width * 0.55,
        "Date de naissance (jour/mois/année) :",
        dn,
    )
    _dotted_field(
        c,
        left + width * 0.58,
        y,
        width * 0.42,
        "Lieu :",
        adhesion.lieu_naissance,
    )
    y -= 5 * mm
    _hline(c, left, y, right, 0.5)
    y -= 6 * mm

    # 2. Sexe
    c.setFont(FONT_B, 9)
    c.drawString(left, y, "2. Sexe")
    _checkbox(c, left + 28 * mm, y, "Masculin", adhesion.sexe == "M")
    _checkbox(c, left + 58 * mm, y, "Féminin", adhesion.sexe == "F")
    y -= 5 * mm
    _hline(c, left, y, right, 0.5)
    y -= 6 * mm

    # 3. État civil
    c.setFont(FONT_B, 9)
    c.drawString(left, y, "3. Etat civil")
    ec = adhesion.etat_civil
    _checkbox(c, left + 35 * mm, y, "Célibataire", ec == "CELIBATAIRE")
    _checkbox(c, left + 68 * mm, y, "Marié (e)", ec == "MARIE")
    _checkbox(c, left + 98 * mm, y, "Divorcé (e)", ec == "DIVORCE")
    _checkbox(c, left + 132 * mm, y, "Veuf/Veuve", ec == "VEUF")
    if ec == "UNION_LIBRE":
        _checkbox(c, left + 165 * mm, y, "Union libre", True)
    y -= 5 * mm
    _hline(c, left, y, right, 0.5)
    y -= 6 * mm

    # 4 + 5 colonnes
    col_gap = 6 * mm
    col_w = (width - col_gap) / 2
    y_top = y

    c.setFont(FONT_B, 9)
    c.drawString(left, y, "4. Adresse actuelle")
    y -= 5.5 * mm
    _dotted_field(c, left, y, col_w, "", adhesion.adresse)
    y -= 5.5 * mm
    _dotted_field(c, left, y, col_w, "", "")
    y -= 5.5 * mm
    _dotted_field(c, left, y, col_w, "N° de Tél. :", adhesion.telephone)
    y -= 5.5 * mm
    _dotted_field(c, left, y, col_w, "E-mail :", adhesion.email or "")
    y_left_end = y

    y = y_top
    rx = left + col_w + col_gap
    c.setFont(FONT_B, 9)
    c.drawString(rx, y, "5. Nationalité :")
    c.setFont(FONT, 9)
    c.drawString(rx + 28 * mm, y, adhesion.nationalite or "")
    y -= 5.5 * mm
    _dotted_field(c, rx, y, col_w, "Province d'origine :", str(adhesion.province_origine))
    y -= 5.5 * mm
    _dotted_field(
        c,
        rx,
        y,
        col_w,
        "Type de pièce d'identité :",
        adhesion.get_type_piece_identite_display(),
    )
    y -= 5.5 * mm
    _dotted_field(c, rx, y, col_w, "N° pièce d'identité :", adhesion.numero_piece_identite)
    y = min(y, y_left_end) - 5 * mm
    _hline(c, left, y, right, 0.5)
    y -= 6 * mm

    # 6 + 7
    c.setFont(FONT_B, 9)
    c.drawString(left, y, "6. Niveau d'études :")
    c.setFont(FONT, 9)
    c.drawString(
        left + 35 * mm,
        y,
        adhesion.get_niveau_etudes_display() if adhesion.niveau_etudes else "",
    )
    y -= 5 * mm
    _hline(c, left, y, right, 0.4)
    y -= 6 * mm
    _dotted_field(c, left, y, width, "7. Profession :", adhesion.profession or "")
    y -= 5 * mm
    _hline(c, left, y, right, 0.5)
    y -= 6 * mm

    # 8. Déjà membre
    c.setFont(FONT_B, 9)
    c.drawString(left, y, "8. Avez-vous déjà été membre d'un parti politique ou d'une association ?")
    y -= 5.5 * mm
    _checkbox(c, left + 8 * mm, y, "Oui", adhesion.deja_membre)
    _checkbox(c, left + 28 * mm, y, "Non", not adhesion.deja_membre)
    y -= 5.5 * mm
    c.setFont(FONT, 8)
    _set_fill(c, INK)
    c.drawString(
        left,
        y,
        "Si oui, précisez le nom de cette organisation et les raisons de votre départ :",
    )
    y -= 5 * mm
    _dotted_field(
        c,
        left,
        y,
        width,
        "",
        adhesion.details_membre if adhesion.deja_membre else "",
    )
    y -= 6 * mm
    c.setFont(FONT_B, 9)
    c.drawString(left, y, "Donnez les raisons qui motivent votre choix d'adhérer au Parti E.C.C.O :")
    y -= 5.5 * mm
    motiv_lines = _wrap(c, adhesion.motivations or "", FONT, 9, width)
    for i in range(3):
        val = motiv_lines[i] if i < len(motiv_lines) else ""
        _dotted_field(c, left, y, width, "", val)
        y -= 5.5 * mm
    y -= 1 * mm
    _hline(c, left, y, right, 0.5)
    y -= 6 * mm

    # 9. Engagement
    c.setFont(FONT_B, 9)
    c.drawString(left, y, "9.")
    engagement = (
        "Je soussigné(e) certifie exacts et sincères les renseignements portés sur ce formulaire "
        "et m'engage à mettre mon savoir-faire, mon savoir-être, mon expérience et mon temps "
        "au service du Parti E.C.C.O."
    )
    c.setFont(FONT, 8.5)
    ey = y
    for line in _wrap(c, engagement, FONT, 8.5, width - 8 * mm):
        c.drawString(left + 6 * mm, ey, line)
        ey -= 3.8 * mm
    y = ey - 3 * mm

    ds = adhesion.date_signature.strftime("%d / %m / %Y") if adhesion.date_signature else ""
    c.setFont(FONT_B, 9)
    c.drawString(left, y, f"Date (jour-mois-année) :  {ds}")
    c.drawString(left + width * 0.55, y, "Signature")
    if adhesion.certifie_exactitude:
        c.setFont(FONT, 8)
        _set_fill(c, GRAY)
        c.drawString(left + width * 0.55, y - 4.5 * mm, "(certifié exact)")
    y -= 8 * mm
    _hline(c, left, y, right, 0.8)
    y -= 2 * mm

    # Section bureau
    band_h = 8 * mm
    _set_fill(c, HEADER_BG)
    c.rect(left, y - band_h, width, band_h, stroke=0, fill=1)
    c.setFont(FONT_B, 10)
    _set_fill(c, (1, 1, 1))
    c.drawCentredString(PAGE_W / 2, y - band_h + 2.5 * mm, "SECTION RESERVEE AU BUREAU")
    y -= band_h + 5 * mm

    c.setFont(FONT_B, 9)
    _set_fill(c, INK)
    c.drawString(left, y, "10. Observations :")
    obs = adhesion.motif_rejet if adhesion.statut == "REJETE" else ""
    y -= 5.5 * mm
    for i in range(2):
        _dotted_field(c, left, y, width, "", obs if i == 0 else "")
        y -= 5.2 * mm

    y -= 2 * mm
    statut = adhesion.get_statut_display()
    c.setFont(FONT_B, 9)
    c.drawString(left, y, f"11. Date (jour-mois-année) :  {created}")
    c.drawString(left + width * 0.45, y, f"Statut : {statut}")
    y -= 8 * mm

    c.setFont(FONT_B, 9)
    c.drawString(left, y, "12. Signature")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
