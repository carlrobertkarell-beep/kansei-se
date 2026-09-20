"""Exercise flow uses fictional plans; help choices never send symptom reports."""
import unittest
from playwright.sync_api import expect
from recovery_browser_test import RecoveryTests,ROOT
class T(RecoveryTests):
 def setUp(self):
  super().setUp()
  self.p.evaluate("const d=JSON.parse(localStorage.getItem('test-server'));Object.assign(d.plan.payload.exercises[0].dose,{sets:2,rest:1,tempo:3});localStorage.setItem('test-server',JSON.stringify(d))")
  self.p.reload();self.p.locator('#start').click()
 def test_sides_rounds_rest_and_focus_follow_recorded_progress(self):
  expect(self.p.locator('#patientExerciseCues')).to_contain_text('3 sek per repetition')
  expect(self.p.locator('#playerCurrentRound')).to_have_text('Omgång 1 på den här sidan av 2')
  self.p.locator('[data-round="0"]').click();expect(self.p.locator('#playerStep')).to_have_text('Byt till höger sida');expect(self.p.locator('#restNext')).to_have_text('Nästa omgång: höger sida');expect(self.p.locator('#resumeExercise')).to_be_focused()
  expect(self.p.locator('#restStatus')).to_contain_text('Vilotiden är slut',timeout=3000);expect(self.p.locator('#sessionProgressText')).to_contain_text('1 av 4');self.p.locator('#resumeExercise').click();expect(self.p.locator('[data-round="1"]')).to_be_focused();expect(self.p.locator('#playerCurrentRound')).to_have_text('Omgång 1 på den här sidan av 2')
  self.p.locator('[data-round="1"]').click();expect(self.p.locator('#playerStep')).to_have_text('Byt till vänster sida');expect(self.p.locator('#playerCurrentRound')).to_have_text('Omgång 2 på den här sidan av 2')
  self.p.locator('#resumeExercise').click();self.p.locator('[data-round="2"]').click();self.p.locator('#resumeExercise').click();self.p.locator('[data-round="3"]').click();expect(self.p.locator('#playerStep')).to_have_text('Övningen är klar');expect(self.p.locator('#next')).to_be_focused()
 def test_pain_and_difficulty_offer_pause_without_recording_or_sending(self):
  self.p.locator('[data-round="0"]').click();self.p.locator('#resumeExercise').click()
  for choice,title in [('difficult','Övningen känns för svår'),('pain','Det gör ont')]:
   self.p.locator('#openExerciseHelp').click();self.p.locator('[data-player-concern="'+choice+'"]').click();expect(self.p.locator('#playerConcernTitle')).to_have_text(title);expect(self.p.locator('#playerConcernTitle')).to_be_focused();expect(self.p.locator('#playerConcern')).to_contain_text('Inget meddelande skickas');self.p.locator('#playerPauseForHelp').click();expect(self.p.locator('#player')).not_to_be_visible();self.p.locator('#start').click();expect(self.p.locator('#sessionProgressText')).to_contain_text('1 av 4');expect(self.p.locator('#motionSide')).to_have_text('Höger sida')
 def test_clearer_instruction_and_phone_illustration(self):
  self.p.locator('#openExerciseHelp').click();self.p.locator('#playerShowClearly').click();expect(self.p.locator('#playerHelp')).not_to_be_visible();expect(self.p.locator('#lessonDetails')).to_be_visible();self.p.keyboard.press('Escape');expect(self.p.locator('#sessionProgressText')).to_contain_text('0 av 4')
  for width,height in [(390,844),(360,640),(320,640)]:
   self.p.set_viewport_size({'width':width,'height':height});self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));self.assertGreaterEqual(self.p.locator('#motionStudio').bounding_box()['height'],190)
  self.p.set_viewport_size({'width':390,'height':844});self.p.evaluate('scrollTo(0,0)');out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/'exercise-flow-ready.png'))
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(T(n)for n in T.__dict__ if n.startswith('test_')))
 raise SystemExit(not result.wasSuccessful())
