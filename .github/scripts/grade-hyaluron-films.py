#!/usr/bin/env python3
"""Render the approved, subtle daylight lift for the two existing clinic films."""
from pathlib import Path
import argparse
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]

# Equal RGB curves keep skin and product colours natural. Anchor black and white
# instead of raising black or clipping highlights. The brighter inserts need less lift.
CURVES = {
    'talk': '0/0 0.06/0.072 0.18/0.218 0.4/0.474 0.7/0.762 0.9/0.935 1/1',
    'products': '0/0 0.06/0.07 0.18/0.214 0.4/0.465 0.7/0.762 0.9/0.937 1/1',
    'model': '0/0 0.18/0.19 0.4/0.42 0.7/0.72 0.9/0.912 1/1',
    'room': '0/0 0.06/0.072 0.18/0.215 0.4/0.46 0.7/0.75 0.9/0.931 1/1',
    'demo': '0/0 0.18/0.192 0.4/0.424 0.7/0.724 0.9/0.916 1/1',
}
FILMS = {
    '1': ('hyaluroninjektion-stockholm', {
        'talk': 'lt(t,2.6)+gte(t,8.8)*lt(t,23.7)+gte(t,29.2)*lt(t,64.1)',
        'products': 'gte(t,2.6)*lt(t,8.8)',
        'model': 'gte(t,23.7)*lt(t,29.2)',
    }),
    '3': ('ultraljudsvagledd-hyaluroninjektion', {
        'talk': 'lt(t,22.633333)+gte(t,28.033333)*lt(t,30.1)+gte(t,37.7)*lt(t,67)',
        'room': 'gte(t,22.633333)*lt(t,28.033333)',
        'demo': 'gte(t,34.4)*lt(t,37.7)',
    }),
}


def render(number):
    stem, intervals = FILMS[number]
    source = ROOT / 'assets/video' / f'{stem}.20261019c.mp4'
    target = ROOT / 'assets/video' / f'{stem}.20261020.mp4'
    filters = [f"curves=all='{CURVES[name]}':enable='{when}'"
               for name, when in intervals.items()]
    # Ultrasound/anatomy and the end cards have no exposure adjustment.
    filters += ['scale=out_color_matrix=bt709:out_range=tv', 'format=yuv420p']
    subprocess.run([
        'ffmpeg', '-v', 'warning', '-y', '-i', str(source),
        '-map', '0:v:0', '-map', '0:a:0', '-vf', ','.join(filters),
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-threads', '4',
        '-c:a', 'copy', '-color_range', 'tv', '-colorspace', 'bt709',
        '-color_trc', 'bt709', '-color_primaries', 'bt709',
        '-movflags', '+faststart', str(target),
    ], check=True)
    print(json.dumps({'path': str(target), 'bytes': target.stat().st_size}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('film', choices=FILMS)
    render(parser.parse_args().film)
