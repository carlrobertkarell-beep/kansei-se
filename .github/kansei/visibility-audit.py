"""Read-only public-site inventory. No private analytics or patient records."""
from pathlib import Path
from bs4 import BeautifulSoup
import json,re,collections
root=Path(__file__).resolve().parents[2]
main_pages=['index.html','naprapati/index.html','hyaluronsyra/index.html','ultraljud/index.html','kontakt/index.html','om-oss/index.html','team/carl-robert-karell/index.html','priser/index.html','cookie/index.html','bildinformation/index.html']
for relative in main_pages:
 p=root/relative
 if not p.exists():continue
 s=BeautifulSoup(p.read_text(),'html.parser')
 print('\nPAGE',relative)
 print('TITLE',s.title.get_text() if s.title else '')
 print('DESC',[(x.get('name'),x.get('content')) for x in s.select('meta[name=description]')])
 print('HEADINGS',[(x.name,x.get('id'),x.get_text(' ',strip=True)) for x in s.select('h1,h2,h3')])
 print('CONTENT',s.find('main').get_text(' ',strip=True)[:22000] if s.find('main') else '')
 print('SCRIPTS', [x.get('src') for x in s.select('script[src]')])
 print('STRUCTURED', [x.get_text() for x in s.select('script[type="application/ld+json"]')])
 print('SECTIONS',[(x.get('id'),x.get('class'),x.get_text(' ',strip=True)[:140]) for x in s.select('main > section')])
 print('BOOKINGS',[(x.get_text(' ',strip=True),x.get('href')) for x in s.select('a[href]') if 'bokadirekt' in x['href']][:12])
print('\nPUBLIC URL INVENTORY')
for p in sorted(root.rglob('index.html')):
 rel=p.relative_to(root).as_posix()
 if rel.startswith(('.github/','reda/','reda2/')):continue
 s=BeautifulSoup(p.read_text(),'html.parser')
 if not s.body or 'clinic-site' not in s.body.get('class',[]):continue
 can=s.select_one('link[rel=canonical]')
 print(rel, '|', s.title.get_text() if s.title else '', '|',can.get('href') if can else 'NO CANONICAL')
 for t in s.find_all(string=re.compile(r'sida vid sida|fysioterapeut|Torsgatan|2[ \u00a0]?[59]90|2590|2990')):
  if t.parent.name not in ['script','style']:
   print('REVIEW',rel,repr(str(t)[:600]))
print('\nMAINTENANCE FILES')
for folder in ['docs','.github/scripts']:
 p=root/folder
 if p.exists(): print(folder,[str(f.relative_to(root)) for f in p.rglob('*') if f.is_file()])
print('\nANALYTICS / BOOKING HOOKS')
for p in (root/'assets').glob('*.js'):
 text=p.read_text(errors='replace')
 if 'kansei:booking-intent' in text or 'kansei-statistics' in text:
  print(p.relative_to(root),text[:25000])
print('\nSITEMAP', (root/'sitemap.xml').read_text()[:25000])
