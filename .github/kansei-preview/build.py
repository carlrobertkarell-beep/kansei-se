#!/usr/bin/env python3
"""Build a coherent *preview only* from the preserved clinic sources.
No writes to the source tree, no Reda app export, no production mode.
Usage: python build.py SOURCE DESTINATION
"""
from pathlib import Path
from bs4 import BeautifulSoup as BS
from urllib.parse import urlsplit, urljoin
from PIL import Image
import argparse,copy,hashlib,html,json,re,shutil
ROOT=Path(__file__).resolve().parent
P=argparse.ArgumentParser();P.add_argument('source',type=Path);P.add_argument('destination',type=Path);A=P.parse_args()
SRC=A.source.resolve();OUT=A.destination.resolve()
if OUT==SRC or SRC in OUT.parents and OUT.name not in ('public','preview-output'):raise SystemExit('Use a separate preview output directory.')
OUT.mkdir(parents=True,exist_ok=True)
EXCLUDED={'.github','.git','supabase','node_modules','docs','reda','reda-2','reda2','ovningar','reda-test-results','reda2-test-results','kansei-test-results'}
ALLOWED={'.html','.css','.js','.mjs','.json','.svg','.png','.jpg','.jpeg','.webp','.gif','.ico','.woff','.woff2','.webmanifest','.xml','.txt','.mp4','.webm','.pdf'}
for f in SRC.rglob('*'):
 if not f.is_file() or f.is_symlink():continue
 rel=f.relative_to(SRC)
 if rel.parts[0] in EXCLUDED or any(x.startswith('.') for x in rel.parts):continue
 if f.suffix.lower() not in ALLOWED or rel.as_posix() in {'package.json','package-lock.json','BingSiteAuth.xml','robots.txt','sitemap.xml','__kansei-preview.json'}:continue
 target=OUT/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
BOOK='https://www.bokadirekt.se/places/kansei-rehabcenter-48847'
CONSULT='https://www.bokadirekt.se/boka-tjanst/kansei-rehabcenter-48847/konsultation-infor-injektionsbehandling-3409513'
esc=lambda x:html.escape(str(x),quote=True)
parse=lambda t:BS(t,'html.parser')
home=parse((SRC/'index.html').read_text())
icons=str(home.select_one('.icon-defs'))
guide=str(home.select_one('#guide-dialog'))
base=(SRC/'assets/style.48672f28084a.css').read_text()
css=base+'\n'+(SRC/'assets/cluster.css').read_text()+'\n'+(ROOT/'polish.css').read_text()
js=(SRC/'assets/app.bad9fa366e44.js').read_text()+'\n'+(ROOT/'polish.js').read_text()
def asset(name,body,ext):
 path='assets/'+name+'.'+hashlib.sha256(body.encode()).hexdigest()[:12]+'.'+ext
 (OUT/path).write_text(body);return '/'+path
CSS=asset('clinic',css,'css');JS=asset('clinic',js,'js')
AREAS='/assets/areas.52980d1b3316.js';GUIDE='/assets/guide.5fd4e6908c48.js'
NAV=[('/hjalp-mig-boka/','Hitta rätt'),('/tjanster/','Tjänster'),('/kunskapsbank/','Kunskapsbanken'),('/om-oss/','Kliniken'),('/priser/','Priser')]
MENU=[('/tjanster/','Tjänster'),('/kunskapsbank/','Kunskapsbanken'),('/om-oss/','Kliniken'),('/priser/','Priser'),('/kontakt/','Kontakt')]
INJECTIONS={'/prp/','/hyaluronsyra/','/kortison/','/injektioner/'}
def icon(n='arrow'):return '<svg class="icon" aria-hidden="true"><use href="#i-'+n+'"/></svg>'
def active(url,path):return ' aria-current="page"' if url==path else ''
def shell(path,book):
 logo='<img src="/assets/logo-dark.webp" width="550" height="137" alt="Kansei Rehabcenter">'
 reda='<img src="/bilder/reda/lockup.svg" width="120" height="36" alt="Reda">'
 nav=''.join(f'<a href="{u}"{active(u,path)}>{t}</a>' for u,t in NAV)
 top=f'<a class="skip" href="#main">Hoppa till innehållet</a>{icons}<header class="site-header"><div class="header-inner wrap"><a class="brand" href="/" aria-label="Kansei Rehabcenter, startsida">{logo}</a><nav class="desktop-nav" aria-label="Huvudmeny">{nav}<a class="menu-reda" href="/reda-rehab/" aria-label="Reda">{reda}</a></nav><div class="header-actions"><a class="button button-dark header-book" href="{esc(book)}" target="_blank" rel="noopener noreferrer">Boka besök {icon("up")}</a><button class="site-menu-toggle" type="button" data-site-menu aria-label="Öppna meny" aria-controls="site-menu" aria-expanded="false"><span>Meny</span>{icon("menu")}</button></div></div></header>'
 navitems=''.join(f'<a href="{u}"{active(u,path)}><span>{t}</span><small>{i:02}</small></a>' for i,(u,t) in enumerate(MENU,1))
 menu=f'<dialog id="site-menu" aria-label="Kanseis meny"><div class="site-menu-head"><a href="/" aria-label="Kansei, startsida">{logo}</a><button type="button" class="site-menu-close" data-site-close aria-label="Stäng meny">{icon("close")}</button></div><div class="site-menu-body"><nav class="menu-primary" aria-label="Alla sidor">{navitems}</nav><nav class="menu-secondary" aria-label="Mer från Kansei"><a href="/hjalp-mig-boka/">Hjälp mig boka rätt</a><a href="/fragor-och-svar/">Vanliga frågor</a><a href="/patientinformation/">Inför ditt besök</a><a href="/om-oss/#om">Möt teamet</a><a class="menu-reda" href="/reda-rehab/" aria-label="Reda">{reda}</a><a href="https://www.kansei.se/reda/" target="_blank" rel="noopener noreferrer">Min rehabplan ↗</a></nav><div class="menu-bottom"><a class="button button-dark" href="{esc(book)}" target="_blank" rel="noopener noreferrer">Boka ditt besök {icon("up")}</a><p>Upplandsgatan 26 · Odenplan<br>Frågor? Läs FAQ eller mejla info@kansei.se.</p></div></div></dialog>'
 foot=f'<footer class="footer"><div class="wrap"><div class="footer-cta"><h2>Din väg<br>framåt.</h2><a class="footer-book" href="{esc(book)}" target="_blank" rel="noopener noreferrer"><span>Boka ditt besök {icon("up")}</span><small>Välj tid och bekräfta på Bokadirekt.</small></a></div><div class="footer-bottom"><a class="brand" href="/"><img src="/assets/logo-white.webp" width="550" height="137" alt="Kansei Rehabcenter"></a><p>Upplandsgatan 26 · Odenplan<br><a href="mailto:info@kansei.se">info@kansei.se</a></p><nav class="footer-links" aria-label="Sidfot"><a href="/kontakt/">Kontakt</a><a href="/fragor-och-svar/">Vanliga frågor</a><a href="/patientinformation/">Inför besöket</a><a href="/kunskapsbank/">Kunskapsbanken</a><a href="/priser/">Priser</a><a class="menu-reda" href="/reda-rehab/">{reda}</a></nav></div></div></footer>'
 nojs='<noscript><nav class="nojs-nav" aria-label="Genvägar utan JavaScript">'+''.join(f'<a href="{u}">{t}</a>' for u,t in NAV+[('/kontakt/','Kontakt')])+'</nav></noscript>'
 return top+nojs,foot+menu+guide

def clean(node,path):
 for el in list(node.find_all(True)):
  if el.name in ('script','style') or (el.name=='video' and not el.get('src') and not el.select_one('source[src]')):el.decompose();continue
  for attr in list(el.attrs):
   if attr.startswith('on') or attr in ('data-reveal','style'):del el[attr]
  if el.get('class'):el['class']=[c for c in el['class'] if c not in ('reveal','gl','visible')]
 for a in node.select('a[href]'):
  u=urlsplit(urljoin('https://www.kansei.se'+path,a['href']))
  if u.hostname in ('www.kansei.se','kansei.se'):
   dest=u.path+(('?'+u.query) if u.query else '')+(('#'+u.fragment) if u.fragment else '')
   if u.path in ('/','/index.html') and u.fragment in ('priser','tjanster','om'):dest={'priser':'/priser/','tjanster':'/tjanster/','om':'/om-oss/'}[u.fragment]
   if u.path in ('/kliniken/','/kliniken-vid-odenplan/'):dest='/om-oss/'
   if u.path in ('/reda/','/reda-2/') or u.path.startswith(('/reda/','/reda-2/')):dest=u.path+(('?'+u.query) if u.query else '')+(('#'+u.fragment) if u.fragment else '')
   else:a.attrs.pop('target',None);a.attrs.pop('rel',None)
   # Same-page anchors remain ordinary anchor links.
   if u.path==path and u.fragment:dest='#'+u.fragment
   a['href']=dest
  if a['href'].startswith(('tel:','sms:')) and re.sub(r'\D','',a['href']) in ('46733988588','0733988588'):
   a['href']='sms:+46733988588' if path=='/kontakt/' else 'mailto:info@kansei.se';a.clear();a.append('Skicka SMS' if path=='/kontakt/' else 'Mejla oss')
 for txt in list(node.find_all(string=True)):
  if txt.parent.name in ('script','style'):continue
  t=str(txt);new=t.replace('073 398 85 88','info@kansei.se').replace('Ring oss','Mejla oss').replace('ring oss','mejla oss')
  if new!=t:txt.replace_with(new)
 for img in node.select('img'):
  u=urlsplit(urljoin('https://www.kansei.se'+path,img.get('src','')))
  if u.hostname not in ('www.kansei.se','kansei.se'):continue
  f=SRC/u.path.lstrip('/')
  if f.exists():
   img['src']=u.path+(('?'+u.query) if u.query else '')
   try:
    with Image.open(f) as im:img['width']=str(im.width);img['height']=str(im.height)
   except Exception:pass
  img['decoding']='async'
  if not img.get('loading') and not img.get('fetchpriority'):img['loading']='lazy'
 for region in node.select('.cmp-wrap'):
  region['tabindex']='0';region['role']='region';region['aria-label']='Jämförelsetabell, rulla i sidled vid behov'
 return node

def metadata(s,path,title=None,description=None):
 head=copy.deepcopy(s.head) if s.head else parse('<head><meta charset="utf-8"></head>').head
 for el in list(head.select('style,script:not([type="application/ld+json"]),link[rel="stylesheet"],link[rel="preload"],link[rel="preconnect"],link[rel="dns-prefetch"],meta[http-equiv="refresh"]')):el.decompose()
 for key,value in [('viewport','width=device-width,initial-scale=1'),('robots','noindex,nofollow,noarchive'),('theme-color','#f7f9fa')]:
  el=head.select_one(f'meta[name="{key}"]')
  if not el:el=s.new_tag('meta',attrs={'name':key});head.append(el)
  el['content']=value
 if title:
  if head.title:head.title.string=title
  else:t=s.new_tag('title');t.string=title;head.append(t)
 if description:
  el=head.select_one('meta[name=description]')
  if el:el['content']=description
  else:head.append(s.new_tag('meta',attrs={'name':'description','content':description}))
 if path=='/kunskapsbank/':
  can=head.select_one('link[rel=canonical]')
  if can:can['href']='https://www.kansei.se/kunskapsbank/'
  else:head.append(s.new_tag('link',rel='canonical',href='https://www.kansei.se/kunskapsbank/'))
 head.append(s.new_tag('link',rel='stylesheet',href=CSS))
 return str(head)

articles=[]
for f in sorted((SRC/'blogg').glob('*/index.html')):
 s=parse(f.read_text());path='/'+str(f.parent.relative_to(SRC))+'/'
 if not s.h1:continue
 title=s.h1.get_text(' ',strip=True);meta=s.select_one('meta[name=description]');desc=meta.get('content','') if meta else ''
 low=title.lower()
 cat='Axel' if any(x in low for x in ('axel','skuldra')) else 'Knä & höft' if any(x in low for x in ('knä','höft','kna','hoft','artros','hoppar')) else 'Rygg & nacke' if any(x in low for x in ('rygg','nack','disk','ischias')) else 'Hand & armbåge' if any(x in low for x in ('arm','hand','händer','karpal')) else 'Fot & hälsena' if any(x in low for x in ('häl','fot','benhinne')) else 'Undersökning & behandling'
 articles.append((path,title,desc,cat))

def library(archive=False):
 title='Blogg' if archive else 'Förstå mer.<br><span>Välj ditt nästa steg.</span>'
 intro='Klinikens artiklar om besvär, undersökningar och behandlingsalternativ. Samma artiklar och adresser, samlade i kunskapsbanken.'
 featured=''.join(f'<a class="knowledge-feature" href="/kunskapsbank/{u}/"><span class="eyebrow">BÖRJA MED ETT OMRÅDE</span><h2>{h} {icon()}</h2><p>{d}</p></a>' for u,h,d in [('axel','Axel','Nattlig värk, stelhet och smärta när du lyfter armen. Läs om bedömning och nästa steg.'),('kna','Knä','Svullnad, trappsmärta och artros. Förstå vad som kan behöva undersökas.')])
 topics=['Alla','Axel','Knä & höft','Rygg & nacke','Hand & armbåge','Fot & hälsena','Undersökning & behandling']
 filters=''.join(f'<button type="button" data-topic="{esc(t)}" aria-pressed="{str(i==0).lower()}">{esc(t)}</button>' for i,t in enumerate(topics))
 cards=''.join(f'<article class="knowledge-result" data-library-card data-category="{esc(cat)}" data-search="{esc(title+" "+desc)}"><span class="eyebrow">{esc(cat)}</span><h2><a href="{u}">{esc(title)}</a></h2><p>{esc(desc)}</p><span class="read-more" aria-hidden="true">Läs artikeln ↗</span></article>' for u,title,desc,cat in articles)
 return f'<main id="main" tabindex="-1"><section class="knowledge-top wrap"><p class="crumbs"><a href="/">Kansei</a> / Kunskapsbanken</p><span class="eyebrow">KUNSKAP FRÅN KLINIKEN</span><h1>{title}</h1><p class="intro">{intro}</p><div class="knowledge-featured">{featured}</div></section><section class="knowledge-library wrap"><div class="knowledge-toolbar"><div class="knowledge-search"><label for="library-search">Sök bland våra artiklar</label><input type="search" id="library-search" data-library-search placeholder="Till exempel axel, artros eller ultraljud" autocomplete="off"></div><p class="library-count" aria-live="polite" data-library-count>{len(articles)} artiklar</p></div><div class="knowledge-filter" role="group" aria-label="Filtrera på ämne">{filters}</div><div class="knowledge-results">{cards}</div><div class="knowledge-empty" data-library-empty hidden><p>Ingen artikel matchade din sökning. Prova ett annat ord eller visa alla ämnen.</p><button data-library-reset type="button">Visa alla artiklar</button></div></section></main>'

manifest=[]
for f in sorted(OUT.rglob('*.html')):
 rel=f.relative_to(OUT);path='/' if rel.as_posix()=='index.html' else '/404.html' if rel.as_posix()=='404.html' else '/'+rel.parent.as_posix()+'/'
 if rel.parts[0] in ('reda-rehab','en'):continue
 s=parse(f.read_text())
 if s.select_one('meta[http-equiv=refresh]') and path!='/kunskapsbank/':
  # Keep established alias semantics, but never send a clinic link out of preview.
  for m in s.select('meta[http-equiv=refresh]'):m['content']=m['content'].replace('https://www.kansei.se','').replace('https://kansei.se','')
  for a in s.select('a[href]'):a['href']=a['href'].replace('https://www.kansei.se','').replace('https://kansei.se','')
  for script in s.select('script'):script.string=script.get_text().replace('https://www.kansei.se','').replace('https://kansei.se','')
  f.write_text(str(s));continue
 original_title=s.title.get_text() if s.title else ''
 original_canonical=s.select_one('link[rel=canonical]');original_canonical=original_canonical.get('href') if original_canonical else None
 original_h1=s.h1.get_text(' ',strip=True) if s.h1 else None
 book=CONSULT if path in INJECTIONS else BOOK
 top_old=s.select_one('header.page')
 if top_old and path not in INJECTIONS:
  direct=top_old.select_one('.tf-fot a[href*="bokadirekt"]')
  if direct:book=direct['href']
 wide=path in ('/om-oss/','/tjanster/')
 if path in ('/blogg/','/kunskapsbank/'):
  body=library(path=='/blogg/')
  head=metadata(s,path,'Kunskapsbank | Kansei Rehabcenter' if path=='/kunskapsbank/' else None,'Artiklar om axel, knä, rygg och andra rörelsebesvär. Läs om undersökning, rehabilitering och behandlingsalternativ hos Kansei.' if path=='/kunskapsbank/' else None)
 elif top_old and s.main:
  top=clean(copy.deepcopy(top_old),path);top.name='section';content=clean(copy.deepcopy(s.main),path);content.name='div';content.attrs={'class':'original-main'}
  for price in top.select('.tf-pris'):
   if price.get_text(strip=True).startswith('Bokas som naprapati'):
    text=price.get_text(' ',strip=True).split('·')[-1].strip();price.clear();price.append(text);small=s.new_tag('small');small.string='Bokas som naprapati';price.append(small)
  if path.startswith('/blogg/'):
   cat=next((a[3] for a in articles if a[0]==path),'Artiklar');ey=top.select_one('.eyebrow')
   if ey:ey.string='Kunskapsbanken · '+cat
  for unneeded in top.select('.vagvisare,.trustline'):unneeded.decompose()
  for old_toc in content.select('.toc'):old_toc.decompose()
  if path in INJECTIONS:
   price=top.select_one('.tf-pris')
   if price:
    price.clear();price.append('890 kr');small=s.new_tag('small');small.string='Injektionskonsultation. Ultraljud vid konsultationen: +400 kr enligt prislistan. Behandling debiteras separat.';price.append(small)
   for a in top.select('a[href*="bokadirekt"]'):a['href']=CONSULT;a.clear();a.append('Boka konsultation →')
  titles=[]
  for i,h in enumerate(content.select('h2'),1):
   if not h.get('id'):h['id']='avsnitt-'+str(i)
   titles.append((h['id'],h.get_text(' ',strip=True)))
  nav=''.join(f'<a href="#{esc(sid)}"><span>{i:02}</span>{esc(t)}</a>' for i,(sid,t) in enumerate(titles,1))
  aside='' if wide else f'<aside class="editorial-aside"><p class="eyebrow">PÅ DEN HÄR SIDAN</p><nav aria-label="Sidans innehåll">{nav}</nav><a class="aside-next" href="/fragor-och-svar/">Frågor inför besöket? →</a></aside>'
  mobile='' if wide else f'<details class="contents-mobile"><summary>Hoppa till ett avsnitt</summary><nav aria-label="Innehåll på mobil">{nav}</nav></details>'
  card=s.select_one('#planKort')
  if card and not content.select_one('#planKort'):
   card=clean(copy.deepcopy(card),path);card['class']=card.get('class',[])+['inherited-reda'];content.append(card)
  if path=='/om-oss/':
   figure=content.select_one('.klinik')
   if figure:
    # Add an authentic arrival photo; keep the original interior photograph too.
    facade=parse('<figure class="facade-photo"><img src="/bilder/k455db62d95.jpg" width="1600" height="1067" alt="Entrén till Kansei på Upplandsgatan 26" loading="lazy"><figcaption>Här hittar du oss på Upplandsgatan 26.</figcaption></figure>').figure
    content.append(facade)
  body=f'<main id="main" tabindex="-1" class="editorial-page {"editorial-wide" if wide else ""}"><div class="editorial-top wrap"><p class="crumbs"><a href="/">Kansei</a> / {esc(original_h1 or "Information")}</p>{top}</div><div class="editorial-layout wrap">{aside}<div class="editorial-body">{mobile}{content}</div></div></main>'
  head=metadata(s,path)
 else:
  m=s.main
  if not m:continue
  m=copy.deepcopy(m);m['id']='main';m['tabindex']='-1'
  # Keep the existing Framåt composition and compatibility contract.
  m=clean(m,path)
  if path=='/':
   for t in m.select('[data-method]'):t['role']='tab';t['aria-controls']='method-panel';t['tabindex']='0' if t.get('aria-selected')=='true' else '-1'
   panel=m.select_one('#method-panel')
   if panel:panel['role']='tabpanel';panel['aria-labelledby']='method-tab-1'
   # The clinic section should show a place, not repeat a treatment photograph.
   ci=m.select_one('.clinic-image img')
   if ci:ci['src']='/bilder/k0d80f0e3b7.webp';ci['alt']='Klinikmiljön på Kansei Rehabcenter'
  body=str(m);head=metadata(s,path)
 top,bottom=shell(path,book)
 doc='<!doctype html><html lang="sv">'+head+'<body>'+top+body+bottom+f'<script src="{JS}" data-area-src="{AREAS}" data-guide-src="{GUIDE}" defer></script></body></html>'
 final=parse(doc);clean(final.body,path)
 final.body.append(final.new_tag('script',src=JS,attrs={'data-area-src':AREAS,'data-guide-src':GUIDE,'defer':''}))
 # Ensure pure SVG symbols occupy no layout space without an external sheet.
 defs=final.select_one('.icon-defs')
 if defs:defs['width']='0';defs['height']='0'
 if path not in ('/kunskapsbank/',):
  assert final.title.get_text()==original_title,(path,'title drift')
  if original_canonical:assert final.select_one('link[rel=canonical]')['href']==original_canonical,(path,'canonical drift')
  if original_h1:assert final.h1.get_text(' ',strip=True)==original_h1,(path,'H1 drift')
 assert len(final.select('.site-header'))==1 and len(final.select('#site-menu'))==1,path
 assert not final.select('link[href*="fonts.googleapis.com"]'),path
 assert not final.select('a[href^="tel:+46733988588"]'),path
 f.write_text(str(final))
 manifest.append({'path':path,'file':rel.as_posix(),'canonical':original_canonical,'title_preserved':path!='/kunskapsbank/','template':'editorial' if top_old else 'framat','bytes':f.stat().st_size})
# Each canonical article stays in the new shell, with its original indexed URL.
for path,title,desc,cat in articles:
 s=parse((OUT/path.lstrip('/')/'index.html').read_text());assert s.select_one('.site-header');assert s.select_one('link[rel=canonical]')['href']=='https://www.kansei.se'+path
(OUT/'_headers').write_text("/*\n  X-Robots-Tag: noindex, nofollow, noarchive\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Content-Security-Policy: connect-src 'self'; form-action 'none'; frame-src 'none'\n")
(OUT/'robots.txt').write_text('User-agent: *\nDisallow: /\n')
(OUT/'_redirects').write_text('/kliniken/ /om-oss/ 302!\n/kliniken-vid-odenplan/ /om-oss/ 302!\n/reda /reda/ 302\n/reda/ https://www.kansei.se/reda/ 302!\n/reda/* https://www.kansei.se/reda/:splat 302!\n/reda-2 /reda-2/ 302\n/reda-2/ https://www.kansei.se/reda-2/ 302!\n/reda-2/* https://www.kansei.se/reda-2/:splat 302!\n')
report={'version':'coherent-clinic-preview-v2','clinic_pages':len(manifest),'canonical_articles':len(articles),'pages':manifest,'css':CSS,'js':JS,'excluded_unchanged':['Reda app folders','Reda product pages','English landing'],'note':'UI preview only. Not approved for production. Canonical titles, URLs and H1 preserved for source pages. New knowledge hub is noindex.'}
(OUT/'__clinic-build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'clinic_pages':len(manifest),'canonical_articles':len(articles),'css':CSS,'js':JS}))
