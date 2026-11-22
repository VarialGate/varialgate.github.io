---
name: spritevpg
description: Entender, procesar, validar, generar y ampliar sprite patterns SpriteVPG (Sprite Varial Pixel Gen) — hojas de sprites PNG con los frames limpios desde la esquina de arriba a la izquierda y la ficha completa (entidad, rejilla, arte, cajas de colisión, animaciones, estilo, instrucciones) escrita debajo en zonas recuadradas con título (ENTITY, SHEET, ART, BODY, ANIMATIONS…) y una barra final «SPRITEVPG 1.0 … HTTPS://VARIALGATE.GITHUB.IO/SPECS/SPRITEVPG/». Úsalo cuando aparezca un fichero *.spritevpg.png o una hoja de sprites con ese aspecto, o cuando se pida crear, leer, importar en un motor, recortar, animar o añadir animaciones o direcciones a una hoja de sprites de un personaje, objeto o construcción en este formato.
---

# SpriteVPG: sprite patterns

Un **sprite pattern** es un PNG que lleva dibujada toda su información, como un patrón de costura:

- **Zona de frames**: desde `(0, 0)`, rejilla pura de `columnas × filas` celdas de `fw × fh`, sin margen ni
  separación, fondo transparente. Frame `i` = `fila·columnas + columna`, desde 0. Una línea de tinta la bordea por
  fuera; unas muescas rosas marcan el apoyo de cada fila y columna.
- **Márgenes** (papel `#F3EEDD`, tinta `#1F2A44`): todo el texto va en una **rejilla de celdas de 4×7 px** con la
  fuente SpriteVPG 3×5 (mayúsculas). Debajo de los frames, la ficha en **zonas** con barra de título en negativo:
  `ENTITY`, `SHEET`, `ART`, `BODY`, `DETAIL` (dibujo con las cajas), `ANIMATIONS`, `DIRECTIONS`, `STATES`, `WORLD`,
  `STYLE`, `AI`, `PROVENANCE`.
- **Notación**: en cada zona, líneas `CLAVE valor`; una fila sangrada continúa la anterior.
- **Barra final**: `SPRITEVPG 1.0` y el enlace a la especificación.
- No hay QR. La ficha es lo que está escrito; un programa lo lee de forma exacta comparando cada celda con la tabla
  de la fuente. El PNG puede llevar además una copia en JSON (bloque iTXt `spritevpg`), opcional.

Especificación: https://varialgate.github.io/specs/spritevpg/spec.html · Notación y campos: `reference.md`.

## Herramienta

`scripts/spritevpg.py` (Python 3; solo necesita Pillow):

```bash
pip install pillow                                     # si falta
python3 scripts/spritevpg.py info     patron.png       # resumen legible
python3 scripts/spritevpg.py text     patron.png       # la notación, tal como está escrita en la imagen
python3 scripts/spritevpg.py validate patron.png       # o ficha.json
python3 scripts/spritevpg.py read     patron.png -o salida/ --gifs   # hoja limpia, frames, ficha JSON, GIFs
python3 scripts/spritevpg.py make     hoja.png ficha.json -o entidad.spritevpg.png --preview 4
```

`read`, `info`, `text` y `validate` leen el dibujo: funcionan con PNG sin metadatos y con copias ampliadas a escala
entera (detectan la escala con la barra final). No funcionan con JPEG ni con imágenes reescaladas con suavizado.

## Entender un sprite pattern

1. Con herramienta: `info` (o `text` para verlo todo). Explica qué es la entidad, las animaciones (frames, duración,
   bucle, siguiente, eventos), las direcciones volteadas, los estados, el apoyo y las cajas, y lo que digan
   `AI SUMMARY` y `AI HOWTO`.
2. Sin herramienta (solo ves la imagen): lee las zonas como texto.
   - `SHEET` basta para cortar: `FRAME 32X32`, `GRID 6X3` (columnas × filas), `FRAMES 0-1 6-15` (los que tienen
     dibujo).
   - `ANIMATIONS`: `ATTACK RIGHT ONCE > IDLE F12 80 F13 120 … F14 90 HIT BOX HIT 20,4 11X22`: nombre, dirección,
     bucle, siguiente y, por frame, milisegundos, eventos y cajas o puntos propios. `F6-11 110`: seis frames a 110 ms.
   - Si la letra se ve pequeña o borrosa, pide la copia ampliada (`@4x`). No inventes datos que no puedas leer.

## Procesar (importar, recortar, convertir)

- `read -o salida/ --gifs` deja `<nombre>.sheet.png` (hoja limpia, sin márgenes), `frames/NNN.png`,
  `<nombre>.spritevpg.json` y un GIF por animación.
- En un motor no hace falta recortar: los frames empiezan en 0,0.
  - Unity: Grid By Cell Size, offset 0.
  - Godot: «Añadir frames desde hoja», sin offset.
  - Tiled: margin 0, spacing 0.
  - Código propio: `x = (i % C)·fw`, `y = (i // C)·fh`.
- Para convertir a otro formato (Aseprite JSON, Godot `SpriteFrames`, Unity), sigue la ficha:
  - las duraciones son `ms` por frame;
  - `loop`: `loop`, `once` (sigue `next`), `pingpong` o `hold`;
  - las direcciones de `directions.mirror` se sacan volteando y no tienen frames propios;
  - apoyo, cajas y puntos de un frame: lo del frame en la animación, si no lo de `frames[]`, si no `defaults`.

## Generar un sprite pattern

1. **Hoja limpia**: frames del mismo tamaño en rejilla desde `(0, 0)`, fondo transparente, **una fila por animación y
   dirección** (o por grupo de estados).
2. **Ficha** en JSON, sin `image` ni `frames` (se calculan); parte de `templates/card.template.json`. Obligatorio:
   - `entity` (`kind`, `name`), `art.view` y `grid`;
   - `defaults.pivot`;
   - `animations`, con `ms` en **cada** frame;
   - `ai.summary` y `provenance`.
   Recomendado: `style` con `reference.frame`, cajas `collision` y `hurt`, eventos (`footstep`, `hit`).
3. `make hoja.png ficha.json -o <nombre>.spritevpg.png --preview 4` y después `validate`. Enseña la copia `@4x`.

Los identificadores (nombres de entidad, animación, caja, punto, estado, evento) van en minúsculas: `[a-z0-9_:-]`.
El texto libre se dibuja en mayúsculas.

## Ampliar con el mismo estilo (otra animación o dirección)

1. `read` el patrón: tendrás la hoja limpia, los frames y la ficha.
2. Toma la guía: `style.summary`, `style.proportions`, `style.rules`, la paleta de `art.palette` y el frame
   `style.reference.frame`.
3. Genera los frames nuevos.
   - Con un modelo de imagen: pásale el frame de referencia ampliado (a escala entera) en la primera celda de una
     plantilla con tantas celdas como frames, fondo magenta `#FF00FF`, y un prompt como:
     «Pixel art sprite sheet of the same character as in the first cell: <animación>. <style.summary>. Same size,
     proportions, colors and outline in every frame; feet on the bottom edge; one frame per cell. Background solid
     magenta #FF00FF; never use magenta in the character.»
   - Después reduce a la resolución nativa (un píxel del dibujo = un píxel), quita el magenta y recorta cada frame a
     `fw × fh` con el apoyo en el mismo sitio que en los demás frames.
4. Añade una fila nueva a la hoja limpia con esos frames y su animación a `animations` (índices `fila·C + col`, `ms`
   en cada frame, `loop`, `next`, eventos). Sube `grid.rows`.
5. `make` y `validate`. Comprueba en la copia ampliada que encaja con los demás frames.

## Reglas que no se rompen

- Nada dentro de la zona de frames salvo frames; nunca texto ni marcas.
- PNG siempre; nunca JPEG. Ampliar solo a escala entera y sin suavizado.
- Los frames empiezan en 0,0, sin margen ni separación.
- Una hoja = una entidad. El par `name` + `direction` no se repite.
- No inventes datos que no estén en la ficha. Si falta algo (cajas, eventos), dilo o pregúntalo.
