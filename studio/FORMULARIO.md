# Formulario de pedido · Alejandría (Tally)

Cómo armarlo en Tally (tally.so, plan gratis):
1. Crea un formulario nuevo llamado **"Pedido de invitación · Alejandría"**.
2. Copia las preguntas de abajo en orden. Usa **lógica condicional** (Conditional logic) donde dice *Solo si…*.
3. Agrega un **campo oculto** (Hidden field) llamado `paquete` (así, si el cliente viene del botón "Elegir Clásica" del sitio, ya llega marcado).
4. En *Integrations* conecta **Google Sheets** → hoja "Pedidos Alejandría".
5. En *Settings* activa la notificación por correo a tu Gmail para cada respuesta nueva.
6. Publica y pega el link en `FORM_URL` dentro de `index.html` (o pídeselo al agente).

La columna "Campo" indica dónde cae cada respuesta en `clientes/<slug>/pedido.json`.

---

## Página 1 · Tu paquete

| # | Pregunta | Tipo | Opciones | Campo |
|---|---|---|---|---|
| 1 | ¿Qué paquete quieres? | Opción única (obligatoria) | Esencial $590 · Clásica $990 · Premium $1,590 | `paquete` |
| 2 | ¿Qué celebras? | Opción única (obligatoria) | XV años · Boda · Bautizo · Primera Comunión · Baby Shower · Cumpleaños · Otro | `evento` |
| 3 | Extras (opcional) | Casillas | Entrega exprés 24 h (+$250) · Pase personalizado por familia (+$390) · 5 fotos extra (+$120) · Diseño extra de pre-invitación (+$150) · Dominio propio (+$450) | (para la cotización) |

## Página 2 · Tus datos de contacto (no se publican)

| # | Pregunta | Tipo | Campo |
|---|---|---|---|
| 4 | Tu nombre completo | Texto corto (obligatorio) | — |
| 5 | Tu WhatsApp | Teléfono (obligatorio) | — |
| 6 | ¿Cómo nos conociste? | Opción única: Facebook · Instagram · TikTok · Recomendación · Salón/fotógrafo · Otro | — |

## Página 3 · El evento

| # | Pregunta | Tipo | Campo |
|---|---|---|---|
| 7 | Nombre(s) como quieres que aparezcan. Boda: nombre de la novia y del novio | Texto corto ×2 (el segundo solo si es Boda) | `festejados` |
| 8 | Fecha del evento | Fecha (obligatoria) | `fecha` |
| 9 | Hora de inicio | Hora (obligatoria) | `fecha` |
| 10 | Ciudad y estado | Texto corto · ej. "Jamay, Jalisco" | `ciudad` |
| 11 | Lugar de la ceremonia o misa (nombre y dirección) | Texto largo · opcional | `lugares[0]` |
| 12 | Link de Google Maps de la ceremonia | Link · opcional | `lugares[0].mapa` |
| 13 | Lugar de la recepción/fiesta (nombre y dirección) | Texto largo (obligatorio) | `lugares[1]` |
| 14 | Link de Google Maps de la recepción | Link · opcional | `lugares[1].mapa` |
| 15 | Itinerario: escribe cada actividad con su hora, una por renglón. Ej.: "5:00 PM Misa" | Texto largo (obligatorio) | `itinerario` |
| 16 | Papás, padrinos o personas a nombrar (nombre y rol, uno por renglón) | Texto largo · opcional | `familia` |

## Página 4 · Tu estilo

| # | Pregunta | Tipo | Campo |
|---|---|---|---|
| 17 | Elige una paleta o "Quiero mis propios colores" | Opción única con imagen: Rosa y olivo · Rosa Barbie y oro · Azul y plata · Vino y oro · Lavanda y salvia · Esmeralda y oro · Champaña y café · Rojo y negro · Azul cielo y perla · Durazno y terracota · Quiero mis propios colores | `colores.paleta` |
| 18 | *Solo si eligió sus colores:* ¿Cuál es tu color principal? (nombre o código, ej. "lila", #B57EDC) | Texto corto | `colores.principal` |
| 19 | *Solo si eligió sus colores:* ¿Y el color que lo acompaña? | Texto corto | `colores.secundario` |
| 20 | ¿Hay algún detalle, tema o idea que quieras? (mariposas, flores, estilo vintage, una canción, una frase…) | Texto largo · opcional | `textos` / notas |
| 21 | Código de vestimenta | Opción única: Formal · Etiqueta rigurosa · Casual elegante · Temático (explica) · No aplica | `vestimenta.tipo` |
| 22 | Colores que los invitados deben evitar | Texto corto · opcional | `vestimenta.evitar` |

## Página 5 · Fotos y música

| # | Pregunta | Tipo | Campo |
|---|---|---|---|
| 23 | Foto principal (vertical, de buena calidad) | Subir archivo · 1 · obligatoria | `fotos.portada` |
| 24 | *Solo Clásica/Premium:* Fotos para la galería (Clásica hasta 8, Premium hasta 16) | Subir archivo · varios | `galeria` |
| 25 | *Solo Clásica/Premium:* Canción de fondo (nombre y artista, o sube el MP3) | Texto corto + archivo | `musica` |

## Página 6 · Su historia (solo Clásica y Premium)

| # | Pregunta | Tipo | Campo |
|---|---|---|---|
| 26 | Cuéntanos su historia con tus palabras: cómo es, qué le gusta, anécdotas. Nosotros la redactamos bonito | Texto largo | `historia` |
| 27 | *Solo Premium:* Una frase especial para la foto destacada | Texto corto · opcional | `frase_destacada` |

## Página 7 · Regalos, hospedaje y confirmación

| # | Pregunta | Tipo | Campo |
|---|---|---|---|
| 28 | ¿Cómo recibirás regalos? | Opción única: Lluvia de sobres · Mesa de regalos · Transferencia · Ambos · No mostrar | `regalos.tipo` |
| 29 | *Si eligió mesa o tiendas:* ¿En qué tiendas? (Liverpool, Amazon, número de evento…) | Texto corto | `regalos.tiendas` |
| 30 | *Si eligió transferencia:* Datos para transferencia: banco, titular y CLABE. **Te recomendamos dar solo la CLABE; nunca el número de tarjeta.** | Texto largo | `regalos.banco` |
| 31 | *Solo Clásica/Premium:* Hoteles cercanos que recomiendas | Texto largo · opcional | `hospedaje` |
| 32 | Número de WhatsApp donde recibirás las confirmaciones | Teléfono (obligatorio) | `rsvp.whatsapp` |
| 33 | Fecha límite para confirmar | Fecha (obligatoria) | `rsvp.fecha_limite` |
| 34 | *Solo Premium:* Link del álbum para fotos de invitados (Google Fotos/iCloud) o lo dejamos a tu WhatsApp | Link · opcional | `fotos_invitados_link` |
| 35 | Hashtag (opcional) | Texto corto | `hashtag` |

## Página final

| # | Pregunta | Tipo |
|---|---|---|
| 36 | Acepto el aviso de privacidad y que mis fotos se publiquen en mi invitación | Casilla obligatoria |
| 37 | ¿Podemos mostrar tu invitación como ejemplo en nuestras redes? | Sí / No |

**Mensaje de agradecimiento:** "¡Gracias! 💛 En menos de 24 horas te escribimos por WhatsApp con tu cotización final y los datos para el anticipo del 50%. Tu invitación estará lista 72 horas después del anticipo."
