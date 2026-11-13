"""Check the homepage's introduction without opening a booking service."""
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
        hero = page.locator('.home-intro.home-first-impression')
        if hero.count() != 1 or page.locator('h1').count() != 1:
            raise AssertionError('Homepage needs one new introduction and one clear H1')
        heading = hero.locator('h1')
        lead = hero.locator('.landing-hero-lead')
        photo = hero.locator('.home-intro-image img')
        if photo.count() != 1 or not photo.is_visible() or not heading.is_visible() or not lead.is_visible():
            raise AssertionError('Hero photograph, heading or service introduction is missing')
        for content in (photo, heading, lead):
            if not content.evaluate('''element => {
                for (let node = element; node; node = node.parentElement) {
                    if (parseFloat(getComputedStyle(node).opacity) === 0) return false;
                }
                return true;
            }'''):
                raise AssertionError('Hero content is invisible behind an unfinished entrance')
        photo.evaluate('''async image => {
            if (!image.complete) await new Promise((resolve, reject) => {
                image.addEventListener('load', resolve, {once:true});
                image.addEventListener('error', reject, {once:true});
            });
        }''')
        if not photo.evaluate('image => image.naturalWidth > 0 && image.width > 0 && image.height > 0'):
            raise AssertionError('Hero photograph does not load or has no reserved space')
        if photo.get_attribute('loading') == 'lazy' or photo.get_attribute('fetchpriority') != 'high':
            raise AssertionError('The first hero photograph is delayed behind lazy or low-priority loading')
        if photo.get_attribute('src') != '/bilder/k945944e614.webp' or 'knä' not in photo.get_attribute('alt'):
            raise AssertionError('The homepage must show the authentic knee ultrasound photograph with descriptive alt text')
        introduction = (heading.inner_text() + " " + lead.inner_text()).casefold()
        if any(term not in introduction for term in ('naprapati', 'ultraljud', 'injektioner', 'hyaluron', 'prp', 'odenplan', 'stockholm')):
            raise AssertionError('Hero introduction no longer identifies services and local clinic')
        actions = hero.locator('.landing-hero-actions')
        booking = actions.locator('a[data-measure="booking_click"]')
        if booking.count() != 1 or booking.get_attribute('href') != 'https://www.bokadirekt.se/places/kansei-naprapati-rehabcenter-48847':
            raise AssertionError('Hero booking action is duplicated or its destination changed')
        if booking.get_attribute('data-placement') != 'hero' or booking.get_attribute('target') != '_blank':
            raise AssertionError('Hero booking placement or native target changed')
        help_link = actions.locator('a[href="/hjalp-mig-boka/"]')
        if help_link.count() != 1:
            raise AssertionError('The hero no longer offers one clear booking helper')
        if hero.locator('.home-treatment-routes').count():
            raise AssertionError('Hero repeats the service choices immediately below it')
        services = page.locator('main > section:nth-of-type(2)#vara-huvudtjanster .home-visit')
        if services.locator('h3').all_text_contents() != ['Naprapati', 'Ultraljud', 'Injektioner']:
            raise AssertionError('The introduction must be followed by the three service choices')
        injection_actions = services.filter(has=page.get_by_role('heading', name='Injektioner', exact=True)).locator('a')
        if injection_actions.evaluate_all('links => links.map(link => link.getAttribute("href"))') != ['/hyaluronsyra/', '/prp/']:
            raise AssertionError('Homepage injection options must link directly to hyaluron and PRP')
        for control in (booking, help_link, *services.locator('.home-visit-actions a').all()):
            if not control.is_visible() or not control.evaluate('''element => {
                const box = element.getBoundingClientRect();
                return box.width >= 44 && box.height >= 44;
            }'''):
                raise AssertionError('A homepage booking or service action is hidden or too small for touch')
        if page.evaluate('document.documentElement.scrollWidth > innerWidth + 3'):
            raise AssertionError('Homepage hero causes horizontal overflow')
        if not photo.evaluate('''image => {
            const photo = image.getBoundingClientRect();
            const section = image.closest('.home-first-impression');
            const hero = section.getBoundingClientRect();
            const heading = section.querySelector('h1').getBoundingClientRect();
            const mobile = matchMedia('(max-width: 760px)').matches;
            if (Math.abs(photo.top - hero.top) > 1 || Math.abs(photo.right - hero.right) > 1) return false;
            if (mobile) return Math.abs(photo.width - hero.width) <= 1 && photo.height >= 230 &&
                heading.top - photo.top >= 185 && heading.top >= photo.bottom - 53;
            return photo.width >= hero.width * .7 && Math.abs(photo.bottom - hero.bottom) <= 1 &&
                heading.bottom < hero.bottom;
        }'''):
            raise AssertionError('The homepage needs a prominent right-aligned photograph, above its text on mobile')
        feature = page.locator('.clinic-feature')
        if feature.locator('h2').inner_text() != 'Alla skador behöver inte opereras.' or \
                feature.locator('a[href="/ultraljud/"]').count() != 1:
            raise AssertionError('The homepage needs a clear injury message with a route to ultrasound information')
        if viewport == 'mobile':
            for element in (heading, lead, booking):
                if not element.evaluate('''element => {
                    const box = element.getBoundingClientRect();
                    const header = document.querySelector('.site-header').getBoundingClientRect();
                    return box.top >= header.bottom - 1 && box.bottom <= innerHeight + 1 &&
                        box.left >= -1 && box.right <= innerWidth + 1;
                }'''):
                    raise AssertionError('The 390px first view hides its heading, local service text or booking action')
        page.screenshot(path=str(Path(output) / ('home-first-impression-' + viewport + '.png')),
                        full_page=False, animations='disabled')
        # The search is installed by the shared public header script.
        # Push checks can briefly see the earlier live build while Pages publishes.
        if page.url.startswith('http://127.0.0.1:4173'):
            check_header_search(page, output, viewport)
        return 'Photograph, local service introduction, direct routes and accessible booking passed'
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
    expect(dialog.locator('.site-search-results a[href="/ultraljud/kna/"]')).to_be_visible()
    query.fill('hitta hit')
    expect(dialog.locator('.site-search-results a[href="/kontakt/"]')).to_be_visible()
    page.screenshot(path=str(Path(output) / f'home-header-search-{viewport}.png'), animations='disabled')
    query.fill('zzzz-inte-ett-amne')
    expect(dialog.get_by_role('status')).to_have_text('Inga träffar. Prova ett annat sökord.')
    page.keyboard.press('Escape')
    expect(dialog).to_be_hidden()
    expect(search).to_be_focused()
    page.mouse.move(0, 0)
