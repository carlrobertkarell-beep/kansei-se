"""Shadow review uses fictional data and the real runtime UI; no external traffic."""
import functools, http.server, threading, unittest
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[2]
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args): pass
class ShadowReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
  threading.Thread(target=cls.server.serve_forever,daemon=True).start()
  cls.origin=f'http://127.0.0.1:{cls.server.server_port}'
  cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch()
 @classmethod
 def tearDownClass(cls):
  cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.server.server_close()
 def test_mobile_desktop_scope_navigation_and_review_retry(self):
  for width in [390,1440]:
   with self.subTest(width=width):
    context=self.browser.new_context(viewport={'width':width,'height':950})
    context.route('**/*',lambda r:r.continue_() if r.request.url.startswith(self.origin) else r.abort())
    context.route('**/shadow-review-fixture',lambda r:r.fulfill(content_type='text/html',body='''<!doctype html><html lang="sv"><head><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/reda-2/runtime-ui.css"><style>body{font:16px system-ui;margin:12px}main{max-width:960px;margin:auto}button{font:inherit;padding:.7rem;cursor:pointer}</style></head><body><main id="engine"></main></body></html>'''))
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.clock.set_fixed_time('2026-09-19T12:00:00Z');page.goto(self.origin+'/shadow-review-fixture')
    page.evaluate('''async()=>{
     const {mountClinicEngine}=await import('/reda-2/runtime-ui.mjs');
     const frame={id:'frame-1',execution:'shadow',status:'approved',current_step:0,current_plan_id:'plan-1',policy:{steps:[{},{}],validFrom:'2026-09-01',validUntil:'2026-10-01'}};
     window.decisions=Array.from({length:7},(_,i)=>({id:'decision-'+i,frame_id:i===0?'old-frame':'frame-1',plan_id:'plan-1',step:0,action:'advance',code:'ready',applied:false,created_at:'2026-09-'+(19-i)+'T10:00:00Z',review:i>0&&i<6?{verdict:'agree',note:'Bedömt i testet.'}:null}));
     window.calls=[];window.failOnce=true;
     const api={engineOverview:async()=>({frames:[frame],decisions:window.decisions,cases:[]}),reviewDecision:async(id,verdict,note)=>{window.calls.push({id,verdict,note});if(window.failOnce){window.failOnce=false;throw Error('Tillfälligt sparfel. Försök igen.')}window.decisions.find(d=>d.id===id).review={verdict,note};return {id}},approveFrame:async()=>{throw Error('Ingen ram ska aktiveras av översikten')}};
     window.active={id:'plan-1',payload:{schema:6,exercises:[]}};
     window.original=JSON.stringify(window.active);
     await mountClinicEngine(document.getElementById('engine'),{api,patientId:'patient-1',active:window.active,getPlan:()=>null,isCurrent:()=>true});
    }''')
    host=page.locator('.shadow-review');expect(host).to_have_attribute('data-shadow-state','review')
    self.assertEqual(host.locator('.shadow-review-counts strong').all_text_contents(),['5','0','0','1'])
    expect(host).to_contain_text('inget automatiskt klartecken')
    self.assertEqual(page.evaluate('calls.length'),0)
    host.locator('[data-next-shadow-review]').click()
    target=page.locator('[data-decision-id="decision-6"]');expect(target).to_be_visible()
    expect(target.locator('select')).to_be_focused();target.locator('select').select_option('disagree')
    target.locator('textarea').fill('Den här bedömningen behöver följas upp.')
    target.locator('button').click();expect(page.locator('.runtime-status')).to_contain_text('sparfel')
    expect(target.locator('textarea')).to_have_value('Den här bedömningen behöver följas upp.')
    target.locator('button').click();expect(host).to_have_attribute('data-shadow-state','attention')
    self.assertEqual(host.locator('.shadow-review-counts strong').all_text_contents(),['5','1','0','0'])
    self.assertEqual(page.evaluate('calls.map(x=>x.id)'),['decision-6','decision-6'])
    self.assertTrue(page.evaluate('JSON.stringify(active)===original'))
    self.assertEqual(errors,[])
    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
    out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True)
    host.screenshot(path=str(out/f'reda-shadow-review-{width}.png'))
    context.close()
if __name__=='__main__':unittest.main(verbosity=2)
