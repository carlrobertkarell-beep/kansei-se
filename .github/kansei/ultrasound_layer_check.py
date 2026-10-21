"""Check the audited ultrasound layers without a browser or external services.

Requires Pillow. Run from any directory:
  python .github/kansei/ultrasound_layer_check.py --base HEAD --output /tmp/layers.json

The git revision is the reference for immutable clinical image bytes. This check
does not establish clinical accuracy or pixel-perfect illustration registration.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
CASES = (
    'ultraljud/axel/bicepstendinopati',
    'ultraljud/axel/pectoralisruptur',
    'ultraljud/hand-handled/karpaltunnelsyndrom',
    'ultraljud/axel/ac-ledsskada',
    'ultraljud/kalkaxel',
    'ultraljud/bursit-axel',
    'ultraljud/kna',
    'ultraljud/loparkna',
    'ultraljud/hoftled/bilder',
    'ultraljud/glutealsenor/bilder',
    'ultraljud/halsena/bilder',
    'ultraljud/tennisarmbage/bilder',
)
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}
ANATOMY = {'patient-overlay', 'anatomy-layer', 'knee-anatomy'}
GEOMETRY = {
    'path': ('d',),
    'circle': ('cx', 'cy', 'r'),
    'ellipse': ('cx', 'cy', 'rx', 'ry'),
    'line': ('x1', 'y1', 'x2', 'y2'),
    'polygon': ('points',),
    'polyline': ('points',),
    'rect': ('x', 'y', 'width', 'height', 'rx', 'ry'),
    'image': ('href', 'xlink:href', 'x', 'y', 'width', 'height'),
}


class Node:
    def __init__(self, tag, attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []

    @property
    def classes(self):
        return set(self.attrs.get('class', '').split())

    def walk(self):
        for child in self.children:
            yield child
            yield from child.walk()

    def ancestors(self):
        node = self.parent
        while node:
            yield node
            node = node.parent


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.root = Node('document')
        self.current = self.root
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in VOID:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        node = self.current
        while node is not self.root:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent


def local_source(node):
    source = node.attrs.get('src', node.attrs.get('href', node.attrs.get('xlink:href', '')))
    parsed = urlsplit(source)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith('/'):
        raise AssertionError('Expected a local clinical/anatomy asset: ' + source)
    return parsed.path.lstrip('/')


def geometry(layer):
    """Compare source coordinates, including ancestor transforms, not CSS style."""
    result = []
    for node in layer.walk():
        if node.tag not in GEOMETRY:
            continue
        transforms = []
        current = node
        while current is not layer.parent:
            if current.attrs.get('transform'):
                transforms.append(current.attrs['transform'])
            current = current.parent
        result.append((node.tag, tuple((k, node.attrs.get(k)) for k in GEOMETRY[node.tag]),
                       tuple(reversed(transforms))))
    return result


def check(base):
    revision = subprocess.check_output(['git', 'rev-parse', base], cwd=ROOT, text=True).strip()
    originals, anatomy, cases = {}, {}, []
    pairs, shared, unavailable = 0, 0, 0
    for case in CASES:
        document = Document((ROOT / case / 'index.html').read_text())
        views = []
        for picture in document.root.walk():
            if not picture.classes.intersection({'patient-picture', 'knee-picture'}):
                continue
            image_sources, painting_sources = [], []
            for node in picture.walk():
                if node.tag not in {'img', 'image'}:
                    continue
                ancestors = list(node.ancestors())
                if any('patient-finding' in a.classes or 'knee-findings' in a.classes for a in ancestors):
                    continue
                target = painting_sources if any(ANATOMY.intersection(a.classes) for a in ancestors) else image_sources
                target.append((local_source(node), node.attrs))
            if not painting_sources:
                continue
            if len(image_sources) != 1 or len(painting_sources) != 1:
                raise AssertionError(f'{case}: expected one original and one painting per static view')
            original, _ = image_sources[0]
            painting, attributes = painting_sources[0]
            if original not in originals:
                data = (ROOT / original).read_bytes()
                reference = subprocess.check_output(['git', 'show', f'{revision}:{original}'], cwd=ROOT)
                sha = hashlib.sha256(data).hexdigest()
                if sha != hashlib.sha256(reference).hexdigest():
                    raise AssertionError('Clinical original bytes changed: ' + original)
                with Image.open(ROOT / original) as image:
                    image.load()
                    original_size = list(image.size)
                originals[original] = {'path': original, 'sha256': sha, 'size': original_size,
                                       'matches_git_reference': True}
            if painting not in anatomy:
                with Image.open(ROOT / painting) as image:
                    image.load()
                    size = list(image.size)
                declared = [int(attributes['width']), int(attributes['height'])]
                if size != declared:
                    raise AssertionError(f'{painting}: native {size} != HTML {declared}')
                anatomy[painting] = {'path': painting, 'size': size,
                                    'sha256': hashlib.sha256((ROOT / painting).read_bytes()).hexdigest()}
            panel = next((n for n in picture.ancestors()
                          if n.classes.intersection({'reader-panel', 'knee-panel'})), None)
            modes = {}
            for node in picture.walk():
                if 'patient-finding' in node.classes and node.attrs.get('data-finding-mode'):
                    mode = node.attrs['data-finding-mode']
                    if mode in modes:
                        raise AssertionError(f'{case}: duplicate finding layer for {mode}')
                    modes[mode] = geometry(node)
            if modes:
                if set(modes) != {'ultrasound', 'anatomy'} or not modes['ultrasound']:
                    raise AssertionError(f'{case}: incomplete paired clinical finding geometry')
                if modes['ultrasound'] != modes['anatomy']:
                    raise AssertionError(f'{case}: clinical finding geometry differs between modes')
                pairs += 1
                finding_layer = 'paired-identical'
            else:
                layers = [n for n in picture.walk() if 'knee-findings' in n.classes]
                explicitly_unavailable = panel and panel.attrs.get('data-findings-available') == 'false'
                if len(layers) != 1 or (not geometry(layers[0]) and not explicitly_unavailable):
                    raise AssertionError(f'{case}: expected one shared clinical finding layer')
                if any(n.classes.intersection({'knee-finding-ultrasound', 'knee-finding-anatomy'})
                       for n in layers[0].walk()):
                    raise AssertionError(f'{case}: stale mode-specific finding group')
                if explicitly_unavailable:
                    if geometry(layers[0]):
                        raise AssertionError(f'{case}: findings present despite being declared unavailable')
                    unavailable += 1
                    finding_layer = 'explicitly-unavailable'
                else:
                    shared += 1
                    finding_layer = 'shared'
            views.append({'id': panel.attrs.get('id') if panel else picture.attrs.get('id'),
                          'original': original, 'anatomy': painting,
                          'finding_layer': finding_layer,
                          'stage_style': picture.attrs.get('style', '')})
        cases.append({'page': case + '/', 'views': views})
    return {'base': revision, 'cases': cases, 'originals': list(originals.values()),
            'anatomy': list(anatomy.values()), 'summary': {
                'case_pages': len(cases), 'static_view_occurrences': sum(len(c['views']) for c in cases),
                'unique_clinical_originals': len(originals), 'unique_anatomy_assets': len(anatomy),
                'paired_identical_findings': pairs, 'shared_finding_layers': shared,
                'explicitly_unavailable_findings': unavailable,
                'clinical_originals_match_git_reference': True,
                'anatomy_decode_and_html_dimensions_match': True}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='HEAD', help='Git revision with the unchanged clinical originals')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = check(args.base)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('PASS: ' + json.dumps(report['summary']))
