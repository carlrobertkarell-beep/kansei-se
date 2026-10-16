"""Check the four-plane shoulder reader and actual film playback."""


def check_bursa(page, output, label):
    viewer = page.locator('[data-patient-viewer]')
    anatomy = viewer.locator('[data-patient-toggle]')
    findings = viewer.locator('[data-patient-findings]')
    if viewer.get_by_role('tab').count() != 5:
        raise AssertionError('Expected four still views and one film')
    samples = {}
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
        image = picture.locator('.anatomy-layer img')
        if not image.get_attribute('src').endswith('.anatomi.20261016e.webp'):
            raise AssertionError('Every view must have a painted, contour-aligned anatomy layer')
        points = {
            'bursa-1': [(700, 370), (700, 250)],
            'bursa-2': [(80, 650), (250, 650)],
            'supraspinatus': [(800, 325), (800, 242), (778, 515), (835, 502)],
            'subscapularis': [(500, 650), (755, 680), (180, 430), (1100, 680)],
        }[key]
        rgb = image.evaluate("""(image,points)=>{
            const c=document.createElement('canvas');c.width=1280;c.height=960;
            const ctx=c.getContext('2d');ctx.drawImage(image,0,0,1280,960);
            return points.map(([x,y])=>{
                const p=ctx.getImageData(x-5,y-5,11,11).data,s=[0,0,0,0];
                for(let i=0;i<p.length;i++)s[i%4]+=p[i];
                return s.map(v=>v/121);
            });
        }""", points)
        samples[key] = rgb
        def muscle(p): return p[0] > p[1]*1.25 and p[1] < 160 and p[3] > 240
        def fat(p): return p[1] > 95 and p[0] > p[1]*1.1 and p[1] > p[2]*1.12
        def bone(p): return p[0] > p[1]*1.18 and p[2] < p[1]*.82
        if key == 'bursa-1' and not (muscle(rgb[0]) and fat(rgb[1])):
            raise AssertionError('View 1 deltoid/fat material crosses the clinician borders')
        if key == 'bursa-2' and not (muscle(rgb[0]) and rgb[1][1] > rgb[1][0]*1.2):
            raise AssertionError('View 2 must continue deltoid along the left side, outside the bursa')
        # Coarse palette guards sample tissue interiors, not the antialiased
        # cortical boundary. Visual comparison to the clinician guide remains
        # necessary; these samples cannot prove clinical geometry or fiber style.
        if key == 'supraspinatus' and not (muscle(rgb[0]) and fat(rgb[1]) and bone(rgb[2]) and rgb[3][2] > rgb[3][1]*.79):
            raise AssertionError('View 3 deltoid or uneven humeral cortical contour is mispainted')
        if key == 'subscapularis' and not (bone(rgb[0]) and rgb[1][2]/rgb[1][1] > rgb[0][2]/rgb[0][1]+.08 and rgb[1][3] > 240):
            raise AssertionError('View 4 must separate humerus from the residual-fiber defect')
        if key == 'subscapularis' and not all(p[3] > 240 and p[0] > p[2]*1.25 for p in rgb[2:]):
            raise AssertionError('View 4 has unpainted tissue around the stump or below the fluid pocket')
        if picture.locator('[data-finding-mode=anatomy] path:not(.finding-pointer):not(.finding-pointer-shadow)').count():
            raise AssertionError('Findings must use the shared pointers, without colored tissue outlines')
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
    if viewer.locator('.bursa-legend').count():
        raise AssertionError('The shared reader has no separate tissue color legend')
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
    return {'reader': 'Four originals, painted anatomy, independent findings, film and pause passed', 'clinical_material_samples': samples}
