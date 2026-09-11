"""Actual patient page, with fictional messaging service and no external network."""
from intelligence_browser_test import T as Base,MOCK
from playwright.sync_api import expect
import unittest
MESSAGES="""
window.messageCalls=[];window.messageFailure=true;window.patientConversation=[{id:'question-1',kind:'clinician',body:'Vilken övning gäller det? <img src=x onerror=alert(1)>',created_at:'2026-09-10T10:00:00Z'}];
export async function patientMessages(){return {patient_id:'patient-1',reply_to:window.patientConversation.length===1?'question-1':null,messages:window.patientConversation}}
export async function patientReply(messageId,requestId,body){window.messageCalls.push({messageId,requestId,body});await new Promise(r=>setTimeout(r,200));if(window.messageFailure){window.messageFailure=false;throw Error('Fiktivt nätverksfel. Texten finns kvar.')}window.patientConversation.push({id:requestId,kind:'patient',body,reply_to:messageId,created_at:'2026-09-10T11:00:00Z'});return {id:requestId,sent:true}}
"""
class MessagingTests(Base):
 def setUp(self):
  super().setUp();self.c.unroute('**/secure-browser.mjs*');self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=MOCK+MESSAGES))
 def test_patient_reads_and_replies_without_losing_a_failed_draft(self):
  self.p.goto(self.o+'/reda-2/patient.html');h=self.p.locator('#patientMessages');expect(h.locator('.reda-message-list')).to_contain_text('Vilken övning');self.assertEqual(h.locator('img').count(),0);h.locator('textarea').fill('Det gäller bensparken från stolen.');h.locator('[type=submit]').click();expect(self.p.locator('#logout')).to_be_visible();expect(h.locator('.reda-message-status')).to_contain_text('Fiktivt nätverksfel');expect(h.locator('textarea')).to_have_value('Det gäller bensparken från stolen.');h.locator('[type=submit]').click();expect(h.locator('.reda-message-status')).to_contain_text('levererat i Reda');expect(h.locator('.reda-reply')).not_to_be_visible();expect(h.locator('.reda-message-list')).to_contain_text('Det gäller bensparken från stolen.');self.assertTrue(self.p.evaluate('messageCalls[0].requestId===messageCalls[1].requestId'));self.assertEqual(self.p.evaluate('localStorage.length+sessionStorage.length'),0);self.shot('patient-message-reply-mobile.png')
 # Only run this module's new journey, not the inherited unrelated suite again.
for name in list(vars(Base)):
 if name.startswith('test_'):setattr(MessagingTests,name,None)
del Base
if __name__=='__main__':unittest.main(verbosity=2)
