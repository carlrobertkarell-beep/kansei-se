from __future__ import annotations
import functools,http.server,threading,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reda2-test-results'
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
class T(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  OUT.mkdir(exist_ok=True);c.s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(ROOT)));threading.Thread(target=c.s.serve_forever,daemon=True).start();c.o=f'http://127.0.0.1:{c.s.server_port}';c.pw=sync_playwright().start();c.b=c.pw.chromium.launch()
 @classmethod
 def tearDownClass(c):c.b.close();c.pw.stop();c.s.shutdown()
 def setUp(self):
  self.c=self.b.new_context(viewport={'width':390,'height':844});self.ext=[];self.c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(self.o+'/') else (self.ext.append(r.request.url),r.abort())[1]);self.p=self.c.new_page();self.err=[];self.p.on('pageerror',lambda e:self.err.append(str(e)));self.p.goto(self.o+'/reda-2/motion-lab.html')
 def tearDown(self):self.assertEqual(self.err,[]);self.assertEqual(self.ext,[]);self.c.close()
 def test_lab_lists_graph_and_versioned_motion(self):
  self.assertIn('Övningsgraf',self.p.locator('.catalog h1').inner_text());self.assertGreater(self.p.locator('.node-btn').count(),20);self.assertEqual(self.p.locator('#motion svg').get_attribute('data-motion-version'),'1');self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),391)
 def test_bridge_graph_stills_and_animation(self):
  self.p.locator('#search').fill('Höftlyft');self.p.locator('.node-btn').first.click();self.assertIn('Höftlyft',self.p.locator('.stage h1').inner_text());self.assertEqual(self.p.locator('.still').count(),3);before=self.p.locator('#motion svg g').inner_html();self.p.get_by_role('button',name='Visa rörelsen').click();self.p.wait_for_timeout(650);after=self.p.locator('#motion svg g').inner_html();self.assertNotEqual(before,after);self.p.screenshot(path=str(OUT/'motion-lab-bridge-mobile.png'),full_page=True)
 def test_patient_app_uses_versioned_motion(self):
  self.p.goto(self.o+'/reda-2/');self.p.get_by_role('button',name='Prova exempelprogrammet').click();self.p.get_by_role('button',name='Starta passet',exact=True).click();svg=self.p.locator('#motion svg');self.assertEqual(svg.get_attribute('data-motion-version'),'1');self.assertEqual(svg.get_attribute('data-motion'),'sit-to-stand.support')
if __name__=='__main__':unittest.main(verbosity=2)
