"""Interaction and content-gutter regressions for booking versus reading.
Runs against the exact generated export before upload. No external bookings.
"""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup as BS
from playwright.sync_api import sync_playwright
import functools, http.server, threading, json, os, sys, traceback
root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
manifest=json.loads((root/'__clinic-build.json').read_text());assert manifest.get('intent_pass')
report={'result':'RUNNING','engines':{},'links_checked':0}
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def copyfile(self,source,output):
  try:super().copyfile(source,output)
  except (BrokenPipeError,ConnectionResetError):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
routes=['/kunskapsbank/axel/','/kunskapsbank/kna/']+[p['path'] for p in manifest['pages'] if p['path'].startswith(('/kunskapsbank/axel/','/kunskapsbank/kna/')) and p['path'].count('/')==4]
for route in ['/']+routes:
 doc=BS((root/route.lstrip('/')/'index.html').read_text(),'html.parser')
 for a in doc.select('.home-reading a,.hub-guide,.hub-next a'):
  u=urlsplit(a['href']);assert not u.netloc,(route,a['href'],'unexpected host');target=root/unquote(u.path).lstrip('/')
  assert (target/'index.html').is_file(),(route,a['href'],'missing target')
  if a.get('class') and ('hub-guide' in a['class']):
   target_doc=BS((target/'index.html').read_text(),'html.parser');assert target_doc.h1 and target_doc.select_one('.site-header')
  report['links_checked']+=1
try:
 with sync_playwright() as pw:
  engines=['chromium'] if os.environ.get('KANSEI_LOCAL_CHROMIUM') else ['chromium','webkit']
  for engine in engines:
   args={'executable_path':os.environ['KANSEI_LOCAL_CHROMIUM']} if engine=='chromium' and os.environ.get('KANSEI_LOCAL_CHROMIUM') else {}
   browser=getattr(pw,engine).launch(**args);ctx=browser.new_context(viewport={'width':390,'height':844},locale='sv-SE')
   ctx.route('**/*',lambda r:r.continue_() if r.request.url.startswith(origin) else r.abort())
   page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   record={'layout_cases':0,'min_gutter':999,'flows':[]};report['engines'][engine]=record
   for route in routes:
    page.goto(origin+route,wait_until='networkidle')
    for width in [320,390,430,768,1440]:
     page.set_viewport_size({'width':width,'height':844});page.wait_for_timeout(80)
     assert page.evaluate('document.documentElement.scrollWidth')<=width,(engine,route,width,'overflow')
     selector='.hub-head h1,.hub-head .hub-lead,.hub-crumbs,.hub-grid' if page.locator('.knowledge-hub').count() else '.article-main h1,.article-main>.lead'
     boxes=page.locator(selector).evaluate_all('(els)=>els.map(e=>{let r=e.getBoundingClientRect();return {left:r.left,right:r.right,text:e.textContent.slice(0,40)}})')
     for box in boxes:
      assert box['left']>=21.5 and box['right']<=width-21.5,(engine,route,width,'gutter',box)
      record['min_gutter']=min(record['min_gutter'],round(box['left'],1),round(width-box['right'],1))
     if page.locator('.hub-title').count():
      size=page.locator('.hub-title').evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)');assert size<=42 if width<=430 else size<=73
      if width<=430:
       box=page.locator('.hub-guide').first.bounding_box();assert box['y']<844,(route,width,'no first guide in initial viewport')
     record['layout_cases']+=1
   page.set_viewport_size({'width':390,'height':844});page.goto(origin+'/',wait_until='networkidle')
   assert page.locator('#hitta-ratt [data-area]').count()==7
   assert page.locator('main .cluster-entry').count()==0
   assert page.locator('.home-reading [data-area],.home-reading [data-start-guide]').count()==0
   assert page.locator('.home-reading a[href^="/blogg/"]').count()==3
   page.locator('#hitta-ratt [data-area="shoulder"]').click();assert page.locator('#guide-dialog').is_visible()
   page.locator('#guide-content').get_by_text('Vad känner du i axeln?',exact=True).wait_for(state='visible')
   page.locator('#guide-dialog [data-close]').click()
   record['flows'].append('Homepage Axel opens booking patterns, not a knowledge hub')
   link=page.locator('.home-reading .reading-story').first;url=link.get_attribute('href');link.click();page.wait_for_load_state('networkidle');assert page.url==origin+url;assert not page.locator('#guide-dialog').is_visible()
   record['flows'].append('Homepage reading card opens local article, never a booking modal')
   for slug in ['axel','kna']:
    page.goto(origin+'/kunskapsbank/');page.locator(f'.knowledge-feature[href="/kunskapsbank/{slug}/"]').click();page.wait_for_load_state('networkidle')
    assert page.locator('.knowledge-hub').count()==1
    assert page.locator('.hub-guide').count()==6
    assert 'BEFINTLIG GUIDE' not in page.locator('main').inner_text()
    for i in range(6):
     a=page.locator('.hub-guide').nth(i);url=a.get_attribute('href');a.click();page.wait_for_load_state('networkidle');assert page.url==origin+url
     assert page.locator('h1').count()==1;assert page.locator('.site-header').count()==1
     page.go_back(wait_until='networkidle');assert page.locator('.knowledge-hub').count()==1
    page.locator('.hub-next [data-area]').click();assert page.locator('#guide-dialog').is_visible()
   record['flows'].append('Knowledge library -> each hub -> all 12 articles -> browser back and optional booking')
   for route in routes[:2]:
    page.goto(origin+route);page.add_style_tag(content='main *{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}main p{margin-bottom:2em!important}')
    assert page.evaluate('document.documentElement.scrollWidth')<=390,(engine,route,'text spacing stress')
   for route,label in [('/','homepage'),('/kunskapsbank/axel/','shoulder'),('/kunskapsbank/kna/','knee'),('/kunskapsbank/axel/ont-i-axeln-pa-natten/','article')]:
    for width,device in [(390,'mobile'),(1440,'desktop')]:
     page.set_viewport_size({'width':width,'height':844});page.goto(origin+route,wait_until='networkidle')
     if route=='/':
      page.locator('.reading-feature img').scroll_into_view_if_needed();page.wait_for_timeout(500)
      page.locator('.reading-feature img').evaluate('(e)=>e.decode()')
      page.evaluate('window.scrollTo({top:0,behavior:"instant"})');page.wait_for_timeout(100)
      page.screenshot(path=str(out/f'{engine}-homepage-{device}.png'),full_page=True)
     else:page.screenshot(path=str(out/f'{engine}-{label}-{device}.png'),full_page=True)
   ctx.close();ctx=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844});page=ctx.new_page();page.goto(origin+'/kunskapsbank/axel/')
   a=page.locator('.hub-guide').first;url=a.get_attribute('href');a.click();assert page.url==origin+url
   page.goto(origin+'/');page.locator('#hitta-ratt [data-area="shoulder"]').click();assert page.url==origin+'/hjalp-mig-boka/'
   record['flows'].append('Reading and booking fallback work without JavaScript')
   assert not errors,errors;record['javascript_errors']=errors;record['result']='PASS';ctx.close();browser.close()
 report['result']='PASS'
except Exception as e:report['result']='FAIL';report['failure']=str(e);traceback.print_exc();raise
finally:
 server.shutdown();server.server_close();(out/'intent-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
