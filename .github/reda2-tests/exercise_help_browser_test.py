"""Real player and guide, fictional APIs only. No patient data or external sends."""
import unittest
from pathlib import Path
from playwright.sync_api import expect
from recovery_browser_test import RecoveryTests
from patient_loop_browser_test import LOOP_MOCK
from handover_browser_test import CLINIC
from plan_authoring_browser_test import T as ClinicBase

PATIENT=LOOP_MOCK+"""
window.helpRequests=[];window.helpRows=[];
export async function submitExerciseHelp(sessionId,exerciseId,requestId,answers){
 window.helpRequests.push({sessionId,exerciseId,requestId,answers});
 if(window.holdHelp)await new Promise(resolve=>window.releaseHelp=resolve);
 let row=window.helpRows.find(x=>x.id===requestId);
 if(!row){row={id:requestId,...answers};window.helpRows.push(row)}
 if(window.loseHelpReceipt){window.loseHelpReceipt=false;throw Error('Kunde inte bekräfta sparningen. Försök igen.')}
 return row;
}
"""
class Patient(RecoveryTests):
 def setUp(self):
  super().setUp()
  self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=PATIENT))
  self.p.evaluate("const d=JSON.parse(localStorage.getItem('test-server'));Object.assign(d.plan.payload.exercises[0],{instructions:['Sitt med stöd.','Följ den ordinerade rörelsen.'],support:'Stol med ryggstöd',prescribedRange:'Det individuellt överenskomna området'});localStorage.setItem('test-server',JSON.stringify(d))")
  self.p.reload();expect(self.p.locator('#app')).to_be_visible();self.p.locator('#start').click()
 def topic(self,t):
  if not self.p.locator('.exercise-coach').get_attribute('open')=='':self.p.locator('.exercise-coach summary').click()
  self.p.locator('[data-coach-topic="'+t+'"]').click()
 def test_help_in_current_exercise_preserves_side_dose_and_requires_outcome(self):
  before=self.p.locator('#dose').inner_text();expect(self.p.locator('#motionSide')).to_have_text('Vänster sida');self.topic('side');expect(self.p.locator('.coach-answer')).to_contain_text('Båda sidor, en i taget');self.assertEqual(self.p.evaluate('helpRows.length'),0)
  self.p.locator('[data-round="0"]').click();expect(self.p.locator('#motionSide')).to_have_text('Höger sida');expect(self.p.locator('#motion svg')).to_have_attribute('data-side','right');self.assertNotIn('scale(-1',self.p.locator('#motion').inner_html())
  self.p.locator('[data-coach-topic="range"]').click();expect(self.p.locator('.coach-answer')).to_contain_text('Det individuellt överenskomna området');self.assertEqual(self.p.locator('#dose').inner_text(),before)
  self.p.locator('[data-coach-clear]').click();expect(self.p.locator('[data-coach-status]')).to_contain_text('upplever instruktionen som tydlig');self.assertEqual(self.p.evaluate('helpRows.length'),1);self.assertEqual(self.p.evaluate('helpRows[0].topics'),['side','range']);self.assertEqual(self.p.evaluate('helpRows[0].outcome'),'clear')
 def test_missing_prescription_cannot_look_like_a_complete_answer(self):
  self.p.locator('#closePlayer').click();self.p.evaluate("const d=JSON.parse(localStorage.getItem('test-server'));delete d.plan.payload.exercises[0].prescribedRange;localStorage.setItem('test-server',JSON.stringify(d))");self.p.reload();self.p.locator('#start').click();self.topic('range');expect(self.p.locator('.coach-answer')).to_contain_text('inte preciserat');expect(self.p.locator('[data-coach-clear]')).to_have_count(0);expect(self.p.locator('[data-coach-contact]')).to_be_visible()
 def test_lost_help_receipt_keeps_question_and_reuses_request(self):
  self.topic('execution');self.p.locator('[data-coach-contact]').click();self.p.locator('[data-coach-form] textarea').fill('Jag undrar över slutläget.');self.p.evaluate('window.loseHelpReceipt=true');self.p.locator('[data-coach-form] [type=submit]').click();expect(self.p.locator('[data-coach-status]')).to_contain_text('Försök igen');expect(self.p.locator('[data-coach-form] textarea')).to_have_value('Jag undrar över slutläget.');self.p.locator('[data-coach-form] [type=submit]').click();expect(self.p.locator('[data-coach-status]')).to_contain_text('sparad hos kliniken');self.assertEqual(self.p.evaluate('helpRows.length'),1);self.assertTrue(self.p.evaluate('helpRequests[0].requestId===helpRequests[1].requestId'));self.assertEqual(self.p.evaluate('helpRows[0].note'),'Jag undrar över slutläget.')
 def test_inflight_help_cannot_switch_exercise_finish_or_logout(self):
  self.topic('setup');self.p.evaluate('window.holdHelp=true');self.p.locator('[data-coach-clear]').click();expect(self.p.locator('#closePlayer')).to_be_disabled();expect(self.p.locator('[data-round="0"]')).to_be_disabled();expect(self.p.locator('#logout')).to_be_disabled();expect(self.p.locator('[data-tab="program"]')).to_be_disabled();self.p.wait_for_function('typeof releaseHelp===\'function\'');self.p.evaluate('releaseHelp()');expect(self.p.locator('[data-coach-status]')).to_contain_text('Sparat');expect(self.p.locator('#closePlayer')).to_be_enabled();expect(self.p.locator('[data-round="0"]')).to_be_enabled();expect(self.p.locator('#next')).to_be_disabled()
 def test_reduced_motion_allows_stills_and_saved_instruction(self):
  self.p.emulate_media(reduced_motion='reduce');self.p.reload();self.p.locator('#start').click();self.p.locator('[data-lesson-mode="watch"]').click();expect(self.p.locator('#motionPlay')).to_be_disabled();self.p.locator('[data-motion-frame="1"]').click();expect(self.p.locator('#motionPhase')).to_have_text('Slutläge');self.topic('execution');expect(self.p.locator('.coach-answer')).to_contain_text('Följ den ordinerade rörelsen.')
 def test_mobile_keyboard_focus_touch_targets_and_rendering(self):
  self.topic('setup');expect(self.p.locator('[data-coach-topic="setup"]')).to_be_focused();self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));self.assertGreaterEqual(self.p.locator('[data-coach-topic="setup"]').bounding_box()['height'],44)
  out=Path('reda2-test-results');out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/'exercise-help-mobile.png'),full_page=True)
  self.p.locator('[data-lesson-mode="watch"]').click();self.p.locator('#motionPlay').click();expect(self.p.locator('#motionPlay')).to_have_text('Pausa rörelsen');self.p.locator('#motionSlow').click();expect(self.p.locator('#motionSlow')).to_have_attribute('aria-pressed','true');self.p.locator('#closePlayer').click();expect(self.p.locator('#player')).to_be_hidden()
 def test_learning_separates_reading_and_motion_and_never_records_repetitions(self):
  before=self.p.locator('#dose').inner_text();expect(self.p.locator('#lessonInstruction')).to_contain_text('Stol med ryggstöd');expect(self.p.locator('#motionPlay')).not_to_be_visible();self.p.locator('#lessonNext').click();expect(self.p.locator('#lessonInstruction')).to_have_text('Sitt med stöd.');expect(self.p.locator('#movementLesson')).to_have_attribute('data-playing','false');self.p.locator('[data-lesson-mode="watch"]').click();expect(self.p.locator('#lessonInstruction')).not_to_be_visible();self.p.locator('#motionPlay').click();expect(self.p.locator('#movementLesson')).to_have_attribute('data-playing','true');self.p.wait_for_function('Number(document.querySelector("#motion").dataset.position)>.003');self.p.locator('#motionPlay').click();position=self.p.locator('#motion').get_attribute('data-position');expect(self.p.locator('#motionPlay')).to_have_text('Fortsätt visningen');self.p.locator('#motionSlow').click();self.assertEqual(self.p.locator('#motion').get_attribute('data-position'),position);self.p.locator('#lessonReady').click();expect(self.p.locator('[data-round="0"]')).to_be_focused();expect(self.p.locator('#sessionProgressText')).to_contain_text('0 av');self.assertEqual(self.p.locator('#dose').inner_text(),before)
 def test_chair_demo_waits_after_each_part_and_can_resume(self):
  self.p.goto(self.origin+'/reda-2/exercise-guide.html');self.p.locator('[data-lesson-mode="watch"]').click();self.p.locator('#motionPlay').click();expect(self.p.locator('#movementLesson')).to_have_attribute('data-playing','false',timeout=9000);expect(self.p.locator('#motionPhase')).to_have_text('Framåtlutning');expect(self.p.locator('#lessonStatus')).to_contain_text('Nästa del väntar');self.assertAlmostEqual(float(self.p.locator('#motion').get_attribute('data-position')),.23);self.p.locator('#lessonNextPart').click();expect(self.p.locator('#motionPhase')).to_have_text('Uppresning');expect(self.p.locator('#movementLesson')).to_have_attribute('data-playing','true');self.p.locator('#motionPlay').click();expect(self.p.locator('#movementLesson')).to_have_attribute('data-playing','false');self.p.locator('[data-lesson-mode="read"]').click();expect(self.p.locator('#lessonInstruction')).to_be_visible();self.assertAlmostEqual(float(self.p.locator('#motion').get_attribute('data-position')),0)
 def test_mobile_learning_card_has_readable_text_and_large_controls(self):
  self.p.goto(self.origin+'/reda-2/exercise-guide.html');expect(self.p.locator('#guideSide')).not_to_be_visible();self.p.locator('#movementLesson').scroll_into_view_if_needed();self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));self.assertGreaterEqual(self.p.locator('#lessonNext').bounding_box()['height'],52);self.assertGreaterEqual(self.p.locator('#lessonInstruction').evaluate('(el)=>parseFloat(getComputedStyle(el).fontSize)'),20)
  out=Path('reda2-test-results');out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/'paced-learning-mobile.png'),full_page=True);self.p.locator('[data-lesson-mode="watch"]').click();self.p.screenshot(path=str(out/'paced-movement-mobile.png'),full_page=True)
 def test_review_guide_all_five_families_and_simulated_case_are_isolated(self):
  self.p.goto(self.origin+'/reda-2/exercise-guide.html');expect(self.p.locator('.preview-note')).to_contain_text('Inga patientuppgifter');
  for n in range(5):
   self.p.locator('#guideExercise').select_option(str(n));self.p.locator('[data-lesson-mode="watch"]').click();self.p.locator('.lesson-stills summary').click();self.p.locator('[data-frame="1"]').click();expect(self.p.locator('#motion svg')).to_have_attribute('data-renderer-version','5');self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
  self.topic('execution');self.p.locator('[data-coach-contact]').click();self.p.locator('[data-coach-form] [type=submit]').click();expect(self.p.locator('#guideResult')).to_contain_text('Så skulle underlaget visas');expect(self.p.locator('[data-coach-status]')).to_contain_text('Inget har skickats eller sparats');self.assertEqual(self.p.locator('script[src*="secure-browser"]').count(),0)
  self.p.set_viewport_size({'width':1280,'height':1000});self.p.screenshot(path='reda2-test-results/exercise-guide-desktop.png',full_page=True)

CLINIC_HELP=CLINIC.replace('export async function dashboardPatient(id)','async function previousDashboard(id)')+"""
export async function dashboardPatient(id){const d=await previousDashboard(id);d.cases=[{id:'help-case',code:'execution_help',status:'open',plan_id:d.patient.plan_id,plan_version:2,created_at:'2026-09-12T10:00:00Z',exercise_help:{exercise_name:'Benspark från stol',exercise:{side:'right',instructions:['Individuell sparad instruktion.']},plan_version:2,topics:['side','execution'],outcome:'needs_help',option_label:'Ordinarie pass',note:'Är det rätt sida?'}}];return d}
"""
class Clinic(ClinicBase):
 def setUp(self):
  super().setUp();self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=CLINIC_HELP));self.p.reload();expect(self.p.locator('[data-detail="a-2"]')).to_be_visible()
 def test_patient_question_is_visible_without_reading_full_card(self):
  self.p.locator('[data-detail="a-2"]').click();expect(self.p.locator('.dash-immediate')).to_contain_text('Benspark från stol');expect(self.p.locator('.dash-immediate')).to_contain_text('Höger sida');expect(self.p.locator('.dash-immediate')).to_contain_text('Är det rätt sida?');self.p.get_by_text('Underlaget bakom förslaget',exact=False).click();self.p.get_by_text('Förklaringar från den sparade övningen',exact=True).click();expect(self.p.locator('.dash-evidence')).to_contain_text('Individuell sparad instruktion.')

def load_tests(loader,tests,pattern):
 return unittest.TestSuite(cls(name)for cls in (Patient,Clinic)for name in cls.__dict__ if name.startswith('test_'))
if __name__=='__main__':unittest.main(verbosity=2)
