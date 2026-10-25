"""Browser checks for symptom discovery and distinct, existing booking services."""
from pathlib import Path

GUIDE = '/kunskapsbank/kna/ont-pa-utsidan-av-knat/'
ULTRASOUND = 'https://www.bokadirekt.se/boka-tjanst/kansei-naprapati-rehabcenter-48847/muskuloskeletalt-ultraljud-1946824'
CLINICAL = 'https://www.bokadirekt.se/boka-tjanst/kansei-rehabcenter-48847/naprapati-ny-resp-aterbesok-3263299'
REGIONS = tuple('/ultraljud/' + key + '/' for key in (
    'axel', 'armbage', 'hand-handled', 'hoft-ljumske', 'fot-fotled',
    'overarm', 'underarm', 'lar-muskulatur', 'underben'))
SEARCH_PATHS = REGIONS + ('/ultraljud/', '/ultraljud/kna/', '/ultraljud/bilder/', GUIDE)


def check_search_paths(page, path: str, output: Path, label: str):
    if path in REGIONS:
        links = page.locator('.us-symptom-links a')
        assert links.count() == 3, 'Regional symptoms need three contextual routes'
        assert all(link.get_attribute('href').startswith('/') for link in links.all())
        if path != '/ultraljud/axel/':
            booking = page.locator('#boka-ultraljud')
            assert booking.locator('a[data-measure="booking_click"]').get_attribute('href') == ULTRASOUND
            assert '1 290 kr' in booking.inner_text() and '45 minuter' in booking.inner_text()
            booking.screenshot(path=str(output / f'search-booking-{path.strip("/").replace("/", "-")}-{label}.png'))
        if path in tuple('/ultraljud/' + key + '/' for key in ('overarm', 'underarm', 'lar-muskulatur', 'underben')):
            faq = page.locator('#faq details').first
            faq.locator('summary').click()
            assert faq.locator('p').is_visible(), 'New FAQ answer is not reachable'
            faq.locator('summary').click()
    elif path == '/ultraljud/':
        search = page.locator('#ultrasound-search')
        search.fill('ont utsida knä')
        found = page.locator('.hub-directory-link[href="' + GUIDE + '"]')
        found.wait_for(state='visible', timeout=5000)
        assert page.locator('.hub-directory-link:visible').count() == 1, 'Symptom query does not isolate the relevant route'
        found.screenshot(path=str(output / f'search-symptom-match-{label}.png'))
        page.locator('#clear-ultrasound-search').click()
        assert not search.input_value(), 'Symptom search cannot be cleared'
    elif path == '/ultraljud/kna/':
        assert page.locator('.knee-symptoms a[href="' + GUIDE + '"]').count() == 1
    elif path == '/ultraljud/bilder/':
        assert page.locator('.atlas-actions a[data-measure="booking_click"]').get_attribute('href') == ULTRASOUND
        assert '1 290 kr' in page.locator('.atlas-booking-note').inner_text()
    elif path == GUIDE:
        choices = page.locator('.us-guide-choice')
        assert choices.count() == 2, 'Clinical assessment and ultrasound choices must remain distinct'
        assert choices.nth(0).locator('a[data-measure="booking_click"]').get_attribute('href') == CLINICAL
        assert choices.nth(1).locator('a[data-measure="booking_click"]').get_attribute('href') == ULTRASOUND
        assert '890 kr' in choices.nth(0).inner_text() and '1 290 kr' in choices.nth(1).inner_text()
        assert page.locator('a[href="/ultraljud/loparkna/#bilder"]').count() == 1
        page.screenshot(path=str(output / f'lateral-knee-guide-top-{label}.png'))
        page.locator('.article-cta a[href="#valj-besok"]').click()
        assert page.url.endswith('#valj-besok'), 'Guide cannot reach its booking choices'
        page.locator('#valj-besok').screenshot(path=str(output / f'lateral-knee-guide-booking-{label}.png'))
        page.locator('#faq summary').first.click()
        assert page.locator('#faq details').first.locator('p').is_visible()
        page.evaluate("history.replaceState(null,'',location.pathname+location.search)")
    # Every check may scroll to a control; later checks must see a fresh intro.
    page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
    page.wait_for_timeout(120)
    return 'Symptom routes, existing service destinations, prices and reachable answers passed; no booking submitted'
