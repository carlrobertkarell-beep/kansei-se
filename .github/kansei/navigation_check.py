#!/usr/bin/env python3
"""Keep public navigation readable without decorative direction arrows."""
from pathlib import Path
from html.parser import HTMLParser
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
ARROWS = set('←→↑↓↗↘↙↖⇐⇒⇑⇓↔↕➜➝➞➔⟶⟵⌃⌄‹›❯❮')
STYLESHEET = '/assets/navigation.20261027.css'
VOID_ELEMENTS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                 'link', 'meta', 'param', 'source', 'track', 'wbr'}

class Navigation(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.excluded = []
        self.errors = []
        self.has_body = False
        self.redirect = False
        self.stylesheet_count = 0
        self.clinic_page = False
        self.elements = []
        self.stack = []
        self.anchors = []
        self.desktop_navs = []
        self.primary_menus = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        element = {'tag': tag, 'attrs': attrs, 'text': [],
                   'parent': self.stack[-1] if self.stack else None,
                   'index': len(self.elements)}
        self.elements.append(element)
        if tag == 'a':
            self.anchors.append(element)
        if tag == 'nav' and 'desktop-nav' in attrs.get('class', '').split():
            self.desktop_navs.append(element)
        if tag == 'nav' and 'menu-primary' in attrs.get('class', '').split():
            self.primary_menus.append(element)
        if tag not in VOID_ELEMENTS:
            self.stack.append(element)
        if tag in ('script', 'style', 'symbol', 'defs'):
            self.excluded.append(tag)
        if tag == 'body':
            self.has_body = True
            self.clinic_page = 'clinic-site' in attrs.get('class', '').split()
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
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]['tag'] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        for element in self.stack:
            if element['tag'] == 'a':
                element['text'].append(data)
        if not self.excluded and ARROWS.intersection(data):
            self.errors.append('visible arrow remains in ' + ' '.join(data.split())[:90])

    def check_actions(self):
        """Catch duplicated actions within one group, not across menu/footer routes."""
        if not self.clinic_page or self.redirect:
            return
        groups = defaultdict(list)
        for anchor in self.anchors:
            label = ' '.join(' '.join(anchor['text']).split())
            href = anchor['attrs'].get('href', '')
            parent = anchor['parent']
            if label and href and parent:
                groups[(parent['index'], href, label)].append(anchor)
        for (_, href, label), anchors in groups.items():
            if len(anchors) > 1:
                self.errors.append(f'duplicate sibling action {label!r} to {href}')
        for nav in self.desktop_navs + self.primary_menus:
            links = []
            for anchor in self.anchors:
                parent = anchor['parent']
                while parent and parent is not nav:
                    parent = parent['parent']
                if parent is nav:
                    links.append(anchor['attrs'].get('href'))
            if sum(links.count(route) for route in ('/injektioner/', '/hyaluronsyra/')) != 1:
                name = 'desktop navigation' if nav in self.desktop_navs else 'primary menu'
                self.errors.append(name + ' needs one injection route')

def main():
    errors = []
    count = 0
    for path in sorted(ROOT.rglob('*.html')):
        if any(part in ('.git', 'node_modules', 'docs', '.openai') for part in path.parts):
            continue
        parser = Navigation(path)
        parser.feed(path.read_text())
        parser.check_actions()
        if parser.has_body and not parser.redirect and parser.stylesheet_count != 1:
            parser.errors.append('expected exactly one shared navigation stylesheet')
        errors.extend(f'{path.relative_to(ROOT)}: {message}' for message in parser.errors)
        count += 1

    # The dynamic components use text labels too, including on the mobile reader.
    for filename in ('assets/clinic.20261031.js', 'assets/guide.20261019.js',
                     'assets/analytics.20261101.js', 'assets/reading-sections.20261017.js',
                     'reda-2/ui.js', 'config.js'):
        source = (ROOT / filename).read_text()
        if ARROWS.intersection(source):
            errors.append(filename + ': dynamic arrow ornament remains')

    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Navigation, distinct action groups and injection routes verified on {count} HTML files and six dynamic components.')


if __name__ == "__main__":
    main()
