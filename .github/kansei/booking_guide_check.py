"""Browser checks for the booking guide without opening a booking provider."""

from playwright.sync_api import expect


def check_booking_guide(page, output, viewport):
    guide = page.locator('#guide-dialog')
    opener = page.locator('[data-area="knee"]')
    decline = page.locator('button[data-statistics="no"]:visible')
    if decline.count():
        decline.click()

    def save(label):
        if viewport == 'mobile':
            page.screenshot(path=str(output / f'booking-guide-{label}-mobile.png'), animations='disabled')

    def choose(attribute, value):
        guide.locator(f'button[data-{attribute}="{value}"]').click(timeout=5000)

    def step(screen, number=None):
        expect(guide.locator('#guide-content')).to_have_attribute('data-guide-screen', screen)
        expect(guide.locator('#guide-title')).to_be_focused()
        if number:
            expect(guide.get_by_role('progressbar')).to_have_attribute('aria-valuenow', str(number))
        if viewport != 'desktop':
            assert guide.evaluate(
                """dialog => {
                    const rect = dialog.getBoundingClientRect();
                    const close = dialog.querySelector('[data-close]').getBoundingClientRect();
                    return rect.left >= -1 && rect.right <= innerWidth + 1 &&
                        dialog.scrollWidth <= dialog.clientWidth + 2 &&
                        close.width >= 44 && close.height >= 44 &&
                        close.top >= -1 && close.bottom <= innerHeight + 1;
                }"""
            ), f'{screen}: guide exceeds the mobile viewport or its close control is unreachable'
            for choice in guide.locator('.guide-choice:visible').all():
                assert choice.evaluate('el => el.getBoundingClientRect().height >= 44'), 'Guide choice has a small touch target'

    def select_pattern(area, pattern):
        choose('guide-area', area)
        step('patterns', 1)
        choose('pattern', pattern)
        step('goals', 2)

    def select_goal(goal):
        choose('goal', goal)
        step('safety', 3)
        choose('safety', 'continue')
        step('result', 4)

    def result(title, reason):
        expect(guide.locator('.result-main h3')).to_have_text(title)
        assert reason in guide.locator('.guide-visit-copy').inner_text().casefold(), f'{title}: wrong area in result explanation'

    def booking(service_id):
        cta = guide.locator('.result-main a[data-placement="guide"]')
        expect(cta).to_have_count(1)
        href = cta.get_attribute('href') or ''
        assert href.startswith('https://www.bokadirekt.se/boka-tjanst/') and href.endswith('-' + service_id), href
        expect(cta).to_have_attribute('target', '_blank')

    def reset():
        guide.locator('button[data-reset]').click()
        step('areas', 1)

    def close():
        page.keyboard.press('Escape')
        expect(guide).not_to_have_attribute('open', '')

    save('entry')
    opener.click()
    step('patterns', 1)
    choose('pattern', 'arthritis')
    step('goals', 2)
    save('goals')
    select_goal('injection')
    result('Hyaluron i knät', 'bedömd')
    expect(guide.locator('.guide-booking a')).to_have_attribute('href', '/hyaluronsyra/kna/#boka')
    expect(guide.locator('.guide-case a')).to_have_attribute('href', '/ultraljud/kna/artros-ledband-hyaluron/')
    expect(guide.locator('a[href="/blogg/prp-eller-hyaluronsyra-vid-knaartros/"]')).to_be_visible()
    expect(guide.locator('.guide-result-next li')).to_be_visible()
    expect(guide.locator('.result-main a[href*="bokadirekt.se"]')).to_have_count(0)
    save('result')
    comparison = guide.locator('.guide-comparison')
    comparison.locator('summary').click()
    expect(comparison).to_have_attribute('open', '')
    expect(comparison.locator('h3')).to_have_text(['Hyaluron i knät', 'Naprapatisk bedömning'])
    if viewport == 'mobile':
        comparison.screenshot(path=str(output / 'booking-guide-comparison-mobile.png'), animations='disabled')

    guide.locator('[data-edit-goal]').click()
    step('goals', 2)
    expect(guide.locator('[data-goal="injection"]')).to_have_attribute('data-current-choice', '')
    guide.locator('[data-guide-back]').click()
    step('patterns', 1)
    expect(guide.locator('[data-pattern="arthritis"]')).to_have_attribute('data-current-choice', '')
    close()
    expect(opener).to_be_focused()

    if viewport != 'desktop':
        return

    page.locator('[data-area="shoulder"]').click()
    step('patterns', 1)
    choose('pattern', 'lifting')
    step('goals', 2)
    select_goal('investigate')
    result('Muskuloskeletalt ultraljud', 'axel')
    booking('1946824')
    expect(guide.locator('.guide-case a')).to_have_attribute('href', '/ultraljud/kalkaxel/')
    guide.locator('[data-edit-goal]').click()
    step('goals', 2)
    select_goal('rehab')
    result('Naprapatisk bedömning', 'axeln')
    booking('3263299')
    reset()

    select_pattern('hip', 'side')
    select_goal('investigate')
    result('Muskuloskeletalt ultraljud', 'höften')
    booking('1946824')
    expect(guide.locator('.guide-case a')).to_have_attribute('href', '/ultraljud/glutealsenor/bilder/')
    reset()

    select_pattern('lowerLeg', 'achilles')
    expect(guide.locator('[data-goal="injection"]')).to_have_count(0)
    select_goal('investigate')
    result('Muskuloskeletalt ultraljud', 'hälsenan')
    booking('1946824')
    expect(guide.locator('.guide-case a')).to_have_attribute('href', '/ultraljud/halsena/bilder/')
    reset()

    select_pattern('lowerLeg', 'calf')
    choose('goal', 'investigate')
    step('safety', 3)
    expect(guide.get_by_text('Ny svullnad och värme i ena vaden eller benet.')).to_be_visible()
    choose('safety', 'care')
    step('care')
    expect(guide.locator('a[href="tel:1177"]')).to_be_visible()
    expect(guide.locator('a[href="tel:112"]')).to_be_visible()
    expect(guide.locator('a[href*="bokadirekt.se"]')).to_have_count(0)
    reset()

    choose('guide-area', 'shoulder')
    choose('pattern', 'injury')
    step('care')
    expect(guide.locator('a[href*="bokadirekt.se"]')).to_have_count(0)
    close()

    page.locator('[data-guide-intent="injection"]').click()
    step('areas', 1)
    expect(guide.locator('button[data-guide-area]')).to_have_count(3)
    expect(guide.locator('[data-guide-area="lowerLeg"]')).to_have_count(0)
    choose('guide-area', 'hip')
    choose('pattern', 'groin')
    step('prior', 2)
    choose('prior', 'no')
    step('safety', 3)
    choose('safety', 'continue')
    step('result', 4)
    result('Naprapatisk bedömning', 'höftens')
    booking('3263299')
    expect(guide.locator('a[href*="/hyaluronsyra/"]')).to_have_count(0)
    close()

    page.locator('[data-guide-intent="investigate"]').click()
    step('areas', 1)
    choose('guide-area', 'shoulder')
    choose('pattern', 'lifting')
    step('safety', 3)
    choose('safety', 'continue')
    step('result', 4)
    result('Muskuloskeletalt ultraljud', 'axel')
    close()
