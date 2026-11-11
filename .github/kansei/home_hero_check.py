"""Check the homepage's image-first introduction without opening a booking service."""
from pathlib import Path


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
        introduction = lead.inner_text().casefold()
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
        if viewport == 'mobile':
            if not photo.evaluate('''image => {
                const photo = image.getBoundingClientRect();
                const heading = document.querySelector('.home-first-impression h1').getBoundingClientRect();
                return photo.top < heading.top && photo.top < innerHeight / 2 && photo.height >= 180;
            }'''):
                raise AssertionError('Mobile introduction no longer leads with a prominent photograph')
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
        return 'Photograph, local service introduction, direct routes and accessible booking passed'
    finally:
        page.set_viewport_size(original_size)
        page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
