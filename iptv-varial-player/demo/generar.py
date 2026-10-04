"""Genera la lista de demostración de IPTV Varial Player (para la revisión
de las tiendas y para probar la app): una lista M3U con emisiones de prueba
públicas (de Unified Streaming, Apple, Mux y Google Shaka; las películas
son las abiertas de la Blender Foundation) y una guía XMLTV de un año para
los canales en directo.

Uso: python3 generar.py
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

DIR = Path(__file__).resolve().parent
BASE = 'https://varialgate.github.io/iptv-varial-player/demo'

USP = 'https://demo.unified-streaming.com/k8s'
APPLE = 'https://devstreaming-cdn.apple.com/videos/streaming/examples'
SHAKA = 'https://storage.googleapis.com/shaka-demo-assets'

# (tvg-id, nombre, URL, programas que se alternan en la guía)
LIVE = [
    ('demo1', 'Demo Directo 1', f'{USP}/live/stable/live.isml/.m3u8',
     ['Emisión de prueba', 'Señal continua', 'Directo de demostración']),
    ('demo2', 'Demo Directo 2', f'{USP}/live/stable/scte35.isml/.m3u8',
     ['Emisión con cortes', 'Señal continua', 'Directo de demostración']),
]

# (nombre, URL, duración en segundos)
MOVIES = [
    ('Big Buck Bunny (2008)', 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8', 635),
    ('Tears of Steel (2012)',
     f'{USP}/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8', 734),
    ('Angel One (varios idiomas)', f'{SHAKA}/angel-one-hls/hls.m3u8', 60),
]

SERIES = [
    ('Pruebas de vídeo S01E01', f'{APPLE}/bipbop_16x9/bipbop_16x9_variant.m3u8', 1800),
    ('Pruebas de vídeo S01E02', f'{APPLE}/img_bipbop_adv_example_fmp4/master.m3u8', 600),
    ('Pruebas de vídeo S01E03', f'{SHAKA}/apple-advanced-stream-ts/master.m3u8', 600),
]


def playlist():
    lines = [f'#EXTM3U url-tvg="{BASE}/guia.xml"']
    for tvg, name, url, _ in LIVE:
        lines += [f'#EXTINF:-1 tvg-id="{tvg}" tvg-name="{name}" '
                  f'group-title="Directo de demostración",{name}', url]
    for name, url, secs in MOVIES:
        lines += [f'#EXTINF:{secs} group-title="Películas de demostración",{name}', url]
    for name, url, secs in SERIES:
        lines += [f'#EXTINF:{secs} group-title="Series de demostración",{name}', url]
    (DIR / 'lista.m3u').write_text('\n'.join(lines) + '\n')


def guide():
    start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    fmt = '%Y%m%d%H%M%S +0000'
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<tv generator-info-name="IPTV Varial Player demo">']
    for tvg, name, _, _ in LIVE:
        xml.append(f'  <channel id="{tvg}"><display-name>{escape(name)}'
                   '</display-name></channel>')
    for tvg, name, _, shows in LIVE:
        t = start
        for i in range(366 * 12):
            end = t + timedelta(hours=2)
            title = shows[i % len(shows)]
            xml.append(f'  <programme start="{t.strftime(fmt)}" stop="{end.strftime(fmt)}" '
                       f'channel="{tvg}"><title lang="es">{escape(title)}</title>'
                       f'<desc lang="es">Programa de demostración de {escape(name)}.</desc>'
                       '</programme>')
            t = end
    xml.append('</tv>')
    (DIR / 'guia.xml').write_text('\n'.join(xml) + '\n')


if __name__ == '__main__':
    playlist()
    guide()
