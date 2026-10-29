#!/usr/bin/env python3
"""Tarjetas MasCastillo — 10 variantes (frente + dorso).

Salida por opción: SVG frente/dorso (capas con nombre, texto editable),
PDF de imprenta de 2 páginas (sangrado + TrimBox) y PNG de vista previa.
Además: un SVG único con todas las opciones y láminas de presentación.

Medida: 90 x 50 mm al corte (la 10 es vertical, 50 x 90) + 3 mm de sangrado.
"""
import io
import math
import os
import re
import subprocess

import cairosvg
import segno
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "fuente")
OUT = os.path.join(HERE, "opciones")

# ---------------------------------------------------------------- datos
WHATSAPP = "11 3768 2397"
MAIL = "hola@mascastillo.com"
INSTAGRAM = "@mascastillo.ok"
WEB = "mascastillo.com"
URL_QR = "https://mascastillo.com/qr"
CONTACTOS = [("wa", "WhatsApp", WHATSAPP), ("mail", "Email", MAIL),
             ("ig", "Instagram", INSTAGRAM), ("web", "Web", WEB)]

# ---------------------------------------------------------------- marca
NARANJA = "#F5921E"     # naranja del logo / portada
NARANJA_O = "#CE7F1C"   # línea del dibujo del castillo
NARANJA_L = "#DE912F"   # fondo del logo
NEGRO = "#0B0B10"       # fondo de la web
NEGRO_2 = "#16161D"     # píldoras de la web
BORDE = "#3A3A44"
GRIS = "#8A8A96"
BLANCO = "#FFFFFF"
VERDE_WA = "#25D366"

B = 3.0  # sangrado (mm)


# ================================================================ recursos
def _castillo_d():
    tmp = "/tmp/_mc_portada.svg"
    subprocess.run(["pdftocairo", "-svg", os.path.join(SRC, "Portada-castillo.ai"), tmp],
                   check=True)
    s = open(tmp).read()
    ds = re.findall(r'<path[^>]*d="([^"]*)"', s)
    d = " ".join(ds)
    # 1 decimal alcanza (el dibujo mide 1920 unidades) y aliviana el archivo
    return re.sub(r"-?\d+\.\d+", lambda m: f"{float(m.group()):.1f}", d)


CAST_D = _castillo_d()
CAST_W, CAST_H = 1920.0, 1020.0
def _logo():
    """Logo vectorial original (MasCastillo-Perfil.ai, pág. 1), separado en partes."""
    tmp = "/tmp/_mc_logo.svg"
    subprocess.run(["pdftocairo", "-svg", "-f", "1", "-l", "1",
                    os.path.join(SRC, "MasCastillo-Perfil.ai"), tmp], check=True)
    ds = re.findall(r'<path[^>]*d="([^"]*)"', open(tmp).read())[:35]  # el .ai lo trae duplicado
    partes = {"mas": ds[0:3], "castillo": ds[3:11], "tag1": ds[11:28], "tag2": ds[28:35]}
    logo = {}
    for k, lst in partes.items():
        nums = [float(v) for d in lst for v in re.findall(r"-?\d+\.?\d*", d)]
        xs, ys = nums[0::2], nums[1::2]
        logo[k] = " ".join(lst)
        logo[k + "_bbox"] = (min(xs), min(ys), max(xs), max(ys))
    return logo


LOGO = _logo()
LX0, LY0 = LOGO["mas_bbox"][0], LOGO["mas_bbox"][1]
LX1 = LOGO["castillo_bbox"][2]
LY1_TAG, LY1_SIN = LOGO["tag2_bbox"][3], LOGO["castillo_bbox"][3]


def g_castillo(x, y, w, color, op=1.0, gid="Castillo"):
    k = w / CAST_W
    return (f'<g id="{gid}" transform="translate({x:.3f} {y:.3f}) scale({k:.6f})">'
            f'<path fill="{color}" fill-opacity="{op}" d="{CAST_D}"/></g>')


def logo_h(w, tag=True):
    return w * ((LY1_TAG if tag else LY1_SIN) - LY0) / (LX1 - LX0)


def g_logo(x, y, w, c_mas, c_cast, c_t1=None, c_t2=None, tag=True, gid="Logo"):
    k = w / (LX1 - LX0)
    out = [f'<g id="{gid}" transform="translate({x:.3f} {y:.3f}) scale({k:.6f}) '
           f'translate({-LX0} {-LY0})">',
           f'<path id="{gid}-mas" fill="{c_mas}" d="{LOGO["mas"]}"/>',
           f'<path id="{gid}-castillo" fill="{c_cast}" d="{LOGO["castillo"]}"/>']
    if tag:
        out += [f'<path id="{gid}-profesionalizamos" fill="{c_t1}" d="{LOGO["tag1"]}"/>',
                f'<path id="{gid}-tu-marca" fill="{c_t2}" d="{LOGO["tag2"]}"/>']
    out.append("</g>")
    return "".join(out)


def g_palabra(key, x, y, w, color, op=1.0, gid=None):
    """Una palabra del logo sola ('mas' o 'castillo'), escalada a ancho w."""
    x0, y0, x1, y1 = LOGO[key + "_bbox"]
    k = w / (x1 - x0)
    gid = gid or f"Palabra-{key}"
    return (f'<g id="{gid}" transform="translate({x:.3f} {y:.3f}) scale({k:.6f}) '
            f'translate({-x0} {-y0})"><path fill="{color}" fill-opacity="{op}" '
            f'd="{LOGO[key]}"/></g>')


def palabra_h(key, w):
    x0, y0, x1, y1 = LOGO[key + "_bbox"]
    return w * (y1 - y0) / (x1 - x0)


# ================================================================ QR
def _rrect(x, y, w, h, r):
    return (f"M{x+r:.3f} {y:.3f}H{x+w-r:.3f}A{r:.3f} {r:.3f} 0 0 1 {x+w:.3f} {y+r:.3f}"
            f"V{y+h-r:.3f}A{r:.3f} {r:.3f} 0 0 1 {x+w-r:.3f} {y+h:.3f}"
            f"H{x+r:.3f}A{r:.3f} {r:.3f} 0 0 1 {x:.3f} {y+h-r:.3f}"
            f"V{y+r:.3f}A{r:.3f} {r:.3f} 0 0 1 {x+r:.3f} {y:.3f}Z")


def g_qr(x, y, size, color, fondo, centro=NARANJA, pad=1.4, gid="QR"):
    """QR vectorial a mascastillo.com/qr, ojos redondeados y 'más' al centro."""
    qr = segno.make(URL_QR, error="h", boost_error=False, version=4)
    m = [list(r) for r in qr.matrix]
    n = len(m)
    q = size / n
    eyes = [(0, 0), (n - 7, 0), (0, n - 7)]
    hole, h0 = 7, (n - 7) // 2
    rects = []
    for r in range(n):
        for c in range(n):
            if not m[r][c]:
                continue
            if any(er <= r < er + 7 and ec <= c < ec + 7 for ec, er in eyes):
                continue
            if h0 <= r < h0 + hole and h0 <= c < h0 + hole:
                continue
            rects.append(f"M{c*q:.3f} {r*q:.3f}h{q:.3f}v{q:.3f}h{-q:.3f}z")
    out = [f'<g id="{gid}" transform="translate({x:.3f} {y:.3f})">',
           f'<rect id="{gid}-fondo" x="{-pad}" y="{-pad}" width="{size+2*pad:.3f}" '
           f'height="{size+2*pad:.3f}" rx="1.6" fill="{fondo}"/>',
           f'<path id="{gid}-modulos" fill="{color}" d="{"".join(rects)}"/>']
    for ec, er in eyes:
        ox, oy = ec * q, er * q
        out.append(f'<path fill="{color}" fill-rule="evenodd" d="{_rrect(ox, oy, 7*q, 7*q, 2*q)}'
                   f'{_rrect(ox+q, oy+q, 5*q, 5*q, 1.3*q)}"/>')
        out.append(f'<rect fill="{color}" x="{ox+2*q:.3f}" y="{oy+2*q:.3f}" width="{3*q:.3f}" '
                   f'height="{3*q:.3f}" rx="{0.8*q:.3f}"/>')
    cs = hole * q * 0.86
    c0 = (h0 + hole / 2) * q - cs / 2
    out.append(f'<rect x="{c0:.3f}" y="{c0:.3f}" width="{cs:.3f}" height="{cs:.3f}" '
               f'rx="{cs*0.22:.3f}" fill="{centro}"/>')
    mw = cs * 0.74
    out.append(g_palabra("mas", c0 + (cs - mw) / 2, c0 + (cs - palabra_h("mas", mw)) / 2 + cs * 0.03,
                         mw, BLANCO, gid=f"{gid}-mas"))
    out.append("</g>")
    return "\n".join(out)


# ================================================================ íconos (24 x 24)
_CIRC = lambda cx, cy, r: (f"M{cx-r} {cy}a{r} {r} 0 1 0 {2*r} 0a{r} {r} 0 1 0 {-2*r} 0Z")
ICON = {
    "mail": "M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z",
    "web": "M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zm6.93 6h-2.95c-.32-1.25-.78-2.45-1.38-3.56 1.84.63 3.37 1.91 4.33 3.56zM12 4.04c.83 1.2 1.48 2.53 1.91 3.96h-3.82c.43-1.43 1.08-2.76 1.91-3.96zM4.26 14C4.1 13.36 4 12.69 4 12s.1-1.36.26-2h3.38c-.08.66-.14 1.32-.14 2 0 .68.06 1.34.14 2H4.26zm.82 2h2.95c.32 1.25.78 2.45 1.38 3.56-1.84-.63-3.37-1.9-4.33-3.56zm2.95-8H5.08c.96-1.66 2.49-2.93 4.33-3.56C8.81 5.55 8.35 6.75 8.03 8zM12 19.96c-.83-1.2-1.48-2.53-1.91-3.96h3.82c-.43 1.43-1.08 2.76-1.91 3.96zM14.34 14H9.66c-.09-.66-.16-1.32-.16-2 0-.68.07-1.35.16-2h4.68c.09.65.16 1.32.16 2 0 .68-.07 1.34-.16 2zm.25 5.56c.6-1.11 1.06-2.31 1.38-3.56h2.95c-.96 1.65-2.49 2.93-4.33 3.56zM16.36 14c.08-.66.14-1.32.14-2 0-.68-.06-1.34-.14-2h3.38c.16.64.26 1.31.26 2s-.1 1.36-.26 2h-3.38z",
    "ig": (_rrect(3, 3, 18, 18, 5.2) + _rrect(4.9, 4.9, 14.2, 14.2, 3.6)
           + _CIRC(12, 12, 4.4) + _CIRC(12, 12, 2.6) + _CIRC(17.2, 6.8, 1.15)),
    # globo de diálogo (anillo + cola) con tubo de teléfono
    "wa": (_CIRC(12.2, 11.6, 9.2) + _CIRC(12.2, 11.6, 7.4)
           + "M4.9 16.3L2.6 21.6L8.2 19.9L7.2 18.2Z"
           + "M9.0 7.0c.3-.3.8-.3 1 .1l1 1.9c.2.3.1.7-.1 1l-.7.7c.6 1.3 1.6 2.3 2.9 2.9l.7-.7"
             "c.3-.3.7-.3 1-.1l1.9 1c.4.2.4.7.1 1l-.9.9c-.6.6-1.6.7-2.4.3-2.1-1-3.8-2.7-4.8-4.8"
             "-.4-.8-.3-1.8.3-2.4z"),
}


def g_icono(key, cx, cy, r, fondo, glyph, gid=None):
    """Ícono en círculo. fondo='marca' usa los colores de cada red."""
    defs = ""
    if fondo == "marca":
        if key == "ig":
            gidg = f"igg{abs(hash((cx, cy))) % 10**6}"
            defs = (f'<linearGradient id="{gidg}" x1="0" y1="1" x2="1" y2="0">'
                    f'<stop offset="0" stop-color="#F9A23A"/><stop offset="0.5" stop-color="#E1306C"/>'
                    f'<stop offset="1" stop-color="#8A3AB9"/></linearGradient>')
            fondo = f"url(#{gidg})"
        elif key == "wa":
            fondo = VERDE_WA
        else:
            fondo = "#23232D"
    s = r * 1.12 / 24
    rule = ' fill-rule="evenodd"' if key in ("ig", "wa") else ""
    return (f'<g>{f"<defs>{defs}</defs>" if defs else ""}'
            f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" fill="{fondo}"/>'
            f'<path fill="{glyph}"{rule} transform="translate({cx-12*s:.3f} {cy-12*s:.3f}) '
            f'scale({s:.5f})" d="{ICON[key]}"/></g>')


def T(x, y, s, size, fill, weight=500, family="Inter", ls=0.0, anchor="start", op=1.0):
    return (f'<text x="{x:.3f}" y="{y:.3f}" font-family="{family}" font-weight="{weight}" '
            f'font-size="{size}" fill="{fill}" fill-opacity="{op}" letter-spacing="{ls}" '
            f'text-anchor="{anchor}">{s}</text>')


def filas(x, y, dy, r, c_circ, c_glyph, c_val, c_lab=None, size=2.45, items=CONTACTOS,
          weight=500):
    """Lista de contactos: ícono + (etiqueta chica) + valor."""
    out = ['<g id="Contactos">']
    for i, (k, lab, val) in enumerate(items):
        cy = y + i * dy
        out.append(g_icono(k, x + r, cy, r, c_circ, c_glyph))
        tx = x + 2 * r + 2.0
        if c_lab:
            out.append(T(tx, cy - 0.45, lab, 1.55, c_lab, weight=500))
            out.append(T(tx, cy + 2.15, val, size, c_val, weight=weight))
        else:
            out.append(T(tx, cy + 0.85, val, size, c_val, weight=weight))
    out.append("</g>")
    return out


def pildora(x, y, w, h, key, lab, val, fondo=NEGRO_2, borde=BORDE):
    """Píldora como en la web: ícono de color + etiqueta gris + valor blanco."""
    r = h / 2 - 1.0
    return (f'<g><rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" rx="{h/2:.3f}" '
            f'fill="{fondo}" stroke="{borde}" stroke-width="0.2"/>'
            + g_icono(key, x + 1.0 + r, y + h / 2, r, "marca", BLANCO)
            + T(x + 2 * r + 3.0, y + h / 2 - 0.55, lab, 1.5, GRIS)
            + T(x + 2 * r + 3.0, y + h / 2 + 1.95, val, 2.25, BLANCO, weight=600) + "</g>")


def almenas(y, fw, alto, ancho, color, gid="Almenas"):
    """Borde superior almenado (silueta de muralla) desde y hasta el pie."""
    d = [f"M-1 {y}"]
    x, up = -1.0, True
    while x < fw + 1:
        nx = min(x + ancho, fw + 1)
        if up:
            d.append(f"L{x:.2f} {y-alto:.2f}L{nx:.2f} {y-alto:.2f}L{nx:.2f} {y:.2f}")
        else:
            d.append(f"L{nx:.2f} {y:.2f}")
        x, up = nx, not up
    d.append(f"L{fw+1} 500L-1 500Z")
    return f'<path id="{gid}" fill="{color}" d="{"".join(d)}"/>'


def glow(gid, cx, cy, rx, ry, color, op):
    defs = (f'<radialGradient id="{gid}" cx="0.5" cy="0.5" r="0.5">'
            f'<stop offset="0" stop-color="{color}" stop-opacity="{op}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>')
    return defs, f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#{gid})"/>'


def rect(fw, fh, color, gid="Fondo-color"):
    return f'<rect id="{gid}" x="0" y="0" width="{fw}" height="{fh}" fill="{color}"/>'


# ================================================================ FRENTES
def f01(fw, fh):
    d, g = glow("g1", fw / 2, fh / 2, 34, 18, NARANJA, 0.95)
    lw = 50.0
    return [d], ['<g id="Fondo">', rect(fw, fh, NARANJA),
                 g_castillo(-3, fh - 54.5, 102, NARANJA_O), g, "</g>",
                 g_logo((fw - lw) / 2, (fh - logo_h(lw)) / 2, lw, BLANCO, NEGRO, BLANCO, BLANCO)]


def f02(fw, fh):
    d1, g1 = glow("g2a", fw / 2, fh + 6, 60, 30, NARANJA, 0.45)
    lw = 50.0
    return [d1], ['<g id="Fondo">', rect(fw, fh, NEGRO), g1,
                  g_castillo(-3, fh - 54.5, 102, NARANJA, 0.22), "</g>",
                  g_logo((fw - lw) / 2, (fh - logo_h(lw)) / 2, lw, NARANJA, BLANCO, BLANCO, NARANJA)]


def f03(fw, fh):
    hor = 40.0
    defs = [f'<clipPath id="c3a"><rect x="0" y="0" width="{fw}" height="{hor}"/></clipPath>',
            f'<clipPath id="c3b"><rect x="0" y="{hor}" width="{fw}" height="{fh}"/></clipPath>']
    cx, cy, cw = 36.0, 4.0, 80.0
    lw = 36.0
    return defs, ['<g id="Fondo">', rect(fw, fh, NARANJA),
                  f'<rect id="Suelo" x="0" y="{hor}" width="{fw}" height="{fh-hor}" fill="{NEGRO}"/>',
                  f'<g clip-path="url(#c3a)">{g_castillo(cx, cy, cw, NEGRO, 0.4, "Castillo-cielo")}</g>',
                  f'<g clip-path="url(#c3b)">{g_castillo(cx, cy, cw, NARANJA, 0.9, "Castillo-suelo")}</g>',
                  "</g>",
                  g_logo(B + 5.5, B + 5.0, lw, BLANCO, NEGRO, NEGRO, NEGRO)]


def f04(fw, fh):
    lw = 34.0
    lh = logo_h(lw)
    px, py, pw, ph = B + 4.0, fh - B - 4.0 - (lh + 7.0), lw + 8.0, lh + 7.0
    return [], ['<g id="Fondo">', rect(fw, fh, NARANJA),
                g_castillo(-112, -38, 215, NEGRO, 0.8, "Castillo-zoom"), "</g>",
                f'<rect id="Chip" x="{px}" y="{py}" width="{pw}" height="{ph}" rx="2.2" fill="{NEGRO}"/>',
                g_logo(px + 4.0, py + 3.5, lw, NARANJA, BLANCO, BLANCO, NARANJA)]


def f05(fw, fh):
    lw = 40.0
    return [], ['<g id="Fondo">', rect(fw, fh, BLANCO),
                g_castillo((fw - 70) / 2, fh - 28.5, 70, NARANJA, 0.85), "</g>",
                g_logo((fw - lw) / 2, B + 5.0, lw, NARANJA, NEGRO, NEGRO, NARANJA)]


def f06(fw, fh):
    d1, g1 = glow("g6a", fw * 0.5, fh + 4, 52, 26, NARANJA, 0.55)
    d2, g2 = glow("g6b", fw * 0.95, -4, 30, 18, "#8A3AB9", 0.35)
    lw = 46.0
    lh = logo_h(lw, tag=False)
    body = ['<g id="Fondo">', rect(fw, fh, NEGRO), g1, g2, "</g>",
            g_logo((fw - lw) / 2, (fh - lh) / 2 - 3.5, lw, NARANJA, BLANCO, tag=False),
            f'<rect x="{(fw-38)/2}" y="{fh/2+lh/2+0.8:.3f}" width="38" height="5.6" rx="2.8" '
            f'fill="none" stroke="{BORDE}" stroke-width="0.2"/>',
            T(fw / 2, fh / 2 + lh / 2 + 4.6, "PROFESIONALIZAMOS TU MARCA", 1.65, BLANCO,
              weight=600, family="Montserrat", ls=0.32, anchor="middle")]
    return [d1, d2], body


def f07(fw, fh):
    # portal de castillo (arco) con el dibujo adentro
    ax, aw, top = 52.0, 36.0, 7.0
    r = aw / 2
    arco = f"M{ax} {fh+1}V{top+r}A{r} {r} 0 0 1 {ax+aw} {top+r}V{fh+1}Z"
    defs = [f'<clipPath id="c7"><path d="{arco}"/></clipPath>']
    lw = 38.0
    return defs, ['<g id="Fondo">', rect(fw, fh, NARANJA),
                  f'<path id="Portal" fill="{NEGRO}" d="{arco}"/>',
                  f'<g clip-path="url(#c7)">{g_castillo(-14, 6, 140, NARANJA, 0.85)}</g>',
                  f'<path fill="none" stroke="{BLANCO}" stroke-width="0.35" d="'
                  f'M{ax-2.2} {fh+1}V{top+r}A{r+2.2} {r+2.2} 0 0 1 {ax+aw+2.2} {top+r}V{fh+1}"/>',
                  "</g>",
                  g_logo(B + 5.5, (fh - logo_h(lw)) / 2, lw, BLANCO, NEGRO, BLANCO, BLANCO)]


def f08(fw, fh):
    lw = 46.0
    return [], ['<g id="Fondo">', rect(fw, fh, NARANJA),
                g_palabra("castillo", -10, fh - palabra_h("castillo", 150) + 9, 150, NARANJA_O, 0.75,
                          gid="Castillo-gigante"),
                g_palabra("mas", 50, -10, 70, NARANJA_O, 0.5, gid="Mas-gigante"), "</g>",
                g_logo(B + 6.0, (fh - logo_h(lw)) / 2, lw, BLANCO, NEGRO, BLANCO, BLANCO)]


def f09(fw, fh):
    lw = 44.0
    lh = logo_h(lw, tag=False)
    return [], ['<g id="Fondo">', rect(fw, fh, NEGRO),
                almenas(fh - 13.0, fw, 3.2, 4.6, NARANJA), "</g>",
                g_logo((fw - lw) / 2, 9.5, lw, NARANJA, BLANCO, tag=False),
                T(fw / 2, fh - 6.6, "PROFESIONALIZAMOS TU MARCA", 1.9, NEGRO, weight=700,
                  family="Montserrat", ls=0.35, anchor="middle")]


def f10(fw, fh):  # vertical
    lw = 38.0
    return [], ['<g id="Fondo">', rect(fw, fh, NARANJA),
                g_castillo(-38, fh - 62, 125, NARANJA_O), "</g>",
                g_logo((fw - lw) / 2, B + 10.0, lw, BLANCO, NEGRO, BLANCO, BLANCO)]


# ================================================================ DORSOS
def d01(fw, fh):
    qs = 18.0
    body = ['<g id="Fondo">', rect(fw, fh, NARANJA), g_castillo(-3, fh - 54.5, 102, NARANJA_O, 0.35),
            "</g>",
            g_logo(B + 6, B + 5.5, 24, BLANCO, NEGRO, tag=False)]
    body += filas(B + 6, B + 20.0, 6.4, 2.05, NEGRO, NARANJA, NEGRO, weight=600)
    body.append(g_qr(fw - B - 6 - qs, fh - B - 6.5 - qs, qs, NEGRO, BLANCO))
    return [], body


def d02(fw, fh):
    d1, g1 = glow("g2b", fw * 0.25, fh + 8, 50, 22, NARANJA, 0.28)
    body = ['<g id="Fondo">', rect(fw, fh, NEGRO), g1, "</g>"]
    pw, ph, x = 52.0, 8.6, B + 4.5
    body.append('<g id="Pildoras">')
    for i, (k, lab, val) in enumerate(CONTACTOS[:3]):
        body.append(pildora(x, B + 6.0 + i * 11.0, pw, ph, k, lab, val))
    body.append("</g>")
    qs = 20.0
    qx = fw - B - 6.5 - qs
    body.append(g_qr(qx, B + 6.5, qs, NEGRO, BLANCO))
    body.append(T(qx + qs / 2, B + 34.5, WEB, 2.2, BLANCO, weight=600, anchor="middle"))
    body.append(T(qx + qs / 2, B + 38.0, "ESCANEÁ", 1.45, NARANJA, weight=700, ls=0.35,
                  anchor="middle"))
    return [d1], body


def d03(fw, fh):
    bw = 32.0
    qs = 19.0
    body = ['<g id="Fondo">', rect(fw, fh, BLANCO),
            f'<rect id="Bloque" x="0" y="0" width="{B+bw}" height="{fh}" fill="{NARANJA}"/>',
            g_castillo(-40, fh - 26, 110, NARANJA_O, 0.6).replace(
                'id="Castillo"', 'id="Castillo" clip-path="url(#c3d)"'), "</g>"]
    defs = [f'<clipPath id="c3d"><rect x="0" y="0" width="{(B+bw)/ (110/1920):.1f}" height="2000"/></clipPath>']
    body.append(g_qr(B + (bw - qs) / 2, B + 8.0, qs, NEGRO, BLANCO))
    x = B + bw + 7.0
    body.append(g_logo(x, B + 5.5, 30, NARANJA, NEGRO, tag=False))
    body += filas(x, B + 20.5, 6.6, 1.9, NARANJA, BLANCO, NEGRO, c_lab=GRIS, size=2.35, weight=600)
    return defs, body


def d04(fw, fh):
    body = ['<g id="Fondo">', rect(fw, fh, NEGRO), "</g>"]
    x = B + 6.0
    body.append(T(x, B + 9.5, "Profesionalizamos", 4.1, BLANCO, weight=700, family="Montserrat",
                  ls=-0.08))
    body.append(T(x, B + 14.8, "tu marca.", 4.1, NARANJA, weight=700, family="Montserrat", ls=-0.08))
    body.append('<g id="Contactos">')
    for i, (k, lab, val) in enumerate(CONTACTOS):
        yy = B + 25.5 + i * 5.0
        body.append(T(x, yy, lab.upper(), 1.45, NARANJA, weight=700, ls=0.3))
        body.append(T(x + 13.5, yy, val, 2.4, BLANCO, weight=500))
    body.append("</g>")
    qs = 17.0
    body.append(g_qr(fw - B - 6 - qs, fh - B - 6 - qs, qs, NEGRO, BLANCO))
    body.append(g_palabra("mas", fw - B - 6 - 12, B + 5.5, 12, NARANJA, gid="Mas"))
    return [], body


def d05(fw, fh):
    qs = 19.0
    body = ['<g id="Fondo">', rect(fw, fh, NARANJA), g_castillo(-3, fh - 54.5, 102, BLANCO, 0.18),
            "</g>", g_logo(B + 6, B + 6, 30, BLANCO, NEGRO, tag=False)]
    body += filas(B + 6, B + 22.0, 6.3, 2.0, BLANCO, NARANJA, BLANCO, weight=700)
    body.append(g_qr(fw - B - 7 - qs, (fh - qs) / 2, qs, NEGRO, BLANCO))
    return [], body


def d06(fw, fh):
    sw = 36.0
    qs = 21.0
    body = ['<g id="Fondo">', rect(fw, fh, NEGRO),
            f'<rect id="Bloque" x="0" y="0" width="{B+sw}" height="{fh}" fill="{NARANJA}"/>', "</g>",
            g_qr(B + (sw - qs) / 2, B + 6.5, qs, NEGRO, BLANCO),
            T(B + sw / 2, B + 34.5, "ESCANEÁ Y CONOCENOS", 1.5, NEGRO, weight=700, ls=0.25,
              anchor="middle")]
    body += filas(B + sw + 7.0, B + 10.0, 8.6, 2.1, "marca", BLANCO, BLANCO, c_lab=GRIS, size=2.4,
                  weight=600)
    return [], body


def d07(fw, fh):
    qs = 25.0
    body = ['<g id="Fondo">', rect(fw, fh, BLANCO), "</g>",
            g_qr(B + 6.5, (fh - qs) / 2 - 1.5, qs, NEGRO, BLANCO),
            T(B + 6.5 + qs / 2, (fh + qs) / 2 + 2.6, "ESCANEÁ", 1.6, NARANJA, weight=700, ls=0.4,
              anchor="middle")]
    x = B + 40.0
    body.append(g_logo(x, B + 5.5, 34, NARANJA, NEGRO, NEGRO, NARANJA))
    body.append(f'<rect x="{x}" y="{B+26.2}" width="44" height="0.2" fill="{NEGRO}" opacity="0.2"/>')
    body += filas(x, B + 30.0, 4.8, 1.55, NEGRO, BLANCO, NEGRO, size=2.25, items=CONTACTOS[:3])
    return [], body


def d08(fw, fh):
    qs = 18.0
    body = ['<g id="Fondo">', rect(fw, fh, NEGRO),
            g_palabra("mas", 34, -6, 82, "#1E1E26", gid="Mas-gigante"), "</g>",
            g_logo(B + 6, B + 6, 26, NARANJA, BLANCO, tag=False)]
    body += filas(B + 6, B + 21.5, 6.3, 2.0, NARANJA, NEGRO, BLANCO, weight=600)
    body.append(g_qr(fw - B - 6 - qs, fh - B - 6 - qs, qs, NEGRO, BLANCO))
    return [], body


def d09(fw, fh):
    qs = 18.0
    body = ['<g id="Fondo">', rect(fw, fh, NARANJA),
            almenas(9.0, fw, 3.2, 4.6, NEGRO).replace('M-1 9.0', 'M-1 9.0').replace(
                f"L{fw+1} 500L-1 500Z", f"L{fw+1} -1L-1 -1Z"), "</g>"]
    # almenas invertidas: banda negra arriba
    body += filas(B + 6, B + 16.5, 6.6, 2.05, NEGRO, NARANJA, NEGRO, weight=700)
    body.append(g_qr(fw - B - 6.5 - qs, fh - B - 5.5 - qs, qs, NEGRO, BLANCO))
    return [], body


def d10(fw, fh):  # vertical
    d1, g1 = glow("g10", fw / 2, fh + 6, 40, 30, NARANJA, 0.35)
    qs = 26.0
    body = ['<g id="Fondo">', rect(fw, fh, NEGRO), g1, "</g>",
            g_logo((fw - 22) / 2, B + 5.0, 22, NARANJA, BLANCO, tag=False),
            g_qr((fw - qs) / 2, B + 19.5, qs, NEGRO, BLANCO),
            T(fw / 2, B + 50.3, "ESCANEÁ", 1.6, NARANJA, weight=700, ls=0.4, anchor="middle")]
    body += filas(B + 5.0, B + 57.5, 6.3, 1.9, "marca", BLANCO, BLANCO, size=2.3, weight=600)
    return [d1], body


# ================================================================ opciones
H_, V_ = (90.0, 50.0), (50.0, 90.0)
OPCIONES = [
    (1, "01-castillo-naranja", "Castillo naranja — la portada como fondo", H_, f01, d01),
    (2, "02-noche", "Noche — castillo dorado sobre negro, estilo web", H_, f02, d02),
    (3, "03-horizonte", "Horizonte — el castillo se invierte en el suelo negro", H_, f03, d03),
    (4, "04-torre", "Torre — zoom al dibujo + logo en chip negro", H_, f04, d04),
    (5, "05-minimal", "Minimal — blanca con castillo naranja", H_, f05, d05),
    (6, "06-web", "Web — negro con brillo y píldoras de contacto", H_, f06, d06),
    (7, "07-portal", "Portal — el castillo visto por un arco", H_, f07, d07),
    (8, "08-tipografica", "Tipográfica — 'más castillo' gigante tono sobre tono", H_, f08, d08),
    (9, "09-almenas", "Almenas — muralla naranja sobre negro", H_, f09, d09),
    (10, "10-vertical", "Vertical — formato 50 x 90 con QR grande", V_, f10, d10),
]


def dims(op):
    w, h = op[3]
    return w, h, w + 2 * B, h + 2 * B


def svg_doc(defs, body, fw, fh, title):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{fw}mm" height="{fh}mm" '
            f'viewBox="0 0 {fw} {fh}">\n<title>{title}</title>\n'
            f'<defs>{"".join(defs)}</defs>\n' + "\n".join(body) + "\n</svg>\n")


def guias(w, h):
    return (f'<g id="Guias-NO-IMPRIMIR" fill="none" stroke="#FF00FF" stroke-width="0.1">'
            f'<rect x="{B}" y="{B}" width="{w}" height="{h}"/>'
            f'<rect x="{B+4}" y="{B+4}" width="{w-8}" height="{h-8}" stroke-dasharray="0.6 0.6"/></g>')


def main():
    os.makedirs(OUT, exist_ok=True)
    for op in OPCIONES:
        n, slug, nombre, _, ff, fd = op
        w, h, fw, fh = dims(op)
        d = os.path.join(OUT, slug)
        os.makedirs(d, exist_ok=True)
        pdfw = PdfWriter()
        for cara, fn in (("frente", ff), ("dorso", fd)):
            defs, body = fn(fw, fh)
            limpio = svg_doc(defs, body, fw, fh, f"MasCastillo {slug} {cara}")
            open(os.path.join(d, f"{cara}.svg"), "w").write(
                svg_doc(defs, body + [guias(w, h)], fw, fh, f"MasCastillo {slug} {cara}"))
            img = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=limpio.encode(),
                                                         output_width=int(fw * 12))))
            k = img.width / fw
            img.crop((int(B * k), int(B * k), int((B + w) * k), int((B + h) * k))).save(
                os.path.join(d, f"preview-{cara}.png"))
            tmp = f"/tmp/_mc_{slug}_{cara}.pdf"
            cairosvg.svg2pdf(bytestring=limpio.encode(), write_to=tmp)
            pg = PdfReader(tmp).pages[0]
            mm = 72 / 25.4
            pw, ph = float(pg.mediabox.width), float(pg.mediabox.height)
            pg.bleedbox = RectangleObject([0, 0, pw, ph])
            pg.trimbox = RectangleObject([B * mm, B * mm, pw - B * mm, ph - B * mm])
            pdfw.add_page(pg)
        pdfw.add_metadata({"/Title": f"MasCastillo tarjeta {slug}"})
        pdfw.write(os.path.join(d, f"MasCastillo-tarjeta-{slug}.pdf"))
        print("ok", slug)
    lamina()
    svg_unico()


def lamina():
    S = 8
    pad, gap, head = 60, 36, 70
    hw, hh = int(90 * S), int(50 * S)
    vw, vh = int(50 * S), int(90 * S)
    width = pad * 2 + hw * 2 + gap
    height = pad
    for op in OPCIONES:
        height += head + (vh if op[3] == V_ else hh) + gap
    sheet = Image.new("RGB", (width, height), (232, 230, 226))
    dr = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(os.path.join(HERE, "fuentes", "Montserrat-700.ttf"), 30)
    y = pad
    for op in OPCIONES:
        dr.text((pad, y), f"Opción {op[0]} · {op[2]}", font=f, fill=(20, 20, 24))
        y += head
        cw, ch = (vw, vh) if op[3] == V_ else (hw, hh)
        for i, cara in enumerate(("frente", "dorso")):
            im = Image.open(os.path.join(OUT, op[1], f"preview-{cara}.png")).resize((cw, ch), Image.LANCZOS)
            x = pad + i * (cw + gap)
            sheet.paste(Image.new("RGB", (cw, ch), (200, 198, 194)), (x + 6, y + 8))
            sheet.paste(im, (x, y))
        y += ch + gap
    sheet.save(os.path.join(OUT, "MasCastillo-tarjetas-presentacion.png"))
    sheet.save(os.path.join(OUT, "MasCastillo-tarjetas-presentacion.pdf"), resolution=150)


def _prefijar(defs, body, pre):
    txt = "\n".join(defs) + "\u0000" + "\n".join(body)
    txt = re.sub(r'id="([^"]+)"', lambda m: f'id="{pre}-{m.group(1)}"', txt)
    txt = re.sub(r'url\(#([^)]+)\)', lambda m: f'url(#{pre}-{m.group(1)})', txt)
    return txt.split("\u0000")


def svg_unico():
    """Todas las opciones en un solo SVG (frente | dorso por fila)."""
    gap, head, m = 12.0, 10.0, 10.0
    tw = m * 2 + 96.0 * 2 + gap
    defs, cards, tit, gu = [], [], [], []
    y = m
    for op in OPCIONES:
        w, h, fw, fh = dims(op)
        tit.append(T(m, y + 6.0, f"Opción {op[0]} · {op[2]}", 4.2, NEGRO, weight=700,
                     family="Montserrat"))
        y += head
        for i, (cara, fn) in enumerate((("Frente", op[4]), ("Dorso", op[5]))):
            x = m + i * (fw + gap)
            pre = f"Op{op[0]:02d}-{cara}"
            dd, bb = _prefijar(*fn(fw, fh), pre)
            defs.append(dd)
            defs.append(f'<clipPath id="{pre}-clip"><rect width="{fw}" height="{fh}"/></clipPath>')
            cards.append(f'<g id="{pre}" transform="translate({x:.3f} {y:.3f})">'
                         f'<g clip-path="url(#{pre}-clip)">{bb}</g></g>')
            gu.append(f'<rect x="{x+B:.3f}" y="{y+B:.3f}" width="{w}" height="{h}"/>'
                      f'<rect x="{x+B+4:.3f}" y="{y+B+4:.3f}" width="{w-8}" height="{h-8}" '
                      f'stroke-dasharray="0.6 0.6"/>')
        y += fh + gap
    th = y - gap + m
    svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{tw}mm" height="{th}mm" '
           f'viewBox="0 0 {tw} {th}">\n<title>MasCastillo tarjetas</title>\n'
           f'<defs>{"".join(defs)}</defs>\n'
           f'<g id="Mesa"><rect width="{tw}" height="{th}" fill="#E8E6E2"/></g>\n'
           f'<g id="Tarjetas">{"".join(cards)}</g>\n<g id="Titulos">{"".join(tit)}</g>\n'
           f'<g id="Guias-NO-IMPRIMIR" fill="none" stroke="#FF00FF" stroke-width="0.1">'
           f'{"".join(gu)}</g>\n</svg>\n')
    open(os.path.join(OUT, "MasCastillo-tarjetas-todas.svg"), "w").write(svg)


if __name__ == "__main__":
    main()
