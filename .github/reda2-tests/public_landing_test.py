from __future__ import annotations
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
 def setUp(self):self.c=self.b.new_context(viewport={'width':390,'height':844});self.p=self.c.new_page();self.err=[];self.p.on('pageerror',lambda e:self.err.append(str(e)))
 def tearDown(self):self.assertEqual(self.err,[]);self.c.close()
 def test_public_reda_landing(self):
  self.p.goto(self.o+'/reda-rehab/');self.assertIn('Din plan',self.p.locator('h1').inner_text());self.assertIn('automatiskt',self.p.locator('body').inner_text().lower());self.assertEqual(self.p.locator('link[rel="canonical"]').get_attribute('href'),'https://www.kansei.se/reda-rehab/');self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),391)
 def test_homepage_explains_reda_and_preserves_old_portal(self):
  self.p.goto(self.o+'/');card=self.p.locator('#planKort');card.scroll_into_view_if_needed();self.assertIn('Reda håller ihop',card.text_content());self.assertEqual(card.get_by_role('link',name='Läs om Reda →').get_attribute('href'),'/reda-rehab/');self.assertEqual(card.get_by_role('link',name='Har du redan ett Reda-program? Öppna patientportalen →').get_attribute('href'),'/reda/')
if __name__=='__main__':unittest.main(verbosity=2)
