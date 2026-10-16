"""Place continuous paintings on the original ultrasound canvas.

One global transform per painting; no internal warping or tiled materials.
Clinical scans are read only for internal review composites.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'bilder/ultraljud/bursit-axel'
ART = ROOT / '.github/kansei/artwork/bursa'
VERSION = '20261016e'


def data_uri(path):
    # This Inkscape build cannot decode embedded WebP; lossless PNG transport
    # changes only the file format, never the tissue painting.
    if path.suffix == '.webp':
        mime = 'image/png'
        content = subprocess.check_output(['convert', str(path), 'png:-'])
    else:
        mime, content = 'image/jpeg', path.read_bytes()
    return 'data:' + mime + ';base64,' + base64.b64encode(content).decode()


def build(key, view, preview):
    source = ART / view['painting']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == view['painting_sha256']
    width, height = view['source_size']
    left, top, right, bottom = view['source_scan_bounds']
    x1, y1, x2, y2 = view['target_scan_bounds']
    sx, sy = (x2-x1)/(right-left), (y2-y1)/(bottom-top)
    tx, ty = x1-left*sx, y1-top*sy
    painting = (f'<image xlink:href="{data_uri(source)}" width="{width}" height="{height}" '
                f'transform="matrix({sx:.10f} 0 0 {sy:.10f} {tx:.10f} {ty:.10f})"/>')
    doc = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1280" height="960" viewBox="0 0 1280 960">
<title>Axel – anatomisk illustration</title>
<desc>Sammanhängande pedagogisk målning utifrån undersökarens bildbeskrivning. Originalultraljudet är underlaget för bildbedömningen.</desc>
<defs>
<clipPath id="scan"><path d="{view['scan']}"/></clipPath>
<linearGradient id="depth" x1="0" y1="780" x2="0" y2="835" gradientUnits="userSpaceOnUse"><stop stop-color="black" stop-opacity="0"/><stop offset="1" stop-color="black"/></linearGradient>
<mask id="machine-labels" maskUnits="userSpaceOnUse" x="0" y="0" width="1280" height="960"><rect width="1280" height="960" fill="white"/><rect x="1136" y="165" width="77" height="245" fill="black"/></mask>
</defs>
<g clip-path="url(#scan)" mask="url(#machine-labels)"><rect width="1280" height="960" fill="black"/>{painting}<rect y="780" width="1280" height="55" fill="url(#depth)"/></g>
</svg>'''
    vector = preview / (key + '-anatomy-source.svg')
    vector.write_text(doc)
    png = preview / (key + '-anatomy-source.png')
    subprocess.run(['inkscape', '--batch-process', str(vector), '--export-type=png', '--export-filename='+str(png)], check=True, capture_output=True)
    output = OUT / (key + '.anatomi.' + VERSION + '.webp')
    subprocess.run(['convert', str(png), '-quality', '94', str(output)], check=True, capture_output=True)
    base = f'<image xlink:href="{data_uri(OUT/(key+".original.jpg"))}" width="1280" height="960"/>'
    composite = doc.replace('<g clip-path="url(#scan)"', base+'<g clip-path="url(#scan)"', 1)
    review = preview / (key+'-preview.svg')
    review.write_text(composite)
    subprocess.run(['inkscape', '--batch-process', str(review), '--export-type=png', '--export-filename='+str(preview/(key+'-preview.png'))], check=True, capture_output=True)
    return {'view': key, 'asset': str(output.relative_to(ROOT)), 'painting_sha256': view['painting_sha256'], 'global_placement': [sx, 0, 0, sy, tx, ty], 'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', type=Path, required=True)
    args = parser.parse_args()
    args.preview.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ART/('whole-paintings.'+VERSION+'.json')).read_text())
    rows = [build(key, view, args.preview) for key, view in manifest['views'].items()]
    (ART/('registration-report.'+VERSION+'.json')).write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(rows, ensure_ascii=False))
