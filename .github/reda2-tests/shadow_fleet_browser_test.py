"""Fictional batch RPCs: groups, pagination, stop/failure and workspace boundaries."""
import unittest
from playwright.sync_api import expect
from clinic_navigation_browser_test import T as NavigationBase,MOCK,ROOT
MOCK+='''
window.previewCalls=[];window.previewDelay=30;
export async function previewProgressionBatch(after){const org=current;window.previewCalls.push({org,after});await new Promise(r=>setTimeout(r,window.previewDelay));if(window.previewDenied)throw {code:'42501'};if(window.previewFail&&after)throw Error('offline');const offset=after?Number(after):0,total=window.previewEmpty?0:67,rows=Array.from({length:total},(_,i)=>({patient_id:i===0?'a-2':org+'-preview-'+i,display_name:org+' Preview '+String(i).padStart(3,'0'),evaluated_at:'2026-09-20T09:00:00Z',decision:{action:i<30?'advance':i<60?'wait':i<65?'review':'none',code:i<30?'ready':i<60?'evidence':i<65?'pending_review':'no_frame',applied:false,frame_id:i<65?'frame-'+i:null,plan_id:'plan-'+i,step:0,steps:3,execution:'shadow',execution_open:false,mandate_enabled:false,metrics:{successfulDays:i<30?3:1,requiredDays:3,daysAtStep:8},next_step:i<30?'Nästa nivå':null}}));return {preview:true,items:rows.slice(offset,offset+25),next_cursor:offset+25<total?String(offset+25):null}}
'''
class T(NavigationBase):
 def setUp(self):
  self.c=self.browser.new_context(viewport={'width':1440,'height':1000});self.c.route('**/*',lambda r:r.continue_()if r.request.url.startswith(self.origin)else r.abort());self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=MOCK));self.p=self.c.new_page();self.errors=[];self.p.on('pageerror',lambda e:self.errors.append(str(e)));self.p.goto(self.origin+'/reda-2/klinik-live.html');self.p.locator('[data-detail="a-2"]').wait_for();self.nav('ei');self.host=self.p.locator('#eiPreview')
 def start(self):self.host.locator('[data-preview-run]').click()
 def done(self):expect(self.host.locator('[data-preview-status]')).to_contain_text('Provkörning klar.')
 def test_groups_evidence_pagination_and_current_patient(self):
  self.assertEqual(self.p.evaluate('window.previewCalls.length'),0);self.start();self.done();expect(self.host.locator('[data-preview-status]')).to_contain_text('67 aktiva planer')
  for key,count in [('review','5'),('ready','30'),('waiting','30')]:expect(self.host.locator('[data-preview-group="'+key+'"] strong')).to_have_text(count)
  expect(self.host.locator('.shadow-row')).to_have_count(5);self.host.locator('[data-preview-group="ready"]').click();expect(self.host.locator('.shadow-row')).to_have_count(25);self.host.locator('[data-preview-next]').click();expect(self.host.locator('.shadow-row')).to_have_count(5);expect(self.host.locator('[data-preview-page]')).to_have_text('26–30 av 30')
  self.host.locator('[data-preview-search]').fill('000');expect(self.host.locator('.shadow-row')).to_have_count(1);self.host.locator('summary').click();expect(self.host).to_contain_text('Automatisk progression är stängd.');expect(self.host).to_contain_text('Nästa nivå');self.host.locator('[data-preview-open="a-2"]').click();expect(self.p.locator('.dash-detail')).to_be_visible();expect(self.p.locator('#eiPreview')).not_to_be_visible()
  self.assertEqual(self.p.evaluate('window.mandates.length'),0);self.assertEqual(self.errors,[])
 def test_cancel_and_failure_are_never_complete(self):
  self.p.evaluate('window.previewDelay=350');self.start();expect(self.host.locator('[data-preview-status]')).to_contain_text('25 planer genomgångna');self.host.locator('[data-preview-run]').click();expect(self.host).to_contain_text('Resultatet är ofullständigt.');self.p.wait_for_timeout(450);expect(self.host.locator('[data-preview-status]')).not_to_contain_text('klar')
  self.p.evaluate('window.previewFail=true;window.previewDelay=30');self.start();expect(self.host).to_contain_text('kunde inte slutföras');expect(self.host).to_contain_text('25 planer genomgångna');self.p.evaluate('window.previewFail=false');self.start();self.done();expect(self.host.locator('[data-preview-status]')).to_contain_text('67 aktiva planer')
 def test_workspace_change_discards_inflight_results_and_access_revocation_clears_names(self):
  self.p.evaluate('window.previewDelay=350');self.start();self.p.locator('#workspaceSelect').select_option('b');self.nav('ei');self.p.wait_for_timeout(450);expect(self.host).to_contain_text('Ingen provkörning gjord');expect(self.host.locator('.shadow-row')).to_have_count(0)
  self.p.evaluate('window.previewDelay=30');self.start();self.done();expect(self.host).to_contain_text('b Preview');expect(self.host).not_to_contain_text('a Preview');self.p.evaluate('window.previewDenied=true');self.start();expect(self.host).to_contain_text('Åtkomsten kunde inte verifieras');expect(self.host.locator('.shadow-row')).to_have_count(0)
 def test_uncovered_empty_and_mobile(self):
  self.start();self.done();self.host.locator('[data-preview-group="uncovered"]').click();expect(self.host.locator('.shadow-row')).to_have_count(2);expect(self.host).to_contain_text('Förbered och granska en ram');self.p.set_viewport_size({'width':390,'height':844});self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));self.host.scroll_into_view_if_needed();out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/'shadow-preview-mobile.png'),full_page=True)
  self.p.evaluate('window.previewEmpty=true');self.start();expect(self.host).to_contain_text('Inga tilldelade patienter med aktiva planer');expect(self.host.locator('[data-preview-results]')).not_to_be_visible()
if __name__=='__main__':unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(T(n)for n in T.__dict__ if n.startswith('test_'))).wasSuccessful()or exit(1)
