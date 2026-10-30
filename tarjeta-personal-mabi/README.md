# Tarjeta personal — MABI · Miguel Angel Biondi

9 opciones en dos series. La serie 1 son las opciones 1 a 6. Cada una tiene un **frente** (logo grande sobre un fondo abstracto inspirado en la tarjeta de Bagno) y un **dorso** (datos, QR y logo, armado como en Bagno).

- Medida: **90 × 50 mm** al corte, con **3 mm de sangrado** por lado (el archivo mide 96 × 56 mm).
- Colores (los de las piezas de MABI): verde `#063A27`, verde logo `#123F2B`, dorado `#EFA013` y crema `#F5F6F0`.
- Tipografías: **Sora** (nombre) e **Inter** (datos). Las dos son las de mabi.com.ar y están en `fuentes/`. Hay que instalarlas antes de abrir los SVG.
- El QR es vectorial y lleva a https://mabi.com.ar/. Tiene corrección de errores H, con el isotipo en el centro, y se verificó que se puede leer.

## Archivos por opción (`opciones/NN-nombre/`)

| Archivo | Para qué |
|---|---|
| `frente.svg` / `dorso.svg` | **Para trabajar en Illustrator.** El texto es editable y los grupos tienen nombre (Fondo, Fondo-facetas, Logo, QR, Datos). La capa `Guias-NO-IMPRIMIR` marca el corte y la zona segura: hay que borrarla u ocultarla antes de imprimir. |
| `MABI-tarjeta-NN-….pdf` | PDF de imprenta de 2 páginas (frente y dorso) con sangrado, TrimBox y BleedBox. También se abre en Illustrator. |
| `preview-*.png` | Vista previa al corte. |

`opciones/MABI-tarjetas-presentacion.png` (serie 1) y `MABI-tarjetas-presentacion-2.png` (serie 2), cada una también en `.pdf`, son las láminas con todas las opciones. `MABI-tarjeta-final` (PNG y SVG) responde al pedido del cliente: la composición de la 8 con el efecto de facetas de la 1 (opción 11) y una variante híbrida que suma líneas suaves (opción 12). `MABI-tarjetas-seleccion` es la preselección del cliente: opciones 1, 3, 5, 7, 8 y 9. `MABI-tarjetas-seleccion.svg` junta esas 6 opciones, frente y dorso, en un solo archivo para Illustrator para mostrarle al cliente.

## Opciones

1. **Bosque**: fondo verde profundo con un abanico de planos como el de Bagno. El logo va en crema y dorado.
2. **Dorado**: es la versión más parecida a Bagno. El lima pasa a dorado y los planos azules pasan a verde. El logo va en verde.
3. **Bosque + Oro**: haces dorados que cruzan el verde. El dorso es crema y lleva una franja abstracta.
4. **Crema**: fondo claro con prismas verdes y dorados. El dorso está invertido (verde oscuro).
5. **Verde vivo**: el abanico está espejado y tiene una esquina dorada. El dorso lleva una franja.
6. **Manuscrito**: usa el logo web "mabi" (manuscrito) en el frente sobre un abanico verde y dorado.

### Serie 2: conceptos distintos (lámina `MABI-tarjetas-presentacion-2`)
7. **Monograma**: frente crema con el isotipo dorado gigante, recortado por el borde, y el logo en verde abajo a la izquierda. El dorso es verde, con una grilla editorial: el nombre grande en dos colores, etiquetas TEL/MAIL/WEB y el QR en un panel.
8. **Surcos**: frente verde con líneas topográficas doradas que evocan el campo y el viento del isotipo, y el logo a la izquierda. El dorso es crema y repite las mismas líneas en verde suave.
9. **Sol**: frente verde con un arco dorado gigante (un sol sobre el campo), anillos y el isotipo dentro. El dorso va en bloques: datos sobre crema y un panel verde redondeado con el QR y la palabra "ESCANEÁ".

## Antes de imprenta
- Pasar los textos a contornos en Illustrator (Texto → Crear contornos) o mandar las fuentes.
- Convertir a CMYK según el perfil de la imprenta. Los archivos están en RGB (los colores de marca).
- Los logos se sacaron en vectores de `fuente/Mabi-Perfil.ai` y `fuente/Mabi-Logo-Web.ai`.

## Regenerar
`python3 generar.py` (requiere cairosvg, segno, skia-pathops, fonttools, pypdf y pillow, además de `pdftocairo`).
