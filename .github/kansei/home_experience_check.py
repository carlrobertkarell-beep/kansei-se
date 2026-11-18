"""Check the homepage decision paths, sourced patient voices, practitioner and film."""
import re
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect


def check_home_experience(page):
    hero = page.locator('.home-first-impression')
    reviews = page.locator('#omdomen')
    choices = page.locator('#vara-huvudtjanster')
    try:
        deny = page.locator('[data-statistics="no"]:visible')
        if deny.count():
            deny.click()
        ratings = hero.get_by_role('link', name=re.compile('Google'))
        expect(ratings).to_be_visible()
        dest = urlsplit(ratings.get_attribute('href'))
        assert dest.netloc == 'search.google.com' and dest.path == '/local/reviews'
        assert parse_qs(dest.query).get('placeid') == ['ChIJA_rM2cSdX0YRF0Qnxqujcuw']
        expect(hero.locator('a[href="#omdomen"]')).to_contain_text('Bokadirekt')
        assert reviews.evaluate("el => el.previousElementSibling.classList.contains('home-first-impression')")
        assert choices.evaluate("el => el.previousElementSibling.id === 'omdomen'")
        quotes = reviews.locator('figure:has(blockquote)')
        assert quotes.count() >= 2, 'Show patients speaking in their own words with both sources'
        expect(reviews.locator('blockquote:visible').first).to_be_visible()
        more = reviews.locator('details')
        more.locator('summary').focus()
        page.keyboard.press('Enter')
        sources = set()
        for quote in quotes.all():
            expect(quote.locator('blockquote')).to_be_visible()
            caption = quote.locator('figcaption')
            expect(caption).to_be_visible()
            if 'Google' in caption.inner_text():
                source = urlsplit(caption.get_by_role('link').get_attribute('href'))
                assert source.hostname == 'www.google.com' and source.path.startswith('/maps/reviews/')
                sources.add('Google')
            if 'Bokadirekt' in caption.inner_text():
                sources.add('Bokadirekt')
        assert sources == {'Google', 'Bokadirekt'}, 'Each review needs its actual source next to its quote'
        expect(reviews.get_by_role('link', name=re.compile('Bokadirekt'))).to_have_attribute(
            'href', 'https://www.bokadirekt.se/places/kansei-naprapati-rehabcenter-48847')
        more.locator('summary').click()
        expect(choices.locator('.home-visit')).to_have_count(3)
        service_links = choices.locator('.home-visit a[href]')
        links = service_links.evaluate_all('nodes => nodes.map(link => link.getAttribute("href"))')
        for suffix in ('-3263299', '-1946824', '-3409516'):
            assert any(link.startswith('https://www.bokadirekt.se/boka-tjanst/') and link.endswith(suffix)
                       for link in links), f'Preselected booking missing: {suffix}'
        for href in ('/naprapati/', '/ultraljud/', '/prp/'):
            assert href in links, f'Visit choices must link to {href}'
        normalized = ' '.join(choices.inner_text().split())
        assert '1 290 kr' in normalized and '890 kr' in normalized
        for link in service_links.all():
            if not link.is_visible():
                continue
            bounds = link.bounding_box()
            assert bounds and min(bounds['width'], bounds['height']) >= 44, 'Small visit-choice touch target'

        profile = page.locator('#arbetssatt')
        portrait = profile.locator('.home-human-avatar')
        expect(portrait).to_be_visible()
        portrait.scroll_into_view_if_needed()
        assert portrait.evaluate("""async img => {
            await img.decode();
            const box = img.getBoundingClientRect();
            return img.naturalWidth >= 700 && box.width >= Math.min(280, innerWidth * .82) && box.height >= 215;
        }"""), 'The named clinician needs a substantial, loaded portrait on mobile and desktop'
        assert 'carl-robert' in (portrait.get_attribute('alt') or '').lower()
        assert portrait.get_attribute('src') != hero.locator('.home-intro-image img').get_attribute('src')
        expect(profile.locator('a[href="/team/carl-robert-karell/"]')).to_be_visible()

        cover = page.locator('[data-home-film-play]')
        expect(cover).to_be_visible()
        expect(cover).to_have_attribute('href', '/hyaluronsyra/film/')
        player = page.locator('.home-hyaluron-film video')
        expect(player).to_be_hidden()
        poster = cover.locator('img')
        expect(poster).to_be_visible()
        assert poster.evaluate("async img => { await img.decode(); return img.naturalWidth > 0; }"), 'The educational film needs a usable poster'
        assert player.get_attribute('poster') == poster.get_attribute('src')
        assert player.get_attribute('controls') is not None
        assert player.locator('track[kind="captions"][srclang="sv"], track[kind="subtitles"][srclang="sv"]').count() >= 1
        if player.evaluate("video => !!video.canPlayType('video/mp4')"):
            cover.click()
            expect(player).to_be_visible()
            player.evaluate('video => video.pause()')
        symptoms = page.locator('#se-och-forsta')
        expect(symptoms.get_by_role('heading', level=2)).to_be_visible()
        expect(symptoms.locator('a[href="/hjalp-mig-boka/"]')).to_be_visible()
        return 'Patient choices, two sourced voices, large clinician portrait and captioned film passed'
    finally:
        page.evaluate("document.activeElement?.blur(); window.scrollTo({top:0,behavior:'instant'})")
