"""Exercise actual guide screens in Chromium/WebKit. No external calls/bookings.
Reports modal width, actual copy gaps, viewport resizing, enlarged text and 42 routes.
"""
from pathlib import Path
import functools,http.server,threading,json,sys,traceback
from playwright.sync_api import sync_playwright

root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
report={'result':'RUNNING','version':'mobile-guide-v1','engines':{}}
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
    def copyfile(self,source,output):
        try:super().copyfile(source,output)
        except (BrokenPipeError,ConnectionResetError):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'

def box(p,selector):
    r=p.locator(selector).first.bounding_box();assert r,selector;return r

def gap(p,a,b):
    x=box(p,a);y=box(p,b);return round(y['y']-x['y']-x['height'],2)

def open_guide(p):
    p.goto(origin+'/',wait_until='networkidle')
    p.locator('[data-start-guide]').first.click()
    p.locator('[data-guide-area="back"]').wait_for()
    p.wait_for_timeout(280)

def result(p):
    p.locator('[data-guide-area="back"]').click()
    p.locator('[data-pattern="radiating"]').click()
    p.locator('[data-safety="continue"]').click()
    p.locator('.guide-price').wait_for()

def geometry(p,width):
    r=box(p,'#guide-dialog')
    if width<=700:assert abs(r['x'])<=1 and abs(r['width']-width)<=1,('not fullscreen',width,r)
    assert p.locator('#guide-dialog').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1'), 'Dialog horizontal overflow'
    bad=p.locator('#guide-content *:not(.sr-only)').evaluate_all('''els=>els.filter(e=>{let r=e.getBoundingClientRect(),d=document.querySelector('#guide-dialog').getBoundingClientRect();return r.width>1&&(r.left<d.left-1||r.right>d.right+1)}).map(e=>e.tagName+'.'+e.className)''')
    assert not bad,('clipped guide content',bad)
    return r

try:
    with sync_playwright() as pw:
        for name in ['chromium','webkit']:
            browser=getattr(pw,name).launch()
            c=browser.new_context(viewport={'width':390,'height':740},locale='sv-SE')
            requests=[];errors=[]
            c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(origin) else r.abort())
            p=c.new_page();p.on('pageerror',lambda e:errors.append(str(e)))
            p.on('request',lambda r:requests.append(r.url))
            data={'result':'RUNNING','measurements':{},'routes_checked':0,'care_stops':0};report['engines'][name]=data
            for width,height in [(320,700),(390,740),(414,740),(430,844),(768,900),(1440,900)]:
                p.set_viewport_size({'width':width,'height':height});open_guide(p);result(p)
                geometry(p,width)
                measurements={'dialog_width':box(p,'#guide-dialog')['width'],'heading_copy_gap':gap(p,'.result-main h3','.guide-visit-copy'),'copy_booking_gap':gap(p,'.guide-visit-copy','.guide-price'),'price_button_gap':gap(p,'.guide-price','.guide-booking>.button'),'cta_height':box(p,'.guide-booking>.button')['height']}
                assert measurements['heading_copy_gap']>=15.5,measurements
                assert measurements['copy_booking_gap']>=40,measurements
                assert measurements['price_button_gap']>=15,measurements
                assert measurements['cta_height']>=51,measurements
                assert p.locator('.guide-visit-copy').evaluate('(e)=>parseFloat(getComputedStyle(e).lineHeight)/parseFloat(getComputedStyle(e).fontSize)')>=1.6
                if width in (390,414,430):
                    b=box(p,'.guide-booking>.button');assert b['y']+b['height']<height,('CTA initially offscreen',width,b)
                data['measurements'][str(width)]=measurements
                p.locator('.result-details summary').first.click()
                assert p.locator('.result-details details').first.get_attribute('open') is not None
                assert gap(p,'.result-details summary','.result-details details p')>=0
                p.locator('#guide-dialog').evaluate('(e)=>e.scrollTop=e.scrollHeight')
                assert box(p,'.guide-header')['y']>=-1
                assert box(p,'.guide-header')['y']<2
                p.locator('[data-guide-back]').click();assert p.locator('[data-safety="continue"]').count()==1
                p.locator('[data-guide-back]').click();assert p.locator('[data-pattern="radiating"]').count()==1
                p.locator('[data-reset]').click();assert p.locator('[data-guide-area]').count()==7
                p.get_by_role('button',name='Stäng bokningshjälpen').click();assert not p.locator('#guide-dialog').is_visible()
            p.set_viewport_size({'width':390,'height':740});open_guide(p)
            patterns=p.evaluate('Object.entries(window.KanseiAreas).flatMap(([area,v])=>[...v.patterns.map(p=>({area,pattern:p[0],urgent:!!p[4]})),{area,pattern:"unclear",urgent:false}])')
            for route in patterns:
                p.locator('[data-guide-area="'+route['area']+'"]').click()
                p.locator('[data-pattern="'+route['pattern']+'"]').click()
                if route['urgent']:
                    assert p.locator('#guide-content a[href="tel:1177"]').count()==1
                    assert p.locator('#guide-content a[href*="bokadirekt"]').count()==0
                    data['care_stops']+=1
                else:
                    p.locator('[data-safety="continue"]').click()
                    link=p.locator('.guide-booking a');assert '/boka-tjanst/' in link.get_attribute('href')
                    expected='skuldra' if route['area']=='shoulder' else 'naprapati'
                    assert link.get_attribute('href')==p.evaluate('(k)=>window.KanseiBooking[k].url',expected)
                    geometry(p,390)
                data['routes_checked']+=1;p.locator('[data-reset]').click()
            p.locator('[data-guide-area="back"]').click();p.locator('[data-pattern="radiating"]').click();p.locator('[data-safety="care"]').click()
            assert p.locator('#guide-content a[href*="bokadirekt"]').count()==0
            p.locator('[data-reset]').click();p.locator('[data-guide-services]').click();assert p.locator('#guide-content .guide-choice').count()==5
            p.keyboard.press('Escape');assert not p.locator('#guide-dialog').is_visible()
            open_guide(p);p.screenshot(path=str(out/(name+'-areas.png')))
            p.locator('[data-guide-area="back"]').click();p.screenshot(path=str(out/(name+'-patterns.png')))
            p.locator('[data-pattern="radiating"]').click();p.screenshot(path=str(out/(name+'-safety.png')))
            p.locator('[data-safety="continue"]').click();p.screenshot(path=str(out/(name+'-result.png')))
            p.locator('.result-details summary').first.click();p.locator('#guide-dialog').evaluate('(e)=>e.scrollTop=560');p.screenshot(path=str(out/(name+'-details.png')))
            p.set_viewport_size({'width':390,'height':560});geometry(p,390)
            p.locator('#guide-dialog').evaluate('(e)=>e.scrollTop=e.scrollHeight');assert box(p,'.guide-header')['y']>=-1
            p.get_by_role('button',name='Stäng bokningshjälpen').click()
            p.set_viewport_size({'width':390,'height':740});open_guide(p);result(p)
            p.add_style_tag(content='html{font-size:24px}#guide-dialog p{letter-spacing:.12em;word-spacing:.16em;line-height:1.5;margin-bottom:2em}')
            geometry(p,390)
            assert gap(p,'.result-main h3','.guide-visit-copy')>=15
            p.screenshot(path=str(out/(name+'-large-text.png')))
            assert not errors,errors
            assert not [u for u in requests if not u.startswith(origin)],'Unexpected external request'
            data['page_errors']=errors;data['external_requests']=0;data['result']='PASS'
            c.close()
            c=browser.new_context(viewport={'width':390,'height':740},reduced_motion='reduce');p=c.new_page();open_guide(p);result(p)
            assert p.locator('#guide-dialog').evaluate('(e)=>getComputedStyle(e).animationName')=='none'
            c.close();browser.close()
    report['result']='PASS'
except Exception as error:
    report['result']='FAIL';report['error']=str(error);traceback.print_exc();raise
finally:
    (out/'guide-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False));server.shutdown();server.server_close()
