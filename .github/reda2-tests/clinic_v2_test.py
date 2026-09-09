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
 def test_clinic_workspace(self):
  p=self.b.new_page(viewport={'width':1440,'height':1000});errs=[];p.on('pageerror',lambda e:errs.append(str(e)));p.goto(self.o+'/reda-2/klinik-2.html');self.assertIn('Anna Lind',p.locator('body').inner_text());self.assertIn('Progression sker i rummet',p.locator('body').inner_text());self.assertGreaterEqual(p.locator('.exercise').count(),3);p.locator('button[data-choice="stage"][data-value="gentle"]').click();self.assertIn('Förslag uppdaterat',p.locator('#status').inner_text());p.locator('#activate').click();self.assertTrue(p.locator('#modal').evaluate('e=>e.open'));self.assertIn('inte användas med verkliga patientuppgifter',p.locator('#modal').inner_text());self.assertEqual(errs,[]);p.close()
 def test_security_files_have_required_guards(self):
  sql=(ROOT/'reda-2/supabase/migrations/20260909_001_secure_reda.sql').read_text();rpc=(ROOT/'reda-2/supabase/migrations/20260909_002_session_rpc.sql').read_text();fn=(ROOT/'reda-2/supabase/functions/invite-patient/index.ts').read_text();self.assertIn('enable row level security',sql);self.assertIn("(auth.jwt()->>'aal')='aal2'",sql);self.assertIn('revoke all on public.reda_profiles',sql);self.assertIn('reda_activate_plan',sql);self.assertIn('client_session_id',rpc);self.assertIn('on conflict(client_session_id)',rpc);self.assertIn("ctx.jwtClaims?.aal !== 'aal2'",fn);self.assertIn('inviteUserByEmail',fn);self.assertNotIn('SUPABASE_SECRET_KEY',fn)
if __name__=='__main__':unittest.main(verbosity=2)
