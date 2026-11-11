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

def sprig(color, flip=False, scale=1.0):
    """Rama con hojas, dibujada en SVG."""
    leaves = []
    for i in range(7):
        t = i / 6
        x = 10 + 120 * t; y = 110 - 70 * t - 18 * math.sin(t * math.pi)
        for side in (-1, 1):
            if i == 6 and side == 1: continue
            ang = -35 + side * 48 - 30 * t
            leaves.append(f'<ellipse cx="0" cy="-11" rx="5.2" ry="12" transform="translate({x:.1f},{y:.1f}) rotate({ang:.0f})" fill="{color}" opacity="{0.78 + 0.2 * (i % 2)}"/>')
    stem = '<path d="M6 116 C 50 92, 95 62, 136 36" stroke="%s" stroke-width="1.6" fill="none" stroke-linecap="round"/>' % color
    tr = f'transform="scale({-scale if flip else scale},{scale}) translate({-150 if flip else 0},0)"'
    return f'<svg viewBox="0 0 150 130" width="{150*scale:.0f}" height="{130*scale:.0f}"><g {tr}>{stem}{"".join(leaves)}</g></svg>'

def qr_svg(link, color):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, border=0, box_size=10)
    q.add_data(link); q.make(fit=True)
    m = q.get_matrix(); n = len(m)
    rects = "".join(f'<rect x="{x}" y="{y}" width="1.04" height="1.04"/>' for y, row in enumerate(m) for x, v in enumerate(row) if v)
    return f'<svg viewBox="0 0 {n} {n}" shape-rendering="crispEdges" style="width:100%;height:100%;display:block"><g fill="{color}">{rects}</g></svg>'

def card_html(a):
    P, S = a.principal, a.secundario
    olive_d = dark(P, .25); wood_d = dark(S, .35); wood_l = light(S, .35)
    cream = "#F8F3E9"
    wood = (f'<svg width="100%" height="100%" preserveAspectRatio="none" style="position:absolute;inset:0">'
            f'<filter id="g"><feTurbulence type="fractalNoise" baseFrequency="0.008 0.22" numOctaves="4" seed="7"/>'
            f'<feColorMatrix values="0 0 0 0 {hx(wood_d)[0]:.3f}  0 0 0 0 {hx(wood_d)[1]:.3f}  0 0 0 0 {hx(wood_d)[2]:.3f}  0 0 0 1.6 -.45"/></filter>'
            f'<rect width="100%" height="100%" fill="{S}"/><rect width="100%" height="100%" filter="url(#g)"/></svg>')
    return f"""
<div class="card">
  <div class="wood">{wood}</div>
  <div class="paper">
    <div class="sp tl">{sprig(P, False, .72)}</div>
    <div class="sp tr">{sprig(P, True, .72)}</div>
    <div class="eyebrow">{a.titulo}</div>
    <div class="names">{a.nombres}</div>
    <div class="rule"><span></span><i></i><span></span></div>
    <p class="lead">Ayúdanos a guardar cada momento de {a.evento}.<br>Escanea y sube tus fotos y videos.</p>
    <div class="qrbox"><div class="qr">{qr_svg(a.link, olive_d)}</div></div>
    <ol class="steps"><li><b>1</b>Abre tu cámara</li><li><b>2</b>Escanea</li><li><b>3</b>Sube tus fotos</li></ol>
    <div class="rule bottom"><span></span><i></i><span></span></div>
    <div class="foot">{a.hashtag + ' · ' if a.hashtag else ''}{a.fecha}</div>
  </div>
</div>""", dict(P=P, S=S, olive_d=olive_d, wood_d=wood_d, wood_l=wood_l, cream=cream)

def css(c):
    return f"""
@font-face{{font-family:CG;src:url(file://{FONTS}/Cormorant-SemiBold.ttf)}}
@font-face{{font-family:CGI;src:url(file://{FONTS}/Cormorant-SemiBoldItalic.ttf)}}
@font-face{{font-family:J;src:url(file://{FONTS}/Jost-Medium.ttf)}}
@font-face{{font-family:JR;src:url(file://{FONTS}/Jost-Regular.ttf)}}
*{{margin:0;padding:0;box-sizing:border-box}}
.card{{width:4in;height:6in;position:relative;overflow:hidden;font-family:JR;color:{c['olive_d']}}}
.wood{{position:absolute;inset:0}}
.paper{{position:absolute;inset:.2in;background:{c['cream']};border-radius:4px;box-shadow:inset 0 0 0 1.5px {c['wood_l']},inset 0 0 0 5px {c['cream']},inset 0 0 0 5.8px {c['P']};
  display:flex;flex-direction:column;align-items:center;text-align:center;padding:.62in .3in .22in}}
.sp{{position:absolute;top:.02in}} .tl{{left:0}} .tr{{right:0}}
.eyebrow{{font-family:J;font-size:8.5pt;letter-spacing:3.2pt;text-transform:uppercase;color:{c['wood_d']}}}
.names{{font-family:CGI;font-size:32pt;line-height:1.05;margin-top:4pt;color:{c['P']};text-wrap:balance}}
.rule{{display:flex;align-items:center;gap:6px;margin:7pt 0 6pt}} .rule span{{width:.55in;height:1px;background:{c['S']}}}
.rule i{{width:5px;height:5px;transform:rotate(45deg);background:{c['S']}}}
.lead{{font-family:CG;font-size:12.5pt;line-height:1.25;color:{c['olive_d']}}}
.qrbox{{margin-top:14pt;padding:9px;background:#fff;border-radius:10px;box-shadow:0 0 0 1.5px {c['S']},0 0 0 5px #fff,0 0 0 6px {c['wood_l']}}}
.qr{{width:1.85in;height:1.85in}}
.steps{{list-style:none;display:flex;gap:12pt;margin-top:15pt;font-size:7.6pt;letter-spacing:.3pt;white-space:nowrap}}
.steps li{{display:flex;align-items:center;gap:4px}}
.steps b{{font-family:J;font-weight:500;display:grid;place-items:center;width:13px;height:13px;border-radius:50%;background:{c['P']};color:#fff;font-size:6.5pt}}
.bottom{{margin-top:auto}}
.foot{{margin-top:2pt;font-family:J;font-size:7.5pt;letter-spacing:2pt;text-transform:uppercase;color:{c['wood_d']}}}
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True); ap.add_argument("--nombres", required=True); ap.add_argument("--link", required=True)
    ap.add_argument("--fecha", default=""); ap.add_argument("--principal", default="#6B6B3A"); ap.add_argument("--secundario", default="#A0754B")
    ap.add_argument("--hashtag", default=""); ap.add_argument("--titulo", default="Comparte tus fotos"); ap.add_argument("--evento", default="este día")
    a = ap.parse_args()
    out = ROOT / "i" / a.slug / "tarjetas"; out.mkdir(parents=True, exist_ok=True)
    body, c = card_html(a); style = css(c)
    single = f"<!doctype html><meta charset=utf8><style>{style}@page{{size:4in 6in;margin:0}}</style>{body}"
    sheet = (f"<!doctype html><meta charset=utf8><style>{style}@page{{size:letter;margin:0}}"
             ".sheet{width:8.5in;height:11in;display:flex;justify-content:center;align-items:flex-start;padding-top:.6in;gap:.25in;position:relative}"
             ".cut{position:absolute;background:#999}</style><div class=sheet>" + body + body +
             "</div><p style='position:absolute;top:7in;width:8.5in;text-align:center;font:9pt sans-serif;color:#888'>Recorta por el borde de madera · 10 × 15 cm</p>")
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
