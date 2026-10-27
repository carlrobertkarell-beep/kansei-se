#!/usr/bin/env python3
"""Keep public navigation readable without decorative direction arrows."""
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[2]
ARROWS = set('←→↑↓↗↘↙↖⇐⇒⇑⇓↔↕➜➝➞➔⟶⟵⌃⌄‹›❯❮')
STYLESHEET = '/assets/navigation.20261027.css'

class Navigation(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.excluded = []
        self.errors = []
        self.has_body = False
        self.redirect = False
        self.stylesheet_count = 0

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag in ('script', 'style', 'symbol', 'defs'):
            self.excluded.append(tag)
        if tag == 'body':
            self.has_body = True
        if tag == 'meta' and attrs.get('http-equiv', '').lower() == 'refresh':
            self.redirect = True
        if tag == 'link' and attrs.get('href', '') == STYLESHEET:
            self.stylesheet_count += 1
        if tag == 'use' and not self.excluded:
            href = attrs.get('href', attrs.get('xlink:href', ''))
            if href in ('#i-arrow', '#i-up', '#i-down', '#i-left', '#i-right'):
                self.errors.append('decorative SVG arrow remains')

    def handle_endtag(self, tag):
        if tag in self.excluded:
            self.excluded.remove(tag)

    def handle_data(self, data):
        if not self.excluded and ARROWS.intersection(data):
            self.errors.append('visible arrow remains in ' + ' '.join(data.split())[:90])

errors = []
count = 0
for path in sorted(ROOT.rglob('*.html')):
    if any(part in ('.git', 'node_modules', 'docs', '.openai') for part in path.parts):
        continue
    parser = Navigation(path)
    parser.feed(path.read_text())
    if parser.has_body and not parser.redirect and parser.stylesheet_count != 1:
        parser.errors.append('expected exactly one shared navigation stylesheet')
    errors.extend(f'{path.relative_to(ROOT)}: {message}' for message in parser.errors)
    count += 1

# The dynamic components use text labels too, including on the mobile reader.
for filename in ('assets/clinic.20261008.js', 'assets/guide.20261019.js',
                 'assets/analytics.20261017.js', 'assets/reading-sections.20261017.js',
                 'reda-2/ui.js', 'config.js'):
    source = (ROOT / filename).read_text()
    if ARROWS.intersection(source):
        errors.append(filename + ': dynamic arrow ornament remains')

if errors:
    raise SystemExit('\n'.join(errors))
print(f'Navigation verified on {count} HTML files and six dynamic components.')
