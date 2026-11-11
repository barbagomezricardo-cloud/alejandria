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
    """QR de puntos con ojos cuadrados redondeados."""
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=0)
    q.add_data(link); q.make(fit=True)
    m = q.get_matrix(); n = len(m)
    def in_eye(x, y): return (x < 7 and y < 7) or (x >= n - 7 and y < 7) or (x < 7 and y >= n - 7)
    dots = "".join(f'<rect x="{x+.06}" y="{y+.06}" width=".88" height=".88" rx=".42"/>' for y, row in enumerate(m) for x, v in enumerate(row) if v and not in_eye(x, y))
    eyes = "".join(f'<rect x="{ex+.5}" y="{ey+.5}" width="6" height="6" rx="1.4" fill="none" stroke="{color}" stroke-width="1"/>'
                   f'<rect x="{ex+2}" y="{ey+2}" width="3" height="3" rx=".7"/>' for ex, ey in ((0, 0), (n - 7, 0), (0, n - 7)))
    return f'<svg viewBox="0 0 {n} {n}" style="width:100%;height:100%;display:block"><g fill="{color}">{dots}{eyes}</g></svg>'

def leaf(x, y, rot, L, col, vein="#fff", w=.42):
    W = L * w
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.0f})"><path d="M0,0 C{W:.1f},{-L*.2:.1f} {W:.1f},{-L*.75:.1f} 0,{-L:.1f} C{-W:.1f},{-L*.75:.1f} {-W:.1f},{-L*.2:.1f} 0,0Z" fill="{col}"/>'
            f'<path d="M0,-1 Q{W*.15:.1f},{-L*.5:.1f} 0,{-L*.9:.1f}" stroke="{vein}" stroke-width=".5" fill="none" opacity=".45"/></g>')

def spray(x, y, ang, length, P, seed, n=7, size=17):
    """Rama con hojas ovaladas alternas (tipo eucalipto/olivo)."""
    import random
    rnd = random.Random(seed)
    tones = [P, light(P, .25), light(P, .45), dark(P, .12)]
    out = []
    ex, ey = x + length * math.cos(math.radians(ang)), y + length * math.sin(math.radians(ang))
    bend = rnd.uniform(-.18, .18) * length
    cx, cy = (x + ex) / 2 - bend * math.sin(math.radians(ang)), (y + ey) / 2 + bend * math.cos(math.radians(ang))
    out.append(f'<path d="M{x:.1f},{y:.1f} Q{cx:.1f},{cy:.1f} {ex:.1f},{ey:.1f}" stroke="{dark(P,.2)}" stroke-width=".9" fill="none"/>')
    for i in range(n):
        t = .18 + .8 * i / max(1, n - 1)
        px = (1-t)**2*x + 2*(1-t)*t*cx + t*t*ex; py = (1-t)**2*y + 2*(1-t)*t*cy + t*t*ey
        side = 1 if i % 2 else -1
        L = size * (1.05 - .35 * t) * rnd.uniform(.9, 1.1)
        out.append(leaf(px, py, ang + 90 + side * rnd.uniform(38, 55), L, rnd.choice(tones)))
    out.append(leaf(ex, ey, ang + 90, size * .7, tones[0]))
    return "".join(out)

def rose(x, y, r, wood):
    petal, shade, edge = "#FBF7EE", "#EFE6D3", light(wood, .55)
    out = [f'<g transform="translate({x:.1f},{y:.1f})">']
    for k, (rr, n, off) in enumerate(((r, 7, 0), (r*.78, 6, 25), (r*.56, 5, 10))):
        for i in range(n):
            a = i * 360 / n + off
            out.append(f'<ellipse cx="0" cy="{-rr*.48:.1f}" rx="{rr*.52:.1f}" ry="{rr*.55:.1f}" transform="rotate({a:.0f})" fill="{petal if k%2==0 else shade}" stroke="{edge}" stroke-width=".5"/>')
    out.append(f'<circle r="{r*.3:.1f}" fill="{shade}" stroke="{edge}" stroke-width=".5"/>')
    out.append(f'<path d="M{-r*.12:.1f},0 a{r*.14:.1f},{r*.14:.1f} 0 1,1 {r*.2:.1f},{r*.05:.1f} a{r*.2:.1f},{r*.2:.1f} 0 1,1 {-r*.32:.1f},{-r*.12:.1f}" fill="none" stroke="{edge}" stroke-width=".7"/>')
    out.append('</g>')
    return "".join(out)

def babys_breath(x, y, ang, length, P, seed):
    import random
    rnd = random.Random(seed)
    out = []
    for k in range(5):
        a = ang + rnd.uniform(-35, 35); L = length * rnd.uniform(.5, 1)
        ex, ey = x + L * math.cos(math.radians(a)), y + L * math.sin(math.radians(a))
        out.append(f'<path d="M{x:.1f},{y:.1f} L{ex:.1f},{ey:.1f}" stroke="{light(P,.3)}" stroke-width=".5"/>')
        for j in range(4):
            fx, fy = ex + rnd.uniform(-6, 6), ey + rnd.uniform(-6, 6)
            out.append(f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="{rnd.uniform(1.6,2.4):.1f}" fill="#FFFDF7" stroke="#E4DCC8" stroke-width=".4"/><circle cx="{fx:.1f}" cy="{fy:.1f}" r=".6" fill="#E9DDB8"/>')
    return "".join(out)

def florals(P, S):
    tr = (spray(390, 6, 165, 150, P, 1, 10, 26) + spray(392, 52, 200, 120, P, 2, 8, 24) + spray(372, -6, 118, 120, P, 3, 8, 22)
          + spray(392, 120, 245, 95, P, 13, 7, 22) + spray(330, 0, 150, 70, P, 14, 5, 18)
          + babys_breath(318, 36, 200, 40, P, 4) + babys_breath(368, 96, 120, 32, P, 5)
          + rose(352, 34, 22, S) + rose(318, 12, 13, S))
    bl = (spray(-6, 400, -80, 160, P, 6, 11, 28) + spray(-6, 470, -55, 105, P, 7, 8, 25) + spray(4, 590, -55, 115, P, 8, 8, 23)
          + spray(-6, 540, -65, 130, P, 9, 8, 25) + spray(40, 600, -85, 70, P, 15, 5, 19) + spray(-6, 330, -100, 90, P, 16, 6, 20)
          + babys_breath(40, 430, -60, 42, P, 10) + babys_breath(66, 492, -50, 30, P, 11) + babys_breath(18, 360, -80, 30, P, 12)
          + rose(30, 524, 32, S) + rose(74, 562, 20, S) + rose(16, 455, 20, S))
    return f'<svg class="florals" viewBox="0 0 384 576" width="384" height="576">{tr}{bl}</svg>'

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

HEART = '<svg viewBox="0 0 24 22" width="11" height="10"><path d="M12 20 C5 14 1 10.5 1 6.5 A5 5 0 0 1 12 4.5 A5 5 0 0 1 23 6.5 C23 10.5 19 14 12 20Z" fill="none" stroke="currentColor" stroke-width="2"/></svg>'

def card_html(a):
    P, S = a.principal, a.secundario
    c = dict(P=P, S=S, olive_d=dark(P, .38), wood_d=dark(S, .25), paper="#F8F4EA")
    div = f'<div class="div"><span></span>{HEART}<span></span></div>'
    names = f'<div class="names">{a.nombres}</div>' if a.nombres else ''
    return f"""
<div class="card{" cf" if a.foto else ""}">
  <div class="frame"></div><div class="frame in"></div>
  {florals(P, S)}
  <div class="content">
    {div}
    <h1>Comparte<br><span>tus fotos</span></h1>
    {foto_html(a)}
    <p class="lead">Tus recuerdos también son parte<br>de nuestra historia. {HEART}</p>
    <div class="qrwrap"><div class="qr">{qr_svg(a.link, c['olive_d'])}</div></div>
    <div class="cta">Escanea el QR y<br>comparte tus fotos</div>
    {div}
    {names}<div class="date">{a.fecha}</div>
  </div>
</div>""", c

def css(c):
    return f"""
@font-face{{font-family:GV;src:url(file://{FONTS}/GreatVibes.ttf)}}
@font-face{{font-family:CG;src:url(file://{FONTS}/Cormorant-Medium.ttf)}}
@font-face{{font-family:CGS;src:url(file://{FONTS}/Cormorant-SemiBold.ttf)}}
*{{margin:0;padding:0;box-sizing:border-box}}
.card{{width:4in;height:6in;position:relative;overflow:hidden;color:{c['olive_d']};background:radial-gradient(110% 80% at 50% 40%,#FCFAF4 0%,{c['paper']} 65%,#F0E9DA 100%)}}
.frame{{position:absolute;inset:.17in;border:1.1px solid {c['S']}}}
.frame.in{{inset:.22in;border:.5px solid {c['S']};opacity:.7}}
.florals{{position:absolute;inset:0;width:4in;height:6in;z-index:2;pointer-events:none}}
.content{{position:absolute;inset:.34in .4in .3in .55in;display:flex;flex-direction:column;align-items:center;text-align:center;z-index:1}}
.div{{display:flex;align-items:center;gap:7px;color:{c['S']}}} .div span{{width:.75in;height:.8px;background:{c['S']}}}
h1{{font-family:GV;font-weight:400;font-size:48pt;line-height:.82;margin-top:8pt;color:{c['olive_d']}}} h1 span{{display:inline-block;margin-left:.35in}}
.lead{{font-family:CG;font-size:11.5pt;line-height:1.3;margin-top:9pt;color:{c['olive_d']}}} .lead svg{{color:{c['S']};vertical-align:-1px}}
.qrwrap{{margin-top:11pt;padding:.1in;background:#fff;border:1.4px solid {c['S']};border-radius:12px}}
.qr{{width:1.62in;height:1.62in}}
.cta{{margin-top:10pt;font-family:CGS;font-size:10.5pt;letter-spacing:2.6pt;text-transform:uppercase;line-height:1.35;color:{c['olive_d']}}}
.content>.div:nth-last-of-type(1){{margin-top:9pt}}
.names{{font-family:GV;font-size:20pt;line-height:1;margin-top:5pt;color:{c['P']}}}
.date{{font-family:CGS;font-size:7pt;letter-spacing:2.4pt;text-transform:uppercase;color:{c['wood_d']};margin-top:2pt}}
.foto{{width:1in;height:1.15in;border-radius:.5in .5in 3px 3px;overflow:hidden;margin-top:6pt;box-shadow:0 0 0 1.2px {c['S']},0 0 0 4px {c['paper']},0 0 0 4.6px {c['S']}}}
.foto img{{width:100%;height:100%;object-fit:cover;display:block}}
.card.cf h1{{font-size:40pt}} .card.cf .lead{{font-size:10pt;margin-top:6pt}} .card.cf .qr{{width:1.3in;height:1.3in}} .card.cf .qrwrap{{margin-top:7pt}} .card.cf .cta{{margin-top:7pt;font-size:9pt}}
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
