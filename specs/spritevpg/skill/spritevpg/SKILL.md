---
name: spritevpg
description: Entender, recortar, validar, generar y ampliar sprite patterns SpriteVPG (Sprite Varial Pixel Gen) — hojas de sprites PNG con los frames limpios desde la esquina de arriba a la izquierda, una animación por fila con su rótulo a la derecha (nombre, «FRAMES: 6», «MS/FRAME: 110», «PLAY: LOOP»), y debajo dos zonas con barra de título, SHEET (NAME, FRAME, GRID) y SUBJECT (KIND, VIEW, FACING, DESC), y una barra final con «SPRITEVPG 1.0» y, debajo, «HTTPS://VARIALGATE.GITHUB.IO/SPECS/SPRITEVPG/». Úsalo cuando aparezca un fichero *.spritevpg.png o una hoja de sprites con ese aspecto, o cuando se pida crear, leer, importar en un motor, recortar, animar o añadir animaciones a una hoja de sprites en este formato.
---

# SpriteVPG: sprite patterns

Un **sprite pattern** es una hoja de sprites PNG que dice ella misma cómo se corta, qué es y cómo se anima:

- **Frames** desde `(0, 0)`, en rejilla de `columnas × filas` celdas de `fw × fh`, sin margen ni separación, con
  fondo transparente. **Una fila = una animación**; sus frames van seguidos desde la izquierda. El frame de la fila
  `r` y la columna `c` está en `x = c·fw`, `y = r·fh`.
- Todo dato va como `ETIQUETA: valor`. Una línea que empieza con espacio continúa la de arriba.
- **Rótulo de cada fila**, a su derecha, en el orden de las filas: el nombre y, sangrados, sus datos.

  ```
  ATTACK
    FRAMES: 4
    MS/FRAME: 80 120 90 160
    PLAY: ONCE
  ```

  `MS/FRAME`: un número (todos igual) o uno por frame. `PLAY`: `LOOP` (en bucle), `ONCE` (una vez, se queda en el
  último frame) o `STILL` (imágenes sueltas, no una animación; sin `MS/FRAME`). En filas bajas va seguido:
  `ITEMS · FRAMES: 5 · PLAY: STILL`.
- **`SHEET`**, debajo: `NAME: …`, `FRAME: 32X32 PX`, `GRID: 6 COLUMNS X 3 ROWS`, `ORIGIN: TOP-LEFT 0,0, NO GAPS`.
- **`SUBJECT`** (opcional): `KIND:` (character, creature, item, prop, building, effect, tile, ui), `VIEW:` (una de
  las seis vistas de abajo), `FACING:` (right, left, up, down o una diagonal) y `DESC:` (frase breve).
- **Barra final**, en dos filas: `SPRITEVPG 1.0` y, debajo, `HTTPS://VARIALGATE.GITHUB.IO/SPECS/SPRITEVPG/`.
- Texto en mayúsculas con la fuente SpriteVPG 4×6, en celdas de 5×8 px, tinta `#1F2A44` sobre papel `#F3EEDD`.

Especificación: https://varialgate.github.io/specs/spritevpg/spec.html

## Herramienta

`scripts/spritevpg.py` (Python 3; solo necesita Pillow):

```bash
pip install pillow                                     # si falta
python3 scripts/spritevpg.py info     patron.png       # resumen legible
python3 scripts/spritevpg.py validate patron.png
python3 scripts/spritevpg.py read     patron.png -o salida/ --gifs
python3 scripts/spritevpg.py make     hoja.png datos.json -o nombre.spritevpg.png --preview 4
```

Lee los datos del propio dibujo: funciona con PNG sin metadatos y con copias ampliadas a escala entera. No funciona con
JPEG ni con imágenes reescaladas con suavizado.

## Entender un sprite pattern

- Con herramienta: `info`. Di qué es (tipo, vista, hacia dónde mira, descripción), el tamaño de frame, la rejilla y,
  por fila, la animación, sus frames, su duración y cómo se reproduce.
- Solo mirando la imagen: lee el rótulo de cada fila y las dos zonas; cada dato lleva su etiqueta. Si la letra se ve pequeña o borrosa, pide la
  copia ampliada (`@4x`). No inventes lo que no puedas leer.

## Recortar e importar

- `read -o salida/ --gifs` deja `<nombre>.sheet.png` (la hoja sin márgenes), una carpeta por fila con sus frames
  (`walk/0.png`…), un GIF por animación y `<nombre>.card.json` (los datos leídos, listos para volver a pasárselos a
  `make`).
- En un motor no hace falta recortar: los frames empiezan en 0,0.
  - Unity: Grid By Cell Size, offset 0.
  - Godot: «Añadir frames desde hoja», sin offset.
  - Tiled: margin 0, spacing 0.

## Generar un sprite pattern

1. **Hoja limpia**: frames del mismo tamaño en rejilla desde `(0, 0)`, fondo transparente, una fila por animación, con
   los frames seguidos desde la izquierda.
2. **Datos** para la herramienta, en un JSON (parte de `templates/card.template.json`). Ese JSON es solo la manera
   de pasarle los datos: el formato es la imagen, y no hay que entregarlo con ella.

   ```json
   { "name": "Caballero azul", "kind": "character", "view": "side", "facing": "right",
     "description": "Caballero con armadura azul, espada y escudo",
     "frame": { "w": 32, "h": 32 },
     "rows": [ { "name": "idle", "ms": 400, "loop": "loop" },
               { "name": "attack", "ms": [80, 120, 90, 160], "loop": "once" },
               { "name": "items" } ] }
   ```

   Una entrada por fila, en orden. `ms`: un número (todos los frames igual) o una lista (uno por frame). Sin `ms`,
   imágenes sueltas. Nombres de fila en minúsculas: `[a-z0-9_-]`. `kind`, `view`, `facing` y `description` son
   opcionales, pero ponlos siempre que los sepas: es lo que le dice a otra IA qué está importando.
3. `make hoja.png datos.json -o <nombre>.spritevpg.png --preview 4`. Enseña la copia `@4x`.

## Las seis vistas

| `view` | Qué se ve | Frase para el prompt de un modelo de imagen |
| --- | --- | --- |
| `side` | De lado, a la altura de los ojos | side view: seen straight from the side at eye level, the top is not visible |
| `front` | De frente, a la altura de los ojos | front view: seen straight from the front at eye level, the top is not visible |
| `three-quarter` | Desde arriba a 45°: techo y fachada (RPG de 16 bits) | three-quarter top-down view (3/4 overhead, like a classic 16-bit RPG): seen from above at about 45 degrees, showing the top and the front face, with the top taking about a third of the height |
| `near-top-down` | Casi desde encima: techo y una franja de fachada (gestión de colonias) | near top-down view (like a colony management game): seen from almost directly above, mostly the top is visible plus a thin strip of the front face at the bottom |
| `top-down` | Desde arriba del todo | top-down view: seen from directly above, only roofs, tree crowns and tops are visible; walls, trunks and front faces are not visible at all |
| `isometric` | En diagonal, proyección 2:1 | isometric view: 2:1 pixel art isometric projection, the top is a diamond and two side faces are visible |

## Ampliar un patrón (otra animación con el mismo estilo)

1. `read` el patrón: hoja limpia, frames y datos.
2. Genera los frames nuevos **forzando la vista de `view`** y la dirección de `facing`. Con un modelo de imagen:
   pásale un frame existente ampliado (a escala entera) como referencia en la primera celda de una plantilla, fondo
   magenta `#FF00FF`, y un prompt como: «Pixel art sprite sheet of the same character as in the first cell:
   <animación>. Draw every frame in <frase de la vista>, facing <facing>. Use exactly this same camera angle in every
   frame. Same size, proportions, colors and outline in every frame; one frame per cell. Background solid magenta
   #FF00FF.»
3. Reduce a la resolución nativa, quita el magenta y recorta cada frame a `fw × fh`.
4. Añade una fila a la hoja limpia y una entrada a `rows`, y `make`.

## Reglas

- Nada dentro de la zona de frames salvo frames.
- PNG siempre; nunca JPEG. Ampliar solo a escala entera y sin suavizado.
- El formato 1.0 solo lleva esto. Apoyo, cajas de colisión, eventos y estilo no forman parte: si hacen falta,
  pregúntalos; no los inventes.
