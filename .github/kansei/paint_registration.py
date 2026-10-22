"""Export one whole painting in the original ultrasound coordinate system.

This performs only one global rectangular registration. It does not locally
warp tissue, change clinical pixels, or relocate findings to fit a painting.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import subprocess
from PIL import Image, ImageStat


def register(painting_path, output_path, archive_path, canvas, source_bounds,
             target_bounds, qa_dir, transparent=False):
    painting = Path(painting_path).resolve()
    output = Path(output_path).resolve()
    archive = Path(archive_path).resolve()
    qa = Path(qa_dir).resolve()
    width, height = map(int, canvas)
    sl, st, sr, sb = map(float, source_bounds)
    left, top, right, bottom = map(float, target_bounds)
    if not (sr > sl and sb > st and 0 <= left < right <= width
            and 0 <= top < bottom <= height):
        raise ValueError('Invalid registration bounds')
    for folder in (output.parent, archive.parent, qa):
        folder.mkdir(parents=True, exist_ok=True)
    with Image.open(painting) as im:
        pw, ph = im.size
    # PNG embedding is intentional: Inkscape cannot reliably decode WebP data URLs.
    embedded = qa / (output.stem + '.source.png')
    subprocess.run(['convert', str(painting), str(embedded)], check=True)
    # Validate the archive as well as the public export. Some ImageMagick
    # encodes returned success with an empty WebP for these large paintings.
    with Image.open(painting) as image:
        image.load()
        image.save(archive, format='WEBP', quality=96, method=6)
    with Image.open(archive) as image:
        image.load()
        if image.size != (pw, ph):
            raise ValueError('Wrong archived painting canvas')
    data = base64.b64encode(embedded.read_bytes()).decode()
    clip = (f'<defs><clipPath id="scan"><rect x="{left}" y="{top}" '
            f'width="{right-left}" height="{bottom-top}"/></clipPath></defs>')
    placed = (f'<svg x="{left}" y="{top}" width="{right-left}" height="{bottom-top}" '
              f'viewBox="{sl} {st} {sr-sl} {sb-st}" preserveAspectRatio="none">'
              f'<image xlink:href="data:image/png;base64,{data}" x="0" y="0" '
              f'width="{pw}" height="{ph}"/></svg>')
    background = '' if transparent else f'<rect width="{width}" height="{height}" fill="black"/>'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" '
           f'height="{height}" viewBox="0 0 {width} {height}">'
           f'{background}'
           f'{clip}<g clip-path="url(#scan)">{placed}</g></svg>')
    svg_path = qa / (output.stem + '.svg')
    png_path = qa / (output.stem + '.png')
    svg_path.write_text(svg)
    subprocess.run(['inkscape', '--batch-process', str(svg_path), '--export-type=png',
                    '--export-filename=' + str(png_path)], check=True, capture_output=True)
    subprocess.run(['convert', str(png_path), '-quality', '94', str(output)], check=True)
    with Image.open(output) as im:
        im.load()
        if im.size != (width, height):
            raise ValueError('Wrong exported canvas')
        if max(ImageStat.Stat(im.convert('RGB')).stddev) < 8:
            raise ValueError('Empty exported painting')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    return {'source_image': painting.name, 'source_size': [pw, ph],
            'source_bounds': list(source_bounds), 'target_bounds': list(target_bounds),
            'canvas': [width, height], 'archive': str(archive),
            'archive_sha256': sha(archive), 'asset': str(output),
            'asset_sha256': sha(output), 'qa_png': str(png_path),
            'method': 'One global rectangular registration, clipped to original scan; no local warp.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--painting', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--archive', required=True)
    parser.add_argument('--canvas', type=int, nargs=2, required=True)
    parser.add_argument('--source-bounds', type=float, nargs=4, required=True)
    parser.add_argument('--target-bounds', type=float, nargs=4, required=True)
    parser.add_argument('--qa-dir', required=True)
    args = parser.parse_args()
    print(json.dumps(register(args.painting, args.output, args.archive, args.canvas,
                              args.source_bounds, args.target_bounds, args.qa_dir)))
