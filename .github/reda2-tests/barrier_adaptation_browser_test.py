"""Patient barrier -> exact active plan -> reviewed draft, with fictional services."""
import unittest
from playwright.sync_api import expect
from plan_authoring_browser_test import T as Base,MOCK,ROOT

SUPPORT_MOCK=MOCK.replace('export async function dashboardPatient(id)', 'async function baseDashboardPatient(id)').replace('export async function patientSummary(id)', 'async function basePatientSummary(id)')+"""
window.barrier='time';window.changedEvidence=false;window.newerDraft=false;
function activePayload(){
 const P=window.RedaPlanner;let p=P.buildProgram({blueprintId:'knee_pf',stage:'build',capacity:'standard',trainingHistory:'regular',goalProfile:'daily',guidance:'guided',equipment:'home',floorOK:true,band:true,goal:'Kunna gå i trappor',patientName:'Fiktiv patient 0002'});
 if(!p.exercises.some(x=>x.id==='bridge'))p.exercises.push(P.exerciseFor('bridge',p.context));
 p=P.editExercise(p,0,{sets:3,reps:7,prescribedLoad:'Individuell vikt',prescribedRange:'Individuellt omfång'});return p;
}
export async function dashboardPatient(id){const d=await baseDashboardPatient(id);d.token=window.changedEvidence?'changed':'fixed';d.cases=[{id:'case-current',code:window.barrier==='equipment'?'changed_environment':'training_barrier',status:'open',plan_version:1,reflection:{id:'reflection-current',plan_id:d.patient.plan_id,plan_version:1,answers:{barrier:window.barrier,support:'no',exerciseId:null},created_at:'2026-09-11'}}];return d;}
export async function patientSummary(id){const p={id:'plan-2',version:1,status:'active',patient_id:id,payload:activePayload()};return {plans:window.newerDraft?[{...p,id:'newer',version:2,status:'draft'},p]:[...window.drafts,p],sessions:[],responses:[]};}
"""
class T(Base):
 def setUp(self):
  super().setUp();self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=SUPPORT_MOCK));self.p.reload();expect(self.p.locator('[data-detail="a-2"]')).to_be_visible()
 def open_adaptation(self):
  self.p.locator('[data-detail="a-2"]').click();expect(self.p.locator('[data-adjust-plan]')).to_have_text('Granska EI:s plananpassning');self.p.locator('[data-adjust-plan]').click();expect(self.p.locator('[data-barrier-adaptation]')).to_be_visible()
 def test_time_barrier_prepares_a_comparison_then_saves_only_the_reviewed_draft(self):
  self.open_adaptation();expect(self.p.locator('[data-candidate]')).to_contain_text('En omgång mindre');expect(self.p.locator('[data-candidate] table')).not_to_have_count(0);expect(self.p.locator('[data-edit="sets"][data-index="0"]')).to_have_value('3');self.assertEqual(self.p.evaluate('window.drafts.length'),0)
  self.p.locator('[data-apply]').click();expect(self.p.locator('[data-edit="sets"][data-index="0"]')).to_have_value('2');p=self.save();self.assertEqual(p['exercises'][0]['dose']['reps'],7);self.assertEqual(p['exercises'][0]['prescribedLoad'],'Individuell vikt');self.assertEqual(p['exercises'][0]['prescribedRange'],'Individuellt omfång');expect(self.p.locator('#activate')).to_be_disabled();self.assertEqual(self.p.evaluate('window.saved.length'),0)
 def test_changed_evidence_and_newer_draft_stop_automatic_preparation(self):
  self.p.locator('[data-detail="a-2"]').click();expect(self.p.locator('[data-adjust-plan]')).to_be_visible();self.p.evaluate('window.changedEvidence=true');self.p.locator('[data-adjust-plan]').click();expect(self.p.locator('#deliveryStatus')).to_contain_text('Underlaget har ändrats');expect(self.p.locator('[data-candidate]')).to_be_hidden();self.assertEqual(self.p.evaluate('window.drafts.length'),0)
  self.p.locator('#backToDashboard').click();self.p.locator('[data-detail="a-2"]').click();self.p.evaluate('window.newerDraft=true');self.p.locator('[data-adjust-plan]').click();expect(self.p.locator('#deliveryStatus')).to_contain_text('annat planutkast');expect(self.p.locator('[data-candidate]')).to_be_hidden()
 def test_manual_changes_invalidate_barrier_candidate_and_mobile_comparison_fits(self):
  self.open_adaptation();self.p.set_viewport_size({'width':390,'height':844});self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/'barrier-adaptation-mobile.png'),full_page=True);self.p.set_viewport_size({'width':1440,'height':1000});self.p.screenshot(path=str(out/'barrier-adaptation-desktop.png'),full_page=True);self.p.locator('[data-day="2"]').click();self.p.locator('[data-barrier-option="0"]').click();expect(self.p.locator('#planAuthoring [role="alert"]')).to_contain_text('Planen har ändrats');expect(self.p.locator('[data-candidate]')).to_be_hidden();self.assertEqual(self.p.evaluate('window.drafts.length'),0)
 def test_equipment_needs_a_constraint_choice_before_any_proposal(self):
  self.p.evaluate("window.barrier='equipment'");self.open_adaptation();expect(self.p.locator('[data-candidate]')).to_be_hidden();expect(self.p.locator('[data-barrier-adaptation]')).to_contain_text('Välj efter avstämning');self.p.locator('[data-barrier-option]').first.click();expect(self.p.locator('[data-candidate]')).to_be_visible();self.assertEqual(self.p.evaluate('window.drafts.length'),0)
for name in dir(Base):
 if name.startswith('test_') and name not in T.__dict__:setattr(T,name,None)
del Base
if __name__=='__main__':unittest.main()
