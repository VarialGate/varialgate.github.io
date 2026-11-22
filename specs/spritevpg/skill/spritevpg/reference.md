# SpriteVPG 1.0 · referencia

Especificación completa: https://varialgate.github.io/specs/spritevpg/spec.html
Esquema JSON: https://varialgate.github.io/specs/spritevpg/schema/spritevpg-1.schema.json

Unidades: píxeles nativos, origen arriba a la izquierda, `y` hacia abajo; puntos y cajas relativos al frame;
duraciones en ms. Lo opcional se omite; lo desconocido se ignora.

## La notación de los márgenes

Texto en celdas de 4×7 px (fuente SpriteVPG 3×5, mayúsculas). Zonas con barra de título en negativo. En cada zona,
líneas `CLAVE valor`; una fila que empieza con espacio continúa la anterior. Puntos `x,y`; tamaños `WxH` con `X`;
rectángulos `x,y WxH`; frames `F12` o `F6-11`; colores sin `#`.

| Zona | Líneas |
| --- | --- |
| `ENTITY` | `NAME id` · `TITLE texto` · `KIND tipo` · `TAGS a, b` · `DESC texto` |
| `SHEET` | `FRAME 32X32` · `GRID columnasXfilas` · `FRAMES 0-1 6-15` |
| `ART` | `VIEW vista` · `FACING dir` · `LIGHT texto` · `OUTLINE estilo ancho [color]` · `SHADOW tipo` · `PALETTE color[:papel] …` |
| `BODY` | `PIVOT x,y` · `BOX nombre x,y WxH` · `POINT nombre x,y` · `F12 PIVOT … BOX … POINT …` |
| `ANIMATIONS` | `nombre [dir] bucle [> siguiente]` + frames: `F12 80 [eventos] [OFFSET dx,dy] [PIVOT …] [BOX …] [POINT …]`; `F6-11 110` |
| `DIRECTIONS` | `SET dir …` · `MIRROR destino = origen FLIP X` |
| `STATES` | `nombre F0 [GROUP g] [DEFAULT]` · `nombre ANIM animación` |
| `WORLD` | `PPU n` · `FOOTPRINT WxH TILE n [ORIGIN x,y]` · `SORTY n` · `SHADOW F30 [OFFSET dx,dy]` |
| `STYLE` | `SUMMARY texto` · `PROPORTIONS texto` · `RULE texto` · `REFERENCE F0` |
| `AI` | `SUMMARY texto` · `HOWTO texto` · `WARNING texto` |
| `PROVENANCE` | `APP` · `VERSION` · `MODEL` · `CREATED` · `AUTHOR` · `LICENSE` · `PROMPT` |

`DETAIL` es un dibujo (frames ampliados con cajas, puntos y apoyo, y su leyenda), no datos.
Barra final: `SPRITEVPG 1.0` + enlace a la especificación.

## La ficha en JSON

| Campo | Obligatorio | Valores |
| --- | --- | --- |
| `format` | sí | `"spritevpg"` |
| `version` | sí | `"1.0"` |
| `image` | no (lo calcula `make`; no se dibuja) | `{ file, w, h, pixelArt, framesArea: { x: 0, y: 0, w, h } }` |
| `entity.kind` | sí | `character`, `creature`, `item`, `prop`, `building`, `effect`, `tile`, `custom:…` |
| `entity.name` | sí | `[a-z0-9_-]+` |
| `entity.displayName`, `description`, `tags` | no | texto |
| `art.view` | sí | `side`, `front`, `threeQuarter`, `oblique`, `topDown`, `isometric` |
| `art.facing` | no | dirección (abajo) |
| `art.light`, `outline {style, width, color}`, `shadow` | no | `shadow`: `none`, `baked`, `separate` |
| `art.palette[]` | no (lo calcula `make`) | `{ color: "#rrggbb", role }`; roles: `outline`, `skin`, `hair`, `primary`, `secondary`, `accent`, `metal`, `wood`, `glass`, `light`, `shadow`, con `-light`/`-dark` |
| `grid` | sí | `{ columns, rows, frameSize: { w, h }, margin: 0, spacing: 0 }` |
| `frames[]` | sí (lo calcula `make`) | `{ i, x, y, w, h, pivot?, boxes?, points? }` |
| `defaults.pivot` | sí | `{ x, y }` |
| `defaults.boxes` | no | `collision`, `hurt`, `hit`, `interact`, `custom:…` → `{ x, y, w, h }` |
| `defaults.points` | no | `hand_r`, `hand_l`, `head`, `muzzle`, `spawn`, `smoke`, `light`, `ground`, `custom:…` → `{ x, y }` |
| `directions.set` | no | `down`, `up`, `left`, `right`, `down-left`, `down-right`, `up-left`, `up-right` |
| `directions.mirror` | no | `{ "left": { "from": "right", "flip": "x" } }` |
| `animations[].name` | sí | `idle`, `walk`, `run`, `jump`, `fall`, `land`, `attack`, `cast`, `shoot`, `hurt`, `death`, `use`, `climb`, `swim`, `open`, `close`, `active`, `build`, `destroy`, `play`, `custom:…` |
| `animations[].direction` | no | dirección |
| `animations[].loop` | no | `loop` (por defecto), `once`, `pingpong`, `hold` |
| `animations[].next` | no | nombre de otra animación |
| `animations[].frames[]` | sí | `{ frame, ms, events?, offset?: {dx, dy}, pivot?, boxes?, points? }` |
| eventos | no | `footstep`, `hit`, `hit-end`, `spawn`, `sound:<nombre>`, `custom:…` |
| `states[]` | no | `{ name, frame | animation, group?, default? }` |
| `world` | no | `{ pixelsPerUnit, footprint: { tileSize, w, h, origin }, sortY, shadow: { frame, offset } }` |
| `style` | recomendado | `{ summary, proportions, rules[], reference: { frame } }` |
| `ai` | sí | `{ summary, howTo[], warnings[] }` |
| `provenance` | sí | `{ generator: { app, version, model }, created, author, license, prompt }` |

Precedencia de apoyo, cajas y puntos de un frame: el frame dentro de la animación > `frames[]` > `defaults`.

Manda lo dibujado. Copia opcional en JSON: bloque PNG iTXt `spritevpg` (se usa solo si coincide con el dibujo).
