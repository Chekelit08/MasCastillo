#!/usr/bin/env python3
"""Agenda 2027 MasCastillo — tapa y contratapa (3 ideas).

Formato A4 apaisado (297 x 210 mm) + 3 mm de sangrado, como el interior
compaginado (fuente/A4_Interior_Compaginado.pdf), que no cambia.
Salida por idea: SVG tapa/contratapa (texto editable, capas con nombre),
PDF de imprenta de 2 páginas (tapa, contratapa) con TrimBox y PNG de vista
previa; además un SVG único con las 3 ideas y una lámina de presentación.
"""
import io
import os
import re
import subprocess

import cairosvg
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "ideas")

# ---------------------------------------------------------------- marca
NARANJA = "#F7931E"       # sRGB oficial
NARANJA_LINEA = "#B97E2B"  # solo para la ilustración del castillo
NEGRO = "#000000"
BLANCO = "#FFFFFF"

W, H, B = 297.0, 210.0, 3.0
FW, FH = W + 2 * B, H + 2 * B

ANIO = "2027"
CITA = "MATEO 7:12"
# Reina-Valera 1960
REGLA_RVR = ["Así que, todas las cosas que", "queráis que los hombres hagan",
             "con vosotros, así también", "haced vosotros con ellos."]
# como lo dijo el cliente, en voseo
REGLA_VOS = ["Todo lo que querés", "que los hombres hagan", "con vos, eso hacé",
             "con los hombres."]


# ================================================================ recursos
def _logo():
    """Logo apilado oficial; grupos: mas, castillo, claim (2 líneas)."""
    s = open(os.path.join(HERE, "logos", "mascastillo-apilado-sobre-naranja.svg")).read()
    gs = re.findall(r"(<g transform=\"[^\"]*\">.*?</g>)", s, flags=re.S)
    return {"mas": gs[0], "castillo": gs[1], "claim": gs[2] + gs[3]}


LOGO = _logo()
LVX, LVY, LVW, LVH = 141.0, 329.0, 717.0, 376.0


def logo_h(w):
    return w * LVH / LVW


def g_logo(x, y, w, c_mas, c_cast, c_claim, gid="Logo"):
    k = w / LVW
    tint = lambda frag, c: re.sub(r'fill="#[0-9a-fA-F]{6}"', f'fill="{c}"', frag)
    return (f'<g id="{gid}" transform="translate({x:.3f} {y:.3f}) scale({k:.6f}) '
            f'translate({-LVX} {-LVY})">'
            f'<g id="{gid}-mas">{tint(LOGO["mas"], c_mas)}</g>'
            f'<g id="{gid}-castillo">{tint(LOGO["castillo"], c_cast)}</g>'
            f'<g id="{gid}-claim">{tint(LOGO["claim"], c_claim)}</g></g>')


def _castillo_d():
    tmp = "/tmp/_agenda_castillo.svg"
    subprocess.run(["pdftocairo", "-svg", os.path.join(HERE, "fuente", "Portada-castillo.ai"), tmp],
                   check=True)
    d = " ".join(re.findall(r'<path[^>]*d="([^"]*)"', open(tmp).read()))
    return re.sub(r"-?\d+\.\d+", lambda m: f"{float(m.group()):.1f}", d)


CAST_D = _castillo_d()


def castillo(x, y, w, color, op, gid="Castillo"):
    k = w / 1920.0
    return (f'<g id="{gid}" transform="translate({x:.3f} {y:.3f}) scale({k:.6f})">'
            f'<path fill="{color}" fill-opacity="{op}" d="{CAST_D}"/></g>')


def textura(x0, x1, op=0.35, color=NARANJA_LINEA):
    """Castillo como textura, apoyado en el pie, entre x0 y x1."""
    w = (x1 - x0) + 10
    h = w * 1020 / 1920
    return castillo(x0 - 5, FH - h + 4, w, color, op)


def T(x, y, s, size, fill, family="Nunito Sans", weight=700, ls=0.0, anchor="start", gid=None):
    i = f' id="{gid}"' if gid else ""
    return (f'<text{i} x="{x:.3f}" y="{y:.3f}" font-family="{family}" font-weight="{weight}" '
            f'font-size="{size}" fill="{fill}" letter-spacing="{ls}" text-anchor="{anchor}">{s}</text>')


def parrafo(x, y, lineas, size, lh, fill, family="Nunito", weight=800, anchor="start", gid="Regla"):
    tsp = "".join(f'<tspan x="{x:.3f}" dy="{0 if i == 0 else lh:.3f}">{l}</tspan>'
                  for i, l in enumerate(lineas))
    return (f'<text id="{gid}" x="{x:.3f}" y="{y:.3f}" font-family="{family}" font-weight="{weight}" '
            f'font-size="{size}" fill="{fill}" text-anchor="{anchor}">{tsp}</text>')


def rect(color, x=0, y=0, w=FW, h=FH, gid="Fondo-color", rx=0):
    return (f'<rect id="{gid}" x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
            f'rx="{rx}" fill="{color}"/>')


# ================================================================ IDEA 1 · Franja
# Respeta el armado de la tapa original: franja oscura a la derecha con
# "AGENDA 2027"; el verde pasa a naranja y el logo va en negro.
FR = 52.0  # ancho de la franja (al corte)


def tapa_1():
    fx = FW - B - FR
    lw = 150.0
    cx = fx / 2 + B / 2
    return [
        '<g id="Fondo">', rect(NARANJA), textura(0, fx, 0.30), rect(NEGRO, fx, 0, FW - fx, FH, "Franja"), "</g>",
        g_logo(cx - lw / 2, (FH - logo_h(lw)) / 2, lw, NEGRO, NEGRO, NEGRO),
        '<g id="Agenda">',
        T(fx + FR / 2, FH - B - 30, "AGENDA", 7.5, BLANCO, weight=400, ls=1.2, anchor="middle"),
        T(fx + FR / 2, FH - B - 14, ANIO, 17, NARANJA, family="Nunito", weight=900, anchor="middle"),
        "</g>"]


def contratapa_1():
    fx = B + FR
    cx = fx + (FW - fx) / 2
    return [
        '<g id="Fondo">', rect(NARANJA), textura(fx, FW, 0.30), rect(NEGRO, 0, 0, fx, FH, "Franja"), "</g>",
        T(cx, B + 52, "LA REGLA DE ORO", 5.0, NEGRO, weight=800, ls=1.6, anchor="middle", gid="Titulo"),
        parrafo(cx, B + 76, REGLA_RVR, 13.0, 16.5, NEGRO, anchor="middle"),
        T(cx, B + 76 + 3 * 16.5 + 16, CITA, 5.0, NEGRO, weight=700, ls=1.4, anchor="middle", gid="Cita"),
        g_logo(B + (FR - 36) / 2, FH - B - 14 - logo_h(36), 36, NARANJA, BLANCO, NARANJA, "Logo-chico")]


# ================================================================ IDEA 2 · Logo protagonista
def tapa_2():
    lw = 200.0
    lh = logo_h(lw)
    ly = (FH - lh) / 2 - 14
    pw, ph = 92.0, 17.0
    py = ly + lh + 22
    return [
        '<g id="Fondo">', rect(NARANJA), "</g>",
        g_logo((FW - lw) / 2, ly, lw, NEGRO, NEGRO, NEGRO),
        f'<g id="Pildora">{rect(NEGRO, (FW - pw) / 2, py, pw, ph, "Pildora-fondo", rx=ph / 2)}'
        + T(FW / 2, py + ph / 2 + 2.6, f"AGENDA {ANIO}", 7.5, NARANJA, weight=800, ls=1.4,
            anchor="middle") + "</g>"]


def contratapa_2():
    x = B + 34
    return [
        '<g id="Fondo">', rect(NARANJA), "</g>",
        T(x - 4, B + 82, "“", 70, NEGRO, family="Nunito", weight=900, gid="Comillas"),
        parrafo(x, B + 84, REGLA_RVR, 15.0, 19.0, NEGRO),
        f'<rect id="Linea" x="{x}" y="{B + 84 + 3 * 19 + 12:.3f}" width="18" height="1.2" fill="{NEGRO}"/>',
        T(x, B + 84 + 3 * 19 + 22, CITA, 5.5, NEGRO, weight=800, ls=1.4, gid="Cita"),
        g_logo(FW - B - 22 - 52, FH - B - 18 - logo_h(52), 52, NEGRO, NEGRO, NEGRO, "Logo-chico")]


# ================================================================ IDEA 3 · Castillo + año gigante
def tapa_3():
    return [
        '<g id="Fondo">', rect(NARANJA), textura(0, FW, 0.32), "</g>",
        g_logo(B + 22, B + 20, 92, NEGRO, NEGRO, NEGRO),
        '<g id="Agenda">',
        T(FW - B - 22, FH - B - 84, "agenda", 22, NEGRO, family="Nunito", weight=900, anchor="end"),
        T(FW - B - 18, FH - B - 20, ANIO, 78, NEGRO, family="Nunito", weight=900, ls=-2, anchor="end"),
        "</g>"]


def contratapa_3():
    cw, ch = 196.0, 118.0
    cx, cy = (FW - cw) / 2, (FH - ch) / 2 - 6
    mid = FW / 2
    return [
        '<g id="Fondo">', rect(NARANJA), textura(0, FW, 0.32), "</g>",
        rect(NEGRO, cx, cy, cw, ch, "Placa", rx=10),
        T(mid, cy + 24, "LA REGLA DE ORO", 4.8, NARANJA, weight=800, ls=1.6, anchor="middle", gid="Titulo"),
        parrafo(mid, cy + 46, REGLA_VOS, 13.5, 16.5, BLANCO, anchor="middle"),
        T(mid, cy + 46 + 3 * 16.5 + 17, CITA, 4.8, NARANJA, weight=700, ls=1.4, anchor="middle",
          gid="Cita"),
        g_logo(mid - 22, FH - B - 12 - logo_h(44), 44, NEGRO, NEGRO, NEGRO, "Logo-chico")]


# ================================================================ IDEA 4 · Torres de píldoras
# El castillo dibujado con la forma de píldora de la marca (los trazos
# redondeados de la "ll" de castillo): cada torre es una píldora negra.
def pildoras(x0, base, ancho, gap, alturas, color=NEGRO, gid="Torres"):
    out = [f'<g id="{gid}">']
    for i, h in enumerate(alturas):
        x = x0 + i * (ancho + gap)
        out.append(f'<rect x="{x:.3f}" y="{base - h:.3f}" width="{ancho}" height="{h + 20:.3f}" '
                   f'rx="{ancho / 2}" fill="{color}"/>')
    out.append("</g>")
    return "".join(out)


ALTURAS_4 = [62, 88, 112, 150, 112, 88, 62]


def tapa_4():
    an, gap = 15.0, 5.5
    n = len(ALTURAS_4)
    x0 = FW - B - 16 - (n * an + (n - 1) * gap)
    alta = x0 + 3 * (an + gap)          # la torre más alta lleva el año
    base = FH
    ymid = base - ALTURAS_4[3] + 34       # centro del año, en la parte alta de la torre
    return [
        '<g id="Fondo">', rect(NARANJA), "</g>",
        pildoras(x0, base, an, gap, ALTURAS_4),
        f'<g id="Anio-en-torre" transform="translate({alta + an / 2 + 4.4:.3f} {ymid:.3f}) rotate(-90)">'
        + T(0, 0, ANIO, 12.5, NARANJA, family="Nunito", weight=900, ls=0.5, anchor="middle") + "</g>",
        g_logo(B + 22, B + 20, 84, NEGRO, NEGRO, NEGRO),
        T(B + 20, FH - B - 22, "agenda", 30, NEGRO, family="Nunito", weight=900, gid="Agenda"),
    ]


def contratapa_4():
    an, gap = 8.0, 3.0
    alturas = [h * 0.42 for h in ALTURAS_4]   # el mismo castillo de la tapa, en chico
    n = len(alturas)
    tot = n * an + (n - 1) * gap
    x0 = (FW - tot) / 2
    mid = FW / 2
    pw, ph = 74.0, 11.0
    return [
        '<g id="Fondo">', rect(NARANJA), "</g>",
        pildoras(x0, FH, an, gap, alturas, gid="Castillo-chico"),
        f'<g id="Etiqueta">{rect(NEGRO, mid - pw / 2, B + 26, pw, ph, "Etiqueta-fondo", rx=ph / 2)}'
        + T(mid + 0.5, B + 26 + ph / 2 + 1.75, "LA REGLA DE ORO", 4.8, NARANJA, weight=800, ls=1.0,
            anchor="middle") + "</g>",
        parrafo(mid, B + 66, REGLA_VOS, 15.5, 18.5, NEGRO, weight=900, anchor="middle"),
        T(mid, B + 66 + 3 * 18.5 + 15, CITA, 5.0, NEGRO, weight=800, ls=1.5, anchor="middle", gid="Cita"),
        g_logo(FW - B - 16 - 34, B + 14, 34, NEGRO, NEGRO, NEGRO, "Logo-chico"),
    ]


IDEAS = [
    (1, "01-franja", "Franja — como la original: franja negra con AGENDA 2027", tapa_1, contratapa_1),
    (2, "02-logo-grande", "Logo protagonista — naranja pleno, logo gigante y píldora", tapa_2, contratapa_2),
    (3, "03-castillo", "Castillo — textura de castillo y 2027 gigante", tapa_3, contratapa_3),
    (4, "04-torres", "Torres — el castillo hecho con las píldoras de la marca", tapa_4, contratapa_4),
]


# ================================================================ salida
def svg_doc(body, title, w=FW, h=FH):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">\n<title>{title}</title>\n'
            + "\n".join(body) + "\n</svg>\n")


def guias():
    return (f'<g id="Guias-NO-IMPRIMIR" fill="none" stroke="#FF00FF" stroke-width="0.2">'
            f'<rect x="{B}" y="{B}" width="{W}" height="{H}"/>'
            f'<rect x="{B+10}" y="{B+10}" width="{W-20}" height="{H-20}" stroke-dasharray="1 1"/></g>')


def main():
    os.makedirs(OUT, exist_ok=True)
    for n, slug, nombre, ft, fc in IDEAS:
        d = os.path.join(OUT, slug)
        os.makedirs(d, exist_ok=True)
        pdf = PdfWriter()
        for cara, fn in (("tapa", ft), ("contratapa", fc)):
            body = fn()
            limpio = svg_doc(body, f"Agenda MasCastillo {slug} {cara}")
            open(os.path.join(d, f"{cara}.svg"), "w").write(
                svg_doc(body + [guias()], f"Agenda MasCastillo {slug} {cara}"))
            img = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=limpio.encode(),
                                                         output_width=int(FW * 6))))
            k = img.width / FW
            img.crop((int(B * k), int(B * k), int((B + W) * k), int((B + H) * k))).save(
                os.path.join(d, f"preview-{cara}.png"))
            tmp = f"/tmp/_agenda_{slug}_{cara}.pdf"
            cairosvg.svg2pdf(bytestring=limpio.encode(), write_to=tmp)
            pg = PdfReader(tmp).pages[0]
            mm = 72 / 25.4
            pw, ph = float(pg.mediabox.width), float(pg.mediabox.height)
            pg.bleedbox = RectangleObject([0, 0, pw, ph])
            pg.trimbox = RectangleObject([B * mm, B * mm, pw - B * mm, ph - B * mm])
            pdf.add_page(pg)
        pdf.add_metadata({"/Title": f"Agenda 2027 MasCastillo — {nombre}"})
        pdf.write(os.path.join(d, f"Agenda-MasCastillo-{slug}-tapa-contratapa.pdf"))
        print("ok", slug)
    lamina()
    svg_unico()
    pliego(1)   # la elegida por el cliente


def lamina():
    S = 3
    cw, ch = int(W * S), int(H * S)
    pad, gap, head = 50, 30, 60
    sheet = Image.new("RGB", (pad * 2 + cw * 2 + gap, pad + len(IDEAS) * (head + ch + gap)), (232, 230, 226))
    dr = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(os.path.join(HERE, "fuentes", "NunitoSans-800.ttf"), 30)
    y = pad
    for n, slug, nombre, *_ in IDEAS:
        dr.text((pad, y), f"Idea {n} · {nombre}", font=f, fill=(0, 0, 0))
        y += head
        for i, cara in enumerate(("tapa", "contratapa")):
            im = Image.open(os.path.join(OUT, slug, f"preview-{cara}.png")).resize((cw, ch), Image.LANCZOS)
            x = pad + i * (cw + gap)
            sheet.paste(Image.new("RGB", (cw, ch), (200, 198, 194)), (x + 6, y + 8))
            sheet.paste(im, (x, y))
        y += ch + gap
    sheet.save(os.path.join(OUT, "Agenda-MasCastillo-ideas.png"))
    sheet.save(os.path.join(OUT, "Agenda-MasCastillo-ideas.pdf"), resolution=110)


def svg_unico():
    gap, head, m = 20.0, 16.0, 15.0
    tw = m * 2 + FW * 2 + gap
    th = m + len(IDEAS) * (head + FH + gap) - gap + m
    out, tit, gu = [], [], []
    y = m
    for n, slug, nombre, ft, fc in IDEAS:
        tit.append(T(m, y + 9, f"Idea {n} · {nombre}", 7, NEGRO, weight=800))
        y += head
        for i, (cara, fn) in enumerate((("Tapa", ft), ("Contratapa", fc))):
            x = m + i * (FW + gap)
            pre = f"Idea{n}-{cara}"
            body = re.sub(r'id="([^"]+)"', lambda mm: f'id="{pre}-{mm.group(1)}"', "\n".join(fn()))
            out.append(f'<clipPath id="{pre}-clip"><rect width="{FW}" height="{FH}"/></clipPath>')
            out.append(f'<g id="{pre}" transform="translate({x:.3f} {y:.3f})">'
                       f'<g clip-path="url(#{pre}-clip)">{body}</g></g>')
            gu.append(f'<rect x="{x+B:.3f}" y="{y+B:.3f}" width="{W}" height="{H}"/>')
        y += FH + gap
    body = [f'<g id="Mesa">{rect("#E8E6E2", 0, 0, tw, th, "Mesa-fondo")}</g>',
            '<g id="Tapas">' + "".join(out) + "</g>", '<g id="Titulos">' + "".join(tit) + "</g>",
            '<g id="Guias-NO-IMPRIMIR" fill="none" stroke="#FF00FF" stroke-width="0.2">' + "".join(gu) + "</g>"]
    open(os.path.join(OUT, "Agenda-MasCastillo-3-ideas.svg"), "w").write(
        svg_doc(body, "Agenda MasCastillo 3 ideas", tw, th))


# ================================================================ pliego para la gráfica
# Las dos tapas en una sola tirada: tapa arriba, contratapa abajo, cada una
# con su sangrado (doble corte en el medio), marcas de corte y rótulos fuera
# del corte. 319 x 448 mm: entra en un pliego SRA3 (320 x 450).
M_PL = 8.0  # margen para marcas y rótulos


def pliego(idea):
    n, slug, nombre, ft, fc = next(i for i in IDEAS if i[0] == idea)
    pw, ph = FW + 2 * M_PL, 2 * FH + 2 * M_PL
    body = [rect(BLANCO, 0, 0, pw, ph, "Pliego-fondo")]
    for k, (cara, fn) in enumerate((("Tapa", ft), ("Contratapa", fc))):
        oy = M_PL + k * FH
        pre = f"{cara}"
        b = re.sub(r'id="([^"]+)"', lambda mm: f'id="{pre}-{mm.group(1)}"', "\n".join(fn()))
        body.append(f'<clipPath id="{pre}-clip"><rect width="{FW}" height="{FH}"/></clipPath>')
        body.append(f'<g id="{pre}" transform="translate({M_PL} {oy:.3f})">'
                    f'<g clip-path="url(#{pre}-clip)">{b}</g></g>')
        # rótulo en el margen izquierdo, girado
        cy = oy + FH / 2
        rot = "TAPA · FRENTE" if k == 0 else "CONTRATAPA · DORSO"
        body.append(f'<g transform="translate({M_PL / 2 + 1.2:.3f} {cy:.3f}) rotate(-90)">'
                    + T(0, 0, rot, 3.0, NEGRO, weight=800, ls=0.8, anchor="middle") + "</g>")
    # marcas de corte: bordes externos y doble corte del medio
    x0, x1 = M_PL + B, M_PL + B + W
    ys = [M_PL + B, M_PL + B + H, M_PL + FH + B, M_PL + FH + B + H]
    L, off = 5.0, 0.6
    marcas = []
    for y in ys:
        marcas.append(f"M{x0 - B - off - L:.2f} {y:.2f}H{x0 - B - off:.2f}")
        marcas.append(f"M{x1 + B + off:.2f} {y:.2f}H{x1 + B + off + L:.2f}")
    for x in (x0, x1):
        marcas.append(f"M{x:.2f} {M_PL - off - L + 2:.2f}V{M_PL - off:.2f}")
        marcas.append(f"M{x:.2f} {ph - M_PL + off:.2f}V{ph - M_PL + off + L - 2:.2f}")
    body.append(f'<path id="Marcas-de-corte" fill="none" stroke="{NEGRO}" stroke-width="0.25" '
                f'd="{"".join(marcas)}"/>')
    body.append(T(pw / 2, M_PL - 3.2, f"AGENDA 2027 MASCASTILLO · {nombre.split(' — ')[0].upper()} · "
                  f"2 TAPAS A4 APAISADO 297 × 210 MM · SANGRADO 3 MM · DOBLE CORTE AL MEDIO",
                  2.2, NEGRO, weight=700, ls=0.3, anchor="middle"))
    svg = svg_doc(body, f"Agenda MasCastillo pliego {slug}", pw, ph)
    d = os.path.join(OUT, slug)
    open(os.path.join(d, f"Agenda-MasCastillo-{slug}-pliego-vertical.svg"), "w").write(svg)
    cairosvg.svg2pdf(bytestring=svg.encode(),
                     write_to=os.path.join(d, f"Agenda-MasCastillo-{slug}-pliego-vertical.pdf"))
    cairosvg.svg2png(bytestring=svg.encode(), output_width=int(pw * 5),
                     write_to=os.path.join(d, f"preview-pliego-vertical.png"))


if __name__ == "__main__":
    main()
