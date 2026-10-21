"""Exercise the Achilles reader, including its still/film boundary."""
def check_achilles(page, output, label):
    viewer=page.locator('[data-achilles-viewer]')
    tabs=viewer.get_by_role('tab')
    anatomy=viewer.locator('[data-knee-anatomy]')
    findings=viewer.locator('[data-knee-findings]')
    if tabs.count()!=4:raise AssertionError('Achilles views are missing')
    page.wait_for_function("[...document.querySelectorAll('[data-achilles-viewer] .knee-anatomy img')].every(i=>i.complete&&i.naturalWidth===1280&&i.naturalHeight===960)")
    page.wait_for_function("!document.querySelector('[data-achilles-viewer] [data-knee-anatomy]').disabled")
    if anatomy.get_attribute('aria-checked')!='false':raise AssertionError('Achilles must open with original ultrasound')
    revised=viewer.locator('#view-longitudinal .knee-findings').evaluate("""svg=>{
        const tendon=svg.querySelector('.tendon-outline');
        return [[1040,220],[900,250],[915,325]].every(([x,y])=>tendon.isPointInFill(new DOMPoint(x,y))) && !svg.querySelector('.vascular-path,.vascular-shadow') && svg.querySelectorAll('.rupture-outline').length>=6 && !!svg.querySelector('.advanced-tendinosis');
    }""")
    if not revised:raise AssertionError('Revised tissue pathology or guidance missing; copied vessel-guide strokes must be absent')
    # The transverse boundary must enclose the central tendon continuously.
    # Two mistaken y-values once cut a deep notch through this intact region.
    # Native SVG hit testing needs a rendered panel; hidden paths have no fill.
    viewer.locator('#tab-transverse').click()
    if not viewer.locator('#view-transverse').is_visible():raise AssertionError('Transverse Achilles panel did not open for contour inspection')
    transverse_continuous=viewer.locator('#view-transverse .tendon-outline').evaluate("""path=>{
        return [[520,200],[520,300],[520,420],[700,250]].every(([x,y])=>path.isPointInFill(new DOMPoint(x,y))) && !path.isPointInFill(new DOMPoint(520,130));
    }""")
    if not transverse_continuous:raise AssertionError('Transverse Achilles contour cuts through the tendon interior')
    viewer.locator('#tab-longitudinal').click()
    if anatomy.get_attribute('aria-checked')!='false' or findings.get_attribute('aria-checked')!='false':raise AssertionError('Contour inspection changed the initial overlay selections')

    anatomy.click()
    picture=viewer.locator('#view-longitudinal .knee-picture')
    picture.scroll_into_view_if_needed()
    page.wait_for_function("new DOMMatrix(getComputedStyle(document.querySelector('#view-longitudinal .knee-anatomy')).transform).isIdentity")
    if picture.get_attribute('data-findings')!='false':raise AssertionError('Anatomy-only inspection unexpectedly shows finding graphics')
    red_pixels=picture.locator('.knee-anatomy img').evaluate("""img=>{
        const c=document.createElement('canvas');c.width=1280;c.height=960;const ctx=c.getContext('2d');ctx.drawImage(img,0,0);
        const a=ctx.getImageData(160,220,670,120).data;let count=0;
        for(let i=0;i<a.length;i+=4){const r=a[i],g=a[i+1],b=a[i+2];if(r>g*1.75&&b>g*.82&&r-g>60&&r-b>20)count++}return count;
    }""")
    if red_pixels<500:raise AssertionError('Vessels are missing from the anatomy bitmap when finding graphics are off')
    page.screenshot(path=str(output/f'achilles-{label}-anatomy-only.png'))
    findings.click()
    for key in ('longitudinal','healthy','transverse'):
        viewer.locator('#tab-'+key).click()
        picture=viewer.locator('#view-'+key+' .knee-picture')
        picture.scroll_into_view_if_needed()
        page.wait_for_function("key=>new DOMMatrix(getComputedStyle(document.querySelector('#view-'+key+' .knee-anatomy')).transform).isIdentity",arg=key)
        if picture.get_attribute('data-anatomy')!='true' or picture.get_attribute('data-findings')!='true':raise AssertionError('Achilles loses overlay selections between stills')
        if findings.inner_text().strip()!=('Visa senan' if key=='healthy' else 'Visa fynden'):raise AssertionError('Healthy tendon is described as pathology')
        registered=picture.evaluate("""p=>{const a=p.getBoundingClientRect();return ['.knee-original','.knee-anatomy img','.knee-findings'].every(s=>{const b=p.querySelector(s).getBoundingClientRect();return Math.abs(b.width-a.width)<.2&&Math.abs(b.height-a.height)<.2&&Math.abs(b.top-a.top)<.2})}""")
        if not registered:raise AssertionError('Achilles image coordinate frames differ')
        page.screenshot(path=str(output/f'achilles-{label}-{key}.png'))
    viewer.locator('[data-knee-enlarge]').click()
    if not page.locator('#knee-zoom').is_visible():raise AssertionError('Achilles enlargement failed')
    page.locator('[data-knee-zoom-findings]').click()
    if findings.get_attribute('aria-checked')!='false':raise AssertionError('Enlarged Achilles controls are not synchronized')
    page.keyboard.press('Escape')
    viewer.locator('#tab-doppler').click()
    if viewer.locator('[data-achilles-controls]').is_visible():raise AssertionError('Film displays unusable anatomy controls')
    video=viewer.locator('video')
    video.evaluate("v=>v.play()")
    page.wait_for_function("document.querySelector('[data-achilles-viewer] video').currentTime>0")
    page.screenshot(path=str(output/f'achilles-{label}-doppler.png'))
    tabs.first.click()
    if not video.evaluate('v=>v.paused'):raise AssertionError('Hidden Achilles film keeps playing')
    if anatomy.get_attribute('aria-checked')!='true':raise AssertionError('Anatomy choice lost after movie')
    tabs.first.focus();page.keyboard.press('ArrowLeft')
    if tabs.last.get_attribute('aria-selected')!='true':raise AssertionError('Achilles keyboard tabs fail to wrap')
    for button in viewer.locator('button').all():
        if button.is_visible() and button.bounding_box()['height']<44:raise AssertionError('Achilles touch control is too small')
    # Inspect the reading and booking sections as well as the image viewer.
    # Missing shared case styles previously left these sections touching.
    layout=page.evaluate("""()=>{
        const sections=[...document.querySelectorAll('main>section.section')];
        const sized=sections.every(el=>{const s=getComputedStyle(el);return parseFloat(s.paddingTop)>=32&&parseFloat(s.paddingBottom)>=32});
        const headings=sections.flatMap(el=>[...el.querySelectorAll('h2')]);
        const type=headings.every(el=>parseFloat(getComputedStyle(el).fontSize)<=40);
        const links=[...document.querySelectorAll('.achilles-actions>a')].map(el=>el.getBoundingClientRect());
        const [a,b]=links;
        const separated=links.length===2&&(b.left-a.right>=8||b.top-a.bottom>=8);
        const faq=[...document.querySelectorAll('.knee-faq summary')].every(el=>el.getBoundingClientRect().height>=56);
        return {sized,type,separated,faq};
    }""")
    if not all(layout.values()):raise AssertionError('Achilles reading layout is cramped: '+str(layout))
    for link in page.locator('.case-page-nav a').all():
        if not page.locator(link.get_attribute('href')).count() or link.bounding_box()['height']<44:
            raise AssertionError('Achilles page navigation is missing or too small')
    page.locator('#besok').evaluate('el=>el.scrollIntoView()')
    page.screenshot(path=str(output/f'achilles-{label}-visit.png'))
    page.locator('#besok .cta').screenshot(path=str(output/f'achilles-{label}-booking.png'))
    first=page.locator('.knee-faq details').first
    first.locator('summary').focus();page.keyboard.press('Enter')
    if first.get_attribute('open') is None or not first.locator('p').is_visible():
        raise AssertionError('Achilles FAQ cannot be opened with the keyboard')
    page.locator('#faq').evaluate('el=>el.scrollIntoView()')
    page.screenshot(path=str(output/f'achilles-{label}-faq.png'))
    first.locator('summary').focus();page.keyboard.press('Enter')
    if first.get_attribute('open') is not None:raise AssertionError('Achilles FAQ cannot be closed')
    page.locator('#kallor').evaluate('el=>el.scrollIntoView()')
    page.screenshot(path=str(output/f'achilles-{label}-sources.png'))
    return 'Three registered stills, independent overlays, enlargement, native film, keyboard navigation, section spacing, booking actions and accessible FAQ passed'
