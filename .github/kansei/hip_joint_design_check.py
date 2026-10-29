"""Check the new hip-joint case across the shared clinical reader states."""
HIP_JOINT_PATH = '/ultraljud/hoftled/bilder/'

def check_hip_joint(page, output, label):
    nav = page.locator('.condition-hero .case-page-nav')
    assert nav.count() == 1
    targets = set(nav.locator('a').evaluate_all('(links)=>links.map(a=>a.getAttribute("href"))'))
    assert {'#patientfall', '#bilder', '#nasta-steg'} <= targets
    for a in nav.locator('a').all():
        assert page.locator(a.get_attribute('href')).count() == 1
    viewer = page.locator('[data-knee-viewer]')
    tabs = viewer.get_by_role('tab')
    assert tabs.count() == 3
    anatomy = viewer.locator('[data-knee-anatomy]')
    findings = viewer.locator('[data-knee-findings]')
    page.wait_for_function("[...document.querySelectorAll('.knee-anatomy img')].every(i=>i.complete&&i.naturalWidth===1280)")
    assert anatomy.get_attribute('aria-checked') == findings.get_attribute('aria-checked') == 'false'
    for index, key in enumerate(('kapsel','caput','jamforelse')):
        tabs.nth(index).click()
        panel = viewer.locator('.knee-panel:not([hidden])')
        assert panel.get_attribute('data-key') == key
        assert panel.locator('.knee-original').get_attribute('data-scan-header') == '68/960'
        findings.click()
        assert anatomy.get_attribute('aria-checked') == 'false'
        assert panel.locator('.knee-findings').get_attribute('aria-hidden') == 'false'
        anatomy.click()
        assert panel.locator('.knee-picture').get_attribute('data-anatomy') == 'true'
        panel.screenshot(path=str(output/f'hip-joint-{key}-{label}.png'),animations='disabled',style='body>header{visibility:hidden!important}')
        viewer.locator('[data-knee-enlarge]').click()
        zoom = page.locator('#knee-zoom')
        assert zoom.is_visible()
        assert zoom.locator('[data-knee-zoom-frame]').get_attribute('data-key') == key
        zoom.locator('[data-knee-zoom-anatomy]').click()
        assert anatomy.get_attribute('aria-checked') == 'false'
        zoom.locator('[data-knee-zoom-close]').click()
        findings.click()
    tabs.first.click()
    tabs.first.press('ArrowLeft')
    assert tabs.last.get_attribute('aria-selected') == 'true'
    page.locator('[data-case-tab="tab-caput"]').first.click()
    assert viewer.locator('.knee-panel:not([hidden])').get_attribute('data-key') == 'caput'
    assert findings.get_attribute('aria-checked') == 'true'
    assert page.locator('a[href*="/hyaluronsyra-sinogel-3478216"]').count() >= 1
    assert page.locator('.hip-story-chapter').count() == 3
    return {'views':3,'independent_layers':'passed','all_zoom_views':'passed','keyboard':'passed','story_image_link':'passed'}
