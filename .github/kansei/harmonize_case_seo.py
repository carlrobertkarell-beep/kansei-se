#!/usr/bin/env python3
"""Keep ultrasound case metadata aligned with each page's visible content.

Default mode audits without writing. Use --write --updated YYYY-MM-DD after
an editorial update. Existing publication dates and clinical media are retained.
The knee overview remains an examination/service page with case examples.
"""
from __future__ import annotations

import argparse
import copy
from datetime import date
from html import escape, unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = 'https://www.kansei.se'
AUTHOR_URL = ORIGIN + '/team/carl-robert-karell/'
AUTHOR = {'@type': 'Person', '@id': AUTHOR_URL + '#person',
          'name': 'Carl-Robert Kårell', 'jobTitle': 'Legitimerad naprapat',
          'url': AUTHOR_URL}
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())
MONTHS = ('januari februari mars april maj juni juli augusti september oktober november december').split()

# Case-specific intent is separate from the region and examination landing pages.
CASES = {
    '/ultraljud/axel/bicepstendinopati/': (
        'Bicepssenan på ultraljud | Kansei patientfall',
        'Ont framtill i axeln vid lyft? Följ ett patientexempel med förändrad bicepssena och senskidevätska, ultraljudsbilder, Doppler och fortsatt plan.'),
    '/ultraljud/axel/pectoralisruptur/': (
        'Bröstmuskelskada efter bänkpress | Kansei patientfall',
        'Smärta vid bänkpress och blåmärke på överarmen. Se Kanseis patientfall med pectoralisskada, ultraljudsfynd och bedömning inför fortsatt belastning.'),
    '/ultraljud/axel/ac-ledsskada/': (
        'AC-ledsskada efter fall | Kansei patientfall',
        'Ont ovanpå axeln efter ett fall? Se hur ultraljud, sidjämförelse och axelns funktion bidrog till bedömning och plan i Kanseis patientfall.'),
    '/ultraljud/hand-handled/karpaltunnelsyndrom/': (
        'Karpaltunnelsyndrom på ultraljud | Kansei patientfall',
        'Domningar i handen? Följ ett patientexempel med medianusnerven i karpaltunneln, ultraljudsfynd och hur nervfunktion och symtom påverkar nästa steg.'),
    '/ultraljud/kalkaxel/': (
        'Kalkaxel och senskada på ultraljud | Kansei patientfall',
        'Se kalkinlagringar och samtidig skada i supraspinatussenan på ultraljud. Patientexempel med anatomilager, film och plan för axelns funktion.'),
    '/ultraljud/bursit-axel/': (
        'Bursit och senskador i axeln | Kansei patientfall',
        'Ont vid armlyft och svårt att ligga på axeln? Se ett patientexempel med bursavätska och senskador, flera ultraljudsvyer och fortsatt bedömning.'),
    '/ultraljud/loparkna/': (
        'Löparknä på ultraljud | Kansei patientfall',
        'Ont på knäts utsida när du springer? Se IT-bandet och vätskan under det på ultraljud och följ ett patientexempel om bedömning och löpbelastning.'),
    '/ultraljud/hoftled/bilder/': (
        'Höftleden på ultraljud inför Sinogel | Kansei patientfall',
        'Följ ett patientfall där höftleden undersöktes med ultraljud före en Sinogel-injektion. Se anatomin, undersökningsfynden och behandlingsresonemanget.'),
    '/ultraljud/glutealsenor/bilder/': (
        'Glutealsenor och cysta på ultraljud | Kansei patientfall',
        'Långvarig smärta på höftens utsida utan artrosfynd på röntgen. Följ Kanseis patientfall med glutealsenor, cystfynd och en plan för höftens funktion.'),
    '/ultraljud/halsena/bilder/': (
        'Hälsena med tendinos och rupturer | Kansei patientfall',
        'Se tendinos, rupturområden och kalk i hälsenan på ultraljud. Patientexempel med anatomilager, Doppler och hur fynden vägs in inför rehabilitering.'),
    '/ultraljud/tennisarmbage/bilder/': (
        'Tennisarmbåge på ultraljud | Kansei patientfall',
        'Ont vid grepp, lyft eller padel? Jämför frisk och förändrad extensorsena på ultraljud och följ ett patientexempel om bedömning och belastning.'),
    '/ultraljud/kna/forkalkad-menisk/': (
        'Förkalkad menisk och kalk i brosket | Kansei patientfall',
        'Vad betyder kalk i menisk och ledbrosk? Se ultraljudsbilder och anatomilager och följ ett patientexempel där fynd, besvär och fortsatt plan sätts ihop.'),
    '/ultraljud/kna/artros-ledband-hyaluron/': (
        'Knäartros med ledbandsskada | Kansei patientfall',
        'Följ ett patientfall med långvarig knäsmärta, artros och skada i inre ledbandet. Se ultraljud, hyaluroninjektion och planen för knäts funktion.'),
    '/ultraljud/axel/supraspinatusruptur/': (
        'Totalruptur av supraspinatus | Kansei patientfall',
        'Kraftlös axel vid hårtvätt och lyft. Följ Kanseis patientfall med totalruptur av supraspinatussenan, ultraljudsbilder, anatomilager och fortsatt plan.'),
    # Preserve this established URL's primary examination/booking intent.
    '/ultraljud/kna/': (None, None),
}
OPTIONAL = {'/ultraljud/axel/supraspinatusruptur/'}


class Node:
    def __init__(self, tag, attrs=(), start=0, content_start=0, parent=None):
        self.tag, self.attrs, self.start = tag, dict(attrs), start
        self.content_start = self.content_end = self.end = content_start
        self.parent, self.children = parent, []

    def walk(self):
        for child in self.children:
            yield child
            yield from child.walk()

    def ancestors(self):
        current = self.parent
        while current:
            yield current
            current = current.parent


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.lines = [0] + [match.end() for match in re.finditer('\n', source)]
        self.root = Node('document')
        self.stack = [self.root]
        self.feed(source)

    def absolute_position(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        start = self.absolute_position()
        node = Node(tag, attrs, start, start + len(self.get_starttag_text()), self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            node = self.stack[index]
            if node.tag == tag:
                node.content_end = self.absolute_position()
                node.end = self.source.index('>', node.content_end) + 1
                del self.stack[index:]
                return

    def nodes(self, tag):
        return [node for node in self.root.walk() if node.tag == tag]


def plain(value):
    value = re.sub(r'<(?:script|style)\b[^>]*>[\s\S]*?</(?:script|style)>', ' ', value, flags=re.I)
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]*>', ' ', value))).strip()


def inner(source, node):
    return source[node.content_start:node.content_end]


def replace_ranges(source, changes):
    for start, end, replacement in sorted(changes, reverse=True):
        source = source[:start] + replacement + source[end:]
    return source


def meta(source, key, value, property=False):
    document = Document(source)
    attr = 'property' if property else 'name'
    matches = [node for node in document.nodes('meta') if node.attrs.get(attr, '').lower() == key.lower()]
    tag = f'<meta {attr}="{escape(key, quote=True)}" content="{escape(value, quote=True)}">'
    if not matches:
        return source.replace('</head>', tag + '</head>', 1)
    return replace_ranges(source, [(node.start, node.end, tag if index == 0 else '') for index, node in enumerate(matches)])


def get_meta(document, key):
    return next((node.attrs.get('content', '') for node in document.nodes('meta')
                 if node.attrs.get('name', node.attrs.get('property', '')).lower() == key.lower()), '')


def faq_questions(source, document):
    questions, seen = [], set()
    for detail in document.nodes('details'):
        # Restrict to explicit FAQ blocks. Clinical reasoning and sources also
        # use details/summary, but are not automatically FAQ questions.
        ancestors = [detail] + list(detail.ancestors())
        if not any(node.attrs.get('id') == 'faq' or
                   any(name == 'faq' or name.endswith('-faq') for name in node.attrs.get('class', '').split())
                   for node in ancestors):
            continue
        summary = next((node for node in detail.children if node.tag == 'summary'), None)
        if summary is None:
            continue
        question = plain(inner(source, summary))
        answer = plain(source[summary.end:detail.content_end])
        if not question or not answer or question in seen:
            continue
        seen.add(question)
        questions.append({'@type': 'Question', 'name': question,
                          'acceptedAnswer': {'@type': 'Answer', 'text': answer}})
    return questions


def page_images(page, fallback):
    images = page.get('image', [])
    if not isinstance(images, list):
        images = [images]
    return images or [fallback]


def schema_media(value):
    """Media entities, wherever nested, must be preserved byte-for-byte as data."""
    if isinstance(value, list):
        return [media for item in value for media in schema_media(item)]
    if not isinstance(value, dict):
        return []
    kind = value.get('@type', [])
    kind = [kind] if isinstance(kind, str) else kind
    if set(kind) & {'VideoObject', 'ImageObject', 'Clip'}:
        return [copy.deepcopy(value)]
    return [media for item in value.values() for media in schema_media(item)]


def sync_elements(value, source, ids, url):
    if isinstance(value, list):
        for item in value:
            sync_elements(item, source, ids, url)
    elif isinstance(value, dict):
        if value.get('@type') == 'WebPageElement' and value.get('@id', '').startswith(url + '#'):
            element = ids.get(value['@id'].split('#', 1)[1])
            if element:
                heading = next((node for node in element.walk() if node.tag in {'h2', 'h3'}), None)
                paragraphs = [node for node in element.walk() if node.tag == 'p']
                if heading:
                    value['name'] = re.sub(r'^\d{2}\s*', '', plain(inner(source, heading)))
                if 'description' in value and paragraphs:
                    value['description'] = plain(inner(source, paragraphs[0]))
                if 'text' in value:
                    value['text'] = plain(inner(source, element))
        for item in value.values():
            sync_elements(item, source, ids, url)


def update_schema(source, path, title, description, share_image, updated):
    document = Document(source)
    ids = {node.attrs['id']: node for node in document.root.walk() if 'id' in node.attrs}
    h1s = document.nodes('h1')
    assert len(h1s) == 1, f'{path}: expected one h1'
    headline = plain(inner(source, h1s[0]))
    url = ORIGIN + path
    questions = faq_questions(source, document)
    blocks, page_node, owner = [], None, None
    for script in document.nodes('script'):
        if script.attrs.get('type') != 'application/ld+json':
            continue
        value = json.loads(inner(source, script))
        if isinstance(value, dict) and '@graph' not in value:
            # New pages may start with a single page entity. A graph is needed
            # before adding linked Article/FAQ entities to that JSON-LD block.
            context = value.get('@context', 'https://schema.org')
            value = {'@context': context,
                     '@graph': [{key: item for key, item in value.items() if key != '@context'}]}
        graph = value.get('@graph', [value]) if isinstance(value, dict) else value
        assert isinstance(graph, list), f'{path}: expected JSON-LD object or graph'
        blocks.append((script, value, graph))
        for node in graph:
            if node.get('@type') in {'WebPage', 'MedicalWebPage'}:
                assert page_node is None, f'{path}: duplicate page entities'
                page_node, owner = node, graph
    assert page_node is not None, f'{path}: MedicalWebPage entity missing'
    before_media = [schema_media(value) for _, value, _ in blocks]
    page_id = page_node.setdefault('@id', url + '#webpage')
    page_node.update({'url': url, 'name': title, 'description': description,
                      'inLanguage': 'sv', 'author': copy.deepcopy(AUTHOR)})
    if updated:
        page_node['dateModified'] = updated
    modified = page_node.get('dateModified')
    page_node.setdefault('primaryImageOfPage', {'@id': share_image})
    for _, value, graph in blocks:
        sync_elements(value, source, ids, url)
        # FAQ schema is rebuilt from the current visible FAQ text, never from
        # old copies or every disclosure widget on the page.
        graph[:] = [node for node in graph if node.get('@type') != 'FAQPage']
    if path != '/ultraljud/kna/':
        article = next((node for _, _, graph in blocks for node in graph
                        if node.get('@type') == 'Article'), None)
        if article is None:
            article = {'@type': 'Article', '@id': url + '#article'}
            owner.append(article)
        article.update({'headline': headline, 'description': description,
                        'inLanguage': 'sv', 'author': copy.deepcopy(AUTHOR),
                        'mainEntityOfPage': {'@id': page_id}, 'image': page_images(page_node, share_image)})
        article.setdefault('publisher', {'@id': ORIGIN + '/#clinic'})
        if page_node.get('datePublished'):
            article.setdefault('datePublished', page_node['datePublished'])
        if modified:
            article['dateModified'] = modified
        parts = page_node.setdefault('hasPart', [])
        if isinstance(parts, dict):
            parts = [parts]
            page_node['hasPart'] = parts
        if not any(part.get('@id') == article['@id'] for part in parts if isinstance(part, dict)):
            parts.append({'@id': article['@id']})
    # Rebuild breadcrumbs only from the breadcrumb links visible on the page.
    crumbs = next((node for node in document.root.walk()
                   if node.tag == 'nav' and ('brödsmul' in node.attrs.get('aria-label', '').lower()
                                            or 'breadcrumb' in node.attrs.get('class', ''))), None)
    if crumbs:
        links = [(plain(inner(source, node)), node.attrs['href'])
                 for node in crumbs.walk() if node.tag == 'a' and node.attrs.get('href')]
        links = [(name, href if href.startswith('http') else ORIGIN + href)
                 for name, href in links if not href.startswith('#')]
        if links and links[-1][1] != url:
            links.append((headline.rstrip('.'), url))
        breadcrumb = next((node for _, _, graph in blocks for node in graph
                           if node.get('@type') == 'BreadcrumbList'), None)
        if links:
            if breadcrumb is None:
                breadcrumb = {'@type': 'BreadcrumbList', '@id': url + '#breadcrumb'}
                owner.append(breadcrumb)
            breadcrumb['itemListElement'] = [
                {'@type': 'ListItem', 'position': index + 1, 'name': name, 'item': href}
                for index, (name, href) in enumerate(links)]
            page_node['breadcrumb'] = {'@id': breadcrumb.setdefault('@id', url + '#breadcrumb')}
    if questions:
        owner.append({'@type': 'FAQPage', '@id': url + '#case-questions',
                      'inLanguage': 'sv', 'mainEntity': questions,
                      'isPartOf': {'@id': page_id}})
    assert before_media == [schema_media(value) for _, value, _ in blocks], f'{path}: schema media changed'
    changes = [(script.content_start, script.content_end,
                json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))
               for script, value, _ in blocks]
    return replace_ranges(source, changes), modified, len(questions)


def add_byline(source, modified):
    if not modified:
        return source
    d = date.fromisoformat(modified[:10])
    label = f'{d.day} {MONTHS[d.month - 1]} {d.year}'
    byline = ('<p class="case-seo-byline">Av <a href="/team/carl-robert-karell/">'
              'Carl-Robert Kårell, legitimerad naprapat</a> · Senast uppdaterad '
              f'<time datetime="{d.isoformat()}">{label}</time>.</p>')
    document = Document(source)
    old = [node for node in document.nodes('p')
           if 'case-seo-byline' in node.attrs.get('class', '').split()]
    source = replace_ranges(source, [(node.start, node.end, '') for node in old])
    h1 = Document(source).nodes('h1')[0]
    return source[:h1.end] + byline + source[h1.end:]


def harmonize(source, path, updated=None):
    original_media = re.findall(r'<(?:img|video|source|track)\b[^>]*>', source)
    document = Document(source)
    configured_title, configured_description = CASES[path]
    title = configured_title or plain(inner(source, document.nodes('title')[0]))
    description = configured_description or get_meta(document, 'description')
    # Avoid invisible soft hyphens in snippets and findable copy.
    description = description.replace('\u00ad', '')
    url = ORIGIN + path
    share_image = get_meta(document, 'og:image')
    if not share_image:
        raise AssertionError(f'{path}: representative social image is missing')
    if share_image.startswith('/'):
        share_image = ORIGIN + share_image
    assert share_image.startswith(ORIGIN + '/'), f'{path}: unexpected social image host'
    image_path = ROOT / unquote(urlsplit(share_image).path).lstrip('/')
    assert image_path.is_file(), f'{path}: social image target is missing: {share_image}'
    title_node = document.nodes('title')[0]
    source = replace_ranges(source, [(title_node.content_start, title_node.content_end, escape(title))])
    canonical = [node for node in Document(source).nodes('link')
                 if 'canonical' in node.attrs.get('rel', '').split()]
    tag = f'<link rel="canonical" href="{url}">'
    source = replace_ranges(source, [(node.start, node.end, tag if index == 0 else '')
                                     for index, node in enumerate(canonical)])
    if not canonical:
        source = source.replace('</head>', tag + '</head>', 1)
    for key, value in {'description': description, 'author': AUTHOR['name'],
                       'twitter:card': 'summary_large_image', 'twitter:title': title,
                       'twitter:description': description, 'twitter:image': share_image,
                       'twitter:image:alt': title.split(' | ')[0]}.items():
        source = meta(source, key, value)
    for key, value in {'og:title': title, 'og:description': description, 'og:url': url,
                       'og:type': 'website' if path == '/ultraljud/kna/' else 'article',
                       'og:image': share_image, 'og:image:alt': title.split(' | ')[0],
                       'og:locale': 'sv_SE', 'og:site_name': 'Kansei Naprapati & Rehabcenter',
                       'article:author': AUTHOR_URL}.items():
        source = meta(source, key, value, property=True)
    source, modified, faq_count = update_schema(source, path, title, description, share_image, updated)
    if modified:
        source = meta(source, 'article:modified_time', modified, property=True)
    source = add_byline(source, modified)
    assert re.findall(r'<(?:img|video|source|track)\b[^>]*>', source) == original_media, f'{path}: clinical media tags changed'
    return source, {'path': path, 'title': title, 'description': description,
                    'faq_questions': faq_count, 'modified': modified,
                    'service_intent_preserved': path == '/ultraljud/kna/'}


def sitemap_changes(source, paths, updated):
    if not updated:
        return source
    # Preserve formatting and every unrelated sitemap entry.
    for path in paths:
        pattern = r'(<url>\s*<loc>' + re.escape(ORIGIN + path) + r'</loc>)([\s\S]*?)(</url>)'
        def update(match):
            body = match[2]
            if '<lastmod>' in body:
                body = re.sub(r'<lastmod>[^<]*</lastmod>', f'<lastmod>{updated}</lastmod>', body)
            else:
                body = f'<lastmod>{updated}</lastmod>' + body
            return match[1] + body + match[3]
        source = re.sub(pattern, update, source, count=1)
    ET.fromstring(source)
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Apply the reviewed metadata changes')
    parser.add_argument('--check', action='store_true', help='Fail if normalization remains to be applied')
    parser.add_argument('--updated', help='Editorial update date, YYYY-MM-DD; publication dates remain unchanged')
    parser.add_argument('--report', type=Path, help='Optional audit JSON output')
    args = parser.parse_args()
    if args.updated:
        date.fromisoformat(args.updated)
    results, missing, changed_paths = [], [], []
    for path in CASES:
        file = ROOT / path.strip('/') / 'index.html'
        if not file.is_file():
            if path not in OPTIONAL:
                raise AssertionError('Required case page missing: ' + path)
            missing.append(path)
            continue
        original = file.read_text()
        revised, result = harmonize(original, path, args.updated)
        repeated, _ = harmonize(revised, path, args.updated)
        assert repeated == revised, f'{path}: normalization is not idempotent'
        result['changed'] = revised != original
        if result['changed']:
            changed_paths.append(path)
            if args.write:
                file.write_text(revised)
        results.append(result)
    sitemap = ROOT / 'sitemap.xml'
    source = sitemap.read_text()
    revised = sitemap_changes(source, list(CASES), args.updated)
    sitemap_changed = source != revised
    if args.write and sitemap_changed:
        sitemap.write_text(revised)
    report = {'cases': len(results), 'changed_cases': len(changed_paths),
              'optional_not_present': missing, 'sitemap_changed': sitemap_changed,
              'mode': 'written' if args.write else 'audit', 'results': results,
              'scope': 'Visible metadata, author/date, canonical, social previews and matching JSON-LD; no ranking or rich-result guarantee.'}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))
    if args.check and (changed_paths or sitemap_changed):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
