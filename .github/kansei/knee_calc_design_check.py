"""Exercise the new mineral-deposition reader and its narrative entry points."""
from playwright.sync_api import expect

KNEE_CALC_PATH = '/ultraljud/kna/forkalkad-menisk/'


def check_knee_calc(page, output, label):
    viewer = page.locator('[data-knee-viewer]')
    tabs = viewer.get_by_role('tab')
    anatomy = viewer.locator('[data-knee-anatomy]')
    findings = viewer.locator('[data-knee-findings]')
    expect(tabs).to_have_count(3)
    expect(anatomy).to_be_enabled()
    expect(anatomy).to_have_attribute('aria-checked', 'false')
    expect(findings).to_have_attribute('aria-checked', 'false')
    keys = ('menisk-jamforelse', 'menisk-narbild', 'brosk-kalk')
    for index, key in enumerate(keys):
        tabs.nth(index).click()
        panel = viewer.locator('.knee-panel:not([hidden])')
        expect(panel).to_have_attribute('data-key', key)
        picture = panel.locator('.knee-picture')
        box = picture.bounding_box()
        assert box and box['width'] > 200 and abs(box['height'] / box['width'] - .75) < .01, 'Full scan canvas collapsed or distorted'
        expect(panel.locator('.knee-original')).to_have_attribute('data-scan-header', '68/960')
        dimensions = panel.locator('.knee-anatomy img').evaluate('(e)=>[e.naturalWidth,e.naturalHeight]')
        assert dimensions == [1280, 960]
        findings.click()
        expect(picture).to_have_attribute('data-findings', 'true')
        expect(picture).to_have_attribute('data-anatomy', 'false')
        anatomy.click()
        expect(picture).to_have_attribute('data-anatomy', 'true')
        viewer.locator('[data-knee-enlarge]').click()
        zoom = page.locator('#knee-zoom')
        expect(zoom).to_be_visible()
        expect(zoom.locator('[data-knee-zoom-frame]')).to_have_attribute('data-key', key)
        expect(zoom.locator('.knee-original')).to_have_attribute('data-scan-header', '68/960')
        zoom.locator('[data-knee-zoom-anatomy]').click()
        expect(anatomy).to_have_attribute('aria-checked', 'false')
        zoom.locator('[data-knee-zoom-close]').click()
        findings.click()
    tabs.first.click()
    tabs.first.press('ArrowLeft')
    expect(tabs.last).to_have_attribute('aria-selected', 'true')
    page.locator('.case-story-image-links [data-case-tab="tab-menisk-jamforelse"]').click()
    expect(tabs.first).to_have_attribute('aria-selected', 'true')
    expect(findings).to_have_attribute('aria-checked', 'true')
    expect(page.locator('.case-story-chapter')).to_have_count(3)
    expect(page.locator('.case-story-note')).to_contain_text('illustrativt exempel')
    for heading in page.locator('#faq summary').all():
        heading.click()
        assert heading.locator('..').get_attribute('open') is not None
        heading.click()
    return {'views': 3, 'full_canvas': 'passed', 'independent_layers': 'passed', 'zoom_and_header_clip': 'passed', 'keyboard_and_story_routes': 'passed'}
