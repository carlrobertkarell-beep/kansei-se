"""Keep the existing case readers and navigation consistent without editing media.

Run after the content generators. This deliberately preserves every image,
finding, film and clinical paragraph. Changes are idempotent.
"""
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
SHARED_CSS = '/assets/patient-case.20261009d.css'
VIEWERS = ('data-patient-viewer', 'data-knee-viewer', 'data-elbow-viewer', 'data-achilles-viewer')
LABELS = {
    '#patientfall': 'Patientfallet',
    '#bilder': 'Bilder och fynd',
    '#behandlingen': 'Behandlingen',
    '#behandling': 'Behandlingen',
    '#nasta-steg': 'Bedömning och nästa steg',
    '#faq': 'Frågor och svar',
}
REGIONS = {
    'axel': ('axel', 'axeln'),
    'bursit-axel': ('axel', 'axeln'),
    'kalkaxel': ('axel', 'axeln'),
    'hand-handled': ('hand', 'hand och handled'),
    'tennisarmbage': ('armbage', 'armbågen'),
    'kna': ('kna', 'knät'),
    'loparkna': ('kna', 'knät'),
    'halsena': ('fot', 'fot och fotled'),
    'hoftled': ('hoft', 'höft och säte'),
    'glutealsenor': ('hoft', 'höft och säte'),
}


def harmonize(source, path):
    if not any(viewer in source for viewer in VIEWERS):
        return source
    if SHARED_CSS not in source:
        source = source.replace('</head>', f'<link rel="stylesheet" href="{SHARED_CSS}"></head>', 1)

    # Earlier catalogue integration can leave the same return link twice.
    library_link_seen = False

    def library_link(match):
        nonlocal library_link_seen
        if library_link_seen:
            return ''
        library_link_seen = True
        return match[0]

    source = re.sub(r'<a\b(?=[^>]*class="[^"]*\bcase-library-back\b)[^>]*>.*?</a>', library_link, source, flags=re.S)

    def page_navigation(match):
        nav = re.sub(r'\saria-label="[^"]*"', '', match[0], count=1)
        nav = nav.replace('<nav ', '<nav aria-label="I patientfallet" ', 1)
        for anchor, text in LABELS.items():
            nav = re.sub(r'(<a\b[^>]*href="' + re.escape(anchor) + r'"[^>]*>).*?(</a>)', lambda m: m[1] + text + m[2], nav, flags=re.S)
        return nav

    source = re.sub(r'<nav\b(?=[^>]*class="[^"]*\bcase-page-nav\b)[^>]*>.*?</nav>', page_navigation, source, count=1, flags=re.S)
    key = path.relative_to(ROOT / 'ultraljud').parts[0]
    region, label = REGIONS.get(key, ('', ''))
    region_link = f'<a href="/ultraljud/bilder/?omrade={region}#exempel" class="navigation-link">Fler patientfall om {label}</a>' if region else ''
    all_link = '<a href="/ultraljud/bilder/" class="navigation-link">Alla patientfall</a>'

    def bottom_navigation(match):
        nav = re.sub(r'\saria-label="[^"]*"', '', match[0], count=1)
        nav = nav.replace('<nav ', '<nav aria-label="Fler patientfall" ', 1)
        nav = nav.replace('Nästa bildexempel', 'Nästa patientfall').replace('Föregående bildexempel', 'Föregående patientfall')
        if region:
            nav = re.sub(r'(<a\b[^>]*href="/ultraljud/bilder/\?[^\"]*"[^>]*>).*?(</a>)', lambda m: m[1] + f'Fler patientfall om {label}' + m[2], nav, count=1, flags=re.S)
        if not re.search(r'href="/ultraljud/bilder/"', nav):
            nav = nav.replace('</nav>', all_link + '</nav>')
        return nav

    source, count = re.subn(r'<nav\b(?=[^>]*class="[^"]*\batlas-case-bottom\b)[^>]*>.*?</nav>', bottom_navigation, source, count=1, flags=re.S)
    if not count:
        source = source.replace('</main>', '<nav aria-label="Fler patientfall" class="atlas-case-bottom wrap">' + region_link + all_link + '</nav></main>', 1)
    return source


def main():
    changed, checked = [], []
    for path in sorted((ROOT / 'ultraljud').rglob('index.html')):
        original = path.read_text(encoding='utf-8')
        if not any(viewer in original for viewer in VIEWERS):
            continue
        checked.append(str(path.relative_to(ROOT)))
        updated = harmonize(original, path)
        assert harmonize(updated, path) == updated, f'Layout must be idempotent: {path}'
        if updated != original:
            path.write_text(updated, encoding='utf-8')
            changed.append(str(path.relative_to(ROOT)))
    print({'checked': len(checked), 'changed': len(changed), 'pages': changed})


if __name__ == '__main__':
    main()
