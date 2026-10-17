"""Check section orientation without leaving the page or clicking booking links."""
TARGETS={
 '/ultraljud/':'in-3',
 '/ultraljud/axel/':'undersokning',
 '/ultraljud/kna/':'artros',
 '/ultraljud/kalkaxel/':'patientfall',
 '/hyaluronsyra/':'in-7',
 '/hyaluronsyra/kna/':'pris',
}

def check_reading(page,path,output,label):
    sections=page.locator('[data-reading-section]')
    bar=page.locator('.reading-position')
    assert bar.count()==1 and sections.count()>=3
    assert not bar.is_visible(), 'Reading position covers the introduction'
    assert page.locator('.reading-chapter-number').count()==sections.count()
    ids=sections.evaluate_all('(els)=>els.map(el=>el.id)')
    sections.nth(1).evaluate('el=>el.scrollIntoView({block:"start"})')
    page.wait_for_function("document.querySelector('.reading-position-current').textContent.startsWith('2 / ')")
    assert bar.is_visible()
    summary=bar.locator('summary')
    summary.click()
    assert bar.get_attribute('open') is not None
    links=bar.locator('nav a')
    assert links.count()==sections.count()
    assert bar.locator('a[aria-current="location"]').count()==1
    page.screenshot(path=str(output/f'reading-menu-{path.strip("/").replace("/","-")}-{label}.png'),animations='disabled')
    page.keyboard.press('Escape')
    assert bar.get_attribute('open') is None
    assert summary.evaluate('el=>el===document.activeElement')
    summary.click()
    target=TARGETS[path]
    bar.locator(f'nav a[href="#{target}"]').click()
    page.wait_for_function("id=>location.hash==='#'+id",arg=target)
    position=ids.index(target)+1
    page.wait_for_function("n=>document.querySelector('.reading-position-current').textContent.startsWith(n+' / ')",arg=position)
    assert bar.get_attribute('open') is None
    heading=page.locator('#'+target).locator('h2').first
    assert heading.evaluate('el=>el===document.activeElement')
    header_bottom=page.locator('.site-header').bounding_box()['y']+page.locator('.site-header').bounding_box()['height']
    bar_box=bar.bounding_box()
    assert bar_box and bar_box['y']>=header_bottom-1
    assert heading.bounding_box()['y']>=bar_box['y']+bar_box['height']-1, 'Chapter heading is covered'
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
    page.screenshot(path=str(output/f'reading-section-{path.strip("/").replace("/","-")}-{label}.png'),animations='disabled')
    # Leave every later page test at the beginning, as on a fresh load.
    page.goto(page.url.split('#')[0],wait_until='domcontentloaded')
    page.wait_for_timeout(120)
    return {'chapters':len(ids),'active_location':'Passed','keyboard_and_anchor_clearance':'Passed'}
