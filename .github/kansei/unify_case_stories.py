"""Apply the reviewed hip-case layout to all twelve existing ultrasound cases.

Preserves each reader byte-for-byte and keeps the recorded clinical narrative,
illustrative-example disclosures, source links and existing public anchor IDs.
Run from any directory; no third-party parser or build dependencies required.
"""
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
CSS = '/assets/case-story.20261022.css'
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())
FACTS = {
    'axel/bicepstendinopati': ('Bicepssenan i axeln', 'Strukturförändrad sena och senskidevätska', 'Anpassad belastning och gradvis träning'),
    'axel/pectoralisruptur': ('Stora bröstmuskeln och dess sena', 'Partiell muskelskada. Senfästet bedöms separat', 'Bedöma omfattningen före återgång till tung press'),
    'axel/ac-ledsskada': ('AC-led och omgivande mjukdelar efter fall', 'Förändrat ledläge och skadade mjukdelar', 'Anpassad belastning, rehabilitering och uppföljning'),
    'hand-handled/karpaltunnelsyndrom': ('Medianusnerven i karpaltunneln', 'Lokal kompression vid karpalligamentet', 'Råd, avlastning och ställningstagande till vidare vård'),
    'kalkaxel': ('Supraspinatussenan i axeln', 'Kalkinlagringar och rupturområden', 'Bedöma senskadan och anpassa belastning och rehab'),
    'tennisarmbage/bilder': ('Sträcksenans fäste på armbågens utsida', 'Tendinos och rupturområden inom senan', 'Anpassa grepp och gradvis bygga upp styrkan'),
    'halsena/bilder': ('Hälsenan i flera snitt och med Doppler', 'Tendinos, rupturområden, kalk och kärlsignaler', 'Bedöma omfattningen före individuellt anpassad träning'),
    'loparkna': ('IT-bandet och vävnaden under det', 'Vätskefylld ficka under IT-bandet', 'Anpassad löpbelastning och gradvis återgång'),
    'bursit-axel': ('Slemsäck och rotatorkuffens senor', 'Bursavätska och beskrivna senskador', 'Bedöma kraft, funktion och behov av vidare vård'),
}


class Node:
    def __init__(self, tag, attrs, start, content_start, parent=None):
        self.tag, self.attrs, self.start, self.content_start = tag, dict(attrs), start, content_start
        self.end, self.content_end, self.parent, self.children = content_start, content_start, parent, []

    def has_class(self, name):
        return name in self.attrs.get('class', '').split()

    def find(self, predicate):
        return next((node for node in self.walk() if predicate(node)), None)

    def walk(self):
        for child in self.children:
            yield child
            yield from child.walk()


class Tree(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.lines = [0]
        for match in re.finditer('\n', source):
            self.lines.append(match.end())
        self.root = Node('document', [], 0, 0)
        self.stack = [self.root]
        self.feed(source)

    def position(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        start = self.position()
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
            if self.stack[index].tag == tag:
                node = self.stack[index]
                node.content_end = self.position()
                node.end = self.source.index('>', node.content_end) + 1
                del self.stack[index:]
                return


def raw(source, node):
    return source[node.start:node.end]


def inside(source, node):
    return source[node.content_start:node.content_end]


def text(source):
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', '', source))).strip()


def replace_ranges(source, changes):
    for start, end, replacement in sorted(changes, reverse=True):
        source = source[:start] + replacement + source[end:]
    return source


def chapter(body, number):
    body = re.sub(r'(<h3\b[^>]*>)\d+\.\s*', r'\1', body, count=1)
    body = body.replace('us-case-view-links', 'case-story-image-links')
    return f'<article class="case-story-chapter"><span class="case-story-step" aria-hidden="true">{number:02d}</span><div>{body}</div></article>'


def facts(rows):
    entries = ''.join(f'<div><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>' for label, value in rows)
    return '<div class="case-story-facts"><h3>Fallet i korthet</h3><dl>' + entries + '</dl></div>'


def shared_story(source, key):
    tree = Tree(source)
    header = tree.root.find(lambda n: n.tag == 'header')
    grid = tree.root.find(lambda n: n.has_class('us-case-grid'))
    figure = grid.find(lambda n: n.tag == 'figure')
    assert header and grid and figure, key
    heading = raw(source, header).replace('us-case-intro', 'case-story-heading').replace('us-case-note', 'case-story-note')
    # Lead and disclosure retain their exact text and distinct provenance.
    heading = re.sub(r'<p>(?!<strong)', '<p class="case-story-lead">', heading, count=1)
    chapters = []
    for index, article in enumerate(grid.children, 1):
        assert article.tag == 'article'
        body = inside(source, article).replace(raw(source, figure), '')
        chapters.append(chapter(body, index))
    kind = text(raw(source, header.find(lambda n: n.has_class('eyebrow'))))
    exam, finding, plan = FACTS[key]
    rows = [('Undersökning', exam), ('Bildfynd', finding), ('Fortsatt plan', plan), ('Falltyp', kind)]
    preview = raw(source, figure).replace(' class="us-case-figure"', '').replace('us-case-image-link', 'case-story-image-link')
    tail = source[grid.end:]
    # The caller replaces only the section's contents, so strip the old wrap/section closers.
    tail = tail[:tail.rfind('</div>')]
    tail = tail.replace('us-case-follow', 'case-story-follow').replace('us-case-actions', 'case-story-actions').replace('us-case-note', 'case-story-note').replace('us-case-source', 'case-story-source')
    opening = source[:source.index('>') + 1].replace('section us-case-path', 'section case-story')
    return (opening + '<div class="wrap">' + heading + '<div class="case-story-layout"><div class="case-story-chapters">'
            + '\n'.join(chapters) + tail + '</div><aside class="case-story-aside" aria-label="Patientfallet i korthet">'
            + preview + facts(rows) + '</aside></div></div></section>')


def knee_story(source):
    tree = Tree(source)
    header = tree.root.find(lambda n: n.tag == 'header')
    steps = [n for n in tree.root.walk() if n.has_class('knee-guide-step')]
    assert len(steps) == 4
    heading = raw(source, header).replace('knee-guide-intro', 'case-story-heading').replace('knee-small', 'case-story-note')
    heading = heading.replace('<p>En patient', '<p class="case-story-lead">En patient', 1)
    chapters = []
    for index, step in enumerate(steps, 1):
        body = inside(source, step)
        # These existing side notes now follow their chapter's text in the reading column.
        body = re.sub(r'<aside class="orientation"><h3>(.*?)</h3>(.*?)</aside>',
                      r'<details class="case-story-details"><summary>\1</summary>\2</details>', body, flags=re.S)
        chapters.append(chapter(body, index))
    image = ('<figure><a href="#bilder" data-knee-select="ledvatska" aria-label="Se ledvätskan i bildvisaren">'
             '<img src="/bilder/ultraljud/kna/ledvatska-ultraljud.webp" alt="Ultraljud av ledvätskan ovanför knäskålen." width="1280" height="880" loading="lazy" decoding="async"/>'
             '</a><figcaption>Originalultraljud från Kansei. Öppna bilden för anatomi och fyndmarkeringar.</figcaption></figure>')
    rows = [('Undersökning', 'Knäled och svullnad, tillsammans med tidigare röntgen'),
            ('Bildfynd', 'Ökad ledvätska, osteofyter och lokala broskförändringar'),
            ('Genomförd behandling', 'Hyaluroninjektion med Sinovial i knäleden'),
            ('Fortsatt plan', 'Anpassad rehabilitering och uppföljning av vardagsfunktionen')]
    actions = tree.root.find(lambda n: n.has_class('knee-guide-actions'))
    note = tree.root.find(lambda n: n.has_class('knee-guide-source'))
    opening = source[:source.index('>') + 1].replace('section knee-tint knee-clinical-guide', 'section case-story knee-clinical-guide')
    return (opening + '<div class="wrap">' + heading + '<div class="case-story-layout"><div class="case-story-chapters">'
            + '\n'.join(chapters) + raw(source, actions).replace('knee-guide-actions', 'case-story-actions')
            + raw(source, note).replace('knee-small knee-guide-source', 'case-story-note case-story-source')
            + '</div><aside class="case-story-aside" aria-label="Patientfallet i korthet">' + image + facts(rows)
            + '</aside></div></div></section>')


def hip_story(source):
    # Preserve legacy classes for the existing hip reader checks and generator compatibility.
    def add_aliases(match):
        names = match[1].split()
        aliases = [name.replace('hip-story', 'case-story', 1) for name in names if name.startswith('hip-story')]
        return 'class="' + ' '.join(dict.fromkeys(names + aliases)) + '"'
    result = re.sub(r'class="([^"]*)"', add_aliases, source)
    if 'class="section"' in result[:result.index('>') + 1]:
        result = result.replace('class="section"', 'class="section case-story"', 1)
    return result


def unify(source, key):
    story_id = 'artros' if key == 'kna' else 'patientfall'
    tree = Tree(source)
    story = tree.root.find(lambda n: n.tag == 'section' and n.attrs.get('id') == story_id)
    assert story
    original_story = raw(source, story)
    if not story.has_class('case-story'):
        if key == 'kna':
            replacement = knee_story(original_story)
        elif key in FACTS:
            replacement = shared_story(original_story, key)
        else:
            replacement = hip_story(original_story)
        source = source[:story.start] + replacement + source[story.end:]
    if CSS not in source:
        source = source.replace('</head>', f'<link rel="stylesheet" href="{CSS}"/></head>', 1)

    # Narrative first, reader second: DOM order, anchor menu and reading progress agree.
    tree = Tree(source)
    story = tree.root.find(lambda n: n.tag == 'section' and n.attrs.get('id') == story_id)
    viewer = tree.root.find(lambda n: n.tag == 'section' and n.attrs.get('id') == 'bilder')
    assert story and viewer
    if viewer.start < story.start:
        assert not source[viewer.end:story.start].strip(), 'Unexpected content between reader and story'
        source = source[:viewer.start] + raw(source, story) + '\n' + raw(source, viewer) + source[story.end:]

    tree = Tree(source)
    nav = tree.root.find(lambda n: n.tag == 'nav' and n.has_class('case-page-nav'))
    last = 'faq' if tree.root.find(lambda n: n.attrs.get('id') == 'faq') else 'kansei'
    last_label = 'Frågor och svar' if last == 'faq' else 'Besök och bokning'
    replacement = (f'<nav class="case-page-nav" aria-label="På den här sidan"><a href="#{story_id}">Patientfallet</a>'
                   '<a href="#bilder">Bilder och fynd</a><a href="#nasta-steg">Bedömning och nästa steg</a>'
                   f'<a href="#{last}">{last_label}</a></nav>')
    source = source[:nav.start] + replacement + source[nav.end:]
    if 'class="case-library-back"' not in source:
        marker = source.index('<nav class="case-page-nav"')
        source = source[:marker] + '<a class="case-library-back" href="/ultraljud/bilder/">Alla patientfall</a>' + source[marker:]

    tree = Tree(source)
    changes = []
    sections = [n for n in tree.root.walk() if 'data-reading-section' in n.attrs]
    for index, section in enumerate(sections, 1):
        h2 = section.find(lambda n: n.tag == 'h2')
        assert h2, (key, section.attrs)
        heading = raw(source, h2)
        number = f'<span class="reading-chapter-number" aria-hidden="true">{index:02d}</span>'
        heading = re.sub(r'<span\b[^>]*class="reading-chapter-number"[^>]*>.*?</span>', '', heading, flags=re.S)
        heading = heading[:heading.index('>') + 1] + number + heading[heading.index('>') + 1:]
        changes.append((h2.start, h2.end, heading))
    return replace_ranges(source, changes)


def main():
    updated = []
    for file in sorted((ROOT / 'ultraljud').rglob('index.html')):
        source = file.read_text()
        body = re.search(r'<body\b[^>]*class="([^"]*)"', source)
        if not body or 'ultrasound-case' not in body[1].split():
            continue
        key = str(file.parent.relative_to(ROOT / 'ultraljud'))
        old_tree = Tree(source)
        old_viewer = raw(source, old_tree.root.find(lambda n: n.tag == 'section' and n.attrs.get('id') == 'bilder'))
        updated_source = unify(source, key)
        new_tree = Tree(updated_source)
        new_viewer = raw(updated_source, new_tree.root.find(lambda n: n.tag == 'section' and n.attrs.get('id') == 'bilder'))
        # Chapter numbers reflect the new order; the entire clinical reader stays identical.
        strip_numbers = lambda s: re.sub(r'<span\b[^>]*class="reading-chapter-number"[^>]*>.*?</span>', '', s, flags=re.S)
        assert strip_numbers(old_viewer) == strip_numbers(new_viewer), 'Reader changed: ' + key
        assert unify(updated_source, key) == updated_source, 'Migration must be idempotent: ' + key
        file.write_text(updated_source)
        updated.append(str(file.relative_to(ROOT)))
    assert len(updated) == 12, updated
    print('\n'.join(updated))
    print(f'PASS: {len(updated)} case pages use one journey, navigation and facts layout; clinical readers preserved.')


if __name__ == '__main__':
    main()
