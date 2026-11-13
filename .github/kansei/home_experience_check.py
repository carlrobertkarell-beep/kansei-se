"""Exercise the homepage's single image slider with real keyboard and mouse input."""
from playwright.sync_api import expect


def check_home_experience(page):
    root = page.locator('[data-home-diagnostic]')
    slider = page.get_by_role('slider', name='Andel illustrerad anatomi', exact=True)
    try:
        assert page.get_by_role('slider').count() == 1, 'Expected one exposed comparison slider'
        assert root.locator('.hd-range').count() == 0, 'Duplicate comparison range remains'
        slider.scroll_into_view_if_needed()
        page.wait_for_function(
            "node => [...node.querySelectorAll('img')].every(img => img.complete && img.naturalWidth > 0)",
            arg=slider.element_handle(), timeout=15000)
        expect(slider).to_have_attribute('aria-disabled', 'false', timeout=15000)
        if page.url.startswith('http://127.0.0.1:4173'):
            expect(slider).to_have_attribute('aria-valuenow', '0')
            expect(root.get_by_role('button', name='Ultraljud', exact=True)).to_have_attribute('aria-pressed', 'true')
        slider.press('End')
        expect(slider).to_have_attribute('aria-valuenow', '100')
        slider.press('Home')
        expect(slider).to_have_attribute('aria-valuenow', '0')
        root.get_by_role('button', name='Jämför', exact=True).click()
        expect(slider).to_have_attribute('aria-valuenow', '50')
        slider.scroll_into_view_if_needed()
        box = slider.bounding_box()
        assert box and box['width'] > 0, 'Comparison image has no drag surface'
        x, y = box['x'] + box['width'] * .5, box['y'] + box['height'] * .5
        scroll_before = page.evaluate('window.scrollY')
        page.mouse.move(x, y)
        page.mouse.down()
        try:
            # A real drag over the image catches native img drag stealing pointermove.
            page.mouse.move(box['x'] + box['width'] * .75, y, steps=8)
        finally:
            page.mouse.up()
        value = float(slider.get_attribute('aria-valuenow'))
        assert 70 <= value <= 80, f'Image drag stopped early at {value}%'
        assert abs(page.evaluate('window.scrollY') - scroll_before) <= 1, 'Image drag scrolled the page'
        findings = root.get_by_role('button', name='Visa fynden', exact=True)
        state_before = root.locator('[data-diagnostic-state]').text_content()
        expect(findings).to_have_attribute('aria-pressed', 'false')
        findings.click()
        expect(findings).to_have_attribute('aria-pressed', 'true')
        expect(root).to_have_attribute('data-diagnostic-findings', 'true')
        expect(root.locator('.hd-findings')).to_have_attribute('aria-hidden', 'false')
        assert root.locator('[data-diagnostic-state]').text_content() != state_before, 'Findings status did not change'
        return 'Single slider, keyboard endpoints, continuous mouse drag and findings passed'
    finally:
        page.evaluate("document.activeElement?.blur(); window.scrollTo({top:0,behavior:'instant'})")
        page.wait_for_function('window.scrollY === 0')
