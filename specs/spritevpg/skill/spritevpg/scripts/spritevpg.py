#!/usr/bin/env python3
"""SpriteVPG: genera, lee y comprueba sprite patterns.

Un sprite pattern es una hoja de sprites PNG con los frames limpios desde la
esquina de arriba a la izquierda, una animación por fila, y lo imprescindible
escrito en los márgenes: a la derecha de cada fila, su nombre y su ritmo; y
abajo, el nombre de la hoja, el tamaño de frame y la rejilla, qué es (tipo,
vista, hacia dónde mira y una descripción breve) y el enlace a la
especificación: https://varialgate.github.io/specs/spritevpg/

Uso:
  spritevpg.py make  HOJA.png FICHA.json -o PATRON.png [--preview 4]
  spritevpg.py read  PATRON.png -o CARPETA [--gifs]
  spritevpg.py info  PATRON.png|FICHA.json
  spritevpg.py validate PATRON.png|FICHA.json

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
VIEWS = ('side', 'front', 'three-quarter', 'oblique', 'top-down', 'isometric')
DIRS = ('down', 'up', 'left', 'right', 'down-left', 'down-right', 'up-left', 'up-right')

# ---------------------------------------------------------------- ficha -----
# {"format": "spritevpg", "version": "1.0", "name": "Caballero azul",
#  "kind": "character", "view": "side", "facing": "right",        (opcionales)
#  "description": "Caballero con armadura azul…",                 (opcional)
#  "frame": {"w": 32, "h": 32}, "grid": {"columns": 6, "rows": 3},
#  "rows": [{"name": "idle", "frames": 2, "ms": [400, 400], "loop": "loop"}, ...]}
# Una fila sin "ms" son imágenes sueltas (no es una animación).

def label(row):
    """El rótulo de una fila: NOMBRE [ms… MS LOOP|ONCE]."""
    out = [norm(row['name'])]
    ms = row.get('ms')
    if ms:
        out += [str(ms[0])] if len(set(ms)) == 1 else [str(m) for m in ms]
        out += ['MS', norm(row.get('loop', 'loop'))]
    return out

def parse_label(text, frames):
    t = text.split()
    row = {'name': t[0].lower(), 'frames': frames}
    if 'MS' in t:
        k = t.index('MS')
        ms = [int(x) for x in t[1:k]]
        row['ms'] = ms * frames if len(ms) == 1 else ms
        row['loop'] = t[k + 1].lower() if len(t) > k + 1 else 'loop'
    return row

def title_line(card):
    return (f'{norm(card["name"])} · FRAME {card["frame"]["w"]}X{card["frame"]["h"]}'
            f' · GRID {card["grid"]["columns"]}X{card["grid"]["rows"]}')

def what_line(card):
    """Qué es, en esquema: KIND tipo · VIEW vista · FACING dirección."""
    parts = [f'{key.upper()} {norm(card[key])}' for key in ('kind', 'view', 'facing') if card.get(key)]
    return ' · '.join(parts)

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

def render(sheet, card):
    fw, fh = card['frame']['w'], card['frame']['h']
    cols, nrows = card['grid']['columns'], card['grid']['rows']
    AW, AH = cols * fw, nrows * fh
    sheet = sheet.convert('RGBA').crop((0, 0, AW, AH))
    lab_col = -(-(AW + 6) // CW)
    title = title_line(card)
    link = norm(f'{FORMAT} {VERSION} · {URL}')
    # Rótulos: cortos junto a su fila; el ancho de la hoja lo marca el pie.
    lab_w = max(24, max(len(title), len(link)) + 2 - lab_col)
    labels = [wrap(label(r), lab_w - 1) for r in card['rows']]
    what = what_line(card)
    wide = max(lab_col + max(len(t) for ls in labels for t in ls) + 1,
               len(title) + 2, len(link) + 2, len(what) + 2)
    foot_lines = [title] + ([what] if what else [])
    if card.get('description'):
        foot_lines += wrap(['DESC'] + norm(card['description']).split(' '), wide - 2)
    # Cada rótulo va a la altura de su fila si cabe; si no, debajo del anterior.
    pos, nxt = [], 0
    for r, ls in enumerate(labels):
        ideal = -(-(r * fh + max(1, (fh - len(ls) * CH) // 2)) // CH)
        pos.append(max(nxt, ideal))
        nxt = pos[-1] + len(ls)
    foot = max(-(-(AH + 5) // CH), nxt + 1)
    W, H = wide * CW, (foot + len(foot_lines) + 1) * CH
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
    for r in range(1, nrows):                     # marcas de celda y regla entre filas
        for x in range(AW + 1, W):
            px[x, r * fh] = INK if x <= AW + 3 else RULE
    for c in range(1, cols):
        for y in range(AH + 1, AH + 4):
            px[c * fw, y] = INK
    for ls, ty in zip(labels, pos):
        for j, t in enumerate(ls):
            draw_text(px, lab_col, ty + j, t, INK)
    for j, t in enumerate(foot_lines):
        draw_text(px, 1, foot + j, t, INK)
    bar = foot + len(foot_lines)
    for y in range(bar * CH, H):                  # barra final, en negativo
        for x in range(W):
            px[x, y] = INK
    draw_text(px, 1, bar, link, PAPER)
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
        last = decode_grid(img.crop((0, img.height - CH * k, img.width, img.height)), k)[0]
        if row_text(last, True).strip().startswith(norm(FORMAT) + ' '):
            break
    else:
        raise SystemExit('No es un sprite pattern: falta la barra final «SPRITEVPG …».')
    grid = decode_grid(img, k)
    pat = re.compile(r'(.*) · FRAME (\d+)X(\d+) · GRID (\d+)X(\d+)')
    top = next((i for i in range(len(grid) - 2, -1, -1)
                if pat.fullmatch(row_text(grid[i])[1:].strip()) and row_text(grid[i])[:1] == ' '), None)
    if top is None:
        raise SystemExit('No se encuentra la línea del nombre, FRAME y GRID.')
    m = pat.fullmatch(row_text(grid[top])[1:].strip())
    fw, fh, cols, nrows = (int(x) for x in m.groups()[1:])
    version = row_text(grid[-1], True).split()[1]
    card = {'format': FORMAT, 'version': version, 'name': m.group(1)}
    extra = []                                    # líneas del pie bajo el nombre
    for line in grid[top + 1:-1]:
        t = row_text(line)[1:]
        if not t.strip():
            continue
        if t.startswith(' ') and extra:
            extra[-1] += ' ' + t.strip()
        else:
            extra.append(t.strip())
    for t in extra:
        if t.startswith('DESC '):
            card['description'] = t[5:]
        else:
            for part in t.split(' · '):
                key, _, val = part.partition(' ')
                if key in ('KIND', 'VIEW', 'FACING'):
                    card[key.lower()] = val.lower()
    card.update({'frame': {'w': fw, 'h': fh}, 'grid': {'columns': cols, 'rows': nrows}, 'rows': []})
    native = img.convert('RGBA')
    if k > 1:
        native = native.resize((img.width // k, img.height // k), Image.NEAREST)
    lab_col = -(-(cols * fw + 6) // CW)
    logical = []
    for line in grid[:top]:
        s = row_text(line[lab_col:])
        if not s.strip():
            continue
        if s.startswith(' ') and logical:
            logical[-1] += ' ' + s.strip()
        else:
            logical.append(s.strip())
    if len(logical) != nrows:
        raise SystemExit(f'Hay {len(logical)} rótulos para {nrows} filas.')
    for r, text in enumerate(logical):
        card['rows'].append(parse_label(text, frames_in_row(native, r, cols, fw, fh)))
    return card, k

# ---------------------------------------------------------------- make/read -
def complete(card, sheet):
    fw, fh = card['frame']['w'], card['frame']['h']
    cols, nrows = sheet.width // fw, len(card['rows'])
    out = {'format': FORMAT, 'version': VERSION, 'name': card['name'],
           **{k: card[k] for k in ('kind', 'view', 'facing', 'description') if card.get(k)},
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
    json.dump(card, open(os.path.join(outdir, f'{base}.spritevpg.json'), 'w', encoding='utf-8'),
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
    return '\n'.join(out)

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
    for name, hlp in (('info', 'resumen legible'), ('validate', 'comprueba la ficha')):
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
        print(f'Ficha leída del dibujo (escala x{k}). {sum(r["frames"] for r in card["rows"])} frames en {a.out}/')
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
