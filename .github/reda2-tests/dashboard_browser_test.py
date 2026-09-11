"""Fictional dashboard services exercise the rendered UI, never production health data."""
import functools,http.server,threading,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
MOCK="""
let current=null;window.calls=[];window.failList=false;window.stale=false;window.saved=[];
export async function currentUser(){return {id:'fictional-owner'}}
export async function aal(){return {currentLevel:'aal2'}}
export async function claimClinician(){}
export function setWorkspace(w){current=w?.id||null}
export async function listWorkspaces(){return [{id:'a',name:'Fiktiva kliniken A',kind:'clinic',role:'owner',clinical_access:true,activation_enabled:false},{id:'b',name:'Fiktiva kliniken B',kind:'clinic',role:'member',clinical_access:true,activation_enabled:false}]}
export async function workspaceTeam(){return {can_manage:false,members:[],events:[]}}
export async function listPatients(){throw Error('Dashboard must not fetch the entire patient registry')}
const patient=(n,org)=>({patient_id:org+'-'+n,display_name:n===1?'Fiktiv patient <img src=x onerror=alert(1)>':n===999?'Arkiverad Fiktiv 999':'Fiktiv patient '+String(n).padStart(4,'0'),patient_status:n>400?'archived':'active',connected:n<=400,plan_id:n<=400?'plan-'+n:null,plan_version:1,open_count:n<=2?2:0,pending_count:n<=2?2:0,codes:n<=2?['requested_contact','execution_help']:[],last_session:'2026-09-08',last_response:'2026-09-09',needs_review:n<=2,care_focus:'Vänster knä · trappor',care_goal:'Kunna gå till arbetet',stage:'build',sessions_14d:3,latest_report:{function:'stable',created_at:'2026-09-09',plan_version:1},profile:{has_contact:true,handover:n===2?'Arbetar natt. Föredrar kontakt på eftermiddagen.':''}});
export async function dashboard(search='',filter='priority',offset=0){const org=current;window.calls.push(['list',org,search,filter,offset]);await new Promise(r=>setTimeout(r,search==='slow'?650:10));if(window.failList)throw Error('Fiktivt anslutningsfel');let all=Array.from({length:1000},(_,i)=>patient(i+1,org));let rows=all.filter(p=>(!search||p.display_name.toLowerCase().includes(search.toLowerCase()))&&(filter==='priority'?p.needs_review&&!window.saved.some(s=>s.patientId===p.patient_id):filter==='active'?!!p.plan_id:filter==='archived'?p.patient_status==='archived':filter==='waiting'?window.saved.some(s=>s.patientId===p.patient_id):true));return {today:'2026-09-11',total:rows.length,offset,limit:25,counts:{all:1000,active:400,priority:2-window.saved.length,waiting:window.saved.length},patients:rows.slice(offset,offset+25)}}
export async function dashboardPatient(id){const org=current;window.calls.push(['detail',org,id]);await new Promise(r=>setTimeout(r,id.endsWith('-1')?200:10));const p=patient(Number(id.split('-')[1]),org);return {patient:p,token:'token-'+id,today:'2026-09-11',plan:{id:p.plan_id,version:1,goal:'Kunna promenera',exercises:[]},cases:p.pending_count?[{id:'c1',code:'requested_contact',status:'open',created_at:'2026-09-09',plan_version:1,answers:{contact:'yes'}},{id:'c2',code:'execution_help',status:'open',created_at:'2026-09-09',plan_version:1,answers:{quality:'difficult'}}]:[],history:[]}}
export async function dashboardAct(input){window.calls.push(['act',current,input]);await new Promise(r=>setTimeout(r,200));if(window.stale)throw {code:'40001',message:'Underlaget har ändrats. Läs det nya förslaget.'};window.saved.push(input);return {action:input.action,note:input.note,due_date:input.due,case_count:2,plan_changed:false,message_sent:false}}
export async function patientSummary(id){return {plans:[],sessions:[],responses:[]}}
export async function createPatient(name){return {id:'a-1001',display_name:name,status:'active'}}
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
  self.c=self.browser.new_context(viewport={'width':1440,'height':1000});self.c.route('**/*',lambda r:r.continue_()if r.request.url.startswith(self.origin)else r.abort());self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=MOCK));self.p=self.c.new_page();self.errors=[];self.p.on('pageerror',lambda e:self.errors.append(str(e)));self.p.goto(self.origin+'/reda-2/klinik-live.html');self.p.locator('[data-detail="a-2"]').wait_for()
 def tearDown(self):self.assertEqual(self.errors,[]);self.c.close()
 def test_thousand_patient_registry_is_bounded_searchable_and_stable(self):
  expect(self.p.locator('[data-metric="active"] strong')).to_have_text('400');expect(self.p.locator('[data-metric="all"] strong')).to_have_text('1 000');self.p.locator('[data-metric="all"]').click();expect(self.p.locator('.dash-row')).to_have_count(25);self.p.locator('[data-next]').click();self.p.locator('[data-detail="a-26"]').wait_for();self.p.locator('[data-detail="a-26"]').click();expect(self.p.locator('.dash-detail h3')).to_have_text('Fiktiv patient 0026');self.p.locator('[data-full]').click();expect(self.p.locator('#clinicalWorkspace')).to_be_visible();self.p.locator('#backToDashboard').click();expect(self.p.locator('[data-detail="a-26"]')).to_be_visible();self.p.locator('[data-search]').fill('999');expect(self.p.locator('.dash-row')).to_have_count(1);expect(self.p.locator('.dash-row')).to_contain_text('Arkiverad');self.assertEqual(self.p.locator('.dash-row img').count(),0)
 def test_one_click_saves_concrete_proposal_and_opens_next_patient(self):
  self.p.locator('[data-detail="a-1"]').click();self.p.locator('[data-approve]').wait_for();expect(self.p.locator('.dash-detail h3')).to_contain_text('<img');self.assertEqual(self.p.locator('.dash-detail img').count(),0);self.p.locator('[data-action]').select_option('follow_up');self.p.locator('[data-due]').fill('2026-09-12');self.p.locator('[data-note]').fill('Kontakta patienten imorgon om utförandet.');self.p.locator('[data-approve]').click();expect(self.p.locator('#workspaceSelect')).to_be_disabled();expect(self.p.locator('.dash-detail h3')).to_have_text('Fiktiv patient 0002');self.assertEqual(self.p.evaluate('window.saved.length'),1);self.assertEqual(self.p.evaluate('window.saved[0].note'),'Kontakta patienten imorgon om utförandet.');expect(self.p.locator('.dash-message')).to_contain_text('Uppföljning sparad');expect(self.p.locator('.dash-message')).not_to_contain_text('skickat')
 def test_clinician_can_approve_and_send_the_exact_prepared_message(self):
  self.p.locator('[data-detail="a-2"]').click();self.p.locator('[data-approve]').wait_for();expect(self.p.locator('[data-action]')).to_have_value('send_message');body=self.p.locator('[data-note]').input_value();self.assertIn('Vad vill du ha hjälp med',body);self.p.locator('[data-approve]').click();expect(self.p.locator('.dash-message')).to_contain_text('levererat i Reda');self.assertEqual(self.p.evaluate('window.saved[0].note'),body);self.assertEqual(self.p.evaluate('window.saved[0].action'),'send_message')
 def test_stale_evidence_requires_new_review(self):
  self.p.locator('[data-detail="a-2"]').click();self.p.locator('[data-approve]').wait_for();self.p.evaluate('window.stale=true');self.p.locator('[data-approve]').click();expect(self.p.locator('.dash-detail')).to_contain_text('Underlaget har ändrats');self.assertEqual(self.p.evaluate('window.saved.length'),0);self.assertEqual(self.p.locator('[data-approve]').count(),0)
 def test_late_search_and_patient_results_cannot_leak_across_workspaces(self):
  self.p.locator('[data-detail="a-1"]').click();self.p.locator('#workspaceSelect').select_option('b');self.p.locator('[data-detail="b-2"]').wait_for();self.p.wait_for_timeout(250);expect(self.p.locator('.dash-detail')).not_to_be_visible();self.p.locator('[data-metric="all"]').click();self.p.locator('[data-search]').fill('slow');self.p.wait_for_timeout(300);self.p.locator('[data-search]').fill('999');expect(self.p.locator('.dash-row')).to_have_count(1);self.p.wait_for_timeout(700);expect(self.p.locator('.dash-row')).to_contain_text('999')
 def test_fetch_error_is_not_an_empty_queue(self):
  self.p.evaluate('window.failList=true');self.p.locator('[data-refresh]').click();expect(self.p.locator('.dash-message')).to_have_attribute('role','alert');expect(self.p.locator('.dash-message')).to_contain_text('Fiktivt anslutningsfel');self.assertEqual(self.p.locator('.dash-metric').count(),0)
 def test_mobile_and_desktop_proposal_layout(self):
  out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/'dashboard-overview-desktop.png'),full_page=True);self.p.locator('[data-detail="a-2"]').click();self.p.locator('[data-approve]').wait_for();self.p.screenshot(path=str(out/'dashboard-desktop.png'),full_page=True);self.p.set_viewport_size({'width':390,'height':844});self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));self.p.screenshot(path=str(out/'dashboard-mobile.png'),full_page=True)
if __name__=='__main__':unittest.main()
