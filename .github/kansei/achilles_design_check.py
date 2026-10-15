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
    return 'Three registered stills, independent overlays, healthy labels, enlargement, native film playback/pause and keyboard navigation passed'
