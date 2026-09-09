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
 def tearDownClass(c):c.b.close();c.pw.stop();c.s.shutdown()
 def setUp(self):
  self.c=self.b.new_context(viewport={'width':390,'height':844},permissions=['clipboard-write']);self.p=self.c.new_page();self.err=[];self.p.on('pageerror',lambda e:self.err.append(str(e)));self.p.goto(self.o+'/reda-2/snabb.html')
 def tearDown(self):self.assertEqual(self.err,[]);self.c.close()
 def test_default_is_fast_and_valid(self):
  self.assertIn('Från bedömning till plan',self.p.locator('h1').inner_text());self.assertIn('övningar',self.p.locator('#summary').inner_text());self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),391)
 def test_same_blueprint_changes_with_capacity(self):
  before=self.p.locator('#summary').inner_text();self.p.get_by_role('button',name='Behöver stöd').click();after=self.p.locator('#summary').inner_text();self.assertNotEqual(before,after);self.assertIn('stöd',after.lower())
 def test_dictation_prefills_without_network(self):
  self.p.locator('#dictation').fill('Achilles. Träningsvan. Hög belastning. Gym. Mål: tillbaka till löpning.');self.p.get_by_role('button',name='Tolka till val').click();text=self.p.locator('#summary').inner_text();self.assertIn('Achilles',text);self.assertIn('tillbaka till löpning',text.lower())
 def test_review_date_appears(self):
  self.p.locator('#review').fill('2026-10-01');self.assertIn('1 okt',self.p.locator('#summary').inner_text().lower())
 def test_patient_link_opens_expanded_exercise(self):
  self.p.get_by_role('button',name='Knä · patellarsena').click();encoded=self.p.evaluate('RedaCore.encodePlan((()=>{const bp=RedaClinical.blueprints.knee_tendon,p=RedaCore.template();p.items=bp.slots.map(id=>{const e=RedaData.exercises.find(x=>x.id===id),v=e.variants[0];return RedaCore.makeItem(id,v.id,RedaCore.allowedSides(id,v.id)[0])});return p})())');q=self.c.new_page();q.goto(self.o+'/reda-2/#plan='+encoded);self.assertIn('Quadriceps',q.locator('body').inner_text());q.close()
if __name__=='__main__':unittest.main(verbosity=2)