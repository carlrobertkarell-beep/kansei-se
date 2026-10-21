"""Verify the public clinic model and every ultrasound reader without contacting booking services."""
CASE_PATHS = ('/ultraljud/axel/bicepstendinopati/', '/ultraljud/axel/pectoralisruptur/', '/ultraljud/hand-handled/karpaltunnelsyndrom/', '/ultraljud/axel/ac-ledsskada/', '/ultraljud/kalkaxel/', '/ultraljud/bursit-axel/')

def clinic_model(page):
    return page.evaluate("""()=>({
      font:getComputedStyle(document.querySelector('h1')).fontFamily,
      heading:getComputedStyle(document.querySelector('h1')).fontSize,
      header:document.querySelector('.header-inner').getBoundingClientRect().height,
      ink:getComputedStyle(document.body).getPropertyValue('--ink').trim(),
      paper:getComputedStyle(document.body).getPropertyValue('--paper').trim(),
      gutter:getComputedStyle(document.querySelector('.header-inner')).paddingLeft,
      heading_left:document.querySelector('h1').getBoundingClientRect().left
    })""")

def check_case(page, model):
    actual=clinic_model(page)
    for key in ('font','heading','header','ink','paper','gutter','heading_left'):
        if actual[key] != model[key]:
            raise AssertionError('Clinic design differs: '+key+' '+str(actual[key])+' vs '+str(model[key]))
    if page.locator('.condition-hero .case-visit').count():
        raise AssertionError('Duplicate introductory booking box')
    if page.locator('.case-page-nav').count()!=1 or page.locator('.case-page-nav a').first.get_attribute('href')!='#bilder':
        raise AssertionError('Missing direct path to the images')
    if page.locator('.reader-deep details').count():
        raise AssertionError('Clinical explanation requires nested disclosures')
    for link in page.locator('.case-page-nav a').all():
        if not page.locator(link.get_attribute('href')).count():
            raise AssertionError('Page navigation target missing')
    viewer=page.locator('.patient-viewer')
    switch=viewer.get_by_role('switch',name='Anatomi',exact=True)
    if switch.count()!=1:
        raise AssertionError('Expected one anatomy switch')
    initial_picture=viewer.locator('.patient-picture').first
    initial_picture.scroll_into_view_if_needed()
    switch.wait_for(state='visible')
    page.wait_for_function("!document.querySelector('.patient-viewer [role=switch]').disabled")
    if switch.get_attribute('aria-checked')!='false':
        raise AssertionError('Original image must be the first view')
    page.wait_for_function("[...document.querySelectorAll('.patient-picture')].filter(p=>p.getBoundingClientRect().height>0).every(p=>[...p.querySelectorAll('img')].every(i=>i.complete&&i.naturalWidth>0))")
    switch.click()
    page.wait_for_function("document.querySelector('.patient-viewer [role=switch]').getAttribute('aria-checked')==='true'")
    shown=page.evaluate("""()=>[...document.querySelectorAll('.patient-picture')].filter(p=>p.getBoundingClientRect().height>0).every(p=>{
      const layer=p.querySelector('.patient-overlay,.anatomy-layer');
      const style=getComputedStyle(layer);
      return layer.getAttribute('aria-hidden')==='false' && style.opacity!=='0' && (p.dataset.mode==='anatomy'||style.transform==='none'||new DOMMatrix(style.transform).isIdentity);
    })""")
    if not shown:
        raise AssertionError('Anatomy layer is not revealed')
    tabs=viewer.get_by_role('tab')
    for i in range(tabs.count()):
        tab=tabs.nth(i);tab.click()
        target=page.locator('#'+tab.get_attribute('aria-controls'))
        if not target.is_visible():
            raise AssertionError('Selected image panel not visible')
        if target.locator('.patient-overlay,.anatomy-layer').count():
            page.wait_for_function("!document.querySelector('.patient-viewer [role=switch]').disabled")
            if switch.get_attribute('aria-checked')!='true':
                raise AssertionError('Anatomy choice lost while changing views')
        elif switch.is_visible():
            raise AssertionError('Film exposes an unusable anatomy switch')
    if tabs.count():
        tabs.first.click()
        page.wait_for_function("!document.querySelector('.patient-viewer [role=switch]').disabled")
        tabs.first.focus();page.keyboard.press('ArrowLeft')
        if tabs.last.get_attribute('aria-selected')!='true':
            raise AssertionError('Keyboard view navigation does not wrap')
        tabs.first.click()
        page.wait_for_function("!document.querySelector('.patient-viewer [role=switch]').disabled")
    switch.click()
    if switch.get_attribute('aria-checked')!='false':
        raise AssertionError('Original image cannot be restored')
    for control in viewer.locator('button').all():
        if control.is_visible() and control.bounding_box()['height']<44:
            raise AssertionError('Reader control is too small for touch')
    return {'model':actual,'views':tabs.count(),'reader':'Original, anatomy, every view and keyboard navigation passed'}

def check_hub(page, model):
    if clinic_model(page)!=model:
        raise AssertionError('Ultrasound hub diverges from clinic model')
    search=page.locator('#ultrasound-search')
    search.scroll_into_view_if_needed()
    clear=page.locator('#clear-ultrasound-search')
    if clear.is_visible():raise AssertionError('Empty search displays an unnecessary clear action')
    search.fill('knä')
    if not clear.is_visible():raise AssertionError('Search cannot be cleared')
    if not page.locator('.hub-region[href="/ultraljud/kna/"]').is_visible():raise AssertionError('Swedish search failed')
    clear.click()
    if search.input_value() or clear.is_visible():raise AssertionError('Search reset failed')
    if page.locator('.hub-faq-section > h3').count()!=1 or page.locator('.hub-faq-list').locator('xpath=ancestor::details').count():
        raise AssertionError('FAQ requires an extra opening step')
    gateway=page.locator('#undersokningsfall')
    if gateway.locator('.hub-case').count():raise AssertionError('Service page repeats the full image catalogue')
    if gateway.locator('a[href="/ultraljud/bilder/"]').count()!=1:raise AssertionError('Image overview entrance missing')
    if gateway.locator('.atlas-area-links a').count()!=6:raise AssertionError('Body-region shortcuts missing')
    check_sample(page)
    return {'model':model,'search_and_faq':'Passed'}

def check_sample(page):
    sample=page.locator('[data-atlas-demo]')
    sample.scroll_into_view_if_needed()
    anatomy=sample.get_by_role('switch',name='Anatomi',exact=True)
    findings=sample.get_by_role('switch',name='Visa fynden',exact=True)
    page.wait_for_function("!document.querySelector('[data-atlas-anatomy]').disabled")
    if anatomy.get_attribute('aria-checked')!='true':raise AssertionError('Anatomy preview is not discoverable')
    anatomy.click();findings.click()
    if sample.get_attribute('data-anatomy')!='false' or sample.get_attribute('data-findings')!='true':
        raise AssertionError('Preview findings cannot be shown on the original')
    anatomy.click()
    if sample.get_attribute('data-findings')!='true':raise AssertionError('Preview loses independent finding selection')
    findings.click()

def check_explore(page):
    check_sample(page)
    entries=page.locator('[data-atlas-entry]')
    expected={'/ultraljud/kalkaxel/','/ultraljud/axel/bicepstendinopati/','/ultraljud/axel/pectoralisruptur/','/ultraljud/axel/ac-ledsskada/','/ultraljud/hand-handled/karpaltunnelsyndrom/','/ultraljud/loparkna/','/ultraljud/tennisarmbage/bilder/','/ultraljud/kna/','/ultraljud/halsena/bilder/','/ultraljud/bursit-axel/','/ultraljud/glutealsenor/bilder/'}
    expected.add('/ultraljud/hoftled/bilder/')
    if set(entries.locator('[data-atlas-case]').evaluate_all('(els)=>els.map(e=>e.getAttribute("href"))'))!=expected:
        raise AssertionError('A published image reader is missing or duplicated')
    if set(entries.locator('.atlas-image-shortcut').evaluate_all('(els)=>els.map(e=>e.getAttribute("href").replace(/#bilder$/,""))'))!=expected:
        raise AssertionError('Whole-case links must retain separate image shortcuts')
    search=page.locator('[data-atlas-search]')
    page.locator('[data-atlas-region=kna]').click()
    if entries.evaluate_all('(els)=>els.filter(e=>!e.hidden).length')!=2:
        raise AssertionError('Knee region does not isolate its examples')
    if 'omrade=kna' not in page.url:raise AssertionError('Region choice has no shareable URL')
    search.fill('domningar')
    if not page.locator('[data-atlas-empty]').is_visible():raise AssertionError('Empty region search has no recovery')
    page.locator('[data-atlas-reset]').click()
    if entries.evaluate_all('(els)=>els.filter(e=>!e.hidden).length')!=len(expected) or search.input_value():
        raise AssertionError('Reset does not restore every example')
    search.fill('loparkna')
    if entries.evaluate_all('(els)=>els.filter(e=>!e.hidden).length')!=1:
        raise AssertionError('Swedish search without diacritics failed')
    search.fill('')
    page.locator('[data-atlas-region=hand]').click()
    page.reload(wait_until='domcontentloaded')
    if page.locator('[data-atlas-entry]:not([hidden])').count()!=1:
        raise AssertionError('Direct region URL does not survive reload')
    page.locator('[data-atlas-region=fot]').click()
    if page.locator('[data-atlas-entry]:not([hidden])').count()!=1:raise AssertionError('Foot region missing')
    page.locator('[data-atlas-region=alla]').click()
    for phrase, expected_path in (
        ('min hand somnar på natten','/ultraljud/hand-handled/karpaltunnelsyndrom/'),
        ('ont när jag springer på utsidan av knät','/ultraljud/loparkna/'),
        ('knät svullnar efter promenader','/ultraljud/kna/'),
        ('hyaluronsyra',('/ultraljud/hoftled/bilder/','/ultraljud/kna/')),
        ('Sinogel','/ultraljud/hoftled/bilder/'),
    ):
        search.fill(phrase)
        visible=entries.locator('[data-atlas-case]').evaluate_all('(els)=>els.filter(e=>!e.closest("[data-atlas-entry]").hidden).map(e=>e.getAttribute("href"))')
        expected_matches = {expected_path} if isinstance(expected_path,str) else set(expected_path)
        if set(visible)!=expected_matches:raise AssertionError('Natural-language case search failed: '+phrase+' '+str(visible))
    search.fill('ont när jag lyfter armen')
    if not page.locator('[data-atlas-entry]:not([hidden]) a[href="/ultraljud/bursit-axel/"]').count():
        raise AssertionError('Lifting complaint does not find the shoulder bursa case')
    search.fill('')
    page.locator('[data-atlas-symptom=natt]').click()
    if 'besvar=natt' not in page.url:raise AssertionError('Symptom filter has no shareable URL')
    page.reload(wait_until='domcontentloaded')
    if page.locator('[data-atlas-symptom=natt]').get_attribute('aria-current')!='true':raise AssertionError('Direct symptom URL does not survive reload')
    if entries.evaluate_all('(els)=>els.filter(e=>!e.hidden).length')!=3:raise AssertionError('Sleep filter must include shoulder and hand examples')
    page.locator('[data-atlas-symptom=alla]').click()
    return 'Whole cases, image shortcuts, area/symptom URLs, natural-language search, empty-state recovery and independent preview layers passed'
