"""Publish reviewed case context as crawlable HTML, preserving the clinical media.

This is a one-time content migration from the recorded base revision. It reads
the case-specific editorial data; it never rewrites images, films or prices.
"""
from pathlib import Path
import hashlib
import html
import json
import re

ROOT = Path(__file__).resolve().parents[2]
DATA = json.loads((ROOT/'.github/kansei/content/ultrasound-cases.20261016.json').read_text())
CASES = DATA['cases']
BY_KEY = {c['key']: c for c in CASES}
CSS = '/assets/ultrasound-case-guide.20261016.css'
US_BOOK = 'https://www.bokadirekt.se/boka-tjanst/kansei-rehabcenter-48847/ultraljud-rorelseapparaten-1946824'


def esc(value):
    return html.escape(value, quote=True)


def attach_css(source):
    if CSS not in source:
        source = source.replace('</head>', f'<link rel="stylesheet" href="{CSS}"/></head>', 1)
    return source


def linked(text, url, extra=''):
    if url == US_BOOK:
        extra += ' data-measure="booking_click"'
    return f'<a href="{esc(url)}"{extra}>{esc(text)} →</a>'


def media_link(c):
    tab, text = c['media']
    attrs = ' data-case-view data-case-findings="true"'
    if tab:
        attrs += f' data-case-tab="{esc(tab)}"'
    return linked(text, '#bilder', attrs)


def summary(c):
    goals = ''.join(f'<li>{esc(t)}</li>' for t in c['recognition'])
    return f'''<section class="us-case-guide case-context-summary" id="igenkanning" aria-labelledby="igenkanning-title" data-case-context="summary"><div class="wrap"><div class="case-context-columns"><div><span class="eyebrow">Känner du igen besväret?</span><h2 id="igenkanning-title">{esc(c['headline'])}</h2><p>{esc(c['summary'])}</p><ul class="case-context-goals" aria-label="Rörelser och aktiviteter i fokus">{goals}</ul></div><aside class="case-context-question"><p class="case-context-kind">{esc(c['kind'])}</p><h3>Frågan vi vill besvara</h3><p>{esc(c['question'])}</p><div class="case-context-links">{linked('Följ patientfallet', '#'+c['story'])}{linked('Se bilder och fynd', '#bilder')}</div></aside></div></div></section>'''


def decision(c):
    related = ''.join(f'<article>{linked(BY_KEY[k]["headline"], BY_KEY[k]["path"])}<p>{esc(note)}</p></article>' for k, note in c['related'])
    faq = ''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in c['faq'])
    care = f'''<article><h3>Få området undersökt</h3><p>Vid en särskild fråga om en sena, nerv, slemsäck eller ledvätska kan du boka riktat ultraljud hos Kansei vid Odenplan. Du får fynden förklarade och en rekommendation om nästa steg.</p>{linked('Boka ultraljud', US_BOOK, ' target="_blank" rel="noopener noreferrer"')}</article><article><h3>Funktion och rehabilitering</h3><p>{esc(c['naprapati'])}</p>{linked('Naprapati vid Odenplan – undersökning och plan', '/naprapati/')}</article>'''
    if c['key'] == 'kna':
        care += f'''<article><h3>Hyaluron vid knäartros</h3><p>Vid kvarstående artrosrelaterad smärta kan hyaluron vara ett komplement. Läs om möjlig symtomlindring, forskningsläget, behandlingen och priser. Du kan boka injektion direkt eller välja konsultation om du är osäker.</p>{linked('Hyaluron i knä – behandling och bokning', '/hyaluronsyra/kna/')}</article>'''
    # The label describes planned evaluation, never an invented treatment result.
    follow = c['follow'].split('. ')[0].rstrip('.')+'.'
    return f'''<section class="us-case-guide case-context-decision" id="nasta-steg" aria-labelledby="case-key-title" data-case-context="decision"><div class="wrap"><div class="case-context-key" id="klinisk-nyckel"><span class="eyebrow">Det viktiga i just det här fallet</span><h2 id="case-key-title">{esc(c['key_title'])}</h2><p>{esc(c['key_text'])}</p><p>{esc(c['implication'])}</p><div class="case-context-links">{media_link(c)}</div><p class="case-context-follow"><strong>Uppföljningens fokus:</strong> {esc(follow)}</p></div><h3>Vilket nästa steg passar ditt besvär?</h3><div class="case-context-care" data-care-count="{3 if c['key']=='kna' else 2}">{care}</div><div class="case-context-faq"><h3>Frågor om bildfallet</h3>{faq}</div><h3>Jämför med andra undersökningsfall</h3><div class="case-context-related">{related}</div><div class="case-context-links">{linked('Alla fall – sök efter ditt besvär', '/ultraljud/bilder/')}{linked('Vad ingår i ett ultraljudsbesök?', '/ultraljud/')}</div><p class="case-context-source">Undersökningsbilder: {linked('Carl-Robert Kårell, legitimerad naprapat', '/team/carl-robert-karell/')} · Kansei, Upplandsgatan 26 i Stockholm. {esc(c['kind'])}. Bildgenomgång och förklaringar uppdaterade 16 oktober 2026.</p></div></section>'''


def replace_schema(source, c):
    pattern = r'(<script\b[^>]*type="application/ld\+json"[^>]*>)(.*?)(</script>)'
    found = False
    def update(match):
        nonlocal found
        data = json.loads(match[2])
        graph = data.get('@graph') if isinstance(data, dict) else None
        if not graph or found:
            return match[0]
        webpage = next((x for x in graph if x.get('@type') in ('MedicalWebPage', 'WebPage')), None)
        if webpage is None:
            return match[0]
        found = True
        url = 'https://www.kansei.se'+c['path']
        webpage['description'] = c['description']
        webpage['dateModified'] = DATA['updated']
        # No new medical-review attribution or invented publication date.
        parts = webpage.setdefault('hasPart', [])
        if isinstance(parts, dict): parts = [parts]; webpage['hasPart'] = parts
        parts.extend({'@id': url+'#'+ident} for ident in ('igenkanning', 'klinisk-nyckel', 'nasta-steg'))
        graph.extend([
            {'@type': 'WebPageElement', '@id': url+'#igenkanning', 'name': c['headline'], 'text': c['summary']+' '+c['question']},
            {'@type': 'WebPageElement', '@id': url+'#klinisk-nyckel', 'name': c['key_title'], 'text': c['key_text']+' '+c['implication']},
            {'@type': 'WebPageElement', '@id': url+'#nasta-steg', 'name': 'Från undersökningsfynd till nästa steg', 'isPartOf': {'@id': webpage.get('@id', url+'#webpage')}}
        ])
        questions = [{'@type':'Question', 'name':q, 'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in c['faq']]
        faq = next((x for x in graph if x.get('@type')=='FAQPage'), None)
        if faq:
            existing = faq.setdefault('mainEntity', [])
            names = {q.get('name') for q in existing}
            existing.extend(q for q in questions if q['name'] not in names)
        else:
            graph.append({'@type':'FAQPage', '@id':url+'#case-questions', 'mainEntity':questions})
        return match[1]+json.dumps(data, ensure_ascii=False, separators=(',', ':'))+match[3]
    source = re.sub(pattern, update, source, flags=re.S)
    assert found, 'Structured page entity missing: '+c['path']
    return source


def update_case(c):
    path = ROOT/c['path'].strip('/')/'index.html'
    source = path.read_text()
    assert 'data-case-context=' not in source, 'Migration already applied'
    # Clinical raster/video sources and reader markup are preserved verbatim.
    media_before = re.findall(r'<(?:img|video|source)\b[^>]*>', source)
    source = attach_css(source)
    marker = re.search(r'<section\b[^>]*\bid="bilder"[^>]*>', source)
    assert marker, 'Reader missing: '+c['path']
    source = source[:marker.start()] + summary(c) + '\n' + source[marker.start():]
    # Keep the existing patient narrative; place the clinical key directly after it.
    story = re.search(r'<section\b[^>]*\bid="'+c['story']+r'"[^>]*>.*?</section>', source, re.S)
    assert story
    source = source[:story.end()]+'\n'+decision(c)+'\n'+source[story.end():]
    if 'class="case-page-nav"' in source:
        nav = re.search(r'<nav\b[^>]*class="case-page-nav"[^>]*>.*?</nav>', source, re.S)
        assert nav
        contents = nav[0].replace('</nav>', '<a href="#igenkanning">Känner du igen dig?</a><a href="#nasta-steg">Från fynd till hjälp</a></nav>')
        source = source[:nav.start()]+contents+source[nav.end():]
    if '/assets/ultrasound-case-path.20261015.js' not in source:
        source = source.replace('</body>', '<script defer src="/assets/ultrasound-case-path.20261015.js"></script></body>')
    source = re.sub(r'(<meta\b[^>]*(?:name="description"|property="og:description"|name="twitter:description")[^>]*content=")[^"]*(")', lambda m:m[1]+esc(c['description'])+m[2], source)
    source = replace_schema(source, c)
    assert re.findall(r'<(?:img|video|source)\b[^>]*>', source) == media_before
    path.write_text(source)
    return str(path.relative_to(ROOT))


if __name__ == '__main__':
    files = [update_case(c) for c in CASES]
    print(json.dumps({'cases':len(files), 'files':files}, ensure_ascii=False))
