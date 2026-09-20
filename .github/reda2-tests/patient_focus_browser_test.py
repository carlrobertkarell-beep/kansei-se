"""Patient home priorities and version changes with fictional data only."""
import unittest
from playwright.sync_api import expect
from recovery_browser_test import RecoveryTests,MOCK,ROOT
EXTRA='''
export async function patientSupport(){if(window.contactFailure)throw Error('offline');return {phase:'needs_review'}}
export async function patientMessages(){return {messages:[{id:'m',kind:'clinician',body:'Hur fungerar övningen?',created_at:'2026-09-20T08:00:00Z'}],reply_to:'m'}}
export async function openPatientPlan(){if(window.receiptFailure)throw Error('offline');return {message:'Följ den här dosen enligt vår överenskommelse.'}}
'''
class T(RecoveryTests):
 def setUp(self):
  super().setUp();self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=MOCK+EXTRA));self.p.reload();expect(self.p.locator('#app')).to_be_visible()
 def test_start_is_visible_and_help_has_a_direct_route(self):
  expect(self.p.locator('#intro')).to_have_count(1);expect(self.p.locator('#intro')).not_to_be_visible();expect(self.p.locator('#patientDuration')).to_have_text('I din takt');expect(self.p.locator('#patientContactShortcut')).to_contain_text('Din behandlare har en fråga');self.assertLess(self.p.locator('#start').bounding_box()['y'],700)
  self.p.locator('#patientContactShortcut').click();expect(self.p.locator('#patientMessages textarea')).to_be_visible();self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).sessions.length"),0)
  self.p.locator('#start').click();expect(self.p.locator('#patientExerciseCues')).to_contain_text('Vänster sida');self.p.locator('[data-round="0"]').click();expect(self.p.locator('#patientExerciseCues')).to_contain_text('Höger sida')
 def test_real_new_plan_is_explained_and_not_started_silently(self):
  self.p.locator('#patientMessages textarea').fill('Ett oskickat svar som ska vara kvar.')
  self.p.evaluate("const d=JSON.parse(localStorage.getItem('test-server'));d.plan={...d.plan,id:'plan-2',version:2,payload:{...d.plan.payload,exercises:d.plan.payload.exercises.map(x=>({...x,dose:{...x.dose,reps:8}}))}};localStorage.setItem('test-server',JSON.stringify(d))")
  self.p.locator('#start').click();expect(self.p.locator('#patientPlanChanges')).to_contain_text('Din plan har uppdaterats');expect(self.p.locator('#patientPlanChanges')).to_contain_text('5 repetitioner');expect(self.p.locator('#patientPlanChanges')).to_contain_text('8 repetitioner');expect(self.p.locator('#patientMessages textarea')).to_have_value('Ett oskickat svar som ska vara kvar.');expect(self.p.locator('#player')).not_to_be_visible();self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).sessions.length"),0)
 def test_failed_open_receipt_is_not_attributed_to_clinician(self):
  self.p.evaluate("window.receiptFailure=true;const d=JSON.parse(localStorage.getItem('test-server'));d.plan.id='plan-2';d.plan.version=2;localStorage.setItem('test-server',JSON.stringify(d))");self.p.locator('#start').click();expect(self.p.locator('#planReceiptStatus')).to_contain_text('kunde inte bekräftas');expect(self.p.locator('.patient-plan-message')).to_have_count(0)
 def test_small_phone_large_text_and_completion_emphasis(self):
  self.p.set_viewport_size({'width':320,'height':700});self.p.evaluate("document.documentElement.dataset.redaText='large'");self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/'patient-focus-home.png'),full_page=False,animations='disabled')
  self.p.locator('#start').click();self.p.locator('[data-round="0"]').click();self.p.locator('[data-round="1"]').click();self.p.locator('#next').click();expect(self.p.locator('#todayCard')).to_have_attribute('data-day-state','done');expect(self.p.locator('#start')).to_have_class(__import__('re').compile(r'.*soft.*'));self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
if __name__=='__main__':unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(T(n)for n in T.__dict__ if n.startswith('test_'))).wasSuccessful()or exit(1)
