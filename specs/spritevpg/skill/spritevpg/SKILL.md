---
name: spritevpg
description: Entender, recortar, validar y generar sprite patterns SpriteVPG (Sprite Varial Pixel Gen) — hojas de sprites PNG con los frames limpios desde la esquina de arriba a la izquierda, una animación por fila, un rótulo a la derecha de cada fila (por ejemplo «WALK 110 MS LOOP») y, abajo, el nombre, «FRAME 32X32 · GRID 6X3» y una barra «SPRITEVPG 1.0 · HTTPS://VARIALGATE.GITHUB.IO/SPECS/SPRITEVPG/». Úsalo cuando aparezca un fichero *.spritevpg.png o una hoja de sprites con ese aspecto, o cuando se pida crear, leer, importar en un motor, recortar o animar una hoja de sprites en este formato.
---

# SpriteVPG: sprite patterns

Un **sprite pattern** es una hoja de sprites PNG que dice ella misma cómo se corta y cómo se anima:

- **Frames** desde `(0, 0)`, en rejilla de `columnas × filas` celdas de `fw × fh`, sin margen ni separación, con
  fondo transparente. **Una fila = una animación**; sus frames van seguidos desde la izquierda.
  El frame de la fila `r` y la columna `c` está en `x = c·fw`, `y = r·fh`.
- **Rótulo de cada fila**, a su derecha, en el orden de las filas: `NOMBRE ms… MS LOOP|ONCE`.
  - `WALK 110 MS LOOP`: cada frame dura 110 ms, en bucle.
  - `ATTACK 80 120 90 160 MS ONCE`: una duración por frame, una sola vez.
  - `ITEMS` (solo el nombre): imágenes sueltas, no una animación.
  - Una línea sangrada continúa el rótulo de arriba. El número de frames son las celdas con dibujo de la fila.
- **Pie**: `NOMBRE · FRAME fwXfh · GRID columnasXfilas` y, debajo, la barra en negativo
  `SPRITEVPG 1.0 · HTTPS://VARIALGATE.GITHUB.IO/SPECS/SPRITEVPG/`.
- Texto en mayúsculas con la fuente SpriteVPG 3×5, en celdas de 4×7 px, tinta `#1F2A44` sobre papel `#F3EEDD`.

Especificación: https://varialgate.github.io/specs/spritevpg/spec.html

## Herramienta

`scripts/spritevpg.py` (Python 3; solo necesita Pillow):

```bash
pip install pillow                                     # si falta
python3 scripts/spritevpg.py info     patron.png       # resumen legible
python3 scripts/spritevpg.py validate patron.png       # o ficha.json
python3 scripts/spritevpg.py read     patron.png -o salida/ --gifs
python3 scripts/spritevpg.py make     hoja.png ficha.json -o nombre.spritevpg.png --preview 4
```

Lee la ficha del propio dibujo: funciona con PNG sin metadatos y con copias ampliadas a escala entera. No funciona con
JPEG ni con imágenes reescaladas con suavizado.

## Entender un sprite pattern

- Con herramienta: `info`. Di el tamaño de frame, la rejilla y, por fila, la animación, sus frames, su duración y si
  va en bucle.
- Solo mirando la imagen: lee el pie (`FRAME`, `GRID`) y los rótulos de arriba abajo; el rótulo número `r` es el de
  la fila `r`. Si la letra se ve pequeña o borrosa, pide la copia ampliada (`@4x`). No inventes lo que no puedas leer.

## Recortar e importar

- `read -o salida/ --gifs` deja `<nombre>.sheet.png` (la hoja sin márgenes), una carpeta por fila con sus frames
  (`walk/0.png`…), `<nombre>.spritevpg.json` y un GIF por animación.
- En un motor no hace falta recortar: los frames empiezan en 0,0.
  - Unity: Grid By Cell Size, offset 0.
  - Godot: «Añadir frames desde hoja», sin offset.
  - Tiled: margin 0, spacing 0.
- `ms` es la duración de cada frame; `loop` es `loop` (en bucle) u `once` (una vez, se queda en el último frame).

## Generar un sprite pattern

1. **Hoja limpia**: frames del mismo tamaño en rejilla desde `(0, 0)`, fondo transparente, una fila por animación, con
   los frames seguidos desde la izquierda.
2. **Ficha** (parte de `templates/card.template.json`):

   ```json
   { "name": "Caballero azul", "frame": { "w": 32, "h": 32 },
     "rows": [ { "name": "idle", "ms": 400, "loop": "loop" },
               { "name": "attack", "ms": [80, 120, 90, 160], "loop": "once" },
               { "name": "items" } ] }
   ```

   Una entrada por fila, en orden. `ms`: un número (todos los frames igual) o una lista (uno por frame). Sin `ms`,
   imágenes sueltas. Nombres de fila en minúsculas: `[a-z0-9_-]`.
3. `make hoja.png ficha.json -o <nombre>.spritevpg.png --preview 4`. Enseña la copia `@4x`.

Para añadir una animación a un patrón: `read`, añade una fila a la hoja limpia y una entrada a `rows`, y `make`.

## Reglas

- Nada dentro de la zona de frames salvo frames.
- PNG siempre; nunca JPEG. Ampliar solo a escala entera y sin suavizado.
- El formato 1.0 solo lleva esto. Apoyo, cajas de colisión, eventos, direcciones y estilo no forman parte: si hacen
  falta, pregúntalos; no los inventes.
