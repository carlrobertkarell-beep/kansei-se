"""Actual patient and clinic screens with fictional support state and delivery receipts."""
import unittest
from playwright.sync_api import expect
from patient_loop_browser_test import T as PatientBase,LOOP_MOCK
from dashboard_browser_test import T as ClinicBase,MOCK as DASHMOCK
PATIENT="""
window.supportPhase='none';window.supportQuestion=false;window.failSupport=false;
export async function patientSupport(){if(window.failSupport)throw Error('offline');const reflected=(read().reflections||[]).some(r=>r.answers.barrier!=='none'||r.answers.support==='yes');return {phase:window.supportPhase==='none'&&reflected?'needs_review':window.supportPhase,reply_to:window.supportQuestion?'question-1':null}}
export async function patientMessages(){return {messages:window.supportQuestion?[{id:'question-1',kind:'clinician',body:'Vilken del av utförandet behöver förtydligas?',created_at:'2026-09-12T10:00:00Z'}]:[],reply_to:window.supportQuestion?'question-1':null}}
export async function patientReply(){window.supportQuestion=false;window.supportPhase='needs_review';return {sent:true}}
"""
class Patient(PatientBase):
 def setUp(self):
  super().setUp();self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=LOOP_MOCK+PATIENT));self.p.reload();expect(self.p.locator('#app')).to_be_visible()
 def test_saved_request_then_question_then_reply_refreshes_support(self):
  self.finish();self.p.locator('[data-barrier="execution"]').click();self.p.locator('[data-support="yes"]').click();self.p.locator('[data-reflection-save]').click();expect(self.p.locator('#patientSupport')).to_contain_text('Ditt svar finns hos kliniken')
  self.p.evaluate("window.supportPhase='awaiting_patient';window.supportQuestion=true");self.p.locator('[data-support-refresh]').click();self.p.locator('[data-support-reply]').click();expect(self.p.locator('#patientMessages textarea')).to_be_visible();self.p.locator('#patientMessages textarea').fill('Jag är osäker på hur knät ska sträckas.');self.p.locator('#patientMessages [type=submit]').click();expect(self.p.locator('#patientSupport')).to_contain_text('Ditt svar finns hos kliniken');expect(self.p.locator('[data-support-reply]')).to_have_count(0);self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
 def test_error_does_not_claim_handled_and_recovery_is_available(self):
  self.p.evaluate("window.failSupport=true;window.supportPhase='handled'");self.p.evaluate("document.querySelector('[data-support-refresh]').click()");expect(self.p.locator('#patientSupport')).to_contain_text('kunde inte hämtas');expect(self.p.locator('#patientSupport')).not_to_contain_text('markerad som hanterad');self.p.evaluate('window.failSupport=false');self.p.locator('[data-support-refresh]').click();expect(self.p.locator('#patientSupport')).to_contain_text('inte att dina besvär måste vara borta')
CLINIC=DASHMOCK.replace("const p=patient(Number(id.split('-')[1]),org);return {patient:p", "const p=patient(Number(id.split('-')[1]),org);return {workflow:{phase:'needs_resolution',pending_signals:2,responsibility:'clinician'},patient:p")
class Clinic(ClinicBase):
 def setUp(self):
  super().setUp();self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=CLINIC));self.p.reload();self.p.locator('[data-detail="a-2"]').click()
 def test_outcome_is_chosen_then_explicitly_approved(self):
  expect(self.p.locator('[data-support-phase="needs_resolution"]')).to_contain_text('Återstår att bedöma');expect(self.p.locator('[data-action]')).to_have_value('resolve_cases');expect(self.p.locator('[data-note]')).to_have_value('');self.p.get_by_role('button',name='Instruktion genomgången',exact=True).click();self.assertIn('hjälpbehovet är hanterat',self.p.locator('[data-note]').input_value());self.assertEqual(self.p.evaluate('window.saved.length'),0);self.p.locator('[data-approve]').click();self.p.wait_for_function('window.saved.length===1');self.assertEqual(self.p.evaluate('window.saved[0].action'),'resolve_cases');self.assertIn('Instruktionen',self.p.evaluate('window.saved[0].note'))
for cls,base in [(Patient,PatientBase),(Clinic,ClinicBase)]:
 for name in dir(base):
  if name.startswith('test_') and name not in cls.__dict__:setattr(cls,name,None)
del PatientBase,ClinicBase,cls,base
if __name__=='__main__':unittest.main()
