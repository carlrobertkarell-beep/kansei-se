"""Checks the generated preview via real local HTTP in CI, not source templates."""
from pathlib import Path
from urllib.parse import urlsplit,urljoin,unquote
import functools,http.server,threading,json,sys
from bs4 import BeautifulSoup as BS
from playwright.sync_api import sync_playwright
root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
manifest=json.loads((root/'__clinic-build.json').read_text());report={'pages':len(manifest['pages']),'canonical_articles':manifest['canonical_articles'],'layout_checks':0,'errors':[],'missing_resources':[],'checks':[]}
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch();c=b.new_context(viewport={'width':390,'height':844});p=c.new_page()
  p.on('pageerror',lambda e:report['errors'].append(str(e)))
  p.on('response',lambda r:report['missing_resources'].append(r.url) if r.status>=400 and r.url.startswith(origin) else None)
  c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(origin) else r.abort())
  for row in manifest['pages']:
   p.goto(origin+row['path'],wait_until='networkidle');assert p.locator('.site-header').count()==1,row['path'];assert p.locator('#site-menu').count()==1,row['path']
   for w in [320,390,768,1024,1440]:
    p.set_viewport_size({'width':w,'height':900});p.wait_for_timeout(50)
    assert p.evaluate('document.documentElement.scrollWidth')<=w,(row['path'],w,'overflow')
    assert p.locator('.header-book').is_visible(),row['path'];report['layout_checks']+=1
   assert p.locator('meta[name=robots]').get_attribute('content').startswith('noindex'),row['path']
  p.set_viewport_size({'width':390,'height':844});p.goto(origin+'/')
  top=p.locator('.site-header').bounding_box();p.get_by_role('button',name='Öppna meny',exact=True).click();p.wait_for_timeout(350)
  assert p.locator('#site-menu').is_visible();assert p.locator('.site-header').bounding_box()==top
  p.screenshot(path=str(out/'menu-mobile.png'))
  p.keyboard.press('Escape');p.wait_for_timeout(230);assert not p.locator('#site-menu').is_visible();assert p.get_by_role('button',name='Öppna meny',exact=True).evaluate('(e)=>e===document.activeElement')
  p.get_by_role('button',name='Öppna meny',exact=True).click();p.locator('#site-menu').get_by_role('link',name='Kliniken',exact=False).first.click();p.wait_for_load_state('networkidle');assert p.url==origin+'/om-oss/';assert p.locator('.editorial-page').count()==1
  report['checks'].append('menu open/close/Escape/focus/layout stability and clinic destination')
  p.goto(origin+'/kunskapsbank/');p.wait_for_load_state('networkidle');assert p.url==origin+'/kunskapsbank/';assert p.locator('[data-library-card]').count()==30
  p.locator('[data-library-search]').fill('axeln');assert p.locator('[data-library-card]:visible').count()>0
  p.locator('[data-library-search]').fill('zzznothing');assert p.locator('[data-library-empty]').is_visible();p.locator('[data-library-reset]').click();assert p.locator('[data-library-card]:visible').count()==30
  p.locator('[data-topic="Axel"]').click();assert p.locator('[data-library-card]:visible').count()<30
  link=p.locator('[data-library-card]:visible h2 a').first;href=link.get_attribute('href');link.click();p.wait_for_load_state('networkidle');assert p.url==origin+href;assert p.locator('.site-header').count()==1
  assert p.locator('link[rel=canonical]').get_attribute('href')=='https://www.kansei.se'+href
  report['checks'].append('knowledge search/filter/reset and article stays on preview origin with original canonical')
  p.goto(origin+'/');p.locator('[data-start-guide]').first.click();p.locator('[data-guide-area="knee"]').click();p.locator('[data-pattern="stairs"]').click();p.locator('[data-safety="continue"]').click();assert p.locator('#guide-content a[href*="bokadirekt.se/boka-tjanst/"]').count()>0
  report['checks'].append('lazy guide actually fetched, knee flow to service-specific booking link')
  for route,name in [('/','home'),('/om-oss/','clinic'),('/kunskapsbank/','knowledge'),('/naprapati/','naprapati'),('/blogg/ont-i-axeln-nar-du-lyfter-armen/','article'),('/kontakt/','contact')]:
   for w,label in [(390,'mobile'),(1440,'desktop')]:
    p.set_viewport_size({'width':w,'height':900});p.goto(origin+route,wait_until='networkidle');p.screenshot(path=str(out/(name+'-'+label+'.png')),full_page=True)
  c.close();c=b.new_context(java_script_enabled=False,viewport={'width':390,'height':844});p=c.new_page()
  for route in ['/om-oss/','/kunskapsbank/','/naprapati/','/rehabilitering/']:
   p.goto(origin+route);assert p.locator('h1').is_visible();assert p.locator('.nojs-nav').is_visible();assert p.locator('.header-book').is_visible()
  p.goto(origin+'/rehabilitering/');assert p.locator('#planKort .reda-portal-link').get_attribute('href')=='/reda/'
  report['checks'].append('content/navigation/booking without JavaScript and existing Reda portal preserved')
  b.close()
 assert not report['errors'],report['errors'];assert not report['missing_resources'],report['missing_resources'];report['result']='PASS'
finally:
 server.shutdown();server.server_close();(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
