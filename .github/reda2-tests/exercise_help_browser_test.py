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
  if not self.p.locator('#playerHelp').evaluate('(el)=>el.open'):self.p.locator('#openExerciseHelp').click()
  self.p.locator('[data-coach-topic="'+t+'"]').click()
 def shot(self,name):
  out=Path('reda2-test-results');out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/name))
 def test_help_in_current_exercise_preserves_side_dose_and_requires_outcome(self):
  before=self.p.locator('#dose').inner_text();self.topic('side');expect(self.p.locator('.coach-answer')).to_contain_text('Båda sidor, en i taget');self.assertEqual(self.p.evaluate('helpRows.length'),0)
  self.p.locator('[data-close-sheet="playerHelp"]').click();self.p.locator('[data-round="0"]').click();expect(self.p.locator('#motionSide')).to_have_text('Höger sida');expect(self.p.locator('#motion svg')).to_have_attribute('data-side','right');self.assertNotIn('scale(-1',self.p.locator('#motion').inner_html())
  self.topic('range');expect(self.p.locator('.coach-answer')).to_contain_text('Det individuellt överenskomna området');self.assertEqual(self.p.locator('#dose').inner_text(),before);self.p.locator('[data-coach-clear]').click();expect(self.p.locator('[data-coach-status]')).to_contain_text('upplever instruktionen som tydlig');self.assertEqual(self.p.evaluate('helpRows.length'),1);self.assertEqual(self.p.evaluate('helpRows[0].topics'),['side','range'])
 def test_missing_prescription_cannot_look_like_a_complete_answer(self):
  self.p.locator('#closePlayer').click();self.p.evaluate("const d=JSON.parse(localStorage.getItem('test-server'));delete d.plan.payload.exercises[0].prescribedRange;localStorage.setItem('test-server',JSON.stringify(d))");self.p.reload();self.p.locator('#start').click();self.topic('range');expect(self.p.locator('.coach-answer')).to_contain_text('inte preciserat');expect(self.p.locator('[data-coach-clear]')).to_have_count(0);expect(self.p.locator('[data-coach-contact]')).to_be_visible()
 def test_lost_help_receipt_keeps_question_and_reuses_request(self):
  self.topic('execution');self.p.locator('[data-coach-contact]').click();self.p.locator('[data-coach-form] textarea').fill('Jag undrar över slutläget.');self.p.evaluate('window.loseHelpReceipt=true');self.p.locator('[data-coach-form] [type=submit]').click();expect(self.p.locator('[data-coach-status]')).to_contain_text('Försök igen');expect(self.p.locator('[data-coach-form] textarea')).to_have_value('Jag undrar över slutläget.');self.p.locator('[data-coach-form] [type=submit]').click();expect(self.p.locator('[data-coach-status]')).to_contain_text('sparad hos kliniken');self.assertEqual(self.p.evaluate('helpRows.length'),1);self.assertTrue(self.p.evaluate('helpRequests[0].requestId===helpRequests[1].requestId'))
 def test_inflight_help_cannot_switch_exercise_finish_or_logout(self):
  self.topic('setup');self.p.evaluate('window.holdHelp=true');self.p.locator('[data-coach-clear]').click();expect(self.p.locator('#closePlayer')).to_be_disabled();expect(self.p.locator('[data-round="0"]')).to_be_disabled();expect(self.p.locator('#logout')).to_be_disabled();expect(self.p.locator('[data-tab="program"]')).to_be_disabled();self.p.wait_for_function('typeof releaseHelp===\'function\'');self.p.evaluate('releaseHelp()');expect(self.p.locator('[data-coach-status]')).to_contain_text('Sparat');expect(self.p.locator('[data-round="0"]')).to_be_enabled();expect(self.p.locator('#next')).to_be_disabled()
 def test_reduced_motion_keeps_start_still_and_can_show_an_endpoint(self):
  self.p.emulate_media(reduced_motion='reduce');self.p.reload();self.p.locator('#start').click();expect(self.p.locator('#motionPlay')).to_be_disabled();self.p.locator('#lessonGuided').click();self.p.locator('.lesson-stills summary').click();self.p.locator('[data-motion-frame="1"]').click();expect(self.p.locator('#lessonDetails')).not_to_be_visible();expect(self.p.locator('#motionPhase')).to_have_text('Slutläge');self.assertEqual(self.p.locator('#movementLesson').get_attribute('data-playing'),'false')
 def test_phone_first_frame_shows_exercise_dose_image_and_completion_without_scroll(self):
  expect(self.p.locator('#motionStudio')).to_be_visible();expect(self.p.locator('#motionSide')).to_have_text('Vänster sida');expect(self.p.locator('.nav')).not_to_be_visible();expect(self.p.locator('#lessonDetails')).not_to_be_visible();expect(self.p.locator('#sessionProgressText')).to_contain_text('0 av')
  for selector in ['#exName','#dose','#motionStudio','#motionPlay','#openExerciseHelp','[data-round="0"]']:
   box=self.p.locator(selector).bounding_box();self.assertGreaterEqual(box['y'],-1);self.assertLessEqual(box['y']+box['height'],844)
  self.assertGreater(self.p.locator('#motionStudio').bounding_box()['height'],220);self.assertEqual(self.p.evaluate('helpRows.length'),0);self.shot('phone-patient-ready.png')
 def test_whole_demonstration_runs_once_without_registering_training(self):
  self.p.locator('#motionPlay').click();expect(self.p.locator('#movementLesson')).to_have_attribute('data-playing','true');expect(self.p.locator('#lessonDetails')).not_to_be_visible();expect(self.p.locator('#movementLesson')).to_have_attribute('data-playing','false',timeout=17000);expect(self.p.locator('#motionPlay')).to_have_text('Visa igen');self.assertAlmostEqual(float(self.p.locator('#motion').get_attribute('data-position')),0);expect(self.p.locator('#sessionProgressText')).to_contain_text('0 av')
 def test_instruction_sheet_pauses_motion_preserves_position_and_returns_to_same_screen(self):
  self.p.locator('#motionPlay').click();self.p.wait_for_function('Number(document.querySelector("#motion").dataset.position)>.003');self.p.locator('#lessonGuided').click();expect(self.p.locator('#movementLesson')).to_have_attribute('data-playing','false');self.p.locator('#lessonNext').click();expect(self.p.locator('#lessonInstruction')).to_have_text('Sitt med stöd.');self.shot('phone-instruction-sheet.png');self.p.locator('#lessonCloseDetails').click();expect(self.p.locator('#lessonGuided')).to_be_focused();self.p.locator('[data-round="0"]').click();expect(self.p.locator('#motionSide')).to_have_text('Höger sida');self.p.locator('#lessonGuided').click();expect(self.p.locator('#lessonInstruction')).to_have_text('Sitt med stöd.')
 def test_enlargement_keeps_one_illustration_and_keyboard_exit(self):
  self.p.locator('#lessonExpand').click();expect(self.p.locator('#lessonFocus')).to_be_visible();self.assertEqual(self.p.locator('#motion').count(),1);self.assertGreater(self.p.locator('#motionStudio').bounding_box()['height'],500);self.shot('phone-enlarged-motion.png');self.p.keyboard.press('Escape');expect(self.p.locator('#lessonFocus')).not_to_be_visible();expect(self.p.locator('#lessonExpand')).to_be_focused();expect(self.p.locator('#sessionProgressText')).to_contain_text('0 av')
 def test_chair_parts_stop_and_return_to_the_same_training_action(self):
  self.p.goto(self.origin+'/reda-2/exercise-guide.html');self.p.locator('#start').click();self.p.locator('#lessonGuided').click();self.p.locator('[data-lesson-mode="watch"]').click();self.p.locator('[data-lesson-part="0"]').click();expect(self.p.locator('#lessonDetails')).not_to_be_visible();expect(self.p.locator('#movementLesson')).to_have_attribute('data-playing','false',timeout=9000);self.assertAlmostEqual(float(self.p.locator('#motion').get_attribute('data-position')),.23);expect(self.p.locator('[data-round="0"]')).to_be_visible();expect(self.p.locator('#sessionProgressText')).to_contain_text('0 av')
 def test_prescribed_rest_never_completes_next_round_or_changes_dose(self):
  self.p.locator('#closePlayer').click();self.p.evaluate("const d=JSON.parse(localStorage.getItem('test-server'));d.plan.payload.exercises[0].dose.rest=1;localStorage.setItem('test-server',JSON.stringify(d))");self.p.reload();self.p.locator('#start').click();before=self.p.locator('#dose').inner_text();self.p.locator('[data-round="0"]').click();expect(self.p.locator('#player')).to_have_attribute('data-resting','true');expect(self.p.locator('#restStatus')).to_contain_text('Vilotiden är slut',timeout=3000);expect(self.p.locator('#sessionProgressText')).to_contain_text('1 av 2');self.assertEqual(self.p.locator('#dose').inner_text(),before);expect(self.p.locator('[data-round="1"]')).not_to_be_visible();self.shot('phone-rest.png');self.p.locator('#resumeExercise').click();expect(self.p.locator('[data-round="1"]')).to_be_focused();expect(self.p.locator('#sessionProgressText')).to_contain_text('1 av 2')
 def test_completion_feedback_and_next_action_share_the_same_screen(self):
  self.p.locator('[data-round="0"]').click();self.p.locator('[data-round="1"]').click();expect(self.p.locator('#effort')).to_be_visible();expect(self.p.locator('#next')).to_be_visible();self.p.locator('[data-effort="okay"]').click();expect(self.p.locator('[data-effort="okay"]')).to_have_attribute('aria-pressed','true');self.shot('phone-exercise-complete.png');self.p.locator('#next').click();expect(self.p.locator('#player')).not_to_be_visible();self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).sessions[0].status"),'completed')
 def test_help_sheet_retains_context_and_can_show_the_actual_illustration(self):
  self.topic('setup');expect(self.p.locator('[data-coach-topic="setup"]')).to_be_focused();self.shot('phone-help-sheet.png');self.p.locator('[data-coach-show]').click();expect(self.p.locator('#playerHelp')).not_to_be_visible();expect(self.p.locator('#motionStudio')).to_be_focused();expect(self.p.locator('#sessionProgressText')).to_contain_text('0 av')
 def test_skip_and_pause_are_explicit_and_restore_home_navigation(self):
  self.p.locator('#openPlayerOptions').click();self.p.locator('#skip').click();expect(self.p.locator('#playerOptions')).not_to_be_visible();expect(self.p.locator('#next')).to_be_enabled();self.p.locator('#closePlayer').click();expect(self.p.locator('.nav')).to_be_visible();expect(self.p.locator('#start')).to_be_focused()
 def test_preview_starts_with_plan_and_completes_one_connected_session_without_saving(self):
  storage_before=self.p.evaluate('JSON.stringify([Object.entries(localStorage),Object.entries(sessionStorage)])')
  self.p.goto(self.origin+'/reda-2/exercise-guide.html');expect(self.p.locator('#todayTitle')).to_have_text('Dagens träning');expect(self.p.locator('#player')).not_to_be_visible();expect(self.p.locator('#todayExercises button')).to_have_count(3);self.shot('journey-today.png')
  self.p.locator('#todayExercises button').nth(1).click();expect(self.p.locator('#previewExerciseName')).to_have_text('Benspark från stol');expect(self.p.locator('#preview-motionSide')).to_have_text('Vänster sida');self.shot('journey-preview.png');self.p.locator('#preview-motionPlay').click();expect(self.p.locator('#previewLesson')).to_have_attribute('data-playing','true');self.p.locator('#preview-lessonGuided').click();expect(self.p.locator('#previewLesson')).to_have_attribute('data-playing','false');self.shot('journey-preview-instruction.png');self.p.locator('#preview-lessonCloseDetails').click();self.p.locator('.journey-close').click();expect(self.p.locator('#todayExercises button').nth(1)).to_be_focused();expect(self.p.locator('#player')).not_to_be_visible()
  self.assertTrue(self.p.evaluate("(()=>{const a=[...document.querySelectorAll('[id]')].map(x=>x.id);return a.length===new Set(a).size})()"))
  self.p.locator('#start').click();expect(self.p.locator('#pos')).to_have_text('1 av 3');self.p.locator('[data-round="0"]').click();self.p.locator('#closePlayer').click();expect(self.p.locator('#start')).to_have_text('Fortsätt passet');expect(self.p.locator('#todayExercises')).to_contain_text('1 omgångar klara');self.shot('journey-resume.png');self.p.locator('#start').click();self.p.locator('#resumeExercise').click();expect(self.p.locator('[data-round="1"]')).to_be_visible();self.p.locator('[data-round="1"]').click();self.p.locator('#next').click()
  for n in [2,3]:
   expect(self.p.locator('#pos')).to_have_text(str(n)+' av 3');self.p.locator('[data-round="0"]').click();self.p.locator('#resumeExercise').click();self.p.locator('[data-round="1"]').click();self.p.locator('[data-effort="okay"]').click();self.p.locator('#next').click()
  expect(self.p.locator('#player')).not_to_be_visible();expect(self.p.locator('#journeyFinish')).to_contain_text('3 av 3');self.shot('journey-finished.png');self.p.locator('#showReflection').click();self.p.locator('[data-barrier="execution"]').click();expect(self.p.locator('#demoReflectionAnswer')).to_contain_text('Nästa steg');self.shot('journey-feedback.png');self.p.locator('#doneReflection').click();expect(self.p.locator('#todayExercises .journey-row-status')).to_have_text(['Klar','Klar','Klar']);self.p.locator('[data-tab="activity"]').click();expect(self.p.locator('#demoLog')).to_contain_text('3 av 3');self.assertEqual(self.p.evaluate('JSON.stringify([Object.entries(localStorage),Object.entries(sessionStorage)])'),storage_before)
 def test_patient_can_preview_from_home_and_program_without_creating_training(self):
  self.p.locator('#closePlayer').click();before=self.p.evaluate("localStorage.getItem('test-server')");self.p.locator('#todayExercises button').click();expect(self.p.locator('.journey-preview')).to_be_visible();expect(self.p.locator('#preview-motionSide')).to_have_text('Båda sidor, en i taget');expect(self.p.locator('#previewExerciseDose')).to_contain_text('5');self.p.locator('#preview-lessonGuided').click();self.p.locator('#preview-lessonNext').click();expect(self.p.locator('#preview-lessonInstruction')).to_have_text('Sitt med stöd.');self.p.keyboard.press('Escape');self.p.locator('.journey-close').click();self.assertEqual(self.p.evaluate("localStorage.getItem('test-server')"),before);self.p.locator('[data-tab="program"]').click();self.p.locator('[data-program-preview]').click();expect(self.p.locator('#previewExerciseName')).to_have_text('Benspark från stol');self.p.keyboard.press('Escape');expect(self.p.locator('[data-program-preview]')).to_be_focused();self.assertEqual(self.p.evaluate("localStorage.getItem('test-server')"),before)
 def test_small_and_large_phones_keep_primary_controls_on_screen(self):
  self.p.goto(self.origin+'/reda-2/exercise-guide.html');self.p.locator('#start').click()
  for width,height in [(360,640),(390,844),(430,932)]:
   self.p.set_viewport_size({'width':width,'height':height});self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
   for selector in ['#motionPlay','#lessonExpand','#openExerciseHelp','[data-round="0"]']:
    box=self.p.locator(selector).bounding_box();self.assertGreaterEqual(box['height'],44);self.assertLessEqual(box['y']+box['height'],height)
   body_height=self.p.locator('#motion').evaluate('(el)=>{const r=[...el.querySelectorAll(".motion-human-profile,.motion-active-leg")].map(e=>e.getBoundingClientRect());return Math.max(...r.map(x=>x.bottom))-Math.min(...r.map(x=>x.top))}');self.assertGreaterEqual(body_height,170 if width==360 else 240)
   self.shot('phone-'+str(width)+'-ready.png')
  self.p.set_viewport_size({'width':844,'height':390});self.shot('phone-landscape.png');self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));box=self.p.locator('[data-round="0"]').bounding_box();self.assertLessEqual(box['y']+box['height'],390)
 def test_large_text_can_scroll_without_clipping_instructions_or_actions(self):
  self.p.set_viewport_size({'width':320,'height':640});self.p.evaluate("const els=[...document.querySelectorAll('#player,#player *')],sizes=els.map(e=>parseFloat(getComputedStyle(e).fontSize));els.forEach((e,i)=>e.style.setProperty('font-size',(sizes[i]*2)+'px','important'))");self.shot('phone-large-text.png');self.p.locator('#lessonGuided').click();self.p.locator('#lessonNext').click();expect(self.p.locator('#lessonInstruction')).to_have_text('Sitt med stöd.');self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));self.p.locator('#lessonCloseDetails').click();self.p.locator('[data-round="0"]').click();expect(self.p.locator('#sessionProgressText')).to_contain_text('1 av 2')

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
