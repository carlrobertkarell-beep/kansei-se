"""Verify the three hip images, independent layers and enlarged reader."""
HIP_PATH = '/ultraljud/glutealsenor/bilder/'

def check_hip(page, output, label):
    navigation = page.locator('.case-page-nav')
    bounds = navigation.evaluate('''nav => {
        const box = nav.getBoundingClientRect();
        const heading = document.querySelector('h1').getBoundingClientRect();
        return {left: box.left, headingLeft: heading.left,
                links: [...nav.querySelectorAll('a')].map(a => {
                    const r = a.getBoundingClientRect();
                    return {left:r.left, right:r.right, top:r.top, height:r.height};
                })};
    }''')
    assert abs(bounds['left'] - bounds['headingLeft']) < 2, 'Section navigation must align with the introduction'
    assert len(bounds['links']) == 4 and all(r['height'] >= 43 for r in bounds['links']), 'Section links need separate touch targets'
    for previous, current in zip(bounds['links'], bounds['links'][1:]):
        if abs(previous['top'] - current['top']) < 2:
            assert current['left'] - previous['right'] >= 16, 'Section links must not run together'
    viewer=page.locator('[data-knee-viewer]')
    tabs=viewer.get_by_role('tab')
    assert tabs.count()==3, 'Three supplied long-axis views must be available'
    assert viewer.locator('.knee-panel:not([hidden])').get_attribute('data-key')=='gmed'
    anatomy=viewer.locator('[data-knee-anatomy]')
    findings=viewer.locator('[data-knee-findings]')
    page.wait_for_function("[...document.querySelectorAll('.knee-anatomy img')].every(i=>i.complete&&i.naturalWidth===1280)")
    assert anatomy.get_attribute('aria-checked')=='false', 'Start with the clinical original'
    findings.click()
    assert findings.get_attribute('aria-checked')=='true'
    assert anatomy.get_attribute('aria-checked')=='false', 'Findings must work on the original'
    anatomy.click()
    for index,key in enumerate(('gmed','gmin','paralabral')):
        tabs.nth(index).click()
        panel=viewer.locator('.knee-panel:not([hidden])')
        assert panel.get_attribute('data-key')==key
        assert anatomy.get_attribute('aria-checked')=='true'
        assert findings.get_attribute('aria-checked')=='true', 'Keep layer choices between views'
        assert panel.locator('.knee-picture').get_attribute('data-anatomy')=='true'
        assert panel.locator('.knee-findings').get_attribute('aria-hidden')=='false'
        panel.screenshot(path=str(output/f'hip-{key}-{label}.png'),animations='disabled',style='body>header{visibility:hidden!important}')
    tabs.first.press('ArrowLeft')
    assert tabs.last.get_attribute('aria-selected')=='true', 'Arrow keys wrap between images'
    viewer.locator('[data-knee-enlarge]').click()
    zoom=page.locator('#knee-zoom')
    assert zoom.is_visible()
    zoom.locator('[data-knee-zoom-anatomy]').click()
    assert anatomy.get_attribute('aria-checked')=='false', 'Zoom controls share reader state'
    zoom.locator('[data-knee-zoom-close]').click()
    assert not zoom.is_visible()
    findings.click()
    tabs.first.click()
    return {'views':3,'independent_layers':'passed','zoom':'passed','keyboard':'passed'}
