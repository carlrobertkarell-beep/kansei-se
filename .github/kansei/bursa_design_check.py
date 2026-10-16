"""Check the four-plane shoulder reader and actual film playback."""


def check_bursa(page, output, label):
    viewer = page.locator('[data-patient-viewer]')
    anatomy = viewer.locator('[data-patient-toggle]')
    findings = viewer.locator('[data-patient-findings]')
    if viewer.get_by_role('tab').count() != 5:
        raise AssertionError('Expected four still views and one film')
    for key in ('bursa-1', 'bursa-2', 'supraspinatus', 'subscapularis'):
        viewer.locator('#tab-' + key).click()
        picture = viewer.locator('#view-' + key + ' .patient-picture')
        page.wait_for_function("!document.querySelector('[data-patient-toggle]').disabled")
        if anatomy.get_attribute('aria-checked') == 'true':
            anatomy.click()
        if findings.get_attribute('aria-checked') == 'true':
            findings.click()
        picture.scroll_into_view_if_needed()
        page.wait_for_function("id=>{const i=document.querySelector('#view-'+id+' .original');return i.complete&&i.naturalWidth===1280&&i.naturalHeight===960}", arg=key)
        if label != 'compact' and key == 'bursa-1':
            viewer.screenshot(path=str(output / f'bursa-reader-{label}-original.png'), animations='disabled', style='body>header,body>a[href="#main"]{visibility:hidden!important}')
        findings.click()
        original_marks = picture.locator('[data-finding-mode=ultrasound]')
        if original_marks.get_attribute('aria-hidden') != 'false' or float(original_marks.evaluate('(e)=>getComputedStyle(e).opacity')) != 1:
            raise AssertionError('Original findings are not independently visible')
        anatomy.click()
        page.wait_for_function("id=>new DOMMatrix(getComputedStyle(document.querySelector('#view-'+id+' .anatomy-layer')).transform).isIdentity", arg=key)
        if findings.get_attribute('aria-checked') != 'true' or picture.locator('[data-finding-mode=anatomy]').get_attribute('aria-hidden') != 'false':
            raise AssertionError('Anatomy switch lost independent findings')
        if not picture.evaluate("""p=>{
            const b=p.getBoundingClientRect(), i=p.querySelector('.original').getBoundingClientRect(), a=p.querySelector('.anatomy-layer img').getBoundingClientRect(), f=p.querySelector('[data-finding-mode=anatomy]').getBoundingClientRect();
            return [i,a,f].every(r=>Math.abs(r.width-b.width)<1&&Math.abs(r.height-b.height)<1&&Math.abs(r.top-b.top)<1&&Math.abs(r.left-b.left)<1);
        }"""):
            raise AssertionError('Original, illustration and findings use different canvases')
        if label != 'compact':
            page.locator('#view-' + key).screenshot(path=str(output / f'bursa-{key}-{label}-anatomy-findings.png'), animations='disabled', style='body>header,body>a[href="#main"]{visibility:hidden!important}')
        findings.click()
        if anatomy.get_attribute('aria-checked') != 'true' or picture.locator('[data-finding-mode=anatomy]').get_attribute('aria-hidden') != 'true':
            raise AssertionError('Findings cannot be hidden without hiding anatomy')
    viewer.locator('#tab-film').click()
    if anatomy.is_visible() or findings.is_visible():
        raise AssertionError('Film exposes unusable image controls')
    video = viewer.locator('#view-film video')
    video.evaluate('(v)=>v.load()')
    page.wait_for_function("()=>{const v=document.querySelector('#view-film video');return v.readyState>=1&&v.videoWidth===1280&&v.videoHeight===960&&v.duration>3&&v.duration<3.3}", timeout=15000)
    video.evaluate('(v)=>v.play()')
    page.wait_for_function("document.querySelector('#view-film video').currentTime>0.1", timeout=15000)
    video.evaluate('(v)=>{v.pause();v.currentTime=2.8}')
    if label != 'compact':
        page.locator('#view-film').screenshot(path=str(output / f'bursa-film-{label}.png'), animations='disabled', style='body>header,body>a[href="#main"]{visibility:hidden!important}')
    viewer.locator('#tab-bursa-1').click()
    if not video.evaluate('(v)=>v.paused'):
        raise AssertionError('Hidden film continues playing')
    page.wait_for_function("!document.querySelector('[data-patient-toggle]').disabled")
    if anatomy.get_attribute('aria-checked') == 'true':
        anatomy.click()
    return 'Four originals, independent findings, registered illustration canvas, film playback and pause passed'
