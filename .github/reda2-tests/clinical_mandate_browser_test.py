"""Clinical settings stay separate, scoped, read-only for members, and retry safely."""
import unittest
from playwright.sync_api import expect
from clinic_navigation_browser_test import T as NavigationBase,MOCK,ROOT
MOCK+='''
window.clinicalCalls=[];window.clinicalOwner=true;window.clinicalRevision=0;window.clinicalEnabled=false;window.clinicalSteps=3;
export async function clinicalEISettings(){if(window.clinicalLoadFail)throw Error('unavailable');return {can_manage:window.clinicalOwner,revision:window.clinicalRevision,enabled:window.clinicalEnabled,max_steps:window.clinicalSteps,execution_open:false}}
export async function saveClinicalEIMandate(id,revision,enabled,maxSteps){window.clinicalCalls.push({id,revision,enabled,maxSteps});await new Promise(r=>setTimeout(r,350));if(window.clinicalFail)throw Error('Fiktivt anslutningsfel.');if(window.clinicalStale){window.clinicalOwner=false;window.clinicalRevision++;throw {code:'40001',message:'Mandatet har ändrats.'}}window.clinicalRevision++;window.clinicalEnabled=enabled;window.clinicalSteps=maxSteps;return clinicalEISettings()}
'''
class T(NavigationBase):
 def setUp(self):
  self.c=self.browser.new_context(viewport={'width':1440,'height':1000})
  self.c.route('**/*',lambda r:r.continue_()if r.request.url.startswith(self.origin)else r.abort())
  self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=MOCK))
  self.p=self.c.new_page();self.errors=[];self.p.on('pageerror',lambda e:self.errors.append(str(e)));self.p.goto(self.origin+'/reda-2/klinik-live.html');self.p.locator('[data-detail="a-2"]').wait_for();self.nav('ei')
  self.card=self.p.locator('[data-clinical-mandate]');self.save=self.card.get_by_role('button',name='Spara kliniskt mandat')
 def test_prepare_does_not_claim_activation_and_preserves_admin(self):
  expect(self.card).to_contain_text('Automatisk progression stängd');expect(self.save).to_be_disabled()
  self.card.locator('[name="clinicalEnabled"]').check();self.card.locator('select').select_option('1');self.save.click()
  expect(self.p.locator('#workspaceSelect')).to_be_disabled();expect(self.p.locator('#followupMandateTitle').locator('..')).to_have_attribute('inert','')
  expect(self.card).to_contain_text('Kliniskt mandat sparat.');expect(self.save).to_be_disabled();expect(self.card).to_contain_text('Automatisk progression stängd');expect(self.p.locator('#workspaceSelect')).to_be_enabled()
  self.assertEqual(self.p.evaluate('window.mandates.length'),0);self.assertEqual(self.p.evaluate('window.clinicalCalls[0].maxSteps'),1)
  self.p.set_viewport_size({'width':390,'height':844});self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));self.card.scroll_into_view_if_needed();out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/'clinical-mandate-mobile.png'))
 def test_lost_response_retry_and_revision_conflict(self):
  self.p.evaluate('window.clinicalFail=true');self.card.locator('[name="clinicalEnabled"]').check();self.save.click();expect(self.card).to_contain_text('Fiktivt anslutningsfel.');expect(self.save).to_be_enabled()
  self.p.evaluate('window.clinicalFail=false');self.save.click();expect(self.card).to_contain_text('Kliniskt mandat sparat.');calls=self.p.evaluate('window.clinicalCalls');self.assertEqual(calls[0]['id'],calls[1]['id'])
  self.p.evaluate('window.clinicalStale=true');self.card.locator('select').select_option('2');self.save.click();expect(self.card).to_contain_text('Kontrollera aktuella inställningar.');expect(self.card.locator('select')).to_be_disabled();expect(self.save).to_have_count(0)
 def test_load_failure_never_implies_authority(self):
  self.p.evaluate('window.clinicalLoadFail=true');self.p.locator('#workspaceSelect').select_option('b');self.nav('ei');expect(self.card).to_contain_text('kunde inte hämtas');expect(self.card.locator('input')).to_have_count(0)
  self.p.evaluate('window.clinicalLoadFail=false;window.clinicalOwner=false');self.card.get_by_role('button',name='Försök igen').click();expect(self.card.locator('input')).to_be_disabled();expect(self.card.locator('select')).to_be_disabled();expect(self.save).to_have_count(0)
# Inherited browser checks live in their own suite; only run this module's cases.
if __name__=='__main__':unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(T(n)for n in T.__dict__ if n.startswith('test_'))).wasSuccessful()or exit(1)
