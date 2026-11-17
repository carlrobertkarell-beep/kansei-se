"""Check the homepage's symptom routes, booking help and responsive layout."""
from playwright.sync_api import expect


def check_home_experience(page):
    section = page.locator('.home-symptoms')
    if not section.count() and page.url.startswith('https://www.kansei.se/'):
        previous = page.locator('.home-case-preview')
        expect(previous.get_by_role('link', name='Se patientfallet')).to_have_attribute('href', '/ultraljud/kna/#artros')
        return 'Previous live homepage case still served during publication'

    try:
        rating = page.locator('.home-intro-reviews')
        if rating.count():
            expect(rating).to_have_attribute('href', '#omdomen')
            reviews = page.locator('#omdomen')
            assert reviews.evaluate("element => element.previousElementSibling.id === 'vara-huvudtjanster'")
            quotes = reviews.locator('blockquote')
            expect(quotes).to_have_count(3)
            for quote in quotes.all():
                expect(quote).to_be_visible()
            expect(reviews.locator('.hr-footer a')).to_have_attribute(
                'href', 'https://www.bokadirekt.se/places/kansei-naprapati-rehabcenter-48847')
            avatar = page.locator('.home-human-avatar')
            expect(avatar).to_be_visible()
            assert avatar.bounding_box()['width'] <= 96, 'Practitioner portrait must remain compact'
            expect(page.locator('.home-hyaluron-film video')).to_have_attribute(
                'poster', '/bilder/filmer/kansei-hyaluron-behandlingsrum.20261108.webp')

        expect(section.get_by_role('heading', level=2)).to_be_visible()
        expect(section.locator('.home-symptoms-list').get_by_role('link')).to_have_count(3)
        booking = section.get_by_role('link', name='Hjälp mig välja besök', exact=True)
        expect(booking).to_have_attribute('href', '/hjalp-mig-boka/')
        expect(section.get_by_role('link')).to_have_count(4)
        image = section.get_by_role('img')
        image.scroll_into_view_if_needed()
        page.wait_for_function(
            "img => img.complete && img.naturalWidth > 0",
            arg=image.element_handle(), timeout=15000)
        if page.viewport_size['width'] <= 860:
            assert section.evaluate("""section => {
                const heading = section.querySelector('h2').getBoundingClientRect();
                const photo = section.querySelector('.home-symptoms-photo').getBoundingClientRect();
                const booking = section.querySelector('.home-symptoms-booking').getBoundingClientRect();
                return heading.bottom < booking.top && booking.bottom < photo.top &&
                    Math.abs(photo.left - heading.left) <= 1 &&
                    Math.abs(photo.right - booking.right) <= 1 &&
                    [...section.querySelectorAll('a')].every(link => link.getBoundingClientRect().height >= 44);
            }"""), 'Symptom links and booking help must precede the image and fit the mobile layout'
        return 'Symptom links, booking help, clinic photo and mobile layout passed'
    finally:
        page.evaluate("document.activeElement?.blur(); window.scrollTo({top:0,behavior:'instant'})")
        page.wait_for_function('window.scrollY === 0')
