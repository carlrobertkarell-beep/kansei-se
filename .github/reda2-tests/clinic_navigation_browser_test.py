"""Navigation, retained clinical work, and mandate retries using fictional data only."""
from playwright.sync_api import expect
from plan_authoring_browser_test import T as AuthoringBase, MOCK, ROOT
import unittest

MOCK += """
window.mandates=[];window.mandateRevision=0;window.mandateOn=true;window.mandateOwner=true;
export async function eiSettings(){await new Promise(r=>setTimeout(r,20));return {can_manage:window.mandateOwner,revision:window.mandateRevision,auto_followup:window.mandateOn,clinical_progression_enabled:false,external_ai_enabled:false,connections:[],imports:[]}}
export async function saveEIMandate(id,revision,value){window.mandates.push({id,revision,value});await new Promise(r=>setTimeout(r,350));if(window.mandateFail)throw Error('Fiktivt anslutningsfel. Försök igen.');if(window.mandateStale){window.mandateOwner=false;window.mandateRevision++;throw {code:'40001',message:'Mandatet har ändrats.'}}window.mandateOn=value;window.mandateRevision++;return eiSettings()}
"""
class T(AuthoringBase):
 def setUp(self):
  self.c=self.browser.new_context(viewport={'width':1440,'height':1000})
  self.c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(self.origin) else r.abort())
  self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=MOCK))
  self.p=self.c.new_page();self.errors=[];self.p.on('pageerror',lambda e:self.errors.append(str(e)))
  self.p.goto(self.origin+'/reda-2/klinik-live.html');self.p.locator('[data-detail="a-2"]').wait_for()
 def nav(self,view):self.p.locator('[data-clinic-view="'+view+'"]').click()
 def shot(self,name):
  out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/('navigation-'+name+'.png')),full_page=False)
 def test_distinct_views_and_compact_registry(self):
  expect(self.p.locator('#registryPage')).to_be_visible();expect(self.p.locator('#eiSettings')).not_to_be_visible();expect(self.p.locator('#workspaceTeam')).not_to_be_visible()
  expect(self.p.locator('.dash-streams,.dash-shortcuts')).to_have_count(0)
  self.assertLess(self.p.locator('.dash-row').nth(6).bounding_box()['y'],1000)
  self.shot('patients-desktop');self.nav('attention');expect(self.p.locator('[data-filter]')).to_have_value('priority');expect(self.p.locator('[data-clinic-view="attention"]')).to_have_attribute('aria-current','page')
  self.nav('ei');expect(self.p.locator('#registryPage')).not_to_be_visible();expect(self.p.locator('#eiSettings')).to_contain_text('Automatisk progression stängd');self.shot('mandates-desktop')
  self.nav('team');expect(self.p.locator('#workspaceTeam')).to_be_visible();expect(self.p.locator('#eiSettings')).not_to_be_visible();self.nav('patients');expect(self.p.locator('[data-filter]')).to_have_value('all')
  self.assertEqual(self.p.evaluate('window.mandates.length'),0)
 def test_unsaved_patient_work_survives_navigation_but_not_workspace_switch(self):
  self.open_patient();self.add('bridge');self.p.locator('#goal').fill('Fiktivt osparat mål');before=self.p.locator('#planExercises').inner_text()
  self.nav('ei');self.nav('patient');expect(self.p.locator('#goal')).to_have_value('Fiktivt osparat mål');self.assertEqual(self.p.locator('#planExercises').inner_text(),before);self.assertEqual(self.p.evaluate('window.drafts.length'),0)
  self.nav('team');self.p.locator('#workspaceSelect').select_option('b');expect(self.p.locator('[data-detail="b-2"]')).to_be_visible();expect(self.p.locator('[data-clinic-view="patient"]')).not_to_be_visible();expect(self.p.locator('#goal')).to_have_value('')
 def test_mobile_menu_has_keyboard_navigation_and_no_horizontal_overflow(self):
  self.p.set_viewport_size({'width':390,'height':844});menu=self.p.locator('.clinic-menu')
  expect(menu).to_be_visible();expect(self.p.locator('#clinicNavPanel')).not_to_be_visible();self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));self.shot('patients-mobile')
  menu.click();expect(menu).to_have_attribute('aria-expanded','true');self.p.locator('[data-clinic-view="ei"]').focus();self.p.keyboard.press('Enter');expect(menu).to_have_attribute('aria-expanded','false');expect(self.p.locator('#eiPage')).to_be_focused();self.assertTrue(self.p.evaluate('document.querySelector("#clinicNavPanel").inert'));self.shot('mandates-mobile')
  menu.click();self.p.locator('[data-clinic-view="team"]').focus();self.p.keyboard.press('Escape');expect(menu).to_be_focused();expect(menu).to_have_attribute('aria-expanded','false')
 def test_mandate_retry_keeps_input_and_receipt_and_locks_navigation(self):
  self.nav('ei');save=self.p.get_by_role('button',name='Spara mandat',exact=True);expect(save).to_be_disabled();self.p.locator('[name="automatic"]').uncheck();self.p.evaluate('window.mandateFail=true');save.click()
  expect(self.p.locator('[data-clinic-view="patients"]')).to_be_disabled();expect(self.p.locator('#workspaceSelect')).to_be_disabled();expect(self.p.locator('[data-ei-status]')).to_contain_text('Fiktivt anslutningsfel');expect(self.p.locator('[name="automatic"]')).not_to_be_checked();expect(self.p.locator('.ei-status')).to_have_text('Automatisk uppföljning på')
  self.p.evaluate('window.mandateFail=false');save.click();expect(self.p.locator('[data-ei-status]')).to_contain_text('Mandatet är sparat');expect(self.p.locator('.ei-status')).to_have_text('Automatisk uppföljning av');self.assertTrue(self.p.evaluate('mandates[0].id===mandates[1].id'));expect(self.p.locator('[data-clinic-view="patients"]')).to_be_enabled()
 def test_stale_mandate_reload_respects_revoked_management_permission(self):
  self.nav('ei');self.p.locator('[name="automatic"]').uncheck();self.p.evaluate('window.mandateStale=true');self.p.get_by_role('button',name='Spara mandat',exact=True).click();expect(self.p.locator('[data-ei-status]')).to_contain_text('Mandatet har ändrats');expect(self.p.locator('[name="automatic"]')).to_be_checked();expect(self.p.locator('[name="automatic"]')).to_be_disabled();expect(self.p.get_by_role('button',name='Spara mandat',exact=True)).to_have_count(0)
for name in dir(AuthoringBase):
 if name.startswith('test_') and name not in T.__dict__:setattr(T,name,None)
del AuthoringBase
if __name__=='__main__':unittest.main()
