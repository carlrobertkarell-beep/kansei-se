"""Review summaries with fictional accounts; no backend mutation or emails."""
import functools,http.server,json,threading,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
MOCK="""
export async function currentUser(){return {id:'fictional-clinician'}}
export async function aal(){return {currentLevel:'aal2'}}
export async function claimClinician(){}
export async function clinicianProfile(){return {role:'clinician'}}
export async function listPatients(){return [{id:'a',display_name:'Fiktiv patient A',auth_user_id:'ua'},{id:'b',display_name:'Fiktiv patient B',auth_user_id:'ub'}]}
export async function patientSummary(id){
 await new Promise(r=>setTimeout(r,id==='a'?350:10));
 const base={activated_at:'2026-09-01T10:00:00Z',payload:{goal:'Mål för '+id,reviewDate:'2026-09-20',schedule:{days:[1,3,5]},exercises:[{id:'chair',name:'Uppresning från stol',variantLabel:'Med stöd',dose:{label:'2 × 8'}}]}};
 return {plans:[{...base,id:'new',version:2,status:'active',activated_at:'2026-09-07T10:00:00Z'},{...base,id:'old',version:1,status:'superseded',payload:{...base.payload,goal:'Tidigare mål för '+id}}],sessions:[{plan_id:'old',plan_version:1,status:'partial',started_at:'2026-09-04T10:00:00Z',payload:{exercises:[{exerciseId:'chair',status:'skipped',feedback:'heavy'}]}}]};
}
"""
class T(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(ROOT)));threading.Thread(target=c.s.serve_forever,daemon=True).start();c.o=f'http://127.0.0.1:{c.s.server_port}';c.pw=sync_playwright().start();c.b=c.pw.chromium.launch()
 @classmethod
 def tearDownClass(c):c.b.close();c.pw.stop();c.s.shutdown();c.s.server_close()
 def setUp(self):
  self.c=self.b.new_context(viewport={'width':1440,'height':1000});self.c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(self.o) else r.abort());self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=MOCK));self.p=self.c.new_page();self.errors=[];self.p.on('pageerror',lambda e:self.errors.append(str(e)));self.p.clock.set_fixed_time('2026-09-10T12:00:00Z');self.p.goto(self.o+'/reda-2/klinik-live.html');self.p.locator('[data-patient="a"]').wait_for()
 def tearDown(self):self.assertEqual(self.errors,[]);self.c.close()
 def test_version_scope_and_disclosure(self):
  self.p.locator('[data-patient="a"]').click();self.p.locator('[data-worktab="followup"]').click();self.p.locator('#reviewSummary h3').first.wait_for();self.assertIn('Mål för a',self.p.locator('#reviewSummary').inner_text());self.assertNotIn('Ta upp vid avstämningen',self.p.locator('#reviewSummary').inner_text());self.p.locator('#reviewVersion').select_option('old');self.assertIn('Tidigare mål för a',self.p.locator('#reviewSummary').inner_text());self.assertIn('1 rapporter om för tungt',self.p.locator('#reviewSummary').inner_text());self.assertIn('1 överhoppade tillfällen',self.p.locator('#reviewSummary').inner_text());self.assertIn('Saknad registrering',self.p.locator('#reviewSummary').inner_text());self.p.locator('.review-exercises summary').first.click();self.assertTrue(self.p.locator('.review-exercises dl').first.is_visible())
 def test_patient_switch_discards_late_response(self):
  self.p.locator('[data-patient="a"]').click();self.p.locator('[data-patient="b"]').click();self.p.locator('[data-worktab="followup"]').click();self.p.wait_for_timeout(650);self.assertIn('Mål för b',self.p.locator('#reviewSummary').inner_text());self.assertNotIn('Mål för a',self.p.locator('#reviewSummary').inner_text())
if __name__=='__main__':unittest.main(verbosity=2)
