"""UI integration with a deterministic fake server. Does not send email or access patients."""
import functools,http.server,json,threading,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
MOCK="""
const read=()=>JSON.parse(localStorage.getItem('test-server'));
export async function currentUser(){const mode=localStorage.getItem('test-auth');if(mode){const e=Error(mode==='missing'?'Auth session missing!':'Connection failed');e.name=mode==='missing'?'AuthSessionMissingError':'Error';throw e}return {id:'test-user'}}
export async function patientBootstrap(){return {...read(),userId:'test-user'}}
export async function saveSession(planId,s){
 if(localStorage.getItem('test-fail')==='yes')throw Error('offline');
 const data=read(),existing=data.sessions.find(r=>r.client_session_id===s.clientSessionId);
 const row={id:s.clientSessionId,client_session_id:s.clientSessionId,plan_id:planId,plan_version:existing?.plan_version||data.plan.version,status:s.status,started_at:s.startedAt,completed_at:s.completedAt,payload:s.payload};
 data.sessions=[row,...data.sessions.filter(r=>r.client_session_id!==s.clientSessionId)];localStorage.setItem('test-server',JSON.stringify(data));
}
export async function signOut(){}
export async function sendPatientMagicLink(){throw Error('No email in this test')}
"""
class RecoveryTests(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(ROOT)));threading.Thread(target=c.s.serve_forever,daemon=True).start();c.origin=f'http://127.0.0.1:{c.s.server_port}';c.pw=sync_playwright().start();c.b=c.pw.chromium.launch()
 @classmethod
 def tearDownClass(c):c.b.close();c.pw.stop();c.s.shutdown();c.s.server_close()
 def setUp(self):
  self.c=self.b.new_context(viewport={'width':390,'height':844});self.c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(self.origin) else r.abort());self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=MOCK));self.p=self.c.new_page();self.errors=[];self.p.on('pageerror',lambda e:self.errors.append(str(e)))
  fixture={'patient':{'id':'test-patient','display_name':'Fiktiv testperson'},'plan':{'id':'plan-1','version':1,'payload':{'exercises':[{'id':'extension','name':'Benspark från stol','side':'both','dose':{'sets':1,'reps':5},'motionKey':'knee-extension.seated'}]}},'sessions':[]}
  self.c.add_init_script("if(!localStorage.getItem('test-server'))localStorage.setItem('test-server',"+json.dumps(json.dumps(fixture))+");")
  self.p.goto(self.origin+'/reda-2/patient.html');self.p.locator('#app').wait_for(state='visible')
 def tearDown(self):self.assertEqual(self.errors,[]);self.c.close()
 def start_and_mark(self):
  self.p.locator('#start').click();self.p.locator('[data-round="0"]').click();self.p.wait_for_function("document.querySelector('#sync').textContent==='Synkad med kliniken'")
 def test_reload_restores_exact_side_and_session(self):
  self.start_and_mark();sid=self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).sessions[0].client_session_id");self.p.reload();self.p.get_by_role('button',name='Fortsätt påbörjat pass',exact=True).click();self.assertTrue(self.p.locator('[data-round="0"]').is_disabled());self.assertTrue(self.p.locator('[data-round="1"]').is_enabled());self.p.locator('[data-round="1"]').click();self.p.locator('#next').click();self.p.wait_for_function("JSON.parse(localStorage.getItem('test-server')).sessions[0].status==='completed'");rows=self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).sessions");self.assertEqual(len(rows),1);self.assertEqual(rows[0]['client_session_id'],sid)
 def test_failed_save_survives_closing_tab_and_retries(self):
  self.p.evaluate("localStorage.setItem('test-fail','yes')");self.p.locator('#start').click();self.p.locator('[data-round="0"]').click();self.p.locator('#retrySync').wait_for(state='visible');self.p.close();self.p=self.c.new_page();self.p.on('pageerror',lambda e:self.errors.append(str(e)));self.p.goto(self.origin+'/reda-2/patient.html');self.p.locator('#app').wait_for(state='visible');self.p.evaluate("localStorage.removeItem('test-fail')");self.p.locator('#retrySync').click();self.p.wait_for_function("JSON.parse(localStorage.getItem('test-server')).sessions.length===1");self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).sessions[0].payload.exercises[0].roundsDone"),1)
 def test_new_version_closes_old_session_without_moving_rounds(self):
  self.start_and_mark();self.p.evaluate("const d=JSON.parse(localStorage.getItem('test-server'));d.plan.id='plan-2';d.plan.version=2;localStorage.setItem('test-server',JSON.stringify(d))");self.p.reload();self.p.locator('#closePrevious').wait_for(state='visible');self.assertTrue(self.p.locator('#start').is_disabled());self.p.locator('#closePrevious').click();self.p.wait_for_function("!document.querySelector('#start').disabled");r=self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).sessions[0]");self.assertEqual(r['plan_id'],'plan-1');self.assertEqual(r['plan_version'],1);self.assertEqual(r['status'],'partial');self.p.locator('#start').click();self.assertTrue(self.p.locator('[data-round="0"]').is_enabled())
 def test_duplicate_start_does_not_create_two_sessions(self):
  self.p.locator('#start').evaluate('(el)=>{el.click();el.click()}');self.p.locator('#player').wait_for(state='visible');self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).sessions.length"),1)
 def test_signed_out_is_normal_and_real_errors_remain_visible(self):
  self.p.evaluate("localStorage.setItem('test-auth','missing')");self.p.reload();self.p.locator('#auth').wait_for(state='visible');self.p.wait_for_timeout(300);self.assertTrue(self.p.locator('#authError').is_hidden());self.assertTrue(self.p.locator('#app').is_hidden());self.p.evaluate("localStorage.setItem('test-auth','network')");self.p.reload();self.p.locator('#authError').wait_for(state='visible');self.assertEqual(self.p.locator('#authError').inner_text(),'Connection failed')
 def test_reference_review_mobile_and_still_frames(self):
  self.p.goto(self.origin+'/reda-2/motion-reference.html');self.assertEqual(self.p.locator('.reference').count(),7);self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),390);self.p.locator('.reference').nth(2).get_by_role('button',name='Slutläge',exact=True).click();self.assertEqual(self.p.locator('.reference').nth(2).get_by_role('button',name='Slutläge',exact=True).get_attribute('aria-pressed'),'true');self.assertEqual(self.p.locator('svg[data-renderer-version="4"]').count(),7)
if __name__=='__main__':unittest.main(verbosity=2)
