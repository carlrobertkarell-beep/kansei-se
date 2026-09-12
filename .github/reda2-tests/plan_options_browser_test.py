"""Fictional end-to-end approval and patient choice; no production patients."""
import unittest
from playwright.sync_api import expect
from plan_authoring_browser_test import T as AuthoringBase
from recovery_browser_test import RecoveryTests

class Authoring(AuthoringBase):
 def approve_options(self):
  self.add('extension');self.p.locator('.prescription-edit summary').click();self.p.locator('[data-edit="sets"]').fill('3');self.p.locator('[data-edit="sets"]').press('Tab');self.p.locator('[data-options-prepare]').click();self.p.locator('[data-option-check="0"]').check();expect(self.p.locator('[data-options-approve]')).to_be_disabled();self.p.locator('[data-options-confirm]').check();self.p.locator('[data-options-approve]').click();expect(self.p.locator('[data-options-remove]')).to_be_visible()
 def test_combined_approval_is_saved_and_plan_edit_requires_reapproval(self):
  self.approve_options();payload=self.save();self.assertTrue(payload['planOptions']['approved']);self.assertEqual(payload['planOptions']['items'][0]['exercises'][0]['dose']['sets'],2);self.assertEqual(payload['exercises'][0]['dose']['sets'],3)
  self.p.locator('[data-preview]').click();expect(self.p.locator('dialog.authoring-preview')).to_contain_text('Godkända alternativ');self.p.locator('[data-close-preview]').click();self.p.locator('[data-day="2"]').click();expect(self.p.locator('[data-options-remove]')).to_have_count(0);self.assertNotIn('planOptions',self.save())
 def test_pending_options_do_not_survive_a_change_to_the_basis(self):
  self.add('extension');self.p.locator('[data-options-prepare]').click();self.p.locator('[data-option-check="0"]').check();self.p.locator('[data-day="2"]').click();expect(self.p.locator('[data-options-approve]')).to_have_count(0);self.assertNotIn('planOptions',self.save())

class Patient(RecoveryTests):
 def setUp(self):
  super().setUp();self.p.evaluate("""async()=>{const {approveOptions}=await import('/reda-2/plan-options.mjs?v=1');const d=JSON.parse(localStorage.getItem('test-server'));let p=d.plan.payload;p.schema=6;p.context={equipment:'home'};p.schedule={days:[1,3,5]};p.exercises[0].dose={sets:2,reps:5,hold:0,rest:60,tempo:5,label:'2 × 5'};p.exercises[0].instructions=['Saved instruction'];const next=structuredClone(p);next.exercises[0].dose.sets=1;next.exercises[0].dose.label='1 × 5';d.plan.payload=approveOptions(p,[{id:'less-rounds',title:'Kortare pass',plan:next}]);localStorage.setItem('test-server',JSON.stringify(d));}""");self.p.reload();expect(self.p.locator('[data-session-option="less-rounds"]')).to_be_visible()
 def test_short_pass_resumes_its_own_dose_and_saves_actual_choice(self):
  self.p.locator('[data-session-option="less-rounds"]').click();self.p.locator('#start').click();expect(self.p.locator('[data-round]')).to_have_count(2);self.p.locator('[data-round="0"]').click();expect(self.p.locator('[data-session-option=""]')).to_be_disabled();self.p.reload();self.p.locator('#start').click();expect(self.p.locator('[data-round]')).to_have_count(2);expect(self.p.locator('[data-round="0"]')).to_be_disabled();self.p.locator('[data-round="1"]').click();self.p.locator('#next').click();self.p.wait_for_function("JSON.parse(localStorage.getItem('test-server')).sessions[0].status==='completed'");self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).sessions[0].payload.optionId"),'less-rounds');self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).plan.payload.exercises[0].dose.sets"),2)
  self.p.locator('[data-session-option=""]').click();self.p.locator('#start').click();expect(self.p.locator('[data-round]')).to_have_count(4);self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
 def test_choice_without_starting_never_records_a_session(self):
  self.p.locator('[data-session-option="less-rounds"]').click();self.p.locator('#openPlanGuide').click();expect(self.p.locator('.plan-guide')).to_contain_text('Kortare pass');expect(self.p.locator('.guide-facts')).to_contain_text('1 × 5');self.p.locator('[data-guide-close]').click();self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).sessions.length"),0)

for cls,base in [(Authoring,AuthoringBase),(Patient,RecoveryTests)]:
 for name in dir(base):
  if name.startswith('test_') and name not in cls.__dict__:setattr(cls,name,None)
del AuthoringBase,RecoveryTests,cls,base
if __name__=='__main__':unittest.main()
