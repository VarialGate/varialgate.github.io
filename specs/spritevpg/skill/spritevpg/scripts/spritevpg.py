#!/usr/bin/env python3
"""SpriteVPG: genera, lee y comprueba sprite patterns.

Un sprite pattern es una hoja de sprites PNG con los frames limpios desde la
esquina de arriba a la izquierda y la información (rótulos, detalle, ficha en
un QR) a la derecha y abajo. Especificación:
https://varialgate.github.io/specs/spritevpg/

Uso:
  spritevpg.py make  HOJA.png FICHA.json -o PATRON.png [--preview 4]
  spritevpg.py read  PATRON.png -o CARPETA [--gifs]
  spritevpg.py info  PATRON.png|FICHA.json
  spritevpg.py validate PATRON.png|FICHA.json

Necesita Pillow y qrcode (make). Para leer el QR cuando el PNG no trae la ficha
dentro (bloque iTXt), opencv-python o pyzbar.
"""
import argparse, json, os, sys, unicodedata, zlib
from collections import Counter

from PIL import Image, PngImagePlugin

FORMAT, VERSION = 'spritevpg', '1.0'
QR_PREFIX = 'SVPG1:'
SCHEMA = 'https://varialgate.github.io/specs/spritevpg/schema/spritevpg-1.schema.json'

# ---------------------------------------------------------------- fuente ----
# SpriteVPG 5x7: la misma tabla que la fuente TTF (font/spritevpg-5x7.ttf).
# Glifos de 5x7, avance 6, línea 9. Solo mayúsculas: el texto se pasa a
# mayúsculas y sin tildes (la Ñ se conserva).
G = {
'A':["01110","10001","10001","11111","10001","10001","10001"],
'B':["11110","10001","10001","11110","10001","10001","11110"],
'C':["01110","10001","10000","10000","10000","10001","01110"],
'D':["11110","10001","10001","10001","10001","10001","11110"],
'E':["11111","10000","10000","11110","10000","10000","11111"],
'F':["11111","10000","10000","11110","10000","10000","10000"],
'G':["01110","10001","10000","10111","10001","10001","01111"],
'H':["10001","10001","10001","11111","10001","10001","10001"],
'I':["11111","00100","00100","00100","00100","00100","11111"],
'J':["00111","00010","00010","00010","00010","10010","01100"],
'K':["10001","10010","10100","11000","10100","10010","10001"],
'L':["10000","10000","10000","10000","10000","10000","11111"],
'M':["10001","11011","10101","10101","10001","10001","10001"],
'N':["10001","10001","11001","10101","10011","10001","10001"],
'O':["01110","10001","10001","10001","10001","10001","01110"],
'P':["11110","10001","10001","11110","10000","10000","10000"],
'Q':["01110","10001","10001","10001","10101","10010","01101"],
'R':["11110","10001","10001","11110","10100","10010","10001"],
'S':["01111","10000","10000","01110","00001","00001","11110"],
'T':["11111","00100","00100","00100","00100","00100","00100"],
'U':["10001","10001","10001","10001","10001","10001","01110"],
'V':["10001","10001","10001","10001","10001","01010","00100"],
'W':["10001","10001","10001","10101","10101","10101","01010"],
'X':["10001","10001","01010","00100","01010","10001","10001"],
'Y':["10001","10001","01010","00100","00100","00100","00100"],
'Z':["11111","00001","00010","00100","01000","10000","11111"],
'Ñ':["01110","00000","10001","11001","10101","10011","10001"],
'0':["01110","10001","10011","10101","11001","10001","01110"],
'1':["00100","01100","00100","00100","00100","00100","01110"],
'2':["01110","10001","00001","00010","00100","01000","11111"],
'3':["11111","00010","00100","00010","00001","10001","01110"],
'4':["00010","00110","01010","10010","11111","00010","00010"],
'5':["11111","10000","11110","00001","00001","10001","01110"],
'6':["00110","01000","10000","11110","10001","10001","01110"],
'7':["11111","00001","00010","00100","01000","01000","01000"],
'8':["01110","10001","10001","01110","10001","10001","01110"],
'9':["01110","10001","10001","01111","00001","00010","01100"],
' ':["00000"]*7,
'.':["00000","00000","00000","00000","00000","01100","01100"],
',':["00000","00000","00000","00000","01100","00100","01000"],
':':["00000","01100","01100","00000","01100","01100","00000"],
'-':["00000","00000","00000","11111","00000","00000","00000"],
'+':["00000","00100","00100","11111","00100","00100","00000"],
'/':["00001","00010","00010","00100","01000","01000","10000"],
'(':["00010","00100","01000","01000","01000","00100","00010"],
')':["01000","00100","00010","00010","00010","00100","01000"],
'=':["00000","00000","11111","00000","11111","00000","00000"],
'#':["01010","01010","11111","01010","11111","01010","01010"],
'>':["01000","00100","00010","00001","00010","00100","01000"],
'<':["00010","00100","01000","10000","01000","00100","00010"],
'*':["00000","10101","01110","11111","01110","10101","00000"],
'%':["11000","11001","00010","00100","01000","10011","00011"],
'_':["00000","00000","00000","00000","00000","00000","11111"],
'"':["01010","01010","00000","00000","00000","00000","00000"],
'·':["00000","00000","00000","00100","00000","00000","00000"],
'×':["00000","10001","01010","00100","01010","10001","00000"],
'→':["00000","00100","00010","11111","00010","00100","00000"],
}

G.update({
';':["00000","01100","01100","00000","01100","00100","01000"],
'!':["00100","00100","00100","00100","00100","00000","00100"],
'?':["01110","10001","00001","00010","00100","00000","00100"],
"'":["00100","00100","01000","00000","00000","00000","00000"],
'&':["01100","10010","10100","01000","10101","10010","01101"],
'[':["01110","01000","01000","01000","01000","01000","01110"],
']':["01110","00010","00010","00010","00010","00010","01110"],
})
ADV, LINE = 6, 9

def norm(s):
    out = []
    for ch in str(s).upper():
        if ch in G:
            out.append(ch)
            continue
        base = unicodedata.normalize('NFD', ch)[0]
        out.append(base if base in G else '?')
    return ''.join(out)

def text_width(s):
    return max(0, len(norm(s)) * ADV - 1)

# ---------------------------------------------------------------- colores ---
PAPER = (242, 238, 227, 255)
INK = (26, 28, 44, 255)
GRID = (200, 193, 178, 255)
PIVOT = (177, 62, 83, 255)
BOX = {'collision': (56, 183, 100, 255), 'hurt': (239, 125, 87, 255),
       'hit': (228, 59, 68, 255), 'interact': (65, 166, 246, 255)}
POINT = (59, 93, 201, 255)
CHECK = ((255, 255, 255, 255), (230, 226, 215, 255))

# ---------------------------------------------------------------- rótulos ---
LABELS = {
 'es': {
  'kind': {'character': 'PERSONAJE', 'creature': 'CRIATURA', 'item': 'OBJETO',
           'prop': 'DECORADO', 'building': 'CONSTRUCCIÓN', 'effect': 'EFECTO',
           'tile': 'CASILLA'},
  'view': {'side': 'VISTA LATERAL', 'front': 'VISTA FRONTAL',
           'threeQuarter': 'VISTA 3/4 CENITAL', 'oblique': 'CENITAL OBLICUA',
           'topDown': 'VISTA CENITAL', 'isometric': 'ISOMÉTRICA'},
  'dir': {'right': 'DER', 'left': 'IZQ', 'down': 'ABAJO', 'up': 'ARRIBA',
          'down-right': 'ABAJO-DER', 'down-left': 'ABAJO-IZQ',
          'up-right': 'ARRIBA-DER', 'up-left': 'ARRIBA-IZQ'},
  'loop': {'loop': 'BUCLE', 'once': 'UNA VEZ', 'pingpong': 'IDA Y VUELTA',
           'hold': 'Y SE QUEDA'},
  'event': {'footstep': 'PASO', 'hit': 'GOLPE', 'hit-end': 'FIN GOLPE',
            'spawn': 'SALIDA'},
  'box': {'collision': 'CHOQUE', 'hurt': 'DAÑO', 'hit': 'GOLPE',
          'interact': 'USO'},
  'point': {'hand_r': 'MANO DER', 'hand_l': 'MANO IZQ', 'head': 'CABEZA',
            'muzzle': 'BOCA', 'spawn': 'SALIDA', 'smoke': 'HUMO',
            'light': 'LUZ', 'ground': 'SUELO'},
  'facing': 'MIRA {d}', 'frame': 'FRAME {w}×{h} · {c}×{r} · DESDE 0,0',
  'palette': 'PALETA', 'detail': 'DETALLE F{i}', 'pivot': 'APOYO {x},{y}',
  'animations': 'ANIMACIONES', 'states': 'ESTADOS', 'style': 'ESTILO: ',
  'ai': 'IA: ', 'index': 'F = FILA×{c} + COLUMNA', 'mirror': '{a} = {b} VOLTEADA',
  'see': 'VER PIE', 'at': '{e} EN {f}', 'ms': 'MS: ', 'card': 'FICHA',
  'footprint': 'HUELLA {w}×{h} CASILLAS DE {t}', 'sortY': 'PROFUNDIDAD Y={y}',
  'ppu': '{p} PX POR UNIDAD', 'default': 'INICIAL', 'license': 'LICENCIA ',
  'sound': 'SONIDO',
 },
 'en': {
  'kind': {'character': 'CHARACTER', 'creature': 'CREATURE', 'item': 'ITEM',
           'prop': 'PROP', 'building': 'BUILDING', 'effect': 'EFFECT',
           'tile': 'TILE'},
  'view': {'side': 'SIDE VIEW', 'front': 'FRONT VIEW',
           'threeQuarter': '3/4 TOP-DOWN', 'oblique': 'OBLIQUE TOP-DOWN',
           'topDown': 'TOP-DOWN', 'isometric': 'ISOMETRIC'},
  'dir': {'right': 'RIGHT', 'left': 'LEFT', 'down': 'DOWN', 'up': 'UP',
          'down-right': 'DOWN-RIGHT', 'down-left': 'DOWN-LEFT',
          'up-right': 'UP-RIGHT', 'up-left': 'UP-LEFT'},
  'loop': {'loop': 'LOOP', 'once': 'ONCE', 'pingpong': 'PING-PONG',
           'hold': 'HOLD'},
  'event': {'footstep': 'STEP', 'hit': 'HIT', 'hit-end': 'HIT END',
            'spawn': 'SPAWN'},
  'box': {'collision': 'COLLISION', 'hurt': 'HURT', 'hit': 'HIT',
          'interact': 'INTERACT'},
  'point': {'hand_r': 'RIGHT HAND', 'hand_l': 'LEFT HAND', 'head': 'HEAD',
            'muzzle': 'MUZZLE', 'spawn': 'SPAWN', 'smoke': 'SMOKE',
            'light': 'LIGHT', 'ground': 'GROUND'},
  'facing': 'FACING {d}', 'frame': 'FRAME {w}×{h} · {c}×{r} · FROM 0,0',
  'palette': 'PALETTE', 'detail': 'DETAIL F{i}', 'pivot': 'PIVOT {x},{y}',
  'animations': 'ANIMATIONS', 'states': 'STATES', 'style': 'STYLE: ',
  'ai': 'AI: ', 'index': 'F = ROW×{c} + COLUMN', 'mirror': '{a} = {b} FLIPPED',
  'see': 'SEE BELOW', 'at': '{e} AT {f}', 'ms': 'MS: ', 'card': 'CARD',
  'footprint': 'FOOTPRINT {w}×{h} TILES OF {t}', 'sortY': 'SORT Y={y}',
  'ppu': '{p} PX PER UNIT', 'default': 'DEFAULT', 'license': 'LICENSE ',
  'sound': 'SOUND',
 },
}

def lab(card):
    return LABELS.get(card.get('lang', 'es'), LABELS['es'])

def custom(v):
    return v.split(':', 1)[1] if isinstance(v, str) and v.startswith('custom:') else v

# ---------------------------------------------------------------- Base45 ----
A45 = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:'

def b45encode(bs):
    out = []
    for i in range(0, len(bs), 2):
        if i + 1 < len(bs):
            n = bs[i] * 256 + bs[i + 1]
            c, n = n % 45, n // 45
            d, e = n % 45, n // 45
            out += [A45[c], A45[d], A45[e]]
        else:
            out += [A45[bs[i] % 45], A45[bs[i] // 45]]
    return ''.join(out)

def b45decode(s):
    out = bytearray()
    for i in range(0, len(s), 3):
        ch = s[i:i + 3]
        n = sum(A45.index(c) * 45 ** k for k, c in enumerate(ch))
        out += bytes([n // 256, n % 256]) if len(ch) == 3 else bytes([n])
    return bytes(out)

def card_to_payloads(card, max_chars=3000):
    data = b45encode(zlib.compress(json.dumps(card, separators=(',', ':'),
                                              ensure_ascii=False).encode(), 9))
    if len(data) <= max_chars:
        return [QR_PREFIX + data]
    parts = [data[i:i + max_chars] for i in range(0, len(data), max_chars)]
    return [f'{QR_PREFIX}{k + 1}/{len(parts)}:{p}' for k, p in enumerate(parts)]

def payloads_to_card(payloads):
    chunks = {}
    for p in payloads:
        if not p.startswith(QR_PREFIX):
            continue
        body = p[len(QR_PREFIX):]
        head = body.split(':', 1)
        if len(head) == 2 and '/' in head[0] and head[0].replace('/', '').isdigit():
            k, _ = head[0].split('/')
            chunks[int(k)] = head[1]
        else:
            chunks[1] = body
    if not chunks:
        return None
    data = ''.join(chunks[k] for k in sorted(chunks))
    return json.loads(zlib.decompress(b45decode(data)))

# ---------------------------------------------------------------- utilidades
def frame_rect(card, i):
    for f in card.get('frames', []):
        if f['i'] == i:
            return f
    g = card['grid']
    c, fw, fh = g['columns'], g['frameSize']['w'], g['frameSize']['h']
    return {'i': i, 'x': (i % c) * fw, 'y': (i // c) * fh, 'w': fw, 'h': fh}

def frame_value(card, i, kind, name=None):
    """Caja, punto o apoyo de un frame: el suyo, el de la animación o el de
    defaults."""
    d = card.get('defaults', {})
    val = d.get(kind)
    if name is not None:
        val = (val or {}).get(name)
    f = next((f for f in card.get('frames', []) if f['i'] == i), {})
    own = f.get(kind)
    if name is not None:
        own = (own or {}).get(name)
    for a in card.get('animations', []):
        for af in a['frames']:
            if af['frame'] == i:
                v = af.get(kind)
                if name is not None:
                    v = (v or {}).get(name)
                if v is not None:
                    own = v
    return own if own is not None else val

def frames_of(a):
    return [f['frame'] for f in a['frames']]

def ranges(nums):
    nums = list(nums)
    if nums == list(range(nums[0], nums[0] + len(nums))):
        return f'F{nums[0]}-{nums[-1]}' if len(nums) > 1 else f'F{nums[0]}'
    return ' '.join(f'F{n}' for n in nums)

def wrap(s, width_px):
    words, lines, cur = norm(s).split(' '), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if text_width(t) <= width_px or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

# ---------------------------------------------------------------- dibujo ----
class Canvas:
    def __init__(self, img):
        self.img, self.px = img, img.load()

    def text(self, x, y, s, col=INK):
        for ch in norm(s):
            for r, row in enumerate(G[ch]):
                for c, b in enumerate(row):
                    if b == '1':
                        self.px[x + c, y + r] = col
            x += ADV
        return x

    def h(self, x0, x1, y, col):
        for x in range(x0, x1 + 1):
            self.px[x, y] = col

    def v(self, x, y0, y1, col):
        for y in range(y0, y1 + 1):
            self.px[x, y] = col

    def rect(self, x, y, w, h, col):
        self.h(x, x + w - 1, y, col)
        self.h(x, x + w - 1, y + h - 1, col)
        self.v(x, y, y + h - 1, col)
        self.v(x + w - 1, y, y + h - 1, col)

    def fill(self, x, y, w, h, col):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.px[xx, yy] = col

def auto_palette(sheet, n=16):
    cnt = Counter(p[:3] for p in sheet.convert('RGBA').get_flattened_data() if p[3]) if hasattr(sheet, 'get_flattened_data') else Counter(p[:3] for p in sheet.convert('RGBA').getdata() if p[3])
    return ['#%02x%02x%02x' % c for c, _ in cnt.most_common(n)]

def hex_rgba(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)

def row_label(card, r, cols, nlines):
    """Rótulo de la fila r: las animaciones que empiezan en ella."""
    L = lab(card)
    first, last = r * cols, r * cols + cols - 1
    anims = [a for a in card.get('animations', [])
             if first <= frames_of(a)[0] <= last]
    states = [s for s in card.get('states', [])
              if 'frame' in s and first <= s['frame'] <= last]
    if anims:
        a = anims[0]
        name = custom(a['name']).upper()
        d = L['dir'].get(a.get('direction', ''), '')
        ms = {f['ms'] for f in a['frames']}
        lines = [f'{name} {d}'.strip(),
                 f'{ranges(frames_of(a))} {L["loop"].get(a.get("loop", "loop"), "")}',
                 f'{ms.pop()}MS' if len(ms) == 1 else L['see']]
        if len(anims) > 1:
            lines[0] += ' +' + str(len(anims) - 1)
    elif states:
        lines = [' · '.join(custom(s['name']).upper() for s in states)]
    else:
        lines = []
    return lines[:nlines]

def render(sheet, card):
    """Dibuja el sprite pattern a partir de la hoja limpia y la ficha."""
    L = lab(card)
    g = card['grid']
    cols, rows = g['columns'], g['rows']
    fw, fh = g['frameSize']['w'], g['frameSize']['h']
    AW, AH = cols * fw, rows * fh
    if sheet.size != (AW, AH):
        sheet = sheet.crop((0, 0, AW, AH))
    nlines = max(1, min(3, fh // LINE))
    labels = [row_label(card, r, cols, nlines) for r in range(rows)]
    RW = max([60] + [text_width(t) for ls in labels for t in ls]) + 2
    GAP = 8
    W = max(AW + GAP + RW, 256)

    # Pie: se maqueta primero para saber la altura.
    pal = card['art'].get('palette') or [{'color': c} for c in auto_palette(sheet)]
    ref = card.get('style', {}).get('reference', {}).get('frame')
    if ref is None:
        ref = card['frames'][0]['i'] if card.get('frames') else 0
    details = [ref]
    for a in card.get('animations', []):
        for af in a['frames']:
            if af.get('boxes') and af['frame'] not in details and len(details) < 2:
                details.append(af['frame'])
    k = 2 if fw <= 48 and fh <= 48 else 1
    pw, ph = fw * k, fh * k
    lines = [L['animations']]
    for a in card.get('animations', []):
        name = custom(a['name']).upper()
        d = L['dir'].get(a.get('direction', ''), '')
        ms = [f['ms'] for f in a['frames']]
        loop = L['loop'].get(a.get('loop', 'loop'), '')
        nxt = f' → {custom(a["next"]).upper()}' if a.get('next') else ''
        lines.append(f'{name} {d} {ranges(frames_of(a))} {loop}{nxt}'.replace('  ', ' '))
        if len(set(ms)) == 1:
            lines.append(f'  {ms[0]}MS')
        else:
            lines.append('  ' + L['ms'] + ', '.join(f'F{f["frame"]} {f["ms"]}' for f in a['frames']))
        ev = {}
        for f in a['frames']:
            for e in f.get('events', []):
                if e.startswith('sound:'):
                    e = L['sound'] + ' ' + e[6:].upper()
                ev.setdefault(L['event'].get(e, custom(e).upper()), []).append(f'F{f["frame"]}')
        for e, fs in ev.items():
            lines.append('  ' + L['at'].format(e=e, f=', '.join(fs)))
    for dst, m in card.get('directions', {}).get('mirror', {}).items():
        lines.append(L['mirror'].format(a=L['dir'].get(dst, dst), b=L['dir'].get(m['from'], m['from'])))
    if card.get('states'):
        lines.append(L['states'])
        for s in card['states']:
            where = f'F{s["frame"]}' if 'frame' in s else custom(s.get('animation', '')).upper()
            extra = f' ({L["default"]})' if s.get('default') else ''
            lines.append(f'  {custom(s["name"]).upper()} {where}{extra}')
    w = card.get('world', {})
    if w.get('pixelsPerUnit'):
        lines.append(L['ppu'].format(p=w['pixelsPerUnit']))
    if w.get('footprint'):
        fp = w['footprint']
        lines.append(L['footprint'].format(w=fp['w'], h=fp['h'], t=fp['tileSize']))
    if 'sortY' in w:
        lines.append(L['sortY'].format(y=w['sortY']))
    legend_items = []
    for b in ('collision', 'hurt', 'hit', 'interact'):
        if any(frame_value(card, i, 'boxes', b) for i in details):
            legend_items.append((BOX[b], L['box'][b]))
    for pname in sorted({p for i in details for p in (frame_value(card, i, 'points') or {})}):
        legend_items.append((POINT, L['point'].get(pname, custom(pname).upper())))
    piv = card.get('defaults', {}).get('pivot', {'x': fw // 2, 'y': fh - 1})
    legend_items.append((PIVOT, L['pivot'].format(x=piv['x'], y=piv['y'])))
    left_w = max([pw, text_width(L['detail'].format(i=99))] +
                 [12 + text_width(t) for _, t in legend_items])
    tx = 4 + left_w + 8
    tw = W - tx - 4
    text = []
    for ln in lines:
        text += wrap(ln, tw)
    st = card.get('style', {}).get('summary')
    if st:
        text += wrap(L['style'] + st, tw)
    text.append(norm(L['index'].format(c=cols)))
    for hw in card.get('ai', {}).get('howTo', []):
        text += wrap(L['ai'] + hw, tw)
    prov = card.get('provenance', {})
    lic = prov.get('license')
    gen = prov.get('generator', {}).get('app')
    if lic or gen:
        text += wrap(' · '.join(x for x in [L['license'] + lic if lic else None, gen] if x), tw)

    payloads = card_to_payloads(card)
    import qrcode
    mats = []
    for p in payloads:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                           border=0, box_size=1)
        qr.add_data(qrcode.util.QRData(p, mode=qrcode.util.MODE_ALPHA_NUM))
        qr.make(fit=True)
        mats.append(qr.get_matrix())

    strip = AH + 16
    head = strip + 4
    foot = head + 40
    left_h = len(details) * (ph + 12) + len(legend_items) * LINE + 4
    text_h = len(text) * LINE
    qr_h = max(len(m) for m in mats) + 10
    qr_w = sum(len(m) + 4 for m in mats)
    body_h = max(left_h, text_h + qr_h + 4)
    if tx + max(text_width(t) for t in text) > W - qr_w - 4:
        body_h = max(left_h, text_h + qr_h + 4)
    H = foot + body_h + 6

    img = Image.new('RGBA', (W, H), PAPER)
    cv = Canvas(img)
    cv.fill(0, 0, AW, AH, (0, 0, 0, 0))
    img.alpha_composite(sheet.convert('RGBA'), (0, 0))
    cv = Canvas(img)

    # A la derecha: rótulos de fila, bordes y muesca del apoyo (y).
    for r in range(rows):
        y0 = r * fh
        for j, t in enumerate(labels[r]):
            cv.text(AW + GAP, y0 + 1 + j * 10, t)
        if r:
            cv.h(AW + 1, AW + 3, y0, GRID)
        ay = y0 + piv['y']
        cv.v(AW + 5, ay - 2, ay + 2, PIVOT)
        cv.v(AW + 4, ay - 1, ay + 1, PIVOT)
        cv.px[AW + 3, ay] = PIVOT
    # Debajo: bordes de columna, muesca del apoyo (x) y número de columna.
    for c in range(cols):
        if c:
            cv.v(c * fw, AH + 1, AH + 3, GRID)
        ax = c * fw + piv['x']
        cv.h(ax - 2, ax + 2, AH + 5, PIVOT)
        cv.h(ax - 1, ax + 1, AH + 4, PIVOT)
        cv.px[ax, AH + 3] = PIVOT
        s = str(c)
        if text_width(s) <= fw:
            cv.text(c * fw + fw // 2 - text_width(s) // 2, AH + 8, s)
    # Marcas de registro: las tres esquinas exteriores de la zona.
    for t in range(4):
        cv.px[AW + 1, t] = INK; cv.px[AW + 1 + t, 0] = INK
        cv.px[0, AH + 1 + t] = INK; cv.px[t, AH + 1] = INK
        cv.px[AW + 1, AH + 1 + t] = INK; cv.px[AW + 1 + t, AH + 1] = INK
    # Cabecera.
    cv.h(0, W - 1, head - 2, GRID)
    e = card['entity']
    cv.text(4, head + 1, f'{FORMAT.upper()} {VERSION} · {e.get("displayName", e["name"])}')
    view = L['view'].get(card['art'].get('view'), '')
    facing = card['art'].get('facing')
    l2 = [L['kind'].get(e['kind'], custom(e['kind']).upper()), view]
    if facing:
        l2.append(L['facing'].format(d=L['dir'].get(facing, facing)))
    cv.text(4, head + 10, ' · '.join(x for x in l2 if x))
    cv.text(4, head + 19, L['frame'].format(w=fw, h=fh, c=cols, r=rows))
    x = cv.text(4, head + 29, L['palette']) + 4
    for p in pal:
        if x + 6 > W - 40:
            break
        cv.fill(x, head + 28, 6, 7, INK)
        cv.fill(x + 1, head + 29, 4, 5, hex_rgba(p['color']))
        x += 8
    rx = W - 36
    cv.h(rx, rx + 31, head + 33, INK)
    for t in range(0, 33, 8):
        cv.v(min(rx + t, rx + 31), head + 30, head + 33, INK)
    cv.text(rx, head + 21, '32 PX')
    cv.h(0, W - 1, foot - 4, GRID)
    # Pie, izquierda: detalles con cajas, puntos y apoyo, y la leyenda.
    y = foot
    for i in details:
        cv.text(4, y, L['detail'].format(i=i))
        dx, dy = 4, y + 10
        for yy in range(dy - 1, dy + ph + 1):
            for xx in range(dx - 1, dx + pw + 1):
                cv.px[xx, yy] = CHECK[(xx // 4 + yy // 4) % 2]
        fr = frame_rect(card, i)
        crop = sheet.crop((fr['x'], fr['y'], fr['x'] + fr['w'], fr['y'] + fr['h']))
        img.alpha_composite(crop.resize((fr['w'] * k, fr['h'] * k), Image.NEAREST), (dx, dy))
        cv = Canvas(img)
        for b in ('hurt', 'collision', 'interact', 'hit'):
            bx = frame_value(card, i, 'boxes', b)
            if bx:
                cv.rect(dx + bx['x'] * k, dy + bx['y'] * k, bx['w'] * k, bx['h'] * k, BOX[b])
        for pname, pt in (frame_value(card, i, 'points') or {}).items():
            px_, py_ = dx + pt['x'] * k, dy + pt['y'] * k
            cv.h(px_ - 2, px_ + 2, py_, POINT); cv.v(px_, py_ - 2, py_ + 2, POINT)
        pv = frame_value(card, i, 'pivot') or piv
        ax, ay = dx + pv['x'] * k, dy + pv['y'] * k
        cv.h(ax - 2, ax + 2, min(ay, dy + ph - 1), PIVOT)
        cv.v(ax, ay - 2, min(ay + 1, dy + ph - 1), PIVOT)
        y = dy + ph + 2
    y += 2
    for col, t in legend_items:
        cv.fill(4, y + 1, 5, 5, col)
        cv.text(12, y, t)
        y += LINE
    # Pie, derecha: texto y QR.
    for j, t in enumerate(text):
        cv.text(tx, foot + j * LINE, t)
    qy = H - max(len(m) for m in mats) - 4
    qx = W - 4
    for m in reversed(mats):
        n = len(m)
        qx -= n
        for yy in range(n):
            for xx in range(n):
                cv.px[qx + xx, qy + yy] = INK if m[yy][xx] else PAPER
        qx -= 4
    cv.text(qx + 4, qy - 9, L['card'] + (f' ×{len(mats)}' if len(mats) > 1 else ''))
    return img

# ---------------------------------------------------------------- ficha -----
def complete(card, sheet):
    """Rellena lo que se calcula: formato, frames con dibujo, tamaño, paleta."""
    g = card['grid']
    cols, rows = g['columns'], g['rows']
    fw, fh = g['frameSize']['w'], g['frameSize']['h']
    card = {'format': FORMAT, 'version': VERSION, '$schema': SCHEMA, **card}
    if not card.get('frames'):
        fr = []
        for i in range(cols * rows):
            x, y = (i % cols) * fw, (i // cols) * fh
            box = sheet.crop((x, y, x + fw, y + fh)).getbbox()
            if box:
                fr.append({'i': i, 'x': x, 'y': y, 'w': fw, 'h': fh})
        card['frames'] = fr
    if not card['art'].get('palette'):
        card['art']['palette'] = [{'color': c} for c in auto_palette(sheet)]
    return card

def make(sheet_path, card_path, out, preview=0):
    sheet = Image.open(sheet_path).convert('RGBA')
    card = json.load(open(card_path, encoding='utf-8'))
    card = complete(card, sheet)
    g = card['grid']
    AW, AH = g['columns'] * g['frameSize']['w'], g['rows'] * g['frameSize']['h']
    # Dos pasadas: el tamaño de la imagen va en la ficha, y la ficha en el QR.
    card['image'] = {'file': os.path.basename(out), 'w': 0, 'h': 0, 'pixelArt': True,
                     'framesArea': {'x': 0, 'y': 0, 'w': AW, 'h': AH}}
    for _ in range(3):
        img = render(sheet, card)
        if (card['image']['w'], card['image']['h']) == img.size:
            break
        card['image']['w'], card['image']['h'] = img.size
    info = PngImagePlugin.PngInfo()
    info.add_itxt(FORMAT, json.dumps(card, ensure_ascii=False, separators=(',', ':')), zip=True)
    img.save(out, pnginfo=info)
    if preview:
        # Copia para enseñar: ampliada y con damero donde es transparente.
        prev = Image.new('RGBA', img.size)
        pp = prev.load()
        for y in range(img.height):
            for x in range(img.width):
                pp[x, y] = CHECK[(x // 4 + y // 4) % 2]
        prev.alpha_composite(img)
        prev.resize((img.width * preview, img.height * preview), Image.NEAREST).save(
            out.replace('.png', f'@{preview}x.png'))
    return card, img

def read_card(path):
    """La ficha de un patrón: del bloque iTXt o, si no está, del QR."""
    img = Image.open(path)
    txt = getattr(img, 'text', {}) or {}
    if FORMAT in txt:
        return json.loads(txt[FORMAT]), 'itxt'
    payloads = decode_qr(img)
    card = payloads_to_card(payloads)
    if card is None:
        raise SystemExit('No se encuentra la ficha: ni bloque iTXt ni QR legible.')
    return card, 'qr'

def decode_qr(img):
    """Lee los QR del patrón (uno o varios). Prueba OpenCV (primero el detector
    para códigos grandes) y, si no está, pyzbar."""
    rgb = img.convert('RGB')
    tried = False
    for k in (3, 4, 2):
        big = rgb.resize((rgb.width * k, rgb.height * k), Image.NEAREST)
        try:
            import cv2, numpy as np
        except ImportError:
            break
        tried = True
        arr = cv2.cvtColor(np.array(big), cv2.COLOR_RGB2BGR)
        dets = [cv2.QRCodeDetectorAruco()] if hasattr(cv2, 'QRCodeDetectorAruco') else []
        dets.append(cv2.QRCodeDetector())
        for det in dets:
            try:
                ok, vals, _, _ = det.detectAndDecodeMulti(arr)
                vals = [v for v in (vals or []) if v]
            except cv2.error:
                vals = []
            if not vals:
                v = det.detectAndDecode(arr)[0]
                vals = [v] if v else []
            if vals:
                return vals
    try:
        from pyzbar.pyzbar import decode
        return [d.data.decode() for d in decode(rgb.resize((rgb.width * 3, rgb.height * 3), Image.NEAREST))]
    except ImportError:
        if not tried:
            raise SystemExit('Para leer el QR hace falta opencv-python o pyzbar.')
        return []

def scale_of(img, card):
    k = img.width / card['image']['w']
    if k != int(k) or img.height != card['image']['h'] * k:
        raise SystemExit(f'La imagen mide {img.size} y la ficha dice '
                         f'{card["image"]["w"]}x{card["image"]["h"]}: no es una ampliación entera.')
    return int(k)

def read(path, outdir, gifs=False):
    card, src = read_card(path)
    img = Image.open(path).convert('RGBA')
    k = scale_of(img, card)
    if k > 1:
        img = img.resize((img.width // k, img.height // k), Image.NEAREST)
    os.makedirs(outdir, exist_ok=True)
    fa = card['image']['framesArea']
    sheet = img.crop((fa['x'], fa['y'], fa['x'] + fa['w'], fa['y'] + fa['h']))
    base = card['entity']['name']
    sheet.save(os.path.join(outdir, f'{base}.sheet.png'))
    json.dump(card, open(os.path.join(outdir, f'{base}.spritevpg.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    fdir = os.path.join(outdir, 'frames')
    os.makedirs(fdir, exist_ok=True)
    for f in card['frames']:
        sheet.crop((f['x'], f['y'], f['x'] + f['w'], f['y'] + f['h'])).save(
            os.path.join(fdir, f'{f["i"]:03d}.png'))
    if gifs:
        for a in card.get('animations', []):
            fr = [sheet.crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h']))
                  for r in (frame_rect(card, i) for i in frames_of(a))]
            big = [f.resize((f.width * 4, f.height * 4), Image.NEAREST) for f in fr]
            name = custom(a['name']) + (f'_{a["direction"]}' if a.get('direction') else '')
            big[0].save(os.path.join(outdir, f'{name}.gif'), save_all=True,
                        append_images=big[1:], duration=[f['ms'] for f in a['frames']],
                        loop=0 if a.get('loop', 'loop') != 'once' else 1, disposal=2)
    return card, src, k

# ---------------------------------------------------------------- validar ---
KINDS = {'character', 'creature', 'item', 'prop', 'building', 'effect', 'tile'}
VIEWS = {'side', 'front', 'threeQuarter', 'oblique', 'topDown', 'isometric'}
DIRS = {'down', 'up', 'left', 'right', 'down-left', 'down-right', 'up-left', 'up-right'}
LOOPS = {'loop', 'once', 'pingpong', 'hold'}

def validate(card):
    err, warn = [], []
    def need(cond, msg):
        if not cond:
            err.append(msg)
    need(card.get('format') == FORMAT, 'format debe ser "spritevpg"')
    need(str(card.get('version', '')).split('.')[0] == '1', 'version 1.x')
    for k in ('image', 'entity', 'art', 'grid', 'frames', 'defaults', 'ai', 'provenance'):
        need(k in card, f'falta {k}')
    if err:
        return err, warn
    e = card['entity']
    need(e.get('kind') in KINDS or str(e.get('kind', '')).startswith('custom:'), 'entity.kind no válido')
    need(bool(e.get('name')), 'falta entity.name')
    v = card['art'].get('view')
    need(v is None or v in VIEWS, f'art.view no válido: {v}')
    g = card['grid']
    fw, fh = g['frameSize']['w'], g['frameSize']['h']
    fa = card['image'].get('framesArea', {})
    need(fa.get('x') == 0 and fa.get('y') == 0, 'framesArea debe empezar en 0,0')
    need(fa.get('w') == g['columns'] * fw and fa.get('h') == g['rows'] * fh,
         'framesArea no coincide con la rejilla')
    ids = set()
    for f in card['frames']:
        ids.add(f['i'])
        need(f['x'] + f['w'] <= fa.get('w', 0) and f['y'] + f['h'] <= fa.get('h', 0),
             f'frame {f["i"]} fuera de la zona de frames')
    names = set()
    for a in card.get('animations', []):
        key = (a['name'], a.get('direction'))
        need(key not in names, f'animación repetida: {key}')
        names.add(key)
        need(a.get('loop', 'loop') in LOOPS, f'{a["name"]}: loop no válido')
        need(a.get('direction') is None or a['direction'] in DIRS, f'{a["name"]}: dirección no válida')
        for f in a['frames']:
            need(f['frame'] in ids, f'{a["name"]}: el frame {f["frame"]} no existe')
            need(isinstance(f.get('ms'), int) and f['ms'] > 0, f'{a["name"]}: ms no válido en F{f["frame"]}')
        if a.get('next'):
            need(any(b['name'] == a['next'] for b in card['animations']), f'{a["name"]}: next desconocido')
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
        col = c.get('color', '')
        need(len(col) == 7 and col.startswith('#'), f'color no válido: {col}')
    if not card['ai'].get('summary'):
        warn.append('falta ai.summary')
    if 'style' not in card:
        warn.append('sin style: una IA no tendrá guía para ampliarla')
    return err, warn

# ---------------------------------------------------------------- resumen ---
def summary(card):
    L = lab(card)
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
    i = sub.add_parser('info', help='resumen legible de la ficha')
    i.add_argument('path')
    v = sub.add_parser('validate', help='comprueba la ficha')
    v.add_argument('path')
    a = p.parse_args(argv)

    def load(path):
        if path.lower().endswith('.json'):
            return json.load(open(path, encoding='utf-8'))
        return read_card(path)[0]

    if a.cmd == 'make':
        card, img = make(a.sheet, a.card, a.out, a.preview)
        err, warn = validate(card)
        print(f'{a.out}: {img.width}x{img.height}')
        for w in warn:
            print('aviso:', w)
        for e in err:
            print('error:', e)
        return 1 if err else 0
    if a.cmd == 'read':
        card, src, k = read(a.pattern, a.out, a.gifs)
        print(f'Ficha leída del {"bloque iTXt" if src == "itxt" else "QR"} (escala x{k}). '
              f'{len(card["frames"])} frames en {a.out}/')
        return 0
    if a.cmd == 'info':
        print(summary(load(a.path)))
        return 0
    if a.cmd == 'validate':
        err, warn = validate(load(a.path))
        for w in warn:
            print('aviso:', w)
        for e in err:
            print('error:', e)
        print('válida' if not err else f'{len(err)} errores')
        return 1 if err else 0

if __name__ == '__main__':
    sys.exit(main())
