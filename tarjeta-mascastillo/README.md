# Tarjetas MasCastillo — 10 variantes

Cada opción tiene un frente y un dorso. Medida: **90 × 50 mm** al corte (la opción 10 es vertical, **50 × 90 mm**), con **3 mm de sangrado** por lado.

- **Logo:** vectorial original, tomado de `fuente/MasCastillo-Perfil.ai`. Está separado en las partes "más", "castillo", "PROFESIONALIZAMOS" y "TU MARCA", así cada una se puede colorear por separado.
- **Castillo:** es el dibujo vectorial original de `fuente/Portada-castillo.ai` (628 trazos), así que se puede recolorear.
- **Colores:** naranja `#F5921E`, línea del castillo `#CE7F1C`, negro de la web `#0B0B10`, píldoras `#16161D` y blanco.
- **Tipografías:** Inter (datos) y Montserrat (frases). Están en `fuentes/`.
- **QR:** es vectorial y lleva a **https://mascastillo.com/qr**. Tiene corrección de errores H y el "más" en el centro, y se verificó que se lee. ⚠️ La página `/qr` todavía no existe: hay que crearla (o armar una redirección) antes de imprimir.
- **Datos:** WhatsApp 11 3768 2397 · hola@mascastillo.com · @mascastillo.ok · mascastillo.com

## Archivos
- `opciones/MasCastillo-tarjetas-todas.svg`: **un solo SVG con las 10 opciones** (frente y dorso por fila). Cada tarjeta es un grupo de recorte con su sangrado, y la capa `Guias-NO-IMPRIMIR` marca el corte y la zona segura.
- `opciones/NN-nombre/`: `frente.svg`, `dorso.svg`, el PDF de imprenta de 2 páginas (con TrimBox) y las vistas previas en PNG.
- `opciones/MasCastillo-tarjetas-presentacion.png` / `.pdf`: la lámina para mostrar.

## Opciones
1. **Castillo naranja:** la portada como fondo. El dorso es naranja.
2. **Noche:** castillo naranja sobre negro. El dorso usa las píldoras de contacto de la web.
3. **Horizonte:** el castillo cambia de color al cruzar al suelo negro. El dorso tiene un bloque naranja con el QR.
4. **Torre:** zoom al dibujo y el logo en un chip negro. El dorso es editorial, con la frase "Profesionalizamos tu marca."
5. **Minimal:** fondo blanco con el castillo naranja. El dorso es naranja.
6. **Web:** negro con brillo. El dorso está dividido en naranja y negro, con los íconos de cada red.
7. **Portal:** el castillo se ve a través de un arco. El dorso es blanco con un QR grande.
8. **Tipográfica:** "más castillo" gigante, tono sobre tono.
9. **Almenas:** una muralla almenada naranja sobre negro.
10. **Vertical:** formato 50 × 90 mm con un QR grande.

## Antes de imprenta
Pasar el texto a contornos, convertir a CMYK y crear la página mascastillo.com/qr.

## Regenerar
`python3 generar.py` (requiere cairosvg, segno, pypdf, pillow y `pdftocairo`).
