#!/usr/bin/env python3
"""Public-site visibility and conversion regression checks. Standard library only."""
import json,re,xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[2]
class Scan(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True)
        self.links=[];self.assets=[];self.metas={};self.jsonld=[];self.ld=False;self.buf=[];self.h1=0
        self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a':self.links.append(a)
        if tag=='script' and a.get('src'):self.assets.append(a['src'])
        if tag=='meta':self.metas[a.get('name',a.get('property',''))]=a.get('content','')
        if tag=='h1':self.h1+=1
        if tag=='script' and a.get('type')=='application/ld+json':self.ld=True;self.buf=[]
    def handle_data(self,data):
        if self.ld:self.buf.append(data)
    def handle_endtag(self,tag):
        if tag=='script' and self.ld:self.jsonld.append(json.loads(''.join(self.buf)));self.ld=False

def objects(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from objects(v)
    elif isinstance(x,list):
        for v in x:yield from objects(v)

def check():
    ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls=[n.text for n in ET.parse(ROOT/'sitemap.xml').findall('s:url/s:loc',ns)]
    checked=0;ignored=0;bookings=0
    for url in urls:
        path=ROOT/urlsplit(url).path.lstrip('/')/'index.html'
        if not path.exists():continue
        text=path.read_text();s=Scan(text)
        if 'kansei-ga4' not in s.metas:continue
        checked+=1
        assert s.assets.count('/assets/analytics.20261031.js')==1, f'Incorrect analytics inclusion: {path}'
        assert not any('analytics.20261009' in a for a in s.assets), f'Old analytics active: {path}'
        assert s.metas['kansei-ga4']=='G-F1EVW66L9S'
        assert s.h1==1, f'Expected one H1: {path}'
        assert 'max-image-preview:large' in s.metas.get('robots',''), f'Missing preview permission: {path}'
        if 'menu-secondary' in text:
            assert any(a.get('href')=='/ultraljud/bilder/' for a in s.links), f'Missing HTML image-library link: {path}'
        for a in s.links:
            u=urlsplit(a.get('href',''))
            if u.hostname in ['www.bokadirekt.se','bokadirekt.se'] and '48847' in u.path:
                assert a.get('data-measure') in ['booking_click','ignore'], f'Unclassified clinic link: {path}'
                if a['data-measure']=='ignore':ignored+=1
                else:bookings+=1
    assert checked>=120,checked
    # Only current published offer schemas are compared; unrelated campaign prices are not touched.
    hy=Scan((ROOT/'hyaluronsyra/index.html').read_text())
    offers=[x for b in hy.jsonld for x in objects(b) if x.get('@type')=='Offer' and str(x.get('price')) in ['3190','5790','3490','6290']]
    assert {'3190','5790','3490','6290'}<={str(x['price']) for x in offers}, 'Hyaluron one/two-joint prices diverge'
    for rel in ['index.html','hyaluronsyra/index.html','priser/index.html','injektioner/index.html']:
        text=(ROOT/rel).read_text()
        assert not re.search(r'(?<!\d)(?:2[ \u00a0]?590|2[ \u00a0]?990)\s*(?:kr|SEK)',text), 'Old hyaluron offer on '+rel
    nap=(ROOT/'naprapati/index.html').read_text()
    assert 'vi arbetar sida vid sida med leg. fysioterapeut' not in nap
    assert 'Specialistmedverkan sker efter förfrågan' in nap
    assert '590' in (ROOT/'priser/index.html').read_text(), 'Written report price missing'
    article=(ROOT/'blogg/naprapat-fysioterapeut-kiropraktor-eller-ortoped/index.html').read_text()
    assert 'alla leder till samma bedömning' not in article
    assert 'Specialistmedverkan planeras separat efter förfrågan' in article
    assert 'under samma tak' not in article
    cookie=(ROOT/'cookie/index.html').read_text()
    assert 'statistik-kallgrupp' in cookie and 'sessionStorage' in cookie
    assert ignored>0 and bookings>0
    print(f'PASS: {checked} indexable clinic pages use one consent bridge; {bookings} booking links and {ignored} non-booking links explicitly separated.')
    print('PASS: shared HTML discovery, one H1, large-image permission, current offers, clinic representation and measurement disclosure.')
    print('Scope: these are site regressions, not measured rankings, AI citations or confirmed bookings.')

if __name__=='__main__':check()
