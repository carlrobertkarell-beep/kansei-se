"""Readability checks against generated output in Chromium AND WebKit.
Local HTTP, no external data calls or real bookings. Not a physical iPhone test.
"""
from pathlib import Path
import functools,http.server,threading,json,sys,itertools,traceback
from playwright.sync_api import sync_playwright
root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
manifest=json.loads((root/'__clinic-build.json').read_text())
report={'source':'generated-preview','version':manifest['version'],'engines':{},'result':'RUNNING'}
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def copyfile(self,source,outputfile):
  try:super().copyfile(source,outputfile)
  except (BrokenPipeError,ConnectionResetError):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'

def gap(page,a,b):
 x=page.locator(a).first.bounding_box();y=page.locator(b).first.bounding_box();assert x and y,(a,b)
 return round(y['y']-x['y']-x['height'],2)

def checks(page):
 page.goto(origin+'/kontakt/',wait_until='networkidle')
 r={}
 boxes=page.locator('.contact-actions>.button').evaluate_all('(els)=>els.map(e=>{let b=e.getBoundingClientRect();return {left:b.left,right:b.right,top:b.top,bottom:b.bottom,width:b.width,height:b.height}})')
 distances=[]
 for a,b in itertools.combinations(boxes,2):
  dx=max(b['left']-a['right'],a['left']-b['right']);dy=max(b['top']-a['bottom'],a['top']-b['bottom']);distances.append(max(dx,dy));assert max(dx,dy)>=11.5,('buttons too close',a,b)
 assert all(x['height']>=48 for x in boxes),boxes
 r['button_min_gap']=round(min(distances),2)
 for i in range(1,4):
  sel=f'.contact-task:nth-child({i})'
  g=gap(page,sel+' h3',sel+' p');assert g>=15.5,('heading and paragraph',g);r['task_'+str(i)+'_heading_gap']=g
  if page.locator(sel+' .text-link').count():assert gap(page,sel+' p',sel+' .text-link')>=17.5
 page.goto(origin+'/tjanster/',wait_until='networkidle')
 assert page.locator('#boka-cta h2').evaluate('(e)=>getComputedStyle(e).hyphens')!='auto'
 g=gap(page,'#boka-cta .action-group','#boka-cta .cta-trust');assert g>=27,('CTA-help',g);r['cta_help_gap']=g
 g=gap(page,'#boka-cta .cta-help','#boka-cta .cta-proof');assert g>=23,('help-review',g);r['review_gap']=g
 g=gap(page,'#boka-cta .ct-s','#boka-cta .ct-q');assert g>=9,('stars-review',g);r['stars_quote_gap']=g
 assert page.locator('#boka-cta .ct-q').evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)')>=14
 return r

try:
 with sync_playwright() as pw:
  for name,widths in [('chromium',[320,390,768,1440]),('webkit',[390,430])]:
   browser=getattr(pw,name).launch();ctx=browser.new_context(viewport={'width':390,'height':844},locale='sv-SE',device_scale_factor=1)
   ctx.route('**/*',lambda route:route.continue_() if route.request.url.startswith(origin) else route.abort())
   page=ctx.new_page();errors=[];failed=[]
   page.on('pageerror',lambda error:errors.append(str(error)))
   page.on('response',lambda response:failed.append(response.url) if response.status>=400 and response.url.startswith(origin) else None)
   data={'pages':len(manifest['pages']),'widths':widths,'layout_checks':0,'measurements':{},'flow_checks':[]};report['engines'][name]=data
   for row in manifest['pages']:
    page.goto(origin+row['path'],wait_until='networkidle')
    for width in widths:
     page.set_viewport_size({'width':width,'height':844});page.wait_for_timeout(50)
     sw=page.evaluate('document.documentElement.scrollWidth')
     if sw>width:
      bad=page.locator('main *').evaluate_all('(els)=>els.filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.right>innerWidth+1}).slice(0,8).map(e=>({tag:e.tagName,class:e.className,text:e.textContent.slice(0,100)}))')
      raise AssertionError((row['path'],width,'overflow',sw,bad))
     assert page.locator('.header-book').is_visible(),(row['path'],width)
     data['layout_checks']+=1
   for width in widths:
    page.set_viewport_size({'width':width,'height':844});data['measurements'][str(width)]=checks(page)
   page.set_viewport_size({'width':390,'height':844});page.goto(origin+'/kontakt/')
   page.locator('[data-site-menu]').click();page.wait_for_timeout(380);assert page.locator('#site-menu').is_visible()
   page.locator('[data-site-close]').click();page.wait_for_timeout(240);assert not page.locator('#site-menu').is_visible()
   assert page.locator('[data-site-menu]').evaluate('(e)=>e===document.activeElement')
   page.locator('[data-site-menu]').click();page.wait_for_timeout(380);page.keyboard.press('Escape');page.wait_for_timeout(240);assert not page.locator('#site-menu').is_visible()
   data['flow_checks'].append('menu opening/closing, Escape, focus restoration')
   page.goto(origin+'/kunskapsbank/');page.locator('[data-library-search]').fill('axel');assert page.locator('[data-library-card]:visible').count()>0
   a=page.locator('[data-library-card]:visible h2 a').first;href=a.get_attribute('href');a.click();page.wait_for_load_state('networkidle');assert page.url==origin+href
   data['flow_checks'].append('knowledge search and local article navigation')
   page.goto(origin+'/');page.locator('[data-start-guide]').first.click();page.locator('[data-guide-area="knee"]').click();page.locator('[data-pattern="stairs"]').click();page.locator('[data-safety="continue"]').click();assert page.locator('#guide-content a[href*="bokadirekt.se/boka-tjanst/"]').count()>0
   data['flow_checks'].append('booking guide to knee visit, no external booking submitted')
   # Stress the reading areas using WCAG text-spacing values, not a compliance certification.
   spacing='main *{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}main p{margin-bottom:2em!important}'
   data['text_spacing_stress']=[]
   for route in ['/kontakt/','/tjanster/','/naprapati/','/kunskapsbank/']:
    page.goto(origin+route,wait_until='networkidle');page.add_style_tag(content=spacing);page.wait_for_timeout(100)
    assert page.evaluate('document.documentElement.scrollWidth')<=390,(name,route,'text spacing overflow')
    if route=='/tjanster/':assert gap(page,'#boka-cta .action-group','#boka-cta .cta-trust')>=20
    data['text_spacing_stress'].append(route)
   # Evidence is captured on the ordinary design, without stress overrides.
   for route,label in [('/kontakt/','contact'),('/tjanster/','services'),('/naprapati/','naprapati'),('/','home'),('/kunskapsbank/','knowledge'),('/om-oss/','clinic')]:
    page.goto(origin+route,wait_until='networkidle');page.screenshot(path=str(out/(name+'-'+label+'-mobile.png')),full_page=True)
   page.goto(origin+'/kontakt/',wait_until='networkidle');page.locator('.contact-tasks').screenshot(path=str(out/(name+'-contact-tasks.png')))
   page.goto(origin+'/tjanster/',wait_until='networkidle');page.locator('#boka-cta').screenshot(path=str(out/(name+'-booking-panel.png')))
   # Increased base text size, still normal heading/body flow.
   page.goto(origin+'/kontakt/');page.add_style_tag(content='html{font-size:20px}');assert page.evaluate('document.documentElement.scrollWidth')<=390
   data['flow_checks'].append('contact at 125% root font size')
   assert not errors,errors;assert not failed,failed;data['page_errors']=errors;data['missing_resources']=failed
   ctx.close();browser.close();data['result']='PASS'
 report['result']='PASS'
except Exception as error:
 report['result']='FAIL';report['failure']=str(error);traceback.print_exc();raise
finally:
 server.shutdown();server.server_close();(out/'readability-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
