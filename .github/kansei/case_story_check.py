"""Check the path from a clinical narrative to an existing ultrasound reader."""

STORY_PATHS = (
    '/ultraljud/axel/bicepstendinopati/',
    '/ultraljud/axel/pectoralisruptur/',
    '/ultraljud/axel/ac-ledsskada/',
    '/ultraljud/hand-handled/karpaltunnelsyndrom/',
    '/ultraljud/kalkaxel/',
    '/ultraljud/tennisarmbage/bilder/',
    '/ultraljud/halsena/bilder/',
    '/ultraljud/loparkna/',
)


def check_story(page, path, output, label):
    story = page.locator('#patientfall')
    if story.count() != 1:
        raise AssertionError('Clinical narrative missing or duplicated')
    if page.locator('.case-page-nav a[href="#patientfall"]').count() != 1:
        raise AssertionError('Narrative is not reachable from page navigation')
    links = story.locator('[data-case-view]')
    if not links.count():
        raise AssertionError('Narrative has no route to the image reader')
    checked = set()
    for link in links.all():
        tab_id = link.get_attribute('data-case-tab') or ''
        findings = link.get_attribute('data-case-findings') == 'true'
        key = (tab_id, findings)
        if key in checked:
            continue
        if not checked:
            link.focus()
            page.keyboard.press('Enter')
        else:
            link.click()
        if tab_id:
            tab = page.locator('#' + tab_id)
            if tab.get_attribute('aria-selected') != 'true':
                raise AssertionError('Narrative opened the wrong image tab')
            if not page.locator('#' + tab.get_attribute('aria-controls')).is_visible():
                raise AssertionError('Narrative image panel is not visible')
        if findings:
            viewer = page.locator('[data-patient-viewer],[data-knee-viewer],[data-elbow-viewer],[data-achilles-viewer]')
            toggle = viewer.locator('[data-patient-findings],[data-knee-findings]')
            if not toggle.is_visible() or toggle.get_attribute('aria-checked') != 'true':
                raise AssertionError('Narrative does not reveal the requested findings')
        checked.add(key)
    story.scroll_into_view_if_needed()
    image = story.locator('img').first
    image.scroll_into_view_if_needed()
    page.wait_for_function("[...document.querySelectorAll('#patientfall img')].every(i=>i.complete&&i.naturalWidth>0)")
    slug = path.strip('/').replace('/', '-')
    story.screenshot(
        path=str(output / f'patient-case-{slug}-{label}.png'),
        animations='disabled',
        style='.header,.skip-link{visibility:hidden!important}',
    )
    return {'image_routes': len(checked), 'keyboard': 'Passed', 'narrative_and_image': 'Passed'}
