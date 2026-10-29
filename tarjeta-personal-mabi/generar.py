#!/usr/bin/env python3
"""Genera las opciones de tarjeta personal MABI (frente + dorso).

Salida por opción:  SVG (frente / dorso, capas nombradas, texto editable),
PDF de imprenta de 2 páginas (con sangrado y TrimBox) y PNG de vista previa.

Medidas: 90 x 50 mm al corte + 3 mm de sangrado por lado (96 x 56 mm).
Requiere: cairosvg, segno, skia-pathops, fonttools, pypdf, pillow.
"""
import io
import os
import re
import subprocess

import cairosvg
import pathops
import segno
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.svgLib.path import parse_path
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "fuente")
OUT = os.path.join(HERE, "opciones")

# ---------------------------------------------------------------- datos
NOMBRE = "Miguel Angel Biondi"
EMPRESA = "MABI · Distribución Inteligente"
TEL = "+54 9 11 4940-9319"
MAIL = "mbiondicentral@gmail.com"
WEB = "mabi.com.ar"
URL = "https://mabi.com.ar/"

# ---------------------------------------------------------------- marca
VERDE = "#063A27"      # verde institucional (piezas de redes)
VERDE_2 = "#123F2B"    # verde del logo web
VERDE_M = "#1D5C3F"    # verde medio (derivado, para facetas)
VERDE_C = "#2F7A52"    # verde claro (derivado, para facetas)
ORO = "#EFA013"        # dorado institucional
ORO_C = "#F6C24E"      # dorado claro (derivado)
CREMA = "#F5F6F0"      # crema institucional
BLANCO = "#FFFFFF"

W, H, B = 90.0, 50.0, 3.0          # corte y sangrado (mm)
FW, FH = W + 2 * B, H + 2 * B      # formato con sangrado


# ================================================================ logos
def _paths(svg_file):
    s = open(svg_file).read()
    return [(m.group(1), m.group(2)) for m in
            re.finditer(r'<path[^>]*fill="([^"]*)"[^>]*d="([^"]*)"', s)]


def _sk(d):
    p = pathops.Path()
    parse_path(d, p.getPen())
    return p


def _d(p):
    pen = SVGPathPen(None)
    p.draw(pen)
    return pen.getCommands()


def _pdf_to_svg(ai, page, out):
    subprocess.run(["pdftocairo", "-svg", "-f", str(page), "-l", str(page),
                    ai, out], check=True)


def cargar_logo_mabi():
    """Logo 'MABI · Distribución Inteligente' (Perfil.ai, pág. 1)."""
    tmp = "/tmp/_mabi_perfil.svg"
    _pdf_to_svg(os.path.join(SRC, "Mabi-Perfil.ai"), 1, tmp)
    ps = [d for _, d in _paths(tmp)]
    # 0-11 DISTRIBUCIÓN · 12-22 INTELIGENTE · 23-25 viento · 26 halo blanco
    # 27-30 hojas/ola · 31-34 MABI. El halo blanco recorta las líneas de
    # viento: se resuelve con una resta booleana para que funcione sobre
    # cualquier fondo (sin blancos “tapando”).
    halo = _sk(ps[26])
    viento = []
    for i in (23, 24, 25):
        r = pathops.op(_sk(ps[i]), halo, pathops.PathOp.DIFFERENCE)
        viento.append(_d(r))
    return {
        "isotipo": viento + [ps[i] for i in (27, 28, 29, 30)],
        "mabi": ps[31:35],
        "distribucion": ps[0:12],
        "inteligente": ps[12:23],
        "bbox": (155.7, 292.0, 925.2, 787.3),
    }


def cargar_logo_script():
    """Logo manuscrito 'mabi' (Mabi-Logo-Web.ai)."""
    tmp = "/tmp/_mabi_web.svg"
    _pdf_to_svg(os.path.join(SRC, "Mabi-Logo-Web.ai"), 1, tmp)
    ps = [d for _, d in _paths(tmp)]
    return {"letras": ps[0:2], "hojas": ps[2:5], "bbox": (0.0, 0.0, 462.5, 222.6)}


LOGO = cargar_logo_mabi()
SCRIPT = cargar_logo_script()


def g_logo_mabi(x, y, w, c_iso, c_mabi, c_dist, c_int, layer="Logo"):
    """Logo apilado, esquina sup-izq en (x, y) mm y ancho w mm."""
    x0, y0, x1, y1 = LOGO["bbox"]
    k = w / (x1 - x0)
    out = [f'<g id="{layer}" transform="translate({x:.3f} {y:.3f}) '
           f'scale({k:.6f}) translate({-x0} {-y0})">']
    for name, col in (("isotipo", c_iso), ("mabi", c_mabi),
                      ("distribucion", c_dist), ("inteligente", c_int)):
        out.append(f'<g id="{layer}-{name}" fill="{col}">')
        out += [f'<path d="{d}"/>' for d in LOGO[name]]
        out.append("</g>")
    out.append("</g>")
    return "\n".join(out), (x1 - x0) * k, (y1 - y0) * k


def logo_mabi_h(w):
    x0, y0, x1, y1 = LOGO["bbox"]
    return w * (y1 - y0) / (x1 - x0)


def g_logo_script(x, y, w, c_letras, c_hojas, layer="Logo"):
    x0, y0, x1, y1 = SCRIPT["bbox"]
    k = w / (x1 - x0)
    out = [f'<g id="{layer}" transform="translate({x:.3f} {y:.3f}) scale({k:.6f})">',
           f'<g id="{layer}-letras" fill="{c_letras}">']
    out += [f'<path d="{d}"/>' for d in SCRIPT["letras"]]
    out += ["</g>", f'<g id="{layer}-hojas" fill="{c_hojas}">']
    out += [f'<path d="{d}"/>' for d in SCRIPT["hojas"]]
    out += ["</g>", "</g>"]
    return "\n".join(out)


def logo_script_h(w):
    x0, y0, x1, y1 = SCRIPT["bbox"]
    return w * (y1 - y0) / (x1 - x0)


# ================================================================ QR
QR_VERSION, QR_HUECO = 4, 7   # 33 módulos; hueco central de 7x7 para el isotipo

def g_qr(x, y, size, color, fondo, layer="QR", version=QR_VERSION, hole=QR_HUECO):
    """QR vectorial a mabi.com.ar con ojos redondeados e isotipo al centro."""
    qr = segno.make(URL, error="h", boost_error=False, version=version)
    m = [list(r) for r in qr.matrix]
    n = len(m)
    q = size / n
    rects = []
    eyes = [(0, 0), (n - 7, 0), (0, n - 7)]

    def in_eye(r, c):
        return any(er <= r < er + 7 and ec <= c < ec + 7 for ec, er in eyes)

    # hueco central para el isotipo (cubierto por la corrección H)
    h0 = (n - hole) // 2

    def in_hole(r, c):
        return h0 <= r < h0 + hole and h0 <= c < h0 + hole

    for r in range(n):
        for c in range(n):
            if m[r][c] and not in_eye(r, c) and not in_hole(r, c):
                rects.append(f"M{c*q:.3f} {r*q:.3f}h{q:.3f}v{q:.3f}h{-q:.3f}z")
    out = [f'<g id="{layer}" transform="translate({x:.3f} {y:.3f})">',
           f'<rect id="{layer}-fondo" x="{-q:.3f}" y="{-q:.3f}" width="{size+2*q:.3f}" '
           f'height="{size+2*q:.3f}" rx="{q*1.2:.3f}" fill="{fondo}"/>',
           f'<path id="{layer}-modulos" fill="{color}" d="{"".join(rects)}"/>']
    for ec, er in eyes:
        ox, oy = ec * q, er * q
        out.append(
            f'<path fill="{color}" fill-rule="evenodd" d="'
            f'{_rrect(ox, oy, 7*q, 7*q, 2.0*q)}{_rrect(ox+q, oy+q, 5*q, 5*q, 1.3*q)}"/>')
        out.append(f'<rect fill="{color}" x="{ox+2*q:.3f}" y="{oy+2*q:.3f}" '
                   f'width="{3*q:.3f}" height="{3*q:.3f}" rx="{0.8*q:.3f}"/>')
    # isotipo centrado
    iw = hole * q * 0.92
    cx = cy = (h0 + hole / 2) * q
    if hole:
        out.append(_isotipo(cx - iw / 2, cy - iw * 0.3, iw, color))
    out.append("</g>")
    return "\n".join(out), n


def _rrect(x, y, w, h, r):
    return (f"M{x+r:.3f} {y:.3f}H{x+w-r:.3f}A{r:.3f} {r:.3f} 0 0 1 {x+w:.3f} {y+r:.3f}"
            f"V{y+h-r:.3f}A{r:.3f} {r:.3f} 0 0 1 {x+w-r:.3f} {y+h:.3f}"
            f"H{x+r:.3f}A{r:.3f} {r:.3f} 0 0 1 {x:.3f} {y+h-r:.3f}"
            f"V{y+r:.3f}A{r:.3f} {r:.3f} 0 0 1 {x+r:.3f} {y:.3f}Z")


ISO_BBOX = (315.0, 292.0, 658.0, 479.0)


def _isotipo(x, y, w, color):
    x0, y0, x1, y1 = ISO_BBOX
    k = w / (x1 - x0)
    ds = "".join(f'<path d="{d}"/>' for d in LOGO["isotipo"])
    return (f'<g fill="{color}" transform="translate({x:.3f} {y:.3f}) '
            f'scale({k:.6f}) translate({-x0} {-y0})">{ds}</g>')


# ================================================================ íconos
# Material Icons (Apache 2.0) — 24 x 24
ICON = {
    "tel": "M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z",
    "mail": "M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z",
    "web": "M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zm6.93 6h-2.95c-.32-1.25-.78-2.45-1.38-3.56 1.84.63 3.37 1.91 4.33 3.56zM12 4.04c.83 1.2 1.48 2.53 1.91 3.96h-3.82c.43-1.43 1.08-2.76 1.91-3.96zM4.26 14C4.1 13.36 4 12.69 4 12s.1-1.36.26-2h3.38c-.08.66-.14 1.32-.14 2 0 .68.06 1.34.14 2H4.26zm.82 2h2.95c.32 1.25.78 2.45 1.38 3.56-1.84-.63-3.37-1.9-4.33-3.56zm2.95-8H5.08c.96-1.66 2.49-2.93 4.33-3.56C8.81 5.55 8.35 6.75 8.03 8zM12 19.96c-.83-1.2-1.48-2.53-1.91-3.96h3.82c-.43 1.43-1.08 2.76-1.91 3.96zM14.34 14H9.66c-.09-.66-.16-1.32-.16-2 0-.68.07-1.35.16-2h4.68c.09.65.16 1.32.16 2 0 .68-.07 1.34-.16 2zm.25 5.56c.6-1.11 1.06-2.31 1.38-3.56h2.95c-.96 1.65-2.49 2.93-4.33 3.56zM16.36 14c.08-.66.14-1.32.14-2 0-.68-.06-1.34-.14-2h3.38c.16.64.26 1.31.26 2s-.1 1.36-.26 2h-3.38z",
}


def g_icono(key, cx, cy, r, c_circ, c_ico):
    s = r * 1.15 / 24
    return (f'<g><circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" fill="{c_circ}"/>'
            f'<path fill="{c_ico}" transform="translate({cx-12*s:.3f} {cy-12*s:.3f}) '
            f'scale({s:.5f})" d="{ICON[key]}"/></g>')


# ================================================================ fondos abstractos
def _grad(gid, x1, y1, x2, y2, stops):
    st = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>'
                 for o, c, a in stops)
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" '
            f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{st}</linearGradient>')


def fondo(spec, pref):
    """spec = {'base': (c1, c2, ángulo), 'facetas': [(puntos, (x1,y1,x2,y2), stops)]}"""
    defs, body = [], []
    c1, c2, (gx1, gy1, gx2, gy2) = spec["base"]
    defs.append(_grad(f"{pref}-base", gx1, gy1, gx2, gy2, [(0, c1, 1), (1, c2, 1)]))
    body.append(f'<rect id="Fondo-base" x="0" y="0" width="{FW}" height="{FH}" '
                f'fill="url(#{pref}-base)"/>')
    body.append('<g id="Fondo-facetas">')
    for i, (pts, gv, stops) in enumerate(spec["facetas"]):
        gid = f"{pref}-f{i}"
        defs.append(_grad(gid, *gv, stops))
        p = " ".join(f"{x},{y}" for x, y in pts)
        body.append(f'<polygon points="{p}" fill="url(#{gid})"/>')
    body.append("</g>")
    return defs, body


def fan(dark, light, corner, base1, base2, mirror=False, a=1.0, r=0.0):
    """Composición tipo Bagno: abanico de planos que nacen del borde derecho."""
    X = (lambda v: FW - v) if mirror else (lambda v: v)
    P = lambda pts: [(round(X(x), 3), y) for x, y in pts]
    G = lambda x1, y1, x2, y2: (round(X(x1), 3), y1, round(X(x2), 3), y2)
    return {
        "base": (base1, base2, G(0, 0, FW, FH)),
        "facetas": [
            # gran plano oscuro superior derecho
            (P([(38 + r, -1), (FW + 1, -1), (FW + 1, 38 - r * 0.6)]), G(44 + r, 4, 92, 30),
             [(0, dark, 0), (0.55, dark, 0.55 * a), (1, dark, 0.95 * a)]),
            # plano claro (brillo) que lo cruza
            (P([(16, -1), (56, -1), (FW + 1, 40)]), G(20, 0, 90, 38),
             [(0, light, 0.0), (0.5, light, 0.35 * a), (1, light, 0.05)]),
            # segundo plano oscuro, más cerrado
            (P([(60, -1), (FW + 1, -1), (FW + 1, 22)]), G(62, 0, 96, 16),
             [(0, dark, 0.2 * a), (1, dark, 0.9 * a)]),
            # banda inferior
            (P([(-1, 24 + r), (FW + 1, 40 + r * 0.3), (FW + 1, FH + 1), (64 + r, FH + 1)]), G(0, 30, 96, 50),
             [(0, dark, 0), (0.6, dark, 0.45 * a), (1, dark, 0.85 * a)]),
            # brillo inferior izquierdo
            (P([(-1, FH + 1), (-1, 36), (58, FH + 1)]), G(0, 40, 50, 56),
             [(0, light, 0.4 * a), (1, light, 0)]),
            # esquina clara (como el recorte lima de Bagno)
            (P([(87, -1), (FW + 1, -1), (FW + 1, 15), (89, 17)]), G(87, 0, 96, 16),
             [(0, corner, 0.95), (1, corner, 0.75)]),
        ],
    }


def cruce(c_a, c_b, light, base1, base2):
    """Dos haces que se cruzan desde esquinas opuestas."""
    return {
        "base": (base1, base2, (0, FH, FW, 0)),
        "facetas": [
            ([(-1, -1), (44, -1), (FW + 1, 46), (FW + 1, FH + 1), (80, FH + 1)],
             (0, 0, 96, 56), [(0, c_a, 0.0), (0.55, c_a, 0.2), (1, c_a, 0.7)]),
            ([(-1, FH + 1), (-1, 30), (70, -1), (FW + 1, -1), (36, FH + 1)],
             (0, 56, 96, 0), [(0, c_b, 0.85), (0.6, c_b, 0.3), (1, c_b, 0.0)]),
            ([(50, -1), (FW + 1, -1), (FW + 1, 28)], (60, 0, 96, 20),
             [(0, light, 0.0), (1, light, 0.45)]),
            ([(-1, FH + 1), (-1, 44), (24, FH + 1)], (0, 44, 20, 56),
             [(0, light, 0.5), (1, light, 0.1)]),
        ],
    }


def prisma(c_a, c_b, light, base1, base2):
    """Triángulos facetados que suben desde abajo (efecto cristal)."""
    return {
        "base": (base1, base2, (0, 0, 0, FH)),
        "facetas": [
            ([(-1, FH + 1), (-1, 18), (40, FH + 1)], (0, 20, 30, 56),
             [(0, c_a, 0.75), (1, c_a, 0.15)]),
            ([(10, FH + 1), (48, 26), (86, FH + 1)], (48, 26, 48, 56),
             [(0, c_b, 0.05), (1, c_b, 0.55)]),
            ([(48, 26), (FW + 1, -1), (FW + 1, FH + 1), (86, FH + 1)], (60, 30, 96, 10),
             [(0, c_a, 0.1), (1, c_a, 0.8)]),
            ([(60, -1), (FW + 1, -1), (FW + 1, 20)], (70, 0, 96, 14),
             [(0, light, 0.0), (1, light, 0.6)]),
            ([(-1, -1), (30, -1), (-1, 14)], (0, 0, 20, 10),
             [(0, c_b, 0.5), (1, c_b, 0.0)]),
        ],
    }


# ================================================================ armado SVG
def svg_doc(defs, body, title):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{FW}mm" height="{FH}mm" '
            f'viewBox="0 0 {FW} {FH}">\n<title>{title}</title>\n'
            f'<defs>{"".join(defs)}</defs>\n' + "\n".join(body) + "\n</svg>\n")


def guias():
    """Capa de guías (corte y zona segura). Ocultar/borrar antes de imprimir."""
    s = 4.0
    return (f'<g id="Guias-NO-IMPRIMIR" fill="none" stroke="#FF00FF" stroke-width="0.1">'
            f'<rect x="{B}" y="{B}" width="{W}" height="{H}"/>'
            f'<rect x="{B+s}" y="{B+s}" width="{W-2*s}" height="{H-2*s}" '
            f'stroke-dasharray="0.6 0.6"/></g>')


def frente(op):
    defs, body = fondo(op["fondo"], f"o{op['n']}")
    body = ['<g id="Fondo">'] + body + ["</g>"]
    if op.get("script"):
        lw = 62.0
        lh = logo_script_h(lw)
        body.append(g_logo_script((FW - lw) / 2, (FH - lh) / 2 - 1.0, lw, *op["logo_frente"]))
    else:
        lw = 54.0
        lh = logo_mabi_h(lw)
        body.append(g_logo_mabi((FW - lw) / 2, (FH - lh) / 2, lw, *op["logo_frente"])[0])
    return defs, body


def dorso(op):
    d = op["dorso"]
    defs, body = [], []
    body.append(f'<g id="Fondo"><rect x="0" y="0" width="{FW}" height="{FH}" fill="{d["fondo"]}"/>')
    if d.get("franja"):
        # franja abstracta en el borde derecho, eco del frente
        fdefs, fbody = fondo(op["fondo"], f"d{op['n']}")
        defs += fdefs
        defs.append(f'<clipPath id="d{op["n"]}-clip"><polygon points="'
                    f'{FW-7.5},0 {FW+1},0 {FW+1},{FH} {FW-4.5},{FH}"/></clipPath>')
        body.append(f'<g id="Franja" clip-path="url(#d{op["n"]}-clip)">' + "".join(fbody) + "</g>")
    body.append("</g>")

    # columna izquierda: logo + QR
    colx, colw = B + 5.5, 25.0
    lw = 23.0
    body.append(g_logo_mabi(colx + (colw - lw) / 2, B + 5.0, lw, *d["logo"])[0])
    lh = logo_mabi_h(lw)
    # línea de color bajo el logo (como el subrayado de Bagno)
    ly = B + 5.0 + lh + 2.0
    body.append(f'<g id="Linea"><rect x="{colx+1.0:.3f}" y="{ly:.3f}" width="{colw-2.0:.3f}" '
                f'height="0.45" fill="{d["acento"]}"/></g>')
    qs = 17.5
    qy = ly + 2.6
    qr, _ = g_qr(colx + (colw - qs) / 2, qy, qs, d["qr"], d["qr_fondo"])
    body.append(qr)

    # columna derecha: datos
    tx = B + 40.5
    tc, sc = d["texto"], d["texto2"]
    body.append('<g id="Datos">')
    body.append(f'<text x="{tx}" y="{B+12.6}" font-family="Sora" font-weight="700" '
                f'font-size="3.55" fill="{d["nombre"]}" letter-spacing="-0.03">{NOMBRE}</text>')
    body.append(f'<rect x="{tx}" y="{B+14.6}" width="7" height="0.55" fill="{d["acento"]}"/>')
    body.append(f'<text x="{tx}" y="{B+18.6}" font-family="Inter" font-weight="500" '
                f'font-size="2.05" fill="{sc}" letter-spacing="0.02">{EMPRESA}</text>')
    rows = [("tel", TEL), ("mail", MAIL), ("web", WEB)]
    y0, dy, r = B + 27.6, 6.2, 1.85
    for i, (k, txt) in enumerate(rows):
        cy = y0 + i * dy
        body.append(g_icono(k, tx + r, cy, r, d["icono"], d["icono_fg"]))
        body.append(f'<text x="{tx + 2*r + 2.2:.3f}" y="{cy + 0.85:.3f}" font-family="Inter" '
                    f'font-weight="500" font-size="2.5" fill="{tc}">{txt}</text>')
    body.append("</g>")
    return defs, body


# ================================================================ opciones
OPCIONES = [
    {
        "n": 1, "slug": "01-bosque",
        "nombre": "Bosque — verde profundo, abanico tipo Bagno",
        "fondo": fan(dark="#021F14", light=VERDE_C, corner=VERDE_C,
                     base1="#0E5A3A", base2=VERDE),
        "logo_frente": (ORO, CREMA, CREMA, ORO),
        "dorso": dict(fondo=BLANCO, logo=(ORO, VERDE, VERDE, ORO), acento=ORO,
                      qr=VERDE, qr_fondo=BLANCO, nombre=VERDE, texto="#1E1E1E",
                      texto2="#5A6A62", icono=VERDE, icono_fg=BLANCO),
    },
    {
        "n": 2, "slug": "02-dorado",
        "nombre": "Dorado — la traducción más fiel de Bagno (oro + planos verdes)",
        "fondo": fan(dark=VERDE, light="#FFE7A6", corner=ORO_C,
                     base1=ORO_C, base2=ORO, a=0.95, r=16),
        "logo_frente": (VERDE, VERDE, VERDE, VERDE),
        "dorso": dict(fondo=BLANCO, logo=(VERDE, VERDE, VERDE, ORO), acento=ORO,
                      qr=VERDE, qr_fondo=BLANCO, nombre=VERDE, texto="#1E1E1E",
                      texto2="#5A6A62", icono=ORO, icono_fg=VERDE),
    },
    {
        "n": 3, "slug": "03-bosque-oro",
        "nombre": "Bosque + Oro — haces dorados cruzando el verde",
        "fondo": cruce(c_a=ORO, c_b=VERDE_C, light=ORO_C, base1="#04301F", base2=VERDE_M),
        "logo_frente": (ORO, CREMA, CREMA, ORO),
        "dorso": dict(fondo=CREMA, logo=(ORO, VERDE, VERDE, ORO), acento=ORO,
                      qr=VERDE, qr_fondo=CREMA, nombre=VERDE, texto="#1E1E1E",
                      texto2="#5A6A62", icono=VERDE, icono_fg=ORO, franja=True),
    },
    {
        "n": 4, "slug": "04-crema",
        "nombre": "Crema — fondo claro con prismas verde y oro",
        "fondo": prisma(c_a=VERDE_M, c_b=ORO, light=ORO_C, base1=CREMA, base2="#E9EBDF"),
        "logo_frente": (VERDE, VERDE, VERDE, VERDE),
        "dorso": dict(fondo=VERDE, logo=(ORO, CREMA, CREMA, ORO), acento=ORO,
                      qr=VERDE, qr_fondo=CREMA, nombre=CREMA, texto=CREMA,
                      texto2="#B9C7BF", icono=ORO, icono_fg=VERDE),
    },
    {
        "n": 5, "slug": "05-verde-vivo",
        "nombre": "Verde vivo — abanico espejado con esquina dorada",
        "fondo": fan(dark="#03271A", light="#5FA97C", corner=ORO,
                     base1="#3C8A5C", base2="#0B4A31", mirror=True),
        "logo_frente": (ORO, BLANCO, BLANCO, ORO),
        "dorso": dict(fondo=BLANCO, logo=(VERDE, VERDE, VERDE, ORO), acento=VERDE_C,
                      qr=VERDE, qr_fondo=BLANCO, nombre=VERDE, texto="#1E1E1E",
                      texto2="#5A6A62", icono="#1E1E1E", icono_fg=BLANCO, franja=True),
    },
    {
        "n": 6, "slug": "06-manuscrito",
        "nombre": "Manuscrito — logo web 'mabi' sobre abanico verde/oro",
        "script": True,
        "fondo": fan(dark="#021F14", light=ORO, corner=ORO,
                     base1="#0E5A3A", base2=VERDE, a=0.9),
        "logo_frente": (CREMA, ORO),
        "dorso": dict(fondo=BLANCO, logo=(ORO, VERDE, VERDE, ORO), acento=ORO,
                      qr=VERDE, qr_fondo=BLANCO, nombre=VERDE, texto="#1E1E1E",
                      texto2="#5A6A62", icono=VERDE, icono_fg=ORO),
    },
]


# ================================================================ serie 2 — conceptos nuevos
import math

WM_BBOX = (155.7, 505.0, 925.2, 787.3)   # MABI + leyenda, sin isotipo


def g_wordmark(x, y, w, c_mabi, c_dist, c_int, layer="Logo-wordmark"):
    x0, y0, x1, y1 = WM_BBOX
    k = w / (x1 - x0)
    out = [f'<g id="{layer}" transform="translate({x:.3f} {y:.3f}) '
           f'scale({k:.6f}) translate({-x0} {-y0})">']
    for name, col in (("mabi", c_mabi), ("distribucion", c_dist), ("inteligente", c_int)):
        out.append(f'<g id="{layer}-{name}" fill="{col}">')
        out += [f'<path d="{d}"/>' for d in LOGO[name]]
        out.append("</g>")
    out.append("</g>")
    return "\n".join(out)


def wordmark_h(w):
    x0, y0, x1, y1 = WM_BBOX
    return w * (y1 - y0) / (x1 - x0)


def iso_h(w):
    x0, y0, x1, y1 = ISO_BBOX
    return w * (y1 - y0) / (x1 - x0)


def _txt(x, y, s, size, fill, family="Inter", weight=500, ls=0.0, anchor="start"):
    return (f'<text x="{x:.3f}" y="{y:.3f}" font-family="{family}" font-weight="{weight}" '
            f'font-size="{size}" fill="{fill}" letter-spacing="{ls}" '
            f'text-anchor="{anchor}">{s}</text>')


def _qr_panel(x, y, size, color, panel, pad=1.6, layer="QR"):
    """QR con zona de silencio clara (sirve sobre fondos oscuros)."""
    qr, _ = g_qr(x, y, size, color, panel, layer=layer)
    bg = (f'<rect x="{x-pad:.3f}" y="{y-pad:.3f}" width="{size+2*pad:.3f}" '
          f'height="{size+2*pad:.3f}" rx="1.6" fill="{panel}"/>')
    return bg + qr


def _contactos_label(x, y, dy, c_lab, c_val, size=2.35):
    """Contactos estilo editorial: etiqueta en versalitas + valor."""
    out = []
    for i, (lab, val) in enumerate((("TEL", TEL), ("MAIL", MAIL), ("WEB", WEB))):
        yy = y + i * dy
        out.append(_txt(x, yy, lab, 1.55, c_lab, weight=600, ls=0.32))
        out.append(_txt(x + 8.2, yy, val, size, c_val, weight=500))
    return out


# ---------- 07 · Monograma: isotipo gigante recortado + grilla suiza
def frente_07(op):
    body = [f'<g id="Fondo"><rect width="{FW}" height="{FH}" fill="{CREMA}"/></g>']
    iw = 112.0
    body.append(f'<g id="Isotipo-gigante">{_isotipo(36.0, -15.0, iw, ORO)}</g>')
    ww = 40.0
    body.append(g_wordmark(B + 6.0, FH - B - 6.0 - wordmark_h(ww), ww, VERDE, VERDE, VERDE))
    return [], body


def dorso_07(op):
    body = [f'<g id="Fondo"><rect width="{FW}" height="{FH}" fill="{VERDE}"/></g>']
    x = B + 6.0
    body.append(f'<g id="Isotipo">{_isotipo(FW - B - 6.0 - 9.0, B + 5.0, 9.0, ORO)}</g>')
    body.append('<g id="Datos">')
    body.append(_txt(x, B + 7.2, "MABI · DISTRIBUCIÓN INTELIGENTE", 1.55, ORO, weight=600, ls=0.32))
    first, last = NOMBRE.rsplit(" ", 1)
    body.append(_txt(x, B + 15.2, first, 5.2, CREMA, family="Sora", weight=800, ls=-0.12))
    body.append(_txt(x, B + 21.4, last, 5.2, ORO, family="Sora", weight=800, ls=-0.12))
    body.append(f'<rect x="{x}" y="{B+28.6}" width="44" height="0.18" fill="{CREMA}" opacity="0.35"/>')
    body += _contactos_label(x, B + 34.2, 4.4, ORO, CREMA)
    body.append("</g>")
    qs = 15.0
    body.append(_qr_panel(FW - B - 6.0 - qs, FH - B - 6.0 - qs, qs, VERDE, CREMA))
    return [], body


# ---------- 08 · Surcos: líneas topográficas (campo / viento del isotipo)
def _topo(cx, cy, n, r0, dr, color, w, op0, op1, seed=0.0, sx=1.6):
    out = []
    for i in range(n):
        r = r0 + i * dr
        pts = []
        for j in range(181):
            t = 2 * math.pi * j / 180
            k = (1 + 0.07 * math.sin(3 * t + seed + i * 0.17)
                 + 0.045 * math.sin(5 * t - seed * 1.3 + i * 0.09)
                 + 0.025 * math.cos(7 * t + i * 0.05))
            pts.append((cx + sx * r * k * math.cos(t), cy + r * k * math.sin(t)))
        d = "M" + " L".join(f"{px:.2f} {py:.2f}" for px, py in pts) + "Z"
        a = op0 + (op1 - op0) * i / max(1, n - 1)
        out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" '
                   f'stroke-opacity="{a:.3f}"/>')
    return out


def frente_08(op):
    defs = [_grad("o8-base", 0, 0, FW, FH, [(0, "#0A4A32", 1), (1, "#03281A", 1)])]
    body = ['<g id="Fondo">', f'<rect width="{FW}" height="{FH}" fill="url(#o8-base)"/>',
            '<g id="Lineas-topograficas">']
    body += _topo(FW - 4, FH + 2, 26, 3.0, 2.15, ORO, 0.22, 0.95, 0.12, seed=0.6)
    body += ["</g>", "</g>"]
    lw = 44.0
    body.append(g_logo_mabi(B + 7.0, (FH - logo_mabi_h(lw)) / 2, lw, ORO, CREMA, CREMA, ORO)[0])
    return defs, body


def dorso_08(op):
    body = ['<g id="Fondo">', f'<rect width="{FW}" height="{FH}" fill="{CREMA}"/>',
            '<g id="Lineas-topograficas">']
    body += _topo(-6, -4, 22, 3.0, 2.15, VERDE, 0.16, 0.55, 0.06, seed=2.1)
    body += ["</g>", "</g>"]
    x = B + 40.0
    body.append('<g id="Datos">')
    body.append(_txt(x, B + 11.5, NOMBRE, 3.9, VERDE, family="Sora", weight=700, ls=-0.06))
    body.append(_txt(x, B + 16.0, "MABI · DISTRIBUCIÓN INTELIGENTE", 1.55, ORO, weight=700, ls=0.3))
    rows = [("tel", TEL), ("mail", MAIL), ("web", WEB)]
    for i, (k, v) in enumerate(rows):
        cy = B + 26.0 + i * 5.6
        body.append(g_icono(k, x + 1.7, cy, 1.7, ORO, VERDE))
        body.append(_txt(x + 5.6, cy + 0.85, v, 2.45, "#1E1E1E"))
    body.append("</g>")
    qs = 17.0
    body.append(_qr_panel(B + 8.0, B + 19.0, qs, VERDE, BLANCO, pad=1.4))
    body.append(g_wordmark(B + 7.0, B + 6.5, 19.5, VERDE, VERDE, ORO))
    return [], body


# ---------- 09 · Sol: arco dorado gigante + bloques de color
def frente_09(op):
    cx, cy = FW - 10.0, FH + 6.0
    body = ['<g id="Fondo">', f'<rect width="{FW}" height="{FH}" fill="{VERDE}"/>',
            '<g id="Sol">']
    for i, (r, a) in enumerate(((60, 0.10), (52, 0.18), (44, 0.30))):
        body.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{ORO}" '
                     f'stroke-width="0.35" stroke-opacity="{a}"/>')
    defs = [_grad("o9-sol", cx - 30, cy - 36, cx + 10, cy, [(0, ORO_C, 1), (1, ORO, 1)])]
    body.append(f'<circle cx="{cx}" cy="{cy}" r="34" fill="url(#o9-sol)"/>')
    body.append(f'<g id="Isotipo-en-sol">{_isotipo(cx - 21.0, cy - 28.0, 26.0, VERDE)}</g>')
    body += ["</g>", "</g>"]
    ww = 46.0
    body.append(g_wordmark(B + 6.0, (FH - wordmark_h(ww)) / 2 - 2.0, ww, CREMA, CREMA, ORO))
    return defs, body


def dorso_09(op):
    px = 61.0
    body = ['<g id="Fondo">', f'<rect width="{FW}" height="{FH}" fill="{CREMA}"/>',
            f'<path id="Panel" fill="{VERDE}" d="M{px+6} 0H{FW}V{FH}H{px+6}'
            f'A6 6 0 0 1 {px} {FH-6}V6A6 6 0 0 1 {px+6} 0Z"/>', "</g>"]
    qs = 16.0
    qx = px + (FW - B - px - qs) / 2 + 1.0
    body.append(_qr_panel(qx, B + 10.5, qs, VERDE, CREMA))
    body.append(_txt(qx + qs / 2, B + 33.0, "ESCANEÁ", 1.5, ORO, weight=700, ls=0.35, anchor="middle"))
    x = B + 6.0
    body.append('<g id="Datos">')
    body.append(f'<g id="Isotipo">{_isotipo(x, B + 5.5, 10.0, ORO)}</g>')
    body.append(_txt(x, B + 17.8, NOMBRE, 3.9, VERDE, family="Sora", weight=800, ls=-0.08))
    body.append(_txt(x, B + 22.0, "MABI · Distribución Inteligente", 2.0, "#5A6A62", weight=500))
    for i, v in enumerate((TEL, MAIL, WEB)):
        yy = B + 31.0 + i * 4.8
        body.append(f'<circle cx="{x+0.7}" cy="{yy-0.8:.3f}" r="0.7" fill="{ORO}"/>')
        body.append(_txt(x + 3.0, yy, v, 2.45, "#1E1E1E"))
    body.append("</g>")
    return [], body


OPCIONES += [
    {"n": 7, "slug": "07-monograma", "serie": 2, "ff": frente_07, "fd": dorso_07,
     "nombre": "Monograma — isotipo gigante recortado + grilla editorial"},
    {"n": 8, "slug": "08-surcos", "serie": 2, "ff": frente_08, "fd": dorso_08,
     "nombre": "Surcos — líneas topográficas doradas sobre verde"},
    {"n": 9, "slug": "09-sol", "serie": 2, "ff": frente_09, "fd": dorso_09,
     "nombre": "Sol — arco dorado gigante y bloques de color"},
]


# opciones que eligió el cliente (lámina de preselección)
SELECCION = (1, 3, 5, 7, 8, 9)


def _prefijar(defs, body, pre):
    """Prefija ids y referencias para que no choquen al juntar tarjetas."""
    txt = "\n".join(defs) + "\u0000" + "\n".join(body)
    txt = re.sub(r'id="([^"]+)"', lambda m: f'id="{pre}-{m.group(1)}"', txt)
    txt = re.sub(r'url\(#([^)]+)\)', lambda m: f'url(#{pre}-{m.group(1)})', txt)
    return txt.split("\u0000")


def svg_unico(numeros, path):
    """Un solo SVG con todas las opciones elegidas (frente | dorso por fila).

    Cada tarjeta es un grupo con sangrado incluido (96 x 56 mm); la capa
    Guias-NO-IMPRIMIR marca el corte de 90 x 50 mm y la zona segura."""
    gap, head, margen = 12.0, 10.0, 10.0
    ops = [o for o in OPCIONES if o["n"] in numeros]
    tw = margen * 2 + FW * 2 + gap
    th = margen + len(ops) * (head + FH + gap) - gap + margen
    defs, cards, titulos, gu = [], [], [], []
    y = margen
    for op in ops:
        titulos.append(_txt(margen, y + 6.0, f"Opción {op['n']} · {op['nombre']}", 4.2,
                            VERDE, family="Sora", weight=700))
        y += head
        for i, (cara, fn) in enumerate((("Frente", op.get("ff", frente)),
                                        ("Dorso", op.get("fd", dorso)))):
            x = margen + i * (FW + gap)
            pre = f"Op{op['n']:02d}-{cara}"
            d, b = _prefijar(*fn(op), pre)
            defs.append(d)
            defs.append(f'<clipPath id="{pre}-clip"><rect width="{FW}" height="{FH}"/></clipPath>')
            cards.append(f'<g id="{pre}" transform="translate({x:.3f} {y:.3f})">'
                         f'<g clip-path="url(#{pre}-clip)">{b}</g></g>')
            gu.append(f'<rect x="{x+B:.3f}" y="{y+B:.3f}" width="{W}" height="{H}"/>'
                      f'<rect x="{x+B+4:.3f}" y="{y+B+4:.3f}" width="{W-8}" height="{H-8}" '
                      f'stroke-dasharray="0.6 0.6"/>')
        y += FH + gap
    svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{tw}mm" height="{th}mm" '
           f'viewBox="0 0 {tw} {th}">\n<title>MABI tarjetas seleccion</title>\n'
           f'<defs>{"".join(defs)}</defs>\n'
           f'<g id="Mesa"><rect width="{tw}" height="{th}" fill="#ECECE8"/></g>\n'
           f'<g id="Tarjetas">{"".join(cards)}</g>\n'
           f'<g id="Titulos">{"".join(titulos)}</g>\n'
           f'<g id="Guias-NO-IMPRIMIR" fill="none" stroke="#FF00FF" stroke-width="0.1">'
           f'{"".join(gu)}</g>\n</svg>\n')
    open(path, "w").write(svg)


def render_pdf(svg, path):
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=path)


def main():
    os.makedirs(OUT, exist_ok=True)
    previews = []
    for op in OPCIONES:
        d = os.path.join(OUT, op["slug"])
        os.makedirs(d, exist_ok=True)
        caras = {}
        for cara, fn in (("frente", op.get("ff", frente)), ("dorso", op.get("fd", dorso))):
            defs, body = fn(op)
            title = f"MABI tarjeta {op['slug']} {cara}"
            limpio = svg_doc(defs, body, title)
            con_guias = svg_doc(defs, body + [guias()], title)
            open(os.path.join(d, f"{cara}.svg"), "w").write(con_guias)
            caras[cara] = limpio
            png = os.path.join(d, f"preview-{cara}.png")
            # vista previa al corte (sin sangrado)
            img = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=limpio.encode(),
                                                         output_width=int(FW * 12))))
            k = img.width / FW
            img.crop((int(B * k), int(B * k), int((B + W) * k), int((B + H) * k))).save(png)
            previews.append(png)
        # PDF imprenta: pág 1 frente, pág 2 dorso, TrimBox/BleedBox
        w = PdfWriter()
        for cara in ("frente", "dorso"):
            tmp = f"/tmp/_{op['slug']}_{cara}.pdf"
            render_pdf(caras[cara], tmp)
            pg = PdfReader(tmp).pages[0]
            mm = 72 / 25.4
            pw, ph = float(pg.mediabox.width), float(pg.mediabox.height)
            pg.bleedbox = RectangleObject([0, 0, pw, ph])
            pg.trimbox = RectangleObject([B * mm, B * mm, pw - B * mm, ph - B * mm])
            w.add_page(pg)
        w.add_metadata({"/Title": f"MABI tarjeta personal {op['slug']}"})
        w.write(os.path.join(d, f"MABI-tarjeta-{op['slug']}.pdf"))
        print("ok", op["slug"])
    hoja_presentacion(1, "MABI-tarjetas-presentacion")
    hoja_presentacion(2, "MABI-tarjetas-presentacion-2")
    hoja_presentacion(None, "MABI-tarjetas-seleccion", SELECCION)
    svg_unico(SELECCION, os.path.join(OUT, "MABI-tarjetas-seleccion.svg"))


def hoja_presentacion(serie, nombre, numeros=None):
    """Lámina con todas las opciones (frente | dorso) para mostrar al cliente."""
    S = 8  # px por mm en la lámina
    cw, ch = int(W * S), int(H * S)
    pad, gap, head = 60, 36, 70
    cols_w = pad * 2 + cw * 2 + gap
    if numeros:
        ops = [o for o in OPCIONES if o["n"] in numeros]
    else:
        ops = [o for o in OPCIONES if o.get("serie", 1) == serie]
    rows_h = pad + len(ops) * (ch + head + gap)
    sheet = Image.new("RGB", (cols_w, rows_h), (236, 236, 232))
    from PIL import ImageDraw, ImageFont
    dr = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(os.path.join(HERE, "fuentes", "Sora-700.ttf"), 30)
    y = pad
    for op in ops:
        dr.text((pad, y), f"Opción {op['n']} · {op['nombre']}", font=f, fill=(6, 58, 39))
        y += head
        for i, cara in enumerate(("frente", "dorso")):
            im = Image.open(os.path.join(OUT, op["slug"], f"preview-{cara}.png"))
            im = im.resize((cw, ch), Image.LANCZOS)
            x = pad + i * (cw + gap)
            sh = Image.new("RGB", (cw, ch), (205, 205, 200))
            sheet.paste(sh, (x + 6, y + 8))
            sheet.paste(im, (x, y))
        y += ch + gap
    sheet.save(os.path.join(OUT, f"{nombre}.png"))
    sheet.convert("RGB").save(os.path.join(OUT, f"{nombre}.pdf"), resolution=150)


if __name__ == "__main__":
    main()
