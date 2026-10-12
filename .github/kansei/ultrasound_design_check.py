"""Verify the public clinic model and every ultrasound reader without contacting booking services."""
CASE_PATHS = ('/ultraljud/axel/bicepstendinopati/', '/ultraljud/axel/pectoralisruptur/', '/ultraljud/hand-handled/karpaltunnelsyndrom/', '/ultraljud/axel/ac-ledsskada/', '/ultraljud/kalkaxel/')

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
    if page.locator('.hub-case').count()!=5:raise AssertionError('A published case is missing')
    return {'model':model,'search_and_faq':'Passed'}
