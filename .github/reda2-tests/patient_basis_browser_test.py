"""Real screens, fictional data only. Goal report retries and owner mandate controls."""
import unittest
from playwright.sync_api import expect
from recovery_browser_test import RecoveryTests,MOCK
from dashboard_browser_test import T as ClinicBase,MOCK as DASHMOCK
PATIENT=MOCK+"""
window.checkinCalls=[];window.goalReports=[];window.failGoal=true;
export async function myCheckins(){return {plan:{id:'plan-1',version:1,goal:'Kunna gå till arbetet'},latest:window.goalReports.at(-1)||null,baseline:window.goalReports[0]||null,history:window.goalReports}}
export async function submitCheckin(planId,requestId,answers){window.checkinCalls.push({planId,requestId,answers});const saved=window.goalReports.find(x=>x.id===requestId)||{id:requestId,goal_key:'walking',answers,created_at:'2026-09-12T10:00:00Z'};if(!window.goalReports.some(x=>x.id===requestId))window.goalReports.push(saved);if(window.failGoal){window.failGoal=false;throw Error('Kvittot kunde inte hämtas. Försök igen.')}return saved}
"""
class Patient(RecoveryTests):
 def setUp(self):
  super().setUp();self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=PATIENT));self.p.reload();self.p.locator('[data-tab="follow"]').click();self.p.locator('#patientCheckin summary').click()
 def test_goal_choices_survive_lost_receipt_and_retry_same_request(self):
  expect(self.p.locator('#patientCheckin')).to_contain_text('Kunna gå till arbetet');self.p.locator('[name="ability"]').select_option('4');self.p.locator('[name="minutes"]').select_option('10');self.p.locator('[name="equipment"]').select_option('home');self.p.locator('[name="band"]').select_option('false');self.p.locator('[name="floorOK"]').select_option('false');self.p.locator('.basis-form [type="submit"]').click();expect(self.p.locator('[data-checkin-status]')).to_contain_text('Kvittot');expect(self.p.locator('[name="ability"]')).to_have_value('4');self.p.locator('.basis-form [type="submit"]').click();expect(self.p.locator('[data-checkin-status]')).to_contain_text('sparad till kliniken');self.assertTrue(self.p.evaluate('checkinCalls[0].requestId===checkinCalls[1].requestId'));self.assertEqual(self.p.evaluate('goalReports.length'),1);self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
SETTINGS="""
window.mandateCalls=[];window.autoTask=true;window.mandateRevision=0;
export async function eiSettings(){return {can_manage:true,auto_followup:window.autoTask,revision:window.mandateRevision,clinical_progression_enabled:false,external_ai_enabled:false,connections:[{id:'booking',name:'Bokning',connected:false},{id:'journal',name:'Journal',connected:false},{id:'billing',name:'Betalning och abonnemang',connected:false}],imports:[]}}
export async function saveEIMandate(requestId,revision,value){window.mandateCalls.push({requestId,revision,value});window.autoTask=value;window.mandateRevision++;return await eiSettings()}
"""
CLINIC=DASHMOCK.replace("return {patient:p,token", "return {basis:{profile:{focus:'Vänster knä',goal:'Gå till arbetet',updated_at:'2026-09-01'},plan:{id:'plan-2',version:1,goal:'Gå till arbetet',activated_at:'2026-09-01'},latest:{id:'report-2',goal_key:'walking',answers:{ability:6,minutes:15,equipment:'home',band:false,floorOK:true},created_at:'2026-09-12',plan_version:1},baseline:{id:'report-1',goal_key:'walking',answers:{ability:3},created_at:'2026-09-01'}},patient:p,token")+SETTINGS
class Clinic(ClinicBase):
 def setUp(self):
  super().setUp();self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=CLINIC));self.p.reload()
 def test_source_overview_and_goal_change_are_readable(self):
  self.p.locator('[data-detail="a-2"]').click();expect(self.p.locator('.basis-card')).to_contain_text('Patientens egna uppgifter');expect(self.p.locator('.basis-card')).to_contain_text('+3 från första skattningen');self.p.set_viewport_size({'width':390,'height':844});self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
 def test_owner_mandate_saves_and_connections_never_look_connected(self):
  self.p.locator('#eiSettings summary').first.click();expect(self.p.locator('#eiSettings')).to_contain_text('Inte ansluten');expect(self.p.locator('#eiSettings')).to_contain_text('Automatisk progression stängd');self.p.locator('[name="automatic"]').uncheck();self.assertEqual(self.p.evaluate('mandateCalls.length'),0);self.p.get_by_role('button',name='Spara mandat',exact=True).click();expect(self.p.locator('[data-ei-status]')).to_contain_text('Mandatet är sparat');expect(self.p.locator('[name="automatic"]')).not_to_be_checked();self.assertEqual(self.p.evaluate('mandateCalls[0].value'),False)
for cls,base in [(Patient,RecoveryTests),(Clinic,ClinicBase)]:
 for name in dir(base):
  if name.startswith('test_') and name not in cls.__dict__:setattr(cls,name,None)
del RecoveryTests,ClinicBase,cls,base
if __name__=='__main__':unittest.main()
