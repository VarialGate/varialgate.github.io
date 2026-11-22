#!/usr/bin/env python3
"""SpriteVPG: genera, lee y comprueba sprite patterns.

Un sprite pattern es una hoja de sprites PNG con los frames limpios desde la
esquina de arriba a la izquierda y una animación por fila. A la derecha de
cada fila va su rótulo (nombre, FRAMES, MS/FRAME y PLAY) y debajo, dos zonas
con título: SHEET (nombre, tamaño de frame y rejilla) y SUBJECT (tipo, vista,
hacia dónde mira y una descripción breve); opcionalmente, AGENTS (lo que debe
respetar quien amplíe la hoja con IA); y una barra final con el enlace
a la especificación: https://varialgate.github.io/specs/spritevpg/

Uso:
  spritevpg.py make  HOJA.png DATOS.json -o PATRON.png [--preview 4]
  spritevpg.py read  PATRON.png -o CARPETA [--gifs]
  spritevpg.py info  PATRON.png
  spritevpg.py validate PATRON.png

Solo necesita Pillow. La ficha se lee del propio dibujo (cada carácter cae en
una celda fija y se reconoce comparando píxeles): funciona con PNG sin
metadatos y con copias ampliadas a escala entera.
"""
import argparse, json, os, re, sys, unicodedata

from PIL import Image

FORMAT, VERSION = 'spritevpg', '1.0'
URL = 'https://varialgate.github.io/specs/spritevpg/'

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
 'U': '1001 1001 1001 1001 1001 0110', 'V': '1001 1001 1001 1001 0110 0110',
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

LOOPS = ('loop', 'once')
KINDS = ('character', 'creature', 'item', 'prop', 'building', 'effect', 'tile', 'ui')
VIEWS = ('side', 'front', 'three-quarter', 'near-top-down', 'top-down', 'isometric')
DIRS = ('down', 'up', 'left', 'right', 'down-left', 'down-right', 'up-left', 'up-right')

# ---------------------------------------------------------------- ficha -----
# {"format": "spritevpg", "version": "1.0", "name": "Caballero azul",
#  "kind": "character", "view": "side", "facing": "right",        (opcionales)
#  "description": "Caballero con armadura azul…",                 (opcional)
#  "agents": ["Contorno oscuro de 1 px…", "…"],                   (opcional)
#  "frame": {"w": 32, "h": 32}, "grid": {"columns": 6, "rows": 3},
#  "rows": [{"name": "idle", "frames": 2, "ms": [400, 400], "loop": "loop"}, ...]}
# Una fila sin "ms" son imágenes sueltas (no es una animación).

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
def draw_text(px, col, row, s, fg):
    for i, ch in enumerate(s):
        if ch == ' ':
            continue
        for r, bits in enumerate(cell_rows(ch)):
            for c, b in enumerate(bits):
                if b == '1':
                    px[(col + i) * CW + c, row * CH + r] = fg

def frames_in_row(sheet, r, cols, fw, fh):
    """Cuántos frames con dibujo tiene la fila (seguidos, desde la izquierda)."""
    n = 0
    for c in range(cols):
        if sheet.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)).getbbox():
            if n != c:
                raise SystemExit(f'Fila {r}: hay un hueco antes del frame de la columna {c}.')
            n += 1
    return n

ZONES = ('SHEET', 'SUBJECT', 'AGENTS')

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

def sheet_lines(card, width):
    f, g = card['frame'], card['grid']
    return keyed([('NAME', card['name']), ('FRAME', f'{f["w"]}X{f["h"]} PX'),
                  ('GRID', f'{g["columns"]} COLUMNS X {g["rows"]} ROWS'),
                  ('ORIGIN', 'TOP-LEFT 0,0, NO GAPS')], width)

def subject_lines(card, width):
    pairs = [(key.upper() if key != 'description' else 'DESC', card[key])
             for key in ('kind', 'view', 'facing', 'description') if card.get(key)]
    return keyed(pairs, width) if pairs else []

def agents_lines(card, width):
    """Instrucciones del autor para quien amplíe la hoja con IA: una por
    línea, con guion; lo que no cabe sigue debajo, sangrado."""
    out = []
    for note in card.get('agents', []):
        cur = '-'
        for word in norm(note).split(' '):
            if len(cur) + 1 + len(word) > width:
                out.append(cur)
                cur = '  ' + word
            else:
                cur += ' ' + word
        out.append(cur)
    return out

def row_chunks(row):
    """Lo que se escribe junto a una fila: el nombre y sus datos, `CLAVE: valor`."""
    ms = row.get('ms')
    out = [norm(row['name']), f'FRAMES: {row["frames"]}']
    if ms:
        out.append('MS/FRAME: ' + (str(ms[0]) if len(set(ms)) == 1 else ' '.join(map(str, ms))))
    out.append('PLAY: ' + (norm(row['loop']) if ms else 'STILL'))
    return out

def row_label(row, lines, width):
    """El rótulo de una fila en `lines` líneas como mucho: un dato por línea si
    caben; si no, seguidos y separados por «·». Las líneas de continuación van
    sangradas dos celdas."""
    chunks = row_chunks(row)
    if lines >= len(chunks):
        return [chunks[0]] + ['  ' + c for c in chunks[1:]]
    out, cur = [], chunks[0]
    for c in chunks[1:]:
        if len(cur) + 3 + len(c) <= width:
            cur += ' · ' + c
        else:
            out.append(cur)
            cur = '  ' + c
    return out + [cur]

def render(sheet, card):
    fw, fh = card['frame']['w'], card['frame']['h']
    cols, nrows = card['grid']['columns'], card['grid']['rows']
    AW, AH = cols * fw, nrows * fh
    sheet = sheet.convert('RGBA').crop((0, 0, AW, AH))
    spec, link = norm(f'{FORMAT} {VERSION}'), norm(URL)   # las dos filas de la barra final
    lab_col = -(-(AW + 6) // CW)                  # rótulos, a la derecha de los frames
    room = max(26, len(link) + 2 - lab_col - 1)
    labels = [row_label(r, fh // CH, room) for r in card['rows']]
    wide = max(len(link) + 2, lab_col + max(len(t) for ls in labels for t in ls) + 1)
    # Cada rótulo va a la altura de su fila si cabe; si no, debajo del anterior.
    pos, nxt = [], 0
    for r, ls in enumerate(labels):
        ideal = -(-(r * fh + max(0, (fh - len(ls) * CH) // 2)) // CH)
        pos.append(max(nxt, ideal))
        nxt = pos[-1] + len(ls)
    has_subject = bool(subject_lines(card, 99))
    half = (wide - 1) // 2 if has_subject else wide
    left = sheet_lines(card, half - 2)
    right = subject_lines(card, wide - half - 3) if has_subject else []
    notes = agents_lines(card, wide - 2)
    top = max(-(-(AH + 4) // CH), nxt + 1)        # barras de título
    ag = top + 1 + max(len(left), len(right)) + 1
    bar = ag + (1 + len(notes) + 1 if notes else 0)
    W, H = wide * CW, (bar + 2) * CH
    img = Image.new('RGBA', (W, H), PAPER)
    px = img.load()
    for y in range(AH):
        for x in range(AW):
            px[x, y] = (0, 0, 0, 0)
    img.alpha_composite(sheet, (0, 0))
    px = img.load()
    for y in range(AH + 1):                       # borde de la zona, por fuera
        px[AW, y] = INK
    for x in range(AW + 1):
        px[x, AH] = INK
    for r in range(1, nrows):                     # marca de celda y regla entre rótulos
        for x in range(AW + 1, AW + 4):
            px[x, r * fh] = INK
        gy = pos[r] * CH - 1                      # por la fila libre de las celdas de texto
        for x in range(lab_col * CW, W):
            px[x, gy] = RULE
    for c in range(1, cols):
        for y in range(AH + 1, AH + 4):
            px[c * fw, y] = INK
    for ls, ty in zip(labels, pos):
        for j, t in enumerate(ls):
            draw_text(px, lab_col, ty + j, t, INK)

    def zone(title, c0, c1, row, lines):
        for y in range(row * CH, (row + 1) * CH):  # barra de título, en negativo
            for x in range(c0 * CW, c1 * CW):
                px[x, y] = INK
        draw_text(px, c0 + 1, row, title, PAPER)
        for j, t in enumerate(lines):
            draw_text(px, c0 + 1, row + 1 + j, t, INK)

    zone('SHEET', 0, half, top, left)
    if has_subject:
        zone('SUBJECT', half + 1, wide, top, right)
    if notes:
        zone('AGENTS', 0, wide, ag, notes)
    zone(spec, 0, wide, bar, [])                  # barra final: formato y versión…
    zone(link, 0, wide, bar + 1, [])              # …y, debajo, el enlace
    return img

# ---------------------------------------------------------------- leer ------
def decode_grid(img, k=1):
    """La rejilla de caracteres: (carácter, en negativo) por celda; None donde
    no hay un carácter."""
    px = img.convert('RGBA').load()
    grid = []
    for row in range(img.height // k // CH):
        line = []
        for col in range(img.width // k // CW):
            bits = []
            for r in range(GH):
                for c in range(GW):
                    p = px[(col * CW + c) * k, (row * CH + r) * k]
                    bits.append('1' if p == INK else '0' if p == PAPER else 'x')
            key = ''.join(bits)
            inv = key.translate(str.maketrans('01', '10'))
            full = all(px[(col * CW + GW) * k, (row * CH + r) * k] == INK for r in range(CH)) and \
                all(px[(col * CW + c) * k, (row * CH + GH) * k] == INK for c in range(GW))
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
    # Barras de título: tramos en negativo cuyo texto es el nombre de una zona.
    bars = []
    for r, line in enumerate(grid[:-2]):
        c = 0
        while c < len(line):
            if line[c] and line[c][1]:
                e = c
                while e + 1 < len(line) and line[e + 1] and line[e + 1][1]:
                    e += 1
                title = ''.join(x[0] for x in line[c:e + 1]).strip()
                if title in ZONES:
                    bars.append((r, c, e, title))
                c = e + 1
            else:
                c += 1
    zones = {}
    for r, c0, c1, title in bars:
        end = min([b[0] for b in bars if b[0] > r and not (b[2] < c0 or b[1] > c1)] + [len(grid) - 2])
        lines = []
        for rr in range(r + 1, end):
            t = row_text(grid[rr][c0 + 1:c1 + 1])
            if not t.strip():
                continue
            if t.startswith(' ') and lines:       # continúa la línea de arriba
                lines[-1] += ' ' + t.strip()
            else:
                lines.append(t.strip())
        zones[title] = lines
    if 'SHEET' not in zones:
        raise SystemExit('Falta la zona SHEET.')
    def pairs(name):
        return {t.partition(':')[0].strip(): t.partition(':')[2].strip() for t in zones.get(name, [])}
    sh, su = pairs('SHEET'), pairs('SUBJECT')
    fw, fh = (int(x) for x in sh['FRAME'].split()[0].split('X'))
    g = sh['GRID'].split()
    cols, nrows = int(g[0]), int(g[3])
    card = {'format': FORMAT, 'version': row_text(grid[-2], True).split()[1], 'name': sh['NAME']}
    for key in ('KIND', 'VIEW', 'FACING'):
        if key in su:
            card[key.lower()] = su[key].lower()
    if 'DESC' in su:
        card['description'] = su['DESC']
    if zones.get('AGENTS'):
        card['agents'] = [t.lstrip('- ').strip() for t in zones['AGENTS']]
    card.update({'frame': {'w': fw, 'h': fh}, 'grid': {'columns': cols, 'rows': nrows}, 'rows': []})
    # Rótulos de fila: a la derecha de los frames, por encima de las barras.
    lab_col = -(-(cols * fw + 6) // CW)
    logical = []
    for line in grid[:min(b[0] for b in bars)]:
        t = row_text(line[lab_col:])
        if not t.strip():
            continue
        if t.startswith(' ') and logical:
            logical[-1] += ' ' + t.strip()
        else:
            logical.append(t.strip())
    if len(logical) != nrows:
        raise SystemExit(f'Hay {len(logical)} rótulos para {nrows} filas.')
    for t in logical:
        def value(key):
            m = re.search(key + r': ([^:·]*?)(?= ·| [A-Z/]+:|$)', t)
            return m.group(1).strip() if m else None
        row = {'name': t.split()[0].lower(), 'frames': int(value('FRAMES'))}
        if value('PLAY') != 'STILL':
            ms = [int(x) for x in value('MS/FRAME').split()]
            row['ms'] = ms * row['frames'] if len(ms) == 1 else ms
            row['loop'] = value('PLAY').lower()
        card['rows'].append(row)
    return card, k

# ---------------------------------------------------------------- make/read -
def complete(card, sheet):
    fw, fh = card['frame']['w'], card['frame']['h']
    cols, nrows = sheet.width // fw, len(card['rows'])
    out = {'format': FORMAT, 'version': VERSION, 'name': card['name'],
           **{k: card[k] for k in ('kind', 'view', 'facing', 'description', 'agents') if card.get(k)},
           'frame': {'w': fw, 'h': fh}, 'grid': {'columns': cols, 'rows': nrows}, 'rows': []}
    for r, row in enumerate(card['rows']):
        n = frames_in_row(sheet, r, cols, fw, fh)
        new = {'name': row['name'].lower(), 'frames': n}
        if row.get('ms'):
            ms = row['ms'] if isinstance(row['ms'], list) else [row['ms']]
            new['ms'] = ms * n if len(ms) == 1 else ms
            new['loop'] = row.get('loop', 'loop')
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
        for c, f in enumerate(fr):
            f.save(os.path.join(d, f'{c}.png'))
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
    for key, known in (('kind', KINDS), ('view', VIEWS), ('facing', DIRS)):
        if card.get(key) and card[key] not in known:
            err.append(f'{key} no válido: {card[key]} (valen: {", ".join(known)})')
    rows = card.get('rows', [])
    if card.get('grid', {}).get('rows') != len(rows):
        err.append('grid.rows no coincide con el número de filas')
    names = set()
    for r, row in enumerate(rows):
        n = row.get('name', '')
        if not re.fullmatch(r'[a-z0-9_\-]+', n):
            err.append(f'fila {r}: name solo admite a-z, 0-9, _ y -')
        if n in names:
            err.append(f'fila {r}: nombre repetido ({n})')
        names.add(n)
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
    out = [f'{card["name"]} · {FORMAT} {card.get("version")}'] + ([what] if what else []) + \
        ([card['description']] if card.get('description') else []) + [
        f'Frames de {fw}x{fh} en {card["grid"]["columns"]}x{card["grid"]["rows"]}, desde 0,0. '
        f'El frame de la fila r y la columna c está en x = c*{fw}, y = r*{fh}.']
    for r, row in enumerate(card['rows']):
        if row.get('ms'):
            ms = f'{row["ms"][0]} ms cada uno' if len(set(row['ms'])) == 1 else ', '.join(map(str, row['ms'])) + ' ms'
            mode = 'en bucle' if row['loop'] == 'loop' else 'una vez'
            out.append(f'- fila {r}: {row["name"]}, {row["frames"]} frames, {ms}, {mode}')
        else:
            out.append(f'- fila {r}: {row["name"]}, {row["frames"]} imágenes sueltas')
    for note in card.get('agents', []):
        out.append('Para ampliarla: ' + note)
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
