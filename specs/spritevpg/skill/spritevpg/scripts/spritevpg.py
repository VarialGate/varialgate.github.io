#!/usr/bin/env python3
"""SpriteVPG: genera, lee y comprueba sprite patterns.

Un sprite pattern es una hoja de sprites PNG con los frames limpios desde la
esquina de arriba a la izquierda y, a la derecha y abajo, la ficha completa
escrita en una rejilla de caracteres con zonas recuadradas. Especificación:
https://varialgate.github.io/specs/spritevpg/

Uso:
  spritevpg.py make  HOJA.png FICHA.json -o PATRON.png [--preview 4]
  spritevpg.py read  PATRON.png -o CARPETA [--gifs]
  spritevpg.py text  PATRON.png|FICHA.json     (la notación de los márgenes)
  spritevpg.py info  PATRON.png|FICHA.json     (resumen legible)
  spritevpg.py validate PATRON.png|FICHA.json

Solo necesita Pillow. La ficha se lee del propio dibujo (cada carácter cae en
una celda fija de la rejilla y se reconoce comparando píxeles), así que
funciona con PNG sin metadatos y con copias ampliadas a escala entera.
"""
import argparse, json, os, re, sys, unicodedata
from collections import Counter

from PIL import Image, PngImagePlugin

FORMAT, VERSION = 'spritevpg', '1.0'
URL = 'https://varialgate.github.io/specs/spritevpg/'
SCHEMA = URL + 'schema/spritevpg-1.schema.json'

# ---------------------------------------------------------------- fuente ----
# SpriteVPG 3x5: la misma tabla que la fuente TTF (font/spritevpg-3x5.ttf).
# Cada carácter ocupa una celda de 4x7: fila 0 para la tilde, filas 1-5 para
# el glifo de 3x5 y fila 6 y columna 3 libres (por ahí pasan las reglas).
G = {
 'A': '010 101 111 101 101', 'B': '110 101 110 101 110', 'C': '011 100 100 100 011',
 'D': '110 101 101 101 110', 'E': '111 100 110 100 111', 'F': '111 100 110 100 100',
 'G': '011 100 101 101 011', 'H': '101 101 111 101 101', 'I': '111 010 010 010 111',
 'J': '001 001 001 101 010', 'K': '101 101 110 101 101', 'L': '100 100 100 100 111',
 'M': '111 111 101 101 101', 'N': '110 101 101 101 101', 'O': '111 101 101 101 111',
 'P': '110 101 110 100 100', 'Q': '111 101 101 110 011', 'R': '110 101 110 101 101',
 'S': '011 100 010 001 110', 'T': '111 010 010 010 010', 'U': '101 101 101 101 111',
 'V': '101 101 101 101 010', 'W': '101 101 101 111 111', 'X': '101 101 010 101 101',
 'Y': '101 101 010 010 010', 'Z': '111 001 010 100 111',
 '0': '010 101 101 101 010', '1': '010 110 010 010 111', '2': '110 001 010 100 111',
 '3': '110 001 010 001 110', '4': '101 101 111 001 001', '5': '111 100 110 001 110',
 '6': '011 100 111 101 111', '7': '111 001 010 010 010', '8': '111 101 111 101 111',
 '9': '111 101 111 001 110',
 ' ': '000 000 000 000 000', '.': '000 000 000 000 010', ',': '000 000 000 010 100',
 ':': '000 010 000 010 000', ';': '000 010 000 010 100', '-': '000 000 111 000 000',
 '+': '000 010 111 010 000', '/': '001 001 010 100 100', '(': '010 100 100 100 010',
 ')': '010 001 001 001 010', '[': '110 100 100 100 110', ']': '011 001 001 001 011',
 '=': '000 111 000 111 000', '#': '101 111 101 111 101', '<': '001 010 100 010 001',
 '>': '100 010 001 010 100', '*': '101 010 111 010 101', '%': '101 001 010 100 101',
 '_': '000 000 000 000 111', '"': '101 101 000 000 000', "'": '010 010 000 000 000',
 '!': '010 010 010 000 010', '?': '110 001 010 000 010', '&': '010 101 010 101 011',
 '·': '000 000 010 000 000', '¿': '010 000 010 100 011', '¡': '010 000 010 010 010',
}
G = {k: v.split() for k, v in G.items()}
# Tildes: en la fila 0 de la celda, sobre la letra.
ACUTE, TILDE, DIAER = '010', '111', '101'
ACCENTED = {'Á': ('A', ACUTE), 'É': ('E', ACUTE), 'Í': ('I', ACUTE), 'Ó': ('O', ACUTE),
            'Ú': ('U', ACUTE), 'Ü': ('U', DIAER), 'Ñ': ('N', TILDE)}
CW, CH = 4, 7

def cell_rows(ch):
    """Las 6 filas (tilde + 5) de un carácter, como cadenas de 3 bits."""
    if ch in ACCENTED:
        base, acc = ACCENTED[ch]
        return [acc] + G[base]
    return ['000'] + G[ch]

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
RULE = (154, 163, 181, 255)      # reglas secundarias y marcas de celda
PIVOT = (214, 51, 108, 255)      # apoyo
BOX = {'collision': (47, 158, 68, 255), 'hurt': (240, 140, 0, 255),
       'hit': (224, 49, 49, 255), 'interact': (28, 126, 214, 255)}
BOX_OTHER = (112, 72, 232, 255)
POINT = (112, 72, 232, 255)
CHECK = ((255, 255, 255, 255), (228, 223, 206, 255))

# ---------------------------------------------------------------- vocabulario
KINDS = ['character', 'creature', 'item', 'prop', 'building', 'effect', 'tile']
VIEWS = ['side', 'front', 'threeQuarter', 'oblique', 'topDown', 'isometric']
DIRS = ['down', 'up', 'left', 'right', 'down-left', 'down-right', 'up-left', 'up-right']
LOOPS = ['loop', 'once', 'pingpong', 'hold']
SHADOWS = ['none', 'baked', 'separate']
OUTLINES = ['dark', 'colored', 'none']
ZONES = ['ENTITY', 'SHEET', 'ART', 'BODY', 'DETAIL', 'ANIMATIONS', 'DIRECTIONS',
         'STATES', 'WORLD', 'STYLE', 'AI', 'PROVENANCE']

def ident(s, known=()):
    """Un identificador leído del dibujo (mayúsculas) a como va en la ficha."""
    low = s.lower()
    for k in known:
        if k.lower() == low:
            return k
    return low

# ---------------------------------------------------------------- notación --
# La ficha, escrita como líneas `CLAVE valor` por zonas. Es lo que se dibuja
# en los márgenes y lo que se vuelve a leer.

def ranges(nums):
    out, nums = [], sorted(nums)
    i = 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(f'{nums[i]}-{nums[j]}' if j > i else f'{nums[i]}')
        i = j + 1
    return ' '.join(out)

def pt(p):
    return f'{p["x"]},{p["y"]}'

def rect(b):
    return f'{b["x"]},{b["y"]} {b["w"]}X{b["h"]}'

def geometry_chunks(o):
    """PIVOT, BOX y POINT de un frame o de defaults."""
    out = []
    if 'pivot' in o:
        out.append(f'PIVOT {pt(o["pivot"])}')
    for name, b in o.get('boxes', {}).items():
        out.append(f'BOX {name} {rect(b)}')
    for name, p in o.get('points', {}).items():
        out.append(f'POINT {name} {pt(p)}')
    return out

def notation(card):
    """Zonas de la ficha: lista de (título, [línea lógica]). Una línea lógica
    es una lista de trozos que no se parten al ajustar el texto."""
    def words(key, text):
        return [key] + norm(text).split(' ')
    z = []
    e = card['entity']
    lines = [['NAME', e['name']]]
    if e.get('displayName'):
        lines.append(words('TITLE', e['displayName']))
    lines.append(['KIND', e['kind']])
    if e.get('tags'):
        lines.append(['TAGS'] + [t for t in (', '.join(e['tags'])).split(' ')])
    if e.get('description'):
        lines.append(words('DESC', e['description']))
    z.append(('ENTITY', lines))

    g = card['grid']
    lines = [['FRAME', f'{g["frameSize"]["w"]}X{g["frameSize"]["h"]}'],
             ['GRID', f'{g["columns"]}X{g["rows"]}'],
             ['FRAMES'] + ranges(f['i'] for f in card['frames']).split(' ')]
    z.append(('SHEET', lines))

    a = card['art']
    lines = []
    if a.get('view'):
        lines.append(['VIEW', a['view']])
    if a.get('facing'):
        lines.append(['FACING', a['facing']])
    if a.get('light'):
        lines.append(words('LIGHT', a['light']))
    if a.get('outline'):
        o = a['outline']
        lines.append(['OUTLINE', o.get('style', 'dark'), str(o.get('width', 1))]
                     + ([o['color'].lstrip('#')] if o.get('color') else []))
    if a.get('shadow'):
        lines.append(['SHADOW', a['shadow']])
    if a.get('palette'):
        lines.append(['PALETTE'] + [p['color'].lstrip('#') + (':' + p['role'] if p.get('role') else '')
                                    for p in a['palette']])
    z.append(('ART', lines))

    d = card.get('defaults', {})
    lines = [c.split(' ') for c in geometry_chunks(d)]
    for f in card['frames']:
        extra = geometry_chunks(f)
        if extra:
            lines.append([f'F{f["i"]}'] + extra)
    z.append(('BODY', lines))

    if card.get('animations'):
        lines = []
        for an in card['animations']:
            head = [an['name']]
            if an.get('direction'):
                head.append(an['direction'])
            head.append(an.get('loop', 'loop'))
            if an.get('next'):
                head += ['>', an['next']]
            chunks = [' '.join(head)]
            fr = an['frames']
            i = 0
            while i < len(fr):
                f = fr[i]
                extra = list(f.get('events', []))
                if 'offset' in f:
                    extra.append(f'OFFSET {f["offset"].get("dx", 0)},{f["offset"].get("dy", 0)}')
                extra += geometry_chunks(f)
                j = i
                if not extra:      # frames seguidos, misma duración, sin nada más
                    while (j + 1 < len(fr) and fr[j + 1]['frame'] == fr[j]['frame'] + 1
                           and fr[j + 1]['ms'] == f['ms'] and set(fr[j + 1]) == {'frame', 'ms'}):
                        j += 1
                tag = f'F{f["frame"]}' + (f'-{fr[j]["frame"]}' if j > i else '')
                chunks.append(' '.join([tag, str(f['ms'])] + extra))
                i = j + 1
            lines.append(chunks)
        z.append(('ANIMATIONS', lines))

    dr = card.get('directions')
    if dr:
        lines = [['SET'] + list(dr.get('set', []))]
        for dst, m in dr.get('mirror', {}).items():
            lines.append(['MIRROR', dst, '=', m['from'], 'FLIP', m.get('flip', 'x')])
        z.append(('DIRECTIONS', lines))

    if card.get('states'):
        lines = []
        for s in card['states']:
            ln = [s['name'], f'F{s["frame"]}' if 'frame' in s else f'ANIM {s["animation"]}']
            if s.get('group'):
                ln.append(f'GROUP {s["group"]}')
            if s.get('default'):
                ln.append('DEFAULT')
            lines.append(ln)
        z.append(('STATES', lines))

    w = card.get('world')
    if w:
        lines = []
        if 'pixelsPerUnit' in w:
            lines.append(['PPU', f'{w["pixelsPerUnit"]:g}'])
        if w.get('footprint'):
            fp = w['footprint']
            ln = ['FOOTPRINT', f'{fp["w"]}X{fp["h"]}', f'TILE {fp["tileSize"]}']
            if fp.get('origin'):
                ln.append(f'ORIGIN {pt(fp["origin"])}')
            lines.append(ln)
        if 'sortY' in w:
            lines.append(['SORTY', str(w['sortY'])])
        if w.get('shadow'):
            sh = w['shadow']
            ln = ['SHADOW', f'F{sh["frame"]}']
            if sh.get('offset'):
                ln.append(f'OFFSET {sh["offset"].get("dx", 0)},{sh["offset"].get("dy", 0)}')
            lines.append(ln)
        z.append(('WORLD', lines))

    st = card.get('style')
    if st:
        lines = []
        if st.get('summary'):
            lines.append(words('SUMMARY', st['summary']))
        if st.get('proportions'):
            lines.append(words('PROPORTIONS', st['proportions']))
        for r in st.get('rules', []):
            lines.append(words('RULE', r))
        if st.get('reference', {}).get('frame') is not None:
            lines.append(['REFERENCE', f'F{st["reference"]["frame"]}'])
        z.append(('STYLE', lines))

    ai = card.get('ai', {})
    lines = []
    if ai.get('summary'):
        lines.append(words('SUMMARY', ai['summary']))
    for h in ai.get('howTo', []):
        lines.append(words('HOWTO', h))
    for h in ai.get('warnings', []):
        lines.append(words('WARNING', h))
    z.append(('AI', lines))

    p = card.get('provenance', {})
    gen = p.get('generator', {})
    lines = []
    for key, val in [('APP', gen.get('app')), ('VERSION', gen.get('version')), ('MODEL', gen.get('model')),
                     ('CREATED', p.get('created')), ('AUTHOR', p.get('author')),
                     ('LICENSE', p.get('license')), ('PROMPT', p.get('prompt'))]:
        if val:
            lines.append(words(key, val))
    z.append(('PROVENANCE', lines))
    return [(t, [[norm(c) for c in ln] for ln in lines]) for t, lines in z]

def wrap_line(chunks, width, indent=2):
    """Ajusta una línea lógica al ancho. Las filas de continuación van
    sangradas: así se sabe, al leer, que siguen a la anterior."""
    rows, cur = [], ''
    for c in chunks:
        pieces = [c] if len(c) <= width - indent else c.split(' ')
        for p in pieces:
            first = not rows and not cur
            room = width if first else width - indent
            while len(p) > room:                    # palabra más larga que la fila
                if cur:
                    rows.append(cur); cur = ''
                rows.append(('' if first else ' ' * indent) + p[:room])
                p, first, room = p[room:], False, width - indent
            if not cur:
                cur = ('' if not rows else ' ' * indent) + p
            elif len(cur) + 1 + len(p) <= width:
                cur += ' ' + p
            else:
                rows.append(cur)
                cur = ' ' * indent + p
    if cur:
        rows.append(cur)
    return rows

def notation_text(card, width=70):
    out = []
    for title, lines in notation(card):
        out.append(f'[{title}]')
        for ln in lines:
            out += wrap_line(ln, width)
    return '\n'.join(out)

# ---------------------------------------------------------------- lectura ---
INT = r'-?\d+'

def parse_pt(s):
    x, y = s.split(',')
    return {'x': int(x), 'y': int(y)}

def parse_size(s):
    w, h = s.upper().split('X')
    return int(w), int(h)

def parse_geometry(tokens, into):
    """Consume PIVOT/BOX/POINT/OFFSET de una lista de palabras; devuelve el resto."""
    rest, i = [], 0
    while i < len(tokens):
        t = tokens[i]
        if t == 'PIVOT':
            into['pivot'] = parse_pt(tokens[i + 1]); i += 2
        elif t == 'BOX':
            w, h = parse_size(tokens[i + 3])
            into.setdefault('boxes', {})[ident(tokens[i + 1])] = {**parse_pt(tokens[i + 2]), 'w': w, 'h': h}
            i += 4
        elif t == 'POINT':
            into.setdefault('points', {})[ident(tokens[i + 1])] = parse_pt(tokens[i + 2]); i += 3
        elif t == 'OFFSET':
            dx, dy = tokens[i + 1].split(',')
            into['offset'] = {'dx': int(dx), 'dy': int(dy)}; i += 2
        else:
            rest.append(t); i += 1
    return rest

def expand(spec):
    out = []
    for part in spec:
        a, _, b = part.partition('-')
        out += list(range(int(a), int(b or a) + 1))
    return out

def parse_notation(zones):
    """De {zona: [línea lógica (cadena)]} a la ficha. El texto libre queda en
    mayúsculas, como está dibujado."""
    card = {'format': FORMAT, 'version': VERSION, '$schema': SCHEMA}
    def kv(zone):
        for ln in zones.get(zone, []):
            key, _, val = ln.partition(' ')
            yield key, val.strip()
    e = {}
    for k, v in kv('ENTITY'):
        if k == 'NAME': e['name'] = ident(v)
        elif k == 'TITLE': e['displayName'] = v
        elif k == 'KIND': e['kind'] = ident(v, KINDS)
        elif k == 'TAGS': e['tags'] = [t.strip() for t in v.split(',') if t.strip()]
        elif k == 'DESC': e['description'] = v
    card['entity'] = {k: e[k] for k in ('kind', 'name', 'displayName', 'description', 'tags') if k in e}
    grid, frame_ids = {}, []
    for k, v in kv('SHEET'):
        if k == 'FRAME':
            w, h = parse_size(v); grid['frameSize'] = {'w': w, 'h': h}
        elif k == 'GRID':
            c, r = parse_size(v); grid['columns'], grid['rows'] = c, r
        elif k == 'FRAMES':
            frame_ids = expand(v.split())
    art = {}
    for k, v in kv('ART'):
        if k == 'VIEW': art['view'] = ident(v, VIEWS)
        elif k == 'FACING': art['facing'] = ident(v)
        elif k == 'LIGHT': art['light'] = v.lower()
        elif k == 'OUTLINE':
            t = v.split()
            art['outline'] = {'style': ident(t[0]), 'width': int(t[1])}
            if len(t) > 2: art['outline']['color'] = '#' + t[2].lower()
        elif k == 'SHADOW': art['shadow'] = ident(v)
        elif k == 'PALETTE':
            art['palette'] = []
            for t in v.split():
                col, _, role = t.partition(':')
                art['palette'].append({'color': '#' + col.lower(), **({'role': ident(role)} if role else {})})
    card['art'] = art
    fw, fh = grid['frameSize']['w'], grid['frameSize']['h']
    card['grid'] = {'columns': grid['columns'], 'rows': grid['rows'],
                    'frameSize': grid['frameSize'], 'margin': 0, 'spacing': 0}
    frames = {i: {'i': i, 'x': (i % grid['columns']) * fw, 'y': (i // grid['columns']) * fh, 'w': fw, 'h': fh}
              for i in frame_ids}
    defaults = {}
    for ln in zones.get('BODY', []):
        t = ln.split()
        if re.fullmatch(r'F\d+', t[0]):
            parse_geometry(t[1:], frames[int(t[0][1:])])
        else:
            parse_geometry(t, defaults)
    card['frames'] = [frames[i] for i in sorted(frames)]
    card['defaults'] = defaults
    dr = {}
    for k, v in kv('DIRECTIONS'):
        t = v.split()
        if k == 'SET': dr['set'] = [ident(x) for x in t]
        elif k == 'MIRROR':
            dr.setdefault('mirror', {})[ident(t[0])] = {'from': ident(t[2]), 'flip': ident(t[4]) if len(t) > 4 else 'x'}
    if dr:
        card['directions'] = dr
    anims = []
    for ln in zones.get('ANIMATIONS', []):
        t = ln.split()
        k = next((i for i, x in enumerate(t) if re.fullmatch(r'F\d+(-\d+)?', x)), len(t))
        head, body = t[:k], t[k:]
        an = {'name': ident(head[0])}
        h = head[1:]
        if '>' in h:
            an['next'] = ident(h[h.index('>') + 1]); h = h[:h.index('>')]
        for x in h:
            if x.lower() in DIRS: an['direction'] = x.lower()
            elif x.lower() in LOOPS: an['loop'] = x.lower()
        an = {k_: an[k_] for k_ in ('name', 'direction', 'loop', 'next') if k_ in an}
        an['frames'] = []
        i = 0
        while i < len(body):
            j = i + 1
            while j < len(body) and not re.fullmatch(r'F\d+(-\d+)?', body[j]):
                j += 1
            ids = expand([body[i][1:]])
            ms, extra = int(body[i + 1]), {}
            events = [ident(x) for x in parse_geometry(body[i + 2:j], extra)]
            for n in ids:
                f = {'frame': n, 'ms': ms}
                if events: f['events'] = list(events)
                f.update({k_: extra[k_] for k_ in ('offset', 'pivot', 'boxes', 'points') if k_ in extra})
                an['frames'].append(f)
            i = j
        anims.append(an)
    if anims:
        card['animations'] = anims
    states = []
    for ln in zones.get('STATES', []):
        t = ln.split()
        s = {'name': ident(t[0])}
        i = 1
        while i < len(t):
            if re.fullmatch(r'F\d+', t[i]): s['frame'] = int(t[i][1:]); i += 1
            elif t[i] == 'ANIM': s['animation'] = ident(t[i + 1]); i += 2
            elif t[i] == 'GROUP': s['group'] = ident(t[i + 1]); i += 2
            elif t[i] == 'DEFAULT': s['default'] = True; i += 1
            else: i += 1
        states.append(s)
    if states:
        card['states'] = states
    w = {}
    for k, v in kv('WORLD'):
        t = v.split()
        if k == 'PPU': w['pixelsPerUnit'] = float(v) if '.' in v else int(v)
        elif k == 'FOOTPRINT':
            a, b = parse_size(t[0]); fp = {'tileSize': int(t[t.index('TILE') + 1]), 'w': a, 'h': b}
            if 'ORIGIN' in t: fp['origin'] = parse_pt(t[t.index('ORIGIN') + 1])
            w['footprint'] = fp
        elif k == 'SORTY': w['sortY'] = int(v)
        elif k == 'SHADOW':
            sh = {'frame': int(t[0][1:])}
            if 'OFFSET' in t:
                dx, dy = t[t.index('OFFSET') + 1].split(','); sh['offset'] = {'dx': int(dx), 'dy': int(dy)}
            w['shadow'] = sh
    if w:
        card['world'] = w
    st = {}
    for k, v in kv('STYLE'):
        if k == 'SUMMARY': st['summary'] = v
        elif k == 'PROPORTIONS': st['proportions'] = v
        elif k == 'RULE': st.setdefault('rules', []).append(v)
        elif k == 'REFERENCE': st['reference'] = {'frame': int(v[1:])}
    if st:
        card['style'] = st
    ai = {}
    for k, v in kv('AI'):
        if k == 'SUMMARY': ai['summary'] = v
        elif k == 'HOWTO': ai.setdefault('howTo', []).append(v)
        elif k == 'WARNING': ai.setdefault('warnings', []).append(v)
    card['ai'] = ai
    p, gen = {}, {}
    for k, v in kv('PROVENANCE'):
        if k in ('APP', 'VERSION', 'MODEL'): gen[k.lower()] = v
        elif k in ('CREATED', 'AUTHOR', 'LICENSE', 'PROMPT'): p[k.lower()] = v
    card['provenance'] = {**({'generator': gen} if gen else {}), **p}
    return card

def normalized(card):
    """La ficha tal como se lee del dibujo (texto libre en mayúsculas)."""
    zones = {}
    for title, lines in notation(card):
        zones[title] = [' '.join(ln) for ln in lines]
    out = parse_notation(zones)
    if 'image' in card:
        out['image'] = card['image']
    return out

# ---------------------------------------------------------------- dibujo ----
class Canvas:
    def __init__(self, img):
        self.img, self.px = img, img.load()

    def text(self, col, row, s, fg=INK):
        for i, ch in enumerate(s):
            if ch == ' ':
                continue
            x0, y0 = (col + i) * CW, row * CH
            for r, bits in enumerate(cell_rows(ch)):
                for c, b in enumerate(bits):
                    if b == '1':
                        self.px[x0 + c, y0 + r] = fg

    def h(self, x0, x1, y, col):
        for x in range(x0, x1 + 1):
            self.px[x, y] = col

    def v(self, x, y0, y1, col):
        for y in range(y0, y1 + 1):
            self.px[x, y] = col

    def rect(self, x, y, w, h, col):
        self.h(x, x + w - 1, y, col); self.h(x, x + w - 1, y + h - 1, col)
        self.v(x, y, y + h - 1, col); self.v(x + w - 1, y, y + h - 1, col)

    def fill(self, x, y, w, h, col):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.px[xx, yy] = col

def auto_palette(sheet, n=16):
    data = sheet.convert('RGBA')
    px = data.get_flattened_data() if hasattr(data, 'get_flattened_data') else data.getdata()
    cnt = Counter(p[:3] for p in px if p[3])
    return ['#%02x%02x%02x' % c for c, _ in cnt.most_common(n)]

def hex_rgba(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)

def frame_rect(card, i):
    for f in card.get('frames', []):
        if f['i'] == i:
            return f
    g = card['grid']
    c, fw, fh = g['columns'], g['frameSize']['w'], g['frameSize']['h']
    return {'i': i, 'x': (i % c) * fw, 'y': (i // c) * fh, 'w': fw, 'h': fh}

def frame_value(card, i, kind, name=None):
    """Apoyo, caja o punto de un frame: el del frame en una animación, si no
    el de frames[], si no el de defaults."""
    def pick(o):
        v = o.get(kind)
        return (v or {}).get(name) if name is not None else v
    val = pick(card.get('defaults', {}))
    own = pick(next((f for f in card.get('frames', []) if f['i'] == i), {}))
    for a in card.get('animations', []):
        for af in a['frames']:
            if af['frame'] == i and pick(af) is not None:
                own = pick(af)
    return own if own is not None else val

def box_color(name):
    return BOX.get(name, BOX_OTHER)

def row_labels(card, r, cols, nlines):
    first, last = r * cols, r * cols + cols - 1
    anims = [a for a in card.get('animations', []) if first <= a['frames'][0]['frame'] <= last]
    states = [s for s in card.get('states', []) if 'frame' in s and first <= s['frame'] <= last]
    lines = []
    for a in anims:
        ids = [f['frame'] for f in a['frames']]
        ms = {f['ms'] for f in a['frames']}
        lines += [' '.join([a['name']] + ([a['direction']] if a.get('direction') else [])),
                  'F' + ranges(sorted(set(ids))).replace(' ', ' F'),
                  a.get('loop', 'loop') + (' > ' + a['next'] if a.get('next') else ''),
                  (f'{ms.pop()} MS' if len(ms) == 1 else 'MS: SEE ANIMATIONS')]
    if not anims and states:
        lines = [' '.join(s['name'] for s in states)]
    return [norm(x) for x in lines][:nlines]

def layout_rows(zones, wide):
    """Filas de zonas: (título, ancho en columnas, líneas ya ajustadas)."""
    z = dict(zones)
    half_l, half_r = (wide - 1) // 2, wide - 1 - (wide - 1) // 2
    def wrapped(title, width):
        out = []
        for ln in z[title]:
            out += wrap_line(ln, width - 2)
        return out
    rows = [[('ENTITY', half_l), ('SHEET', half_r)], [('ART', wide - 1)], [('BODY', half_l), ('DETAIL', half_r)]]
    if 'ANIMATIONS' in z:
        rows.append([('ANIMATIONS', wide - 1)])
    small = [t for t in ('DIRECTIONS', 'STATES', 'WORLD') if t in z]
    while small:
        pair = small[:2]; small = small[2:]
        rows.append([(pair[0], half_l), (pair[1], half_r)] if len(pair) == 2 else [(pair[0], wide - 1)])
    for t in ('STYLE', 'AI', 'PROVENANCE'):
        if t in z:
            rows.append([(t, wide - 1)])
    return [[(t, w, wrapped(t, w) if t != 'DETAIL' else None) for t, w in row] for row in rows]

def render(sheet, card):
    """Dibuja el sprite pattern a partir de la hoja limpia y la ficha."""
    g = card['grid']
    cols, rows = g['columns'], g['rows']
    fw, fh = g['frameSize']['w'], g['frameSize']['h']
    AW, AH = cols * fw, rows * fh
    sheet = sheet.convert('RGBA').crop((0, 0, AW, AH))
    piv = card.get('defaults', {}).get('pivot', {'x': fw // 2, 'y': fh - 1})

    # Rótulos de fila, a la derecha de la zona de frames.
    nlines = max(1, (fh - 8) // CH)
    labels = [row_labels(card, r, cols, nlines) for r in range(rows)]
    lab_col = -(-(AW + 8) // CW)
    lab_w = max([8] + [len(t) for ls in labels for t in ls])
    wide = max(72, lab_col + lab_w + 1)            # ancho de la hoja en caracteres
    W = wide * CW

    # Detalles: el frame de referencia y uno con cajas propias.
    ref = card.get('style', {}).get('reference', {}).get('frame')
    if ref is None:
        ref = card['frames'][0]['i']
    details = [ref]
    for a in card.get('animations', []):
        for af in a['frames']:
            if af.get('boxes') and af['frame'] not in details and len(details) < 2:
                details.append(af['frame'])
    half_r = wide - 1 - (wide - 1) // 2
    # Margen alrededor de cada detalle para las cajas que sobresalen del frame.
    padl = padt = padr = padb = 0
    for i in details:
        for bx in (frame_value(card, i, 'boxes') or {}).values():
            padl, padt = max(padl, -bx['x']), max(padt, -bx['y'])
            padr, padb = max(padr, bx['x'] + bx['w'] - fw), max(padb, bx['y'] + bx['h'] - fh)
    padl, padt, padr, padb = (min(v, fw) for v in (padl, padt, padr, padb))
    k = 2 if ((fw + padl + padr) * 2 + 6 + 4 * CW) * len(details) <= (half_r - 2) * CW else 1
    legend = []
    for b in list(BOX) + sorted({n for i in details for n in (frame_value(card, i, 'boxes') or {}) if n not in BOX}):
        if any(frame_value(card, i, 'boxes', b) for i in details):
            legend.append((box_color(b), norm(b)))
    for pname in sorted({p for i in details for p in (frame_value(card, i, 'points') or {})}):
        legend.append((POINT, norm(pname)))
    legend.append((PIVOT, 'PIVOT'))
    det_h = (fh + padt + padb) * k + 3
    det_rows = -(-det_h // CH) + -(-len(legend) // 2)

    zones = notation(card)
    lay = layout_rows(zones + [('DETAIL', [])], wide)
    strip_row = -(-(AH + 7) // CH)                 # fila de texto de los números de columna
    top = strip_row + 2                            # primera fila de la primera zona
    total = top
    heights = []
    for row in lay:
        # barra de título + contenido + una fila libre antes de la regla de abajo
        hgt = 2 + max((det_rows if t == 'DETAIL' else len(ls)) for t, w, ls in row)
        heights.append(hgt)
        total += hgt
    H = (total + 1) * CH                           # + la barra del enlace

    img = Image.new('RGBA', (W, H), PAPER)
    cv = Canvas(img)
    cv.fill(0, 0, AW, AH, (0, 0, 0, 0))
    img.alpha_composite(sheet, (0, 0))
    cv = Canvas(img)

    # Borde de la zona de frames (por fuera) y panel de filas.
    cv.v(AW, 0, AH, INK)
    cv.h(0, AW, AH, INK)
    for r in range(rows):
        y0 = r * fh
        if r:
            cv.h(AW + 1, AW + 3, y0, INK)                    # marca entre filas
            cv.h(AW + 5, W - 1, y0, RULE)                    # separa los rótulos
        ay = y0 + piv['y']                                    # muesca del apoyo
        for t in range(3):
            cv.v(AW + 1 + t, ay - t, ay + t, PIVOT)
        ty = -(-(y0 + 2) // CH)
        for j, t in enumerate(labels[r]):
            cv.text(lab_col, ty + j, t)
    for c in range(cols):
        x0 = c * fw
        if c:
            cv.v(x0, AH + 1, AH + 3, INK)                    # marca entre columnas
        ax = x0 + piv['x']
        for t in range(3):
            cv.h(ax - t, ax + t, AH + 1 + t, PIVOT)
        s = str(c)
        cx = round((x0 + fw / 2 - (len(s) * CW - 1) / 2) / CW)
        if len(s) * CW <= fw:
            cv.text(cx, strip_row, s)

    # Zonas.
    y = top
    for row, hgt in zip(lay, heights):
        x = 1
        for title, w, ls in row:
            px0, px1 = x * CW - 1, (x + w) * CW - 1
            py0, py1 = y * CH, (y + hgt) * CH - 1
            cv.fill(px0, py0, px1 - px0 + 1, CH, INK)        # barra de título
            cv.text(x + 1, y, title, PAPER)
            cv.v(px0, py0, py1, INK); cv.v(px1, py0, py1, INK)
            cv.h(px0, px1, py1, INK)
            if title == 'DETAIL':
                dx = (x + 1) * CW + padl * k
                dy = (y + 1) * CH + 2 + padt * k
                for i in details:
                    fr = frame_rect(card, i)
                    for yy in range(dy, dy + fh * k):
                        for xx in range(dx, dx + fw * k):
                            cv.px[xx, yy] = CHECK[((xx - dx) // 4 + (yy - dy) // 4) % 2]
                    crop = sheet.crop((fr['x'], fr['y'], fr['x'] + fw, fr['y'] + fh))
                    img.alpha_composite(crop.resize((fw * k, fh * k), Image.NEAREST), (dx, dy))
                    cv = Canvas(img)
                    for b, bx in sorted(((b, frame_value(card, i, 'boxes', b))
                                         for b in (frame_value(card, i, 'boxes') or {})),
                                        key=lambda t: -t[1]['w'] * t[1]['h']):
                        cv.rect(dx + bx['x'] * k, dy + bx['y'] * k, bx['w'] * k, bx['h'] * k, box_color(b))
                    for pname, p in (frame_value(card, i, 'points') or {}).items():
                        qx, qy = dx + p['x'] * k, dy + p['y'] * k
                        cv.h(qx - 2, qx + 2, qy, POINT); cv.v(qx, qy - 2, qy + 2, POINT)
                    pv = frame_value(card, i, 'pivot') or piv
                    qx, qy = dx + pv['x'] * k, min(dy + pv['y'] * k, dy + fh * k - 1)
                    cv.h(qx - 2, qx + 2, qy, PIVOT); cv.v(qx, qy - 2, qy, PIVOT)
                    cv.text(-(-(dx + (fw + padr) * k + 2) // CW), y + 1, f'F{i}')
                    dx += (fw + padr + padl) * k + 6 + CW * (len(str(i)) + 2)
                ly = y + 1 + -(-det_h // CH)
                colw = (w - 2) // 2
                for n, (col, name) in enumerate(legend):
                    lx, lr = x + 1 + (n % 2) * colw, ly + n // 2
                    cv.fill(lx * CW, lr * CH + 1, 3, 5, col)
                    cv.text(lx + 2, lr, name[:colw - 3])
            else:
                for j, t in enumerate(ls):
                    cv.text(x + 1, y + 1 + j, t)
                if title == 'ART':
                    # Muestras de la paleta: a la derecha de las primeras filas,
                    # donde las líneas de texto son cortas.
                    pal = card['art'].get('palette', [])
                    free = (w - 2 - max([0] + [len(t) for t in ls[:2]]) - 2) * CW
                    size = 9 if len(pal) * 10 <= free else 6
                    if len(pal) * (size + 1) <= free and len(ls) >= 2:
                        sx = px1 - 3 - len(pal) * (size + 1)
                        sy = py0 + CH + 2
                        for n, p in enumerate(pal):
                            cv.fill(sx + n * (size + 1), sy, size, size, INK)
                            cv.fill(sx + n * (size + 1) + 1, sy + 1, size - 2, size - 2, hex_rgba(p['color']))
            x += w
        y += hgt
    # Barra final con el formato y el enlace a la especificación.
    cv.fill(0, y * CH, W, CH, INK)
    cv.text(1, y, norm(f'{FORMAT} {VERSION}'), PAPER)
    link = norm(URL)
    cv.text(wide - 1 - len(link), y, link, PAPER)
    return img

# ---------------------------------------------------------------- leer el dibujo
def decode_grid(img, k=1):
    """La rejilla de caracteres de la imagen: (texto, invertido) por celda;
    None donde no hay un carácter."""
    px = img.convert('RGBA').load()
    W, H = img.width // k, img.height // k
    grid = []
    for row in range(H // CH):
        line = []
        for col in range(W // CW):
            bits, ok = [], True
            for r in range(6):
                for c in range(3):
                    p = px[(col * CW + c) * k, (row * CH + r) * k]
                    if p == INK: bits.append('1')
                    elif p == PAPER: bits.append('0')
                    else: ok = False; break
                if not ok: break
            if not ok:
                line.append(None); continue
            key = ''.join(bits)
            inv = ''.join('1' if b == '0' else '0' for b in bits)
            gap = all(px[(col * CW + 3) * k, (row * CH + r) * k] == INK for r in range(CH)) and \
                all(px[(col * CW + c) * k, (row * CH + 6) * k] == INK for c in range(3))
            if gap and inv in LOOKUP:
                line.append((LOOKUP[inv], True))
            elif key in LOOKUP:
                line.append((LOOKUP[key], False))
            else:
                line.append(None)
        grid.append(line)
    return grid

def find_scale(img):
    for k in range(1, 13):
        if img.width % (CW * k) or img.height % (CH * k):
            continue
        last = decode_grid(img.crop((0, img.height - CH * k, img.width, img.height)), k)[0]
        s = ''.join(c[0] if c and c[1] else ' ' for c in last)
        if s.strip().startswith(norm(FORMAT) + ' '):
            return k, s
    raise SystemExit('No es un sprite pattern: falta la barra final «SPRITEVPG …».')

def decode_zones(img, k):
    grid = decode_grid(img, k)
    bars = []                                     # (fila, col inicial, col final, título)
    names = re.compile(r' (' + '|'.join(ZONES) + r')(?= |$)')
    for r, line in enumerate(grid[:-1]):
        c = 0
        while c < len(line):
            if line[c] and line[c][1]:
                e = c
                while e + 1 < len(line) and line[e + 1] and line[e + 1][1]:
                    e += 1
                run = ''.join(x[0] for x in line[c:e + 1])
                starts = [(m.start(), m.group(1)) for m in names.finditer(run)]
                for n, (st, title) in enumerate(starts):   # dos zonas seguidas comparten barra
                    stop = starts[n + 1][0] - 1 if n + 1 < len(starts) else len(run) - 1
                    bars.append((r, c + st, c + stop, title))
                c = e + 1
            else:
                c += 1
    zones = {}
    for r, c0, c1, title in bars:
        end = min([b[0] for b in bars if b[0] > r and not (b[2] < c0 or b[1] > c1)] + [len(grid) - 1])
        logical = []
        for rr in range(r + 1, end):
            s = ''.join((x[0] if x and not x[1] else ' ') for x in grid[rr][c0 + 1:c1 + 1]).rstrip()
            if not s.strip():
                continue
            if s.startswith(' ') and logical:
                logical[-1] += ' ' + s.strip()
            else:
                logical.append(s.strip())
        zones[title] = logical
    return zones

def read_card(path):
    """La ficha de un patrón, leída del dibujo. Si el PNG trae la copia iTXt y
    dice lo mismo, se usa esa (conserva minúsculas del texto libre)."""
    img = Image.open(path)
    k, _ = find_scale(img)
    card = parse_notation(decode_zones(img, k))
    g = card['grid']
    card['image'] = {'w': img.width // k, 'h': img.height // k, 'pixelArt': True,
                     'framesArea': {'x': 0, 'y': 0, 'w': g['columns'] * g['frameSize']['w'],
                                    'h': g['rows'] * g['frameSize']['h']}}
    txt = (getattr(img, 'text', {}) or {}).get(FORMAT)
    src = 'dibujo'
    if txt:
        try:
            full = json.loads(txt)
            a, b = normalized(full), dict(card)
            a.pop('image', None); b.pop('image', None)
            if a == b:
                card, src = full, 'dibujo + iTXt'
        except (ValueError, KeyError):
            pass
    return card, src, k

# ---------------------------------------------------------------- make/read -
def complete(card, sheet):
    """Rellena lo que se calcula: formato, frames con dibujo, paleta."""
    g = card['grid']
    cols, rows = g['columns'], g['rows']
    fw, fh = g['frameSize']['w'], g['frameSize']['h']
    card = {'format': FORMAT, 'version': VERSION, '$schema': SCHEMA,
            **{k: v for k, v in card.items() if k not in ('format', 'version', '$schema', 'lang')}}
    card['grid'] = {'columns': cols, 'rows': rows, 'frameSize': {'w': fw, 'h': fh}, 'margin': 0, 'spacing': 0}
    if not card.get('frames'):
        fr = []
        for i in range(cols * rows):
            x, y = (i % cols) * fw, (i // cols) * fh
            if sheet.crop((x, y, x + fw, y + fh)).getbbox():
                fr.append({'i': i, 'x': x, 'y': y, 'w': fw, 'h': fh})
        card['frames'] = fr
    if not card['art'].get('palette'):
        card['art']['palette'] = [{'color': c} for c in auto_palette(sheet)]
    return card

def make(sheet_path, card_path, out, preview=0):
    sheet = Image.open(sheet_path).convert('RGBA')
    card = complete(json.load(open(card_path, encoding='utf-8')), sheet)
    g = card['grid']
    img = render(sheet, card)
    card['image'] = {'file': os.path.basename(out), 'w': img.width, 'h': img.height, 'pixelArt': True,
                     'framesArea': {'x': 0, 'y': 0, 'w': g['columns'] * g['frameSize']['w'],
                                    'h': g['rows'] * g['frameSize']['h']}}
    info = PngImagePlugin.PngInfo()
    info.add_itxt(FORMAT, json.dumps(card, ensure_ascii=False, separators=(',', ':')), zip=True)
    img.save(out, pnginfo=info)
    if preview:
        # La copia ampliada es también un sprite pattern válido: conserva la
        # transparencia y la ficha.
        img.resize((img.width * preview, img.height * preview), Image.NEAREST).save(
            out.replace('.png', f'@{preview}x.png'), pnginfo=info)
    return card, img

def read(path, outdir, gifs=False):
    card, src, k = read_card(path)
    img = Image.open(path).convert('RGBA')
    if k > 1:
        img = img.resize((img.width // k, img.height // k), Image.NEAREST)
    os.makedirs(outdir, exist_ok=True)
    fa = card['image']['framesArea']
    sheet = img.crop((0, 0, fa['w'], fa['h']))
    base = card['entity']['name']
    sheet.save(os.path.join(outdir, f'{base}.sheet.png'))
    json.dump(card, open(os.path.join(outdir, f'{base}.spritevpg.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    fdir = os.path.join(outdir, 'frames')
    os.makedirs(fdir, exist_ok=True)
    for f in card['frames']:
        sheet.crop((f['x'], f['y'], f['x'] + f['w'], f['y'] + f['h'])).save(os.path.join(fdir, f'{f["i"]:03d}.png'))
    if gifs:
        for a in card.get('animations', []):
            fr = [sheet.crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h']))
                  for r in (frame_rect(card, f['frame']) for f in a['frames'])]
            big = [f.resize((f.width * 4, f.height * 4), Image.NEAREST) for f in fr]
            name = a['name'].replace(':', '_') + (f'_{a["direction"]}' if a.get('direction') else '')
            big[0].save(os.path.join(outdir, f'{name}.gif'), save_all=True, append_images=big[1:],
                        duration=[f['ms'] for f in a['frames']],
                        loop=0 if a.get('loop', 'loop') != 'once' else 1, disposal=2)
    return card, src, k

# ---------------------------------------------------------------- validar ---
def validate(card):
    err, warn = [], []
    def need(cond, msg):
        if not cond:
            err.append(msg)
    need(card.get('format') == FORMAT, 'format debe ser "spritevpg"')
    need(str(card.get('version', '')).split('.')[0] == '1', 'version 1.x')
    for k in ('entity', 'art', 'grid', 'frames', 'defaults', 'ai', 'provenance'):
        need(k in card, f'falta {k}')
    if err:
        return err, warn
    e = card['entity']
    need(e.get('kind') in KINDS or str(e.get('kind', '')).startswith('custom:'), 'entity.kind no válido')
    need(bool(re.fullmatch(r'[a-z0-9_\-]+', e.get('name', ''))), 'entity.name: solo a-z, 0-9, _ y -')
    v = card['art'].get('view')
    need(v in VIEWS, f'art.view no válido: {v}')
    g = card['grid']
    fw, fh = g['frameSize']['w'], g['frameSize']['h']
    AW, AH = g['columns'] * fw, g['rows'] * fh
    if 'image' in card:
        fa = card['image'].get('framesArea', {})
        need(fa.get('x') == 0 and fa.get('y') == 0, 'framesArea debe empezar en 0,0')
        need(fa.get('w') == AW and fa.get('h') == AH, 'framesArea no coincide con la rejilla')
    ids = set()
    for f in card['frames']:
        ids.add(f['i'])
        need(f['x'] + f['w'] <= AW and f['y'] + f['h'] <= AH, f'frame {f["i"]} fuera de la zona de frames')
        need((f['x'], f['y']) == ((f['i'] % g['columns']) * fw, (f['i'] // g['columns']) * fh),
             f'frame {f["i"]}: no está en su celda')
    need('pivot' in card['defaults'], 'falta defaults.pivot')
    names = set()
    anims = card.get('animations', [])
    for a in anims:
        key = (a['name'], a.get('direction'))
        need(key not in names, f'animación repetida: {key}')
        names.add(key)
        need(a.get('loop', 'loop') in LOOPS, f'{a["name"]}: loop no válido')
        need(a.get('direction') is None or a['direction'] in DIRS, f'{a["name"]}: dirección no válida')
        for f in a['frames']:
            need(f['frame'] in ids, f'{a["name"]}: el frame {f["frame"]} no existe')
            need(isinstance(f.get('ms'), int) and f['ms'] > 0, f'{a["name"]}: ms no válido en F{f["frame"]}')
        if a.get('next'):
            need(any(b['name'] == a['next'] for b in anims), f'{a["name"]}: next desconocido')
        if a.get('loop') == 'once' and not a.get('next'):
            warn.append(f'{a["name"]}: una vez y sin next')
    for dst, m in card.get('directions', {}).get('mirror', {}).items():
        need(m.get('from') in card['directions'].get('set', []), f'mirror {dst}: from desconocido')
    for s in card.get('states', []):
        need(('frame' in s) != ('animation' in s), f'estado {s["name"]}: frame o animation, no los dos')
        if 'frame' in s:
            need(s['frame'] in ids, f'estado {s["name"]}: el frame no existe')
    ref = card.get('style', {}).get('reference', {}).get('frame')
    need(ref is None or ref in ids, 'style.reference.frame no existe')
    for c in card['art'].get('palette', []):
        need(bool(re.fullmatch(r'#[0-9a-fA-F]{6}', c.get('color', ''))), f'color no válido: {c.get("color")}')
    if not card['ai'].get('summary'):
        warn.append('falta ai.summary')
    if 'style' not in card:
        warn.append('sin style: una IA no tendrá guía para ampliarla')
    return err, warn

# ---------------------------------------------------------------- resumen ---
def summary(card):
    e, g = card['entity'], card['grid']
    out = [f'{e.get("displayName", e["name"])} ({e["kind"]}) · {FORMAT} {card.get("version")}',
           f'Frames de {g["frameSize"]["w"]}x{g["frameSize"]["h"]} en {g["columns"]}x{g["rows"]}, '
           f'desde 0,0; frame i en x=(i % {g["columns"]})*{g["frameSize"]["w"]}, '
           f'y=(i // {g["columns"]})*{g["frameSize"]["h"]}.',
           f'Vista: {card["art"].get("view")}; mira a: {card["art"].get("facing")}.']
    piv = card.get('defaults', {}).get('pivot')
    if piv:
        out.append(f'Apoyo: {piv["x"]},{piv["y"]} dentro de cada frame.')
    for a in card.get('animations', []):
        fs = ', '.join(f'{f["frame"]}({f["ms"]}ms' + (' ' + '+'.join(f['events']) if f.get('events') else '') + ')'
                       for f in a['frames'])
        out.append(f'- {a["name"]}' + (f' [{a["direction"]}]' if a.get('direction') else '')
                   + f' {a.get("loop", "loop")}' + (f' -> {a["next"]}' if a.get('next') else '') + f': {fs}')
    for dst, m in card.get('directions', {}).get('mirror', {}).items():
        out.append(f'{dst} = {m["from"]} volteado ({m.get("flip", "x")}).')
    for s in card.get('states', []):
        out.append(f'Estado {s["name"]}: ' + (f'frame {s["frame"]}' if 'frame' in s else f'animación {s["animation"]}'))
    if card.get('ai', {}).get('summary'):
        out.append('IA: ' + card['ai']['summary'])
    return '\n'.join(out)

# ---------------------------------------------------------------- CLI -------
def main(argv=None):
    p = argparse.ArgumentParser(description='SpriteVPG: sprite patterns.')
    sub = p.add_subparsers(dest='cmd', required=True)
    m = sub.add_parser('make', help='hoja limpia + ficha -> sprite pattern')
    m.add_argument('sheet'); m.add_argument('card')
    m.add_argument('-o', '--out', required=True)
    m.add_argument('--preview', type=int, default=0, help='guarda también una copia ampliada xN')
    r = sub.add_parser('read', help='sprite pattern -> ficha, hoja limpia y frames')
    r.add_argument('pattern'); r.add_argument('-o', '--out', required=True)
    r.add_argument('--gifs', action='store_true', help='un GIF por animación')
    for name, hlp in (('text', 'la notación de los márgenes'), ('info', 'resumen legible'),
                      ('validate', 'comprueba la ficha')):
        s = sub.add_parser(name, help=hlp)
        s.add_argument('path')
    a = p.parse_args(argv)

    def load(path):
        if not path.lower().endswith('.json'):
            return read_card(path)[0]
        card = json.load(open(path, encoding='utf-8'))
        if 'frames' not in card:                   # ficha de entrada, sin calcular
            g = card['grid']
            fw, fh = g['frameSize']['w'], g['frameSize']['h']
            card['frames'] = [{'i': i, 'x': (i % g['columns']) * fw, 'y': (i // g['columns']) * fh,
                               'w': fw, 'h': fh} for i in range(g['columns'] * g['rows'])]
        return {'format': FORMAT, 'version': VERSION, **card}

    if a.cmd == 'make':
        card, img = make(a.sheet, a.card, a.out, a.preview)
        err, warn = validate(card)
        print(f'{a.out}: {img.width}x{img.height}')
        for w in warn: print('aviso:', w)
        for e in err: print('error:', e)
        return 1 if err else 0
    if a.cmd == 'read':
        card, src, k = read(a.pattern, a.out, a.gifs)
        print(f'Ficha leída del {src} (escala x{k}). {len(card["frames"])} frames en {a.out}/')
        return 0
    if a.cmd == 'text':
        print(notation_text(load(a.path)))
        return 0
    if a.cmd == 'info':
        print(summary(load(a.path)))
        return 0
    if a.cmd == 'validate':
        err, warn = validate(load(a.path))
        for w in warn: print('aviso:', w)
        for e in err: print('error:', e)
        print('válida' if not err else f'{len(err)} errores')
        return 1 if err else 0

if __name__ == '__main__':
    sys.exit(main())
