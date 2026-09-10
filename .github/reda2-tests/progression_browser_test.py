"""Fictional progression paths in the browser; no external API or patient writes."""
import functools,http.server,threading,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
class T(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(ROOT)));threading.Thread(target=c.s.serve_forever,daemon=True).start();c.o=f'http://127.0.0.1:{c.s.server_port}';c.pw=sync_playwright().start();c.b=c.pw.chromium.launch()
 @classmethod
 def tearDownClass(c):c.b.close();c.pw.stop();c.s.shutdown();c.s.server_close()
 def setUp(self):
  self.c=self.b.new_context(viewport={'width':390,'height':844});self.c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(self.o) else r.abort());self.p=self.c.new_page();self.err=[];self.writes=[];self.p.on('pageerror',lambda e:self.err.append(str(e)));self.p.on('request',lambda r:self.writes.append(r.url) if r.method!='GET' else None);self.p.goto(self.o+'/reda-2/progression-lab.html')
 def tearDown(self):self.assertEqual(self.err,[]);self.assertEqual(self.writes,[]);self.assertEqual(self.p.evaluate('localStorage.length+sessionStorage.length'),0);self.c.close()
 def test_all_profiles_have_real_distinct_prescriptions_and_state_resets(self):
  choices=[]
  for profile in ['daily','hyrox','strength']:
   self.p.locator('[data-lab-profile='+profile+']').click();self.assertTrue(self.p.locator('#labAdvance').is_visible());choices.append(self.p.locator('#labPrescription').inner_text());self.p.locator('#labScenario').select_option('heavy');self.assertTrue(self.p.locator('#labAdvance').is_hidden())
  self.assertEqual(len(set(choices)),3)
 def test_missing_data_load_and_new_symptoms_do_not_advance_or_sell(self):
  for case,action in [('missing','wait'),('single','wait'),('load','hold'),('low','hold'),('worse','review'),('open','wait')]:
   self.p.locator('#labScenario').select_option(case);self.assertEqual(self.p.locator('.lab-state').get_attribute('data-action'),action);self.assertTrue(self.p.locator('#labAdvance').is_hidden());self.assertTrue(self.p.locator('#labContinuation').is_hidden())
 def test_full_path_requires_new_evidence_then_ends_without_checkout(self):
  for i in range(2):
   self.p.locator('#labScenario').select_option('ready');self.p.locator('#labAdvance').click();self.assertEqual(self.p.locator('#labScenario').input_value(),'missing');self.assertTrue(self.p.locator('#labAdvance').is_hidden())
  self.p.locator('#labScenario').select_option('ready');self.assertEqual(self.p.locator('.lab-state').get_attribute('data-action'),'complete');self.assertTrue(self.p.locator('#labContinuation').is_visible());self.p.locator('#labScenario').select_option('worse');self.assertTrue(self.p.locator('#labContinuation').is_hidden());self.p.locator('#labReset').click();self.assertTrue(self.p.locator('#labAdvance').is_visible())
 def test_responsive_layout_keyboard_and_screenshots(self):
  self.p.emulate_media(reduced_motion='reduce');self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),390);self.p.locator('#labScenario').focus();self.p.keyboard.press('ArrowDown');self.assertEqual(self.p.locator('.lab-state').get_attribute('data-action'),'wait');self.p.locator('#labReset').click();out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/'reda-engine-mobile.png'),full_page=True);self.p.set_viewport_size({'width':1440,'height':1000});self.p.locator('[data-lab-profile=hyrox]').click();self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),1440);self.p.screenshot(path=str(out/'reda-engine-desktop.png'),full_page=True)
if __name__=='__main__':unittest.main(verbosity=2)
