#!/usr/bin/env python3
"""Apply the 22 October ultrasound search-intent and booking update.

Standard library only. Search Console exports and other private analytics must
remain outside this public repository. Existing readers and media are retained.
"""
from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = Path(__file__).resolve().parent / 'content'
ORIGIN = 'https://www.kansei.se'
CSS = '/assets/ultrasound-search.20261022.css'
GUIDE = '/kunskapsbank/kna/ont-pa-utsidan-av-knat/'
BOOK = 'https://www.bokadirekt.se/boka-tjanst/kansei-rehabcenter-48847/ultraljud-rorelseapparaten-1946824'
DAY = '2026-10-22'
CHANGED: set[str] = set()


class Fragment(HTMLParser):
    def __init__(self, value: str):
        super().__init__(convert_charrefs=True)
        self.attrs: dict[str, str | None] = {}
        self.words: list[str] = []
        self.feed(value)

    def handle_starttag(self, tag, attrs):
        if not self.attrs:
            self.attrs = dict(attrs)

    def handle_data(self, data):
        self.words.append(data)


def plain(value: str) -> str:
    return ' '.join(' '.join(Fragment(value).words).split())


def save(path: str, value: str):
    target = ROOT / path
    if not target.exists() or target.read_text() != value:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value)
        CHANGED.add(path)


def add_css(value: str) -> str:
    if CSS not in value:
        value = value.replace('</head>', f'<link rel="stylesheet" href="{CSS}"></head>', 1)
    return value


def set_meta(value: str, key: str, content: str, *, prop=False) -> str:
    attribute = 'property' if prop else 'name'
    replacement = f'<meta {attribute}="{key}" content="{html.escape(content, quote=True)}">'
    found = False

    def replace(match):
        nonlocal found
        if Fragment(match[0]).attrs.get(attribute) == key:
            assert not found, f'Duplicate metadata: {key}'
            found = True
            return replacement
        return match[0]

    value = re.sub(r'<meta\b[^>]*>', replace, value, flags=re.I)
    return value if found else value.replace('</head>', replacement + '</head>', 1)


def faq_questions(value: str) -> list[dict]:
    main = re.search(r'<main\b[^>]*>(.*?)</main>', value, re.S)[1]
    result = []
    for block in re.findall(r'<details\b[^>]*>(.*?)</details>', main, re.S):
        heading = re.search(r'<summary\b[^>]*>(.*?)</summary>', block, re.S)
        if heading and '?' in plain(heading[1]):
            answer = plain(block[heading.end():])
            assert answer, plain(heading[1])
            result.append({'@type': 'Question', 'name': plain(heading[1]),
                           'acceptedAnswer': {'@type': 'Answer', 'text': answer}})
    return result


def metadata(value: str, route: str, spec: dict, *, sync_faq=False) -> str:
    if spec.get('heading'):
        value = re.sub(r'(<h1\b[^>]*>).*?(</h1>)',
                       lambda m: m[1] + html.escape(spec['heading']) + m[2], value, count=1, flags=re.S)
    value = re.sub(r'(<title>).*?(</title>)',
                   lambda m: m[1] + html.escape(spec['title']) + m[2], value, count=1, flags=re.S)
    for key, content, prop in [
        ('description', spec['description'], False),
        ('og:title', spec['title'], True), ('og:description', spec['description'], True),
        ('og:url', ORIGIN + '/' + route, True),
        ('twitter:title', spec['title'], False), ('twitter:description', spec['description'], False)
    ]:
        value = set_meta(value, key, content, prop=prop)
    if not re.search(r'<link\b[^>]*rel=["\']icon["\']', value):
        value = value.replace('</head>', '<link rel="icon" href="/favicon.svg" type="image/svg+xml"></head>', 1)
    questions = faq_questions(value) if sync_faq else None
    h1 = plain(re.search(r'<h1\b[^>]*>(.*?)</h1>', value, re.S)[1])
    faq_seen = False

    def schema(match):
        nonlocal faq_seen
        document = json.loads(match[2])
        nodes = document.get('@graph', [document]) if isinstance(document, dict) else document
        legal_entity_needed = False

        def entities(node):
            nonlocal legal_entity_needed
            if isinstance(node, list):
                return [entities(child) for child in node]
            if not isinstance(node, dict):
                return node
            if node.get('@type') == 'Organization' and node.get('name') == 'Kansei AB':
                legal_entity_needed = True
                return {'@id': ORIGIN + '/#kansei-ab'}
            if (node.get('@type') == 'Organization'
                    and node.get('@id') == ORIGIN + '/#clinic'):
                return {'@id': ORIGIN + '/#clinic'}
            return {key: entities(child) for key, child in node.items()}

        for node in nodes:
            if not isinstance(node, dict):
                continue
            types = node.get('@type', [])
            types = [types] if isinstance(types, str) else types
            if set(types) & {'WebPage', 'MedicalWebPage', 'CollectionPage'}:
                if node.get('url', '').rstrip('/') == (ORIGIN + '/' + route).rstrip('/'):
                    node['name'] = spec['title']
                    node['description'] = spec['description']
            if 'Article' in types:
                node['headline'] = h1
                node['description'] = spec['description']
            if 'FAQPage' in types and questions is not None:
                node['mainEntity'] = questions
                faq_seen = True
        nodes[:] = [entities(node) if node.get('@id') != ORIGIN + '/#kansei-ab' else node
                    for node in nodes]
        if legal_entity_needed and not any(n.get('@id') == ORIGIN + '/#kansei-ab' for n in nodes):
            nodes.append({'@type': 'Organization', '@id': ORIGIN + '/#kansei-ab',
                          'name': 'Kansei AB', 'url': ORIGIN + '/',
                          'logo': ORIGIN + '/assets/logo-dark.webp'})
        if isinstance(document, dict) and '@graph' in document:
            document['@graph'] = nodes
        elif len(nodes) > 1:
            document = {'@context': 'https://schema.org', '@graph': nodes}
        else:
            document = nodes[0]
        return match[1] + json.dumps(document, ensure_ascii=False, separators=(',', ':')) + match[3]

    value = re.sub(r'(<script\b[^>]*type="application/ld\+json"[^>]*>)(.*?)(</script>)',
                   schema, value, flags=re.S)
    if questions is not None and not faq_seen:
        faq = {'@context': 'https://schema.org', '@type': 'FAQPage',
               '@id': ORIGIN + '/' + route + '#faq', 'mainEntity': questions}
        value = value.replace('</head>', '<script type="application/ld+json">'
                              + json.dumps(faq, ensure_ascii=False, separators=(',', ':'))
                              + '</script></head>', 1)
    return value


# Links answer a symptom question, show a relevant examination, or show the
# clinic's original evidence. They are ordinary crawlable links without scripts.
REGIONS = {
 'axel': ('axeln', [
    ('Ont när du lyfter armen', 'Läs om möjliga orsaker och klinisk bedömning.', '/blogg/ont-i-axeln-nar-du-lyfter-armen/'),
    ('Ont i axeln på natten', 'Besvär vid sömn och sidoliggande.', '/kunskapsbank/axel/ont-i-axeln-pa-natten/'),
    ('Axelsmärta efter ett fall', 'När skadan behöver bedömas och vad som undersöks.', '/blogg/axelsmarta-efter-fall/')]),
 'hoft-ljumske': ('höft och ljumske', [
    ('Ont på utsidan av höften', 'Smärta vid gång eller när du ligger på sidan.', '/blogg/ont-pa-utsidan-av-hoften/'),
    ('Ont i ljumsken', 'Hur muskelfästen och höftleden kan behöva bedömas.', '/blogg/ljumsksmarta-adduktorer-och-hoft/'),
    ('Se vårt höftfall', 'Egna bilder, glutealsenor och kliniska överväganden.', '/ultraljud/glutealsenor/bilder/')]),
 'armbage': ('armbågen', [
    ('Ont på utsidan av armbågen', 'Tennisarmbåge, belastning och nästa steg.', '/blogg/tennisarmbage-behandling-som-fungerar/'),
    ('Ont på insidan av armbågen', 'Läs om golfarmbåge och klinisk undersökning.', '/blogg/golfarmbage-ont-pa-insidan/'),
    ('Se frisk och förändrad sena', 'Kanseis egna ultraljudsbilder med anatomi och fynd.', '/ultraljud/tennisarmbage/bilder/')]),
 'hand-handled': ('hand och handled', [
    ('Ont vid tummen', 'Senor och senskidor vid handledens tumsida.', '/blogg/de-quervain-ont-vid-tummen/'),
    ('En knöl på handleden', 'Ganglion och när en knöl behöver undersökas.', '/blogg/ganglion-knol-pa-handleden/'),
    ('Ultraljud av handledens senor', 'När bilder kan komplettera bedömningen.', '/ultraljud/de-quervain/')]),
 'fot-fotled': ('fot och fotled', [
    ('Ont under hälen', 'Läs om hälsporre, plantarfascia och belastning.', '/blogg/halsporre-plantarfasciit-sa-blir-du-av-med-den/'),
    ('Ont i hälsenan', 'Senbesvär och en plan för återgång till aktivitet.', '/blogg/halsenesmarta-vila-racker-inte/'),
    ('Ont efter en stukad fotled', 'Kvarstående smärta och hur fotleden undersöks.', '/ultraljud/fotledsstukning/')]),
 'lar-muskulatur': ('låret', [
    ('Plötslig smärta i en lårmuskel', 'Läs om muskelbristning och vad som undersöks.', '/blogg/muskelbristning-hur-allvarlig-ar-den/'),
    ('Ont högt på lårets baksida', 'Hamstringsfästet vid sittbenet och metodens gränser.', '/ultraljud/hoft-ljumske/#strukturer'),
    ('Ont ovanför knäskålen', 'Undersökning av quadricepssenan.', '/ultraljud/quadricepssena/')]),
 'overarm': ('överarmen', [
    ('Smärta och blåmärke efter träning', 'Läs hur en misstänkt muskelbristning bedöms.', '/blogg/muskelbristning-hur-allvarlig-ar-den/'),
    ('Ont framtill i axeln', 'Bicepssenan i axeln är en annan del av undersökningen.', '/ultraljud/bicepssena-axel/'),
    ('Bröstmuskelskada vid bänkpress', 'Se vårt bildfall med smärta nära axel och överarm.', '/ultraljud/axel/pectoralisruptur/')]),
 'underarm': ('underarmen', [
    ('Ont vid grepp och lyft', 'När besvären sitter vid senfästet på armbågens utsida.', '/ultraljud/tennisarmbage/'),
    ('Belastningssmärta i armen', 'Läs om musarm, funktion och anpassad belastning.', '/blogg/musarm-nar-armen-sager-ifran/'),
    ('Ont närmare handleden', 'Undersökning av handens och handledens mjukdelar.', '/ultraljud/hand-handled/')]),
 'underben': ('vad och underben', [
    ('Misstänkt bristning i vaden', 'När ett riktat muskelultraljud kan tillföra något.', '/ultraljud/muskelbristning/'),
    ('Smärta längs underbenet', 'Läs om belastningsbesvär och klinisk bedömning.', '/blogg/benhinneinflammation-loparens-vanligaste-stopp/'),
    ('Ont längre ned i hälsenan', 'Hälsenan och vadmuskeln ger olika frågeställningar.', '/ultraljud/halsena/')])
}

REGION_COPY = {
 'underarm': ('Strukturer i underarm', 'Ont i underarmen – vad kan undersökas?',
     'Frågeställningen styr', 'Smärta vid grepp, vridning eller träning?',
     'Flexor- och extensormuskulatur, senor, myotendinösa övergångar och ytliga nerver.',
     'Vid lokal smärta i underarmen kan vi undersöka tillgängliga böj- och sträckmuskler, senor och övergångar mellan muskel och sena. Besvärens läge och den kliniska undersökningen styr vad vi tittar på.'),
 'overarm': ('Strukturer i överarm', 'Ont i överarmen efter belastning eller skada',
     'Frågeställningen styr', 'När kan ett riktat ultraljud tillföra något?',
     'Biceps- och tricepsmuskulatur, myotendinösa övergångar och ytliga mjukdelar.',
     'Smärta i biceps, triceps eller en lokal svullnad efter träning kan ge en fråga om muskelbristning, blödning eller övergången mellan muskel och sena. Vi avgränsar undersökningen efter hur besvären började och var de sitter.'),
 'lar-muskulatur': ('Strukturer i lår &amp; muskulatur', 'Smärta i lårets fram- eller baksida',
     'Frågeställningen styr', 'Plötslig sträckning eller kvarstående muskelsmärta?',
     'Quadriceps, hamstrings, adduktorer, muskelfascior och myotendinösa övergångar.',
     'Vid en misstänkt muskelbristning i låret bedömer vi tillgängliga delar av quadriceps, hamstrings eller adduktorer. Vi följer också övergången mellan muskel och sena när den är relevant för dina besvär.'),
 'underben': ('Strukturer i underben', 'Ont i vaden efter en muskelskada',
     'Frågeställningen styr', 'Vadsmärta som behöver en riktad bedömning',
     'Vadmuskel, soleus, myotendinösa övergångar, ytliga senor och lokala mjukdelar.',
     'Ultraljud av vad och underben kan komplettera bedömningen vid misstänkt muskelbristning, lokal blödning eller kvarstående besvär efter en muskelskada. Gastrocnemius, soleus och tillgängliga senor undersöks utifrån frågeställningen.')
}

REGION_FAQS = {
 'underarm': [
    ('Vad kan ultraljud visa vid ont i underarmen?', 'Tillgängliga muskler, senor och övergångar mellan muskel och sena kan bedömas vid en riktad fråga. Smärtans läge, rörelser som provocerar och den kliniska undersökningen avgör vilka strukturer som är relevanta.'),
    ('Kan besvären komma från armbågen eller handleden?', 'Ja. Underarmens muskler fortsätter i senor mot armbåge och handled. Undersökningen kan därför behöva riktas mot ett senfäste eller en sena utanför själva muskelbuken.'),
    ('Vad kostar ultraljud av underarmen i Stockholm?', 'Hos Kansei vid Odenplan kostar besöket 1 290 kr och tar 45 minuter. Klinisk undersökning, riktat ultraljud, genomgång av fynden och rekommendation om nästa steg ingår. Ingen remiss behövs.')],
 'overarm': [
    ('Kan en bristning i biceps eller triceps ses med ultraljud?', 'Många tillgängliga muskelskador, vätskeansamlingar och skador i övergången mellan muskel och sena kan bedömas. Djupa eller omfattande skador kan behöva annan bilddiagnostik. Bilderna vägs mot styrka och funktion.'),
    ('Är ultraljud av överarmen samma undersökning som av axeln?', 'Frågeställningen skiljer sig. I överarmen undersöks främst muskelbukar och övergångar till sena. Bicepssenans övre del bedöms vid axeln och det nedre fästet vid armbågen.'),
    ('Kan jag boka ultraljud av överarmen utan remiss?', 'Ja. Du bokar direkt hos Kansei vid Odenplan i Stockholm. Besöket tar 45 minuter och kostar 1 290 kr. Klinisk undersökning och genomgång av fynden ingår.')],
 'lar-muskulatur': [
    ('Kan ultraljud användas vid en muskelbristning i låret?', 'Ja, vid en riktad fråga om en tillgänglig muskelskada kan ultraljud ge information om muskelfibrer, vätska och blödning. Djupa eller omfattande skador kan kräva MR eller annan medicinsk bedömning.'),
    ('Avgör ultraljudet när jag kan börja springa igen?', 'Nej. Bildfynd kan bidra med information, men styrka, funktion, belastningstolerans och hur besvären utvecklas behöver också bedömas innan återgång till träning.'),
    ('Vad ingår i ultraljud av låret hos Kansei?', 'Besöket omfattar klinisk undersökning, riktat ultraljud, genomgång av fynden och rekommendation om nästa steg. Det tar 45 minuter och kostar 1 290 kr. Du bokar vid Odenplan i Stockholm utan remiss.')],
 'underben': [
    ('Kan ultraljud visa en bristning i vadmuskeln?', 'Tillgängliga delar av gastrocnemius, soleus och övergången mellan muskel och sena kan undersökas vid en riktad fråga. Skadans djup och omfattning kan begränsa vad som går att bedöma.'),
    ('Är detta en undersökning för blodpropp i vaden?', 'Nej. Kanseis muskuloskeletala ultraljud ersätter inte kärlultraljud eller medicinsk utredning vid misstänkt blodpropp. Nytillkommen ensidig vadsvullnad eller andra symtom som väcker sådan misstanke ska bedömas av sjukvården.'),
    ('Vad kostar ultraljud av vad och underben?', 'Hos Kansei vid Odenplan i Stockholm kostar besöket 1 290 kr och tar 45 minuter. Klinisk undersökning, riktat ultraljud, genomgång av fynden och råd om nästa steg ingår. Ingen remiss behövs.')]
}


def symptom_links(items):
    return '<div class="us-search-paths"><h3>Utgå från dina besvär</h3><div class="us-symptom-links">' + ''.join(
        f'<a href="{url}"><strong>{html.escape(title)}</strong><span>{html.escape(description)}</span></a>'
        for title, description, url in items) + '</div></div>'


def region_page(key: str):
    path = f'ultraljud/{key}/index.html'
    value = (ROOT / path).read_text()
    area, items = REGIONS[key]
    if key in REGION_COPY:
        old, new, old_side, new_side, old_p, new_p = REGION_COPY[key]
        value = value.replace(old, html.escape(new), 1).replace(old_side, html.escape(new_side), 1)
        value = value.replace(old_p, html.escape(new_p), 1)
    if 'class="us-search-paths"' not in value:
        pattern = r'(<section\b[^>]*\bid="bedomning"[^>]*>)(.*?)(</section>)'
        value, count = re.subn(pattern, lambda m: m[1] + m[2] + symptom_links(items) + m[3], value, count=1, flags=re.S)
        assert count == 1, path
    blocks = ''
    if key in REGION_FAQS and 'id="faq"' not in value:
        blocks += '<section class="section us-search-faq" id="faq" data-reading-section data-reading-title="Vanliga frågor"><h2>Vanliga frågor inför undersökningen</h2>'
        blocks += ''.join(f'<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>' for q, a in REGION_FAQS[key])
        blocks += '</section>'
    if key != 'axel' and 'id="boka-ultraljud"' not in value:
        blocks += f'<section class="section us-booking-next" id="boka-ultraljud" data-reading-section data-reading-title="Pris och bokning"><p class="eyebrow">KANSEI · ODENPLAN, STOCKHOLM</p><h2>Få dina besvär i {area} undersökta.</h2><p>Klinisk undersökning, riktat ultraljud och genomgång av fynden vid samma besök. Du får råd om nästa steg och behöver ingen remiss.</p><p><strong>1 290 kr · 45 minuter</strong><br>Upplandsgatan 26, Odenplan. På Bokadirekt väljer du ”Ultraljud av rörelseapparaten”.</p><div class="us-booking-actions"><a class="button button-dark" href="{BOOK}" target="_blank" rel="noopener noreferrer" data-measure="booking_click">Boka ultraljud av {area} →</a><a class="text-link" href="/hjalp-mig-boka/">Hjälp mig välja besök →</a></div></section>'
    if blocks:
        value, count = re.subn(r'(?=<section\b[^>]*\bid="fler-omraden")', lambda m: blocks, value, count=1)
        assert count == 1, path
    # Keep static chapter labels aligned with the existing reading navigation.
    chapter = 0

    def renumber(match):
        nonlocal chapter
        chapter += 1
        content = re.sub(r'(<h2\b[^>]*>)(?:<span\b[^>]*class="reading-chapter-number"[^>]*>.*?</span>)?',
                         lambda m: m[1] + f'<span class="reading-chapter-number" aria-hidden="true">{chapter:02}</span>',
                         match[2], count=1, flags=re.S)
        return match[1] + content + match[3]
    value = re.sub(r'(<section\b[^>]*\bdata-reading-section[^>]*>)(.*?)(</section>)', renumber, value, flags=re.S)
    for label, anchor in [('Vanliga frågor', '#faq'), ('Pris och bokning', '#boka-ultraljud')]:
        if anchor == '#faq' and key not in REGION_FAQS:
            continue
        if anchor == '#boka-ultraljud' and key == 'axel':
            continue
        if f'href="{anchor}"' not in value:
            value = re.sub(r'(?=<a\b[^>]*href="#fler-omraden")', f'<a href="{anchor}">{label}</a>', value, count=1)
    save(path, add_css(value))


def new_guide():
    path = GUIDE.lstrip('/') + 'index.html'
    value = (ROOT / 'kunskapsbank/kna/ont-i-knat-i-trappor/index.html').read_text()
    main = (CONTENT / 'knee-lateral-pain.20261022.html.in').read_text().strip()
    value = re.sub(r'<main\b[^>]*>.*?</main>', lambda m: main, value, count=1, flags=re.S)
    value = value.replace(ORIGIN + '/kunskapsbank/kna/ont-i-knat-i-trappor/', ORIGIN + GUIDE)
    page_schema = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'MedicalWebPage', '@id': ORIGIN + GUIDE + '#webpage', 'url': ORIGIN + GUIDE,
         'name': 'Ont på utsidan av knät – vad kan det bero på?', 'inLanguage': 'sv-SE',
         'datePublished': DAY, 'dateModified': DAY,
         'author': {'@id': ORIGIN + '/team/carl-robert-karell/#person'},
         'isPartOf': {'@id': ORIGIN + '/#website'}, 'breadcrumb': {'@id': ORIGIN + GUIDE + '#breadcrumb'},
         'about': {'@type': 'MedicalCondition', 'name': 'Knäsmärta'}},
        {'@type': 'Person', '@id': ORIGIN + '/team/carl-robert-karell/#person',
         'name': 'Carl-Robert Kårell', 'jobTitle': 'Legitimerad naprapat',
         'url': ORIGIN + '/team/carl-robert-karell/'},
        {'@type': 'BreadcrumbList', '@id': ORIGIN + GUIDE + '#breadcrumb', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': title, 'item': ORIGIN + url}
            for i, (title, url) in enumerate([('Kansei', '/'), ('Kunskapsbanken', '/kunskapsbank/'),
                                            ('Knä', '/kunskapsbank/kna/'), ('Ont på utsidan av knät', GUIDE)])]}
    ]}
    value = value.replace('</head>', '<script type="application/ld+json">'
                          + json.dumps(page_schema, ensure_ascii=False) + '</script></head>', 1)
    spec = {'title': 'Ont på utsidan av knät – orsaker och bedömning | Kansei',
            'description': 'Ont på utsidan av knät när du springer, går eller böjer benet? Läs om möjliga orsaker, vad ultraljud kan visa och bedömning hos Kansei i Stockholm.'}
    save(path, metadata(add_css(value), GUIDE.lstrip('/'), spec, sync_faq=True))


def link_guide():
    path = 'ultraljud/kna/index.html'
    value = (ROOT / path).read_text()
    if f'href="{GUIDE}"' not in value:
        marker = '<div class="knee-symptoms">'
        card = f'<a href="{GUIDE}"><strong>Ont på utsidan av knät</strong><span>Löpning, vridning och andra möjliga förklaringar.</span></a>'
        value = value.replace(marker, marker + card, 1)
        assert card in value
    save(path, value)
    path = 'ultraljud/loparkna/index.html'
    value = (ROOT / path).read_text()
    if f'href="{GUIDE}"' not in value:
        paragraph = f'<p class="knee-small">Vill du börja med symtomen? Läs guiden <a href="{GUIDE}">ont på utsidan av knät – löpning, skada och nästa steg</a>. Här nedan förklarar vi våra undersökningsbilder.</p>'
        value, count = re.subn(r'(<section\b[^>]*\bid="igenkanning"[^>]*>.*?)(</section>)',
                              lambda m: m[1] + paragraph + m[2], value, count=1, flags=re.S)
        assert count == 1
    save(path, value)

    path = 'kunskapsbank/kna/index.html'
    value = (ROOT / path).read_text()
    if f'href="{GUIDE}"' not in value:
        card = f'<a class="hub-guide" href="{GUIDE}"><span class="eyebrow">GUIDE / KNÄ</span><h3>Ont på utsidan av knät</h3><p>Löprelaterad smärta, besvär efter en vridning och när ultraljud kan tillföra något.</p><span class="reading-cta">Läs guiden →</span></a>'
        value = value.replace('<div class="hub-grid">', '<div class="hub-grid">' + card, 1)
        value = value.replace('9 guider', '10 guider', 1)
    save(path, value)
    path = 'kunskapsbank/index.html'
    value = (ROOT / path).read_text()
    if f'href="{GUIDE}"' not in value:
        card = f'<article class="knowledge-result" data-category="Knä &amp; höft" data-library-card data-search="Ont på utsidan av knät löparknä löpning vridning undersökning ultraljud"><span class="eyebrow">Knä &amp; höft</span><h2><a href="{GUIDE}">Ont på utsidan av knät – vad kan det bero på?</a></h2><p>Så skiljer sig frågor om löparknä, skada och svullnad. Läs om klinisk bedömning och vad ultraljud kan tillföra.</p><span aria-hidden="true" class="read-more">Läs artikeln ↗</span></article>'
        value, count = re.subn(r'(?=<article\b[^>]*class="knowledge-result")', lambda m: card, value, count=1)
        assert count == 1
    save(path, value)
    path = 'blogg/loparkna-eller-hopparkna/index.html'
    value = (ROOT / path).read_text()
    if f'href="{GUIDE}"' not in value:
        paragraph = f'<p>Smärta på utsidan behöver inte alltid vara löparknä. Läs vår guide om <a href="{GUIDE}">ont på utsidan av knät vid löpning, efter en skada eller tillsammans med svullnad</a>.</p>'
        value, count = re.subn(r'(<h2\b[^>]*>Löparknä: smärta på knäts utsida</h2>)', lambda m: m[1] + paragraph, value, count=1)
        assert count == 1
    value = value.replace('Text uppdaterad 14 oktober 2026', 'Text uppdaterad 22 oktober 2026', 1)
    save(path, value)


def hub():
    path = 'ultraljud/index.html'
    value = (ROOT / path).read_text()
    names = {
        '/ultraljud/halsena/': ('Ont i hälsenan', 'Stelhet och smärta bakom hälen vid belastning'),
        '/ultraljud/tennisarmbage/': ('Ont på utsidan av armbågen', 'Senfästet vid smärta när du greppar eller lyfter'),
        '/ultraljud/plantarfascia/': ('Ont under hälen – hälsporre', 'När plantarfascian kan behöva undersökas'),
        '/ultraljud/glutealsenor/': ('Ont på utsidan av höften', 'Senfästen och slemsäckar kring höften'),
        '/ultraljud/patellarsena/': ('Ont under knäskålen – hopparknä', 'Undersökning av patellarsenan vid belastningsbesvär'),
        '/ultraljud/de-quervain/': ('Ont vid tummen och handleden', 'Tummens senor och senskidor')
    }

    def label(match):
        attrs = Fragment(match[0]).attrs
        if attrs.get('href') not in names:
            return match[0]
        title, detail = names[attrs['href']]
        link = re.sub(r'<strong>.*?</strong>', f'<strong>{html.escape(title)}</strong>', match[0], count=1, flags=re.S)
        return re.sub(r'<small>.*?</small>', f'<small>{html.escape(detail)}</small>', link, count=1, flags=re.S)
    value = re.sub(r'<a\b[^>]*class="hub-directory-link"[^>]*>.*?</a>', label, value, flags=re.S)
    if f'href="{GUIDE}"' not in value:
        card = f'<a class="hub-directory-link" href="{GUIDE}"><span><strong>Ont på utsidan av knät</strong><small>Löpning, skada och hur du väljer nästa steg</small></span><span class="tag">Knä</span><svg class="icon" aria-hidden="true"><use href="#i-arrow"></use></svg></a>'
        value, count = re.subn(r'(Sök utifrån vanliga besvär.*?<div class="hub-directory-grid">)', lambda m: m[1] + card, value, count=1, flags=re.S)
        assert count == 1
    question = 'Är diagnostiskt ultraljud samma sak som ultraljudsbehandling?'
    if question not in value:
        faq = f'<details><summary>{question}</summary><p>Hos Kansei använder vi diagnostiskt ultraljud för att undersöka muskler, senor, leder och vissa ytliga nerver. Du får bilderna förklarade och en klinisk bedömning. Ultraljudsbehandling är en annan användning av ljudvågor; besöket som beskrivs här är en undersökning.</p></details>'
        value, count = re.subn(r'(<div class="hub-faq-list">)(.*?)(</div>)', lambda m: m[1] + m[2] + faq + m[3], value, count=1, flags=re.S)
        assert count == 1
    save(path, value)
    path = 'ultraljud/bilder/index.html'
    value = (ROOT / path).read_text()
    value = value.replace('href="/ultraljud/#boka-cta">Boka ultraljud →', f'href="{BOOK}" target="_blank" rel="noopener noreferrer" data-measure="booking_click">Boka ultraljud →', 1)
    if 'class="atlas-booking-note"' not in value:
        value = value.replace('<ul class="atlas-feature-list">', '<p class="atlas-booking-note">Ultraljud vid Odenplan i Stockholm · 1 290 kr, 45 minuter · Utan remiss.</p><ul class="atlas-feature-list">', 1)
    save(path, add_css(value))


def sitemap():
    path = 'sitemap.xml'
    value = (ROOT / path).read_text()
    changed_urls = {ORIGIN + '/' + p[:-len('index.html')] for p in CHANGED if p.endswith('/index.html')}

    def lastmod(match):
        loc = html.unescape(re.search(r'<loc>(.*?)</loc>', match[0], re.S)[1])
        if loc in changed_urls:
            if '<lastmod>' in match[0]:
                return re.sub(r'<lastmod>.*?</lastmod>', f'<lastmod>{DAY}</lastmod>', match[0], count=1)
            return match[0].replace('</loc>', f'</loc><lastmod>{DAY}</lastmod>', 1)
        return match[0]
    value = re.sub(r'<url>.*?</url>', lastmod, value, flags=re.S)
    if f'<loc>{ORIGIN}{GUIDE}</loc>' not in value:
        value = value.replace('</urlset>', f'  <url><loc>{ORIGIN}{GUIDE}</loc><lastmod>{DAY}</lastmod></url>\n</urlset>', 1)
    save(path, value)


def run():
    specs = json.loads((CONTENT / 'ultrasound-search-intent.20261022.json').read_text())
    assert len(specs) == 40
    new_guide()
    for key in REGIONS:
        region_page(key)
    link_guide()
    hub()
    faq_routes = {'ultraljud/', *{f'ultraljud/{key}/' for key in REGION_FAQS}}
    for route, spec in specs.items():
        path = route + 'index.html'
        save(path, metadata((ROOT / path).read_text(), route, spec, sync_faq=route in faq_routes))
    sitemap()
    print(json.dumps({'changed_files': sorted(CHANGED), 'reviewed_ultrasound_pages': len(specs)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    run()
