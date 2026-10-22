"""Export fixed clinical contours on scans and paintings for visual review.

This is a review aid, not a clinical accuracy test. Each contour is rasterized
once in the native source canvas and reused without relocation on all three
images. Source scans and site assets are never modified.
"""
from pathlib import Path
import argparse
import json
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont
from build_tissue_realism import ROOT, ART, source_findings


def export(spec, folder):
    w, h = spec['size']
    markup = source_findings(spec)
    start = markup.find('<svg')
    markup = markup[start:markup.rfind('</svg>')+6]
    markup = re.sub(r'viewBox="[^"]*"', f'viewBox="0 0 {w} {h}"', markup, count=1)
    markup = markup.replace('<image ', '<image opacity="0" ')
    style = ('<style>path,ellipse,polygon,polyline,line,circle,rect{fill:none!important;'
             'stroke:#ffdc76!important;stroke-width:2!important;opacity:1!important}'
             '.finding-pointer,.finding-pointer-shadow,.pointer,.pointer-shadow{display:none}'
             'text{display:none}</style>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}">{style}{markup}</svg>')
    path = folder / (spec['key']+'.overlay.svg')
    path.write_text(svg)
    overlay_path = path.with_suffix('.png')
    for attempt in range(3):
        subprocess.run(['inkscape', '--batch-process', str(path), '--export-type=png',
                        '--export-filename='+str(overlay_path)], capture_output=True, check=True)
        try:
            overlay = Image.open(overlay_path).convert('RGBA')
            overlay.load()
            break
        except OSError:
            if attempt == 2:
                raise
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
    panels = []
    for name, source in [('original', spec['original']), ('previous', spec['anatomy']),
                         ('current', spec['output'])]:
        image = Image.open(ROOT/source).convert('RGBA')
        image.alpha_composite(overlay)
        image.convert('RGB').save(folder/(spec['key']+'.'+name+'.jpg'), quality=96)
        panels.append(image)
    sheet = Image.new('RGB', (w*3, h+48), '#17252b')
    draw = ImageDraw.Draw(sheet)
    for i, (name, panel) in enumerate(zip(['Original', 'Tidigare anatomi', 'Aktuell anatomi'], panels)):
        sheet.paste(panel.convert('RGB'), (i*w, 48))
        draw.text((i*w+12, 10), name, font=font, fill='white')
    sheet.save(folder/(spec['key']+'.comparison.jpg'), quality=94)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keys', nargs='*')
    p.add_argument('--output', type=Path, required=True)
    args=p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for spec in json.loads((ART/'sources.json').read_text()):
        if not args.keys or any(spec['key'].startswith(k) for k in args.keys):
            export(spec, args.output)
            print(spec['key'], flush=True)
