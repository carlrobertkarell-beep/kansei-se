"""Actual patient/clinician pages. Fictional APIs, no mail or production data."""
import unittest
from pathlib import Path
from playwright.sync_api import expect
from patient_loop_browser_test import LOOP_MOCK
from recovery_browser_test import RecoveryTests
from handover_browser_test import CLINIC
from plan_authoring_browser_test import T as ClinicBase

PATIENT=LOOP_MOCK+"""
window.barrierRequests=[];window.loseBarrierReceipt=false;
const loops=()=>JSON.parse(localStorage.getItem('barrier-loops')||'[]');
const put=l=>localStorage.setItem('barrier-loops',JSON.stringify(l));
export async function patientBarriers(){
 if(window.failBarriers)throw Error('offline');
 let l=loops();if(!l.length&&read().reflections?.length){l=[{id:'loop-a',case_id:'case-a',source_plan_id:'plan-1',barrier:read().reflections[0].answers.barrier,phase:'needs_context'}];put(l)}
 return l.map(x=>{const s=read().sessions.find(s=>s.plan_id===x.result_plan_id&&s.completed_at);return x.phase==='trying'&&s?{...x,phase:'check_result',session_id:s.id}:x});
}
export async function answerBarrier(id,rid,context){
 window.barrierRequests.push({id,rid,context});const l=loops().map(x=>x.id===id?{...x,context,phase:'ready'}:x);put(l);
 if(window.loseBarrierReceipt){window.loseBarrierReceipt=false;throw Error('Svaret kunde inte bekräftas. Försök igen.')}return l.find(x=>x.id===id);
}
export async function barrierOutcome(id,rid,outcome,sid){const l=loops().map(x=>x.id===id?{...x,outcome,session_id:sid,phase:outcome==='helped'?'helped':'needs_review'}:x);put(l);return l.find(x=>x.id===id)}
window.approveFictionalChange=()=>{const d=read();d.plan={...d.plan,id:'plan-2',version:2};localStorage.setItem('test-server',JSON.stringify(d));put(loops().map(l=>({...l,result_plan_id:'plan-2',result_version:2,phase:'trying'})))};
"""
class Patient(RecoveryTests):
 def setUp(self):
  super().setUp();self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=PATIENT));self.p.reload();expect(self.p.locator('#app')).to_be_visible()
 def finish(self):
  self.p.locator('#start').click();self.p.locator('[data-round="0"]').click();self.p.locator('[data-round="1"]').click();self.p.locator('#next').click();expect(self.p.locator('[data-reflection-save]')).to_be_visible()
 def report(self,barrier='time'):
  self.finish();self.p.locator('[data-barrier="'+barrier+'"]').click();self.p.locator('[data-support="no"]').click();self.p.locator('[data-reflection-save]').click();self.p.locator('[data-reflection-barrier]').click();expect(self.p.locator('[data-barrier-phase="needs_context"]')).to_be_visible()
 def test_time_report_question_reviewed_change_trial_and_targeted_outcome(self):
  self.report();self.p.locator('[data-context-choice][data-value="10"]').click();self.p.locator('[data-barrier-save]').click();expect(self.p.locator('[data-barrier-phase="ready"]')).to_contain_text('10 minuter');self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).plan.id"),'plan-1')
  self.p.evaluate('approveFictionalChange()');self.p.reload();expect(self.p.locator('[data-barrier-phase="trying"]')).to_be_visible();expect(self.p.locator('[data-barrier-outcome="helped"]')).to_have_count(0)
  self.finish();self.p.locator('[data-reflection-later]').click();expect(self.p.locator('[data-barrier-phase="check_result"]')).to_be_visible();self.p.locator('[data-barrier-outcome="helped"]').click();expect(self.p.locator('[data-barrier-phase="helped"]')).to_contain_text('praktiska hindret');self.p.reload();expect(self.p.locator('[data-barrier-phase="helped"]')).to_be_visible()
 def test_context_retry_preserves_choice_and_request_without_duplicate(self):
  self.report();self.p.locator('[data-context-choice][data-value="15"]').click();self.p.evaluate('window.loseBarrierReceipt=true');self.p.locator('[data-barrier-save]').click();expect(self.p.locator('[data-barrier-status]')).to_contain_text('Försök igen');expect(self.p.locator('[data-context-choice][data-value="15"]')).to_have_attribute('aria-pressed','true');self.p.locator('[data-barrier-save]').click();expect(self.p.locator('[data-barrier-phase="ready"]')).to_be_visible();self.assertTrue(self.p.evaluate('barrierRequests[0].rid===barrierRequests[1].rid'));self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('barrier-loops')).length"),1)
 def test_equipment_requires_explicit_choices_and_not_tried_returns_to_clinician(self):
  self.report('equipment');expect(self.p.locator('[data-barrier-save]')).to_be_disabled();self.p.locator('[data-key="equipment"][data-value=\'"home"\']').click();self.p.locator('[data-key="band"][data-value="false"]').click();self.p.locator('[data-key="floorOK"][data-value="true"]').click();self.p.locator('[data-barrier-save]').click();expect(self.p.locator('[data-barrier-phase="ready"]')).to_contain_text('Utan gummiband');self.p.evaluate('approveFictionalChange()');self.p.reload();self.p.locator('.barrier-not-tried summary').click();self.p.locator('[data-barrier-outcome="not_tried"]').click();expect(self.p.locator('[data-barrier-phase="needs_review"]')).to_contain_text('öppen')
 def test_mobile_primary_action_navigation_player_and_layout(self):
  self.p.set_viewport_size({'width':390,'height':844});start=self.p.locator('#start').bounding_box();nav=self.p.locator('.nav').bounding_box();self.assertLess(start['y']+start['height'],nav['y']);self.assertGreaterEqual(start['height'],44)
  self.p.locator('[data-tab="program"]').click();expect(self.p.locator('[data-tab="program"]')).to_have_attribute('aria-current','page');expect(self.p.locator('#program')).to_contain_text('Varje övning har en uppgift');self.p.locator('[data-tab="today"]').click();self.p.locator('#start').click();expect(self.p.locator('#todayCard')).to_be_hidden();self.p.locator('[data-round="0"]').click();expect(self.p.locator('#sessionProgress')).to_have_attribute('value','1');self.p.locator('#closePlayer').click();expect(self.p.locator('#todayCard')).to_be_visible();expect(self.p.locator('#start')).to_be_focused()
  self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));out=Path('reda2-test-results');out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/'patient-experience-mobile.png'),full_page=True);self.p.set_viewport_size({'width':1280,'height':900});self.p.screenshot(path=str(out/'patient-experience-desktop.png'),full_page=True)
 def test_fetch_error_never_looks_like_completed_work_and_reduced_motion_is_respected(self):
  self.report();self.p.evaluate('window.failBarriers=true');self.p.locator('[data-barrier-refresh]').click();expect(self.p.locator('[data-barrier-status]')).to_contain_text('kunde inte hämtas');expect(self.p.locator('[data-barrier-phase="helped"]')).to_have_count(0);self.p.emulate_media(reduced_motion='reduce');self.assertEqual(self.p.locator('#today').evaluate('e=>getComputedStyle(e).animationName'),'none')

CLINIC_LOOP=CLINIC.replace('export async function dashboardPatient(id)','async function previousDashboard(id)')+"""
export async function dashboardPatient(id){const d=await previousDashboard(id);d.barriers=[{id:'loop-a',case_id:'case-current',phase:window.needContext?'needs_context':'ready',source_plan_id:d.patient.plan_id,barrier:'time',context:window.needContext?null:{minutes:10}}];return d}
export async function publishBarrier(input){return publishReviewed(input)}
"""
class Clinic(ClinicBase):
 def setUp(self):
  super().setUp();self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=CLINIC_LOOP));self.p.reload();expect(self.p.locator('[data-detail="a-2"]')).to_be_visible()
 def test_review_links_context_change_and_followup_in_one_approval(self):
  self.p.locator('[data-detail="a-2"]').click();self.p.locator('[data-review-barrier]').click();expect(self.p.locator('.plan-review')).to_contain_text('10 minuter');expect(self.p.locator('[data-diff]')).to_contain_text('Dos');expect(self.p.locator('[data-barrier-due]')).to_be_visible();self.p.locator('.plan-review [data-note]').fill('Patientens tidsutrymme och dos bedömda.');self.p.locator('[data-reviewed]').check();self.p.locator('[data-publish]').click();expect(self.p.locator('[data-status]')).to_contain_text('Kvittot');self.p.locator('[data-publish]').click();expect(self.p.locator('.plan-review')).to_contain_text('Reda följer upp ändringen');self.assertEqual(self.p.evaluate('published.length'),1);self.assertEqual(self.p.evaluate('published[0].loopId'),'loop-a');self.assertTrue(self.p.evaluate('!!published[0].dueDate'));self.assertTrue(self.p.evaluate('publishCalls[0].requestId===publishCalls[1].requestId'))
 def test_unanswered_question_has_clear_owner_and_no_premature_publish(self):
  self.p.evaluate('window.needContext=true');self.p.locator('[data-detail="a-2"]').click();expect(self.p.locator('.barrier-clinic')).to_contain_text('En snabbfråga återstår');expect(self.p.locator('[data-review-barrier]')).to_have_count(0);expect(self.p.locator('[data-review-plan]')).to_have_count(0)
for cls,base in [(Patient,RecoveryTests),(Clinic,ClinicBase)]:
 for name in dir(base):
  if name.startswith('test_') and name not in cls.__dict__:setattr(cls,name,None)
del cls,base,RecoveryTests,ClinicBase
if __name__=='__main__':unittest.main()
