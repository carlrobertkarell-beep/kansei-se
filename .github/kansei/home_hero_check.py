"""Exercise the homepage's first view and its route to a specific service without booking."""
from pathlib import Path

from playwright.sync_api import expect


def check_home_hero(page, output, viewport):
    original_size = page.viewport_size.copy()
    if viewport == 'mobile':
        page.set_viewport_size({'width': 390, 'height': 700})
    elif viewport == 'compact':
        page.set_viewport_size({'width': 320, 'height': 568})
    try:
        denied = page.locator('[data-statistics="no"]:visible')
        if denied.count():
            denied.click()
        page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
        hero = page.locator('.home-first-impression')
        expect(page.get_by_role('heading', level=1)).to_have_count(1)
        heading = hero.get_by_role('heading', level=1)
        expect(heading).to_be_visible()
        photo = hero.locator('.home-intro-image img')
        expect(photo).to_be_visible()
        expect(photo).to_have_attribute('fetchpriority', 'high')
        assert photo.get_attribute('loading') != 'lazy'
        assert 'carl-robert' in (photo.get_attribute('alt') or '').lower(), 'Identify the clinician in the photograph'
        assert photo.evaluate("""async image => {
            await image.decode();
            for (let parent = image; parent; parent = parent.parentElement) {
                if (Number(getComputedStyle(parent).opacity) === 0) return false;
            }
            const bounds = image.getBoundingClientRect();
            return image.naturalWidth >= 600 && bounds.width >= innerWidth * .45 && bounds.height >= 190;
        }"""), 'The first view must give a real, loaded clinician photograph substantial space'
        # Different authentic clinic photographs are used for mobile and wide screens.
        # The earlier close-up of an arm showed neither the clinician nor his face.
        assert photo.evaluate("""image => {
            const visible = new URL(image.currentSrc).pathname;
            return ['/bilder/kb7f0805cfb.webp', '/bilder/kliniken/carl-robert-ultraljud-mobil.webp'].includes(visible);
        }"""), 'The first view needs the clinician in the examining room'
        hero_text = hero.inner_text().lower()
        for detail in ('carl-robert', 'naprapat', 'ultraljud', 'odenplan'):
            assert detail in hero_text, f'Missing introduction detail: {detail}'
        choose = hero.locator('a[href="#vara-huvudtjanster"]')
        guide = hero.locator('a[href="/hjalp-mig-boka/"]')
        expect(choose).to_be_visible()
        expect(guide).to_be_visible()
        assert choose.get_attribute('data-measure') != 'booking_click', 'Choosing a visit is not an outbound booking click'
        assert page.locator('.site-header .header-book').get_attribute('href') == '#vara-huvudtjanster'
        if viewport == 'mobile':
            for element in (heading, choose):
                assert element.evaluate("""element => {
                    const box = element.getBoundingClientRect();
                    const header = document.querySelector('.site-header').getBoundingClientRect();
                    return box.top >= header.bottom - 1 && box.bottom <= innerHeight + 1;
                }"""), 'The mobile first view must show the heading and primary action'
        assert page.locator('.site-header').evaluate("""el => {
            const transparent = getComputedStyle(el).backgroundColor === 'rgba(0, 0, 0, 0)';
            return transparent && el.getBoundingClientRect().bottom > document.querySelector('.home-intro-image').getBoundingClientRect().top;
        }"""), 'The header must sit transparently over the photograph at the top'
        if viewport in ('mobile', 'compact'):
            assert hero.evaluate("el => el.getBoundingClientRect().bottom >= innerHeight - 1"), 'White strip below mobile hero'
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2'), 'Horizontal overflow on homepage'
        for link in (choose, guide):
            box = link.bounding_box()
            assert box and min(box['width'], box['height']) >= 44, 'Hero links need 44 px touch targets'

        page.screenshot(path=str(Path(output) / f'home-first-impression-{viewport}.png'),
                        full_page=False, animations='disabled')
        choose.focus()
        page.keyboard.press('Enter')
        expect(page.locator('#vara-huvudtjanster')).to_be_in_viewport()
        assert page.url.endswith('#vara-huvudtjanster'), 'Booking action should first reveal the three patient choices'
        page.evaluate("history.replaceState(null, '', location.pathname + location.search)")
        page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
        if page.url.startswith('http://127.0.0.1:4173'):
            check_header_search(page, output, viewport)
        return 'Clinician photograph, first-view guidance, keyboard routes and header search passed'
    finally:
        page.set_viewport_size(original_size)
        page.evaluate("window.scrollTo({top:0,behavior:'instant'})")


def check_header_search(page, output, viewport):
    header = page.locator('.site-header .header-icon-actions')
    booking = header.locator('.header-book')
    search = header.get_by_role('button', name='Sök på Kansei')
    menu = header.get_by_role('button', name='Öppna meny')
    boxes = [element.bounding_box() for element in (booking, search, menu)]
    if not all(box and box['width'] >= 44 and box['height'] >= 44 for box in boxes):
        raise AssertionError('The three header actions must have usable touch targets')
    if not boxes[0]['x'] < boxes[1]['x'] < boxes[2]['x']:
        raise AssertionError('Header action order must be booking, search, menu')
    if booking.inner_text().strip() != 'Boka' or booking.locator('svg').count() != 1:
        raise AssertionError('Header booking needs its calendar icon and short label')
    if booking.evaluate('link => getComputedStyle(link).backgroundColor') != 'rgba(0, 0, 0, 0)':
        raise AssertionError('Header booking must have no filled background')
    search.focus()
    page.keyboard.press('Enter')
    dialog = page.get_by_role('dialog', name='Sök på Kansei')
    query = dialog.get_by_role('searchbox', name='Sökord')
    expect(query).to_be_focused()
    query.fill('ultraljud kna')
    first = dialog.locator('.site-search-results a').first
    expect(first).to_have_attribute('href', '/ultraljud/kna/')
    query.fill('hitta hit')
    expect(first).to_have_attribute('href', '/kontakt/')
    page.screenshot(path=str(Path(output) / f'home-header-search-{viewport}.png'), animations='disabled')
    query.fill('zzzz-inte-ett-amne')
    expect(dialog.get_by_role('status')).to_have_text('Inga träffar. Prova ett annat sökord.')
    page.keyboard.press('Escape')
    expect(dialog).to_be_hidden()
    expect(search).to_be_focused()
    page.mouse.move(0, 0)
