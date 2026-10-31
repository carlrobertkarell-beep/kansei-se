#!/usr/bin/env python3
"""Verify that every marked-up film has an accessible, video-first watch page."""
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = 'https://www.kansei.se'
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9',
      'v': 'http://www.google.com/schemas/sitemap-video/1.1'}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


def objects(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from objects(item)
    elif isinstance(value, list):
        for item in value:
            yield from objects(item)


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.canonicals = []
        self.robots = ''
        self.videos = []
        self.links = []
        self.blocks = []
        self.buffer = None
        self.watch = False
        self.sequence = 0
        self.first_h2 = float('inf')
        self.feed(text)

    def hidden(self):
        return any('hidden' in a or 'inert' in a or a.get('aria-hidden') == 'true'
                   or (tag == 'details' and 'open' not in a)
                   or re.search(r'(?:display\s*:\s*none|visibility\s*:\s*hidden)', a.get('style', ''), re.I)
                   for tag, a in self.stack)

    def handle_starttag(self, tag, attributes):
        a = dict(attributes)
        self.sequence += 1
        if tag == 'main':
            self.watch = bool({'film-watch', 'video-watch-page'} & set(a.get('class', '').split()))
        inside = any(t == 'main' for t, _ in self.stack)
        if inside and tag == 'h2':
            self.first_h2 = min(self.first_h2, self.sequence)
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonicals.append(a.get('href'))
        if tag == 'meta' and a.get('name') == 'robots':
            self.robots = a.get('content', '')
        if tag == 'video':
            self.videos.append({'attrs': a, 'main': inside, 'hidden': self.hidden() or 'hidden' in a,
                                'sequence': self.sequence, 'sources': [a['src']] if a.get('src') else []})
        if tag == 'source' and any(t == 'video' for t, _ in self.stack) and a.get('src'):
            self.videos[-1]['sources'].append(a['src'])
        if tag == 'a' and a.get('href') and not self.hidden():
            self.links.append(a['href'])
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.buffer = []
        if tag not in VOID:
            self.stack.append((tag, a))

    def handle_data(self, data):
        if self.buffer is not None:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.buffer is not None:
            self.blocks.append(json.loads(''.join(self.buffer)))
            self.buffer = None
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def video_objects(self):
        return [item for block in self.blocks for item in objects(block) if item.get('@type') == 'VideoObject']


def check():
    sitemap = ET.parse(ROOT / 'sitemap.xml')
    entries = sitemap.findall('s:url', NS)
    urls = {entry.findtext('s:loc', namespaces=NS) for entry in entries}
    pages = {url: Page((ROOT / urlsplit(url).path.lstrip('/') / 'index.html').read_text()) for url in urls}
    targets = {}
    incoming = set()
    for source, page in pages.items():
        incoming.update(urljoin(source, href).split('#')[0].split('?')[0]
                        for href in page.links if urljoin(source, href).split('#')[0].split('?')[0] != source)
        for video in page.video_objects():
            target = video.get('url')
            assert target in pages and pages[target].watch, f'{source}: film needs a dedicated watch URL: {target}'
            content = video['contentUrl']
            assert targets.setdefault(content, target) == target, f'Duplicate watch URLs for {content}'
            assert video.get('mainEntityOfPage', {}).get('@id') == target + '#webpage', f'Wrong mainEntityOfPage: {source}'
    watches = {url for url, page in pages.items() if page.watch}
    assert watches == set(targets.values()), 'Watch pages and video destinations diverge'
    for url in sorted(watches):
        page = pages[url]
        assert page.canonicals == [url] and 'noindex' not in page.robots, f'Watch page is not self-canonical/indexable: {url}'
        assert url in incoming, f'Watch page has no visible HTML discovery link: {url}'
        assert len(page.videos) == 1 and len(page.video_objects()) == 1, f'Expected one prominent video: {url}'
        player, schema = page.videos[0], page.video_objects()[0]
        assert player['main'] and not player['hidden'], f'Player is hidden behind a tab or details: {url}'
        assert player['sequence'] < page.first_h2, f'Player must precede secondary content: {url}'
        assert 'controls' in player['attrs'] and player['attrs'].get('preload') == 'metadata', f'Player must load directly: {url}'
        assert schema['contentUrl'] in [urljoin(ORIGIN, src) for src in player['sources']], f'Player/schema mismatch: {url}'
        thumb = schema['thumbnailUrl']
        assert urljoin(ORIGIN, player['attrs'].get('poster', '')) == (thumb[0] if isinstance(thumb, list) else thumb), f'Poster mismatch: {url}'
        assert any(item.get('@id') == url + '#webpage' and item.get('mainEntity', {}).get('@id') == schema['@id']
                   for block in page.blocks for item in objects(block)), f'WebPage must name the film as mainEntity: {url}'
    advertised = {}
    for entry in entries:
        url = entry.findtext('s:loc', namespaces=NS)
        for video in entry.findall('v:video', NS):
            assert url in watches, f'Supplementary page advertised as watch page in sitemap: {url}'
            content = video.findtext('v:content_loc', namespaces=NS)
            assert content not in advertised, f'Duplicate video sitemap entry: {content}'
            advertised[content] = url
    assert advertised == targets, 'Video sitemap must list every unique film on its watch page'
    film_entries = ET.parse(ROOT / 'video-sitemap.xml').findall('s:url', NS)
    film_urls = [entry.findtext('s:loc', namespaces=NS) for entry in film_entries]
    assert len(film_urls) == len(set(film_urls)), 'Duplicate watch URL in dedicated video sitemap'
    assert set(film_urls) == watches, 'Dedicated video sitemap must contain only and all watch pages'
    for entry in film_entries:
        url = entry.findtext('s:loc', namespaces=NS)
        listed = entry.findall('v:video', NS)
        assert len(listed) == 1, f'Dedicated video sitemap needs one film per watch page: {url}'
        schema = pages[url].video_objects()[0]
        thumb = schema['thumbnailUrl']
        assert listed[0].findtext('v:content_loc', namespaces=NS) == schema['contentUrl'], f'Wrong film in dedicated video sitemap: {url}'
        assert listed[0].findtext('v:thumbnail_loc', namespaces=NS) == (thumb[0] if isinstance(thumb, list) else thumb), f'Wrong poster in dedicated video sitemap: {url}'
    assert 'Sitemap: ' + ORIGIN + '/video-sitemap.xml' in (ROOT / 'robots.txt').read_text().splitlines(), 'Declare the dedicated video sitemap in robots.txt'
    print(f'PASS: {len(targets)} unique films have one visible watch page each, matching schema/poster, HTML links and video sitemap.')
    print('Scope: crawlable source and page structure; Google decides video indexing after recrawling.')


if __name__ == '__main__':
    check()
