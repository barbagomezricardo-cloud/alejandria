#!/usr/bin/env python3
"""Genera las imágenes de publicidad de Alejandría (posts 1080x1350, historias 1080x1920 y og.jpg del sitio).
Uso: python3 marketing/generar_publicidad.py"""
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "studio" / "fonts"
A = ROOT / "assets"
OUT = ROOT / "marketing"
logo_claro = (A / "logo-vertical-claro.svg").read_text()
logo = (A / "logo-vertical.svg").read_text()
demo = A / "demo-boda.jpg"

CSS = f"""
@font-face{{font-family:CG;src:url(file://{F}/Cormorant-SemiBold.ttf)}}
@font-face{{font-family:CGI;src:url(file://{F}/Cormorant-SemiBoldItalic.ttf)}}
@font-face{{font-family:J;src:url(file://{F}/Jost-Medium.ttf)}}
@font-face{{font-family:JR;src:url(file://{F}/Jost-Regular.ttf)}}
*{{margin:0;box-sizing:border-box}}
body{{width:1080px;overflow:hidden;font-family:JR;color:#2B1F22}}
.k{{font-family:J;letter-spacing:9px;text-transform:uppercase;font-size:26px}}
h1{{font-family:CG;font-weight:400;line-height:1.02}}
em{{font-family:CGI;font-style:normal}}
.pill{{display:inline-block;font-family:J;letter-spacing:5px;text-transform:uppercase;font-size:26px;padding:24px 50px;border-radius:60px}}
.logo svg{{width:100%;height:auto;display:block}}
.arch{{position:absolute;border:3px solid #D9B77E;border-bottom:0;border-radius:999px 999px 0 0}}
"""

def foot(pill, pill_style, lg):
    return f"""<div style="position:absolute;left:0;right:0;bottom:90px;display:flex;flex-direction:column;align-items:center;gap:34px">
<div class=pill style="{pill_style}">{pill}</div><div class=logo style="width:240px">{lg}</div></div>"""

ADS = {}

ADS["bodas-post"] = (1350, f"""<div style="position:relative;height:1350px;background:#F6EFE4;text-align:center;padding:120px 90px">
<div class=arch style="left:170px;right:170px;top:90px;height:840px"></div>
<div class=arch style="left:196px;right:196px;top:116px;height:814px;border-width:1.5px"></div>
<div style="position:relative;padding-top:130px">
<div class=k style="color:#9A7643">Invitaciones de boda</div>
<h1 style="font-size:124px;color:#6B2338;margin:30px 0">El sí<br><em style="color:#9A7643">merece</em><br>ser recordado</h1>
<div style="font-size:32px;color:#5A4A4C;max-width:640px;margin:0 auto">Su historia, ceremonia y recepción con mapa, mesa de regalos y confirmación.</div></div>
{foot("Cotiza por WhatsApp","background:#6B2338;color:#fff",logo)}</div>""")

ADS["bautizo-comunion-post"] = (1350, f"""<div style="position:relative;height:1350px;background:linear-gradient(180deg,#EAF0F5,#F6EFE4);text-align:center;padding:140px 90px">
<div style="font-size:90px;color:#9A7643;line-height:1">✦</div>
<div class=k style="color:#4E6E8A;margin-top:24px">Bautizos · Primera Comunión</div>
<h1 style="font-size:116px;color:#2F4B66;margin:34px 0">Un día de fe,<br><em style="color:#9A7643">una invitación</em><br>a su altura</h1>
<div style="font-size:32px;color:#4A5763;max-width:760px;margin:0 auto">Papás y padrinos, misa y recepción con mapa, y confirmación por WhatsApp. Sin imprimir ni repartir.</div>
{foot("Desde $590 · Lista en 72 h","background:#2F4B66;color:#fff",logo)}</div>""")

ADS["baby-shower-post"] = (1350, f"""<div style="position:relative;height:1350px;background:#F8EDE6;text-align:center;padding:150px 90px;overflow:hidden">
<div style="position:absolute;width:520px;height:520px;border-radius:50%;background:#EFD9CF;left:-170px;top:-140px"></div>
<div style="position:absolute;width:380px;height:380px;border-radius:50%;background:#E1E9DC;right:-130px;top:420px"></div>
<div style="position:relative">
<div class=k style="color:#A65A3C">Baby Shower</div>
<h1 style="font-size:132px;color:#6B2338;margin:34px 0">La dulce<br><em style="color:#A65A3C">espera</em><br>se celebra</h1>
<div style="font-size:32px;color:#5A4A4C;max-width:740px;margin:0 auto">Fecha, lugar, mesa de regalos y confirmación en un solo link para toda la familia.</div></div>
{foot("Pide la tuya","background:#6B2338;color:#fff",logo)}</div>""")

ADS["lanzamiento-post"] = (1350, f"""<div style="position:relative;height:1350px;background:#6B2338;color:#fff;text-align:center;padding:100px 90px">
<div class=logo style="width:400px;margin:0 auto">{logo_claro}</div>
<h1 style="font-size:112px;margin:50px 0 24px">¡Abrimos<br><em style="color:#D9B77E">en Jamay!</em></h1>
<div style="font-size:33px;color:#F3E3E0;max-width:780px;margin:0 auto">Invitaciones digitales para XV años, bodas, bautizos, comuniones y baby showers.</div>
<div style="margin:54px auto 0;display:inline-block;border:2px solid #D9B77E;border-radius:28px;padding:30px 60px">
<div class=k style="color:#D9B77E;font-size:24px">Precio de lanzamiento</div>
<div style="font-family:CG;font-size:96px;line-height:1.05">10% off</div>
<div style="font-size:28px;color:#F3E3E0">a los primeros 10 clientes</div></div>
<div style="position:absolute;left:0;right:0;bottom:70px;font-family:J;letter-spacing:4px;font-size:26px;color:#E7C6C3">WHATSAPP 392 132 3212</div></div>""")

pasos = [(1, "Elige tu paquete", "Esencial, Clásica o Premium"), (2, "Llena el formulario", "Datos, colores favoritos y fotos"),
         (3, "Revisa y aprueba", "Te la mandamos en 72 horas"), (4, "¡Compártela!", "Link, PDF e imagen para estados")]
ADS["como-funciona-historia"] = (1920, f"""<div style="position:relative;height:1920px;background:#F6EFE4;padding:170px 90px;text-align:center">
<div class=logo style="width:300px;margin:0 auto">{logo}</div>
<h1 style="font-size:110px;color:#6B2338;margin:70px 0 60px">Tu invitación<br><em style="color:#9A7643">en 4 pasos</em></h1>
<div style="display:grid;gap:30px;text-align:left">""" + "".join(
    f"""<div style="display:flex;gap:34px;align-items:center;background:#fff;border-radius:30px;padding:36px 44px">
<div style="flex:none;width:96px;height:96px;border-radius:50%;background:#6B2338;color:#fff;font-family:CG;font-size:56px;display:grid;place-items:center">{n}</div>
<div><div style="font-family:CG;font-size:52px;color:#6B2338">{t}</div><div style="font-size:30px;color:#5A4A4C">{d}</div></div></div>""" for n, t, d in pasos)
    + """</div><div class=pill style="background:#6B2338;color:#fff;margin-top:70px">Link en el perfil</div></div>""")

ADS["ejemplo-historia"] = (1920, f"""<div style="position:relative;height:1920px;background:#6B2338;color:#fff;text-align:center;padding:150px 90px">
<div class=k style="color:#E7C6C3">Así la ven tus invitados</div>
<h1 style="font-size:100px;margin:30px 0 70px">Desliza, escucha<br><em style="color:#D9B77E">y confirma</em></h1>
<div style="width:560px;height:1130px;margin:0 auto;border-radius:76px;padding:18px;background:#2B1F22;box-shadow:0 40px 90px rgba(0,0,0,.4)">
<img src="file://{demo}" style="width:100%;height:100%;object-fit:cover;object-position:top;border-radius:60px"></div>
<div class=pill style="background:#fff;color:#6B2338;margin-top:-60px;position:relative">Ver ejemplo · link en perfil</div></div>""")


foto_boda = ROOT / "i/ejemplo-boda-yanin-ricardo/images/r-story1.jpeg"
ADS["bodas-foto-post"] = (1350, f"""<div style="position:relative;height:1350px;background:#2B1F22">
<img src="file://{foto_boda}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 62%">
<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(20,10,10,.05) 30%,rgba(43,15,24,.94) 78%)"></div>
<div style="position:absolute;left:80px;right:80px;bottom:90px;color:#fff;text-align:center">
<div class=k style="color:#E7C6C3">Invitaciones de boda</div>
<h1 style="font-size:104px;margin:22px 0 18px">Su historia de amor,<br><em style="color:#D9B77E">en una invitación</em></h1>
<div style="font-size:32px;opacity:.92">Ceremonia y recepción con mapa, galería, mesa de regalos y confirmación por WhatsApp.</div>
<div style="display:flex;justify-content:space-between;align-items:center;margin-top:44px">
<div class=logo style="width:230px">{logo_claro}</div>
<div class=pill style="background:#fff;color:#6B2338">Cotiza la tuya</div></div></div></div>""")

OG = f"""<div style="width:1200px;height:630px;background:#F6EFE4;display:flex;align-items:center;gap:60px;padding:0 80px;position:relative;overflow:hidden">
<div class=arch style="right:-60px;top:-40px;width:480px;height:720px;opacity:.6"></div>
<div style="flex:1"><div class=logo style="width:360px">{logo}</div>
<h1 style="font-size:64px;color:#6B2338;margin-top:30px">Invitaciones digitales para <em style="color:#9A7643">XV, bodas y más</em></h1></div>
<div style="width:300px;height:560px;border-radius:44px;padding:10px;background:#2B1F22;flex:none;margin-top:120px"><img src="file://{demo}" style="width:100%;height:100%;object-fit:cover;object-position:top;border-radius:36px"></div></div>"""

if __name__ == "__main__":
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name, (h, body) in ADS.items():
            pg = b.new_page(viewport={"width": 1080, "height": h})
            tmp = OUT / "_tmp.html"; tmp.write_text(f"<!doctype html><meta charset=utf8><style>{CSS}</style>{body}", encoding="utf-8")
            pg.goto("file://" + str(tmp)); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(300)
            pg.screenshot(path=str(OUT / f"{name}.png")); pg.close()
        pg = b.new_page(viewport={"width": 1200, "height": 630})
        tmp = OUT / "_tmp.html"; tmp.write_text(f"<!doctype html><meta charset=utf8><style>{CSS}body{{width:1200px}}</style>{OG}", encoding="utf-8")
        pg.goto("file://" + str(tmp)); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(300)
        pg.screenshot(path=str(A / "og.jpg"), type="jpeg", quality=85)
        b.close()
    (OUT / "_tmp.html").unlink(missing_ok=True)
    print("ok")
