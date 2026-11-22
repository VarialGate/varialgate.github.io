---
name: spritevpg
description: Entender, procesar, validar, generar y ampliar sprite patterns SpriteVPG (Sprite Varial Pixel Gen) — hojas de sprites PNG con los frames limpios desde la esquina de arriba a la izquierda y la información (rótulos, cajas de colisión, animaciones, instrucciones y un QR con la ficha JSON) en los márgenes de la derecha y de abajo. Úsalo cuando aparezca un fichero *.spritevpg.png, una hoja de sprites con rótulos en los márgenes o un QR «FICHA», o cuando se pida crear, leer, importar en un motor, recortar, animar o añadir animaciones o direcciones a una hoja de sprites de un personaje, objeto o construcción en este formato.
---

# SpriteVPG: sprite patterns

Un **sprite pattern** es un PNG que lleva dibujada toda su información, como un patrón de costura:

- **Zona de frames**: desde `(0, 0)`, rejilla pura de `columnas × filas` celdas de `fw × fh`, sin margen ni
  separación, fondo transparente. Frame `i` = `fila·columnas + columna`, desde 0.
- **Márgenes** (papel `#F2EEE3`, fuente de píxeles SpriteVPG 5×7):
  - a la derecha de cada fila, su rótulo (`WALK DER` / `F6-11 BUCLE` / `110MS`);
  - debajo, los números de columna y unas muescas rojas que marcan el apoyo;
  - luego la cabecera (`SPRITEVPG 1.0 · NOMBRE`, tipo y vista, `FRAME 32×32 · 6×3 · DESDE 0,0`, paleta, regla de 32 px);
  - y el pie: detalle con cajas y puntos, animaciones, estilo, instrucciones `IA:`, licencia y el QR `FICHA`.
- **Ficha**: JSON con todo (entidad, arte, frames, apoyo, cajas, puntos, direcciones, animaciones, estados, mundo,
  estilo, instrucciones, procedencia). Va en el QR (`SVPG1:` + Base45 de zlib del JSON) y, como copia, en el bloque
  PNG iTXt `spritevpg`. Si discrepan, manda el QR.

Especificación: https://varialgate.github.io/specs/spritevpg/spec.html · Campos: `reference.md` (en este skill).

## Herramienta

`scripts/spritevpg.py` (Python 3, Pillow y qrcode; para leer el QR, opencv-python o pyzbar):

```bash
pip install pillow qrcode opencv-python-headless      # si faltan
python3 scripts/spritevpg.py info     patron.png       # resumen legible de la ficha
python3 scripts/spritevpg.py validate patron.png       # o ficha.json
python3 scripts/spritevpg.py read     patron.png -o salida/ --gifs   # hoja limpia, frames, ficha, GIFs
python3 scripts/spritevpg.py make     hoja.png ficha.json -o entidad.spritevpg.png --preview 4
```

`read` acepta también copias ampliadas a escala entera (detecta la escala con `image.w` de la ficha) y PNG sin
metadatos (lee el QR).

## Entender un sprite pattern

1. Con herramienta: `info`. Explica al usuario qué es la entidad, las animaciones (frames, duración, bucle, siguiente,
   eventos), las direcciones volteadas, los estados, el apoyo y las cajas, y lo que diga `ai.summary` y `ai.howTo`.
2. Sin herramienta (solo ves la imagen): lee la cabecera. La línea `FRAME fw×fh · C×R · DESDE 0,0` basta para
   cortar. Los rótulos de la derecha dicen qué animación empieza en cada fila, y el pie, los detalles. Si la letra
   se ve borrosa, pide la copia ampliada (`@4x`). Para datos exactos (milisegundos, cajas) di que conviene leer el
   QR con la herramienta: no los inventes.

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
   dirección** (o por grupo de estados). El rótulo de cada fila sale de la animación que empieza en ella.
2. **Ficha** sin `image` ni `frames` (se calculan); parte de `templates/card.template.json`. Obligatorio:
   - `entity` (`kind`, `name`), `art` (`view`, `facing`) y `grid`;
   - `defaults.pivot`;
   - `animations`, con `ms` en **cada** frame;
   - `ai.summary` y `provenance`.
   Recomendado: `style` con `reference.frame`, cajas `collision` y `hurt`, eventos (`footstep`, `hit`).
3. `make hoja.png ficha.json -o <nombre>.spritevpg.png --preview 4` y después `validate`. Enseña la copia `@4x`.

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
- `framesArea` empieza en 0,0; `margin` y `spacing` son 0.
- Una hoja = una entidad. El par `name` + `direction` no se repite.
- No inventes datos que no estén en la ficha. Si falta algo (cajas, eventos), dilo o pregúntalo.
