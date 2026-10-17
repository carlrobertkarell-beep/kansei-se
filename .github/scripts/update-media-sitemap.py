#!/usr/bin/env python3
"""Refresh the existing sitemap from published clinical images and video metadata.

Run after adding an ultrasound case or changing its assets. Only canonical URLs
already present in sitemap.xml are inspected. No crawl, credentials or third-party
packages are needed. --check reports drift without writing the sitemap.
"""
from __future__ import annotations

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = 'https://www.kansei.se'
SITEMAP = 'http://www.sitemaps.org/schemas/sitemap/0.9'
IMAGE = 'http://www.google.com/schemas/sitemap-image/1.1'
VIDEO = 'http://www.google.com/schemas/sitemap-video/1.1'
for prefix, namespace in [('', SITEMAP), ('image', IMAGE), ('video', VIDEO)]:
    ET.register_namespace(prefix, namespace)


class Media(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.main = False
        self.images: set[str] = set()
        self.sources: set[str] = set()
        self.blocks: list[dict] = []
        self.block: list[str] | None = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'main':
            self.main = True
        if self.main and tag == 'img':
            src = urljoin(ORIGIN, attrs.get('src', ''))
            if urlsplit(src).path.startswith(('/bilder/ultraljud/', '/bilder/produkter/')):
                self.images.add(src)
        if self.main and tag in ('video', 'source') and attrs.get('src'):
            self.sources.add(urljoin(ORIGIN, attrs['src']))
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.block = []

    def handle_data(self, data):
        if self.block is not None:
            self.block.append(data)

    def handle_endtag(self, tag):
        if tag == 'main':
            self.main = False
        if tag == 'script' and self.block is not None:
            self.blocks.append(json.loads(''.join(self.block)))
            self.block = None


def asset_exists(url):
    parts = urlsplit(url)
    if parts.netloc != urlsplit(ORIGIN).netloc:
        raise ValueError('Unexpected media host: ' + url)
    path = (ROOT / unquote(parts.path).lstrip('/')).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError('Published media file is missing: ' + url)


def generate():
    tree = ET.parse(ROOT / 'sitemap.xml')
    image_count = video_count = 0
    for entry in tree.getroot().findall('{' + SITEMAP + '}url'):
        url = entry.findtext('{' + SITEMAP + '}loc')
        path = ROOT / unquote(urlsplit(url).path).lstrip('/') / 'index.html'
        if not path.is_file():
            raise ValueError('Published page is missing: ' + url)
        media = Media(path.read_text(encoding='utf-8'))
        for old in list(entry):
            if old.tag.startswith('{' + IMAGE + '}') or old.tag.startswith('{' + VIDEO + '}'):
                entry.remove(old)
        for src in sorted(media.images):
            asset_exists(src)
            image = ET.SubElement(entry, '{' + IMAGE + '}image')
            ET.SubElement(image, '{' + IMAGE + '}loc').text = src
            image_count += 1
        seen = set()
        for block in media.blocks:
            for item in block.get('@graph', [block]):
                if item.get('@type') != 'VideoObject':
                    continue
                src = item['contentUrl']
                if src not in media.sources:
                    raise ValueError('Video metadata has no matching player: ' + url)
                if src in seen:
                    continue
                seen.add(src)
                thumb = item['thumbnailUrl']
                if isinstance(thumb, list):
                    thumb = thumb[0]
                asset_exists(src)
                asset_exists(thumb)
                video = ET.SubElement(entry, '{' + VIDEO + '}video')
                for name, value in [('thumbnail_loc', thumb), ('title', item['name']),
                                    ('description', item['description']), ('content_loc', src),
                                    ('publication_date', item['uploadDate'])]:
                    ET.SubElement(video, '{' + VIDEO + '}' + name).text = value
                video_count += 1
    ET.indent(tree, space='  ')
    output = ET.tostring(tree.getroot(), encoding='unicode', xml_declaration=False)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + output + '\n', image_count, video_count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text, images, videos = generate()
    if args.check:
        if text != (ROOT / 'sitemap.xml').read_text(encoding='utf-8'):
            raise SystemExit('Media sitemap is stale; run .github/scripts/update-media-sitemap.py')
    else:
        (ROOT / 'sitemap.xml').write_text(text, encoding='utf-8')
    print(f'PASS: media sitemap matches published HTML: {images} image references and {videos} videos.')
