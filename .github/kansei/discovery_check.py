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
    assert block.count() == 1, 'Expected one concise discovery block'
    for href in DISCOVERY_PATHS[path]:
        link = block.locator(f'a[href="{href}"]')
        assert link.count() == 1 and link.is_visible(), 'Case route is missing or hidden'
        assert len(link.inner_text().strip()) > 12, 'Case route needs a descriptive label'
    block.scroll_into_view_if_needed()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2')
    block.screenshot(path=str(output / f'discovery-{path.strip("/").replace("/", "-") or "home"}-{label}.png'))
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
