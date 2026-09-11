"""Workspace isolation at the UI boundary, with fictional services only."""
import functools,http.server,threading,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
MOCK="""
let current=null;window.orgCalls=[];window.clinical=true;
export async function currentUser(){return {id:'fictional-owner'}}
export async function aal(){return {currentLevel:'aal2'}}
export async function claimClinician(){}
export async function listWorkspaces(){return [{id:'a',name:'Fiktiva kliniken A',kind:'clinic',role:'owner',clinical_access:window.clinical,activation_enabled:false},{id:'b',name:'Fiktiva kliniken B',kind:'clinic',role:'member',clinical_access:true,activation_enabled:false},{id:'direct',name:'Reda · direktverksamhet',kind:'direct',role:'owner',clinical_access:false,activation_enabled:false}]}
export function setWorkspace(w){current=w?.id||null}
export async function listPatients(){const id=current;window.orgCalls.push(['patients',id]);return [{id,display_name:'Fiktiv patient i klinik '+id.toUpperCase(),auth_user_id:'fictional-patient'}]}
export async function patientSummary(id){await new Promise(r=>setTimeout(r,id==='a'?700:10));return {plans:[{id:'plan-'+id,version:1,status:'active',activated_at:'2026-09-01',payload:window.RedaPlanner.buildProgram({blueprintId:'knee_pf',capacity:'supported',stage:'protected',equipment:'home',floorOK:true,band:true,goal:'Enbart klinik '+id.toUpperCase()})}],sessions:[]}}
export async function workspaceTeam(){return {can_manage:current!=='b',events:[],members:[{user_id:'fictional-owner',display_name:'Fiktiv ägare',role:'owner',clinical_access:current==='a'&&window.clinical,clinical_eligible:true,status:'active',revision:1,is_self:true}]}}
export async function updateMembership(member,changes){window.orgCalls.push(['role',current,changes]);window.clinical=changes.clinical_access}
export async function clinicInbox(){const org=current;await new Promise(r=>setTimeout(r,org==='a'?900:20));return {total:0,counts:{open:0,acknowledged:0,resolved:0},cases:[],reviews:{agree:org==='a'?99:0,disagree:0,uncertain:0}}}
export async function signOut(){}
"""
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
class T(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(ROOT)));threading.Thread(target=c.s.serve_forever,daemon=True).start();c.origin=f'http://127.0.0.1:{c.s.server_port}';c.pw=sync_playwright().start();c.browser=c.pw.chromium.launch()
 @classmethod
 def tearDownClass(c):c.browser.close();c.pw.stop();c.s.shutdown();c.s.server_close()
 def setUp(self):
  self.c=self.browser.new_context(viewport={'width':1440,'height':1000});self.c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(self.origin) else r.abort());self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=MOCK));self.p=self.c.new_page();self.errors=[];self.p.on('pageerror',lambda e:self.errors.append(str(e)));self.p.goto(self.origin+'/reda-2/klinik-live.html');self.p.locator('[data-patient="a"]').wait_for()
 def tearDown(self):
  self.assertEqual(self.errors,[]);self.c.close()
 def test_late_patient_and_inbox_results_cannot_repopulate_another_workspace(self):
  self.p.locator('[data-patient="a"]').click();self.p.locator('#workspaceSelect').select_option('b');self.p.locator('[data-patient="b"]').click();self.p.wait_for_function("document.querySelector('#goal').value==='Enbart klinik B'");self.p.wait_for_timeout(1000)
  self.assertEqual(self.p.locator('#goal').input_value(),'Enbart klinik B');self.assertNotIn('kliniken A',self.p.locator('#clinicalWorkspace').inner_text());self.assertNotIn('99 instämmer',self.p.locator('#clinicInbox').inner_text());self.assertTrue(self.p.locator('#activate').is_disabled())
  out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/'workspaces-clinic-desktop.png'),full_page=True)
 def test_direct_business_never_fetches_clinic_patients(self):
  self.p.locator('#workspaceSelect').select_option('direct');expect(self.p.locator('#workspaceEmpty')).to_be_visible();expect(self.p.locator('#clinicalWorkspace')).not_to_be_visible();self.assertIn('En egen plats',self.p.locator('#workspaceEmpty').inner_text());self.assertEqual(self.p.evaluate("window.orgCalls.filter(x=>x[0]==='patients'&&x[1]==='direct').length"),0)
  self.p.set_viewport_size({'width':390,'height':844});self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/'workspaces-direct-mobile.png'),full_page=True)
 def test_role_change_is_reviewed_and_clears_clinical_view(self):
  self.p.locator('.team-panel>summary').click();self.p.locator('.team-member details>summary').click();self.p.locator('input[name="clinical"]').uncheck();self.p.get_by_role('button',name='Granska ändring').click();self.assertIn('utan behandlarbehörighet',self.p.locator('.team-confirm').inner_text());self.assertEqual(self.p.evaluate("window.orgCalls.filter(x=>x[0]==='role').length"),0);self.p.get_by_role('button',name='Spara behörighet').click();expect(self.p.locator('#workspaceEmpty')).to_be_visible();expect(self.p.locator('#clinicalWorkspace')).not_to_be_visible();self.assertEqual(self.p.locator('#patients').inner_text(),'');self.assertIn('Behörigheten är sparad',self.p.locator('#workspaceMessage').inner_text())
if __name__=='__main__':unittest.main()
