#!/usr/bin/env python3
"""Verify this release on the public host; optional explicit IndexNow notification.
No Google/GA4/booking account access is performed. No background scheduling.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from urllib.parse import urlsplit
import argparse,hashlib,json,time,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
ORIGIN='https://www.kansei.se'
PATHS=['/','/naprapati/','/ultraljud/','/hyaluronsyra/','/kontakt/','/team/carl-robert-karell/','/blogg/naprapat-fysioterapeut-kiropraktor-eller-ortoped/','/blogg/','/kunskapsbank/','/cookie/']
def get(path):
    req=Request(ORIGIN+path,headers={'User-Agent':'Kansei-owner-release-verification/20261016','Cache-Control':'no-cache'})
    with urlopen(req,timeout=25) as r:
        assert r.status==200,(path,r.status)
        assert urlsplit(r.url).hostname in ['kansei.se','www.kansei.se'], 'Unexpected redirect host'
        return r.read()

def run(notify=False):
    verified=[]
    for path in PATHS+['/assets/analytics.20261017.js']:
        local=ROOT/path.lstrip('/')
        if path.endswith('/'):local=local/'index.html'
        expected=local.read_bytes()
        for attempt in range(12):
            try:
                body=get(path+('?__kansei_release=20261016' if attempt else ''))
                assert body.replace(b'\r\n',b'\n')==expected.replace(b'\r\n',b'\n'), 'Release not yet served at '+path
                verified.append(ORIGIN+path);print('LIVE VERIFIED',path,flush=True);break
            except (AssertionError,HTTPError,URLError,TimeoutError) as exc:
                if attempt==11:raise
                print('Waiting for deployment/CDN',path,str(exc),flush=True);time.sleep(10)
    xml=get('/sitemap.xml')
    assert xml.replace(b'\r\n',b'\n')==(ROOT/'sitemap.xml').read_bytes().replace(b'\r\n',b'\n')
    count=len(ET.fromstring(xml).findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url'))
    result={'date':'2026-10-16','deployment_verified':True,'verified_urls':verified,'sitemap_urls':count,'ga4_collection_verified':False,'ai_benchmark_runs_performed':0,'indexnow':{'submitted':False}}
    if notify:
        key_path=ROOT/'3ed562838d3004201fb2a4f33ee61ef1.txt'
        key=key_path.read_text().strip()
        assert get('/'+key_path.name).decode().strip()==key, 'Public ownership file differs'
        urls=[ORIGIN+p for p in PATHS if p!='/cookie/']
        data=json.dumps({'host':'www.kansei.se','key':key,'keyLocation':ORIGIN+'/'+key_path.name,'urlList':urls}).encode()
        req=Request('https://api.indexnow.org/indexnow',data=data,method='POST',headers={'Content-Type':'application/json; charset=utf-8','User-Agent':'Kansei-owner-release-notification/20261016'})
        try:
            with urlopen(req,timeout=30) as r:
                status=r.status;r.read()
            result['indexnow']={'submitted':status in [200,202],'http_status':status,'url_count':len(urls),'meaning':'Received only; key verification may be pending at 202. Does not prove indexing, rankings or Google submission.'}
        except (HTTPError,URLError,TimeoutError) as exc:
            result['indexnow']={'submitted':False,'error':str(exc),'meaning':'Live deployment is verified separately. No automatic resubmission loop.'}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--notify-indexnow',action='store_true',help='Explicitly notify participating search engines of the changed core pages after live verification.')
    p.add_argument('--output',type=Path)
    a=p.parse_args();result=run(a.notify_indexnow)
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2))
