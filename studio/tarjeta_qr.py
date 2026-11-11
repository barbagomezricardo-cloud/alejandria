#!/usr/bin/env python3
"""
Alejandría · Tarjetas de mesa con QR para que los invitados suban sus fotos.

Uso:
  python3 studio/tarjeta_qr.py --slug boda-ana-luis --nombres "Ana & Luis" \
      --link "https://photos.app.goo.gl/xxxx" --fecha "12 de diciembre, 2026" \
      [--principal "#6B6B3A"] [--secundario "#A0754B"] [--hashtag "#AnaYLuis"] \
      [--titulo "Comparte tus fotos"] [--evento "nuestra boda"]

Genera en i/<slug>/tarjetas/:
  tarjeta-4x6.pdf     1 tarjeta de 4x6 in (10x15 cm) para imprenta o portarretratos
  tarjetas-carta.pdf  2 tarjetas por hoja carta, con marcas de corte, para imprimir en casa
  tarjeta.png         vista previa / para mandar por WhatsApp
"""
import argparse, base64, io, math, colorsys
from pathlib import Path
import qrcode
from qrcode.image.svg import SvgPathImage
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "studio" / "fonts"

def hx(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def tohex(c): return "#" + "".join(f"{round(max(0, min(1, v)) * 255):02X}" for v in c)
def light(h, k):
    r, g, b = hx(h); hh, l, s = colorsys.rgb_to_hls(r, g, b); return tohex(colorsys.hls_to_rgb(hh, min(1, l + (1 - l) * k), s))
def dark(h, k):
    r, g, b = hx(h); hh, l, s = colorsys.rgb_to_hls(r, g, b); return tohex(colorsys.hls_to_rgb(hh, l * (1 - k), s))

def branch(P, scale=1.0, flip=False, seed=0, vflip=False):
    """Rama de olivo: tallo curvo, hojas lanceoladas en dos tonos y aceitunas."""
    import random
    rnd = random.Random(seed)
    leaf_a, leaf_b, olive = P, light(P, .38), dark(P, .35)
    # tallo: curva cuadrática de (0,120) a (200,20)
    def pt(t):
        x0, y0, cx, cy, x1, y1 = 4, 128, 70, 30, 205, 18
        return ((1-t)**2*x0 + 2*(1-t)*t*cx + t*t*x1, (1-t)**2*y0 + 2*(1-t)*t*cy + t*t*y1)
    def ang(t):
        a, b = pt(max(0, t-.01)), pt(min(1, t+.01)); return math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))
    parts = []
    stem = " ".join(f"{'M' if i == 0 else 'L'}{pt(i/40)[0]:.1f},{pt(i/40)[1]:.1f}" for i in range(41))
    parts.append(f'<path d="{stem}" stroke="{dark(P,.15)}" stroke-width="1.3" fill="none" stroke-linecap="round"/>')
    n = 13
    for i in range(n):
        t = .06 + .9 * i / (n - 1)
        x, y = pt(t); base = ang(t)
        side = 1 if i % 2 else -1
        L = 34 - 12 * t + rnd.uniform(-3, 3); W = L * .3
        a = base + side * (34 + rnd.uniform(-6, 6)) - 90
        col = leaf_a if (i // 2) % 2 == 0 else leaf_b
        parts.append(f'<path d="M0,0 Q{W:.1f},{-L*.45:.1f} 0,{-L:.1f} Q{-W:.1f},{-L*.45:.1f} 0,0Z" fill="{col}" transform="translate({x:.1f},{y:.1f}) rotate({a+180:.0f})"/>'
                     f'<path d="M0,-1 L0,{-L*.85:.1f}" stroke="{light(P,.6)}" stroke-width=".5" opacity=".6" transform="translate({x:.1f},{y:.1f}) rotate({a+180:.0f})"/>')
    tip = pt(1); parts.append(f'<path d="M0,0 Q4.5,-9 0,-20 Q-4.5,-9 0,0Z" fill="{leaf_a}" transform="translate({tip[0]:.1f},{tip[1]:.1f}) rotate({ang(1)+90:.0f})"/>')
    for t, off in ((.32, 9), (.58, -8), (.8, 7)):
        x, y = pt(t)
        parts.append(f'<ellipse cx="{x+off*.6:.1f}" cy="{y+abs(off):.1f}" rx="4.2" ry="5.6" fill="{olive}"/>'
                     f'<ellipse cx="{x+off*.6-1.3:.1f}" cy="{y+abs(off)-1.8:.1f}" rx="1.1" ry="1.5" fill="#fff" opacity=".35"/>')
    sx, tx = (-1, -210) if flip else (1, 0); sy, ty = (-1, -140) if vflip else (1, 0)
    g = f'<g transform="scale({sx},{sy}) translate({tx},{ty})">{"".join(parts)}</g>'
    return f'<svg viewBox="0 0 210 140" width="{210*scale:.0f}" height="{140*scale:.0f}" style="display:block">{g}</svg>'

def garland(P, S):
    """Guirnalda de olivo que recorre la parte alta del arco (coordenadas de la tarjeta en px a 96 dpi)."""
    import random
    rnd = random.Random(11)
    cx, cy, r = 192, 28.8 + 167, 167
    leaf_a, leaf_b, olive, stemc = P, light(P, .38), dark(P, .35), dark(P, .15)
    out = []
    for side in (-1, 1):
        a0, a1 = -90 + side * 3, -90 + side * 62
        pts = [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / 60)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / 60))) for k in range(61)]
        out.append('<path d="' + " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts)) + f'" stroke="{stemc}" stroke-width="1" fill="none"/>')
        n = 15
        for i in range(n):
            t = (i + .5) / n
            ang = a0 + (a1 - a0) * t
            x, y = cx + r * math.cos(math.radians(ang)), cy + r * math.sin(math.radians(ang))
            travel = ang + 90 * side            # dirección de avance sobre el arco
            lr = 1 if i % 2 else -1
            L = 19 - 7 * t + rnd.uniform(-2, 2); W = L * .3
            rot = travel + lr * 32 + 90          # la hoja base apunta a -y
            col = leaf_a if (i // 2) % 2 == 0 else leaf_b
            out.append(f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.0f})"><path d="M0,0 Q{W:.1f},{-L*.45:.1f} 0,{-L:.1f} Q{-W:.1f},{-L*.45:.1f} 0,0Z" fill="{col}"/>'
                       f'<path d="M0,-1 L0,{-L*.82:.1f}" stroke="#fff" stroke-width=".4" opacity=".35"/></g>')
            if i in (3, 8, 12):
                ox, oy = x + math.cos(math.radians(ang)) * 6 * lr, y + math.sin(math.radians(ang)) * 6 * lr
                out.append(f'<ellipse cx="{ox:.1f}" cy="{oy:.1f}" rx="2.8" ry="3.6" fill="{olive}" transform="rotate({travel:.0f} {ox:.1f} {oy:.1f})"/>')
        tx, ty = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
        out.append(f'<g transform="translate({tx:.1f},{ty:.1f}) rotate({a1 + 90*side + 90:.0f})"><path d="M0,0 Q3.5,-7 0,-15 Q-3.5,-7 0,0Z" fill="{leaf_a}"/></g>')
    out.append(f'<circle cx="{cx}" cy="{cy-r}" r="3.2" fill="{S}"/><circle cx="{cx}" cy="{cy-r}" r="1.4" fill="#F7F2E8"/>')
    return f'<svg class="garland" viewBox="0 0 384 576" width="384" height="576">{"".join(out)}</svg>'

def qr_svg(link, color):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, border=0, box_size=10)
    q.add_data(link); q.make(fit=True)
    m = q.get_matrix(); n = len(m)
    rects = "".join(f'<rect x="{x}" y="{y}" width="1.04" height="1.04"/>' for y, row in enumerate(m) for x, v in enumerate(row) if v)
    return f'<svg viewBox="0 0 {n} {n}" shape-rendering="crispEdges" style="width:100%;height:100%;display:block"><g fill="{color}">{rects}</g></svg>'

def foto_html(a):
    if not a.foto: return ""
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(a.foto)).convert("RGB"); im.thumbnail((800, 800))
    b = io.BytesIO(); im.save(b, "JPEG", quality=88)
    pos = a.foto_pos
    if not pos:
        try:
            import cv2, numpy as np
            g = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY)
            fs = cv2.CascadeClassifier(str(ROOT / "studio" / "haar_face.xml")).detectMultiScale(g, 1.1, 5, minSize=(20, 20))
            if len(fs):
                cx = sum(x + w / 2 for x, y, w, h in fs) / len(fs) / im.width; cy = sum(y + h / 2 for x, y, w, h in fs) / len(fs) / im.height
                pos = f"{cx*100:.0f}% {min(100, cy*100 + 10):.0f}%"
        except Exception: pass
    pos = pos or "50% 30%"
    return f'<div class="foto"><img src="data:image/jpeg;base64,{base64.b64encode(b.getvalue()).decode()}" style="object-position:{pos}"></div>'

def card_html(a):
    P, S = a.principal, a.secundario
    c = dict(P=P, S=S, olive_d=dark(P, .3), wood_d=dark(S, .3), wood_l=light(S, .55), paper="#F7F2E8")
    lead = "Escanea y comparte tus fotos y videos" if a.foto else f"Escanea el código y comparte con nosotros<br>tus fotos y videos de {a.evento}"
    return f"""
<div class="card{" cf" if a.foto else ""}">
  <div class="arch"></div><div class="arch in"></div>
  {garland(P, S)}
  <div class="content">
    <div class="eyebrow">{a.titulo}</div>
    {foto_html(a)}
    <div class="names">{a.nombres}</div>
    <p class="lead">{lead}</p>
    <div class="qrwrap"><i class="c tl"></i><i class="c tr"></i><i class="c bl"></i><i class="c br"></i><div class="qr">{qr_svg(a.link, c['olive_d'])}</div></div>
    <div class="steps">Abre tu cámara <span>·</span> Escanea <span>·</span> Sube tus fotos</div>
  </div>
  <div class="band"><div>{a.fecha}</div>{f'<div class="tag">{a.hashtag}</div>' if a.hashtag else ''}</div>
</div>""", c

def css(c):
    return f"""
@font-face{{font-family:CG;src:url(file://{FONTS}/Cormorant-SemiBold.ttf)}}
@font-face{{font-family:CGI;src:url(file://{FONTS}/Cormorant-SemiBoldItalic.ttf)}}
@font-face{{font-family:CI;src:url(file://{FONTS}/Cormorant-Italic.ttf)}}
@font-face{{font-family:J;src:url(file://{FONTS}/Jost-Medium.ttf)}}
@font-face{{font-family:JR;src:url(file://{FONTS}/Jost-Regular.ttf)}}
*{{margin:0;padding:0;box-sizing:border-box}}
.card{{width:4in;height:6in;position:relative;overflow:hidden;font-family:JR;color:{c['olive_d']};
  background:radial-gradient(120% 80% at 50% 30%,#FBF8F1 0%,{c['paper']} 60%,#EFE7D8 100%)}}
.arch{{position:absolute;left:.26in;right:.26in;top:.3in;bottom:.62in;border:1.2px solid {c['S']};border-radius:1.74in 1.74in 0 0;border-bottom:0}}
.arch.in{{left:.33in;right:.33in;top:.37in;bottom:.62in;border:.6px solid {c['P']};opacity:.55;border-radius:1.67in 1.67in 0 0;border-bottom:0}}
.crest{{position:absolute;top:.2in;left:0;right:0;display:flex;justify-content:center;gap:0}}
.crest svg:first-child{{margin-right:-.04in}} .crest svg:last-child{{margin-left:-.04in}}
.garland{{position:absolute;inset:0;width:4in;height:6in}}
.content{{position:absolute;left:.42in;right:.42in;top:.92in;bottom:.72in;display:flex;flex-direction:column;align-items:center;justify-content:space-between;text-align:center}}
.eyebrow{{font-family:J;font-size:7.6pt;letter-spacing:3.6pt;text-transform:uppercase;color:{c['wood_d']}}}
.names{{font-family:CGI;font-size:36pt;line-height:1;margin-top:2pt;color:{c['P']};text-wrap:balance}}
.lead{{font-family:CI;font-size:12pt;line-height:1.3;color:{c['olive_d']}}}
.qrwrap{{position:relative;padding:.1in;background:#fff;border-radius:3px;box-shadow:0 1px 6px rgba(80,60,30,.12)}}
.qr{{width:1.75in;height:1.75in}}
.c{{position:absolute;width:12px;height:12px;border:0 solid {c['S']}}}
.c.tl{{top:-5px;left:-5px;border-top-width:1.5px;border-left-width:1.5px}} .c.tr{{top:-5px;right:-5px;border-top-width:1.5px;border-right-width:1.5px}}
.c.bl{{bottom:-5px;left:-5px;border-bottom-width:1.5px;border-left-width:1.5px}} .c.br{{bottom:-5px;right:-5px;border-bottom-width:1.5px;border-right-width:1.5px}}
.steps{{white-space:nowrap;font-family:J;font-size:6.4pt;letter-spacing:1.1pt;text-transform:uppercase;color:{c['olive_d']}}} .steps span{{color:{c['S']};margin:0 3px}}
.band{{position:absolute;left:0;right:0;bottom:0;height:.62in;background:{c['S']};color:#FBF6EC;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;
  background-image:linear-gradient(180deg,rgba(255,255,255,.08),rgba(0,0,0,.08))}}
.band div{{font-family:J;font-size:7.6pt;letter-spacing:3pt;text-transform:uppercase}} .band .tag{{font-family:CI;font-size:11pt;letter-spacing:.5pt;text-transform:none;opacity:.92}}
.foto{{flex:none;width:1.02in;height:1.22in;border-radius:.51in .51in 2px 2px;overflow:hidden;box-shadow:0 0 0 1.2px {c['S']},0 0 0 4px {c['paper']},0 0 0 4.6px {c['P']}}}
.foto img{{width:100%;height:100%;object-fit:cover;display:block}}
.card.cf .names{{font-size:28pt}} .card.cf .lead{{font-size:10.5pt}} .card.cf .qr{{width:1.4in;height:1.4in}}
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True); ap.add_argument("--nombres", required=True); ap.add_argument("--link", required=True)
    ap.add_argument("--fecha", default=""); ap.add_argument("--principal", default="#6B6B3A"); ap.add_argument("--secundario", default="#A0754B")
    ap.add_argument("--hashtag", default=""); ap.add_argument("--foto", default=""); ap.add_argument("--foto-pos", dest="foto_pos", default=""); ap.add_argument("--carpeta", default="tarjetas"); ap.add_argument("--titulo", default="Comparte tus fotos"); ap.add_argument("--evento", default="este día")
    a = ap.parse_args()
    out = ROOT / "i" / a.slug / a.carpeta; out.mkdir(parents=True, exist_ok=True)
    body, c = card_html(a); style = css(c)
    single = f"<!doctype html><meta charset=utf8><style>{style}@page{{size:4in 6in;margin:0}}</style>{body}"
    sheet = (f"<!doctype html><meta charset=utf8><style>{style}@page{{size:letter;margin:0}}"
             ".sheet{width:8.5in;height:11in;display:flex;justify-content:center;align-items:flex-start;padding-top:.6in;gap:.25in;position:relative} .sheet .card{outline:.5px dashed #bbb}"
             ".cut{position:absolute;background:#999}</style><div class=sheet>" + body + body +
             "</div><p style='position:absolute;top:7in;width:8.5in;text-align:center;font:9pt sans-serif;color:#888'>Recorta por el borde · 10 × 15 cm</p>")
    tmp = out / "_t.html"
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 384, "height": 576}, device_scale_factor=3)
        for html, pdf, kw in [(single, "tarjeta-4x6.pdf", dict(width="4in", height="6in")), (sheet, "tarjetas-carta.pdf", dict(format="Letter"))]:
            tmp.write_text(html, encoding="utf-8"); pg.goto("file://" + str(tmp)); pg.wait_for_load_state("networkidle")
            pg.pdf(path=str(out / pdf), print_background=True, **kw)
            if pdf.startswith("tarjeta-"): pg.locator(".card").screenshot(path=str(out / "tarjeta.png"))
        b.close()
    tmp.unlink()
    print(out)

if __name__ == "__main__":
    main()
