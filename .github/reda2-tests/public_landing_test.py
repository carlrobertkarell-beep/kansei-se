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
 def test_archived_development_example(self):
  self.p.goto(self.o+'/reda-rehab/forhandsvisning.html');self.assertIn('Din plan',self.p.locator('h1').inner_text());self.assertIn('Försäljningen har inte öppnat',self.p.locator('.care-options').inner_text());self.assertNotIn('2 490',self.p.locator('body').inner_text());self.p.get_by_text('Ändras planen när en övning känns lätt?',exact=True).click();self.assertIn('ramar som behandlaren bestämt i förväg',self.p.locator('details[open]').inner_text());self.assertIn('I den nuvarande patientversionen sker ännu inga automatiska ändringar',self.p.locator('details[open]').inner_text());self.assertEqual(self.p.locator('link[rel="canonical"]').get_attribute('href'),'https://www.kansei.se/reda-rehab/forhandsvisning.html');self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),391)
 def test_example_changes_real_exercise_variants(self):
  self.p.goto(self.o+'/reda-rehab/forhandsvisning.html');self.p.get_by_role('button',name='Gym',exact=True).click();self.assertEqual(self.p.get_by_role('button',name='Gym',exact=True).get_attribute('aria-pressed'),'true');self.assertIn('styrkan',self.p.locator('#example-goal').inner_text());self.assertGreater(self.p.locator('#example-motion svg').count(),0);self.p.get_by_role('button',name='Löpning',exact=True).click();self.assertIn('löpningen',self.p.locator('#example-goal').inner_text());self.assertGreater(self.p.locator('#example-exercises button').count(),1)
 def test_demo_rounds_reach_followup_and_reset(self):
  self.p.goto(self.o+'/reda-rehab/forhandsvisning.html');self.p.locator('[data-view="exercise"]').click();self.p.locator('#mark-round').click();self.assertIn('1 av',self.p.locator('#round-status').inner_text());self.p.locator('[data-view="follow"]').click();self.assertIn('1 omgång',self.p.locator('#demo-progress').inner_text());self.p.locator('#reset-demo').click();self.p.locator('[data-view="follow"]').click();self.assertIn('Inget registrerat',self.p.locator('#demo-progress').inner_text());self.assertEqual(self.p.evaluate('localStorage.length'),0)
 def test_responsive_preview_and_motion_controls(self):
  self.p.emulate_media(reduced_motion='reduce');self.p.goto(self.o+'/reda-rehab/forhandsvisning.html');self.p.locator('[data-view="exercise"]').click();self.assertEqual(self.p.locator('#play-motion').inner_text(),'Visa rörelsen');self.p.locator('[data-frame="1"]').click();self.assertEqual(self.p.locator('[data-frame="1"]').get_attribute('aria-pressed'),'true');self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),390)
  out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True);self.p.locator('[data-view="plan"]').click();self.p.screenshot(path=str(out/'reda-landing-mobile.png'),full_page=True);self.p.set_viewport_size({'width':1440,'height':1000});self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),1440);self.p.screenshot(path=str(out/'reda-landing-desktop.png'),full_page=True)
 def test_homepage_explains_reda_and_preserves_old_portal(self):
  self.p.goto(self.o+'/');card=self.p.locator('#planKort');card.scroll_into_view_if_needed();self.assertIn('Kommer snart',card.text_content());self.assertEqual(card.get_by_role('link',name='Upptäck Reda →').get_attribute('href'),'/reda-rehab/');self.assertEqual(card.get_by_role('link',name='Har du redan ett Reda-program? Öppna patientportalen →').get_attribute('href'),'/reda/')
 def test_coming_soon_and_support_without_javascript(self):
  self.c.close();self.c=self.b.new_context(viewport={'width':390,'height':844},java_script_enabled=False);self.p=self.c.new_page()
  self.p.goto(self.o+'/reda-rehab/');self.assertIn('Mer rörelse.',self.p.locator('h1').inner_text());self.assertIn('Kommer snart',self.p.locator('.status').inner_text());self.assertEqual(self.p.locator('script').count(),0);self.assertEqual(self.p.locator('form').count(),0);self.assertNotIn('Hyrox',self.p.locator('main').inner_text());self.assertEqual(self.p.locator('link[rel=canonical]').get_attribute('href'),'https://www.kansei.se/reda-rehab/')
  out=ROOT/'reda2-test-results';out.mkdir(exist_ok=True)
  for width in [320,390,768,1440]:
   self.p.set_viewport_size({'width':width,'height':1000});self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),width);self.p.screenshot(path=str(out/f'reda-coming-soon-{width}.png'),full_page=True)
  self.p.set_viewport_size({'width':390,'height':844});self.p.locator('header').get_by_role('link',name='Hjälp & support').click();self.assertIn('/support/',self.p.url);self.p.get_by_text('Min programkod fungerar inte. Vad gör jag?',exact=True).click();self.assertIn('extra mellanslag',self.p.locator('details[open]').inner_text());self.p.get_by_text('Finns det en AI-chatt för support?',exact=True).click();self.assertIn('Ingen supportchatt är öppen ännu',self.p.locator('#lansering').inner_text());self.assertEqual(self.p.locator('form,script').count(),0);self.assertTrue(self.p.locator('#kontakt a.portal').get_attribute('href').startswith('mailto:info@kansei.se?subject='));self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),390);self.p.screenshot(path=str(out/'reda-support-mobile.png'),full_page=True)
  for route in ['/','/rehabilitering/']:
   self.p.goto(self.o+route);self.assertIn('Kommer snart',self.p.locator('#planKort').inner_text());self.assertEqual(self.p.locator('#planKort .reda-portal-link').get_attribute('href'),'/reda/')
 def test_rehab_card_stays_consistent_with_javascript(self):
  self.p.goto(self.o+'/rehabilitering/');self.assertIn('Kommer snart',self.p.locator('#planKort').inner_text());self.assertIn('Mer rörelse.',self.p.locator('#planKort h3').inner_text());self.assertEqual(self.p.locator('#planKort .plan-lockup').get_attribute('src'),'/bilder/reda/nav.svg?v=2')
if __name__=='__main__':unittest.main(verbosity=2)
