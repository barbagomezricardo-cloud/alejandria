#!/usr/bin/env python3
"""
Alejandría · Generador de invitaciones
--------------------------------------
Uso:
    python3 studio/generar.py clientes/<slug>/pedido.json

Lee el pedido (y las fotos en clientes/<slug>/fotos/), y produce en i/<slug>/:
    index.html                 invitación web (lista para GitHub Pages)
    img/*.jpg                  fotos optimizadas con recorte que respeta las caras
    preinvitacion.pdf          pre-invitación con botón que abre la invitación
    preinvitacion-estado.png   versión 1080x1920 para estados de WhatsApp / historias (Clásica y Premium)
    entrega.txt                link + mensaje listo para mandar al cliente
"""
import json, os, sys, re, shutil, math, datetime, urllib.parse, colorsys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDIO = ROOT / "studio"
MARCA = {"nombre": "Alejandría", "url": "https://barbagomezricardo-cloud.github.io/alejandria/"}
BASE_URL = "https://barbagomezricardo-cloud.github.io/alejandria/i/"

# ───────────────────────── paquetes ─────────────────────────
PAQUETES = {
    "esencial": dict(historia=0, galeria=0, familia=True, destacada=False, regalos=True, hospedaje=False,
                     fotos_invitados=False, musica=False, estado_png=False, vestimenta=True),
    "clasica":  dict(historia=1, galeria=8, familia=True, destacada=False, regalos=True, hospedaje=True,
                     fotos_invitados=False, musica=True, estado_png=True, vestimenta=True),
    "premium":  dict(historia=3, galeria=16, familia=True, destacada=True, regalos=True, hospedaje=True,
                     fotos_invitados=True, musica=True, estado_png=True, vestimenta=True),
}

# ───────────────────────── textos por tipo de evento ─────────────────────────
EVENTOS = {
    "xv": dict(eyebrow="Mis XV Años", subtitulo="Quince años de historia", historia_eyebrow="Su historia",
               historia_titulo="Quince años de vida", galeria_titulo="Su galería", familia_titulo="Con la bendición de",
               pdf_eyebrow="SUS QUINCE AÑOS", itinerario_frase="Un día que guardaremos para siempre.",
               hashtag_sufijo="XV"),
    "boda": dict(eyebrow="Nos casamos", subtitulo="", historia_eyebrow="Nuestra historia",
                 historia_titulo="Así empezó todo", galeria_titulo="Nuestra galería", familia_titulo="Con la bendición de",
                 pdf_eyebrow="NOS CASAMOS", itinerario_frase="El día en que nuestras historias se vuelven una sola.",
                 hashtag_sufijo="ParaSiempre"),
    "bautizo": dict(eyebrow="Mi Bautizo", subtitulo="Con la bendición de Dios", historia_eyebrow="Mi historia",
                    historia_titulo="Un pequeño gran milagro", galeria_titulo="Mi galería", familia_titulo="Mis papás y padrinos",
                    pdf_eyebrow="MI BAUTIZO", itinerario_frase="Un día lleno de fe y alegría.", hashtag_sufijo="Bautizo"),
    "comunion": dict(eyebrow="Mi Primera Comunión", subtitulo="Recibo a Jesús en mi corazón", historia_eyebrow="Mi historia",
                     historia_titulo="Un paso de fe", galeria_titulo="Mi galería", familia_titulo="Mis papás y padrinos",
                     pdf_eyebrow="MI PRIMERA COMUNIÓN", itinerario_frase="Un día lleno de fe y alegría.", hashtag_sufijo="PrimeraComunion"),
    "baby": dict(eyebrow="Baby Shower", subtitulo="Muy pronto llegará", historia_eyebrow="Nuestra espera",
                 historia_titulo="La dulce espera", galeria_titulo="Nuestra galería", familia_titulo="Te esperan con amor",
                 pdf_eyebrow="BABY SHOWER", itinerario_frase="Celebremos juntos esta dulce espera.", hashtag_sufijo="BabyShower"),
    "cumple": dict(eyebrow="Mi cumpleaños", subtitulo="Celebremos juntos", historia_eyebrow="Mi historia",
                   historia_titulo="Un año más de vida", galeria_titulo="Mi galería", familia_titulo="Con cariño",
                   pdf_eyebrow="MI CUMPLEAÑOS", itinerario_frase="Un día para celebrar la vida.", hashtag_sufijo="Cumple"),
    "otro": dict(eyebrow="Te invitamos", subtitulo="", historia_eyebrow="Nuestra historia", historia_titulo="Un momento especial",
                 galeria_titulo="Galería", familia_titulo="Con cariño", pdf_eyebrow="TE INVITAMOS",
                 itinerario_frase="Un día que guardaremos para siempre.", hashtag_sufijo=""),
}

# ───────────────────────── paletas listas (si el cliente no da colores) ─────────────────────────
PALETAS = {
    "rosa-olivo":     ("#CB8587", "#8E8B63", "Rosa polvoso", "Verde olivo"),
    "barbie-oro":     ("#E0218A", "#B8923F", "Rosa Barbie", "Dorado"),
    "azul-plata":     ("#3E6FA8", "#8C96A3", "Azul rey", "Plata"),
    "vino-oro":       ("#7B2338", "#B08D57", "Vino", "Oro viejo"),
    "lavanda-salvia": ("#9B7DC0", "#86A38A", "Lavanda", "Verde salvia"),
    "esmeralda-oro":  ("#1F7A5C", "#C2A15A", "Esmeralda", "Dorado"),
    "champana-cafe":  ("#C9A878", "#7A5A45", "Champaña", "Café"),
    "rojo-negro":     ("#B3202A", "#3A3A3A", "Rojo", "Negro"),
    "celeste-blanco": ("#6FA8D6", "#A8B4C0", "Azul cielo", "Gris perla"),
    "durazno-terracota": ("#E8A07C", "#A65A3C", "Durazno", "Terracota"),
}

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# ───────────────────────── color ─────────────────────────
def hx(h):
    h = h.strip().lstrip("#"); h = "".join(c * 2 for c in h) if len(h) == 3 else h
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def tohex(rgb): return "#" + "".join(f"{max(0, min(255, round(c * 255))):02X}" for c in rgb)
def lum(rgb):
    f = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    r, g, b = map(f, rgb); return .2126 * r + .7152 * g + .0722 * b
def contrast(a, b):
    x, y = sorted([lum(a), lum(b)], reverse=True); return (x + .05) / (y + .05)
def mix(a, b, t): return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))
def darken_to(rgb, bg, target):
    """Oscurece manteniendo el tono hasta llegar al contraste pedido contra bg."""
    h, l, s = colorsys.rgb_to_hls(*rgb)
    while contrast(colorsys.hls_to_rgb(h, l, s), bg) < target and l > 0.05:
        l -= 0.01
    return colorsys.hls_to_rgb(h, l, s)
def shade(rgb, k):
    h, l, s = colorsys.rgb_to_hls(*rgb); return colorsys.hls_to_rgb(h, max(0, l * (1 - k)), s)

def construir_colores(principal, secundario):
    P, S = hx(principal), hx(secundario)
    cream = hx("#FBF8F3"); white = (1, 1, 1)
    pale = mix(P, cream, .84)
    accent = darken_to(P, pale, 4.6)                   # títulos legibles sobre fondo suave y crema
    sec = darken_to(S, pale, 4.6)
    dark = shade(mix(P, (0.09, 0.07, 0.06), .82), 0)
    return dict(
        accent=tohex(accent), accent_d=tohex(shade(accent, .22)), accent_s=tohex(mix(P, white, .45)),
        sec=tohex(sec), sec_d=tohex(shade(sec, .22)), sec_s=tohex(mix(S, white, .5)),
        pale=tohex(pale), cream=tohex(cream), line=tohex(mix(S, cream, .7)),
        ink="#2E2620", ink_s="#463B32", dark=tohex(dark),
        raw_p=tohex(P), raw_s=tohex(S),
    )

# ───────────────────────── fotos ─────────────────────────
_face = None
def caras(path):
    global _face
    try:
        import cv2
        if _face is None:
            _face = cv2.CascadeClassifier(str(STUDIO / "haar_face.xml"))
        im = cv2.imread(str(path)); h, w = im.shape[:2]; s = 900 / max(h, w)
        g = cv2.cvtColor(cv2.resize(im, None, fx=s, fy=s), cv2.COLOR_BGR2GRAY)
        fs = _face.detectMultiScale(g, 1.1, 6, minSize=(int(28), int(28)))
        return [(x / s / w, y / s / h, fw / s / w, fh / s / h) for x, y, fw, fh in fs], w, h
    except Exception:
        return [], None, None

def posicion(path, manual=None):
    """object-position que mantiene las caras dentro del recorte (prefiere cortar ropa, no cabezas)."""
    if manual: return manual
    fs, w, h = caras(path)
    if not fs: return "center 25%"
    x0 = min(f[0] for f in fs); x1 = max(f[0] + f[2] for f in fs)
    y0 = min(f[1] for f in fs); y1 = max(f[1] + f[3] for f in fs)
    cx = (x0 + x1) / 2; cy = (y0 + y1) / 2
    py = max(0, min(100, round((cy - 0.06) * 100)))
    px = max(0, min(100, round(cx * 100)))
    return f"{px}% {py}%"

def optimizar(src, dst, lado=1600, calidad=82):
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    im.thumbnail((lado, lado), Image.LANCZOS)
    im.save(dst, "JPEG", quality=calidad, optimize=True, progressive=True)
    return im.size

# ───────────────────────── fechas ─────────────────────────
def fecha_textos(iso):
    d = datetime.datetime.fromisoformat(iso)
    larga = f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1].capitalize()}, {d.year}"
    corta = f"{d.day} de {MESES[d.month - 1].capitalize()}, {d.year}"
    pdf = f"{d.day} DE {MESES[d.month - 1].upper()} DE {d.year}"
    return d, larga, corta, pdf

def fecha_simple(iso):
    d = datetime.date.fromisoformat(iso[:10]); return f"{d.day} de {MESES[d.month - 1].capitalize()}, {d.year}"

def solo_digitos(t): return re.sub(r"\D", "", t or "")
def wa(t):
    d = solo_digitos(t)
    if len(d) == 10: d = "52" + d
    return d
def tel_bonito(t):
    d = solo_digitos(t)[-10:]
    return f"{d[:3]} {d[3:6]} {d[6:8]} {d[8:]}" if len(d) == 10 else t
def mapa(link, nombre, ciudad):
    return link or "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(f"{nombre} {ciudad}")

# ───────────────────────── PDF pre-invitación ─────────────────────────
def pdf_preinvitacion(out, foto, pos, c, ev, nombres, fecha_pdf, ciudad, url, secciones):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from PIL import Image
    import io
    F = STUDIO / "fonts"
    for n in ["Playfair-SemiBoldItalic", "Cormorant-Italic", "Cormorant-SemiBold", "Lato-Regular", "Lato-Bold"]:
        try: pdfmetrics.registerFont(TTFont(n, str(F / f"{n}.ttf")))
        except Exception: pass
    W, H = letter; cv = canvas.Canvas(str(out), pagesize=letter)
    cv.setTitle(f"Pre-invitación · {' & '.join(nombres)}")
    cv.setFillColor(HexColor(c["cream"])); cv.rect(0, 0, W, H, fill=1, stroke=0)
    PH = H * (.46 if len(nombres) == 2 else .52)
    im = Image.open(foto).convert("RGB"); iw, ih = im.size; tr = W / PH
    m = re.match(r"(\d+)%\s+(\d+)%", pos or ""); px, py = (int(m.group(1)) / 100, int(m.group(2)) / 100) if m else (.5, .25)
    if iw / ih > tr:
        nw = int(ih * tr); x0 = int((iw - nw) * px); im = im.crop((x0, 0, x0 + nw, ih))
    else:
        nh = int(iw / tr); y0 = int((ih - nh) * py); im = im.crop((0, y0, iw, y0 + nh))
    b = io.BytesIO(); im.save(b, "JPEG", quality=90); b.seek(0)
    cv.drawImage(ImageReader(b), 0, H - PH, width=W, height=PH)
    # esquinas
    cv.setStrokeColor(HexColor(c["sec"])); cv.setLineWidth(1.1); k = 15 * mm
    for x, y, dx, dy in [(10*mm, H-10*mm, 1, -1), (W-10*mm, H-10*mm, -1, -1), (10*mm, 10*mm, 1, 1), (W-10*mm, 10*mm, -1, 1)]:
        cv.line(x, y, x + dx * k, y); cv.line(x, y, x, y + dy * k)
    y = H - PH - 13 * mm
    cv.setFillColor(HexColor(c["sec_d"])); cv.setFont("Lato-Bold", 8.5)
    cv.drawCentredString(W / 2, y, "   ".join(" ".join(w) for w in ev["pdf_eyebrow"].split()))
    y -= 15 * mm
    cv.setFillColor(HexColor(c["accent"]))
    if len(nombres) == 2:
        size = 40 if max(len(n) for n in nombres) < 16 else 32
        cv.setFont("Playfair-SemiBoldItalic", size); cv.drawCentredString(W / 2, y, nombres[0]); y -= 10 * mm
        cv.setFillColor(HexColor(c["sec"])); cv.setFont("Cormorant-Italic", 22); cv.drawCentredString(W / 2, y, "&"); y -= 13 * mm
        cv.setFillColor(HexColor(c["accent"])); cv.setFont("Playfair-SemiBoldItalic", size); cv.drawCentredString(W / 2, y, nombres[1])
    else:
        size = 52 if len(nombres[0]) < 12 else 38
        cv.setFont("Playfair-SemiBoldItalic", size); cv.drawCentredString(W / 2, y, nombres[0])
    y -= 10 * mm
    cv.setStrokeColor(HexColor(c["sec"])); cv.setLineWidth(.7)
    cv.line(W/2 - 30*mm, y, W/2 - 4*mm, y); cv.line(W/2 + 4*mm, y, W/2 + 30*mm, y)
    cv.setFillColor(HexColor(c["sec"])); cv.circle(W / 2, y, 1.6, fill=1, stroke=0)
    y -= 10 * mm
    cv.setFillColor(HexColor(c["ink"])); cv.setFont("Lato-Bold", 13); cv.drawCentredString(W / 2, y, fecha_pdf); y -= 6.5 * mm
    cv.setFillColor(HexColor(c["ink_s"])); cv.setFont("Lato-Regular", 10.5); cv.drawCentredString(W / 2, y, ciudad); y -= 9 * mm
    cv.setFont("Cormorant-Italic", 14)
    cv.drawCentredString(W / 2, y, "Con todo nuestro cariño, te invitamos a"); y -= 5.6 * mm
    cv.drawCentredString(W / 2, y, "celebrar este día tan especial."); y -= 15 * mm
    bw, bh = 74 * mm, 13 * mm; bx, by = W / 2 - bw / 2, y - bh
    cv.setFillColor(HexColor(c["accent_s"])); cv.setFillAlpha(.35); cv.roundRect(bx - 5, by - 5, bw + 10, bh + 10, 22, fill=1, stroke=0); cv.setFillAlpha(1)
    cv.setFillColor(HexColor(c["accent"])); cv.roundRect(bx, by, bw, bh, 18, fill=1, stroke=0)
    cv.setFillColor(white); cv.setFont("Lato-Bold", 10.5); cv.drawCentredString(W / 2, by + 4.6 * mm, "VER INVITACIÓN COMPLETA")
    cv.linkURL(url, (bx, by, bx + bw, by + bh), relative=0)
    y = by - 7 * mm
    cv.setFillColor(HexColor(c["accent"])); cv.setFont("Lato-Regular", 8); cv.drawCentredString(W / 2, y, url.replace("https://", ""))
    cv.linkURL(url, (W/2 - 60*mm, y - 2, W/2 + 60*mm, y + 6), relative=0)
    cv.setFillColor(HexColor(c["ink_s"])); cv.setFont("Lato-Regular", 7.5)
    cv.drawCentredString(W / 2, 14 * mm, "  ·  ".join(secciones))
    cv.save()

# ───────────────────────── imagen para estados (1080x1920) ─────────────────────────
def png_estado(out, foto_rel_dir, foto, pos, c, ev, nombres, fecha_corta, ciudad, url):
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return False
    nom = (f"{nombres[0]}<br><span>&amp;</span> {nombres[1]}" if len(nombres) == 2 else nombres[0])
    html = f"""<!doctype html><meta charset=utf8><style>
    @font-face{{font-family:P;src:url('file://{STUDIO}/fonts/Playfair-SemiBoldItalic.ttf')}}
    @font-face{{font-family:L;src:url('file://{STUDIO}/fonts/Lato-Bold.ttf')}}
    @font-face{{font-family:C;src:url('file://{STUDIO}/fonts/Cormorant-Italic.ttf')}}
    *{{margin:0;box-sizing:border-box}} body{{width:1080px;height:1920px;position:relative;overflow:hidden;background:{c['dark']};font-family:L}}
    img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:{pos}}}
    .g{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.05) 0%,rgba(0,0,0,.05) 52%,rgba(10,7,4,.9) 82%)}}
    .t{{position:absolute;left:60px;right:60px;bottom:110px;text-align:center;color:#fff}}
    .e{{font-size:28px;letter-spacing:12px;color:{c['accent_s']};margin-bottom:20px}}
    h1{{font-family:P;font-weight:600;font-size:{150 if len(nombres)==1 else 100}px;line-height:1.02;text-shadow:0 6px 40px rgba(0,0,0,.5)}}
    h1 span{{font-family:C;font-size:.6em;color:{c['accent_s']}}}
    .d{{margin-top:36px;font-size:34px;letter-spacing:7px;color:#fff}}
    .c{{margin-top:12px;font-family:C;font-size:42px;color:#f3ece2}}
    .b{{display:inline-block;margin-top:40px;background:{c['accent']};padding:30px 62px;border-radius:60px;font-size:30px;letter-spacing:5px}}
    .u{{margin-top:22px;font-size:24px;letter-spacing:1px;opacity:.85}}
    </style><img src="file://{foto}"><div class=g></div><div class=t><div class=e>{ev['pdf_eyebrow']}</div><h1>{nom}</h1>
    <div class=d>{fecha_corta.upper()}</div><div class=c>{ciudad}</div><div class=b>VER INVITACIÓN</div><div class=u>{url.replace('https://','')}</div></div>"""
    tmp = Path(out).with_suffix(".tmp.html"); tmp.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto("file://" + str(tmp)); pg.wait_for_timeout(300); pg.screenshot(path=str(out)); b.close()
    tmp.unlink(); return True

# ───────────────────────── principal ─────────────────────────
def generar(pedido_path):
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    pedido_path = Path(pedido_path).resolve()
    P = json.loads(pedido_path.read_text(encoding="utf-8"))
    cdir = pedido_path.parent; fdir = cdir / "fotos"
    slug = P["slug"]; paq = PAQUETES[P.get("paquete", "clasica")]
    ev = dict(EVENTOS[P.get("evento", "otro")]); ev.update(P.get("textos", {}))
    out = ROOT / "i" / slug; (out / "img").mkdir(parents=True, exist_ok=True)
    url = BASE_URL + slug + "/"

    # colores
    col = P.get("colores", {})
    if col.get("paleta") in PALETAS:
        p1, p2, n1, n2 = PALETAS[col["paleta"]]
    else:
        p1, p2 = col.get("principal", "#CB8587"), col.get("secundario", "#8E8B63"); n1, n2 = col.get("nombre_principal", "Principal"), col.get("nombre_secundario", "Secundario")
    c = construir_colores(p1, p2)

    # fotos
    def foto(nombre, manual=None):
        src = fdir / nombre
        if not src.exists(): raise SystemExit(f"Falta la foto: {src}")
        dst = out / "img" / (Path(nombre).stem.lower().replace(" ", "-") + ".jpg")
        optimizar(src, dst)
        return {"src": "img/" + dst.name, "pos": posicion(dst, manual), "path": str(dst)}
    F = P.get("fotos", {})
    fotos = {"portada": foto(F["portada"], F.get("portada_pos"))}
    fotos["cierre"] = foto(F.get("cierre") or F["portada"], F.get("cierre_pos"))
    if paq["destacada"] and F.get("destacada"): fotos["destacada"] = foto(F["destacada"])
    historia = []
    for b in P.get("historia", [])[:paq["historia"]]:
        historia.append({"titulo": b["titulo"], "texto": b["texto"], "foto": foto(b["foto"], b.get("pos"))})
    galeria = []
    lista = P.get("galeria", [])[:paq["galeria"]]
    for i, g in enumerate(lista):
        f = foto(g if isinstance(g, str) else g["foto"])
        from PIL import Image
        w, h = Image.open(f["path"]).size
        forma = "tall" if h > w * 1.15 and i % 3 == 0 else ("wide" if w > h * 1.3 and i % 4 == 1 else "")
        galeria.append({**f, "forma": forma})
    if lista and len(lista) % 3 == 2 and galeria and galeria[-1]["forma"] == "": galeria[-1]["forma"] = "wide"

    d, larga, corta, fpdf = fecha_textos(P["fecha"])
    festejados = P["festejados"]
    nombres_texto = " y ".join(festejados)

    lugares = [{**l, "mapa": mapa(l.get("mapa"), l["nombre"], P["ciudad"]), "telefono": tel_bonito(l.get("telefono", "")) if l.get("telefono") else ""}
               for l in P["lugares"]]
    hospedaje = [{**h, "mapa": mapa(h.get("mapa"), h["nombre"], P["ciudad"])} for h in P.get("hospedaje", [])] if paq["hospedaje"] else []

    reg = P.get("regalos")
    if reg:
        tipo = reg.get("tipo", "sobres")
        reg.setdefault("titulo", {"sobres": "Lluvia de sobres", "mesa": "Mesa de regalos"}.get(tipo, "Regalos"))
        reg.setdefault("texto", f"Tu presencia es el regalo más grande. Si deseas hacernos un obsequio especial, "
                                f"{'habrá lluvia de sobres; también' if tipo == 'sobres' else ''} puedes apoyarnos con una transferencia. Escribe tu nombre en el concepto.")
    vest = P.get("vestimenta") or {"tipo": "Formal", "detalle": "Vestido largo o de cóctel · Traje"}
    if "colores" not in vest:
        vest["colores"] = [{"hex": c["raw_p"], "nombre": n1}, {"hex": c["raw_s"], "nombre": n2}, {"hex": c["pale"], "nombre": "Tono suave"}]
    vest.setdefault("colores_titulo", "Paleta de colores de la celebración")

    r = P["rsvp"]
    contactos = [{"nombre": k["nombre"], "telefono_texto": tel_bonito(k["telefono"])} for k in r.get("contactos", [])]
    rsvp = {"fecha_limite_texto": fecha_simple(r["fecha_limite"]), "whatsapp": wa(r["whatsapp"]), "contactos": contactos,
            "mensaje_wa": urllib.parse.quote(f"¡Hola! Confirmo mi asistencia a {('la boda de ' if P.get('evento')=='boda' else 'la celebración de ')}{nombres_texto}. Somos __ personas.")}

    s = {"historia": bool(historia), "destacada": "destacada" in fotos, "familia": paq["familia"] and bool(P.get("familia")),
         "galeria": bool(galeria), "vestimenta": paq["vestimenta"], "regalos": paq["regalos"] and bool(reg),
         "hospedaje": bool(hospedaje), "fotos_invitados": paq["fotos_invitados"] and bool(P.get("fotos_invitados_link"))}
    nav = [(k, v) for k, v, on in [("historia", "Historia", s["historia"]), ("familia", "Familia", s["familia"]),
                                   ("itinerario", "Itinerario", True), ("lugar", "Lugar", True), ("galeria", "Galería", s["galeria"]),
                                   ("vestimenta", "Vestimenta", s["vestimenta"]), ("regalos", "Regalos", s["regalos"]),
                                   ("hospedaje", "Hospedaje", s["hospedaje"]), ("rsvp", "Confirmar", True), ("fotos", "Fotos", s["fotos_invitados"])] if on]

    musica = None
    if paq["musica"] and P.get("musica") and (fdir / P["musica"]).exists():
        shutil.copy(fdir / P["musica"], out / "musica.mp3"); musica = "musica.mp3"

    hashtag = P.get("hashtag") or "#" + "".join(n.split()[0] for n in festejados) + ev.get("hashtag_sufijo", "")
    textos = {
        "eyebrow": ev["eyebrow"], "subtitulo": ev.get("subtitulo"), "historia_eyebrow": ev["historia_eyebrow"],
        "historia_titulo": ev["historia_titulo"], "historia_intro": ev.get("historia_intro", ""),
        "frase_destacada": P.get("frase_destacada", "Un día que guardaremos en el corazón para siempre."),
        "familia_titulo": ev.get("familia_titulo"), "familia_intro": ev.get("familia_intro", "Quienes con su amor y dedicación hacen posible esta celebración."),
        "itinerario_frase": ev["itinerario_frase"], "lugar_intro": ev.get("lugar_intro", "El lugar donde viviremos juntos este día tan especial."),
        "galeria_titulo": ev["galeria_titulo"], "galeria_intro": ev.get("galeria_intro", "Cada imagen guarda un instante que ya forma parte de esta historia."),
        "gracias": ev.get("gracias", "¡Gracias por celebrar con nosotros!"),
        "rsvp_texto": ev.get("rsvp_texto", "Tu presencia hará esta celebración aún más especial. Por favor confírmanos tu asistencia para organizar cada detalle con cariño."),
    }
    env = Environment(loader=FileSystemLoader(str(STUDIO)), autoescape=select_autoescape(["html"]))
    html = env.get_template("plantilla.html").render(
        titulo_pagina=f"{ev['eyebrow']} · {' & '.join(festejados)}", meta_desc=f"{larga} · {P['ciudad']}. ¡Te esperamos!",
        og_image=url + fotos["portada"]["src"], c=c, nav=nav, fotos=fotos, festejados=festejados, nombres_texto=nombres_texto,
        textos=textos, fecha_larga=larga, fecha_larga_corta=corta, ciudad=P["ciudad"], fecha_iso=d.strftime("%Y-%m-%dT%H:%M:00") + P.get("zona", "-06:00"),
        s=s, historia=historia, familia=P.get("familia", []), itinerario=P["itinerario"], lugares=lugares, galeria=galeria,
        vestimenta=vest, regalos=reg, hospedaje=hospedaje, rsvp=rsvp, fotos_invitados_link=P.get("fotos_invitados_link"),
        hashtag=hashtag, musica=musica, marca=MARCA)
    (out / "index.html").write_text(html, encoding="utf-8")

    secciones = [v for k, v in nav if k not in ("fotos",)]
    pdf_preinvitacion(out / "preinvitacion.pdf", fotos["portada"]["path"], fotos["portada"]["pos"], c, ev, festejados, fpdf, P["ciudad"], url, secciones)
    estado = paq["estado_png"] and png_estado(out / "preinvitacion-estado.png", out / "img", fotos["portada"]["path"], fotos["portada"]["pos"], c, ev, festejados, corta, P["ciudad"], url)

    msg = (f"¡Hola! Ya está lista la invitación de {nombres_texto} 🎉\n\n"
           f"Invitación completa: {url}\n"
           f"Pre-invitación (PDF): {url}preinvitacion.pdf\n"
           + (f"Imagen para estados: {url}preinvitacion-estado.png\n" if estado else "")
           + "\nRevísala con calma y dime si quieres algún ajuste. Gracias por confiar en Alejandría ✨")
    (out / "entrega.txt").write_text(msg, encoding="utf-8")
    print(json.dumps({"slug": slug, "url": url, "carpeta": str(out), "paquete": P.get("paquete"), "secciones": [k for k, _ in nav],
                      "colores": {k: c[k] for k in ("accent", "sec", "pale")}, "portada_pos": fotos["portada"]["pos"]}, ensure_ascii=False, indent=1))
    return out

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    generar(sys.argv[1])
