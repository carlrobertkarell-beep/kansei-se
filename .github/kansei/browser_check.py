#!/usr/bin/env python3
"""Read-only browser smoke checks. Never clicks booking links or submits forms."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from achilles_design_check import check_achilles
from ultrasound_design_check import CASE_PATHS, clinic_model, check_case, check_hub, check_explore, check_sample
from case_story_check import STORY_PATHS, check_story
from bursa_design_check import check_bursa
from case_context_check import CONTEXT_PATHS, check_context
from reading_check import TARGETS as READING_PATHS, check_reading
from film_caption_check import FILM_PATHS, check_film_captions

PATHS = ("/", "/injektioner/", "/blogg/prp-eller-hyaluronsyra-vid-knaartros/", "/blogg/hyaluronsyra-vid-artros-vad-sager-evidensen/", "/kunskapsbank/kna/svullet-kna/", "/kunskapsbank/axel/ont-i-axeln-pa-natten/", "/ultraljud/svullet-kna/", "/ultraljud/quadricepssena/", "/ultraljud/bursit-axel/", "/hyaluronsyra/", "/hyaluronsyra/sinovial-sinogel/", "/prp/", "/hyaluronsyra/kna/", "/hyaluronsyra/hoft/", "/hyaluronsyra/axel/", "/hyaluronsyra/infor-och-efter/", "/hjalp-mig-boka/", "/naprapati/", "/ultraljud/", "/ultraljud/axel/", "/ultraljud/kalkaxel/", "/ultraljud/kna/", "/ultraljud/fot-fotled/", "/kontakt/", "/priser/", "/om-oss/", "/reda/", "/reda-rehab/")
KNOWLEDGE_PATHS = ("/kunskapsbank/", "/blogg/knaartros-vad-du-kan-gora/", "/blogg/forsta-besoket-hos-naprapat/", "/blogg/normalt-ultraljud-men-fortfarande-ont/", "/blogg/misstankt-halseneruptur/", "/blogg/domningar-i-handen-pa-natten/")
RUNNER_PATH = "/ultraljud/loparkna/"
ACHILLES_PATH = "/ultraljud/halsena/bilder/"
ELBOW_PATH = "/ultraljud/tennisarmbage/bilder/"
EXPLORE_PATH = "/ultraljud/bilder/"
SIZES = (("mobile", 390, 844), ("desktop", 1440, 1000), ("compact", 320, 780))


def check(base, output):
    parsed = urlsplit(base)
    if base not in ("https://www.kansei.se", "http://127.0.0.1:4173", "http://127.0.0.1:4174"):
        raise ValueError("Unapproved test origin")
    baseline_only = base == "http://127.0.0.1:4174"
    output.mkdir(parents=True, exist_ok=True)
    records, errors = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for label, width, height in SIZES:
            context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce", locale="sv-SE")
            def route(req):
                host = urlsplit(req.request.url).hostname or ""
                if host == parsed.hostname or host in ("fonts.googleapis.com", "fonts.gstatic.com"):
                    req.continue_()
                else:
                    req.abort()
            context.route("**/*", route)
            paths = tuple(dict.fromkeys(PATHS + FILM_PATHS + CASE_PATHS + (() if baseline_only else KNOWLEDGE_PATHS + (RUNNER_PATH, ELBOW_PATH, ACHILLES_PATH, EXPLORE_PATH))))
            if label == 'compact':
                paths = ('/', '/ultraljud/', '/ultraljud/axel/', '/hyaluronsyra/', '/injektioner/', '/hyaluronsyra/kna/', '/hyaluronsyra/hoft/', '/hyaluronsyra/axel/', '/blogg/prp-eller-hyaluronsyra-vid-knaartros/', '/blogg/hyaluronsyra-vid-artros-vad-sager-evidensen/') + FILM_PATHS[1:] + CASE_PATHS + (() if baseline_only else (RUNNER_PATH, ELBOW_PATH, ACHILLES_PATH, EXPLORE_PATH))
            model = None
            for path in paths:
                page = context.new_page()
                js_errors = []
                page.on("pageerror", lambda err: js_errors.append(str(err)[:180]))
                row = {"path": path, "viewport": label, "errors": []}
                try:
                    response = page.goto(base + path, wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(800)
                    page.add_style_tag(content="*,*::before,*::after{animation-duration:0s!important;transition-duration:0s!important;scroll-behavior:auto!important}")
                    if response is None or response.status != 200:
                        row["errors"].append("Page does not return HTTP 200")
                    if page.locator("h1").count() != 1:
                        row["errors"].append("Expected one H1")
                    if not page.title().strip():
                        row["errors"].append("Title missing")
                    dimensions = page.evaluate("({width:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})")
                    row["overflow_px"] = max(0, dimensions["scroll"] - dimensions["width"])
                    if row["overflow_px"] > 3:
                        row["errors"].append("Horizontal overflow")
                    bookings = page.locator('a[href*="bokadirekt.se/"]')
                    row["booking_links"] = bookings.count()
                    if path not in ("/reda/", "/reda-rehab/") and not bookings.count():
                        row["errors"].append("No booking link found")
                    for link in bookings.all():
                        target = urlsplit(link.get_attribute("href") or "")
                        if target.scheme != "https" or target.hostname not in ("www.bokadirekt.se", "bokadirekt.se"):
                            row["errors"].append("Unexpected booking origin")
                    row["broken_visible_images"] = page.locator("img").evaluate_all("els=>els.filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.top<innerHeight&&r.bottom>0&&e.complete&&e.naturalWidth===0}).map(e=>new URL(e.src).pathname)")
                    if row["broken_visible_images"]:
                        row["errors"].append("Broken visible image")

                    if not baseline_only and path in READING_PATHS:
                        row['reading_orientation']=check_reading(page,path,output,label)

                    if not baseline_only and path in FILM_PATHS:
                        row['film_captions']=check_film_captions(page,path,output,label)

                    if not baseline_only and path in ('/ultraljud/', '/ultraljud/axel/', '/hyaluronsyra/'):
                        page.locator('.site-header').screenshot(path=str(output/f'context-header-{path.strip("/").replace("/","-")}-{label}.png'), animations='disabled')
                    if not baseline_only and path=='/ultraljud/axel/':
                        check_sample(page)
                        preview=page.locator('[data-atlas-demo]')
                        preview.screenshot(path=str(output/f'shoulder-preview-anatomy-{label}.png'), animations='disabled')
                        preview.get_by_role('switch',name='Visa fynden',exact=True).click()
                        page.locator('#bildexempel').screenshot(path=str(output/f'shoulder-preview-findings-{label}.png'), animations='disabled', style='body>header,body>a[href="#main"]{visibility:hidden!important}')

                    if not baseline_only:
                        if path == '/':
                            model = clinic_model(page)
                        elif path in CASE_PATHS:
                            row['ultrasound_design'] = check_case(page, model)
                        elif path == '/ultraljud/':
                            row['ultrasound_design'] = check_hub(page, model)
                        elif path == EXPLORE_PATH:
                            row['image_explorer'] = check_explore(page)

                    if not baseline_only and path == "/ultraljud/kna/":
                        page.locator('#artros').scroll_into_view_if_needed()
                        page.locator('#artros').screenshot(path=str(output/f'knee-guide-{label}.png'))

                    if not baseline_only and path in ("/ultraljud/kna/", RUNNER_PATH):
                        viewer=page.locator('[data-knee-viewer]')
                        anatomy=viewer.locator('[data-knee-anatomy]')
                        findings=viewer.locator('[data-knee-findings]')
                        expected_keys={'lateral-fluid','itb-bursa','posterior-meniscus'}
                        actual_keys=set(viewer.locator('.knee-panel').evaluate_all('(els)=>els.map(e=>e.dataset.key)'))
                        if not expected_keys<=actual_keys:
                            raise AssertionError('Runner knee examples missing')
                        if path==RUNNER_PATH and actual_keys!=expected_keys:
                            raise AssertionError('Unexpected runner knee example')
                        page.wait_for_function("[...document.querySelectorAll('.knee-anatomy img')].every(i=>i.complete&&i.naturalWidth>0)")
                        for key in ('itb-bursa','lateral-fluid','posterior-meniscus'):
                            viewer.locator('#tab-'+key).click()
                            picture=viewer.locator('#view-'+key+' .knee-picture')
                            picture.scroll_into_view_if_needed()
                            if anatomy.get_attribute('aria-checked')=='true': anatomy.click()
                            if findings.get_attribute('aria-checked')=='true': findings.click()
                            page.screenshot(path=str(output/f'{key}-{label}-original.png'))
                            findings.click()
                            if picture.get_attribute('data-findings')!='true' or picture.get_attribute('data-anatomy')!='false':
                                raise AssertionError('Findings are not independently visible on original')
                            page.screenshot(path=str(output/f'{key}-{label}-findings.png'))
                            anatomy.click()
                            page.wait_for_function("key=>new DOMMatrix(getComputedStyle(document.querySelector('#view-'+key+' .knee-anatomy')).transform).isIdentity",arg=key)
                            page.screenshot(path=str(output/f'{key}-{label}-anatomy-findings.png'))
                        viewer.locator('[data-knee-enlarge]').click()
                        if not page.locator('#knee-zoom').is_visible():
                            raise AssertionError('Enlarged view did not open')
                        page.locator('[data-knee-zoom-findings]').click()
                        if picture.get_attribute('data-findings')!='false':
                            raise AssertionError('Enlarged findings did not synchronize')
                        page.locator('[data-knee-zoom-close]').click()
                        viewer.get_by_role('tab').first.focus()
                        page.keyboard.press('ArrowLeft')
                        if viewer.get_by_role('tab').last.get_attribute('aria-selected')!='true':
                            raise AssertionError('Knee keyboard navigation did not wrap')
                        row['runner_reader']='Three originals, anatomy sweep, independent findings, enlarged view and keyboard navigation passed'

                    if not baseline_only and path == ELBOW_PATH:
                        if clinic_model(page) != model:
                            raise AssertionError('Elbow page differs from the clinic design')
                        for link in page.locator('.case-page-nav a').all():
                            if not page.locator(link.get_attribute('href')).count():
                                raise AssertionError('Elbow page navigation target missing')
                        viewer=page.locator('[data-elbow-viewer]')
                        anatomy=viewer.locator('[data-knee-anatomy]')
                        findings=viewer.locator('[data-knee-findings]')
                        if viewer.get_by_role('tab').count()!=2:
                            raise AssertionError('Expected healthy and injured elbow tabs')
                        page.wait_for_function("[...document.querySelectorAll('[data-elbow-viewer] .knee-anatomy img')].every(i=>i.complete&&i.naturalWidth===1280&&i.naturalHeight===960)")
                        if anatomy.get_attribute('aria-checked')!='false' or findings.get_attribute('aria-checked')!='false':
                            raise AssertionError('Elbow reader must start with the original ultrasound')
                        picture=viewer.locator('#view-skadad .knee-picture')
                        picture.scroll_into_view_if_needed()
                        page.screenshot(path=str(output/f'elbow-{label}-original.png'))
                        findings.click()
                        if picture.get_attribute('data-findings')!='true' or picture.get_attribute('data-anatomy')!='false':
                            raise AssertionError('Elbow findings cannot be shown on original')
                        page.screenshot(path=str(output/f'elbow-{label}-findings.png'))
                        anatomy.click()
                        page.wait_for_function("new DOMMatrix(getComputedStyle(document.querySelector('#view-skadad .knee-anatomy')).transform).isIdentity")
                        registered=picture.evaluate("""p=>{
                          const b=p.getBoundingClientRect(),i=p.querySelector('.knee-original').getBoundingClientRect(),s=p.querySelector('.knee-findings').getBoundingClientRect();
                          return Math.abs(i.width-b.width)<.1&&Math.abs(i.top+80*i.height/960-b.top)<.1&&Math.abs(i.height*600/960-b.height)<.1&&Math.abs(s.top-b.top)<.1&&Math.abs(s.height-b.height)<.1;
                        }""")
                        if not registered:raise AssertionError('Elbow source and finding coordinate frames differ')
                        page.screenshot(path=str(output/f'elbow-{label}-anatomy-findings.png'))
                        viewer.locator('[data-knee-enlarge]').click()
                        if not page.locator('#knee-zoom').is_visible():raise AssertionError('Elbow enlarged view failed')
                        page.locator('[data-knee-zoom-findings]').click()
                        if picture.get_attribute('data-findings')!='false':raise AssertionError('Elbow enlarged controls are not synchronized')
                        page.locator('[data-knee-zoom-close]').click()
                        viewer.locator('#tab-frisk').click()
                        if findings.is_visible() or anatomy.get_attribute('aria-checked')!='true':
                            raise AssertionError('Healthy elbow must retain anatomy and hide pathology control')
                        viewer.locator('#view-frisk .knee-picture').scroll_into_view_if_needed()
                        page.screenshot(path=str(output/f'elbow-{label}-healthy-anatomy.png'))
                        viewer.locator('[data-knee-enlarge]').click()
                        if page.locator('[data-knee-zoom-findings]').is_visible():raise AssertionError('Healthy enlarged view exposes pathology control')
                        page.keyboard.press('Escape')
                        viewer.get_by_role('tab').first.focus();page.keyboard.press('ArrowLeft')
                        if viewer.get_by_role('tab').last.get_attribute('aria-selected')!='true':raise AssertionError('Elbow keyboard navigation failed')
                        for control in viewer.locator('button').all():
                            if control.is_visible() and control.bounding_box()['height']<44:raise AssertionError('Elbow control is too small for touch')
                        row['elbow_reader']='Two originals, registered anatomy, independent findings, healthy view, synchronized enlargement and keyboard navigation passed'

                    if not baseline_only and path == ACHILLES_PATH:
                        if clinic_model(page) != model:
                            raise AssertionError('Achilles page differs from the clinic design')
                        row['achilles_reader'] = check_achilles(page, output, label)

                    if not baseline_only and path == '/ultraljud/bursit-axel/':
                        row['bursa_reader'] = check_bursa(page, output, label)

                    if not baseline_only and path == "/ultraljud/kalkaxel/":
                        viewer = page.locator('.patient-viewer')
                        switch = viewer.get_by_role('switch', name='Anatomi', exact=True)
                        if switch.count() != 1:
                            raise AssertionError('Expected one anatomy switch')
                        page.wait_for_function("[...document.querySelectorAll('.patient-viewer img[src]')].every(i=>i.complete&&i.naturalWidth>0)")
                        if switch.get_attribute('aria-checked') != 'false':
                            raise AssertionError('Ultrasound must be the initial view')
                        page.locator('#view-kalk .patient-picture').scroll_into_view_if_needed()
                        page.screenshot(path=str(output / f'kalkaxel-{label}-ultrasound.png'))
                        switch.click()
                        page.wait_for_function("document.querySelector('#view-kalk .patient-picture').dataset.mode==='anatomy' && getComputedStyle(document.querySelector('#view-kalk .anatomy-layer')).opacity==='1'")
                        page.wait_for_function("[...document.querySelectorAll('.detail-window img')].every(i=>i.complete&&i.naturalWidth>0&&i.src.endsWith('-anatomi.png'))")
                        page.locator('#view-kalk .patient-picture').scroll_into_view_if_needed()
                        page.screenshot(path=str(output / f'kalkaxel-{label}-anatomy.png'))
                        page.locator('#tab-frisk').click()
                        if switch.get_attribute('aria-checked') != 'true' or not page.locator('#view-frisk .detail-comparison').is_visible():
                            raise AssertionError('Anatomy and comparison must follow the selected side')
                        switch.click()
                        page.wait_for_function("[...document.querySelectorAll('.detail-window img')].every(i=>i.complete&&i.naturalWidth>0&&i.src.endsWith('-ultraljud.jpg'))")
                        for video_tab in ('film', 'dynamisk'):
                            page.locator('#tab-' + video_tab).click()
                            if switch.is_visible() or page.locator('.detail-comparison').is_visible():
                                raise AssertionError('Film view must hide anatomy switch and comparisons')
                            video = page.locator('#view-' + video_tab + ' video')
                            video.evaluate('(v)=>v.load()')
                            page.wait_for_function("id=>{const v=document.querySelector('#view-'+id+' video');return v.readyState>=1 && v.videoWidth===1280 && v.videoHeight===960}",arg=video_tab,timeout=15000)
                            video.evaluate('(v)=>v.play()')
                            page.wait_for_function("id=>document.querySelector('#view-'+id+' video').currentTime>0",arg=video_tab,timeout=15000)
                            video.evaluate('(v)=>v.pause()')
                        page.locator('#tab-kalk').click()
                        row['kalkaxel_reader'] = 'Originals, anatomy, three details, side selection and both films passed'

                    if not baseline_only and path == "/reda/":
                        if not page.locator(".reda-portal-top").is_visible():
                            row["errors"].append("Reda portal header missing")
                        if page.locator('body > nav[aria-label="Huvudmeny"]').is_visible():
                            row["errors"].append("Legacy Kansei navigation still visible")
                        if not page.locator("#kodform").is_visible():
                            row["errors"].append("Reda code form missing")
                        if not page.locator(".reda-portal-title").is_visible():
                            row["errors"].append("Current Reda portal title missing")
                        if page.locator(".reda-lockup").count():
                            row["errors"].append("Legacy mixed Reda hero branding still present")
                        if not page.locator('a[href="/reda-rehab/"]').count():
                            row["errors"].append("Reda product link missing")
                        if not page.locator('.reda-portal-links a[href="/"]').count():
                            row["errors"].append("Return-to-Kansei link missing")
                    elif not baseline_only and path == "/reda-rehab/":
                        if not page.locator('header .identity img[src*="/bilder/reda/nav.svg"]').is_visible():
                            row["errors"].append("Current Reda product brand missing")
                        for portal in page.locator('a[href="/reda/"]').all():
                            if portal.get_attribute("target") == "_blank":
                                row["errors"].append("Reda product page opens patient portal in a new tab")
                    elif not baseline_only:
                        bad_internal = page.locator('a[href^="https://www.kansei.se/"],a[href^="https://kansei.se/"]').count()
                        if bad_internal:
                            row["errors"].append("Absolute internal Kansei link found")
                        rehab = page.get_by_role("link", name="Min rehabplan", exact=True)
                        if rehab.count():
                            if rehab.first.get_attribute("href") != "/reda/":
                                row["errors"].append("Min rehabplan has wrong destination")
                            if rehab.first.get_attribute("target") == "_blank":
                                row["errors"].append("Min rehabplan opens a new tab")
                        # Reda was deliberately removed from the public clinic navigation.
                        reda_links = page.locator('a[href="/reda/"], a[href="/reda-rehab/"]')
                        if any(link.is_visible() for link in reda_links.all()):
                            row["errors"].append("Unreleased Reda link is visible on clinic page")

                    if not baseline_only and path == "/hjalp-mig-boka/" and label == "desktop":
                        # The homepage now links to the dedicated booking helper. Keep all shoulder-routing checks there.
                        # Shoulder routing is temporary while the dedicated shoulder clinician is unavailable.
                        opener = page.locator('button[data-area="shoulder"]').first
                        opener.click()
                        page.locator('#guide-dialog[open]').wait_for(timeout=5000)
                        guide = page.locator('#guide-dialog')

                        def shoulder_route(pattern, expected_title, href_fragment):
                            if guide.locator('[data-guide-screen="areas"]').count():
                                pass
                            if guide.locator('button[data-guide-area="shoulder"]').count():
                                guide.locator('button[data-guide-area="shoulder"]').click()
                            guide.locator(f'button[data-pattern="{pattern}"]').click()
                            guide.locator('button[data-safety="continue"]').click()
                            if guide.locator('.result-main h3').inner_text().strip() != expected_title:
                                row["errors"].append(f"Shoulder {pattern} has wrong recommended visit")
                            href = guide.locator('.guide-booking a[href*="bokadirekt.se/"]').get_attribute("href") or ""
                            if href_fragment not in href:
                                row["errors"].append(f"Shoulder {pattern} has wrong booking link")
                            if "axelbedomning" in href.lower() or "magnus-wennerlund" in href.lower():
                                row["errors"].append(f"Shoulder {pattern} still routes to shoulder assessment")
                            guide.locator('button[data-reset]').click()

                        shoulder_route("lifting", "Muskuloskeletalt ultraljud", "ultraljud-rorelseapparaten")
                        shoulder_route("night", "Muskuloskeletalt ultraljud", "ultraljud-rorelseapparaten")
                        shoulder_route("stiff", "Naprapatisk bedömning", "naprapati-ny-resp-aterbesok")
                        shoulder_route("rehab", "Muskuloskeletalt ultraljud", "ultraljud-rorelseapparaten")

                        guide.locator('button[data-guide-area="shoulder"]').click()
                        guide.locator('button[data-pattern="unclear"]').click()
                        guide.locator('button[data-safety="continue"]').click()
                        if guide.locator('.result-main h3').inner_text().strip() != "Naprapatisk bedömning":
                            row["errors"].append("Unclear shoulder symptoms do not route to naprapathy")
                        unclear_href = guide.locator('.guide-booking a[href*="bokadirekt.se/"]').get_attribute("href") or ""
                        if "naprapati-ny-resp-aterbesok" not in unclear_href:
                            row["errors"].append("Unclear shoulder symptoms have wrong booking link")
                        guide.locator('button[data-reset]').click()

                        guide.locator('button[data-guide-area="shoulder"]').click()
                        guide.locator('button[data-pattern="injury"]').click()
                        if guide.get_by_role("heading", name="Börja inte med en vanlig bokning.").count() != 1:
                            row["errors"].append("Shoulder injury no longer routes to care guidance")
                        if guide.locator('.guide-booking a[href*="bokadirekt.se/"]').count():
                            row["errors"].append("Shoulder injury exposes a commercial booking CTA")
                        guide.locator('button[data-reset]').click()

                        guide.locator('button[data-guide-services]').click()
                        if guide.get_by_text("Axelbedömning", exact=True).count():
                            row["errors"].append("Shoulder assessment still appears in direct service picker")
                        if guide.locator('a[href="/skuldra/"]').count():
                            row["errors"].append("Direct service picker still links to shoulder assessment")
                        page.keyboard.press("Escape")

                    if not baseline_only and path == "/kunskapsbank/":
                        cards = page.locator("[data-library-card]")
                        total = cards.count()
                        if total < 64:
                            row["errors"].append("Expanded knowledge library is incomplete")
                        visible = page.locator("[data-library-card]:not([hidden])")
                        search = page.locator("[data-library-search]")
                        page.get_by_role("button", name="Ultraljud", exact=True).click()
                        if visible.count() < 6 or page.locator('[data-library-card]:not([hidden]):not([data-category="Ultraljud"])').count():
                            row["errors"].append("Ultrasound category filter failed")
                        search.fill("zzzz-inte-ett-amne")
                        if visible.count() != 0 or not page.locator("[data-library-empty]").is_visible():
                            row["errors"].append("Knowledge empty state failed")
                        page.locator("[data-library-reset]").click()
                        if visible.count() != total or search.input_value():
                            row["errors"].append("Knowledge search reset failed")
                        search.fill("halseneruptur")
                        if visible.count() != 1 or "Misstänkt hälseneruptur" not in visible.inner_text():
                            row["errors"].append("Accent-insensitive article search failed")
                        search.fill("")
                        if page.locator("[data-library-count]").inner_text() != f"{total} artiklar":
                            row["errors"].append("Knowledge result count failed")
                    if not baseline_only and path in KNOWLEDGE_PATHS[1:]:
                        if not page.locator(".article-sources a").count():
                            row["errors"].append("Article sources missing")
                        if "Medicinskt granskad" in page.locator("main").inner_text():
                            row["errors"].append("Unsupported medical review attribution")
                        if path == "/blogg/misstankt-halseneruptur/" and page.locator('main a[href*="bokadirekt.se"]').count():
                            row["errors"].append("Urgent injury article exposes a commercial booking CTA")

                    if not baseline_only and path in STORY_PATHS:
                        row['case_story'] = check_story(page, path, output, label)

                    if not baseline_only and path in CONTEXT_PATHS:
                        row['case_context'] = check_context(page, path, output, label)

                    if not baseline_only and path in ('/naprapati/', '/hyaluronsyra/', '/hyaluronsyra/kna/'):
                        bridge=page.locator('[data-case-service]')
                        if bridge.count()!=1:raise AssertionError('Service-to-case entrance missing or duplicated')
                        if label!='compact':
                            bridge.scroll_into_view_if_needed()
                            bridge.screenshot(path=str(output/f'service-cases-{path.strip("/").replace("/","-")}-{label}.png'),animations='disabled',style='body>header,body>a[href="#main"]{visibility:hidden!important}')

                    if not baseline_only:
                        headers = page.locator('[data-scan-header]')
                        if headers.count():
                            if not headers.evaluate_all("""items=>items.every(el=>{
                                const expected=parseFloat(el.style.getPropertyValue('--scan-header'));
                                const actual=parseFloat(getComputedStyle(el).clipPath.replace('inset(',''));
                                // Existing anatomical crops can hide more of the header.
                                return Number.isFinite(expected)&&expected>0&&expected<10&&Number.isFinite(actual)&&actual+.001>=expected;
                            })"""):
                                row['errors'].append('Acquisition header is exposed or scan canvas was shifted')
                            row['hidden_scan_headers'] = headers.count()

                    if not baseline_only and path in ('/blogg/domningar-i-handen-pa-natten/', '/kunskapsbank/axel/ont-i-axeln-pa-natten/'):
                        preview = page.locator('.clinical-evidence-preview')
                        preview.scroll_into_view_if_needed()
                        preview.locator('img').scroll_into_view_if_needed()
                        page.wait_for_function("() => { const img = document.querySelector('.clinical-evidence-preview img'); return img.complete && img.naturalWidth > 0; }", timeout=15000)
                        preview.screenshot(path=str(output / f'clinical-example-{path.strip("/").replace("/", "-")}-{label}.png'), animations='disabled')
                    if not baseline_only and path == '/hyaluronsyra/kna/':
                        prices = page.locator('#pris')
                        prices.scroll_into_view_if_needed()
                        prices.screenshot(path=str(output / f'knee-prices-{label}.png'), animations='disabled', style='body>header,body>a[href="#main"]{visibility:hidden!important}')

                    if not baseline_only and path in ('/hyaluronsyra/', '/hyaluronsyra/sinovial-sinogel/', '/prp/'):
                        galleries = page.locator('[data-product-gallery]')
                        for i in range(galleries.count()):
                            gallery = galleries.nth(i)
                            pictures = gallery.locator('img')
                            for j in range(pictures.count()):
                                picture = pictures.nth(j)
                                picture.scroll_into_view_if_needed()
                                page.wait_for_function("img => img.complete && img.naturalWidth > 0", arg=picture.element_handle(), timeout=15000)
                            gallery.screenshot(path=str(output / f'product-gallery-{path.strip("/").replace("/", "-")}-{i}-{label}.png'), animations='disabled', style='body>header,body>a[href="#main"]{visibility:hidden!important}')

                    slug = path.strip("/").replace("/", "-") or "home"
                    page.screenshot(path=str(output / f"{slug}-{label}.png"), full_page=False, animations="disabled")
                    if label == "mobile" and path not in ("/reda/", "/reda-rehab/") and page.locator("button.burger").count() == 1:
                        menu = page.locator("button.burger")
                        if menu.is_visible():
                            menu.click(timeout=5000)
                            page.wait_for_timeout(100)
                            if menu.get_attribute("aria-expanded") != "true":
                                row["errors"].append("Mobile menu does not expose expanded state")
                            page.screenshot(path=str(output / f"{slug}-mobile-menu.png"), animations="disabled")
                    if js_errors:
                        row["errors"].append("JavaScript runtime error")
                        row["js_errors"] = js_errors[:5]
                except Exception as exc:
                    row["errors"].append(type(exc).__name__ + ": " + str(exc)[:140])
                finally:
                    page.close()
                records.append(row)
                errors.extend(f"{path} {label}: {e}" for e in row["errors"])
            context.close()
        browser.close()
    (output / "report.json").write_text(json.dumps(records, ensure_ascii=False, indent=2))
    print(json.dumps({"checks": len(records), "errors": errors}, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="https://www.kansei.se")
    ap.add_argument("--output", type=Path, default=Path("browser-report"))
    args = ap.parse_args()
    check(args.base, args.output)
