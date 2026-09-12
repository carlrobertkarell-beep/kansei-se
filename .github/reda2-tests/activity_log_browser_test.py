import unittest
from playwright.sync_api import expect
from recovery_browser_test import RecoveryTests,MOCK
EXTRA="""
export async function activityLog(id,args){
 window.logCalls=(window.logCalls||[]);window.logCalls.push({id,...args});
 if(window.failLog)throw Error('offline');
 if(args.category==='finance')return {events:[],billing_connected:false};
 return {events:[{id:args.cursor?'2':'1',occurred_at:'2026-06-01T10:00:00Z',category:'training',title:args.cursor?'Äldre pass':'Pass genomfört',detail:'Kortare pass',plan_version:2}],next_cursor:args.cursor?null:{time:'2026-06-01T10:00:00Z',key:'1'}};
}
"""
class T(RecoveryTests):
 def setUp(self):
  super().setUp();self.c.route('**/secure-browser.mjs*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=MOCK+EXTRA));self.p.reload();self.p.locator('[data-tab="activity"]').click()
 def test_filter_dates_pagination_and_error(self):
  expect(self.p.locator('.activity-events')).to_contain_text('Kortare pass');self.p.locator('.activity-more').click();expect(self.p.locator('.activity-events li')).to_have_count(2)
  self.p.locator('[name="category"]').select_option('finance');self.p.locator('.activity-filters button').click();expect(self.p.locator('.activity-status')).to_contain_text('inte anslutna');expect(self.p.locator('.activity-events li')).to_have_count(0)
  self.p.locator('[name="category"]').select_option('training');self.p.locator('[name="from"]').fill('2026-06-01');self.p.locator('[name="to"]').fill('2026-06-02');self.p.locator('.activity-filters button').click();expect(self.p.locator('.activity-events')).to_contain_text('Pass genomfört');self.assertEqual(self.p.evaluate('logCalls.at(-1).from'),'2026-06-01');self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
  self.p.evaluate('window.failLog=true');self.p.locator('.activity-filters button').click();expect(self.p.locator('.activity-status')).to_contain_text('kunde inte hämtas');expect(self.p.locator('.activity-more')).to_be_hidden()
 def test_patient_has_no_internal_filter(self):
  expect(self.p.locator('[name="category"] option[value="ei"]')).to_have_count(0)
for name in dir(RecoveryTests):
 if name.startswith('test_') and name not in T.__dict__:setattr(T,name,None)
del RecoveryTests
if __name__=='__main__':unittest.main()
