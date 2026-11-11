# Alejandría · Invitaciones que guardan historias

Sitio del negocio + invitaciones de clientes, publicado con GitHub Pages en
**https://barbagomezricardo-cloud.github.io/alejandria/**

## Estructura

```
index.html                 página del negocio (paquetes, ejemplo, preguntas)
privacidad.html            aviso de privacidad
assets/                    logos (SVG), ícono de perfil, imagen para compartir
i/<cliente>/               INVITACIÓN PUBLICADA de cada cliente
   index.html                invitación web  → .../alejandria/i/<cliente>/
   img/                      fotos optimizadas
   preinvitacion.pdf         pre-invitación con botón al link
   preinvitacion-estado.png  imagen 1080x1920 para estados (Clásica y Premium)
   entrega.txt               mensaje listo para mandar al cliente
clientes/<cliente>/        pedido del cliente
   pedido.json               datos de la invitación (lo que se publica)
   fotos/                    fotos originales (NO se suben a GitHub)
studio/                    plantilla, generador, fuentes y formulario
marketing/                 publicidad para redes y su generador
```

## Hacer una invitación nueva

```bash
pip install jinja2 pillow reportlab opencv-python-headless==4.10.0.84 playwright
python3 studio/generar.py clientes/<cliente>/pedido.json
git add i/<cliente> clientes/<cliente>/pedido.json && git commit -m "Invitación <cliente>" && git push
```

Ver `studio/modelo-pedido.json` como modelo y `studio/FORMULARIO.md` para las preguntas del formulario.

## Tarjetas de mesa con QR (+$290)

```bash
python3 studio/tarjeta_qr.py --slug <cliente> --nombres "Ana &amp; Luis" --link "<link del álbum>" \
  --fecha "12 de diciembre, 2026" --principal "#6B6B3A" --secundario "#A0754B" --hashtag "#AnaYLuis" --evento "nuestra boda"
```
Sale en `i/<cliente>/tarjetas/`: `tarjeta-4x6.pdf` (imprenta), `tarjetas-carta.pdf` (2 por hoja) y `tarjeta.png`.

## Paquetes

| Paquete | Precio | Historia | Galería | Extras |
|---|---|---|---|---|
| Esencial | $590 | — | — | 1 ronda de cambios |
| Clásica | $990 | 1 bloque | 8 fotos | música, hospedaje, imagen para estados, 2 rondas |
| Premium | $1,590 | 3 bloques | 16 fotos | foto destacada, álbum de invitados, 48 h, cambios ilimitados |
