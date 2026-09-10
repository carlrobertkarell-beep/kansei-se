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
  self.p.goto(self.o+'/reda-rehab/');self.assertIn('Din plan',self.p.locator('h1').inner_text());self.assertIn('Försäljningen har inte öppnat',self.p.locator('.care-options').inner_text());self.assertNotIn('2 490',self.p.locator('body').inner_text());self.p.get_by_text('Ändras planen när en övning känns lätt?',exact=True).click();self.assertIn('ramar som behandlaren bestämt i förväg',self.p.locator('details[open]').inner_text());self.assertIn('I den nuvarande patientversionen sker ännu inga automatiska ändringar',self.p.locator('details[open]').inner_text());self.assertEqual(self.p.locator('link[rel="canonical"]').get_attribute('href'),'https://www.kansei.se/reda-rehab/');self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),391)
 def test_example_changes_real_exercise_variants(self):
  self.p.goto(self.o+'/reda-rehab/');self.p.get_by_role('button',name='Gym',exact=True).click();self.assertEqual(self.p.get_by_role('button',name='Gym',exact=True).get_attribute('aria-pressed'),'true');self.assertIn('styrkan',self.p.locator('#example-goal').inner_text());self.assertGreater(self.p.locator('#example-motion svg').count(),0);self.p.get_by_role('button',name='Löpning',exact=True).click();self.assertIn('löpningen',self.p.locator('#example-goal').inner_text());self.assertGreater(self.p.locator('#example-exercises button').count(),1)
 def test_demo_rounds_reach_followup_and_reset(self):
  self.p.goto(self.o+'/reda-rehab/');self.p.locator('[data-view="exercise"]').click();self.p.locator('#mark-round').click();self.assertIn('1 av',self.p.locator('#round-status').inner_text());self.p.locator('[data-view="follow"]').click();self.assertIn('1 omgång',self.p.locator('#demo-progress').inner_text());self.p.locator('#reset-demo').click();self.p.locator('[data-view="follow"]').click();self.assertIn('Inget registrerat',self.p.locator('#demo-progress').inner_text());self.assertEqual(self.p.evaluate('localStorage.length'),0)
 def test_responsive_preview_and_motion_controls(self):
  self.p.emulate_media(reduced_motion='reduce');self.p.goto(self.o+'/reda-rehab/');self.p.locator('[data-view="exercise"]').click();self.assertEqual(self.p.locator('#play-motion').inner_text(),'Visa rörelsen');self.p.locator('[data-frame="1"]').click();self.assertEqual(self.p.locator('[data-frame="1"]').get_attribute('aria-pressed'),'true');self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),390)
  out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.locator('[data-view="plan"]').click();self.p.screenshot(path=str(out/'reda-landing-mobile.png'),full_page=True);self.p.set_viewport_size({'width':1440,'height':1000});self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),1440);self.p.screenshot(path=str(out/'reda-landing-desktop.png'),full_page=True)
 def test_homepage_explains_reda_and_preserves_old_portal(self):
  self.p.goto(self.o+'/');card=self.p.locator('#planKort');card.scroll_into_view_if_needed();self.assertIn('Reda håller ihop',card.text_content());self.assertEqual(card.get_by_role('link',name='Läs om Reda →').get_attribute('href'),'/reda-rehab/');self.assertEqual(card.get_by_role('link',name='Har du redan ett Reda-program? Öppna patientportalen →').get_attribute('href'),'/reda/')
if __name__=='__main__':unittest.main(verbosity=2)
