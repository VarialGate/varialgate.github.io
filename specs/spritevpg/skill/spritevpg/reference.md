# SpriteVPG 1.0 · referencia de la ficha

Especificación completa: https://varialgate.github.io/specs/spritevpg/spec.html
Esquema: https://varialgate.github.io/specs/spritevpg/schema/spritevpg-1.schema.json

Unidades: píxeles nativos, origen arriba a la izquierda, `y` hacia abajo; puntos y cajas relativos al frame;
duraciones en ms. Lo opcional se omite; los campos desconocidos se ignoran.

| Campo | Obligatorio | Valores |
| --- | --- | --- |
| `format` | sí | `"spritevpg"` |
| `version` | sí | `"1.0"` |
| `lang` | no | `es` (por defecto) o `en`: idioma de los rótulos |
| `image` | sí (lo calcula `make`) | `{ file, w, h, pixelArt, framesArea: { x: 0, y: 0, w, h } }` |
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

QR: `SVPG1:` + Base45(zlib(JSON compacto)); varios: `SVPG1:k/n:…`. Copia: PNG iTXt `spritevpg`. Manda el QR.
