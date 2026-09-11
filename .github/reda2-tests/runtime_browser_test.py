"""New runtime integration uses fictional, in-memory services and blocks all external traffic."""
import unittest
from intelligence_browser_test import T as Base,MOCK
from playwright.sync_api import expect
EXTRA="""
payload.exercises[0].dose={sets:1,reps:5,hold:0,rest:60,tempo:5,label:'1 × 5'};
const base=structuredClone(payload),next=structuredClone(payload);next.exercises[0].dose.reps=7;next.exercises[0].dose.label='1 × 7';
payload.progressionDraft={schema:1,mode:'simulation-only',id:'fictional-frame',revision:1,validFrom:'2026-09-01',validUntil:'2026-11-01',rules:{minSuccessfulDays:3,minDaysAtStep:7,maxEvidenceAgeDays:14,acceptedEffort:['easy','okay']},steps:[{id:'a',label:'Aktuell nivå',plan:base},{id:'b',label:'Nästa godkända dos',plan:next}]};
window.runtimeFrames=[];window.runtimeDecisions=[];window.runtimeActions=[];window.runtimeCases=[{id:'case-1',code:'changed_symptoms',status:'open',handling_note:'',created_at:'2026-09-09T10:00:00Z'}];
window.runtimeAI=false;window.runtimeAIQuestions=[];window.runtimeVersion=2;
export async function engineOverview(){return {frames:window.runtimeFrames,decisions:window.runtimeDecisions,cases:window.runtimeCases}}
export async function approveFrame(id,policy){window.runtimeActions.push({action:'approve',id,policy});const f={id:'frame-1',policy,execution:'shadow',status:'approved',current_step:0};window.runtimeFrames=[f];return f}
export async function revokeFrame(){window.runtimeActions.push({action:'revoke'});window.runtimeFrames=[]}
export async function handleCase(id,status,note){if(status==='resolved'&&note.trim().length<5)throw Error('Ange bedömning eller åtgärd.');const c=window.runtimeCases.find(x=>x.id===id);c.status=status;c.handling_note=note;return c}
export async function evaluateProgression(){window.runtimeActions.push({action:'evaluate'});const d={code:'pending_review',applied:false,created_at:'2026-09-10T12:00:00Z'};if(window.runtimeApply){window.runtimeApply=false;await new Promise(r=>setTimeout(r,100));window.runtimeVersion=3;d.code='ready';d.applied=true;d.result_plan_id='plan-3'}window.runtimeDecisions.unshift(d);return d}
export async function dialogue(id,action,question){if(action==='capabilities')return {available:window.runtimeAI};window.runtimeAIQuestions.push({id,question});if(window.runtimeAIQuestions.length===1)throw Error('Fiktivt nätverksfel. Försök igen.');return {available:true,intent:'report',paragraphs:['Kontrollera tolkningen. Inget svar är sparat.'],reports:[{field:'recovery',value:'low',quote:'trött'}],canChangePrescription:false}}
"""
DYNAMIC=MOCK.replace("plan:{id:'plan-2',version:2,payload}","plan:{id:'plan-'+window.runtimeVersion,version:window.runtimeVersion,payload:window.runtimeVersion===3?next:payload}")
class RuntimeTests(Base):
 def setUp(self):
  super().setUp();self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=DYNAMIC+EXTRA))
 # Inherited baseline tests also run against the extended service.
 def test_frame_approval_is_explicit_shadow_and_case_ack_is_not_resolution(self):
  self.p.set_viewport_size({'width':1440,'height':1100});self.p.goto(self.o+'/reda-2/klinik-live.html');self.p.locator('[data-patient]').click();self.p.locator('[data-worktab=followup]').click();h=self.p.locator('#enginePanel');h.locator('.runtime-frame summary').click();expect(h.locator('[data-approve]')).to_be_disabled();h.locator('[data-confirm]').check();h.locator('[data-approve]').click();expect(h).to_contain_text('Granskningsläge');self.assertEqual(self.p.evaluate('runtimeActions[0].id'),'plan-2');h.locator('[data-evaluate]').click();expect(h.locator('.runtime-decisions')).to_contain_text('Ordinationen är oförändrad');h.locator('[data-state=acknowledged]').click();expect(h).to_contain_text('Kvitterat');h.locator('.runtime-case summary').click();h.locator('[data-state=resolved]').click();expect(h.locator('[role=status]')).to_contain_text('Ange bedömning');h.locator('[data-note]').fill('Fiktiv bedömning dokumenterad.');h.locator('[data-state=resolved]').click();expect(h).to_contain_text('Bedömt');h.locator('[data-revoke]').click();expect(h).to_contain_text('Ingen aktiv progressionsram');self.shot('reda-runtime-clinic.png')
 def test_plan_help_works_without_AI_and_never_changes_dose(self):
  self.p.goto(self.o+'/reda-2/patient.html');self.p.locator('[data-tab=program]').click();h=self.p.locator('#planHelp');h.locator('summary').click();h.locator('[data-help=dose]').click();expect(h.locator('[data-answer]')).to_contain_text('1 × 5');expect(h.locator('[data-answer]')).to_contain_text('Höger sida');h.locator('[data-open-ai]').click();expect(h.locator('[data-ai-status]')).to_contain_text('inte öppnade');expect(h.locator('[data-ai-form]')).to_be_hidden();self.assertEqual(self.p.evaluate('runtimeAIQuestions.length'),0);self.shot('reda-runtime-patient-help.png')
 def test_AI_retry_retains_question_and_interpretation_needs_separate_response(self):
  self.p.goto(self.o+'/reda-2/patient.html');self.p.evaluate('runtimeAI=true');self.p.locator('[data-tab=program]').click();h=self.p.locator('#planHelp');h.locator('summary').click();h.locator('[data-open-ai]').click();h.locator('[data-question]').fill('Jag är trött idag efter passet.');h.locator('[type=submit]').click();expect(h.locator('[data-ai-status]')).to_contain_text('nätverksfel');expect(h.locator('[data-question]')).to_have_value('Jag är trött idag efter passet.');h.locator('[type=submit]').click();expect(h.locator('[data-answer]')).to_contain_text('Mindre återhämtad');self.assertEqual(self.p.evaluate('eiCalls.length'),0);expect(self.p.locator('#version')).to_have_text('2');self.shot('reda-runtime-ai-confirmation.png')
 def test_progression_finishes_before_new_session_uses_its_version(self):
  self.p.goto(self.o+'/reda-2/patient.html');self.p.evaluate('runtimeApply=true');self.p.locator('[data-tab=follow]').click();self.p.locator('#checkNextStep').click();self.p.locator('[data-tab=today]').click();self.p.locator('#start').click();expect(self.p.locator('#version')).to_have_text('3');expect(self.p.locator('#dose')).to_contain_text('1 × 7');expect(self.p.locator('#player')).to_be_visible();self.shot('reda-runtime-version-switch.png')
del Base
if __name__=='__main__':unittest.main(verbosity=2)
