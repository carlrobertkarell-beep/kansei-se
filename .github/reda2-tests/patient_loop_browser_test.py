"""The actual patient screen, with fictional server receipts and failure injection."""
import unittest
from playwright.sync_api import expect
from recovery_browser_test import RecoveryTests,MOCK,ROOT

LOOP_MOCK=MOCK+"""
window.reflectionRequests=[];
export async function submitSessionReflection(sid,rid,answers){
 window.reflectionRequests.push({sid,rid,answers});
 const data=read(),session=data.sessions.find(x=>x.id===sid);
 if(!session?.completed_at)throw Error('Passet måste sparas först');
 const existing=(data.reflections||[]).find(x=>x.session_id===sid);
 const row=existing||{id:rid,session_id:sid,plan_id:session.plan_id,plan_version:session.plan_version,answers,exercise_name:answers.exerciseId?'Benspark från stol':null,created_at:new Date().toISOString()};
 data.reflections=[row,...(data.reflections||[]).filter(x=>x.session_id!==sid)];localStorage.setItem('test-server',JSON.stringify(data));
 if(window.loseReflectionReceipt){window.loseReflectionReceipt=false;throw Error('Svaret kunde inte bekräftas. Försök igen.')}return row;
}
"""
class T(RecoveryTests):
 def setUp(self):
  super().setUp();self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=LOOP_MOCK));self.p.reload();expect(self.p.locator('#app')).to_be_visible()
 def finish(self):
  self.p.locator('#start').click();self.p.locator('[data-round="0"]').click();self.p.locator('[data-round="1"]').click();self.p.locator('#next').click();expect(self.p.locator('[data-reflection-save]')).to_be_visible()
 def test_finish_answers_receipt_and_reload_are_one_coherent_flow(self):
  self.finish();expect(self.p.locator('#todayTitle')).to_have_text('Dagens pass är registrerat');self.p.locator('[data-barrier="time"]').click();self.p.locator('[data-support="no"]').click();self.p.locator('[data-reflection-exercise]').select_option('extension');self.p.locator('[data-reflection-save]').click();expect(self.p.locator('.loop-receipt')).to_contain_text('Dina svar är sparade');self.assertEqual(self.p.evaluate('window.reflectionRequests.length'),1);self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).reflections[0].plan_id"),'plan-1');expect(self.p.locator('#responsePrompt')).to_be_hidden();self.p.reload();expect(self.p.locator('#app')).to_be_visible();expect(self.p.locator('#reflectionPrompt')).to_be_hidden()
 def test_lost_receipt_keeps_choices_and_reuses_the_same_request(self):
  self.finish();self.p.locator('[data-barrier="equipment"]').click();self.p.locator('[data-support="yes"]').click();self.p.evaluate('window.loseReflectionReceipt=true');self.p.locator('[data-reflection-save]').click();expect(self.p.locator('.loop-reflection [role="alert"]')).to_contain_text('Försök igen');expect(self.p.locator('[data-barrier="equipment"]')).to_have_attribute('aria-pressed','true');self.p.locator('[data-reflection-save]').click();expect(self.p.locator('.loop-receipt')).to_be_visible();self.assertTrue(self.p.evaluate('window.reflectionRequests[0].rid===window.reflectionRequests[1].rid'));self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).reflections.length"),1)
 def test_later_reopens_without_fabricating_feedback_and_mobile_stays_readable(self):
  self.finish();self.p.locator('[data-reflection-later]').click();expect(self.p.locator('#sessionReflection')).to_be_hidden();self.p.locator('#openReflection').click();expect(self.p.locator('[data-reflection-save]')).to_be_disabled();self.p.locator('[data-barrier="symptoms"]').click();expect(self.p.locator('.loop-contact')).to_contain_text('Kontakta kliniken');self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/'patient-loop-mobile.png'),full_page=True);self.p.set_viewport_size({'width':1280,'height':900});self.p.screenshot(path=str(out/'patient-loop-desktop.png'),full_page=True)
 def test_failed_session_save_does_not_offer_a_false_saved_receipt(self):
  self.p.evaluate("localStorage.setItem('test-fail','yes')");self.p.locator('#start').click();self.p.locator('[data-round="0"]').click();self.p.locator('[data-round="1"]').click();self.p.locator('#next').click();expect(self.p.locator('#retrySync')).to_be_visible();expect(self.p.locator('#sessionReflection')).to_be_hidden();self.assertEqual(self.p.evaluate('window.reflectionRequests.length'),0)
for name in dir(RecoveryTests):
 if name.startswith('test_') and name not in T.__dict__:setattr(T,name,None)
del RecoveryTests
if __name__=='__main__':unittest.main()
