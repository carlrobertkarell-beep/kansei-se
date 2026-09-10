"""Contact plan authoring/serialization/patient rendering using fictional in-browser API stubs."""
import functools,http.server,threading,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
MOCK="""
export async function currentUser(){return {id:'fictional-user'}}
export async function aal(){return {currentLevel:'aal2'}}
export async function claimClinician(){}
export async function clinicianProfile(){return {role:'clinician'}}
export async function listPatients(){return [{id:'a',display_name:'Fiktiv patient A',auth_user_id:'ua'},{id:'b',display_name:'Fiktiv patient B',auth_user_id:'ub'}]}
const base=()=>{const p=window.RedaPlanner.buildProgram({blueprintId:'knee_pf',capacity:'supported',stage:'protected',trainingHistory:'new',equipment:'home',floorOK:true,band:true,goal:'Fiktivt mål'});p.exercises[0].dose.reps=17;p.exercises[0].dose.label='2 omgångar × 17 repetitioner';return p};
export async function patientSummary(id){return {plans:id==='a'?[{id:'active',version:1,status:'active',activated_at:'2026-09-01T10:00:00Z',payload:base()}]:[],sessions:[]}}
export async function createDraft(id,payload){await new Promise(r=>setTimeout(r,200));localStorage.setItem('care-draft',JSON.stringify({id,payload}));return {id:'draft',version:2}}
export async function activatePlan(){throw Error('Activation forbidden in this test')}
export async function invitePatient(){throw Error('Invitations forbidden in this test')}
export async function patientBootstrap(){return {userId:'fictional-user',patient:{id:'a',display_name:'Fiktiv patient A'},plan:{id:'fictional-plan',version:2,payload:JSON.parse(localStorage.getItem('care-draft')).payload},sessions:[]}}
export async function signOut(){}
"""
class T(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(ROOT)));threading.Thread(target=c.s.serve_forever,daemon=True).start();c.o=f'http://127.0.0.1:{c.s.server_port}';c.pw=sync_playwright().start();c.b=c.pw.chromium.launch()
 @classmethod
 def tearDownClass(c):c.b.close();c.pw.stop();c.s.shutdown();c.s.server_close()
 def setUp(self):
  self.c=self.b.new_context(viewport={'width':1440,'height':1050});self.c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(self.o) else r.abort());self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=MOCK));self.p=self.c.new_page();self.err=[];self.p.on('pageerror',lambda e:self.err.append(str(e)));self.p.clock.set_fixed_time('2026-09-10T12:00:00Z');self.p.goto(self.o+'/reda-2/klinik-live.html');self.p.locator('[data-patient="a"]').click();self.p.wait_for_function("document.querySelector('#syncStatus').textContent.includes('Utgår från aktuell')")
 def tearDown(self):self.assertEqual(self.err,[]);self.c.close()
 def remote(self):
  self.p.locator('#careMode').select_option('remote');self.p.locator('#careWeeks').select_option('6');self.p.locator('#careStart').fill('2026-09-10');self.p.locator('#suggestContacts').click()
 def save(self):
  self.p.locator('#saveDraft').click();self.p.wait_for_function("localStorage.getItem('care-draft')!==null")
 def test_remote_dates_and_assessment_gate_preserve_existing_dose(self):
  self.p.locator('#goal').fill('Fiktivt ändrat mål');self.p.locator('#guidance').select_option('trained');self.remote();self.assertTrue(self.p.locator('#activate').is_disabled());self.assertTrue(self.p.locator('#saveDraft').is_enabled());self.assertEqual(self.p.locator('#care-review1-date').input_value(),'2026-09-24');self.p.locator('#assessmentDate').fill('2026-09-09');self.p.locator('#careAssessed').check();self.assertTrue(self.p.locator('#activate').is_enabled());self.save();d=self.p.evaluate("JSON.parse(localStorage.getItem('care-draft')).payload");self.assertEqual(d['careJourney']['mode'],'remote');self.assertEqual(d['exercises'][0]['dose']['reps'],17);self.assertEqual(d['reviewDate'],'2026-09-24')
  out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.locator('#care-title').scroll_into_view_if_needed();self.p.screenshot(path=str(out/'reda-clinic-care.png'))
 def test_draft_roundtrip_displays_contacts_in_patient_view(self):
  self.remote();self.p.locator('#assessmentDate').fill('2026-09-09');self.p.locator('#careAssessed').check();self.save();self.p.set_viewport_size({'width':390,'height':844});self.p.goto(self.o+'/reda-2/patient.html');self.p.locator('#app').wait_for(state='visible');self.assertIn('Videosamtal',self.p.locator('#reviewText').inner_text());self.p.locator('[data-tab="follow"]').click();self.assertIn('På distans · 6 veckor',self.p.locator('#careOverview').inner_text());self.assertEqual(self.p.locator('#careOverview .care-timeline li').count(),3);self.assertIn('Tid',self.p.locator('#reviewText').inner_text());self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),390);out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/'reda-patient-care.png'),full_page=True)
 def test_switching_patient_clears_contact_and_personal_fields(self):
  self.remote();self.p.locator('#assessmentDate').fill('2026-09-09');self.p.locator('#careAssessed').check();self.p.locator('[data-patient="b"]').click();self.p.wait_for_function("!document.querySelector('#careMode').disabled");self.assertEqual(self.p.locator('#careMode').input_value(),'clinic');self.assertFalse(self.p.locator('#careAssessed').is_checked());self.assertEqual(self.p.locator('#assessmentDate').input_value(),'');self.assertEqual(self.p.locator('#goal').input_value(),'')
 def test_patient_cannot_change_during_draft_save(self):
  self.p.locator('#saveDraft').click();self.assertTrue(self.p.locator('[data-patient="b"]').is_disabled());self.assertTrue(self.p.locator('#newPatient').is_disabled());self.p.wait_for_function("localStorage.getItem('care-draft')!==null");self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('care-draft')).id"),'a');self.p.wait_for_function("!document.querySelector('[data-patient=b]').disabled")
 def test_remote_without_fixed_contact_package(self):
  self.p.locator('#careMode').select_option('remote');self.assertEqual(self.p.locator('#careWeeks').input_value(),'0');self.p.locator('#assessmentDate').fill('2026-09-09');self.p.locator('#careAssessed').check();self.assertTrue(self.p.locator('#activate').is_enabled());self.save();d=self.p.evaluate("JSON.parse(localStorage.getItem('care-draft')).payload");self.assertEqual(d['careJourney']['checkpoints'],[]);self.assertEqual(d['reviewDate'],'')
 def test_progression_frame_saved_as_inactive_draft_and_stale_when_prescription_changes(self):
  self.p.locator('.progression-author summary').click()
  for id,value in [('pathTarget','19'),('pathDays','3'),('pathMinDays','7'),('pathEvidenceDays','14'),('pathFrom','2026-09-10'),('pathUntil','2026-10-22')]:self.p.locator('#'+id).fill(value)
  self.p.locator('[data-save-path]').click();self.assertIn('Ram sparad som utkast',self.p.locator('.progression-saved').inner_text());self.save();d=self.p.evaluate("JSON.parse(localStorage.getItem('care-draft')).payload");self.assertEqual(d['progressionDraft']['mode'],'simulation-only');self.assertEqual(d['exercises'][0]['dose']['reps'],17);self.assertEqual(d['progressionDraft']['steps'][1]['plan']['exercises'][0]['dose']['reps'],19)
  self.p.locator('#goal').fill('Nytt fiktivt mål');self.assertIn('behöver förnyas',self.p.locator('.progression-saved').inner_text());self.p.locator('[data-patient="b"]').click();self.p.wait_for_function("!document.querySelector('#careMode').disabled");self.assertEqual(self.p.locator('.progression-saved').count(),0)
 def test_invalid_contact_order_blocks_activation_without_losing_draft(self):
  self.remote();self.p.locator('#assessmentDate').fill('2026-09-09');self.p.locator('#careAssessed').check();self.p.locator('#care-review2-date').fill('2026-09-15');self.p.locator('#care-review2-method').focus();self.assertTrue(self.p.locator('#activate').is_disabled());self.assertIn('ordning',self.p.locator('#careIssues').inner_text());self.assertTrue(self.p.locator('#saveDraft').is_enabled())
if __name__=='__main__':unittest.main(verbosity=2)
