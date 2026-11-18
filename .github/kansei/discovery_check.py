"""Exercise visible case routes, local information and reachable booking answers."""

DISCOVERY_PATHS = {
    '/': ('/ultraljud/kna/forkalkad-menisk/', '/ultraljud/bursit-axel/', '/ultraljud/glutealsenor/bilder/'),
    '/ultraljud/': ('/ultraljud/loparkna/', '/ultraljud/kalkaxel/', '/ultraljud/hoftled/bilder/'),
    '/ultraljud/kna/': ('/ultraljud/kna/forkalkad-menisk/', '/ultraljud/loparkna/', '/ultraljud/bakercysta/'),
    '/ultraljud/axel/': ('/ultraljud/bursit-axel/', '/ultraljud/axel/ac-ledsskada/', '/ultraljud/axel/pectoralisruptur/'),
    '/hyaluronsyra/kna/': ('/hyaluronsyra/ultraljudsvagledd-injektion/', '/hyaluronsyra/sinovial-sinogel/film/', '/hyaluronsyra/infor-och-efter/'),
    '/naprapati/': ('/blogg/ryggskott-forsta-48-timmarna/', '/blogg/nacksparr-vad-gor-jag-nu/', '/blogg/ont-i-axeln-nar-du-lyfter-armen/'),
    '/blogg/prp-eller-hyaluronsyra-vid-knaartros/': ('/hyaluronsyra/kna/', '/hyaluronsyra/ultraljudsvagledd-injektion/'),
    '/kunskapsbank/kna/svullet-kna/': ('/ultraljud/bakercysta/', '/ultraljud/kna/#bilder'),
}


def check_discovery(page, path, output, label):
    block = page.locator('.discovery-block')
    routes = DISCOVERY_PATHS[path]
    if path == '/' and page.locator('.home-symptoms').count():
        block = page.locator('.home-symptoms')
        routes = ('/blogg/ont-i-axeln-nar-du-lyfter-armen/', '/kunskapsbank/kna/ont-i-knat-i-trappor/',
                  '/blogg/domningar-i-handen-pa-natten/', '/hjalp-mig-boka/')
    elif path == '/' and page.locator('.home-case-preview').count():
        block = page.locator('.home-case-preview')
        routes = ('/ultraljud/kna/#artros',)
    elif path in ('/ultraljud/kna/', '/ultraljud/axel/') and page.locator('details.visit-more').count():
        # The patient example is visible early; complementary cases can be expanded.
        knee = path == '/ultraljud/kna/'
        featured = page.locator('#loparfall' if knee else '#bildexempel')
        example = '/ultraljud/loparkna/' if knee else '/ultraljud/kalkaxel/#patientfall'
        assert featured.locator(f'a[href="{example}"]').is_visible(), 'Featured case must be directly reachable'
        block = page.locator('#besvar' if knee else '#bildexempel')
        if knee:
            routes = tuple(href for href in routes if href != example)
        more = block.locator('details.visit-more')
        assert more.count() == 1 and not more.evaluate('node => node.open')
        more.locator('summary').focus()
        page.keyboard.press('Enter')
        assert more.evaluate('node => node.open'), 'Additional cases must open from the keyboard'
    assert block.count() == 1, 'Expected one concise discovery block'
    for href in routes:
        link = block.locator(f'a[href="{href}"]')
        assert link.count() == 1 and link.is_visible(), 'Case route is missing or hidden'
        assert len(link.inner_text().strip()) > 12, 'Case route needs a descriptive label'
    block.scroll_into_view_if_needed()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2')
    block.screenshot(path=str(output / f'discovery-{path.strip("/").replace("/", "-") or "home"}-{label}.png'),
                     style='.site-header {visibility:hidden}')
    opened = block.locator('details.visit-more[open]')
    if opened.count():
        opened.locator('summary').click()
    if path == '/naprapati/':
        local = page.locator('.discovery-local')
        assert 'Upplandsgatan 26' in local.inner_text()
        assert local.locator('a[href="/kontakt/"]').count() == 1
    if path in ('/ultraljud/kna/', '/ultraljud/axel/', '/hyaluronsyra/kna/', '/naprapati/'):
        question = page.locator('#faq details').last
        question.locator('summary').click()
        assert question.locator('p').is_visible(), 'New visit answer cannot be opened'
        question.locator('summary').click()
    page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
    page.wait_for_timeout(120)
    return 'Visible descriptive case routes, responsive layout and visit answers passed'
