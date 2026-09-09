"""Real browser tests of fictitious Reda 2 data. Starts a localhost server; no external traffic."""
from __future__ import annotations
import functools
import http.server
import json
import os
from pathlib import Path
import threading
import unittest
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reda2-test-results'
KEY='reda2-prototype-v1'
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass

class RedaBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OUT.mkdir(exist_ok=True)
        cls.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(ROOT)))
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
        cls.origin=f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw=sync_playwright().start()
        executable=os.environ.get('REDA_BROWSER')
        cls.browser=cls.pw.chromium.launch(headless=True,**({'executable_path':executable} if executable else {}))
    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.pw.stop();cls.server.shutdown()
    def setUp(self):
        self.context=self.browser.new_context(viewport={'width':390,'height':844},accept_downloads=True)
        self.external=[]
        def route(r):
            if r.request.url.startswith(self.origin+'/'):r.continue_()
            else:self.external.append(r.request.url);r.abort()
        self.context.route('**/*',route)
        self.p=self.context.new_page();self.errors=[]
        self.p.on('pageerror',lambda e:self.errors.append(str(e)))
        self.p.goto(self.origin+'/reda-2/')
        self.p.evaluate("localStorage.setItem('kanseiLogg_preserve','LEGACY_UNCHANGED')")
    def tearDown(self):
        try:
            self.assertEqual(self.p.evaluate("localStorage.getItem('kanseiLogg_preserve')"),'LEGACY_UNCHANGED')
            self.assertEqual(self.errors,[])
            self.assertEqual(self.external,[])
        finally:self.context.close()
    def seed(self,js=''):
        self.p.evaluate("""() => {const plan=RedaCore.template();plan.days=[0,1,2,3,4,5,6];"""+js+""";localStorage.setItem('reda2-prototype-v1',JSON.stringify({schema:2,plan,sessions:[],settings:{large:false,sound:false}}));} """)
        self.p.reload()
    def start(self):
        self.p.get_by_role('button',name='Starta passet',exact=True).click()
    def mark(self):
        self.p.wait_for_timeout(430)
        self.p.get_by_role('button',name='Omgång klar',exact=True).click()
    def db(self):return self.p.evaluate("JSON.parse(localStorage.getItem('reda2-prototype-v1'))")
    def test_01_welcome_and_no_tracking(self):
        self.assertIn('Din plan.',self.p.locator('h1').inner_text())
        self.assertIn('noindex',self.p.locator('meta[name=robots]').get_attribute('content'))
        self.assertEqual(self.p.locator('script[src*="google"],script[src*="plausible"]').count(),0)
        self.p.screenshot(path=str(OUT/'01-welcome-mobile.png'),full_page=True)
    def test_02_home_responsive(self):
        self.seed()
        for width in (360,390,768,1440):
            self.p.set_viewport_size({'width':width,'height':1000 if width>1000 else 844})
            self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),width+1)
            self.p.screenshot(path=str(OUT/f'02-today-{width}.png'),full_page=True)
    def test_03_full_completion_and_feedback(self):
        self.seed();self.start();self.p.screenshot(path=str(OUT/'03-exercise-mobile.png'),full_page=True)
        for n in range(20):
            if self.p.get_by_role('button',name='Jag är redo').count():self.p.get_by_role('button',name='Jag är redo').click()
            if self.p.get_by_role('button',name='Omgång klar',exact=True).count():self.mark()
            else:break
        self.assertEqual(self.db()['sessions'][0]['status'],'complete')
        self.p.get_by_role('button',name='Lagom',exact=True).click()
        self.assertEqual(self.db()['sessions'][0]['feedback'],'Lagom')
        self.p.screenshot(path=str(OUT/'03-completed-mobile.png'),full_page=True)
    def test_04_skipped_is_not_complete(self):
        self.seed();self.start()
        for n in range(4):
            self.p.get_by_role('button',name='Hoppa över övningen',exact=True).click()
            self.p.get_by_role('button',name='Annan anledning',exact=True).click()
        self.assertEqual(self.db()['sessions'][0]['status'],'not-done')
        self.assertIn('0 av 4',self.p.locator('body').inner_text())
    def test_05_partial_persists_and_resumes(self):
        self.seed();self.start();self.mark()
        self.p.get_by_role('button',name='Spara och pausa passet',exact=True).click()
        before=self.db()['sessions'][0]['id'];self.p.reload()
        self.p.get_by_role('button',name='Fortsätt passet',exact=True).click()
        self.assertEqual(self.db()['sessions'][0]['id'],before)
        self.assertEqual(self.db()['sessions'][0]['items'][0]['done'],1)
        self.assertIn('Omgång 2 av 2',self.p.locator('.dose-card').inner_text())
    def test_06_early_finish_is_partial(self):
        self.seed();self.start();self.mark()
        self.p.get_by_role('button',name='Spara och pausa passet',exact=True).click()
        self.p.get_by_role('button',name='Avsluta passet för idag',exact=True).click()
        self.p.get_by_role('button',name='Avsluta och spara',exact=True).click()
        self.assertEqual(self.db()['sessions'][0]['status'],'partial')
    def test_07_explicit_initial_dose(self):
        self.seed('plan.adjustment.enabled=true;plan.adjustment.sets=1')
        self.start();self.assertIn('Omgång 1 av 1',self.p.locator('.dose-card').inner_text())
        self.mark();self.assertIn('Benspark',self.p.locator('h1').inner_text())
    def test_08_big_text_and_keyboard_dialog(self):
        self.seed();self.p.get_by_role('button',name='Hjälp och inställningar',exact=True).first.click()
        self.p.get_by_label('Större text').check()
        self.assertTrue(self.p.evaluate('document.documentElement.classList.contains("big-text")'))
        self.p.keyboard.press('Escape')
        self.assertFalse(self.p.locator('dialog').evaluate('(d)=>d.open'))
        self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),391)
    def test_09_invalid_shared_link_preserves_storage(self):
        self.seed();before=self.db()
        self.p.goto(self.origin+'/reda-2/#plan=INVALID')
        self.assertTrue(self.p.locator('.gate-error').is_visible())
        self.assertEqual(self.db(),before)
    def test_10_literal_user_input_not_html(self):
        self.seed('plan.title="<img src=x onerror=alert(1)>"')
        self.assertEqual(self.p.locator('img[src=x]').count(),0)
        self.assertIn('<img src=x',self.p.locator('body').inner_text())
    def test_11_builder_live_preview_and_variant(self):
        self.p.goto(self.origin+'/reda-2/klinik.html')
        self.p.get_by_label('Programrubrik',exact=True).fill('Mitt ändrade testprogram')
        self.p.wait_for_timeout(600)
        frame=self.p.frame_locator('#preview')
        frame.get_by_role('heading',name='Mitt ändrade testprogram',exact=True).wait_for()
        self.p.locator('select[data-field=variant]').first.select_option('free')
        self.assertIn('utan hjälp av händerna',self.p.locator('.edit-variant').first.inner_text())
        self.assertEqual(self.p.locator('select[data-field=side]').first.locator('option').count(),1)
        self.p.set_viewport_size({'width':1600,'height':1100})
        self.p.screenshot(path=str(OUT/'11-editor-desktop.png'),full_page=False)
    def test_12_reorder_add_remove(self):
        self.p.goto(self.origin+'/reda-2/klinik.html')
        self.p.get_by_role('button',name='Lägg till',exact=True).click()
        self.p.get_by_label('Sök övning eller område').fill('Höftlyft')
        self.p.get_by_role('button',name='Höftlyft',exact=True).click()
        self.assertEqual(self.p.locator('.edit-exercise').count(),5)
        self.p.get_by_role('button',name='Flytta Höftlyft upp',exact=True).click()
        self.assertIn('Höftlyft',self.p.locator('.edit-exercise h3').nth(3).inner_text())
        self.p.get_by_role('button',name='Ta bort Höftlyft',exact=True).click()
        self.assertEqual(self.p.locator('.edit-exercise').count(),4)
    def test_13_share_requires_review(self):
        self.p.goto(self.origin+'/reda-2/klinik.html')
        self.p.get_by_role('button',name='Skapa testlänk',exact=True).click()
        self.assertTrue(self.p.get_by_role('button',name='Kopiera testlänken',exact=True).is_disabled())
        self.p.locator('#review-check').check()
        self.assertTrue(self.p.get_by_role('button',name='Kopiera testlänken',exact=True).is_enabled())
    def test_14_invalid_dose_blocks_preview(self):
        self.p.goto(self.origin+'/reda-2/klinik.html')
        self.p.locator('input[data-dose=sets]').first.fill('0')
        self.p.wait_for_timeout(500)
        self.assertTrue(self.p.locator('#builder-errors').is_visible())
        self.p.get_by_role('button',name='Skapa testlänk',exact=True).click()
        self.assertFalse(self.p.locator('dialog').evaluate('(x)=>x.open'))
    def test_15_backup_round_trip(self):
        self.seed();self.start();self.mark();self.p.get_by_role('button',name='Spara och pausa passet',exact=True).click()
        self.p.get_by_role('button',name='Hjälp och inställningar',exact=True).first.click()
        self.p.locator('summary').filter(has_text='Flytta eller säkerhetskopiera').click()
        with self.p.expect_download() as dl:self.p.get_by_role('button',name='Exportera säkerhetskopia',exact=True).click()
        path=OUT/'test-backup.json';dl.value.save_as(str(path))
        before=self.db()['sessions'][0]
        self.p.locator('#backup-input').set_input_files(path)
        self.p.get_by_role('button',name='Läs in testkopian',exact=True).click()
        self.assertEqual(self.db()['sessions'][0],before)
    def test_16_bad_import_is_non_destructive(self):
        self.seed();before=self.db()
        self.p.locator('#backup-input').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':b'{"schema":2,"type":"reda2-test-backup","sessions":[]}'})
        self.assertIn('Kunde inte läsa filen',self.p.locator('dialog').inner_text())
        self.assertEqual(self.db(),before)
    def test_17_preview_never_overwrites_patient_testlog(self):
        self.seed();before=self.db()
        encoded=self.p.evaluate('RedaCore.encodePlan(RedaCore.template("hip"))')
        self.p.goto(self.origin+'/reda-2/#preview='+encoded)
        self.assertEqual(self.db(),before)
        self.p.get_by_role('button',name='Idag',exact=True).last.click()
        if self.p.get_by_role('button',name='Starta passet',exact=True).count():self.start()
        self.assertEqual(self.db(),before)
    def test_18_mobile_editor_overflow(self):
        self.p.goto(self.origin+'/reda-2/klinik.html')
        self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),391)
    def test_19_followup_reflects_actual_partial(self):
        self.seed();self.start();self.mark();self.p.get_by_role('button',name='Spara och pausa passet',exact=True).click()
        self.p.get_by_role('button',name='Uppföljning',exact=True).last.click()
        self.assertIn('Påbörjat',self.p.locator('body').inner_text())
        self.assertIn('0 av 4',self.p.locator('body').inner_text())
        self.p.screenshot(path=str(OUT/'19-followup-mobile.png'),full_page=True)
    def test_20_rest_timer_does_not_complete_round(self):
        self.seed('plan.items[0].dose.rest=1');self.start();self.mark();self.p.wait_for_timeout(1250)
        self.assertIn('Pausen är klar',self.p.locator('body').inner_text())
        self.assertEqual(self.db()['sessions'][0]['items'][0]['done'],1)
    def test_21_guidance_never_completes_round(self):
        self.seed('plan.items[0].dose.reps=1;plan.items[0].dose.tempo=2');self.start()
        self.p.get_by_role('button',name='Träna med tidsstöd',exact=True).click();self.p.wait_for_timeout(2300)
        self.assertEqual(self.db()['sessions'][0]['items'][0]['done'],0)
        self.assertIn('först när du själv är färdig',self.p.locator('#guide-text').inner_text())

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RedaBrowserTests))
    (OUT/'test-summary.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)},indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
