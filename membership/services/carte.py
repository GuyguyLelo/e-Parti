"""
Génération carte de membre — PVC CR80 paysage (85.6 × 54 mm).
Tout le texte est horizontal (aucune rotation).
"""
from __future__ import annotations

import io
import re
import unicodedata
from datetime import date, timedelta
from pathlib import Path

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from reportlab.lib.units import mm as rl_mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


CARD_WIDTH_MM = 85.6
CARD_HEIGHT_MM = 54.0
CARD_W = 1011
CARD_H = 638

BRAND_BLUE = (48, 162, 222)
BRAND_BLUE_DARK = (14, 95, 140)
BRAND_CYAN = (80, 190, 230)
BRAND_YELLOW = (240, 215, 77)
BRAND_RED = (211, 33, 37)
BRAND_INK = (20, 28, 36)
BRAND_MUTED = (70, 82, 94)


def _slugify_filename(text: str) -> str:
    """Nom de fichier sûr (sans accents ni caractères spéciaux)."""
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return text.upper() or "MEMBRE"


def _carte_basename(membre) -> str:
    """Ex. CARTE_KABILA_JOSEPH_000001"""
    nom = _slugify_filename(membre.nom_complet)
    numero = membre.numero_membre or str(membre.pk).zfill(6)
    return f"CARTE_{nom}_{numero}"


def _party_cfg():
    return {
        "name": getattr(settings, "PARTY_SHORT_NAME", "E.C.C.O."),
        "full_name": getattr(
            settings, "PARTY_FULL_NAME", "ENSEMBLE, CHANGEONS LE CONGO"
        ),
        "subtitle": getattr(settings, "PARTY_SUBTITLE", "Parti Politique"),
        "motto": getattr(
            settings, "PARTY_MOTTO", "« ENSEMBLE - CHANGEONS - LE CONGO »"
        ),
        "president": getattr(
            settings, "PARTY_PRESIDENT", "Président National"
        ),
        "president_name": getattr(
            settings, "PARTY_PRESIDENT_NAME", "Adam BOMBOLE INTOLE"
        ),
        "qualite": getattr(settings, "PARTY_MEMBER_QUALITY", "MEMBRE EFFECTIF"),
    }


def _logo_path() -> Path | None:
    for p in (
        Path(settings.BASE_DIR) / "static" / "img" / "logo.png",
        Path(settings.BASE_DIR) / "static" / "img" / "logo-Ensemble.png",
    ):
        if p.exists():
            return p
    return None


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    names = (
        (["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"] if bold else [])
        + ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "calibri.ttf"]
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _load_logo(size: int) -> Image.Image:
    path = _logo_path()
    if path:
        logo = Image.open(path).convert("RGBA")
    else:
        logo = Image.new("RGBA", (size, size), (*BRAND_BLUE_DARK, 255))
        d = ImageDraw.Draw(logo)
        d.ellipse((8, 8, size - 8, size - 8), outline=(*BRAND_YELLOW, 255), width=4)
    return logo.resize((size, size), Image.Resampling.LANCZOS)


def _paste_rgba(base: Image.Image, overlay: Image.Image, xy: tuple[int, int]):
    base.paste(overlay, xy, overlay if overlay.mode == "RGBA" else None)


def _wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    words = (text or "").split()
    if not words:
        return [""]
    lines, current = [], words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _fit_text(draw, text: str, font, max_width: int) -> str:
    """Tronque avec ellipse si le texte dépasse la largeur."""
    text = (text or "").strip()
    if not text:
        return "—"
    if draw.textlength(text, font=font) <= max_width:
        return text
    ellipsis = "…"
    while text and draw.textlength(text + ellipsis, font=font) > max_width:
        text = text[:-1]
    return (text + ellipsis) if text else ellipsis


def _draw_kv(
    draw,
    x: int,
    y: int,
    label: str,
    value: str,
    max_w: int,
    label_col_w: int,
    *,
    label_size: int = 28,
    value_size: int = 28,
    row_h: int = 36,
) -> int:
    """Libellé et valeur alignés sur deux colonnes fixes."""
    font_label = _font(label_size, bold=True)
    font_value = _font(value_size, bold=True)
    label_txt = f"{label} :"
    # Alignement vertical : libellé et valeur sur la même ligne de base
    baseline = y + max(0, (row_h - value_size) // 2)
    draw.text((x, baseline + 1), label_txt, fill=BRAND_BLUE_DARK, font=font_label)
    value_x = x + label_col_w
    value_w = max_w - label_col_w
    value_txt = _fit_text(draw, (value or "—").upper(), font_value, value_w)
    draw.text((value_x, baseline), value_txt, fill=BRAND_INK, font=font_value)
    return y + row_h


def _label_col_width(draw, labels: list[str], label_size: int = 28) -> int:
    """Largeur de colonne libellés = plus long libellé + marge."""
    font_label = _font(label_size, bold=True)
    widest = max(int(draw.textlength(f"{label} :", font=font_label)) for label in labels)
    return widest + 16


def _header_gradient(width: int, height: int) -> Image.Image:
    img = Image.new("RGB", (width, height))
    px = img.load()
    for x in range(width):
        t = x / max(width - 1, 1)
        r = int(BRAND_BLUE_DARK[0] * (1 - t) + BRAND_CYAN[0] * t)
        g = int(BRAND_BLUE_DARK[1] * (1 - t) + BRAND_CYAN[1] * t)
        b = int(BRAND_BLUE_DARK[2] * (1 - t) + BRAND_CYAN[2] * t)
        for y in range(height):
            px[x, y] = (r, g, b)
    return img


def generer_numero_carte(membre) -> str:
    year = timezone.now().year
    num = membre.adhesion.numero_membre or str(membre.pk).zfill(6)
    suffix = num.split("-")[-1] if "-" in num else num
    try:
        suffix = f"{int(suffix):06d}"
    except ValueError:
        suffix = str(membre.pk).zfill(6)
    return f"CARD-{year}-{suffix}"


def generate_qr_code(membre, verification_url: str) -> ContentFile:
    payload = (
        f"E.C.C.O.\n"
        f"Nom: {membre.nom_complet}\n"
        f"N°: {membre.numero_membre}\n"
        f"Vérifier: {verification_url}"
    )
    qr = qrcode.QRCode(version=1, box_size=6, border=1)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color=BRAND_BLUE_DARK, back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return ContentFile(buffer.read(), name=f"qr_{_carte_basename(membre)}.png")


def _zone_courte(adhesion) -> str:
    section = adhesion.section_locale
    return f"{section.nom} · {section.province.nom}"


def _build_card_image(membre, qr_image: Image.Image) -> Image.Image:
    """Recto — identité du membre."""
    return _build_card_recto(membre)


def _build_card_recto(membre) -> Image.Image:
    """Carte paysage CR80 — face recto (données membre)."""
    cfg = _party_cfg()
    adhesion = membre.adhesion
    carte = getattr(membre, "carte", None)
    emission = carte.date_emission if carte else date.today()

    card = Image.new("RGB", (CARD_W, CARD_H), (252, 253, 255))
    draw = ImageDraw.Draw(card)

    watermark = _load_logo(240)
    watermark = ImageEnhance.Brightness(watermark).enhance(1.4)
    watermark.putalpha(20)
    _paste_rgba(card, watermark, (400, 220))

    # —— En-tête ——
    header_h = 88
    card.paste(_header_gradient(CARD_W, header_h), (0, 0))
    draw.rectangle((0, header_h, CARD_W, header_h + 4), fill=BRAND_YELLOW)
    draw.rectangle((0, header_h + 4, CARD_W, header_h + 7), fill=BRAND_RED)

    logo_size = 66
    draw.ellipse((12, 9, 12 + 74, 9 + 74), outline=BRAND_YELLOW, width=3)
    draw.ellipse((16, 13, 16 + 66, 13 + 66), outline=BRAND_RED, width=2)
    _paste_rgba(card, _load_logo(logo_size), (20, 17))

    draw.text((100, 10), cfg["name"], fill=BRAND_YELLOW, font=_font(26, bold=True))
    draw.text(
        (100, 40),
        _fit_text(draw, cfg["full_name"].upper(), _font(22, bold=True), CARD_W - 130),
        fill=(255, 255, 255),
        font=_font(22, bold=True),
    )
    draw.text(
        (100, 66),
        _fit_text(
            draw,
            f'{cfg["subtitle"]}  ·  {cfg["motto"]}',
            _font(16),
            CARD_W - 130,
        ),
        fill=(220, 238, 250),
        font=_font(16),
    )

    # —— Zone données + photo ——
    margin = 20
    photo_w, photo_h = 210, 255
    photo_x = CARD_W - photo_w - 48
    content_x = margin
    content_w = photo_x - content_x - 18

    foot_top = CARD_H - 105
    zone_top = header_h + 10
    zone_bottom = foot_top - 10
    zone_h = zone_bottom - zone_top

    # Prépare nom + champs pour calculer la hauteur du bloc et le centrer
    nom_complet = f"{adhesion.nom} {adhesion.post_nom} {adhesion.prenom}".strip()
    font_name = _font(34, bold=True)
    name_lines = _wrap_text(draw, nom_complet.upper(), font_name, content_w)[:2]
    name_block_h = 36 * len(name_lines) + 24

    sexe = adhesion.get_sexe_display() if hasattr(adhesion, "get_sexe_display") else adhesion.sexe
    fields = [
        ("Sexe", sexe),
        ("Fédération", _zone_courte(adhesion)),
        ("Qualité", cfg["qualite"]),
        ("Adresse", adhesion.adresse or "—"),
    ]
    label_size, value_size, row_h = 28, 28, 46
    fields_h = row_h * len(fields)
    content_block_h = name_block_h + fields_h

    # Centre verticalement le bloc infos (et aligne la photo)
    y = zone_top + max(0, (zone_h - content_block_h) // 2)
    photo_y = zone_top + max(0, (zone_h - photo_h) // 2)

    draw.rounded_rectangle(
        (photo_x - 3, photo_y - 3, photo_x + photo_w + 3, photo_y + photo_h + 3),
        radius=6,
        outline=BRAND_BLUE,
        width=3,
    )
    if adhesion.photo1:
        try:
            photo = Image.open(adhesion.photo1.path).convert("RGB")
            photo = photo.resize((photo_w, photo_h), Image.Resampling.LANCZOS)
            card.paste(photo, (photo_x, photo_y))
        except Exception:
            draw.rectangle(
                (photo_x, photo_y, photo_x + photo_w, photo_y + photo_h),
                fill=(226, 234, 240),
            )
            draw.text(
                (photo_x + 48, photo_y + 95),
                "PHOTO",
                fill=BRAND_MUTED,
                font=_font(22, bold=True),
            )
    else:
        draw.rectangle(
            (photo_x, photo_y, photo_x + photo_w, photo_y + photo_h),
            fill=(226, 234, 240),
        )
        draw.text(
            (photo_x + 48, photo_y + 95),
            "PHOTO",
            fill=BRAND_MUTED,
            font=_font(22, bold=True),
        )

    for i, line in enumerate(name_lines):
        draw.text((content_x, y + i * 36), line, fill=BRAND_BLUE_DARK, font=font_name)
    y += name_block_h

    label_col_w = _label_col_width(draw, [f[0] for f in fields], label_size=label_size)

    guide_x = content_x + label_col_w - 8
    draw.line(
        (guide_x, y - 4, guide_x, y + fields_h - 4),
        fill=(210, 226, 236),
        width=1,
    )

    for label, value in fields:
        y = _draw_kv(
            draw,
            content_x,
            y,
            label,
            value,
            content_w,
            label_col_w,
            label_size=label_size,
            value_size=value_size,
            row_h=row_h,
        )

    draw.line((margin, foot_top, CARD_W - margin, foot_top), fill=(200, 220, 232), width=2)

    sig_x = margin
    draw.text((sig_x, foot_top + 2), cfg["president"], fill=BRAND_MUTED, font=_font(18, bold=True))
    draw.text(
        (sig_x, foot_top + 24),
        cfg["president_name"],
        fill=BRAND_BLUE_DARK,
        font=_font(20, bold=True),
    )
    # Espace libre pour signature manuscrite
    draw.line((sig_x + 2, CARD_H - 28, sig_x + 220, CARD_H - 28), fill=BRAND_BLUE_DARK, width=2)

    lieu = adhesion.section_locale.commune.ville.nom
    delivrance = f"Délivré à {lieu.upper()} — {emission.strftime('%d/%m/%Y')}"
    font_del = _font(15)
    del_w = int(draw.textlength(delivrance, font=font_del))
    draw.text(
        (max(margin, CARD_W - margin - del_w), foot_top + 24),
        delivrance,
        fill=BRAND_MUTED,
        font=font_del,
    )

    draw.rectangle((1, 1, CARD_W - 2, CARD_H - 2), outline=BRAND_BLUE, width=2)
    return card


def _build_card_verso(membre, qr_image: Image.Image) -> Image.Image:
    """Carte paysage CR80 — face verso (titre, matricule, QR)."""

    card = Image.new("RGB", (CARD_W, CARD_H), (255, 255, 255))
    draw = ImageDraw.Draw(card)
    matricule = membre.numero_membre or f"{membre.pk:06d}"

    # Fond dégradé léger
    card.paste(_header_gradient(CARD_W, CARD_H), (0, 0))
    overlay = Image.new("RGBA", (CARD_W, CARD_H), (255, 255, 255, 210))
    card = Image.alpha_composite(card.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(card)

    # Bandes couleurs
    draw.rectangle((0, 0, CARD_W, 10), fill=BRAND_BLUE_DARK)
    draw.rectangle((0, 10, CARD_W, 16), fill=BRAND_YELLOW)
    draw.rectangle((0, 16, CARD_W, 22), fill=BRAND_RED)
    draw.rectangle((0, CARD_H - 22, CARD_W, CARD_H - 16), fill=BRAND_RED)
    draw.rectangle((0, CARD_H - 16, CARD_W, CARD_H - 10), fill=BRAND_YELLOW)
    draw.rectangle((0, CARD_H - 10, CARD_W, CARD_H), fill=BRAND_BLUE_DARK)

    # Titre au-dessus du logo
    titre = "CARTE DE MEMBRE"
    font_titre = _font(46, bold=True)
    draw.text(
        ((CARD_W - int(draw.textlength(titre, font=font_titre))) // 2, 34),
        titre,
        fill=BRAND_BLUE_DARK,
        font=font_titre,
    )

    # Matricule sous le titre
    badge_txt = f"N° {matricule}"
    font_badge = _font(28, bold=True)
    badge_w = int(draw.textlength(badge_txt, font=font_badge)) + 28
    badge_x = (CARD_W - badge_w) // 2
    badge_y = 88
    draw.rounded_rectangle(
        (badge_x, badge_y, badge_x + badge_w, badge_y + 40),
        radius=10,
        fill=BRAND_BLUE_DARK,
    )
    draw.text(
        (badge_x + 14, badge_y + 5),
        badge_txt,
        fill=(255, 255, 255),
        font=font_badge,
    )

    logo = _load_logo(130)
    _paste_rgba(card, logo, ((CARD_W - 130) // 2, 148))

    # Bloc QR de vérification
    box_y = 310
    draw.rounded_rectangle(
        (80, box_y, CARD_W - 80, box_y + 160),
        radius=12,
        fill=(245, 250, 253),
        outline=BRAND_BLUE,
        width=2,
    )

    qr_size = 110
    qr_x = (CARD_W - qr_size) // 2 - 160
    card.paste(
        qr_image.convert("RGB").resize((qr_size, qr_size)),
        (qr_x, box_y + 25),
    )

    text_x = qr_x + qr_size + 28
    draw.text(
        (text_x, box_y + 42),
        "VÉRIFICATION OFFICIELLE",
        fill=BRAND_BLUE_DARK,
        font=_font(22, bold=True),
    )
    draw.text(
        (text_x, box_y + 76),
        "Scannez le code QR pour",
        fill=BRAND_INK,
        font=_font(18),
    )
    draw.text(
        (text_x, box_y + 104),
        "authentifier cette carte.",
        fill=BRAND_INK,
        font=_font(18),
    )

    # Mentions légales
    mentions = [
        "Cette carte est personnelle et non cessible.",
        "Elle reste la propriété du parti et doit être présentée sur demande.",
        "En cas de perte, contactez votre section locale.",
    ]
    my = box_y + 178
    font_m = _font(15)
    for line in mentions:
        text = _fit_text(draw, line, font_m, CARD_W - 80)
        draw.text(
            ((CARD_W - int(draw.textlength(text, font=font_m))) // 2, my),
            text,
            fill=BRAND_MUTED,
            font=font_m,
        )
        my += 22

    draw.rectangle((1, 1, CARD_W - 2, CARD_H - 2), outline=BRAND_BLUE, width=2)
    return card


def generate_card_pdf(
    membre,
    recto: Image.Image,
    verso: Image.Image | None = None,
) -> ContentFile:
    """PDF CR80 recto-verso (2 pages)."""
    buffer = io.BytesIO()
    page = (CARD_WIDTH_MM * rl_mm, CARD_HEIGHT_MM * rl_mm)
    c = canvas.Canvas(buffer, pagesize=page)
    width, height = page

    for face in (recto, verso):
        if face is None:
            continue
        img_buf = io.BytesIO()
        face.save(img_buf, format="PNG", dpi=(300, 300))
        img_buf.seek(0)
        c.drawImage(ImageReader(img_buf), 0, 0, width=width, height=height)
        c.showPage()

    c.save()
    buffer.seek(0)
    return ContentFile(
        buffer.read(),
        name=f"{_carte_basename(membre)}.pdf",
    )


def _save_preview_png(
    recto: Image.Image,
    membre,
    verso: Image.Image | None = None,
) -> ContentFile:
    """Aperçu web : recto seul, ou recto + verso empilés."""
    if verso is None:
        preview = recto
    else:
        gap = 24
        label_h = 36
        preview = Image.new(
            "RGB",
            (CARD_W, CARD_H * 2 + gap + label_h * 2),
            (236, 242, 246),
        )
        draw = ImageDraw.Draw(preview)
        font_l = _font(20, bold=True)
        draw.text((12, 8), "RECTO", fill=BRAND_BLUE_DARK, font=font_l)
        preview.paste(recto, (0, label_h))
        draw.text((12, label_h + CARD_H + gap - 28), "VERSO", fill=BRAND_BLUE_DARK, font=font_l)
        preview.paste(verso, (0, label_h + CARD_H + gap))

    buf = io.BytesIO()
    preview.save(buf, format="PNG", dpi=(300, 300))
    buf.seek(0)
    return ContentFile(buf.read(), name=f"{_carte_basename(membre)}.png")


@transaction.atomic
def generate_membership_card(membre):
    from membership.models import CarteMembre

    years = getattr(settings, "MEMBERSHIP_CARD_VALIDITY_YEARS", 2)
    today = date.today()
    expiration = today + timedelta(days=365 * years)
    site = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip("/")
    verification_url = f"{site}/adhesions/verifier/{membre.numero_membre}/"

    carte, created = CarteMembre.objects.select_for_update().get_or_create(
        membre=membre,
        defaults={
            "numero_carte": generer_numero_carte(membre),
            "date_emission": today,
            "date_expiration": expiration,
            "actif": True,
        },
    )
    if not created:
        carte.date_emission = today
        carte.date_expiration = expiration
        carte.actif = True
        if not carte.numero_carte:
            carte.numero_carte = generer_numero_carte(membre)

    qr_file = generate_qr_code(membre, verification_url)
    carte.qr_code.save(qr_file.name, qr_file, save=False)
    carte.save()

    qr_img = Image.open(carte.qr_code.path)
    recto = _build_card_recto(membre)
    verso = _build_card_verso(membre, qr_img)

    preview = _save_preview_png(recto, membre, verso=verso)
    if hasattr(carte, "image_carte"):
        carte.image_carte.save(preview.name, preview, save=False)

    carte.fichier_pdf.save(
        f"{_carte_basename(membre)}.pdf",
        generate_card_pdf(membre, recto, verso),
        save=False,
    )
    carte.save()
    return carte
