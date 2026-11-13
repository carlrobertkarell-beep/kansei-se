"""Build the header search index from Kansei's canonical public pages."""

from argparse import ArgumentParser
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'assets/site-search-index.20261113.json'
ORIGIN = 'https://www.kansei.se'
SITEMAP_NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'

# Put the usual patient destinations first when results are equally relevant.
PATIENT_ROUTES = {
    '/hjalp-mig-boka/': ('Hitta rätt besök', 'boka', 'boka tid', 'bokning', 'välja besök', 'bokadirekt'),
    '/ultraljud/': ('Diagnostiskt ultraljud i Stockholm', 'ultraljud', 'sonografi', 'msk-ultraljud', 'ultrasound'),
    '/ultraljud/axel/': ('Ultraljud av axeln', 'ultraljud axel', 'axelultraljud', 'shoulder ultrasound'),
    '/ultraljud/kna/': ('Ultraljud av knät', 'ultraljud knä', 'knäultraljud', 'knee ultrasound'),
    '/ultraljud/hoft-ljumske/': ('Ultraljud av höft och ljumske', 'ultraljud höft', 'ultraljud ljumske', 'hip ultrasound'),
    '/hyaluronsyra/': ('Hyaluroninjektion i Stockholm', 'hyaluron', 'hyaluronsyra', 'viskosupplementering', 'hyaluronic acid'),
    '/hyaluronsyra/kna/': ('Hyaluroninjektion i knät', 'hyaluron knä', 'hyaluronsyra knä', 'knäartros', 'knee hyaluronic acid'),
    '/hyaluronsyra/hoft/': ('Hyaluroninjektion i höften', 'hyaluron höft', 'hyaluronsyra höft', 'höftartros', 'hip hyaluronic acid'),
    '/hyaluronsyra/axel/': ('Hyaluroninjektion i axeln', 'hyaluron axel', 'hyaluronsyra axel', 'axelartros', 'shoulder hyaluronic acid'),
    '/naprapati/': ('Naprapat vid Odenplan', 'naprapati', 'naprapathy', 'nacke', 'rygg', 'vasastan'),
    '/rehabilitering/': ('Rehabilitering', 'rehab', 'träningsplan', 'rehabilitation'),
    '/prp/': ('PRP-behandling i Stockholm', 'prp', 'acp', 'blodplättar', 'platelet rich plasma'),
    '/injektioner/': ('Injektioner med hyaluron och PRP', 'ledinjektion', 'injektioner', 'injektion'),
    '/kortison/': ('Kortisoninjektion i axeln', 'kortison', 'steroidinjektion', 'cortisone'),
    '/kontakt/': ('Kontakt och vägbeskrivning', 'kontakt', 'hitta hit', 'adress', 'telefon', 'mejl', 'contact', 'directions'),
    '/priser/': ('Prislista', 'pris', 'priser', 'kostnad', 'price', 'prices'),
    '/patientinformation/': ('Patientinformation', 'inför besöket', 'avbokning', 'ombokning', 'patientförsäkring', 'journal'),
    '/fragor-och-svar/': ('Vanliga frågor', 'frågor och svar', 'faq', 'öppettider', 'remiss', 'försäkring'),
    '/om-oss/': ('Kliniken vid Odenplan', 'om oss', 'om kansei', 'klinik', 'about'),
    '/kunskapsbank/': ('Kunskapsbanken', 'kunskapsbank', 'guider', 'artiklar'),
    '/kunskapsbank/axel/': ('Guider om axelbesvär', 'axel', 'skuldra', 'shoulder', 'ont i axeln', 'axelsmärta'),
    '/kunskapsbank/kna/': ('Guider om knäbesvär', 'knä', 'knee', 'ont i knät', 'knäsmärta'),
    '/ultraljud/bilder/': ('Ultraljud i bild', 'ultraljudsbilder', 'patientfall', 'ultraljudsfall', 'atlas'),
    '/en/': ('Kansei in English', 'english', 'engelska', 'naprapathy', 'ultrasound', 'sports injury'),
}


def tidy(value):
    return ' '.join(value.split())


class SearchPage(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = []
        self.meta = {}
        self.canonical = ''
        self.in_title = False
        self.cards = {}
        self.card_keywords = None

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if tag == 'title':
            self.in_title = True
        if tag == 'meta':
            if attrs.get('http-equiv', '').lower() == 'refresh':
                self.meta['refresh'] = True
            name = attrs.get('name', '').lower()
            if name:
                self.meta[name] = attrs.get('content', '')
        if tag == 'link' and 'canonical' in attrs.get('rel', '').lower().split():
            self.canonical = attrs.get('href', '')
        if tag == 'article' and 'data-library-card' in attrs:
            self.card_keywords = attrs.get('data-search', '')
        if tag == 'a' and self.card_keywords is not None:
            self.cards[attrs.get('href', '')] = self.card_keywords
            self.card_keywords = None

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'article':
            self.card_keywords = None

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)


def public_page(path):
    source = ROOT / path.strip('/') / 'index.html'
    page = SearchPage()
    page.feed(source.read_text(encoding='utf-8'))
    page.close()
    robots = re.split(r'[,\s]+', page.meta.get('robots', '').lower())
    if page.canonical != ORIGIN + path or 'noindex' in robots or page.meta.get('refresh'):
        raise ValueError(f'Noncanonical or unlisted page in sitemap: {path}')
    return page


def words(value):
    return re.findall(r'[^\W_]+', value.casefold())


def normalized(value):
    return ''.join(char for char in unicodedata.normalize('NFD', value) if not unicodedata.combining(char))


def collect_keywords(page, custom, card, title, description):
    supplied = [tidy(term) for term in page.meta.get('keywords', '').split(',') if term.strip()]
    known = set(words(normalized(title + ' ' + description)))
    card_terms = [term for term in words(card) if len(term) >= 3 and normalized(term) not in known]
    return list(dict.fromkeys((*custom, *supplied, *card_terms)))


def build_index():
    nodes = ElementTree.parse(ROOT / 'sitemap.xml').findall(f'.//{{{SITEMAP_NS}}}loc')
    entries = []
    seen = set()
    cards = public_page('/kunskapsbank/').cards
    priority = {path: index for index, path in enumerate(PATIENT_ROUTES)}

    for node in nodes:
        url = urlsplit(node.text.strip())
        path = url.path
        if url.scheme != 'https' or url.netloc != 'www.kansei.se' or url.query or url.fragment:
            raise ValueError(f'Unexpected sitemap URL: {node.text}')
        if not path.endswith('/') or path in seen or any(part in ('.', '..') for part in path.split('/')):
            raise ValueError(f'Unexpected or repeated sitemap path: {path}')
        seen.add(path)
        page = public_page(path)
        seo_title = tidy(''.join(page.title)).split(' | Kansei', 1)[0]
        description = tidy(page.meta.get('description', ''))
        title, *custom = PATIENT_ROUTES.get(path, (seo_title,))
        if not title or not description:
            raise ValueError(f'Missing search result title or description: {path}')
        entries.append({
            'path': path,
            'title': title,
            'description': description,
            'keywords': collect_keywords(page, custom, cards.get(path, ''), title, description),
        })

    return sorted(entries, key=lambda row: priority.get(row['path'], len(priority)))


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify that the checked-in index is up to date')
    args = parser.parse_args()
    entries = build_index()
    lines = (json.dumps(entry, ensure_ascii=False, separators=(',', ':')) for entry in entries)
    content = '[\n' + ',\n'.join(lines) + '\n]\n'
    if args.check:
        if OUTPUT.read_text(encoding='utf-8') != content:
            raise SystemExit('Search index is stale. Run python3 .github/kansei/build_site_search_index.py')
    else:
        OUTPUT.write_text(content, encoding='utf-8')
    print(f'{len(entries)} canonical search results, {len(content.encode("utf-8")):,} bytes')


if __name__ == '__main__':
    main()
