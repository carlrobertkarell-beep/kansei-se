"""Check the homepage patient case and allow the prior live build during rollout."""
from playwright.sync_api import expect


def check_home_experience(page):
    preview = page.locator('.home-case-preview')
    if not preview.count() and page.url.startswith('https://www.kansei.se/'):
        return check_previous_home_experience(page)

    try:
        expect(preview.get_by_role('heading', level=2)).to_be_visible()
        image = preview.get_by_role('img')
        image.scroll_into_view_if_needed()
        page.wait_for_function(
            "img => img.complete && img.naturalWidth > 0",
            arg=image.element_handle(), timeout=15000)
        expect(image).to_have_attribute('src', '/bilder/ultraljud/kna/osteofyter-ultraljud.webp')
        link = preview.get_by_role('link', name='Se patientfallet')
        expect(link).to_have_attribute('href', '/ultraljud/kna/#artros')
        expect(preview.get_by_role('link')).to_have_count(1)
        expect(preview.get_by_role('button')).to_have_count(0)
        expect(preview.get_by_role('slider')).to_have_count(0)
        if page.viewport_size['width'] <= 860:
            assert preview.evaluate("""section => {
                const heading = section.querySelector('h2').getBoundingClientRect();
                const image = section.querySelector('img').getBoundingClientRect();
                const link = section.querySelector('a').getBoundingClientRect();
                return heading.bottom < image.top && link.top >= image.bottom &&
                    Math.abs(image.left - heading.left) <= 1 &&
                    Math.abs(image.right - link.right) <= 1 && link.height >= 44;
            }"""), 'Patient case must stack in reading order with aligned mobile margins'
        return 'Original ultrasound, one case link and mobile layout passed'
    finally:
        page.evaluate("document.activeElement?.blur(); window.scrollTo({top:0,behavior:'instant'})")
        page.wait_for_function('window.scrollY === 0')


def check_previous_home_experience(page):
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
