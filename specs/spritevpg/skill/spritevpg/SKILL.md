---
name: spritevpg
description: Entender, recortar, validar, generar y ampliar sprite patterns SpriteVPG (Sprite Varial Pixel Gen) — hojas de sprites PNG con los frames limpios desde la esquina de arriba a la izquierda, una animación por fila con su rótulo a la derecha (nombre, «FRAMES: 6», «MS/FRAME: 110», «PLAY: LOOP»), y debajo dos zonas con barra de título, SHEET (NAME, FRAME, GRID) SUBJECT (KIND, VIEW, FACING, DESC) y, opcionalmente, AGENTS (indicaciones IMPLEMENT y EXTEND para una IA), y una barra final con «SPRITEVPG 1.0» y, debajo, «HTTPS://VARIALGATE.GITHUB.IO/SPECS/SPRITEVPG/». Úsalo cuando aparezca un fichero *.spritevpg.png o una hoja de sprites con ese aspecto, o cuando se pida crear, leer, importar en un motor, recortar, animar o añadir animaciones a una hoja de sprites en este formato.
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
- **`SHEET`**, debajo: `NAME: …`, `FRAME: 32X32 PX`, `GRID: 6 COLUMNS X 3 ROWS`, `ORIGIN: TOP-LEFT 0,0, NO GAPS` y,
  opcionales, `BODY: 21X32 PX AT 5,0` (lo que ocupa el dibujo quieto dentro del frame y dónde empieza) y
  `PIVOT: 15,31` (el punto del frame por el que se coloca en el juego; lo marcan unas muescas rosas en el borde).
  El frame suele ser mayor que el cuerpo, para que quepa la animación que más se sale.
- **`SUBJECT`** (opcional): `KIND:` (character, creature, item, prop, building, effect, tile, ui), `VIEW:` (una de
  las seis vistas de abajo), `FACING:` (right, left, up, down o una diagonal) y `DESC:` (frase breve).
- **`AGENTS`** (opcional): las indicaciones del autor para la IA que trabaje con esta hoja, una por línea, texto
  libre, cada una con su etiqueta:
  - `IMPLEMENT:` qué debe programar quien use la hoja en un juego o una app: volteos, efectos que añade la
    aplicación (sombra, brillo, parpadeo), en qué frame pasa algo;
  - `EXTEND:` qué respetar al ampliarla: estilo, proporciones, lo que no debe cambiar;
  - `NOTE:` cualquier otra cosa.
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
- **Sigue las indicaciones `IMPLEMENT` de la zona `AGENTS`** (las da `info` como «Al usarla en una app»): implementa en el
  código los volteos y los efectos que pidan (sombra, brillo, golpe en tal frame). Si alguna no se puede cumplir en
  ese motor, dilo; no la ignores en silencio.
- Si la hoja lleva `PIVOT`, coloca cada frame por ese punto (no por la esquina de la celda); y si lleva `BODY`, usa
  ese rectángulo, no la celda entera, para lo que ocupa el personaje (colisión, selección).
- En un motor no hace falta recortar: los frames empiezan en 0,0.
  - Unity: Grid By Cell Size, offset 0.
  - Godot: «Añadir frames desde hoja», sin offset.
  - Tiled: margin 0, spacing 0.

## Generar un sprite pattern

1. **Hoja limpia**: frames del mismo tamaño en rejilla desde `(0, 0)`, fondo transparente, una fila por animación, con
   los frames seguidos desde la izquierda. **Un único tamaño de celda** para toda la hoja, el que pida la animación
   que más se sale: si el personaje quieto ocupa 16 px, usa celdas de 24 o 32. Si una animación necesita más sitio,
   agranda todas las celdas, no solo su fila; el cuerpo va en el mismo sitio de la celda en todas las filas (no hace
   falta centrarlo: si el ataque se sale por la derecha, deja el cuerpo a la izquierda). Nunca encojas un frame para
   que quepa. Si una animación es desproporcionada, saca el efecto (espadazo, proyectil) a otra hoja de tipo
   `effect` y dilo en `agents.implement`.
2. **Datos** para la herramienta, en un JSON (parte de `templates/card.template.json`). Ese JSON es solo la manera
   de pasarle los datos: el formato es la imagen, y no hay que entregarlo con ella.

   ```json
   { "name": "Caballero azul", "kind": "character", "view": "side", "facing": "right",
     "description": "Caballero con armadura azul, espada y escudo",
     "agents": { "implement": [ "Para mirar a la izquierda, voltear en horizontal.",
                                "Añadir una sombra elíptica bajo los pies." ],
                 "extend": [ "Contorno oscuro de 1 px, tres tonos de azul, luz arriba a la izquierda." ] },
     "frame": { "w": 32, "h": 32 }, "body": "auto", "pivot": "auto",
     "rows": [ { "name": "idle", "ms": 400, "loop": "loop" },
               { "name": "attack", "ms": [80, 120, 90, 160], "loop": "once" },
               { "name": "items" } ] }
   ```

   Una entrada por fila, en orden. `ms`: un número (todos los frames igual) o una lista (uno por frame). Sin `ms`,
   imágenes sueltas. Nombres de fila en minúsculas: `[a-z0-9_-]`. `kind`, `view`, `facing` y `description` son
   opcionales, pero ponlos siempre que los sepas: es lo que le dice a otra IA qué está importando.
   `body` y `pivot`: con `"auto"` la herramienta mide el primer frame y pone el apoyo en el centro de su base; o dalos
   a mano (`{"x":5,"y":0,"w":21,"h":32}` y `{"x":15,"y":31}`).
   `agents`: lo que tendría que saber otra IA y no está en los datos. En `implement`, lo que debe programar quien
   la use (volteos, efectos que añade la aplicación, en qué frame pasa algo); en `extend`, el estilo (contorno, tonos, luz),
   las proporciones y lo que no debe cambiar. Pocas líneas, concretas. No repitas la vista ni el tamaño.
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
2. Genera los frames nuevos **forzando la vista de `view`** y la dirección de `facing`, y **siguiendo las
   indicaciones `EXTEND` de `AGENTS`** (añádelas al prompt, traducidas al inglés si hace falta). Con un modelo de imagen:
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
- El formato 1.0 solo lleva esto. Cajas de colisión y eventos por frame no forman parte: si hacen falta,
  pregúntalos; no los inventes.
