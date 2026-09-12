"""Actual clinic/patient pages with fictional APIs; never delivers real email."""
import unittest
from playwright.sync_api import expect
from barrier_adaptation_browser_test import SUPPORT_MOCK
from plan_authoring_browser_test import T as ClinicBase
from recovery_browser_test import RecoveryTests,MOCK
CLINIC=SUPPORT_MOCK.replace('export async function dashboardPatient(id)','async function adaptationDashboard(id)')+"""
window.published=[];window.publishCalls=[];window.failReceipt=true;window.stale=false;window.mailFails=false;window.inviteCalls=[];
export async function dashboardPatient(id){const d=await adaptationDashboard(id);d.delivery_enabled=true;d.patient.connected=!window.mailFails;if(window.published.length)d.handover={id:'h',plan_id:'new',delivery_state:'failed'};return d}
export async function publishReviewed(input){window.publishCalls.push(structuredClone(input));if(window.stale)throw Object.assign(Error('Underlaget har ändrats.'),{code:'40001'});let r=window.published.find(r=>r.requestId===input.requestId);if(!r){r={...input,id:'h',plan_id:'new',version:2,delivery_state:window.mailFails?'pending':'not_requested'};window.published.push(r)}if(window.failReceipt){window.failReceipt=false;throw Error('Kvittot kunde inte hämtas. Försök igen.')}return r}
export async function sendInvitation(id){window.inviteCalls.push(id);if(window.mailFails)throw Error('E-posttjänsten svarade inte');return {accepted:true}}
"""
class Clinic(ClinicBase):
 def setUp(self):
  super().setUp();self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=CLINIC));self.p.reload()
 def review(self):
  self.p.locator('[data-detail="a-2"]').click();self.p.locator('[data-review-plan]').click();expect(self.p.locator('.plan-review [data-diff]')).to_contain_text('Dos')
  self.p.locator('[data-note]').last.fill('Bedömt patientens återkoppling och anpassat omfattningen.');self.p.locator('[data-reviewed]').check()
 def test_review_adjustment_and_lost_receipt_only_publish_one_version(self):
  self.review();self.p.locator('.plan-review > details > summary').click();self.p.locator('[data-exercises] details').first.locator('summary').click();self.p.locator('[data-dose="reps"]').first.fill('9');self.p.locator('[data-dose="reps"]').first.press('Tab');expect(self.p.locator('[data-reviewed]')).not_to_be_checked();self.p.locator('[data-reviewed]').check();self.p.locator('[data-publish]').click();expect(self.p.locator('[data-status]')).to_contain_text('Kvittot');self.p.locator('[data-publish]').click();expect(self.p.locator('.plan-review')).to_contain_text('Plan v2 är publicerad');self.assertEqual(self.p.evaluate('published.length'),1);self.assertTrue(self.p.evaluate('publishCalls[0].requestId===publishCalls[1].requestId'));self.assertEqual(self.p.evaluate('published[0].payload.exercises[0].dose.reps'),9)
 def test_stale_evidence_requires_new_review(self):
  self.review();self.p.evaluate('window.stale=true');self.p.locator('[data-publish]').click();expect(self.p.locator('[data-status]')).to_contain_text('Stäng och öppna');expect(self.p.locator('[data-publish]')).to_be_disabled();self.assertEqual(self.p.evaluate('published.length'),0)
 def test_email_failure_preserves_published_plan_and_offers_retry(self):
  self.p.evaluate('window.mailFails=true;window.failReceipt=false');self.review();self.p.locator('[data-email]').fill('fictional@example.test');self.p.locator('[data-publish]').click();expect(self.p.locator('.plan-review')).to_contain_text('utskicket är inte bekräftat');self.assertEqual(self.p.evaluate('published.length'),1);self.p.locator('[data-done]').click();self.p.locator('[data-detail="a-2"]').click();expect(self.p.locator('[data-retry-invitation]')).to_be_visible();self.p.evaluate('window.mailFails=false');self.p.locator('[data-retry-invitation]').click();expect(self.p.locator('[data-invitation-status]')).to_contain_text('e-posttjänsten');self.assertEqual(self.p.evaluate('published.length'),1)
 def test_review_is_readable_on_mobile(self):
  self.p.set_viewport_size({'width':390,'height':844});self.review();self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));self.assertTrue(self.p.locator('.plan-review').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1'))
PATIENT=MOCK.replace('export async function patientBootstrap()', 'async function originalBootstrap()')+"""
export async function patientBootstrap(){if(localStorage.getItem('no-plan'))throw Object.assign(Error('Ingen aktiv plan ännu'),{code:'NO_PLAN'});return originalBootstrap()}
export async function openPatientPlan(){return {message:'Din behandlare har förberett den här planen åt dig.'}}
"""
class Patient(RecoveryTests):
 def setUp(self):
  super().setUp();self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=PATIENT));self.p.reload();expect(self.p.locator('#app')).to_be_visible()
 def test_first_patient_sees_reviewed_message_and_can_finish_first_session(self):
  expect(self.p.locator('#patientStart')).to_contain_text('förberett');expect(self.p.locator('#patientStart')).to_contain_text('Starta ditt första pass');self.p.locator('#start').click();self.p.locator('[data-round="0"]').click();self.p.locator('[data-round="1"]').click();self.p.locator('#next').click();expect(self.p.locator('#patientStart')).to_contain_text('Första passet avslutat');expect(self.p.locator('#patientStart')).to_contain_text('Berätta hur passet fungerade')
 def test_logged_in_patient_can_retry_missing_plan_without_logging_in_again(self):
  self.p.evaluate("localStorage.setItem('no-plan','yes')");self.p.reload();expect(self.p.locator('#authError')).to_contain_text('Ingen aktiv plan');expect(self.p.locator('#logout')).to_be_visible();self.p.evaluate("localStorage.removeItem('no-plan')");self.p.locator('#retryAccess').click();expect(self.p.locator('#app')).to_be_visible()
 def test_manual_update_before_start_is_shown_before_new_session(self):
  self.p.evaluate("const d=JSON.parse(localStorage.getItem('test-server'));d.plan.id='plan-2';d.plan.version=2;localStorage.setItem('test-server',JSON.stringify(d))");self.p.locator('#start').click();expect(self.p.locator('#sync')).to_contain_text('uppdaterat planen');self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).sessions.length"),0);self.p.locator('#start').click();expect(self.p.locator('#player')).to_be_visible();self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).sessions[0].plan_id"),'plan-2')
for cls,base in [(Clinic,ClinicBase),(Patient,RecoveryTests)]:
 for name in dir(base):
  if name.startswith('test_') and name not in cls.__dict__:setattr(cls,name,None)
del ClinicBase,RecoveryTests,cls,base
if __name__=='__main__':unittest.main()
