"""Link the new case into existing navigation, catalogue and sitemap."""
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

from unify_case_stories import Tree, raw
from build_supraspinatus_case import PATH, ASSETS, URL, HEADER

ROOT = Path(__file__).resolve().parents[2]


def main():
    file = ROOT / 'ultraljud/bilder/index.html'
    source = file.read_text()
    if PATH not in source:
        tree = Tree(source)
        group = tree.root.find(lambda n: n.attrs.get('id') == 'omrade-axel')
        grid = group.find(lambda n: n.has_class('atlas-grid'))
        if grid is None:
            # Existing catalogue uses atlas-group-grid on some revisions.
            grid = next(n for n in group.walk() if n.tag == 'div' and any(c.has_class('atlas-entry') for c in n.children))
        card = f'<article class="atlas-entry" data-atlas-entry data-region="axel" data-symptoms="lyft efter-skada" data-search="supraspinatus ruptur totalruptur bald head axel kraftlös svaghet tvätta håret lyfta armen ut sidan skidolycka senfäste rotatorkuff sinogel hyaluron hyaluronsyra"><div class="atlas-thumb" aria-hidden="true"><img src="{ASSETS}sax-without.original.jpg" alt="" width="1280" height="960" loading="lazy" decoding="async"{HEADER}></div><div class="atlas-entry-copy"><small>Axel · Supraspinatusruptur</small><h4><a href="{PATH}" data-atlas-case>Kraftlös axel vid hårtvätt och lyft?</a></h4><span class="atlas-case-type">Patientfall från Kansei</span><p>En tidigare skidolycka och en totalruptur av supraspinatussenan. Följ fynden, behandlingen och patientens egen insats.</p><a class="atlas-image-shortcut" href="{PATH}#bilder">Direkt till bilder och fynd</a></div></article>'
        source = source[:grid.content_end] + card + source[grid.content_end:]
    tree = Tree(source)
    cards = [n for n in tree.root.walk() if n.has_class('atlas-entry')]
    groups = [n for n in tree.root.walk() if n.has_class('atlas-group')]
    for region in ('alla', 'axel', 'armbage', 'hand', 'hoft', 'kna', 'fot'):
        count = len(cards) if region == 'alla' else sum(n.attrs.get('data-region') == region for n in cards)
        # Keep both navigation counters and the initial result count honest.
        pattern = r'(<a\b[^>]*data-atlas-region="' + region + r'"[^>]*>.*?<small>)\d+(</small>)'
        source = re.sub(pattern, lambda m:m[1] + str(count) + m[2], source, flags=re.S)
    source = re.sub(r'\d+ patientfall · Alla områden', str(len(cards)) + ' patientfall · Alla områden', source)
    def schema(match):
        data = json.loads(match[2])
        for node in data.get('@graph', []):
            if node.get('@type') == 'ItemList':
                entries = []
                for i, card in enumerate(cards, 1):
                    link = card.find(lambda n:n.tag == 'a' and 'data-atlas-case' in n.attrs)
                    label = re.sub('<[^>]*>', '', raw(source, link))
                    entries.append({'@type':'ListItem','position':i,'name':label,'url':'https://www.kansei.se' + link.attrs['href']})
                node.update(numberOfItems=len(entries), itemListElement=entries)
            elif node.get('@type') == 'CollectionPage':
                node['dateModified'] = '2026-10-28'
        return match[1] + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + match[3]
    # Reparse because counter replacement may have shifted source positions.
    tree = Tree(source); cards = [n for n in tree.root.walk() if n.has_class('atlas-entry')]
    source = re.sub(r'(<script\b[^>]*type="application/ld\+json"[^>]*>)(.*?)(</script>)', schema, source, flags=re.S)
    file.write_text(source)
    for relative in ('ultraljud/axel/index.html', 'ultraljud/rotatorkuff/index.html'):
        file = ROOT / relative; source = file.read_text()
        if PATH in source:
            continue
        tree = Tree(source)
        section = tree.root.find(lambda n:n.attrs.get('id') == 'fall-och-plan')
        assert section, relative
        wrap = next(n for n in section.children if n.has_class('wrap'))
        link = f'<p><a href="{PATH}">Patientfall med kraftlös axel och supraspinatusruptur</a>. Se senfyndet i två riktningar och läs hur behandling, egen insats och uppföljning kopplades till armens funktion.</p>'
        source = source[:wrap.content_end] + link + source[wrap.content_end:]
        file.write_text(source)
    file = ROOT / 'sitemap.xml'
    tree = ET.parse(file); root = tree.getroot(); ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    entries = {entry.findtext('{' + ns + '}loc'):entry for entry in root}
    if URL not in entries:
        node = ET.SubElement(root, '{' + ns + '}url'); ET.SubElement(node, '{' + ns + '}loc').text = URL; entries[URL] = node
    for url in (URL, 'https://www.kansei.se/ultraljud/bilder/', 'https://www.kansei.se/ultraljud/axel/', 'https://www.kansei.se/ultraljud/rotatorkuff/'):
        node = entries[url]; date = node.find('{' + ns + '}lastmod')
        if date is None: date = ET.SubElement(node, '{' + ns + '}lastmod')
        date.text = '2026-10-28'
    for prefix, uri in [('', ns), ('image', 'http://www.google.com/schemas/sitemap-image/1.1'), ('video', 'http://www.google.com/schemas/sitemap-video/1.1')]: ET.register_namespace(prefix, uri)
    ET.indent(tree, space='  ')
    file.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode') + '\n')
    print(f'Linked supraspinatus case; catalogue has {len(cards)} cases.')


if __name__ == '__main__':
    main()
