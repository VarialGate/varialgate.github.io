#!/usr/bin/env python3
"""SpriteVPG: genera, lee y comprueba sprite patterns.

Un sprite pattern es una hoja de sprites PNG con los frames limpios desde la
esquina de arriba a la izquierda y una animación por fila. A la derecha de
cada fila, en su misma altura, van sus datos en columnas (nombre, frames, ms
por frame, reproducción y, si hace falta, dirección y volteo), con las
cabeceras debajo de la última fila. Debajo van las zonas con título: SHEET
(nombre, tamaño de frame, rejilla y pivote), SUBJECT (tipo, vista, hacia dónde
mira, si se voltea, descripción y cuerpo), PALETTE (los colores de la hoja) y,
opcionalmente, AGENTS (lo que debe hacer una IA al usar la hoja en una app y
al ampliarla); y una barra final con la versión y la dirección de la
especificación: https://varialgate.github.io/specs/spritevpg/

Uso:
  spritevpg.py make  HOJA.png DATOS.json -o PATRON.png [--preview 4]
  spritevpg.py read  PATRON.png -o CARPETA [--gifs]
  spritevpg.py info  PATRON.png
  spritevpg.py validate PATRON.png

Solo necesita Pillow. Los datos se leen del propio dibujo (cada carácter cae
en una celda fija y se reconoce comparando píxeles): funciona con PNG sin
metadatos y con copias ampliadas a escala entera.
"""
import argparse, datetime, json, os, re, sys, unicodedata

from PIL import Image

FORMAT, VERSION = 'spritevpg', '2.2'
URL = 'varialgate.github.io/specs/spritevpg'      # lo que se escribe en la barra final

# ---------------------------------------------------------------- fuente ----
# SpriteVPG 4x6: la misma tabla que la fuente TTF (font/spritevpg-4x6.ttf).
# Cada carácter ocupa una celda de 5x8: fila 0 para la tilde, filas 1-6 para
# el glifo de 4x6, y la fila 7 y la columna 4 libres.
G = {
 'A': '0110 1001 1001 1111 1001 1001', 'B': '1110 1001 1110 1001 1001 1110',
 'C': '0111 1000 1000 1000 1000 0111', 'D': '1110 1001 1001 1001 1001 1110',
 'E': '1111 1000 1110 1000 1000 1111', 'F': '1111 1000 1110 1000 1000 1000',
 'G': '0111 1000 1000 1011 1001 0111', 'H': '1001 1001 1111 1001 1001 1001',
 'I': '1110 0100 0100 0100 0100 1110', 'J': '0011 0001 0001 0001 1001 0110',
 'K': '1001 1010 1100 1100 1010 1001', 'L': '1000 1000 1000 1000 1000 1111',
 'M': '1001 1111 1111 1001 1001 1001', 'N': '1001 1101 1101 1011 1011 1001',
 'O': '0110 1001 1001 1001 1001 0110', 'P': '1110 1001 1001 1110 1000 1000',
 'Q': '0110 1001 1001 1001 1010 0101', 'R': '1110 1001 1001 1110 1010 1001',
 'S': '0111 1000 0110 0001 0001 1110', 'T': '1110 0100 0100 0100 0100 0100',
 'U': '1001 1001 1001 1001 1001 0110', 'V': '1001 1001 1001 0110 0110 0100',
 'W': '1001 1001 1001 1111 1111 1001', 'X': '1001 1001 0110 0110 1001 1001',
 'Y': '1010 1010 0100 0100 0100 0100', 'Z': '1111 0001 0010 0100 1000 1111',
 '0': '0110 1001 1011 1101 1001 0110', '1': '0100 1100 0100 0100 0100 1110',
 '2': '0110 1001 0001 0110 1000 1111', '3': '1110 0001 0110 0001 0001 1110',
 '4': '1001 1001 1111 0001 0001 0001', '5': '1111 1000 1110 0001 0001 1110',
 '6': '0110 1000 1110 1001 1001 0110', '7': '1111 0001 0010 0100 0100 0100',
 '8': '0110 1001 0110 1001 1001 0110', '9': '0110 1001 1001 0111 0001 0110',
 ' ': '0000 0000 0000 0000 0000 0000', '.': '0000 0000 0000 0000 0000 0100',
 ',': '0000 0000 0000 0000 0100 1000', ':': '0000 0100 0000 0000 0100 0000',
 ';': '0000 0100 0000 0000 0100 1000', '-': '0000 0000 1110 0000 0000 0000',
 '+': '0000 0100 1110 0100 0000 0000', '/': '0001 0001 0010 0100 1000 1000',
 '(': '0010 0100 0100 0100 0100 0010', ')': '0100 0010 0010 0010 0010 0100',
 '[': '0110 0100 0100 0100 0100 0110', ']': '0110 0010 0010 0010 0010 0110',
 '=': '0000 1110 0000 1110 0000 0000', '#': '1010 1111 1010 1010 1111 1010',
 '<': '0001 0010 0100 0100 0010 0001', '>': '1000 0100 0010 0010 0100 1000',
 '*': '0000 1010 0100 1110 0100 1010', '%': '1001 0001 0010 0100 1000 1001',
 '_': '0000 0000 0000 0000 0000 1111', '"': '1010 1010 0000 0000 0000 0000',
 "'": '0100 0100 0000 0000 0000 0000', '!': '0100 0100 0100 0100 0000 0100',
 '?': '0110 1001 0001 0010 0000 0010', '&': '0100 1010 0100 1011 1010 0101',
 '·': '0000 0000 0110 0110 0000 0000', '¿': '0100 0000 0100 1000 1001 0110',
 '¡': '0100 0000 0100 0100 0100 0100',
}
G = {k: v.split() for k, v in G.items()}
# Tildes: en la fila 0 de la celda, sobre la letra.
ACUTE, TILDE, DIAER = '0010', '0110', '1001'
ACCENTED = {'Á': ('A', ACUTE), 'É': ('E', ACUTE), 'Í': ('I', ACUTE), 'Ó': ('O', ACUTE),
            'Ú': ('U', ACUTE), 'Ü': ('U', DIAER), 'Ñ': ('N', TILDE)}
CW, CH = 5, 8                  # celda de texto
GW, GH = 4, 7                  # lo que ocupa un carácter: 4 columnas y 7 filas (tilde + 6)

def cell_rows(ch):
    """Las 7 filas (tilde + 6) de un carácter, como cadenas de 4 bits."""
    if ch in ACCENTED:
        base, acc = ACCENTED[ch]
        return [acc] + G[base]
    return ['0000'] + G[ch]

CHARS = list(G) + list(ACCENTED)
LOOKUP = {''.join(cell_rows(c)): c for c in CHARS}
assert len(LOOKUP) == len(CHARS), 'glifos repetidos'

def norm(s):
    """Texto tal como se puede dibujar: mayúsculas y solo caracteres de la fuente."""
    out = []
    for ch in str(s).upper():
        if ch in G or ch in ACCENTED:
            out.append(ch)
            continue
        base = unicodedata.normalize('NFD', ch)[0]
        out.append(base if base in G else {'×': 'X', '→': '>', '«': '"', '»': '"',
                                           '“': '"', '”': '"', '’': "'", '–': '-', '—': '-',
                                           '\n': ' ', '\t': ' '}.get(ch, '?'))
    return re.sub(r' +', ' ', ''.join(out)).strip()

# ---------------------------------------------------------------- colores ---
PAPER = (243, 238, 221, 255)     # papel de patrón
INK = (31, 42, 68, 255)          # tinta azul marino
RULE = (154, 163, 181, 255)      # reglas entre filas
PIVOT = (214, 51, 108, 255)      # muescas del punto de apoyo

LOOPS = ('loop', 'once')
KINDS = ('character', 'creature', 'item', 'prop', 'building', 'effect', 'tile', 'ui')
VIEWS = ('side', 'front', 'three-quarter', 'near-top-down', 'top-down', 'isometric')
DIRS = ('down', 'up', 'left', 'right', 'down-left', 'down-right', 'up-left', 'up-right')
# MIRROR (1.1): la dirección que se obtiene volteando el dibujo en horizontal.
HFLIP = {'left': 'right', 'right': 'left', 'down-left': 'down-right', 'down-right': 'down-left',
         'up-left': 'up-right', 'up-right': 'up-left'}

# ---------------------------------------------------------------- ficha -----
# {"format": "spritevpg", "version": "1.0", "name": "Caballero azul",
#  "kind": "character", "view": "side", "facing": "right",        (opcionales)
#  "mirror": "left",            (opcional, 1.1: volteada sirve para ese lado)
#  "description": "Caballero con armadura azul…",                 (opcional)
#  "agents": {"implement": ["Voltear para la izquierda…"],         (opcional)
#             "extend": ["Contorno oscuro de 1 px…"]},
#  "body": {"x": 5, "y": 0, "w": 21, "h": 32} o "auto",            (opcional)
#  "pivot": {"x": 15, "y": 31} o "auto",                          (opcional)
#  "edited": "2026-11-24 10:32",   (opcional, 2.1: última edición, en UTC;
#                                   `make` pone la hora actual si falta)
#  "frame": {"w": 32, "h": 32}, "grid": {"columns": 6, "rows": 3},
#  "rows": [{"name": "idle", "frames": 2, "ms": [400, 400], "loop": "loop"}, ...]}
# 2.2: una fila puede llevar "names": un nombre por dibujo ("_" si no tiene),
# únicos en toda la hoja: {"name": "items", "names": ["sword", "_", "key"]}.
# Una fila sin "ms" son imágenes sueltas (no es una animación).
# 1.1: una fila puede llevar "facing" (manda sobre el de la hoja) y "mirror"
# (una dirección, o "none" si esa fila no se voltea aunque la hoja sí). Una
# fila con "facing" propio no hereda el "mirror" de la hoja.

def wrap(chunks, width, indent=2):
    """Parte un rótulo en filas de texto; las de continuación van sangradas."""
    rows, cur = [], ''
    for c in chunks:
        if not cur:
            cur = (' ' * indent if rows else '') + c
        elif len(cur) + 1 + len(c) <= width:
            cur += ' ' + c
        else:
            rows.append(cur)
            cur = ' ' * indent + c
    return rows + [cur]

# ---------------------------------------------------------------- dibujo ----
def draw_text(px, col, row, s, fg, y=None):
    """Escribe `s` desde la columna de texto `col`, en la fila de texto `row`
    o, con `y`, a esa altura en píxeles (los rótulos de fila, 1.3)."""
    y0 = row * CH if y is None else y
    for i, ch in enumerate(s):
        if ch == ' ':
            continue
        for r, bits in enumerate(cell_rows(ch)):
            for c, b in enumerate(bits):
                if b == '1':
                    px[(col + i) * CW + c, y0 + r] = fg

def frames_in_row(sheet, r, cols, fw, fh):
    """Cuántos frames con dibujo tiene la fila (seguidos, desde la izquierda)."""
    n = 0
    for c in range(cols):
        if sheet.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)).getbbox():
            if n != c:
                raise SystemExit(f'Fila {r}: hay un hueco antes del frame de la columna {c}.')
            n += 1
    return n

ZONES = ('ANIMATIONS', 'SHEET', 'SUBJECT', 'PALETTE', 'AGENTS')
PALETTE_MAX = 32                   # con más colores solo se escribe cuántos son
EXTRA_KEYS = ('facing', 'mirror')  # columnas de la tabla que solo van si alguna fila las usa
AGENT_KEYS = ('implement', 'extend', 'note')

def keyed(pairs, width):
    """Líneas `CLAVE: valor` con los valores alineados; el valor que no cabe
    sigue debajo, sangrado a la altura del valor."""
    pad = max(len(k) for k, _ in pairs) + 2
    out = []
    for key, val in pairs:
        cur = (key + ':').ljust(pad)
        for word in norm(val).split(' '):
            if len(cur) + len(word) + (0 if cur.endswith(' ') else 1) > width and cur.strip():
                out.append(cur.rstrip())
                cur = ' ' * pad
            cur += ('' if cur.endswith(' ') else ' ') + word
        out.append(cur.rstrip())
    return out

def group(name, pairs):
    """Un grupo: su nombre en una línea y, sangrados debajo, sus datos."""
    pad = max(len(k) for k, _ in pairs) + 2
    return [name] + ['  ' + (k + ':').ljust(pad) + str(v) for k, v in pairs]

def sheet_lines(card, width):
    f, g, pv = card['frame'], card['grid'], card.get('pivot')
    out = keyed([('NAME', card['name'])], width)
    out += group('FRAME', [('WIDTH', f['w']), ('HEIGHT', f['h'])])
    out += group('GRID', [('COLUMNS', g['columns']), ('ROWS', g['rows'])])
    if pv:       # el punto del frame por el que se coloca en el juego
        out += group('PIVOT', [('X', pv['x']), ('Y', pv['y'])])
    return out

def subject_lines(card, width):
    pairs = [(key.upper() if key != 'description' else 'DESC', card[key])
             for key in ('kind', 'view', 'facing', 'mirror', 'description') if card.get(key)]
    out = keyed(pairs, width) if pairs else []
    b = card.get('body')
    if b:        # lo que ocupa el cuerpo quieto dentro de cada frame
        out += group('BODY', [('X', b['x']), ('Y', b['y']), ('WIDTH', b['w']), ('HEIGHT', b['h'])])
    return out

def agent_notes(card):
    """Las indicaciones para IAs como pares (etiqueta, texto). En los datos
    van como {"implement": […], "extend": […], "note": […]}; una lista suelta
    son notas generales."""
    a = card.get('agents') or {}
    if isinstance(a, list):
        a = {'note': a}
    return [(k.upper(), t) for k in AGENT_KEYS for t in a.get(k, [])]

def names_lines(card, width):
    """2.2: el nombre de cada dibujo de una fila (zona NAMES). Una línea por
    fila con nombres: la clave es el nombre de la fila y, después, un nombre
    por celda en el orden de las columnas; «_» es «sin nombre»."""
    pairs = [(norm(r['name']), ' '.join(r['names'])) for r in card['rows'] if r.get('names')]
    return keyed(pairs, width) if pairs else []

def agents_lines(card, width):
    notes = agent_notes(card)
    return keyed(notes, width) if notes else []

def table(card):
    """La tabla de animaciones: (línea de cabeceras, una línea por fila). Cada
    valor empieza en la columna de su cabecera; «-» es «no tiene»."""
    rows = card['rows']
    cols = ['NAME', 'FRAMES', 'MS/FRAME', 'PLAY'] + \
        [k.upper() for k in EXTRA_KEYS if any(r.get(k) for r in rows)]
    def cell(r, c):
        ms = r.get('ms')
        if c == 'NAME':
            return norm(r['name'])
        if c == 'FRAMES':
            return str(r['frames'])
        if c == 'MS/FRAME':
            return '-' if not ms else str(ms[0]) if len(set(ms)) == 1 else ' '.join(map(str, ms))
        if c == 'PLAY':
            return norm(r['loop']) if ms else 'STILL'
        return norm(r.get(c.lower()) or '-')
    t = [cols] + [[cell(r, c) for c in cols] for r in rows]
    w = [max(len(x[i]) for x in t) + 2 for i in range(len(cols))]
    lines = [''.join(v.ljust(w[i]) for i, v in enumerate(x)).rstrip() for x in t]
    return lines[0], lines[1:]

def beside(fh):
    """Si los datos de cada fila caben junto a ella: hace falta una línea de texto."""
    return fh >= CH

def palette_of(sheet):
    """Los colores de los frames, de oscuro a claro."""
    cols = {p[:3] for p in sheet.get_flattened_data() if p[3] >= 128} \
        if hasattr(sheet, 'get_flattened_data') else {p[:3] for p in sheet.getdata() if p[3] >= 128}
    return sorted(cols, key=lambda c: (299 * c[0] + 587 * c[1] + 114 * c[2], c))

def hexcode(c):
    return '#%02X%02X%02X' % tuple(c)

def render(sheet, card):
    fw, fh = card['frame']['w'], card['frame']['h']
    cols, nrows = card['grid']['columns'], card['grid']['rows']
    AW, AH = cols * fw, nrows * fh
    sheet = sheet.convert('RGBA').crop((0, 0, AW, AH))
    spec, link = norm(f'{FORMAT} {VERSION}'), norm(URL)   # las dos filas de la barra final
    lab_col = -(-(AW + 6) // CW)                  # la tabla, a la derecha de los frames
    head, tlines = table(card)
    bes = beside(fh)
    longest = max(len(t) for t in tlines + [head])
    wide = max(len(link) + 2, (lab_col + longest + 1) if bes else (longest + 2))
    has_subject = bool(subject_lines(card, 99))
    half = (wide - 1) // 2 if has_subject else wide
    left = sheet_lines(card, half - 2)
    right = subject_lines(card, wide - half - 3) if has_subject else []
    notes = agents_lines(card, wide - 2)
    cells = names_lines(card, wide - 2)
    pal = palette_of(sheet)
    per = max(1, (wide - 1) // 8)                 # cada color: 7 celdas y un hueco
    shown = pal if len(pal) <= PALETTE_MAX else []
    pal_lines = [f'COLORS: {len(pal)}'] + [''] * (2 * -(-len(shown) // per))
    # Filas de texto: cabeceras de la tabla, zonas y barra final.
    hdr = -(-(AH + 4) // CH)
    an = hdr + 2 if bes else hdr                  # ANIMATIONS, si la tabla no cabe junto a las filas
    nm = an if bes else an + 1 + len(tlines) + 1 + 1     # NAMES, si alguna fila nombra sus dibujos
    top = nm + (1 + len(cells) + 1 if cells else 0)
    pz = top + 1 + max(len(left), len(right)) + 1
    ag = pz + 1 + len(pal_lines) + 1
    bar = ag + (1 + len(notes) + 1 if notes else 0)
    W, H = wide * CW, (bar + 2) * CH
    img = Image.new('RGBA', (W, H), PAPER)
    px = img.load()
    for y in range(AH):
        for x in range(AW):
            px[x, y] = (0, 0, 0, 0)
    img.alpha_composite(sheet, (0, 0))
    px = img.load()
    for y in range(AH + 5):                       # borde de la zona de frames, por fuera,
        px[AW, y] = INK                           # con una marca de corte en la esquina
    for x in range(AW + 5):
        px[x, AH] = INK
    for r in range(1, nrows):                     # marca de celda y línea entre filas de la tabla
        for x in range(AW + 1, AW + 4):
            px[x, r * fh] = INK
        if bes:                                   # justo encima de la fila: nunca pisa texto
            for x in range(lab_col * CW, W):
                px[x, r * fh - 1] = RULE
    for c in range(1, cols):
        for y in range(AH + 1, AH + 4):
            px[c * fw, y] = INK
    if bes:
        # La tabla: cada fila, centrada en la suya al píxel; las cabeceras, debajo.
        for r, t in enumerate(tlines):
            draw_text(px, lab_col, 0, t, INK, y=r * fh + (fh - CH) // 2)
        for x in range(lab_col * CW, W):
            px[x, AH] = INK
        draw_text(px, lab_col, hdr, head, INK)
        if fw >= 8:                               # el número de cada columna, como una regla
            for c in range(cols):
                t = str(c + 1)
                x0 = c * fw + (fw - len(t) * CW + 1) // 2
                for i, ch in enumerate(t):
                    for rr, bits in enumerate(cell_rows(ch)):
                        for cc, b in enumerate(bits):
                            if b == '1':
                                px[x0 + i * CW + cc, hdr * CH + rr] = INK
    pv = card.get('pivot')
    if pv:       # muescas del pivote: a la derecha de cada fila y bajo cada columna
        for r in range(nrows):
            for t in range(3):
                for y in range(r * fh + pv['y'] - t, r * fh + pv['y'] + t + 1):
                    if 0 <= y <= AH:
                        px[AW + 1 + t, y] = PIVOT
        for c in range(cols):
            for t in range(3):
                for x in range(c * fw + pv['x'] - t, c * fw + pv['x'] + t + 1):
                    if 0 <= x <= AW:
                        px[x, AH + 1 + t] = PIVOT

    def zone(title, c0, c1, row, lines):
        for y in range(row * CH, (row + 1) * CH):  # pestaña con el título, en negativo…
            for x in range(c0 * CW, (c0 + len(title) + 2) * CW):
                px[x, y] = INK
        for x in range(c0 * CW, c1 * CW):          # …y una línea hasta el final de la zona
            px[x, row * CH + CH - 1] = INK
        draw_text(px, c0 + 1, row, title, PAPER)
        for j, t in enumerate(lines):
            draw_text(px, c0 + 1, row + 1 + j, t, INK)

    def bar_line(text, row, right=''):             # barra final, maciza
        for y in range(row * CH, (row + 1) * CH):
            for x in range(W):
                px[x, y] = INK
        draw_text(px, 1, row, text, PAPER)
        if right:                                  # 2.1: la última edición, a la derecha
            draw_text(px, wide - 1 - len(right), row, right, PAPER)

    if not bes:
        zone('ANIMATIONS', 0, wide, an, tlines + [head])
    if cells:
        zone('NAMES', 0, wide, nm, cells)
    zone('SHEET', 0, half, top, left)
    if 'PIVOT' in left:                            # leyenda: la muesca, junto a su nombre
        y0 = (top + 1 + left.index('PIVOT')) * CH
        for t in range(4):
            for y in range(y0 + 3 - t, y0 + 3 + t + 1):
                px[7 * CW + 6 - t, y] = PIVOT
    if has_subject:
        zone('SUBJECT', half + 1, wide, top, right)
    zone('PALETTE', 0, wide, pz, pal_lines)
    for i, c in enumerate(shown):                  # barra de color y, debajo, su código
        col, row = 1 + (i % per) * 8, pz + 2 + 2 * (i // per)
        x0, x1, y0 = col * CW, col * CW + 7 * CW - 2, row * CH
        for y in range(y0, y0 + 7):
            for x in range(x0, x1 + 1):
                px[x, y] = INK if y in (y0, y0 + 6) or x in (x0, x1) else tuple(c) + (255,)
        draw_text(px, col, row + 1, hexcode(c), INK)
    if notes:
        zone('AGENTS', 0, wide, ag, notes)
    bar_line(spec, bar, norm(card['edited'] + ' UTC') if card.get('edited') else '')
    bar_line(link, bar + 1)
    return img

# ---------------------------------------------------------------- leer ------
def decode_grid(img, k=1, y0=0, rows=None):
    """La rejilla de caracteres: (carácter, en negativo) por celda; None donde
    no hay un carácter. Las líneas empiezan en el píxel `y0` (de la hoja a
    escala nativa); por defecto, toda la imagen desde arriba."""
    px = img.convert('RGBA').load()
    grid = []
    for row in range(img.height // k // CH if rows is None else rows):
        line = []
        for col in range(img.width // k // CW):
            bits = []
            for r in range(GH):
                for c in range(GW):
                    p = px[(col * CW + c) * k, (y0 + row * CH + r) * k]
                    bits.append('1' if p == INK else '0' if p == PAPER else 'x')
            key = ''.join(bits)
            inv = key.translate(str.maketrans('01', '10'))
            full = all(px[(col * CW + GW) * k, (y0 + row * CH + r) * k] == INK for r in range(CH)) and \
                all(px[(col * CW + c) * k, (y0 + row * CH + GH) * k] == INK for c in range(GW))
            if full and inv in LOOKUP:
                line.append((LOOKUP[inv], True))
            elif key in LOOKUP:
                line.append((LOOKUP[key], False))
            else:
                line.append(None)
        grid.append(line)
    return grid

def row_text(line, negative=False):
    return ''.join(c[0] if c and c[1] == negative else ' ' for c in line).rstrip()

def read_card(path):
    """La ficha de un patrón, leída del dibujo. Devuelve (ficha, escala)."""
    img = Image.open(path)
    for k in range(1, 17):
        if img.width % (CW * k) or img.height % (CH * k):
            continue
        last = decode_grid(img.crop((0, img.height - 2 * CH * k, img.width, img.height)), k)
        if row_text(last[0], True).strip().startswith(norm(FORMAT) + ' ') and row_text(last[1], True).strip():
            break
    else:
        raise SystemExit('No es un sprite pattern: falta la barra final «SPRITEVPG …».')
    grid = decode_grid(img, k)
    version = row_text(grid[-2], True).split()[1]
    if int(version.split('.')[0]) != 2:
        raise SystemExit(f'Versión {version}: esta herramienta lee SpriteVPG 2.x.')
    return read_card_v2(img, k, grid), k

EDITED = re.compile(r'(\d{4}-\d\d-\d\d \d\d:\d\d) UTC\s*$')

def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M')

def tree(lines):
    """Las líneas de una zona como datos: `CLAVE: valor` es un dato; una línea
    sin dos puntos abre un grupo, y las sangradas de debajo son sus datos; una
    línea sangrada tras un dato continúa su valor."""
    out, grp, last = {}, None, None
    for t in lines:
        if not t.strip():
            continue
        if not t.startswith(' '):
            if ':' in t:
                key, _, val = t.partition(':')
                out[key.strip()], grp, last = val.strip(), None, key.strip()
            else:
                grp = out[t.strip()] = {}
        elif grp is not None:
            key, _, val = t.partition(':')
            grp[key.strip()] = val.strip()
        elif last is not None:
            out[last] = (out[last] + ' ' + t.strip()).strip()
    return out

def read_card_v2(img, k, grid):
    """Los datos de un patrón, leídos de la rejilla de texto."""
    version = row_text(grid[-2], True).split()[1]
    # Títulos de zona: una pestaña en negativo con una sola palabra. La zona va
    # desde su pestaña hasta la siguiente de la misma línea (o hasta el borde),
    # y hacia abajo hasta la siguiente pestaña. Las que no se conocen se saltan.
    tabs = []
    for r, line in enumerate(grid[:-2]):
        c = 0
        while c < len(line):
            if line[c] and line[c][1]:
                e = c
                while e + 1 < len(line) and line[e + 1] and line[e + 1][1]:
                    e += 1
                title = ''.join(x[0] for x in line[c:e + 1]).strip()
                if re.fullmatch(r'[A-Z]+', title):
                    tabs.append((r, c, title))
                c = e + 1
            else:
                c += 1
    zones = {}
    for r, c0, title in tabs:
        c1 = min([c for rr, c, _ in tabs if rr == r and c > c0] + [len(grid[r]) + 1]) - 1
        end = min([rr for rr, c, _ in tabs if rr > r and c < c1] + [len(grid) - 2])
        zones[title] = [row_text(grid[rr][c0 + 1:c1]) for rr in range(r + 1, end)]
    if 'SHEET' not in zones:
        raise SystemExit('Falta la zona SHEET.')
    sh, su = tree(zones['SHEET']), tree(zones.get('SUBJECT', []))
    fw, fh = int(sh['FRAME']['WIDTH']), int(sh['FRAME']['HEIGHT'])
    cols, nrows = int(sh['GRID']['COLUMNS']), int(sh['GRID']['ROWS'])
    card = {'format': FORMAT, 'version': version, 'name': sh['NAME']}
    stamp = EDITED.search(row_text(grid[-2], True))    # 2.1: «AAAA-MM-DD HH:MM UTC», a la derecha
    if stamp:
        card['edited'] = stamp.group(1)
    for key in ('KIND', 'VIEW', 'FACING', 'MIRROR'):
        if su.get(key):
            card[key.lower()] = su[key].lower()
    if su.get('DESC'):
        card['description'] = su['DESC']
    if 'BODY' in su:
        b = su['BODY']
        card['body'] = {'x': int(b['X']), 'y': int(b['Y']), 'w': int(b['WIDTH']), 'h': int(b['HEIGHT'])}
    if 'PIVOT' in sh:
        card['pivot'] = {'x': int(sh['PIVOT']['X']), 'y': int(sh['PIVOT']['Y'])}
    notes = []
    for t in zones.get('AGENTS', []):
        if not t.strip():
            continue
        if t.startswith(' ') and notes:
            notes[-1] += ' ' + t.strip()
        else:
            notes.append(t.strip())
    for t in notes:
        key, _, text = t.partition(':')
        if key.lower() not in AGENT_KEYS:
            key, text = 'note', t
        card.setdefault('agents', {}).setdefault(key.lower(), []).append(text.strip())
    pal = ' '.join(zones.get('PALETTE', []))
    codes = re.findall(r'#[0-9A-F]{6}', pal)
    if codes:
        card['palette'] = codes
    card.update({'frame': {'w': fw, 'h': fh}, 'grid': {'columns': cols, 'rows': nrows}, 'rows': []})
    # La tabla de animaciones: junto a las filas (cada línea, centrada en su
    # fila) con las cabeceras debajo; o, si no cabe, en la zona ANIMATIONS.
    if beside(fh):
        lab_col = -(-(cols * fw + 6) // CW)
        head = row_text(grid[-(-(nrows * fh + 4) // CH)][lab_col:])
        lines = [row_text(decode_grid(img, k, r * fh + (fh - CH) // 2, 1)[0][lab_col:]) for r in range(nrows)]
    else:
        t = [x for x in zones.get('ANIMATIONS', []) if x.strip()]
        head, lines = (t[-1], t[:-1]) if t else ('', [])
    if len(lines) != nrows:
        raise SystemExit(f'Hay {len(lines)} filas en la tabla para {nrows} filas de frames.')
    starts = [(m.start(), m.group()) for m in re.finditer(r'\S+', head)]
    for line in lines:
        v = {name: line[a:(starts[i + 1][0] if i + 1 < len(starts) else None)].strip()
             for i, (a, name) in enumerate(starts)}
        row = {'name': v['NAME'].lower(), 'frames': int(v['FRAMES'])}
        if v['PLAY'] != 'STILL':
            ms = [int(x) for x in v['MS/FRAME'].split()]
            row['ms'] = ms * row['frames'] if len(ms) == 1 else ms
            row['loop'] = v['PLAY'].lower()
        for key in EXTRA_KEYS:
            if v.get(key.upper(), '-') not in ('-', ''):
                row[key] = v[key.upper()].lower()
        card['rows'].append(row)
    # 2.2: los nombres de los dibujos de cada fila.
    by_row = {r['name']: r for r in card['rows']}
    for key, val in tree(zones.get('NAMES', [])).items():
        if key.lower() in by_row and isinstance(val, str) and val.split():
            by_row[key.lower()]['names'] = [x.lower() for x in val.split()]
    return card

# ---------------------------------------------------------------- make/read -
def complete(card, sheet):
    fw, fh = card['frame']['w'], card['frame']['h']
    cols, nrows = sheet.width // fw, len(card['rows'])
    out = {'format': FORMAT, 'version': VERSION, 'name': card['name'],
           **{k: card[k] for k in ('kind', 'view', 'facing', 'mirror', 'description', 'agents') if card.get(k)},
           'frame': {'w': fw, 'h': fh}, 'grid': {'columns': cols, 'rows': nrows}, 'rows': []}
    # "body": "auto" mide el primer frame de la fila de referencia (la que se
    # llama "idle"; si no la hay, la primera); "pivot": "auto" es el centro de
    # su base.
    # La última edición: la que diga la ficha; si no dice nada, ahora. Con
    # "edited": null no se escribe.
    edited = card['edited'] if 'edited' in card else now_utc()
    if edited:
        out['edited'] = edited
    body, pivot = card.get('body'), card.get('pivot')
    if body == 'auto' or (pivot == 'auto' and not body):
        names = [str(r.get('name', '')).lower() for r in card['rows']]
        ref = names.index('idle') if 'idle' in names else 0
        x0, y0, x1, y1 = sheet.crop((0, ref * fh, fw, (ref + 1) * fh)).getbbox()
        measured = {'x': x0, 'y': y0, 'w': x1 - x0, 'h': y1 - y0}
        if body == 'auto':
            body = measured
    if pivot == 'auto':
        b = body or measured
        pivot = {'x': b['x'] + (b['w'] - 1) // 2, 'y': b['y'] + b['h'] - 1}
    if body:
        out['body'] = body
    if pivot:
        out['pivot'] = pivot
    for r, row in enumerate(card['rows']):
        n = frames_in_row(sheet, r, cols, fw, fh)
        new = {'name': row['name'].lower(), 'frames': n}
        if row.get('ms'):
            ms = row['ms'] if isinstance(row['ms'], list) else [row['ms']]
            new['ms'] = ms * n if len(ms) == 1 else ms
            new['loop'] = row.get('loop', 'loop')
        for key in ('facing', 'mirror'):
            if row.get(key):
                new[key] = row[key].lower()
        if row.get('names') and any(x and x != '_' for x in row['names']):
            new['names'] = [str(x or '_').lower() for x in row['names']]
        out['rows'].append(new)
    return out

def make(sheet_path, card_path, out, preview=0):
    sheet = Image.open(sheet_path).convert('RGBA')
    card = complete(json.load(open(card_path, encoding='utf-8')), sheet)
    err = validate(card)
    if err:
        raise SystemExit('\n'.join('error: ' + e for e in err))
    img = render(sheet, card)
    img.save(out)
    if preview:        # la copia ampliada es también un sprite pattern válido
        img.resize((img.width * preview, img.height * preview), Image.NEAREST).save(
            out.replace('.png', f'@{preview}x.png'))
    return card, img

def slug(name):
    s = unicodedata.normalize('NFD', name.lower())
    return re.sub(r'[^a-z0-9]+', '_', ''.join(c for c in s if not unicodedata.combining(c))).strip('_') or 'sprite'

def read(path, outdir, gifs=False):
    card, k = read_card(path)
    img = Image.open(path).convert('RGBA')
    if k > 1:
        img = img.resize((img.width // k, img.height // k), Image.NEAREST)
    fw, fh, cols = card['frame']['w'], card['frame']['h'], card['grid']['columns']
    sheet = img.crop((0, 0, cols * fw, card['grid']['rows'] * fh))
    os.makedirs(outdir, exist_ok=True)
    base = slug(card['name'])
    sheet.save(os.path.join(outdir, f'{base}.sheet.png'))
    # Los datos leídos, en el mismo JSON que acepta `make`.
    json.dump(card, open(os.path.join(outdir, f'{base}.card.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    for r, row in enumerate(card['rows']):
        fr = [sheet.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(row['frames'])]
        d = os.path.join(outdir, row['name'])
        os.makedirs(d, exist_ok=True)
        named = row.get('names') or []
        for c, f in enumerate(fr):                 # con nombre, el fichero se llama como el dibujo
            n = named[c] if c < len(named) and named[c] != '_' else str(c)
            f.save(os.path.join(d, f'{n}.png'))
        if gifs and row.get('ms'):
            big = [f.resize((fw * 4, fh * 4), Image.NEAREST) for f in fr]
            big[0].save(os.path.join(outdir, f'{row["name"]}.gif'), save_all=True, append_images=big[1:],
                        duration=row['ms'], loop=0 if row['loop'] == 'loop' else 1, disposal=2)
    return card, k

def validate(card):
    err = []
    if card.get('format') != FORMAT:
        err.append('format debe ser "spritevpg"')
    if not str(card.get('name', '')).strip():
        err.append('falta name')
    if card.get('edited'):
        try:
            datetime.datetime.strptime(str(card['edited']), '%Y-%m-%d %H:%M')
        except ValueError:
            err.append('edited debe ser "AAAA-MM-DD HH:MM" (UTC)')
    for key, known in (('kind', KINDS), ('view', VIEWS), ('facing', DIRS)):
        if card.get(key) and card[key] not in known:
            err.append(f'{key} no válido: {card[key]} (valen: {", ".join(known)})')
    def check_mirror(where, facing, mirror, allow_none=False):
        if not mirror or (allow_none and mirror == 'none'):
            return
        if mirror not in DIRS:
            err.append(f'{where}mirror no válido: {mirror}')
        elif facing and HFLIP.get(facing) != mirror:
            err.append(f'{where}mirror debe ser la dirección volteada de facing '
                       f'({facing} -> {HFLIP.get(facing, "no se voltea")})')
    check_mirror('', card.get('facing'), card.get('mirror'))
    fw, fh = card.get('frame', {}).get('w', 0), card.get('frame', {}).get('h', 0)
    b, pv = card.get('body'), card.get('pivot')
    if b and not (b['w'] > 0 and b['h'] > 0 and 0 <= b['x'] and 0 <= b['y']
                  and b['x'] + b['w'] <= fw and b['y'] + b['h'] <= fh):
        err.append('body no cabe en el frame')
    if pv and not (0 <= pv['x'] < fw and 0 <= pv['y'] < fh):
        err.append('pivot fuera del frame')
    rows = card.get('rows', [])
    if card.get('grid', {}).get('rows') != len(rows):
        err.append('grid.rows no coincide con el número de filas')
    names, cells = set(), set()
    for r, row in enumerate(rows):
        if 'names' in row:                         # 2.2: un nombre por dibujo, únicos en la hoja
            if len(row['names']) != row.get('frames'):
                err.append(f'fila {r}: hace falta un nombre por frame («_» si no tiene)')
            for x in row['names']:
                if not re.fullmatch(r'[a-z0-9_\-]+', str(x)):
                    err.append(f'fila {r}: el nombre «{x}» solo admite a-z, 0-9, _ y -')
                elif x != '_' and x in cells:
                    err.append(f'fila {r}: nombre de dibujo repetido en la hoja ({x})')
                cells.add(x)
        n = row.get('name', '')
        if not re.fullmatch(r'[a-z0-9_\-]+', n):
            err.append(f'fila {r}: name solo admite a-z, 0-9, _ y -')
        if n in names:
            err.append(f'fila {r}: nombre repetido ({n})')
        names.add(n)
        if row.get('facing') and row['facing'] not in DIRS:
            err.append(f'fila {r}: facing no válido: {row["facing"]}')
        check_mirror(f'fila {r}: ', row.get('facing') or card.get('facing'), row.get('mirror'), True)
        if not 1 <= row.get('frames', 0) <= card['grid']['columns']:
            err.append(f'fila {r}: frames fuera de la rejilla')
        if 'ms' in row:
            if len(row['ms']) != row.get('frames') or any(not isinstance(m, int) or m <= 0 for m in row['ms']):
                err.append(f'fila {r}: hace falta un ms positivo por frame')
            if row.get('loop') not in LOOPS:
                err.append(f'fila {r}: loop debe ser loop u once')
    return err

def summary(card):
    fw, fh = card['frame']['w'], card['frame']['h']
    what = ', '.join(f'{k}: {card[k]}' for k in ('kind', 'view', 'facing') if card.get(k))
    if card.get('mirror'):
        what += f' (volteada en horizontal: {card["mirror"]})'
    def turn(row):
        f, m = row.get('facing'), row.get('mirror')
        out = (f', mira a {f}' if f else '')
        if m == 'none':
            out += ', no se voltea'
        elif m:
            out += f', volteada: {m}'
        return out
    out = [f'{card["name"]} · {FORMAT} {card.get("version")}'
           + (f' · editada el {card["edited"]} UTC' if card.get('edited') else '')] + ([what] if what else []) + \
        ([card['description']] if card.get('description') else []) + [
        f'Frames de {fw}x{fh} en {card["grid"]["columns"]}x{card["grid"]["rows"]}, desde 0,0. '
        f'El frame de la fila r y la columna c está en x = c*{fw}, y = r*{fh}.']
    for r, row in enumerate(card['rows']):
        if row.get('ms'):
            ms = f'{row["ms"][0]} ms cada uno' if len(set(row['ms'])) == 1 else ', '.join(map(str, row['ms'])) + ' ms'
            mode = 'en bucle' if row['loop'] == 'loop' else 'una vez'
            out.append(f'- fila {r}: {row["name"]}, {row["frames"]} frames, {ms}, {mode}{turn(row)}')
        else:
            out.append(f'- fila {r}: {row["name"]}, {row["frames"]} imágenes sueltas{turn(row)}')
    if card.get('body'):
        b = card['body']
        out.append(f'El dibujo quieto ocupa {b["w"]}x{b["h"]} px dentro del frame, desde {b["x"]},{b["y"]}.')
    if card.get('pivot'):
        out.append(f'Punto de apoyo: {card["pivot"]["x"]},{card["pivot"]["y"]} dentro de cada frame.')
    if card.get('palette'):
        out.append(f'Paleta de {len(card["palette"])} colores: ' + ' '.join(card['palette']))
    for key, note in agent_notes(card):
        out.append({'IMPLEMENT': 'Al usarla en una app: ', 'EXTEND': 'Al ampliarla: ', 'NOTE': 'Nota: '}[key] + note)
    return '\n'.join(out)

def main(argv=None):
    p = argparse.ArgumentParser(description='SpriteVPG: sprite patterns.')
    sub = p.add_subparsers(dest='cmd', required=True)
    m = sub.add_parser('make', help='hoja limpia + datos (JSON) -> sprite pattern')
    m.add_argument('sheet'); m.add_argument('card')
    m.add_argument('-o', '--out', required=True)
    m.add_argument('--preview', type=int, default=0, help='guarda también una copia ampliada xN')
    r = sub.add_parser('read', help='sprite pattern -> hoja limpia, frames y datos')
    r.add_argument('pattern'); r.add_argument('-o', '--out', required=True)
    r.add_argument('--gifs', action='store_true', help='un GIF por animación')
    for name, hlp in (('info', 'resumen legible'), ('validate', 'comprueba los datos')):
        sub.add_parser(name, help=hlp).add_argument('path')
    a = p.parse_args(argv)

    def load(path):
        if path.lower().endswith('.json'):
            return json.load(open(path, encoding='utf-8'))
        return read_card(path)[0]

    if a.cmd == 'make':
        card, img = make(a.sheet, a.card, a.out, a.preview)
        print(f'{a.out}: {img.width}x{img.height}')
    elif a.cmd == 'read':
        card, k = read(a.pattern, a.out, a.gifs)
        print(f'Datos leídos del dibujo (escala x{k}). {sum(r["frames"] for r in card["rows"])} frames en {a.out}/')
    elif a.cmd == 'info':
        print(summary(load(a.path)))
    else:
        err = validate(load(a.path))
        for e in err:
            print('error:', e)
        print('válida' if not err else f'{len(err)} errores')
        return 1 if err else 0
    return 0

if __name__ == '__main__':
    sys.exit(main())
