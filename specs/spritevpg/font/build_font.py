#!/usr/bin/env python3
"""Construye font/spritevpg-4x6.ttf desde la tabla de glifos de spritevpg.py
(una sola fuente de verdad: el texto que dibuja la herramienta y el de la
fuente son los mismos píxeles).

Celda de 5x8 píxeles: fila 0 para la tilde, filas 1-6 para el glifo de 4x6,
fila 7 y columna 4 libres. Cada píxel mide 100 unidades y el em son 800: a
8 px por em, un píxel de la fuente es un píxel de pantalla; usar múltiplos de
8 px (16, 24, 32…) y sin suavizado.

  python3 font/build_font.py   (necesita fontTools)
"""
import os, sys
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'skill', 'spritevpg', 'scripts'))
from spritevpg import CHARS, CW, CH, GW, GH, cell_rows  # noqa: E402

PX, ROWS = 100, GH

def name(ch):
    return 'space' if ch == ' ' else f'uni{ord(ch):04X}'

def outlines(rows):
    """Contornos de la unión de los píxeles: aristas entre píxel lleno y vacío,
    con lo lleno a la derecha (horario por fuera, antihorario en los huecos,
    como pide TrueType), encadenadas."""
    on = lambda c, r: 0 <= c < GW and 0 <= r < ROWS and rows[r][c] == '1'
    edges = {}
    for r in range(ROWS):
        for c in range(GW):
            if not on(c, r):
                continue
            x0, x1, y1 = c, c + 1, ROWS - r
            y0 = y1 - 1
            if not on(c - 1, r): edges.setdefault((x0, y0), []).append((x0, y1))
            if not on(c, r - 1): edges.setdefault((x0, y1), []).append((x1, y1))
            if not on(c + 1, r): edges.setdefault((x1, y1), []).append((x1, y0))
            if not on(c, r + 1): edges.setdefault((x1, y0), []).append((x0, y0))
    loops = []
    while edges:
        start = next(iter(edges))
        loop, cur = [start], start
        while True:
            outs = edges[cur]
            nxt = outs.pop(0)
            if not outs:
                del edges[cur]
            if nxt == start:
                break
            loop.append(nxt)
            cur = nxt
        loops.append([p for i, p in enumerate(loop)
                      if not ((loop[i - 1][0] == p[0] == loop[(i + 1) % len(loop)][0]) or
                              (loop[i - 1][1] == p[1] == loop[(i + 1) % len(loop)][1]))])
    return loops

def glyph(rows):
    pen = TTGlyphPen(None)
    for loop in outlines(rows):
        pen.moveTo((loop[0][0] * PX, loop[0][1] * PX))
        for x, y in loop[1:]:
            pen.lineTo((x * PX, y * PX))
        pen.closePath()
    return pen.glyph()

order = ['.notdef'] + [name(ch) for ch in CHARS]
fb = FontBuilder(CH * PX, isTTF=True)
fb.setupGlyphOrder(order)
cmap = {}
for ch in CHARS:
    cmap[ord(ch)] = name(ch)
    low = ch.lower()
    if low != ch and len(low) == 1:
        cmap[ord(low)] = name(ch)              # minúsculas = mayúsculas
for code, ch in {0x2019: "'", 0x2013: '-', 0x2014: '-', 0xD7: 'X', 0x201C: '"', 0x201D: '"',
                 0xAB: '"', 0xBB: '"', 0x2192: '>'}.items():
    cmap.setdefault(code, name(ch))
fb.setupCharacterMap(cmap)
box = TTGlyphPen(None)
box.moveTo((0, 0)); box.lineTo((0, 600)); box.lineTo((400, 600)); box.lineTo((400, 0)); box.closePath()
glyphs = {'.notdef': box.glyph()}
glyphs.update({name(ch): glyph(cell_rows(ch)) for ch in CHARS})
fb.setupGlyf(glyphs)
fb.setupHorizontalMetrics({g: (CW * PX, 0) for g in order})
fb.setupHorizontalHeader(ascent=GH * PX, descent=-100)
fb.setupOS2(sTypoAscender=GH * PX, sTypoDescender=-100, sTypoLineGap=0,
            usWinAscent=GH * PX, usWinDescent=100, achVendID='VRGT',
            panose={'bFamilyType': 2, 'bSerifStyle': 0, 'bWeight': 5, 'bProportion': 9,
                    'bContrast': 0, 'bStrokeVariation': 0, 'bArmStyle': 0,
                    'bLetterForm': 0, 'bMidline': 0, 'bXHeight': 0})
fb.setupPost(isFixedPitch=1)
fb.setupNameTable({
    'copyright': 'Copyright 2026 Varial Gate',
    'familyName': 'SpriteVPG 4x6',
    'styleName': 'Regular',
    'uniqueFontIdentifier': 'VarialGate:SpriteVPG4x6:1.0',
    'fullName': 'SpriteVPG 4x6 Regular',
    'psName': 'SpriteVPG4x6-Regular',
    'version': 'Version 1.000',
    'licenseDescription': 'This Font Software is licensed under the SIL Open Font License, Version 1.1.',
    'licenseInfoURL': 'https://openfontlicense.org',
})
out = os.path.join(HERE, 'spritevpg-4x6.ttf')
fb.save(out)
print(out, len(CHARS), 'glifos,', len(cmap), 'caracteres')
