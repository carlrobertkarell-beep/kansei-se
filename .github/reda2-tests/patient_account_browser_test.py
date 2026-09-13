"""Patient account menu and presentation. Fictional APIs; never change a live account."""
import unittest
from pathlib import Path
from playwright.sync_api import expect
from recovery_browser_test import RecoveryTests

class Account(RecoveryTests):
 def shot(self,name):
  out=Path('reda2-test-results');out.mkdir(exist_ok=True);self.p.screenshot(path=str(out/name),animations='disabled')
 def settings(self):self.p.get_by_role('button',name='Inställningar',exact=True).click()
 def close_settings(self):self.p.get_by_role('button',name='Stäng inställningar',exact=True).click()
 def section(self,name):self.p.get_by_label('Inställningskategori',exact=True).select_option(label=name)
 def test_theme_defaults_dark_and_preferences_persist_without_touching_training(self):
  before=self.p.evaluate("localStorage.getItem('test-server')");expect(self.p.locator('html')).to_have_attribute('data-reda-theme','dark');self.shot('account-home-dark.png');self.settings();self.shot('account-settings-dark.png');self.p.get_by_role('button',name='Ljust',exact=True).click();expect(self.p.locator('html')).to_have_attribute('data-reda-theme','light');self.shot('account-settings-light.png');self.close_settings();self.shot('account-home-light.png');self.p.reload();expect(self.p.locator('html')).to_have_attribute('data-reda-theme','light');self.assertEqual(self.p.evaluate("localStorage.getItem('test-server')"),before)
 def test_system_theme_tracks_device_changes_and_explicit_choice_overrides(self):
  self.settings();self.p.locator('[data-pref=theme][data-value=system]').click();self.p.emulate_media(color_scheme='dark');expect(self.p.locator('html')).to_have_attribute('data-reda-theme','dark');self.p.emulate_media(color_scheme='light');expect(self.p.locator('html')).to_have_attribute('data-reda-theme','light');self.p.get_by_role('button',name='Mörkt',exact=True).click();expect(self.p.locator('html')).to_have_attribute('data-reda-theme','dark')
 def test_menu_profile_and_escape_keep_focus_and_hide_clinician_controls(self):
  self.p.get_by_role('button',name='Öppna kontomenyn').click();expect(self.p.locator('.account-trigger')).to_have_attribute('aria-expanded','true');self.shot('account-menu-dark.png');self.p.locator('.account-menu').get_by_role('button',name='Min profil',exact=True).click();expect(self.p.locator('#settingsPanel')).to_contain_text('Fiktiv testperson');expect(self.p.locator('#settingsPanel')).to_contain_text('Säker länk');self.p.keyboard.press('Escape');expect(self.p.locator('.account-trigger')).to_be_focused();expect(self.p.locator('.account-trigger')).to_have_attribute('aria-expanded','false');expect(self.p.locator('.account-menu [data-clinic]')).to_have_count(0)
 def test_still_images_preference_reaches_the_exercise_player(self):
  self.settings();self.p.get_by_role('button',name='Stillbilder',exact=True).click();self.close_settings();self.p.locator('#start').click();expect(self.p.locator('#motionPlay')).to_be_disabled();self.p.locator('#lessonGuided').click();self.p.locator('.lesson-stills summary').first.click();self.p.locator('#movementLesson [data-motion-frame="1"]').click();expect(self.p.locator('#motionPhase')).to_have_text('Slutläge');expect(self.p.locator('#sessionProgressText')).to_contain_text('0 av');self.shot('account-player-still-dark.png')
 def test_large_text_and_billing_state_fit_small_phone(self):
  self.p.set_viewport_size({'width':320,'height':640});self.settings();self.p.get_by_role('button',name='Större text',exact=True).click();expect(self.p.locator('html')).to_have_attribute('data-reda-text','large');self.shot('account-settings-large.png');self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));self.section('Köp & abonnemang');expect(self.p.locator('#settingsPanel')).to_contain_text('ännu inte anslutna');expect(self.p.get_by_role('button',name='Betala',exact=True)).to_have_count(0);self.section('Mina uppgifter');self.p.get_by_role('button',name='Öppna min plan',exact=False).click();expect(self.p.locator('#program')).to_be_visible();expect(self.p.locator('.patient-settings')).not_to_be_visible()
 def test_unsynced_session_still_prevents_logout_from_menu(self):
  self.p.evaluate("localStorage.setItem('test-fail','yes')");self.p.locator('#start').click();self.p.locator('[data-round="0"]').click();expect(self.p.locator('#retrySync')).to_be_visible();self.p.locator('#closePlayer').click();self.p.locator('.account-trigger').click();self.p.locator('#logout').click();expect(self.p.locator('#sync')).to_contain_text('Synka passet innan du loggar ut');expect(self.p.locator('#app')).to_be_visible();self.assertEqual(self.p.evaluate("JSON.parse(localStorage.getItem('test-server')).sessions.length"),0)
 def test_storage_denial_reports_unsaved_choice_without_breaking_settings(self):
  self.p.evaluate("Storage.prototype.setItem=function(k,v){if(k==='reda-presentation-v1')throw Error('blocked')}");self.settings();self.p.get_by_role('button',name='Ljust',exact=True).click();expect(self.p.locator('html')).to_have_attribute('data-reda-theme','light');expect(self.p.locator('[data-preference-status]')).to_contain_text('kunde inte sparas');self.assertEqual(self.errors,[])
 def test_public_preview_and_dark_instruction_share_the_app_theme(self):
  self.p.goto(self.origin+'/reda-2/exercise-guide.html');self.p.get_by_role('button',name='Titta på Benspark från stol',exact=True).click();expect(self.p.locator('.journey-preview')).to_be_visible();self.shot('account-preview-dark.png');self.p.locator('#preview-lessonGuided').click();self.shot('account-instruction-dark.png');self.p.keyboard.press('Escape');self.p.locator('.journey-close').click();self.p.locator('[data-tab=activity]').click();self.shot('account-history-dark.png')
 def test_open_settings_follow_preference_changes_from_another_tab(self):
  self.settings();other=self.c.new_page();other.goto(self.origin+'/reda-2/exercise-guide.html');other.get_by_role('button',name='Inställningar',exact=True).click();other.get_by_role('button',name='Ljust',exact=True).click();expect(self.p.locator('html')).to_have_attribute('data-reda-theme','light');expect(self.p.get_by_role('button',name='Ljust',exact=True)).to_have_attribute('aria-pressed','true');other.close()
 def test_desktop_settings_navigation_and_invalid_stored_preference(self):
  self.p.evaluate("localStorage.setItem('reda-presentation-v1',JSON.stringify({theme:'invalid',text:'invalid',motion:'invalid'}))");self.p.reload();expect(self.p.locator('html')).to_have_attribute('data-reda-theme','dark');self.p.set_viewport_size({'width':1280,'height':900});self.settings();self.shot('account-settings-desktop.png');self.p.get_by_role('navigation',name='Inställningskategorier').get_by_role('button',name='Hjälp & kontakt',exact=True).click();expect(self.p.locator('#settingsPanel')).to_contain_text('Hjälp i ditt pass');expect(self.p.get_by_label('Inställningskategori',exact=True)).not_to_be_visible()
 def test_dark_text_and_primary_action_have_readable_contrast(self):
  values=self.p.evaluate("""()=>{const b=document.body,c=document.querySelector('#start');return [getComputedStyle(b).color,getComputedStyle(b).backgroundColor,getComputedStyle(c).color,getComputedStyle(c).backgroundColor]}""")
  import re
  def luminance(s):
   rgb=[int(x)/255 for x in re.findall(r'\d+',s)[:3]];v=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb];return sum(a*b for a,b in zip(v,[.2126,.7152,.0722]))
  for fg,bg in [(values[0],values[1]),(values[2],values[3])]:
   a,b=sorted([luminance(fg),luminance(bg)]);self.assertGreaterEqual((b+.05)/(a+.05),4.5)

def load_tests(loader,tests,pattern):return unittest.TestSuite(Account(n)for n in Account.__dict__ if n.startswith('test_'))
if __name__=='__main__':unittest.main(verbosity=2)
