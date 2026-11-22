#!/usr/bin/env python3
"""Construye font/spritevpg-5x7.ttf desde la tabla de glifos de spritevpg.py
(una sola fuente de verdad: el texto que dibuja la herramienta y el de la
fuente son los mismos píxeles).

Cada píxel mide 100 unidades (1000 por em): a 10 px por em, un píxel de la
fuente es un píxel de pantalla; usar múltiplos de 10 px y sin suavizado.

  python3 font/build_font.py   (necesita fontTools)
"""
import os, sys, unicodedata
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'skill', 'spritevpg', 'scripts'))
from spritevpg import G, ADV  # noqa: E402

PX, ASC, DESC = 100, 800, -200

def name(ch):
    return 'space' if ch == ' ' else f'uni{ord(ch):04X}'

def outlines(rows):
    """Contornos de la unión de los píxeles: aristas entre píxel lleno y vacío,
    orientadas con lo lleno a la derecha (horario por fuera, antihorario en los
    huecos, como pide TrueType) y encadenadas. Con un rectángulo por tramo,
    algunos rasterizadores dejaban una raya entre filas."""
    on = lambda c, r: 0 <= c < 5 and 0 <= r < 7 and rows[r][c] == '1'
    edges = {}
    for r in range(7):
        for c in range(5):
            if not on(c, r):
                continue
            x0, x1, y1 = c, c + 1, 7 - r
            y0 = y1 - 1
            if not on(c - 1, r): edges.setdefault((x0, y0), []).append((x0, y1))  # izquierda, sube
            if not on(c, r - 1): edges.setdefault((x0, y1), []).append((x1, y1))  # arriba, derecha
            if not on(c + 1, r): edges.setdefault((x1, y1), []).append((x1, y0))  # derecha, baja
            if not on(c, r + 1): edges.setdefault((x1, y0), []).append((x0, y0))  # abajo, izquierda
    loops = []
    while edges:
        start = next(iter(edges))
        loop, cur, prev = [start], start, None
        while True:
            outs = edges[cur]
            nxt = outs.pop(0)
            if not outs:
                del edges[cur]
            if nxt == start:
                break
            loop.append(nxt)
            cur = nxt
        # Quita los puntos intermedios de las rectas.
        simple = [p for i, p in enumerate(loop)
                  if not ((loop[i - 1][0] == p[0] == loop[(i + 1) % len(loop)][0]) or
                          (loop[i - 1][1] == p[1] == loop[(i + 1) % len(loop)][1]))]
        loops.append(simple)
    return loops

def glyph(rows):
    pen = TTGlyphPen(None)
    for loop in outlines(rows):
        pen.moveTo((loop[0][0] * PX, loop[0][1] * PX))
        for x, y in loop[1:]:
            pen.lineTo((x * PX, y * PX))
        pen.closePath()
    return pen.glyph()

order = ['.notdef'] + [name(ch) for ch in G]
fb = FontBuilder(1000, isTTF=True)
fb.setupGlyphOrder(order)
cmap = {}
for ch in G:
    cmap[ord(ch)] = name(ch)
    low = ch.lower()
    if low != ch and len(low) == 1:
        cmap[ord(low)] = name(ch)          # minúsculas = mayúsculas
for code in list(range(0xC0, 0x100)) + [0x2019, 0x2013, 0x2014]:
    ch = chr(code)
    if code in cmap:
        continue
    base = unicodedata.normalize('NFD', ch)[0].upper()
    if base in G:
        cmap[code] = name(base)            # tildes: la letra sin tilde
cmap.setdefault(0x2019, name("'"))
cmap.setdefault(0x2013, name('-'))
cmap.setdefault(0x2014, name('-'))
fb.setupCharacterMap(cmap)
empty = TTGlyphPen(None)
empty.moveTo((0, 0)); empty.lineTo((0, 700)); empty.lineTo((500, 700)); empty.lineTo((500, 0)); empty.closePath()
glyphs = {'.notdef': empty.glyph()}
glyphs.update({name(ch): glyph(G[ch]) for ch in G})
fb.setupGlyf(glyphs)
fb.setupHorizontalMetrics({g: (ADV * PX, 0) for g in order})
fb.setupHorizontalHeader(ascent=ASC, descent=DESC)
fb.setupOS2(sTypoAscender=ASC, sTypoDescender=DESC, sTypoLineGap=100,
            usWinAscent=ASC, usWinDescent=-DESC, achVendID='VRGT',
            panose={'bFamilyType': 2, 'bSerifStyle': 0, 'bWeight': 5, 'bProportion': 9,
                    'bContrast': 0, 'bStrokeVariation': 0, 'bArmStyle': 0,
                    'bLetterForm': 0, 'bMidline': 0, 'bXHeight': 0})
fb.setupPost(isFixedPitch=1)
fb.setupNameTable({
    'copyright': 'Copyright 2026 Varial Gate',
    'familyName': 'SpriteVPG 5x7',
    'styleName': 'Regular',
    'uniqueFontIdentifier': 'VarialGate:SpriteVPG5x7:1.0',
    'fullName': 'SpriteVPG 5x7 Regular',
    'psName': 'SpriteVPG5x7-Regular',
    'version': 'Version 1.000',
    'licenseDescription': 'This Font Software is licensed under the SIL Open Font License, Version 1.1.',
    'licenseInfoURL': 'https://openfontlicense.org',
})
out = os.path.join(HERE, 'spritevpg-5x7.ttf')
fb.save(out)
print(out, len(G), 'glifos,', len(cmap), 'caracteres')
