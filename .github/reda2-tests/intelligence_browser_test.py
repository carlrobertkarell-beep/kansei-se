"""Exercise Intelligence UI with in-memory fictional services; no external writes."""
import functools,http.server,threading,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
MOCK="""
const payload={schema:6,blueprintId:'knee_pf',goal:'Gå till affären',presentation:'guided',context:{stage:'protected',capacity:'supported',goalProfile:'daily',trainingHistory:'new',equipment:'home'},schedule:{days:[1,3,5]},exercises:[{id:'extension',variantId:'seated',name:'Benspark från stol',side:'right',variantLabel:'Sittande',instructions:['Sitt med stöd för ryggen.','Sträck knät enligt din ordination.'],instruction:'Sitt med stöd för ryggen.',dose:{sets:1,reps:5,label:'1 × 5',rest:60},motionKey:'knee-extension.seated'}]};
window.eiCalls=[];window.eiRows=[];
const sessions=[{id:'session-1',plan_id:'plan-1',plan_version:1,status:'completed',started_at:'2026-09-08T12:00:00Z',completed_at:'2026-09-08T12:10:00Z',payload:{exercises:[]}}];
export async function currentUser(){return {id:'fictional-user'}}
export async function patientBootstrap(){return {userId:'fictional-user',patient:{id:'patient-1',display_name:'Fiktiv testperson'},plan:{id:'plan-2',version:2,payload},sessions,responses:window.eiRows}}
export async function submitTrainingResponse(sid,rid,answers){window.eiCalls.push({sid,rid,answers});if(window.eiCalls.length===1)throw Error('Test: anslutningen avbröts. Försök igen.');const row={id:'response-1',session_id:sid,plan_id:'plan-1',plan_version:1,answers,created_at:'2026-09-10T12:00:00Z'};window.eiRows.push(row);return row}
export async function saveSession(){}
export async function signOut(){}
export async function aal(){return {currentLevel:'aal2'}}
export async function claimClinician(){}
export async function clinicianProfile(){return {role:'clinician'}}
export async function listPatients(){return [{id:'patient-1',display_name:'Fiktiv testperson',auth_user_id:'fictional-user'}]}
export async function patientSummary(){return {plans:[{id:'plan-2',version:2,status:'active',activated_at:'2026-09-09T12:00:00Z',payload},{id:'plan-1',version:1,status:'superseded',activated_at:'2026-09-01T12:00:00Z',payload}],sessions,responses:[{id:'response-1',session_id:'session-1',plan_id:'plan-1',plan_version:1,created_at:'2026-09-10T12:00:00Z',answers:{nextDay:'worse',function:'stable',quality:'controlled',recovery:'ready',otherTraining:'usual',contact:'no'}}]}}
"""
class T(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(ROOT)));threading.Thread(target=c.s.serve_forever,daemon=True).start();c.o=f'http://127.0.0.1:{c.s.server_port}';c.pw=sync_playwright().start();c.b=c.pw.chromium.launch()
 @classmethod
 def tearDownClass(c):c.b.close();c.pw.stop();c.s.shutdown();c.s.server_close()
 def setUp(self):
  self.c=self.b.new_context(viewport={'width':390,'height':844});self.c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(self.o) else r.abort());self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=MOCK));self.p=self.c.new_page();self.errors=[];self.writes=[];self.p.on('pageerror',lambda e:self.errors.append(str(e)));self.p.on('request',lambda r:self.writes.append(r.url) if r.method!='GET' else None);self.p.clock.set_fixed_time('2026-09-10T12:00:00Z')
 def tearDown(self):self.assertEqual(self.errors,[]);self.assertEqual(self.writes,[]);self.c.close()
 def shot(self,name):
  self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),self.p.viewport_size['width']);out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/name),full_page=True)
 def fill(self,host):
  host.locator('[data-open]').click()
  for i,a in enumerate(['worse','stable','ready','high','unknown','same','yes']):
   expect(host.locator('[data-forward]')).to_be_disabled();host.locator('[data-answer='+a+']').click()
   if i<6:host.locator('[data-forward]').click()
 def test_patient_answers_retry_without_loss_and_stay_with_old_plan(self):
  self.p.goto(self.o+'/reda-2/patient.html');self.p.locator('#openResponse').click();h=self.p.locator('#responseForm');self.fill(h);h.locator('[data-forward]').click();expect(h.locator('[role=alert]')).to_contain_text('anslutningen');self.assertEqual(self.p.evaluate('localStorage.length+sessionStorage.length'),0);expect(h.locator('[data-answer=yes]')).to_have_attribute('aria-pressed','true');h.locator('[data-forward]').click();expect(h.locator('.ei-receipt')).to_contain_text('plan v1');expect(self.p.locator('#version')).to_have_text('2');self.assertEqual(self.p.evaluate('eiCalls[0].rid===eiCalls[1].rid'),True);self.assertEqual(self.p.evaluate('eiRows.length'),1);expect(self.p.locator('#responsePrompt')).to_be_hidden();h.locator('.ei-response-history summary').click();expect(h.locator('.ei-response-history')).to_contain_text('Mer besvär än vanligt');self.shot('reda-intelligence-patient-feedback.png')
 def test_help_and_motion_controls_preserve_prescription(self):
  self.p.goto(self.o+'/reda-2/patient.html');self.p.locator('#start').click();before=self.p.locator('#dose').inner_text();expect(self.p.locator('.ei-instructions')).to_be_visible();self.p.locator('#helpToggle').click();expect(self.p.locator('.ei-instructions')).to_have_count(0);self.p.locator('#helpToggle').click();self.p.locator('[data-motion-frame="1"]').click();expect(self.p.locator('[data-motion-frame="1"]')).to_have_attribute('aria-pressed','true');self.p.locator('#motionPlay').click();expect(self.p.locator('#motionPlay')).to_have_text('Pausa rörelsen');self.p.locator('#motionSlow').click();expect(self.p.locator('#motionSlow')).to_have_attribute('aria-pressed','true');self.p.locator('#motionPlay').click();self.assertEqual(self.p.locator('#dose').inner_text(),before);expect(self.p.locator('[data-round="0"]')).to_be_enabled();self.shot('reda-intelligence-patient-guidance.png')
 def test_clinician_version_scope_and_saved_context(self):
  self.p.set_viewport_size({'width':1440,'height':1000});self.p.goto(self.o+'/reda-2/klinik-live.html');self.p.locator('[data-patient="patient-1"]').click();expect(self.p.locator('#intelligencePanel')).to_contain_text('Exercise Intelligence');expect(self.p.locator('#intelligencePanel')).to_contain_text('Låg aktuell belastningstolerans');self.p.locator('[data-worktab="followup"]').click();expect(self.p.locator('.ei-responses')).to_contain_text('Ingen återkoppling');self.p.locator('#reviewVersion').select_option('plan-1');expect(self.p.locator('.ei-responses')).to_contain_text('Förändrade besvär eller funktion');self.shot('reda-intelligence-clinician.png')
 def test_public_example_is_clear_reversible_and_responsive(self):
  self.p.goto(self.o+'/reda-rehab/forhandsvisning.html');self.p.locator('[data-profile=hyrox]').click();self.p.locator('#example-basis summary').click();expect(self.p.locator('#example-basis-body')).to_contain_text('Hyrox');self.p.locator('[data-view=follow]').click();h=self.p.locator('#example-response');self.fill(h);h.locator('[data-forward]').click();expect(h.locator('.ei-receipt')).to_contain_text('bara i den här visningen');self.assertNotIn('Din återkoppling är sparad',h.inner_text());self.p.locator('#reset-demo').click();self.p.locator('[data-view=follow]').click();expect(h.locator('[data-open]')).to_be_visible();self.assertEqual(self.p.evaluate('localStorage.length+sessionStorage.length'),0);self.p.locator('[data-view=plan]').click();self.shot('reda-intelligence-landing-mobile.png');self.p.set_viewport_size({'width':1440,'height':1000});self.shot('reda-intelligence-landing-desktop.png')
if __name__=='__main__':unittest.main(verbosity=2)
